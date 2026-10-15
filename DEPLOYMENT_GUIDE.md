# RxCare Hospital Pharmacy Management System (HPMS)
## Deployment & Testing Guide (PostgreSQL & Render Cloud)

This guide provides concise, step-by-step instructions for running the application on Windows PowerShell locally, connecting it securely to Neon PostgreSQL, and deploying it on Render's free tier.

---

### Prerequisites
- Python 3.10+ installed on Windows.
- Existing virtual environment in the project directory (`.\venv`).
- A free account on [Neon.tech](https://neon.tech) (PostgreSQL database).
- A free account on [Render.com](https://render.com) (Web Service hosting).
- Git installed on your machine.

---

### Step 1: Activate Virtual Environment & Verify Dependencies

Open Windows PowerShell in the project directory:

```powershell
# 1. Navigate to your project directory (if not already there)
cd "c:\Users\Keerthana\Desktop\HospitalPharmacyDBMS - Copy"

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Ensure required packages are installed
python -m pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables Privately (`.env`)

1. Copy `.env.example` to `.env` (or edit existing `.env`):
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` in an editor and set your credentials:
   ```env
   # Flask Configuration
   SECRET_KEY=generate_a_secure_random_string_here_for_production
   FLASK_ENV=development
   FLASK_DEBUG=1
   PORT=5000

   # PostgreSQL Connection (Use your Neon connection string)
   DATABASE_URL=postgresql://<user>:<password>@<ep-pool-name>.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
   > [!IMPORTANT]
   > The `.env` file is excluded in `.gitignore`. Never add, commit, or push `.env` to Git.

---

### Step 3: Initialize the PostgreSQL Database Safely

1. Log into your [Neon.tech Console](https://console.neon.tech).
2. Open the **SQL Editor** tab.
3. For a brand new empty database:
   - Run the contents of `schema_postgres_safe.sql` (creates all tables, constraints, foreign keys, indexes, and views non-destructively).
   - *(Optional Demo Data)*: Run the contents of `seed_data_postgres.sql` to populate sample suppliers, medicines, patients, prescriptions, and invoices.
   > [!NOTE]
   > `schema_postgres_safe.sql` uses `CREATE TABLE IF NOT EXISTS` and contains **no** `DROP` or `TRUNCATE` operations. It is completely safe to run against an active database.

---

### Step 4: Run Safe Diagnostics & Create Initial Administrator

Back in PowerShell:

```powershell
# 1. Test physical connectivity and schema integrity
python test_db.py

# 2. Create the first Administrator account interactively
python init_admin.py --username admin --name "Chief Pharmacist" --role ADMIN
# (Enter and confirm your chosen secure password when prompted)
```

---

### Step 5: Start and Test Localhost Website

```powershell
python app.py
```
1. Open your browser at `http://127.0.0.1:5000`.
2. Test the core workflows:
   - **Public Portal:** View formulary, about page, and prescription tracking lookup.
   - **Authentication:** Sign in via `/login` using your administrator account.
   - **Dashboard:** Verify KPIs and recent invoices load.
   - **Formulary (Medicines):** Add, search, and update stock/batches.
   - **Prescriptions:** Create a prescription linked to a patient.
   - **Billing & POS (`/billing/new`):** Dispense medicines, generate invoices, and verify stock auto-deduction.
   - **Reports:** Verify Sales, Inventory, and Expiry risk analytics.
   - **Sign Out:** Ensure session termination works as expected.

---

### Step 6: Prepare and Push to GitHub

Ensure `.env` remains untracked before staging:

```powershell
# 1. Check Git status (verify .env is NOT in staged or untracked list)
git status

# 2. Add modified and created project files
git add .env.example app.py db.py requirements.txt routes/ Procfile schema_postgres.sql schema_postgres_safe.sql seed_data_postgres.sql test_db.py DEPLOYMENT_GUIDE.md

# 3. Commit changes
git commit -m "Configure PostgreSQL backend and Render deployment"

# 4. Push to your GitHub repository
git push origin main
```

---

### Step 7: Deploy on Render (Free Web Service)

1. Log into [Render.com](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository.
4. Fill in the build settings:
   - **Name:** `rxcare-pharmacy` (or your preferred name)
   - **Region:** Nearest region (e.g., Singapore, Frankfurt, Oregon)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
5. Click **Advanced** $\rightarrow$ **Add Environment Variable**:
   - `DATABASE_URL`: Your full Neon PostgreSQL connection string (`postgresql://...sslmode=require`).
   - `SECRET_KEY`: A strong, randomly generated string (e.g., `python -c "import secrets; print(secrets.token_hex(32))"`).
   - `PYTHON_VERSION`: `3.11.9` (or `3.10.12`).
6. Click **Create Web Service**.

---

### Important Free-Tier Cloud Information & Troubleshooting

- **Free-Tier Inactivity Sleep:**
  On Render's free tier, the web service spins down after 15 minutes of inactivity. When a visitor opens the website, the initial boot ("cold start") takes approximately 30–50 seconds. Subsequent page views are immediate. Neon compute instances may also briefly pause on inactivity and wake up automatically within seconds upon query arrival.
- **Quota & Limits Notice:**
  Free tier limits (build hours, compute units, egress bandwidth) are subject to change by cloud providers. Check your provider's usage dashboards periodically.
- **SSL / TLS Connection Errors:**
  If connecting to Neon or cloud databases fails, ensure `?sslmode=require` is present at the end of `DATABASE_URL`. `db.py` automatically enforces this for Neon and Render hosts.
- **Port Binding:**
  Do not hardcode port `5000` for production. `Procfile` uses Gunicorn, and `app.py` respects the dynamic `$PORT` provided by Render.
- **CSRF Token Errors:**
  If you encounter a `400 Bad Request: CSRF token verification failed` on form submissions, ensure your browser cookies are enabled and you are not submitting stale cached forms.
