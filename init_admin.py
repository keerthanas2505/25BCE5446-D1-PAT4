"""
Administrator Initialization Script (init_admin.py)
Hospital Pharmacy Management System (HPMS)
VIT Chennai DBMS PAT 4 Project

Safely provisions or resets administrator and pharmacist accounts in the Oracle APP_USERS table.
Uses Werkzeug PBKDF2/scrypt cryptographic password hashing. Plaintext passwords are NEVER stored.
"""

import sys
import argparse
import getpass
from werkzeug.security import generate_password_hash
from db import execute_query


def init_user(username, password, full_name, role, email=""):
    """
    Insert or update a user securely in the APP_USERS table.
    """
    role = role.upper()
    if role not in ("ADMIN", "PHARMACIST"):
        print(f"[!] Error: Role must be either ADMIN or PHARMACIST, got '{role}'.")
        return False

    password_hash = generate_password_hash(password)

    # Check if user already exists
    existing = execute_query(
        "SELECT user_id, username, role FROM APP_USERS WHERE username = :u",
        {"u": username},
        fetchone=True
    )

    if existing:
        print(f"[*] User '{username}' already exists. Updating password hash and full name...")
        execute_query(
            """
            UPDATE APP_USERS 
            SET password_hash = :p, full_name = :n, role = :r, email = :e, is_active = 1
            WHERE username = :u
            """,
            {"p": password_hash, "n": full_name, "r": role, "e": email, "u": username},
            commit=True
        )
        print(f"[+] User '{username}' successfully updated.")
    else:
        execute_query(
            """
            INSERT INTO APP_USERS (username, password_hash, full_name, role, email, is_active)
            VALUES (:u, :p, :n, :r, :e, 1)
            """,
            {"u": username, "p": password_hash, "n": full_name, "r": role, "e": email},
            commit=True
        )
        print(f"[+] User '{username}' with role '{role}' successfully created.")

    return True


def main():
    parser = argparse.ArgumentParser(description="Initialize HPMS application user accounts.")
    parser.add_argument("--username", help="Account username (e.g., admin)")
    parser.add_argument("--password", help="Account password (or omit to be prompted)")
    parser.add_argument("--name", help="Full display name (e.g., 'Chief Pharmacist')")
    parser.add_argument("--role", default="ADMIN", choices=["ADMIN", "PHARMACIST"], help="User role (ADMIN or PHARMACIST)")
    parser.add_argument("--email", default="", help="User email address")
    parser.add_argument("--demo", action="store_true", help="Create standard academic demo accounts (admin and pharmacist)")

    args = parser.parse_args()

    
    if args.demo:
        print("Demo account creation is disabled to prevent hardcoded credentials.")
        print("Run this script without --demo to create accounts interactively.")
        return

    username = args.username
    if not username:
        username = input("Enter username: ").strip()

    name = args.name
    if not name:
        name = input("Enter full name: ").strip()

    password = args.password
    if not password:
        password = getpass.getpass("Enter password: ").strip()
        confirm = getpass.getpass("Confirm password: ").strip()
        if password != confirm:
            print("[!] Passwords do not match.")
            sys.exit(1)

    init_user(username, password, name, args.role, args.email)


if __name__ == "__main__":
    main()
