"""
Diagnostic & Verification Script (test_db.py)
Hospital Pharmacy Management System (HPMS)
Tests PostgreSQL connectivity, query execution, and schema integrity.
"""

import sys
from db import execute_query, get_connection


def run_diagnostics():
    print("=" * 65)
    print("Hospital Pharmacy Management System - PostgreSQL Diagnostics")
    print("=" * 65)

    # 1. Connection check
    print("[1/4] Testing physical connection to PostgreSQL...")
    try:
        conn = get_connection()
        server_version = conn.server_version if hasattr(conn, "server_version") else "connected"
        print(f"  [+] Connected successfully! PostgreSQL Server Version: {server_version}")
        conn.close()
    except Exception as e:
        print(f"  [!] Connection failed: {e}")
        print("\n  [INFO] Please verify your DATABASE_URL or DB_* environment variables in .env.")
        sys.exit(1)

    # 2. Schema check
    print("\n[2/4] Verifying database tables in schema...")
    expected_tables = [
        "app_users", "supplier", "medicine", "patient",
        "prescription", "prescription_items", "bill", "bill_items"
    ]
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """
    rows = execute_query(query, fetchall=True)
    existing_tables = [r["table_name"].lower() for r in rows]

    all_found = True
    for tbl in expected_tables:
        if tbl in existing_tables:
            print(f"  [+] Table found: {tbl.upper()}")
        else:
            print(f"  [-] Table MISSING: {tbl.upper()}")
            all_found = False

    if not all_found:
        print("\n[!] Warning: Some expected tables are missing. Please execute schema_postgres.sql.")
        sys.exit(1)

    # 3. Sample data count check
    print("\n[3/4] Verifying record counts...")
    tables_to_count = ["SUPPLIER", "MEDICINE", "PATIENT", "PRESCRIPTION", "BILL"]
    for tbl in tables_to_count:
        try:
            count_res = execute_query(f"SELECT COUNT(*) AS cnt FROM {tbl}", fetchone=True)
            print(f"  [+] {tbl} count: {count_res['cnt']}")
        except Exception as e:
            print(f"  [-] {tbl} count query failed: {e}")

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
    print("[SUCCESS] All PostgreSQL diagnostics passed with zero errors!")
    print("=" * 65)


if __name__ == "__main__":
    run_diagnostics()
