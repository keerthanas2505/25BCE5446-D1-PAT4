"""
Medicine Inventory Blueprint (routes/medicine_routes.py)
Hospital Pharmacy Management System (HPMS)
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from auth import login_required
from db import execute_query

medicine_bp = Blueprint("medicines", __name__, url_prefix="/medicines")


@medicine_bp.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    stock_status = request.args.get("stock_status", "").strip()
    sort_by = request.args.get("sort_by", "name_asc")

    sql = """
        SELECT 
            m.medicine_id,
            m.medicine_name,
            m.category,
            m.unit_price,
            m.quantity,
            m.reorder_threshold,
            m.batch_number,
            m.expiry_date,
            s.supplier_id,
            s.supplier_name,
            ROUND(m.expiry_date - TRUNC(CURRENT_DATE)) AS days_to_expiry,
            CASE 
                WHEN m.quantity = 0 THEN 'OUT_OF_STOCK'
                WHEN m.quantity <= m.reorder_threshold THEN 'LOW_STOCK'
                ELSE 'ADEQUATE'
            END AS stock_status_calc,
            CASE 
                WHEN m.expiry_date < TRUNC(CURRENT_DATE) THEN 'EXPIRED'
                WHEN m.expiry_date <= TRUNC(CURRENT_DATE) + 60 THEN 'EXPIRING_SOON'
                ELSE 'VALID'
            END AS expiry_status_calc
        FROM MEDICINE m
        JOIN SUPPLIER s ON m.supplier_id = s.supplier_id
        WHERE 1 = 1
    """
    params = {}

    if search:
        sql += " AND (LOWER(m.medicine_name) LIKE :search OR CAST(m.medicine_id AS TEXT) = :search_exact OR LOWER(m.batch_number) LIKE :search)"
        params["search"] = f"%{search.lower()}%"
        params["search_exact"] = search

    if category:
        sql += " AND m.category = :category"
        params["category"] = category

    if stock_status == "out":
        sql += " AND m.quantity = 0"
    elif stock_status == "low":
        sql += " AND m.quantity <= m.reorder_threshold AND m.quantity > 0"
    elif stock_status == "expired":
        sql += " AND m.expiry_date < TRUNC(CURRENT_DATE)"
    elif stock_status == "expiring_soon":
        sql += " AND m.expiry_date >= TRUNC(CURRENT_DATE) AND m.expiry_date <= TRUNC(CURRENT_DATE) + 60"

    # Sorting
    sort_map = {
        "name_asc": " ORDER BY m.medicine_name ASC",
        "name_desc": " ORDER BY m.medicine_name DESC",
        "stock_asc": " ORDER BY m.quantity ASC",
        "stock_desc": " ORDER BY m.quantity DESC",
        "price_asc": " ORDER BY m.unit_price ASC",
        "price_desc": " ORDER BY m.unit_price DESC",
        "expiry_asc": " ORDER BY m.expiry_date ASC",
    }
    sql += sort_map.get(sort_by, " ORDER BY m.medicine_name ASC")

    medicines = execute_query(sql, params, fetchall=True)

    # Categories for filter dropdown
    categories_res = execute_query(
        "SELECT DISTINCT category FROM MEDICINE ORDER BY category ASC",
        fetchall=True
    )
    categories = [c["category"] for c in categories_res]

    return render_template(
        "medicines/list.html",
        medicines=medicines,
        categories=categories,
        current_search=search,
        current_category=category,
        current_stock_status=stock_status,
        current_sort=sort_by
    )


@medicine_bp.route("/<int:medicine_id>")
@login_required
def detail(medicine_id):
    sql = """
        SELECT 
            m.medicine_id,
            m.medicine_name,
            m.category,
            m.description,
            m.unit_price,
            m.quantity,
            m.reorder_threshold,
            m.batch_number,
            m.expiry_date,
            m.created_at,
            s.supplier_id,
            s.supplier_name,
            s.phone AS supplier_phone,
            s.email AS supplier_email,
            ROUND(m.expiry_date - TRUNC(CURRENT_DATE)) AS days_to_expiry
        FROM MEDICINE m
        JOIN SUPPLIER s ON m.supplier_id = s.supplier_id
        WHERE m.medicine_id = :id
    """
    medicine = execute_query(sql, {"id": medicine_id}, fetchone=True)
    if not medicine:
        flash("Medicine record not found.", "danger")
        return redirect(url_for("medicines.index"))

    # Historical sales summary for this medicine
    sales_history = execute_query(
        """
        SELECT 
            b.bill_number,
            b.bill_date,
            b.customer_name,
            bi.unit_price AS sold_price,
            bi.quantity,
            bi.line_total
        FROM BILL_ITEMS bi
        JOIN BILL b ON bi.bill_id = b.bill_id
        WHERE bi.medicine_id = :mid
        ORDER BY b.bill_date DESC
        LIMIT 10
        """,
        {"mid": medicine_id},
        fetchall=True
    )

    return render_template(
        "medicines/detail.html",
        med=medicine,
        sales_history=sales_history
    )


@medicine_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    suppliers = execute_query(
        "SELECT supplier_id, supplier_name FROM SUPPLIER ORDER BY supplier_name ASC",
        fetchall=True
    )

    if request.method == "POST":
        medicine_name = request.form.get("medicine_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        batch_number = request.form.get("batch_number", "").strip()
        expiry_date_str = request.form.get("expiry_date", "").strip()
        supplier_id = request.form.get("supplier_id", "").strip()
        unit_price_str = request.form.get("unit_price", "").strip()
        quantity_str = request.form.get("quantity", "0").strip()
        reorder_threshold_str = request.form.get("reorder_threshold", "15").strip()

        # Validation
        errors = []
        if not medicine_name:
            errors.append("Medicine name is required.")
        if not category:
            errors.append("Category is required.")
        if not batch_number:
            errors.append("Batch number is required.")
        if not supplier_id:
            errors.append("Please select a valid supplier.")

        try:
            unit_price = float(unit_price_str)
            if unit_price < 0:
                errors.append("Unit price must be non-negative.")
        except ValueError:
            errors.append("Invalid unit price number.")

        try:
            quantity = int(quantity_str)
            if quantity < 0:
                errors.append("Quantity must be non-negative.")
        except ValueError:
            errors.append("Invalid quantity number.")

        try:
            reorder_threshold = int(reorder_threshold_str)
            if reorder_threshold < 0:
                errors.append("Reorder threshold must be non-negative.")
        except ValueError:
            errors.append("Invalid reorder threshold.")

        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Valid expiry date (YYYY-MM-DD) is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("medicines/form.html", suppliers=suppliers, form_data=request.form, is_edit=False)

        # Check unique constraint (medicine_name + batch_number)
        dup = execute_query(
            "SELECT medicine_id FROM MEDICINE WHERE medicine_name = :n AND batch_number = :b",
            {"n": medicine_name, "b": batch_number},
            fetchone=True
        )
        if dup:
            flash(f"A batch with number '{batch_number}' for '{medicine_name}' already exists.", "danger")
            return render_template("medicines/form.html", suppliers=suppliers, form_data=request.form, is_edit=False)

        execute_query(
            """
            INSERT INTO MEDICINE (
                medicine_name, category, description, unit_price, quantity,
                reorder_threshold, batch_number, expiry_date, supplier_id
            ) VALUES (
                :n, :c, :d, :p, :q, :t, :b, TO_DATE(:exp, 'YYYY-MM-DD'), :s
            )
            """,
            {
                "n": medicine_name,
                "c": category,
                "d": description,
                "p": unit_price,
                "q": quantity,
                "t": reorder_threshold,
                "b": batch_number,
                "exp": expiry_date_str,
                "s": int(supplier_id)
            },
            commit=True
        )
        flash(f"Medicine '{medicine_name}' added successfully to inventory.", "success")
        return redirect(url_for("medicines.index"))

    return render_template("medicines/form.html", suppliers=suppliers, form_data={}, is_edit=False)


@medicine_bp.route("/<int:medicine_id>/edit", methods=["GET", "POST"])
@login_required
def edit(medicine_id):
    medicine = execute_query(
        """
        SELECT medicine_id, medicine_name, category, description, unit_price,
               quantity, reorder_threshold, batch_number, 
               TO_CHAR(expiry_date, 'YYYY-MM-DD') AS expiry_date_str,
               supplier_id
        FROM MEDICINE
        WHERE medicine_id = :id
        """,
        {"id": medicine_id},
        fetchone=True
    )
    if not medicine:
        flash("Medicine record not found.", "danger")
        return redirect(url_for("medicines.index"))

    suppliers = execute_query(
        "SELECT supplier_id, supplier_name FROM SUPPLIER ORDER BY supplier_name ASC",
        fetchall=True
    )

    if request.method == "POST":
        medicine_name = request.form.get("medicine_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        batch_number = request.form.get("batch_number", "").strip()
        expiry_date_str = request.form.get("expiry_date", "").strip()
        supplier_id = request.form.get("supplier_id", "").strip()
        unit_price_str = request.form.get("unit_price", "").strip()
        quantity_str = request.form.get("quantity", "0").strip()
        reorder_threshold_str = request.form.get("reorder_threshold", "15").strip()

        errors = []
        if not medicine_name:
            errors.append("Medicine name is required.")
        if not category:
            errors.append("Category is required.")
        if not batch_number:
            errors.append("Batch number is required.")
        if not supplier_id:
            errors.append("Please select a valid supplier.")

        try:
            unit_price = float(unit_price_str)
            if unit_price < 0:
                errors.append("Unit price must be non-negative.")
        except ValueError:
            errors.append("Invalid unit price number.")

        try:
            quantity = int(quantity_str)
            if quantity < 0:
                errors.append("Quantity must be non-negative.")
        except ValueError:
            errors.append("Invalid quantity number.")

        try:
            reorder_threshold = int(reorder_threshold_str)
            if reorder_threshold < 0:
                errors.append("Reorder threshold must be non-negative.")
        except ValueError:
            errors.append("Invalid reorder threshold.")

        try:
            datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            errors.append("Valid expiry date (YYYY-MM-DD) is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "medicines/form.html",
                suppliers=suppliers,
                form_data=request.form,
                is_edit=True,
                medicine_id=medicine_id
            )

        # Update record
        execute_query(
            """
            UPDATE MEDICINE SET
                medicine_name = :n,
                category = :c,
                description = :d,
                unit_price = :p,
                quantity = :q,
                reorder_threshold = :t,
                batch_number = :b,
                expiry_date = TO_DATE(:exp, 'YYYY-MM-DD'),
                supplier_id = :s
            WHERE medicine_id = :id
            """,
            {
                "n": medicine_name,
                "c": category,
                "d": description,
                "p": unit_price,
                "q": quantity,
                "t": reorder_threshold,
                "b": batch_number,
                "exp": expiry_date_str,
                "s": int(supplier_id),
                "id": medicine_id
            },
            commit=True
        )
        flash(f"Medicine '{medicine_name}' updated successfully.", "success")
        return redirect(url_for("medicines.detail", medicine_id=medicine_id))

    # Pre-populate form data for GET
    form_data = {
        "medicine_name": medicine["medicine_name"],
        "category": medicine["category"],
        "description": medicine["description"] or "",
        "unit_price": medicine["unit_price"],
        "quantity": medicine["quantity"],
        "reorder_threshold": medicine["reorder_threshold"],
        "batch_number": medicine["batch_number"],
        "expiry_date": medicine["expiry_date_str"],
        "supplier_id": medicine["supplier_id"],
    }
    return render_template(
        "medicines/form.html",
        suppliers=suppliers,
        form_data=form_data,
        is_edit=True,
        medicine_id=medicine_id
    )


@medicine_bp.route("/<int:medicine_id>/delete", methods=["POST"])
@login_required
def delete(medicine_id):
    # Check if medicine is linked to historical sales or prescriptions
    sales_ref = execute_query(
        "SELECT COUNT(*) AS cnt FROM BILL_ITEMS WHERE medicine_id = :id",
        {"id": medicine_id},
        fetchone=True
    )
    pres_ref = execute_query(
        "SELECT COUNT(*) AS cnt FROM PRESCRIPTION_ITEMS WHERE medicine_id = :id",
        {"id": medicine_id},
        fetchone=True
    )

    sales_count = sales_ref["cnt"] if sales_ref else 0
    pres_count = pres_ref["cnt"] if pres_ref else 0

    if sales_count > 0 or pres_count > 0:
        flash(
            f"Cannot delete medicine (ID: {medicine_id}) because it has historical associations "
            f"({sales_count} sales items, {pres_count} prescription items). "
            f"Past records must be preserved for clinical auditing and financial integrity.",
            "warning"
        )
        return redirect(url_for("medicines.detail", medicine_id=medicine_id))

    try:
        execute_query(
            "DELETE FROM MEDICINE WHERE medicine_id = :id",
            {"id": medicine_id},
            commit=True
        )
        flash("Medicine record deleted safely from inventory.", "success")
        return redirect(url_for("medicines.index"))
    except psycopg2.Error as e:
        flash(f"Database error deleting medicine: {e}", "danger")
        return redirect(url_for("medicines.detail", medicine_id=medicine_id))
