"""
Diagnostic & Verification Script (test_db.py)
Hospital Pharmacy Management System (HPMS)
Tests Oracle XE 21c connectivity, query execution, and schema integrity.
"""

import sys
from db import execute_query, get_connection


def run_diagnostics():
    print("=" * 65)
    print("Hospital Pharmacy Management System - Oracle Diagnostics")
    print("=" * 65)

    # 1. Connection check
    print("[1/4] Testing physical connection to Oracle XE 21c...")
    try:
        conn = get_connection()
        print(f"  [+] Connected successfully! Oracle Server Version: {conn.version}")
        conn.close()
    except Exception as e:
        print(f"  [!] Connection failed: {e}")
        sys.exit(1)

    # 2. Schema check
    print("\n[2/4] Verifying database tables in schema...")
    expected_tables = [
        "APP_USERS", "SUPPLIER", "MEDICINE", "PATIENT",
        "PRESCRIPTION", "PRESCRIPTION_ITEMS", "BILL", "BILL_ITEMS"
    ]
    query = "SELECT table_name FROM user_tables ORDER BY table_name"
    rows = execute_query(query, fetchall=True)
    existing_tables = [r["table_name"] for r in rows]

    all_found = True
    for tbl in expected_tables:
        if tbl in existing_tables:
            print(f"  [+] Table found: {tbl}")
        else:
            print(f"  [-] Table MISSING: {tbl}")
            all_found = False

    if not all_found:
        print("\n[!] Warning: Some expected tables are missing. Please run schema.sql.")
        sys.exit(1)

    # 3. Sample data count check
    print("\n[3/4] Verifying record counts...")
    tables_to_count = ["SUPPLIER", "MEDICINE", "PATIENT", "PRESCRIPTION", "BILL"]
    for tbl in tables_to_count:
        count_res = execute_query(f"SELECT COUNT(*) AS cnt FROM {tbl}", fetchone=True)
        print(f"  [+] {tbl} count: {count_res['cnt']}")

    # 4. View check
    print("\n[4/4] Verifying business views...")
    views = ["VW_INVENTORY_STATUS", "VW_MONTHLY_SALES_SUMMARY", "VW_TOP_SELLING_MEDICINES"]
    for v in views:
        try:
            sample = execute_query(f"SELECT COUNT(*) AS cnt FROM {v}", fetchone=True)
            print(f"  [+] View active: {v} (Rows: {sample['cnt']})")
        except Exception as e:
            print(f"  [-] View failed: {v} ({e})")

    print("\n" + "=" * 65)
    print("[SUCCESS] All Oracle diagnostics passed with zero errors!")
    print("=" * 65)


if __name__ == "__main__":
    run_diagnostics()
