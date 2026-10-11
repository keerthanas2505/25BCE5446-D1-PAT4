"""
Public Healthcare Portal Blueprint (routes/public_routes.py)
RxCare — Hospital Pharmacy Management System
Metropolitan Hospital Pharmacy Services

Provides customer and visitor facing healthcare pages:
- Public Home with pharmacy overview and safety principles
- Formulary & Medicine Catalog with patient-safe availability
- Patient Prescription Status Verification
- Clinical Pharmacy Services & Operations
- About Institutional Pharmacy & Quality Standards
- Responsible Medication Guide & Patient Support
- Hospital Contact & Emergency Dispensary Details
"""

from flask import Blueprint, render_template, request, flash
from db import execute_query

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    """
    Public Homepage: Welcome, core services, safety pledge, and quick navigation.
    Does not expose sensitive internal inventory valuations, revenues, or patient records.
    """
    # Fetch safe aggregate counts for public reassurance
    cat_res = execute_query(
        "SELECT COUNT(DISTINCT category) AS cnt FROM MEDICINE",
        fetchone=True
    )
    total_categories = cat_res["cnt"] if cat_res else 0

    med_res = execute_query(
        "SELECT COUNT(*) AS cnt FROM MEDICINE WHERE quantity > 0",
        fetchone=True
    )
    available_medicines = med_res["cnt"] if med_res else 0

    return render_template(
        "public/home.html",
        total_categories=total_categories,
        available_medicines=available_medicines
    )


@public_bp.route("/about")
def about():
    """
    Institutional background, clinical governance, and quality standards.
    """
    return render_template("public/about.html")


@public_bp.route("/services")
def services():
    """
    Hospital pharmacy services: Inpatient dispensing, outpatient counter,
    emergency formulary, clinical counseling, and unit-dose packaging.
    """
    return render_template("public/services.html")


@public_bp.route("/medicines/catalog")
def catalog():
    """
    Public Medication Formulary & Availability Directory.
    Enables patients and visitors to search essential hospital medicines.
    Displays patient retail pricing and availability status without exposing
    confidential supplier links, purchase costs, batch codes, or warehouse thresholds.
    """
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    sql = """
        SELECT medicine_id, medicine_name, category, description, unit_price, quantity
        FROM MEDICINE
        WHERE 1 = 1
    """
    params = {}

    if q:
        sql += " AND (LOWER(medicine_name) LIKE :q OR LOWER(description) LIKE :q)"
        params["q"] = f"%{q.lower()}%"

    if category:
        sql += " AND category = :cat"
        params["cat"] = category

    sql += " ORDER BY category ASC, medicine_name ASC"

    medicines = execute_query(sql, params, fetchall=True)

    # Categories list for filter dropdown
    categories = execute_query(
        "SELECT DISTINCT category FROM MEDICINE ORDER BY category ASC",
        fetchall=True
    )

    return render_template(
        "public/catalog.html",
        medicines=medicines,
        categories=categories,
        search_query=q,
        selected_category=category
    )


@public_bp.route("/prescriptions/guide")
def guide():
    """
    Educational prescription support and safe medication management guide.
    """
    return render_template("public/guide.html")


@public_bp.route("/contact")
def contact():
    """
    Hospital pharmacy location, dispensary hours, and department phone directory.
    Uses authentic project location: Metropolitan Hospital Pharmacy, VIT Chennai Campus Health Facility.
    """
    return render_template("public/contact.html")


@public_bp.route("/patient/lookup", methods=["GET", "POST"])
def lookup():
    """
    Customer Prescription Verification & Status Checker.
    Enables patients to verify the fulfillment status of their hospital prescriptions
    using either their Prescription Number or Registered Contact Phone Number.
    Strictly read-only; displays safe dispensing status and dosage guidelines.
    """
    results = None
    searched = False
    query_val = ""
    query_type = "rx_number"

    if request.method == "POST":
        searched = True
        query_val = request.form.get("query_val", "").strip()
        query_type = request.form.get("query_type", "rx_number")

        if not query_val:
            flash("Please enter a Prescription ID or Registered Phone Number.", "warning")
            return render_template("public/lookup.html", results=None, searched=False)

        if query_type == "rx_number":
            # Search by numeric prescription ID
            if not query_val.isdigit():
                flash("Prescription ID must be a numeric reference number.", "danger")
                return render_template("public/lookup.html", results=None, searched=True, query_val=query_val, query_type=query_type)

            prescriptions = execute_query(
                """
                SELECT p.prescription_id, p.doctor_name, p.diagnosis, p.prescription_date,
                       p.notes, pt.name AS patient_name, pt.phone AS contact_number
                FROM PRESCRIPTION p
                JOIN PATIENT pt ON p.patient_id = pt.patient_id
                WHERE p.prescription_id = :pid
                ORDER BY p.prescription_date DESC
                """,
                {"pid": int(query_val)},
                fetchall=True
            )
        else:
            # Search by contact phone number (supports exact, partial, and stripped formats)
            clean_digits = "".join(ch for ch in query_val if ch.isdigit())
            prescriptions = execute_query(
                """
                SELECT p.prescription_id, p.doctor_name, p.diagnosis, p.prescription_date,
                       p.notes, pt.name AS patient_name, pt.phone AS contact_number
                FROM PRESCRIPTION p
                JOIN PATIENT pt ON p.patient_id = pt.patient_id
                WHERE pt.phone = :phone 
                   OR pt.phone LIKE :phone_like
                   OR (LENGTH(:digits) >= 6 AND REPLACE(REPLACE(pt.phone, ' ', ''), '-', '') LIKE :digits_like)
                ORDER BY p.prescription_date DESC
                """,
                {
                    "phone": query_val,
                    "phone_like": f"%{query_val}%",
                    "digits": clean_digits,
                    "digits_like": f"%{clean_digits}%"
                },
                fetchall=True
            )

        # For each found prescription, safely fetch items
        enriched_results = []
        for rx in (prescriptions or []):
            items = execute_query(
                """
                SELECT m.medicine_name, m.category, pi.dosage, pi.quantity
                FROM PRESCRIPTION_ITEMS pi
                JOIN MEDICINE m ON pi.medicine_id = m.medicine_id
                WHERE pi.prescription_id = :pid
                ORDER BY pi.item_id ASC
                """,
                {"pid": rx["prescription_id"]},
                fetchall=True
            )
            rx_dict = dict(rx)
            rx_dict["medications"] = items or []
            enriched_results.append(rx_dict)

        results = enriched_results

    return render_template(
        "public/lookup.html",
        results=results,
        searched=searched,
        query_val=query_val,
        query_type=query_type
    )
