"""
Patient Management Blueprint (routes/patient_routes.py)
Hospital Pharmacy Management System (HPMS)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from auth import login_required
from db import execute_query

patient_bp = Blueprint("patients", __name__, url_prefix="/patients")


@patient_bp.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()

    sql = """
        SELECT 
            p.patient_id,
            p.name,
            p.age,
            p.gender,
            p.phone,
            p.address,
            p.created_at,
            (SELECT COUNT(*) FROM PRESCRIPTION pr WHERE pr.patient_id = p.patient_id) AS total_prescriptions,
            (SELECT COUNT(*) FROM BILL b WHERE b.patient_id = p.patient_id) AS total_bills
        FROM PATIENT p
        WHERE 1 = 1
    """
    params = {}
    if search:
        sql += " AND (LOWER(p.name) LIKE :s OR LOWER(p.phone) LIKE :s OR CAST(p.patient_id AS TEXT) = :s_exact)"
        params["s"] = f"%{search.lower()}%"
        params["s_exact"] = search

    sql += " ORDER BY p.name ASC"

    patients = execute_query(sql, params, fetchall=True)
    return render_template("patients/list.html", patients=patients, current_search=search)


@patient_bp.route("/<int:patient_id>")
@login_required
def detail(patient_id):
    patient = execute_query(
        "SELECT * FROM PATIENT WHERE patient_id = :id",
        {"id": patient_id},
        fetchone=True
    )
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.index"))

    # Prescriptions history
    prescriptions = execute_query(
        """
        SELECT prescription_id, doctor_name, diagnosis, prescription_date, notes
        FROM PRESCRIPTION
        WHERE patient_id = :id
        ORDER BY prescription_date DESC
        """,
        {"id": patient_id},
        fetchall=True
    )

    # Billing history
    bills = execute_query(
        """
        SELECT bill_id, bill_number, bill_date, total_amount, payment_method
        FROM BILL
        WHERE patient_id = :id
        ORDER BY bill_date DESC
        """,
        {"id": patient_id},
        fetchall=True
    )

    return render_template(
        "patients/detail.html",
        patient=patient,
        prescriptions=prescriptions,
        bills=bills
    )


@patient_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age_str = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        errors = []
        if not name:
            errors.append("Patient name is required.")
        if not phone:
            errors.append("Phone number is required.")
        if gender not in ("Male", "Female", "Other"):
            errors.append("Gender must be Male, Female, or Other.")

        try:
            age = int(age_str)
            if age < 0 or age > 130:
                errors.append("Age must be between 0 and 130.")
        except ValueError:
            errors.append("Valid age number is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("patients/form.html", form_data=request.form, is_edit=False)

        execute_query(
            """
            INSERT INTO PATIENT (name, age, gender, phone, address)
            VALUES (:name, :age, :gender, :phone, :addr)
            """,
            {"name": name, "age": age, "gender": gender, "phone": phone, "addr": address},
            commit=True
        )
        flash(f"Patient '{name}' registered successfully.", "success")
        return redirect(url_for("patients.index"))

    return render_template("patients/form.html", form_data={}, is_edit=False)


@patient_bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
def edit(patient_id):
    patient = execute_query("SELECT * FROM PATIENT WHERE patient_id = :id", {"id": patient_id}, fetchone=True)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age_str = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        errors = []
        if not name:
            errors.append("Patient name is required.")
        if not phone:
            errors.append("Phone number is required.")
        if gender not in ("Male", "Female", "Other"):
            errors.append("Gender must be Male, Female, or Other.")

        try:
            age = int(age_str)
            if age < 0 or age > 130:
                errors.append("Age must be between 0 and 130.")
        except ValueError:
            errors.append("Valid age number is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("patients/form.html", form_data=request.form, is_edit=True, patient_id=patient_id)

        execute_query(
            """
            UPDATE PATIENT SET
                name = :name,
                age = :age,
                gender = :gender,
                phone = :phone,
                address = :addr
            WHERE patient_id = :id
            """,
            {"name": name, "age": age, "gender": gender, "phone": phone, "addr": address, "id": patient_id},
            commit=True
        )
        flash(f"Patient '{name}' profile updated successfully.", "success")
        return redirect(url_for("patients.detail", patient_id=patient_id))

    return render_template("patients/form.html", form_data=patient, is_edit=True, patient_id=patient_id)


@patient_bp.route("/<int:patient_id>/delete", methods=["POST"])
@login_required
def delete(patient_id):
    # Check references
    pres_ref = execute_query(
        "SELECT COUNT(*) AS cnt FROM PRESCRIPTION WHERE patient_id = :id",
        {"id": patient_id},
        fetchone=True
    )
    bill_ref = execute_query(
        "SELECT COUNT(*) AS cnt FROM BILL WHERE patient_id = :id",
        {"id": patient_id},
        fetchone=True
    )
    p_cnt = pres_ref["cnt"] if pres_ref else 0
    b_cnt = bill_ref["cnt"] if bill_ref else 0

    if p_cnt > 0 or b_cnt > 0:
        flash(
            f"Cannot delete patient (ID: {patient_id}) because {p_cnt} prescriptions and {b_cnt} billing invoices "
            f"are associated with this record. Medical history and accounting records cannot be orphaned.",
            "warning"
        )
        return redirect(url_for("patients.detail", patient_id=patient_id))

    try:
        execute_query("DELETE FROM PATIENT WHERE patient_id = :id", {"id": patient_id}, commit=True)
        flash("Patient record deleted safely.", "success")
        return redirect(url_for("patients.index"))
    except psycopg2.Error as e:
        flash(f"Database error deleting patient: {e}", "danger")
        return redirect(url_for("patients.detail", patient_id=patient_id))
