"""
End-to-End Test Suite (test_app.py)
Hospital Pharmacy Management System (HPMS)
VIT Chennai DBMS PAT 4 Project

Tests authentication, role authorization, medicine inventory CRUD,
prescription workflows, atomic billing transactions, stock deduction,
rejection on insufficient inventory, reports, and CSV downloads.
"""

import unittest
from datetime import datetime
from app import app
from db import execute_query


class HPMSEndToEndTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_01_unauthenticated_redirect(self):
        """Unauthenticated user accessing protected route must be redirected to /login"""
        response = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_02_login_invalid_credentials(self):
        """Invalid username or password must fail"""
        response = self.client.post("/login", data={
            "username": "nonexistent_user",
            "password": "wrong_password"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

    
    def test_03_login_admin_success(self):
        """Valid admin credentials must authenticate and open session"""
        self.skipTest(
            "Skipped because this test uses a hardcoded demo password."
        )


    def test_04_dashboard_oracle_metrics(self):
        """Dashboard must render live numbers from Oracle Database"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "ADMIN"
            sess["full_name"] = "Dr. Vikram Sharma"
            sess["csrf_token"] = "test_token_123"

        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Total Medicines", response.data)
        self.assertIn(b"Today's Revenue", response.data)
        self.assertIn(b"Inventory Value", response.data)
        self.assertIn(b"Oracle XE 21c (XEPDB1) Online", response.data)

    def test_05_medicine_inventory_and_api(self):
        """Test medicine list, detail, and JSON API endpoint"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "ADMIN"
            sess["full_name"] = "Dr. Vikram Sharma"
            sess["csrf_token"] = "test_token_123"

        # List view
        response = self.client.get("/medicines/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Medicine Inventory & Formulary", response.data)

        # JSON API for medicine ID 1 (Paracetamol)
        api_res = self.client.get("/billing/api/medicine/1")
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertIn("medicine_name", data)
        self.assertIn("unit_price", data)
        self.assertIn("quantity", data)
        self.assertEqual(data["medicine_id"], 1)

    def test_06_atomic_billing_transaction_success(self):
        """Test full multi-item billing transaction with stock reduction in Oracle"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "ADMIN"
            sess["full_name"] = "Dr. Vikram Sharma"
            sess["csrf_token"] = "test_token_123"

        # Check pre-transaction stock for Medicine #1 (Paracetamol)
        pre_med = execute_query("SELECT quantity, unit_price FROM MEDICINE WHERE medicine_id = 1", fetchone=True)
        initial_stock = pre_med["quantity"]
        unit_price = pre_med["unit_price"]

        qty_to_buy = 2

        # Post sale to billing
        response = self.client.post("/billing/new", data={
            "csrf_token": "test_token_123",
            "customer_type": "walkin",
            "walkin_name": "Automated Test Patient",
            "payment_method": "UPI",
            "discount_pct": "5.0",
            "tax_pct": "0.0",
            "medicine_id[]": ["1"],
            "quantity[]": [str(qty_to_buy)]
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"METROPOLITAN HOSPITAL PHARMACY", response.data)
        self.assertIn(b"Automated Test Patient", response.data)

        # Check post-transaction stock
        post_med = execute_query("SELECT quantity FROM MEDICINE WHERE medicine_id = 1", fetchone=True)
        self.assertEqual(post_med["quantity"], initial_stock - qty_to_buy)

    def test_07_insufficient_stock_rejection(self):
        """Transaction must reject and roll back when requested quantity exceeds available stock"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "ADMIN"
            sess["full_name"] = "Dr. Vikram Sharma"
            sess["csrf_token"] = "test_token_123"

        # Medicine 10 has only 2 units in stock
        med = execute_query("SELECT quantity FROM MEDICINE WHERE medicine_id = 10", fetchone=True)
        stock = med["quantity"]

        response = self.client.post("/billing/new", data={
            "csrf_token": "test_token_123",
            "customer_type": "walkin",
            "walkin_name": "Test Oversell Attempt",
            "payment_method": "CASH",
            "discount_pct": "0",
            "tax_pct": "0",
            "medicine_id[]": ["10"],
            "quantity[]": [str(stock + 50)]  # Request far more than available
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Insufficient Inventory", response.data)

        # Confirm stock was untouched
        post_med = execute_query("SELECT quantity FROM MEDICINE WHERE medicine_id = 10", fetchone=True)
        self.assertEqual(post_med["quantity"], stock)

    def test_08_reports_and_csv_export(self):
        """Test sales reports, inventory valuation, and CSV file exports"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "ADMIN"
            sess["full_name"] = "Dr. Vikram Sharma"
            sess["csrf_token"] = "test_token_123"

        # Sales Report
        rep_sales = self.client.get("/reports/sales")
        self.assertEqual(rep_sales.status_code, 200)
        self.assertIn(b"Pharmacy Sales Intelligence", rep_sales.data)

        # Inventory Report
        rep_inv = self.client.get("/reports/inventory")
        self.assertEqual(rep_inv.status_code, 200)
        self.assertIn(b"Pharmacy Stock Valuation", rep_inv.data)

        # Expiry Report
        rep_exp = self.client.get("/reports/expiry")
        self.assertEqual(rep_exp.status_code, 200)
        self.assertIn(b"Medication Expiration & Quality Assurance Alerts", rep_exp.data)

        # CSV Export
        csv_res = self.client.get("/reports/export/sales.csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, "text/csv")
        self.assertIn(b"Invoice Number,Date & Time", csv_res.data)

    def test_09_role_authorization_restriction(self):
        """Pharmacist role must be blocked from accessing /users admin panel"""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "pharmacist"
            sess["role"] = "PHARMACIST"
            sess["full_name"] = "Kavitha Raj"
            sess["csrf_token"] = "test_token_123"

        response = self.client.get("/users", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access denied: Administrative privileges required", response.data)

    def test_10_public_homepage(self):
        """Public homepage must be accessible without authentication"""
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your Health, Our Priority", response.data)
        self.assertIn(b"RxCare", response.data)
        self.assertIn(b"Metropolitan Hospital Clinical Pharmacy", response.data)

    def test_11_public_catalog(self):
        """Public medicine formulary must be accessible without authentication"""
        response = self.client.get("/medicines/catalog")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hospital Formulary", response.data)

    def test_12_public_catalog_search(self):
        """Catalog search must return filtered results from Oracle"""
        response = self.client.get("/medicines/catalog?q=para")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Searching:", response.data)

    def test_13_public_guide(self):
        """Prescription guide must be publicly accessible"""
        response = self.client.get("/prescriptions/guide")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prescription Guide", response.data)
        self.assertIn(b"Safe Medication", response.data)

    def test_14_public_lookup_get(self):
        """Patient lookup page must be accessible without authentication"""
        response = self.client.get("/patient/lookup")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prescription Verification", response.data)

    def test_15_public_lookup_valid_prescription(self):
        """Patient lookup must return result for a valid prescription ID"""
        # First GET to ensure CSRF token is created in session
        self.client.get("/patient/lookup")
        with self.client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "test_csrf")

        response = self.client.post("/patient/lookup", data={
            "csrf_token": csrf,
            "query_type": "rx_number",
            "query_val": "1"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should render the lookup page with results or empty state, not 500
        self.assertIn(b"Prescription Verification", response.data)

    def test_16_public_about_and_services(self):
        """About and Services pages must be publicly accessible"""
        about = self.client.get("/about")
        self.assertEqual(about.status_code, 200)
        self.assertIn(b"Metropolitan Hospital", about.data)

        services = self.client.get("/services")
        self.assertEqual(services.status_code, 200)
        self.assertIn(b"Hospital Pharmacy Services", services.data)

    def test_17_public_contact(self):
        """Contact page must display authentic pharmacy contact details"""
        response = self.client.get("/contact")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"pharmacy@metropolitanhospital.org", response.data)
        self.assertIn(b"+91 44 3993 1555", response.data)

    def test_18_dashboard_still_redirects_after_redesign(self):
        """Dashboard must still redirect unauthenticated users to /login"""
        response = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_19_login_page_has_rxcare_branding(self):
        """Login page must carry RxCare branding"""
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"rxcare-logo.svg", response.data)
        self.assertIn(b"Staff Portal Sign In", response.data)
        self.assertIn(b"Return to RxCare", response.data)

    def test_20_public_catalog_category_filter(self):
        """Public catalog must filter by therapeutic category"""
        response = self.client.get("/medicines/catalog?category=Antibiotic")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Antibiotic", response.data)

    def test_21_public_catalog_empty_results(self):
        """Catalog search for nonexistent drug must show friendly empty state"""
        response = self.client.get("/medicines/catalog?q=NonExistentMedicationXYZ")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No medicines match your search criteria", response.data)

    def test_22_public_catalog_privacy_verification(self):
        """Public catalog must not leak internal warehouse thresholds or supplier IDs"""
        response = self.client.get("/medicines/catalog")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"reorder_threshold", response.data)
        self.assertNotIn(b"supplier_id", response.data)

    def test_23_public_lookup_empty_input(self):
        """Prescription lookup with empty query must warn user without crashing"""
        self.client.get("/patient/lookup")
        with self.client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "test_csrf")

        response = self.client.post("/patient/lookup", data={
            "csrf_token": csrf,
            "query_type": "rx_number",
            "query_val": ""
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter a Prescription ID or Registered Phone Number", response.data)

    def test_24_public_lookup_non_numeric_rx_id(self):
        """Prescription lookup with non-numeric Rx ID must reject cleanly"""
        self.client.get("/patient/lookup")
        with self.client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "test_csrf")

        response = self.client.post("/patient/lookup", data={
            "csrf_token": csrf,
            "query_type": "rx_number",
            "query_val": "invalid_alpha_rx"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prescription ID must be a numeric reference number", response.data)

    def test_25_public_lookup_nonexistent_rx_id(self):
        """Prescription lookup for non-existent ID must display empty state"""
        self.client.get("/patient/lookup")
        with self.client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "test_csrf")

        response = self.client.post("/patient/lookup", data={
            "csrf_token": csrf,
            "query_type": "rx_number",
            "query_val": "999999"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No prescription records found", response.data)

    def test_26_public_lookup_phone_search(self):
        """Prescription lookup by patient phone must find active prescription"""
        self.client.get("/patient/lookup")
        with self.client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "test_csrf")

        response = self.client.post("/patient/lookup", data={
            "csrf_token": csrf,
            "query_type": "phone",
            "query_val": "94441"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prescription Verification Records", response.data)
        self.assertIn(b"Karthik Ramanathan", response.data)

    def test_27_public_lookup_phone_no_match(self):
        """Prescription lookup by unregistered phone must display empty state"""
        self.client.get("/patient/lookup")
        with self.client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "test_csrf")

        response = self.client.post("/patient/lookup", data={
            "csrf_token": csrf,
            "query_type": "phone",
            "query_val": "0000000000"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No prescription records found", response.data)

    def test_28_unauthenticated_protected_routes_redirect(self):
        """Public visitors must be prevented from accessing internal staff operations"""
        protected_urls = [
            "/billing/new",
            "/billing/",
            "/medicines/add",
            "/patients/add",
            "/prescriptions/add",
            "/suppliers/add",
            "/reports/sales",
            "/reports/inventory",
            "/reports/expiry",
            "/users"
        ]
        for url in protected_urls:
            res = self.client.get(url, follow_redirects=False)
            self.assertEqual(res.status_code, 302, f"Expected 302 redirect for {url}")
            self.assertIn("/login", res.headers["Location"])


if __name__ == "__main__":
    unittest.main()
