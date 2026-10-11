"""
Authentication & Authorization Security Module (auth.py)
Hospital Pharmacy Management System (HPMS)
VIT Chennai DBMS PAT 4 Project

Implements password verification, session authentication decorators,
role-based access control (Admin / Pharmacist), and CSRF protection.
"""

import functools
import secrets
from flask import session, redirect, url_for, flash, request, abort
from werkzeug.security import check_password_hash
from db import execute_query


def get_current_user():
    """
    Retrieve current logged-in user dictionary from database or None.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = execute_query(
        """
        SELECT user_id, username, full_name, role, email, is_active
        FROM APP_USERS
        WHERE user_id = :usr_id AND is_active = 1
        """,
        {"usr_id": user_id},
        fetchone=True
    )
    return user


def login_user(username, password):
    """
    Verify user credentials against Oracle APP_USERS table using secure password hashing.
    Returns (success_bool, user_dict_or_error_str)
    """
    user = execute_query(
        """
        SELECT user_id, username, password_hash, full_name, role, email, is_active
        FROM APP_USERS
        WHERE username = :u
        """,
        {"u": username.strip()},
        fetchone=True
    )

    if not user:
        return False, "Invalid username or password."

    if user["is_active"] != 1:
        return False, "This account is inactive. Please contact the administrator."

    if not check_password_hash(user["password_hash"], password):
        return False, "Invalid username or password."

    # Establish session
    session.clear()
    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]
    session["role"] = user["role"]
    session["csrf_token"] = secrets.token_hex(32)

    return True, user


def logout_user():
    """
    Clear session and log out the user.
    """
    session.clear()


def login_required(view):
    """
    Decorator requiring an active authenticated user session.
    """
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    """
    Decorator requiring ADMIN role privileges.
    """
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        if session.get("role") != "ADMIN":
            flash("Access denied: Administrative privileges required for this action.", "danger")
            return redirect(url_for("dashboard.index"))
        return view(*args, **kwargs)
    return wrapped_view


def generate_csrf_token():
    """
    Generate or retrieve the session CSRF token.
    """
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf():
    """
    Validate CSRF token on mutating HTTP methods.
    Checks form data or 'X-CSRFToken' request header.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # Allow login route to validate its own CSRF token
        expected = session.get("csrf_token")
        received = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        if not expected or not received or expected != received:
            abort(400, description="Invalid or missing CSRF token.")
