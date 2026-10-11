"""
Billing & Point of Sale Blueprint (routes/billing_routes.py)
Hospital Pharmacy Management System (HPMS)

Handles pharmacy checkout, atomic transactions, pessimistic locking (FOR UPDATE),
server-side price computation, inventory depletion, validation against expired drugs,
and printable tax invoice generation.
"""

from datetime import datetime
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
import oracledb
from auth import login_required
from db import get_db_cursor, execute_query, row_to_dict

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.route("/")
@login_required
def index():
    """
    List billing history with search and date filters.
    """
    search = request.args.get("search", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    sql = """
        SELECT 
            b.bill_id,
            b.bill_number,
            b.customer_name,
            b.patient_id,
            b.bill_date,
            b.subtotal,
            b.discount_pct,
            b.tax_pct,
            b.total_amount,
            b.payment_method,
            u.full_name AS billed_by_user,
            (SELECT COUNT(*) FROM BILL_ITEMS bi WHERE bi.bill_id = b.bill_id) AS items_count
        FROM BILL b
        LEFT JOIN APP_USERS u ON b.created_by = u.user_id
        WHERE 1 = 1
    """
    params = {}

    if search:
        sql += " AND (LOWER(b.bill_number) LIKE :s OR LOWER(b.customer_name) LIKE :s)"
        params["s"] = f"%{search.lower()}%"

    if date_from:
        sql += " AND TRUNC(b.bill_date) >= TO_DATE(:dfrom, 'YYYY-MM-DD')"
        params["dfrom"] = date_from

    if date_to:
        sql += " AND TRUNC(b.bill_date) <= TO_DATE(:dto, 'YYYY-MM-DD')"
        params["dto"] = date_to

    sql += " ORDER BY b.bill_date DESC, b.bill_id DESC"

    bills = execute_query(sql, params, fetchall=True)
    return render_template(
        "billing/list.html",
        bills=bills,
        current_search=search,
        current_date_from=date_from,
        current_date_to=date_to
    )


@billing_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """
    Point of Sale screen for creating new customer/patient pharmacy bills.
    """
    patients = execute_query("SELECT patient_id, name, phone FROM PATIENT ORDER BY name ASC", fetchall=True)
    active_medicines = execute_query(
        """
        SELECT 
            medicine_id, medicine_name, unit_price, quantity, batch_number, expiry_date,
            CASE WHEN expiry_date < TRUNC(CURRENT_DATE) THEN 1 ELSE 0 END AS is_expired
        FROM MEDICINE
        WHERE quantity > 0 AND expiry_date >= TRUNC(CURRENT_DATE)
        ORDER BY medicine_name ASC
        """,
        fetchall=True
    )

    if request.method == "POST":
        customer_type = request.form.get("customer_type", "walkin")
        patient_id_val = request.form.get("patient_id", "").strip()
        walkin_name = request.form.get("walkin_name", "").strip()
        payment_method = request.form.get("payment_method", "CASH")
        discount_str = request.form.get("discount_pct", "0").strip()
        tax_str = request.form.get("tax_pct", "0").strip()

        # Multi-item arrays from POST
        med_ids = request.form.getlist("medicine_id[]")
        quantities = request.form.getlist("quantity[]")

        errors = []

        # Customer Resolution
        resolved_patient_id = None
        if customer_type == "patient":
            if not patient_id_val:
                errors.append("Please select a registered patient.")
            else:
                pat_row = execute_query(
                    "SELECT patient_id, name FROM PATIENT WHERE patient_id = :id",
                    {"id": int(patient_id_val)},
                    fetchone=True
                )
                if not pat_row:
                    errors.append("Selected patient was not found.")
                else:
                    resolved_patient_id = pat_row["patient_id"]
                    customer_name = pat_row["name"]
        else:
            if not walkin_name:
                customer_name = "Walk-in Customer"
            else:
                customer_name = f"Walk-in ({walkin_name})"

        # Discount & Tax Validation
        try:
            discount_pct = float(discount_str)
            if discount_pct < 0 or discount_pct > 100:
                errors.append("Discount percentage must be between 0 and 100.")
        except ValueError:
            errors.append("Invalid discount percentage value.")
            discount_pct = 0.0

        try:
            tax_pct = float(tax_str)
            if tax_pct < 0 or tax_pct > 100:
                errors.append("Tax percentage must be between 0 and 100.")
        except ValueError:
            errors.append("Invalid tax percentage value.")
            tax_pct = 0.0

        if payment_method not in ("CASH", "CARD", "UPI"):
            errors.append("Invalid payment method.")

        # Parsing items
        parsed_items = []
        if not med_ids:
            errors.append("Please add at least one medicine to the bill.")
        else:
            for idx in range(len(med_ids)):
                m_str = med_ids[idx].strip()
                q_str = quantities[idx].strip() if idx < len(quantities) else "1"

                if not m_str:
                    continue

                try:
                    m_id = int(m_str)
                except ValueError:
                    errors.append(f"Line {idx+1}: Invalid medicine selection.")
                    continue

                try:
                    qty = int(q_str)
                    if qty <= 0:
                        errors.append(f"Line {idx+1}: Quantity must be greater than zero.")
                        continue
                except ValueError:
                    errors.append(f"Line {idx+1}: Invalid quantity.")
                    continue

                parsed_items.append({"medicine_id": m_id, "quantity": qty, "line_no": idx + 1})

        if not parsed_items and not errors:
            errors.append("No valid medication items were provided.")

        # Check for duplicates within the same bill
        seen_ids = set()
        for itm in parsed_items:
            if itm["medicine_id"] in seen_ids:
                errors.append(f"Duplicate item detected for medicine ID {itm['medicine_id']}. Please consolidate quantities into a single line.")
            seen_ids.add(itm["medicine_id"])

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "billing/new.html",
                patients=patients,
                active_medicines=active_medicines,
                form_data=request.form
            )

        # --------------------------------------------------------------------
        # ATOMIC BILLING TRANSACTION WITH PESSIMISTIC STOCK LOCKING
        # --------------------------------------------------------------------
        try:
            with get_db_cursor(commit=True) as (conn, cursor):
                calculated_items = []
                subtotal = 0.0

                for itm in parsed_items:
                    # Pessimistic Row Lock: SELECT ... FOR UPDATE
                    cursor.execute(
                        """
                        SELECT medicine_id, medicine_name, unit_price, quantity, expiry_date
                        FROM MEDICINE
                        WHERE medicine_id = :mid
                        FOR UPDATE
                        """,
                        {"mid": itm["medicine_id"]}
                    )
                    med_data = row_to_dict(cursor, cursor.fetchone())

                    if not med_data:
                        raise ValueError(f"Medicine with ID {itm['medicine_id']} was not found in the catalog.")

                    # Expiry validation
                    exp_date = med_data["expiry_date"]
                    if hasattr(exp_date, "date"):
                        exp_date = exp_date.date()
                    if exp_date < datetime.now().date():
                        raise ValueError(
                            f"Safety Violation: '{med_data['medicine_name']}' is EXPIRED ({med_data['expiry_date']}) "
                            f"and cannot be dispensed or billed."
                        )

                    # Stock validation
                    if med_data["quantity"] < itm["quantity"]:
                        raise ValueError(
                            f"Insufficient Inventory for '{med_data['medicine_name']}': "
                            f"Requested {itm['quantity']} units, but only {med_data['quantity']} units available in stock."
                        )

                    # Calculate line total strictly on the server using authoritative database price
                    unit_price = float(med_data["unit_price"])
                    line_total = round(unit_price * itm["quantity"], 2)
                    subtotal += line_total

                    calculated_items.append({
                        "medicine_id": med_data["medicine_id"],
                        "medicine_name": med_data["medicine_name"],
                        "unit_price": unit_price,
                        "quantity": itm["quantity"],
                        "line_total": line_total
                    })

                subtotal = round(subtotal, 2)
                discount_amount = round(subtotal * (discount_pct / 100.0), 2)
                taxable_base = subtotal - discount_amount
                tax_amount = round(taxable_base * (tax_pct / 100.0), 2)
                total_amount = round(taxable_base + tax_amount, 2)

                # Generate Unique Bill Number: INV-YYYYMMDD-XXXX
                today_tag = datetime.now().strftime("%Y%m%d")
                random_suffix = secrets.token_hex(2).upper()
                bill_number = f"INV-{today_tag}-{random_suffix}"

                # Insert BILL record
                out_bill_id = cursor.var(oracledb.NUMBER)
                cursor.execute(
                    """
                    INSERT INTO BILL (
                        bill_number, patient_id, customer_name, bill_date,
                        subtotal, discount_pct, tax_pct, total_amount, payment_method, created_by
                    ) VALUES (
                        :bnum, :pid, :cname, CURRENT_TIMESTAMP,
                        :sub, :disc, :tax, :tot, :pmeth, :created_by_user
                    ) RETURNING bill_id INTO :out_bid
                    """,
                    {
                        "bnum": bill_number,
                        "pid": resolved_patient_id,
                        "cname": customer_name,
                        "sub": subtotal,
                        "disc": discount_pct,
                        "tax": tax_pct,
                        "tot": total_amount,
                        "pmeth": payment_method,
                        "created_by_user": session.get("user_id"),
                        "out_bid": out_bill_id
                    }
                )
                new_bill_id = int(out_bill_id.getvalue()[0])

                # Insert BILL_ITEMS and Deduct Inventory Quantities
                for c_itm in calculated_items:
                    cursor.execute(
                        """
                        INSERT INTO BILL_ITEMS (
                            bill_id, medicine_id, medicine_name, unit_price, quantity, line_total
                        ) VALUES (
                            :bid, :mid, :mname, :uprice, :qty, :ltot
                        )
                        """,
                        {
                            "bid": new_bill_id,
                            "mid": c_itm["medicine_id"],
                            "mname": c_itm["medicine_name"],
                            "uprice": c_itm["unit_price"],
                            "qty": c_itm["quantity"],
                            "ltot": c_itm["line_total"]
                        }
                    )

                    # Inventory Deduction
                    cursor.execute(
                        """
                        UPDATE MEDICINE
                        SET quantity = quantity - :sold_qty
                        WHERE medicine_id = :mid
                        """,
                        {
                            "sold_qty": c_itm["quantity"],
                            "mid": c_itm["medicine_id"]
                        }
                    )

            flash(f"Sale completed successfully! Invoice {bill_number} generated.", "success")
            return redirect(url_for("billing.invoice", bill_id=new_bill_id))

        except Exception as tx_err:
            flash(f"Transaction aborted: {str(tx_err)}", "danger")
            return render_template(
                "billing/new.html",
                patients=patients,
                active_medicines=active_medicines,
                form_data=request.form
            )

    return render_template(
        "billing/new.html",
        patients=patients,
        active_medicines=active_medicines,
        form_data={}
    )


