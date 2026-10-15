"""
Supplier Management Blueprint (routes/supplier_routes.py)
Hospital Pharmacy Management System (HPMS)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from auth import login_required
from db import execute_query

supplier_bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")


@supplier_bp.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()

    sql = """
        SELECT 
            s.supplier_id,
            s.supplier_name,
            s.contact_person,
            s.phone,
            s.email,
            s.address,
            s.created_at,
            (SELECT COUNT(*) FROM MEDICINE m WHERE m.supplier_id = s.supplier_id) AS total_medicines_supplied
        FROM SUPPLIER s
        WHERE 1 = 1
    """
    params = {}
    if search:
        sql += " AND (LOWER(s.supplier_name) LIKE :s OR LOWER(s.contact_person) LIKE :s OR LOWER(s.phone) LIKE :s)"
        params["s"] = f"%{search.lower()}%"

    sql += " ORDER BY s.supplier_name ASC"

    suppliers = execute_query(sql, params, fetchall=True)
    return render_template("suppliers/list.html", suppliers=suppliers, current_search=search)


@supplier_bp.route("/<int:supplier_id>")
@login_required
def detail(supplier_id):
    supplier = execute_query(
        """
        SELECT supplier_id, supplier_name, contact_person, phone, email, address, created_at
        FROM SUPPLIER
        WHERE supplier_id = :id
        """,
        {"id": supplier_id},
        fetchone=True
    )
    if not supplier:
        flash("Supplier not found.", "danger")
        return redirect(url_for("suppliers.index"))

    supplied_medicines = execute_query(
        """
        SELECT medicine_id, medicine_name, category, unit_price, quantity, batch_number, expiry_date
        FROM MEDICINE
        WHERE supplier_id = :id
        ORDER BY medicine_name ASC
        """,
        {"id": supplier_id},
        fetchall=True
    )

    return render_template(
        "suppliers/detail.html",
        supplier=supplier,
        medicines=supplied_medicines
    )


@supplier_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        supplier_name = request.form.get("supplier_name", "").strip()
        contact_person = request.form.get("contact_person", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        errors = []
        if not supplier_name:
            errors.append("Supplier name is required.")
        if not phone:
            errors.append("Phone number is required.")

        # Check unique supplier name
        existing = execute_query(
            "SELECT supplier_id FROM SUPPLIER WHERE LOWER(supplier_name) = LOWER(:name)",
            {"name": supplier_name},
            fetchone=True
        )
        if existing:
            errors.append(f"A supplier with name '{supplier_name}' already exists.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("suppliers/form.html", form_data=request.form, is_edit=False)

        execute_query(
            """
            INSERT INTO SUPPLIER (supplier_name, contact_person, phone, email, address)
            VALUES (:name, :contact, :phone, :email, :addr)
            """,
            {
                "name": supplier_name,
                "contact": contact_person,
                "phone": phone,
                "email": email,
                "addr": address
            },
            commit=True
        )
        flash(f"Supplier '{supplier_name}' registered successfully.", "success")
        return redirect(url_for("suppliers.index"))

    return render_template("suppliers/form.html", form_data={}, is_edit=False)


@supplier_bp.route("/<int:supplier_id>/edit", methods=["GET", "POST"])
@login_required
def edit(supplier_id):
    supplier = execute_query(
        "SELECT * FROM SUPPLIER WHERE supplier_id = :id",
        {"id": supplier_id},
        fetchone=True
    )
    if not supplier:
        flash("Supplier not found.", "danger")
        return redirect(url_for("suppliers.index"))

    if request.method == "POST":
        supplier_name = request.form.get("supplier_name", "").strip()
        contact_person = request.form.get("contact_person", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        errors = []
        if not supplier_name:
            errors.append("Supplier name is required.")
        if not phone:
            errors.append("Phone number is required.")

        existing = execute_query(
            "SELECT supplier_id FROM SUPPLIER WHERE LOWER(supplier_name) = LOWER(:name) AND supplier_id != :id",
            {"name": supplier_name, "id": supplier_id},
            fetchone=True
        )
        if existing:
            errors.append(f"Another supplier with name '{supplier_name}' already exists.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "suppliers/form.html",
                form_data=request.form,
                is_edit=True,
                supplier_id=supplier_id
            )

        execute_query(
            """
            UPDATE SUPPLIER SET
                supplier_name = :name,
                contact_person = :contact,
                phone = :phone,
                email = :email,
                address = :addr
            WHERE supplier_id = :id
            """,
            {
                "name": supplier_name,
                "contact": contact_person,
                "phone": phone,
                "email": email,
                "addr": address,
                "id": supplier_id
            },
            commit=True
        )
        flash(f"Supplier '{supplier_name}' updated successfully.", "success")
        return redirect(url_for("suppliers.detail", supplier_id=supplier_id))

    return render_template(
        "suppliers/form.html",
        form_data=supplier,
        is_edit=True,
        supplier_id=supplier_id
    )


@supplier_bp.route("/<int:supplier_id>/delete", methods=["POST"])
@login_required
def delete(supplier_id):
    # Check if supplier supplies medicines
    med_ref = execute_query(
        "SELECT COUNT(*) AS cnt FROM MEDICINE WHERE supplier_id = :id",
        {"id": supplier_id},
        fetchone=True
    )
    med_count = med_ref["cnt"] if med_ref else 0

    if med_count > 0:
        flash(
            f"Cannot delete supplier (ID: {supplier_id}) because {med_count} medicines are actively linked to this distributor. "
            f"Reassign or archive those products before removing this vendor.",
            "warning"
        )
        return redirect(url_for("suppliers.detail", supplier_id=supplier_id))

    try:
        execute_query("DELETE FROM SUPPLIER WHERE supplier_id = :id", {"id": supplier_id}, commit=True)
        flash("Supplier deleted safely.", "success")
        return redirect(url_for("suppliers.index"))
    except psycopg2.Error as e:
        flash(f"Database error deleting supplier: {e}", "danger")
        return redirect(url_for("suppliers.detail", supplier_id=supplier_id))
