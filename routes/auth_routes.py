"""
Authentication & User Management Blueprint (routes/auth_routes.py)
Hospital Pharmacy Management System (HPMS)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from auth import login_user, logout_user, login_required, admin_required
from db import execute_query

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html", username=username)

        success, result = login_user(username, password)
        if success:
            flash(f"Welcome back, {result['full_name']} ({result['role']})!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.index"))
        else:
            flash(result, "danger")
            return render_template("login.html", username=username)

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/users")
@admin_required
def users_list():
    users = execute_query(
        """
        SELECT user_id, username, full_name, role, email, is_active, created_at
        FROM APP_USERS
        ORDER BY user_id ASC
        """,
        fetchall=True
    )
    return render_template("users.html", users=users)


@auth_bp.route("/users/add", methods=["POST"])
@admin_required
def add_user():
    username = request.form.get("username", "").strip()
    full_name = request.form.get("full_name", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "PHARMACIST").upper()
    email = request.form.get("email", "").strip()

    if not username or not full_name or not password:
        flash("Username, Full Name, and Password are required.", "danger")
        return redirect(url_for("auth.users_list"))

    if role not in ("ADMIN", "PHARMACIST"):
        flash("Invalid role specified.", "danger")
        return redirect(url_for("auth.users_list"))

    # Check username uniqueness
    existing = execute_query(
        "SELECT user_id FROM APP_USERS WHERE username = :u",
        {"u": username},
        fetchone=True
    )
    if existing:
        flash(f"Username '{username}' is already in use.", "danger")
        return redirect(url_for("auth.users_list"))

    password_hash = generate_password_hash(password)
    execute_query(
        """
        INSERT INTO APP_USERS (username, password_hash, full_name, role, email, is_active)
        VALUES (:u, :p, :n, :r, :e, 1)
        """,
        {"u": username, "p": password_hash, "n": full_name, "r": role, "e": email},
        commit=True
    )
    flash(f"User '{username}' created successfully.", "success")
    return redirect(url_for("auth.users_list"))


@auth_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    if user_id == session.get("user_id"):
        flash("You cannot deactivate your own active account.", "warning")
        return redirect(url_for("auth.users_list"))

    user = execute_query("SELECT is_active, username FROM APP_USERS WHERE user_id = :usr_id", {"usr_id": user_id}, fetchone=True)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.users_list"))

    new_status = 0 if user["is_active"] == 1 else 1
    execute_query(
        "UPDATE APP_USERS SET is_active = :s WHERE user_id = :usr_id",
        {"s": new_status, "usr_id": user_id},
        commit=True
    )
    status_label = "activated" if new_status == 1 else "deactivated"
    flash(f"User '{user['username']}' has been {status_label}.", "info")
    return redirect(url_for("auth.users_list"))