@billing_bp.route("/invoice/<int:bill_id>")
@login_required
def invoice(bill_id):
    """
    Printable, professional pharmacy invoice.
    """
    bill = execute_query(
        """
        SELECT 
            b.bill_id,
            b.bill_number,
            b.patient_id,
            b.customer_name,
            b.bill_date,
            b.subtotal,
            b.discount_pct,
            b.tax_pct,
            b.total_amount,
            b.payment_method,
            u.full_name AS billed_by_user,
            p.phone AS patient_phone,
            p.address AS patient_address
        FROM BILL b
        LEFT JOIN APP_USERS u ON b.created_by = u.user_id
        LEFT JOIN PATIENT p ON b.patient_id = p.patient_id
        WHERE b.bill_id = :id
        """,
        {"id": bill_id},
        fetchone=True
    )
    if not bill:
        flash("Invoice not found.", "danger")
        return redirect(url_for("billing.index"))

    items = execute_query(
        """
        SELECT 
            bi.bill_item_id,
            bi.medicine_id,
            bi.medicine_name,
            bi.unit_price,
            bi.quantity,
            bi.line_total,
            m.category,
            m.batch_number
        FROM BILL_ITEMS bi
        LEFT JOIN MEDICINE m ON bi.medicine_id = m.medicine_id
        WHERE bi.bill_id = :id
        ORDER BY bi.bill_item_id ASC
        """,
        {"id": bill_id},
        fetchall=True
    )

    # Compute discount and tax amounts for detailed display
    subtotal = float(bill["subtotal"])
    discount_pct = float(bill["discount_pct"])
    tax_pct = float(bill["tax_pct"])
    discount_amount = round(subtotal * (discount_pct / 100.0), 2)
    tax_amount = round((subtotal - discount_amount) * (tax_pct / 100.0), 2)

    return render_template(
        "billing/invoice.html",
        bill=bill,
        items=items,
        discount_amount=discount_amount,
        tax_amount=tax_amount
    )


@billing_bp.route("/api/medicine/<int:medicine_id>")
@login_required
def api_medicine(medicine_id):
    """
    API returning live stock, batch, and authoritative price for dynamic frontend billing calculations.
    """
    med = execute_query(
        """
        SELECT 
            medicine_id,
            medicine_name,
            category,
            unit_price,
            quantity,
            batch_number,
            TO_CHAR(expiry_date, 'YYYY-MM-DD') AS expiry_date,
            CASE WHEN expiry_date < TRUNC(CURRENT_DATE) THEN 1 ELSE 0 END AS is_expired
        FROM MEDICINE
        WHERE medicine_id = :id
        """,
        {"id": medicine_id},
        fetchone=True
    )
    if not med:
        return jsonify({"error": "Medicine not found"}), 404

    return jsonify({
        "medicine_id": med["medicine_id"],
        "medicine_name": med["medicine_name"],
        "category": med["category"],
        "unit_price": float(med["unit_price"]),
        "quantity": int(med["quantity"]),
        "batch_number": med["batch_number"],
        "expiry_date": med["expiry_date"],
        "is_expired": bool(med["is_expired"])
    })
