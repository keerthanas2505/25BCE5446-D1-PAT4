"""
Prescription Management Blueprint (routes/prescription_routes.py)
Hospital Pharmacy Management System (HPMS)
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from auth import login_required
from db import get_db_cursor, execute_query, row_to_dict

prescription_bp = Blueprint("prescriptions", __name__, url_prefix="/prescriptions")


@prescription_bp.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()

    sql = """
        SELECT 
            pr.prescription_id,
            pr.doctor_name,
            pr.diagnosis,
            pr.prescription_date,
            p.patient_id,
            p.name AS patient_name,
            p.phone AS patient_phone,
            (SELECT COUNT(*) FROM PRESCRIPTION_ITEMS pi WHERE pi.prescription_id = pr.prescription_id) AS items_count
        FROM PRESCRIPTION pr
        JOIN PATIENT p ON pr.patient_id = p.patient_id
        WHERE 1 = 1
    """
    params = {}
    if search:
        sql += " AND (LOWER(p.name) LIKE :s OR LOWER(pr.doctor_name) LIKE :s OR LOWER(pr.diagnosis) LIKE :s OR CAST(pr.prescription_id AS TEXT) = :s_exact)"
        params["s"] = f"%{search.lower()}%"
        params["s_exact"] = search

    sql += " ORDER BY pr.prescription_date DESC, pr.prescription_id DESC"

    prescriptions = execute_query(sql, params, fetchall=True)
    return render_template("prescriptions/list.html", prescriptions=prescriptions, current_search=search)


@prescription_bp.route("/<int:prescription_id>")
@login_required
def detail(prescription_id):
    sql = """
        SELECT 
            pr.prescription_id,
            pr.doctor_name,
            pr.diagnosis,
            pr.prescription_date,
            pr.notes,
            pr.created_at,
            p.patient_id,
            p.name AS patient_name,
            p.age AS patient_age,
            p.gender AS patient_gender,
            p.phone AS patient_phone,
            p.address AS patient_address
        FROM PRESCRIPTION pr
        JOIN PATIENT p ON pr.patient_id = p.patient_id
        WHERE pr.prescription_id = :id
    """
    prescription = execute_query(sql, {"id": prescription_id}, fetchone=True)
    if not prescription:
        flash("Prescription record not found.", "danger")
        return redirect(url_for("prescriptions.index"))

    items_sql = """
        SELECT 
            pi.item_id,
            pi.medicine_id,
            pi.dosage,
            pi.quantity,
            m.medicine_name,
            m.category,
            m.quantity AS stock_available,
            m.unit_price
        FROM PRESCRIPTION_ITEMS pi
        JOIN MEDICINE m ON pi.medicine_id = m.medicine_id
        WHERE pi.prescription_id = :id
        ORDER BY pi.item_id ASC
    """
    items = execute_query(items_sql, {"id": prescription_id}, fetchall=True)

    return render_template("prescriptions/detail.html", pres=prescription, items=items)


@prescription_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    patients = execute_query("SELECT patient_id, name, phone FROM PATIENT ORDER BY name ASC", fetchall=True)
    medicines = execute_query(
        """
        SELECT medicine_id, medicine_name, quantity, unit_price 
        FROM MEDICINE 
        WHERE expiry_date >= CURRENT_DATE
        ORDER BY medicine_name ASC
        """,
        fetchall=True
    )

    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        doctor_name = request.form.get("doctor_name", "").strip()
        diagnosis = request.form.get("diagnosis", "").strip()
        date_str = request.form.get("prescription_date", "").strip()
        notes = request.form.get("notes", "").strip()

        # Multi-item arrays
        med_ids = request.form.getlist("medicine_id[]")
        dosages = request.form.getlist("dosage[]")
        quantities = request.form.getlist("quantity[]")

        errors = []
        if not patient_id:
            errors.append("Please select a registered patient.")
        if not doctor_name:
            errors.append("Prescribing doctor name is required.")
        if not med_ids or len(med_ids) == 0:
            errors.append("At least one medicine item must be added to the prescription.")

        try:
            pres_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
        except ValueError:
            errors.append("Invalid prescription date format.")
            pres_date = datetime.now().date()

        valid_items = []
        for i in range(len(med_ids)):
            m_id = med_ids[i].strip()
            dosage = dosages[i].strip() if i < len(dosages) else ""
            q_str = quantities[i].strip() if i < len(quantities) else "1"

            if not m_id:
                continue
            if not dosage:
                errors.append(f"Item #{i+1}: Dosage instructions are required.")
            try:
                q = int(q_str)
                if q <= 0:
                    errors.append(f"Item #{i+1}: Prescribed quantity must be greater than zero.")
            except ValueError:
                errors.append(f"Item #{i+1}: Invalid quantity.")
                q = 1

            valid_items.append({"medicine_id": int(m_id), "dosage": dosage, "quantity": q})

        if not valid_items:
            errors.append("Please specify at least one valid medication line.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "prescriptions/form.html",
                patients=patients,
                medicines=medicines,
                form_data=request.form
            )

        # Atomic transaction insertion — PostgreSQL RETURNING clause
        try:
            with get_db_cursor(commit=True) as (conn, cursor):
                cursor.execute(
                    """
                    INSERT INTO PRESCRIPTION (patient_id, doctor_name, diagnosis, prescription_date, notes)
                    VALUES (%(pid)s, %(doc)s, %(diag)s, %(pdate)s, %(notes)s)
                    RETURNING prescription_id
                    """,
                    {
                        "pid": int(patient_id),
                        "doc": doctor_name,
                        "diag": diagnosis,
                        "pdate": pres_date,
                        "notes": notes,
                    }
                )
                new_pres_id = cursor.fetchone()["prescription_id"]

                for itm in valid_items:
                    cursor.execute(
                        """
                        INSERT INTO PRESCRIPTION_ITEMS (prescription_id, medicine_id, dosage, quantity)
                        VALUES (%(pres_id)s, %(med_id)s, %(dosage)s, %(qty)s)
                        """,
                        {
                            "pres_id": new_pres_id,
                            "med_id": itm["medicine_id"],
                            "dosage": itm["dosage"],
                            "qty": itm["quantity"]
                        }
                    )

            flash(f"Prescription #{new_pres_id} created successfully.", "success")
            return redirect(url_for("prescriptions.detail", prescription_id=new_pres_id))

        except Exception as e:
            flash(f"Error creating prescription: {e}", "danger")
            return render_template(
                "prescriptions/form.html",
                patients=patients,
                medicines=medicines,
                form_data=request.form
            )

    return render_template(
        "prescriptions/form.html",
        patients=patients,
        medicines=medicines,
        form_data={}
    )
