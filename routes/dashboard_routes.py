"""
Dashboard Analytics Blueprint (routes/dashboard_routes.py)
Hospital Pharmacy Management System (HPMS)
"""

from flask import Blueprint, render_template
from auth import login_required
from db import execute_query

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    # 1. Total Medicines
    res = execute_query("SELECT COUNT(*) AS cnt FROM MEDICINE", fetchone=True)
    total_medicines = res["cnt"] if res else 0

    # 2. Total Suppliers
    res = execute_query("SELECT COUNT(*) AS cnt FROM SUPPLIER", fetchone=True)
    total_suppliers = res["cnt"] if res else 0

    # 3. Total Patients
    res = execute_query("SELECT COUNT(*) AS cnt FROM PATIENT", fetchone=True)
    total_patients = res["cnt"] if res else 0

    # 4. Today's Sales
    res = execute_query(
        """
        SELECT NVL(SUM(total_amount), 0) AS total, COUNT(bill_id) AS cnt
        FROM BILL
        WHERE TRUNC(bill_date) = TRUNC(CURRENT_DATE)
        """,
        fetchone=True
    )
    today_sales_amount = float(res["total"]) if res else 0.0
    today_sales_count = res["cnt"] if res else 0

    # 5. Low-stock Medicines
    res = execute_query(
        "SELECT COUNT(*) AS cnt FROM MEDICINE WHERE quantity <= reorder_threshold",
        fetchone=True
    )
    low_stock_count = res["cnt"] if res else 0

    # 6. Expired Medicines
    res = execute_query(
        "SELECT COUNT(*) AS cnt FROM MEDICINE WHERE expiry_date < TRUNC(CURRENT_DATE)",
        fetchone=True
    )
    expired_count = res["cnt"] if res else 0

    # 7. Medicines Approaching Expiry (within 60 days)
    res = execute_query(
        """
        SELECT COUNT(*) AS cnt 
        FROM MEDICINE 
        WHERE expiry_date >= TRUNC(CURRENT_DATE) 
          AND expiry_date <= TRUNC(CURRENT_DATE) + 60
        """,
        fetchone=True
    )
    near_expiry_count = res["cnt"] if res else 0

    # 8. Current Total Inventory Valuation
    res = execute_query(
        "SELECT NVL(SUM(quantity * unit_price), 0) AS val FROM MEDICINE",
        fetchone=True
    )
    inventory_value = float(res["val"]) if res else 0.0

    # 9. Recent Sales Invoices
    recent_bills = execute_query(
        """
        SELECT bill_id, bill_number, customer_name, total_amount, payment_method, bill_date
        FROM BILL
        ORDER BY bill_date DESC
        FETCH FIRST 5 ROWS ONLY
        """,
        fetchall=True
    )

    # 10. Urgent Stock / Expiry Alerts Table
    critical_medicines = execute_query(
        """
        SELECT m.medicine_id, m.medicine_name, m.category, m.quantity, 
               m.reorder_threshold, m.expiry_date, s.supplier_name,
               CASE 
                   WHEN m.expiry_date < TRUNC(CURRENT_DATE) THEN 'EXPIRED'
                   WHEN m.quantity = 0 THEN 'OUT OF STOCK'
                   WHEN m.quantity <= m.reorder_threshold THEN 'LOW STOCK'
                   WHEN m.expiry_date <= TRUNC(CURRENT_DATE) + 60 THEN 'EXPIRING SOON'
                   ELSE 'OK'
               END AS alert_status
        FROM MEDICINE m
        JOIN SUPPLIER s ON m.supplier_id = s.supplier_id
        WHERE m.quantity <= m.reorder_threshold 
           OR m.expiry_date <= TRUNC(CURRENT_DATE) + 60
        ORDER BY m.quantity ASC, m.expiry_date ASC
        FETCH FIRST 6 ROWS ONLY
        """,
        fetchall=True
    )

    stats = {
        "total_medicines": total_medicines,
        "total_suppliers": total_suppliers,
        "total_patients": total_patients,
        "today_sales_amount": today_sales_amount,
        "today_sales_count": today_sales_count,
        "low_stock_count": low_stock_count,
        "expired_count": expired_count,
        "near_expiry_count": near_expiry_count,
        "inventory_value": inventory_value,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_bills=recent_bills,
        critical_medicines=critical_medicines
    )
