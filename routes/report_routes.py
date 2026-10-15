"""
Reporting & Business Intelligence Blueprint (routes/report_routes.py)
Hospital Pharmacy Management System (HPMS)
"""

import csv
import io
from flask import Blueprint, render_template, request, Response
from auth import login_required
from db import execute_query

report_bp = Blueprint("reports", __name__, url_prefix="/reports")


@report_bp.route("/sales")
@login_required
def sales():
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    sql = """
        SELECT 
            b.bill_id,
            b.bill_number,
            b.customer_name,
            b.bill_date,
            b.subtotal,
            b.discount_pct,
            b.tax_pct,
            b.total_amount,
            b.payment_method,
            u.full_name AS billed_by
        FROM BILL b
        LEFT JOIN APP_USERS u ON b.created_by = u.user_id
        WHERE 1 = 1
    """
    params = {}

    if date_from:
        sql += " AND TRUNC(b.bill_date) >= TO_DATE(:dfrom, 'YYYY-MM-DD')"
        params["dfrom"] = date_from

    if date_to:
        sql += " AND TRUNC(b.bill_date) <= TO_DATE(:dto, 'YYYY-MM-DD')"
        params["dto"] = date_to

    sql += " ORDER BY b.bill_date DESC"

    bills = execute_query(sql, params, fetchall=True)

    # Aggregations
    total_sales_count = len(bills)
    total_revenue = sum(float(b["total_amount"]) for b in bills)
    avg_bill = (total_revenue / total_sales_count) if total_sales_count > 0 else 0.0

    # Best-selling medicines (Leaderboard View)
    best_sellers = execute_query(
        """
        SELECT 
            medicine_name,
            total_quantity_sold,
            total_revenue_generated,
            transaction_count
        FROM VW_TOP_SELLING_MEDICINES
        ORDER BY total_quantity_sold DESC
        LIMIT 8
        """,
        fetchall=True
    )

    # Monthly Trends View
    monthly_summary = execute_query(
        "SELECT * FROM VW_MONTHLY_SALES_SUMMARY ORDER BY sale_month DESC",
        fetchall=True
    )

    return render_template(
        "reports/sales.html",
        bills=bills,
        total_sales_count=total_sales_count,
        total_revenue=total_revenue,
        avg_bill=avg_bill,
        best_sellers=best_sellers,
        monthly_summary=monthly_summary,
        current_date_from=date_from,
        current_date_to=date_to
    )


@report_bp.route("/inventory")
@login_required
def inventory():
    category = request.args.get("category", "").strip()
    status_filter = request.args.get("status", "").strip()

    sql = """
        SELECT 
            medicine_id,
            medicine_name,
            category,
            batch_number,
            quantity,
            reorder_threshold,
            unit_price,
            expiry_date,
            days_to_expiry,
            stock_status,
            expiry_status,
            supplier_name
        FROM VW_INVENTORY_STATUS
        WHERE 1 = 1
    """
    params = {}

    if category:
        sql += " AND category = :cat"
        params["cat"] = category

    if status_filter == "low":
        sql += " AND stock_status IN ('LOW STOCK', 'OUT OF STOCK')"
    elif status_filter == "adequate":
        sql += " AND stock_status = 'ADEQUATE'"

    sql += " ORDER BY quantity ASC, medicine_name ASC"

    medicines = execute_query(sql, params, fetchall=True)

    # Totals
    total_items = len(medicines)
    total_val = sum(float(m["quantity"]) * float(m["unit_price"]) for m in medicines)

    categories = execute_query("SELECT DISTINCT category FROM MEDICINE ORDER BY category ASC", fetchall=True)

    return render_template(
        "reports/inventory.html",
        medicines=medicines,
        total_items=total_items,
        total_val=total_val,
        categories=[c["category"] for c in categories],
        current_category=category,
        current_status=status_filter
    )


@report_bp.route("/expiry")
@login_required
def expiry():
    """
    Expiry Risk Report: Highlights expired and expiring medicines within 60 days.
    """
    sql = """
        SELECT 
            m.medicine_id,
            m.medicine_name,
            m.category,
            m.batch_number,
            m.quantity,
            m.unit_price,
            m.expiry_date,
            ROUND(m.expiry_date - TRUNC(CURRENT_DATE)) AS days_remaining,
            s.supplier_name,
            s.phone AS supplier_phone,
            CASE 
                WHEN m.expiry_date < TRUNC(CURRENT_DATE) THEN 'EXPIRED'
                WHEN m.expiry_date <= TRUNC(CURRENT_DATE) + 30 THEN 'CRITICAL (< 30 Days)'
                ELSE 'WARNING (< 60 Days)'
            END AS risk_tier
        FROM MEDICINE m
        JOIN SUPPLIER s ON m.supplier_id = s.supplier_id
        WHERE m.expiry_date <= TRUNC(CURRENT_DATE) + 60
        ORDER BY m.expiry_date ASC, m.quantity DESC
    """
    risk_medicines = execute_query(sql, fetchall=True)

    expired_count = sum(1 for m in risk_medicines if m["days_remaining"] < 0)
    expiring_count = sum(1 for m in risk_medicines if m["days_remaining"] >= 0)

    return render_template(
        "reports/expiry.html",
        medicines=risk_medicines,
        expired_count=expired_count,
        expiring_count=expiring_count
    )


# ----------------------------------------------------------------------------
# CSV EXPORT ENDPOINTS
# ----------------------------------------------------------------------------
@report_bp.route("/export/sales.csv")
@login_required
def export_sales_csv():
    bills = execute_query(
        """
        SELECT b.bill_number, b.bill_date, b.customer_name, b.payment_method,
               b.subtotal, b.discount_pct, b.tax_pct, b.total_amount
        FROM BILL b
        ORDER BY b.bill_date DESC
        """,
        fetchall=True
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Invoice Number", "Date & Time", "Customer Name", "Payment Method",
        "Subtotal (INR)", "Discount (%)", "Tax (%)", "Final Total (INR)"
    ])

    for b in bills:
        writer.writerow([
            b["bill_number"],
            str(b["bill_date"]),
            b["customer_name"],
            b["payment_method"],
            f"{b['subtotal']:.2f}",
            f"{b['discount_pct']:.2f}",
            f"{b['tax_pct']:.2f}",
            f"{b['total_amount']:.2f}"
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=hpms_sales_report.csv"}
    )


@report_bp.route("/export/inventory.csv")
@login_required
def export_inventory_csv():
    items = execute_query(
        """
        SELECT medicine_name, category, batch_number, quantity, 
               reorder_threshold, unit_price, expiry_date, supplier_name, stock_status
        FROM VW_INVENTORY_STATUS
        ORDER BY medicine_name ASC
        """,
        fetchall=True
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Medicine Name", "Category", "Batch Number", "Current Stock",
        "Reorder Threshold", "Unit Price (INR)", "Expiry Date", "Supplier", "Stock Status"
    ])

    for i in items:
        writer.writerow([
            i["medicine_name"],
            i["category"],
            i["batch_number"],
            i["quantity"],
            i["reorder_threshold"],
            f"{i['unit_price']:.2f}",
            str(i["expiry_date"]),
            i["supplier_name"],
            i["stock_status"]
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=hpms_inventory_report.csv"}
    )
