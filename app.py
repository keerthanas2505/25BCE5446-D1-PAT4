"""
Hospital Pharmacy Management System (HPMS)
Main Application Entry Point (app.py)
VIT Chennai DBMS PAT 4 Project

Full-Stack Flask application backed by Oracle Database XE 21c (XEPDB1).
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, abort
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.medicine_routes import medicine_bp
from routes.supplier_routes import supplier_bp
from routes.patient_routes import patient_bp
from routes.prescription_routes import prescription_bp
from routes.public_routes import public_bp
from routes.billing_routes import billing_bp
from routes.report_routes import report_bp
from auth import get_current_user, generate_csrf_token

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HPMS")


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "vit-chennai-dbms-pat4-hpms-default-key")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    lifetime_minutes = int(os.getenv("PERMANENT_SESSION_LIFETIME_MINUTES", "60"))
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=lifetime_minutes)

    # Register Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(medicine_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(report_bp)

    # Context Processors (available across all templates)
    @app.context_processor
    def inject_globals():
        user = None
        if session.get("user_id"):
            user = {
                "user_id": session.get("user_id"),
                "username": session.get("username"),
                "full_name": session.get("full_name"),
                "role": session.get("role")
            }
        return {
            "current_user": user,
            "csrf_token": generate_csrf_token,
            "now": datetime.now()
        }

    # CSRF Protection Hook for mutating requests
    @app.before_request
    def check_csrf():
        # Ensure session csrf token is present
        generate_csrf_token()

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Exclude login endpoint from strict before_request check
            # (token is initialized on first get and checked)
            if request.endpoint == "auth.login":
                return
            
            token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            session_token = session.get("csrf_token")
            if not token or token != session_token:
                logger.warning(f"CSRF validation failed for {request.path}")
                abort(400, description="Security Error: CSRF token verification failed.")

    # Custom Jinja Filters
    @app.template_filter("currency")
    def currency_filter(value):
        try:
            return f"₹ {float(value):,.2f}"
        except (ValueError, TypeError):
            return "₹ 0.00"

    @app.template_filter("format_date")
    def format_date_filter(value):
        if not value:
            return "N/A"
        if isinstance(value, str):
            try:
                dt = datetime.strptime(value[:10], "%Y-%m-%d")
                return dt.strftime("%d-%b-%Y")
            except Exception:
                return value
        if hasattr(value, "strftime"):
            return value.strftime("%d-%b-%Y")
        return str(value)

    # Custom Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html", description=error.description), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f">> Launching Hospital Pharmacy Management System on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug_mode)
