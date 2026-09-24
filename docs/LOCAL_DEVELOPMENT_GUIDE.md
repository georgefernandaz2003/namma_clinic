# Namma Clinic — Local Laptop Development Guide

## 1. Project Architecture & Target Environment

Namma Clinic is designed to run natively and directly on a **local developer laptop**.

```
    PostgreSQL 16 (Local Laptop Database)
                 ↑
       Django 4.2 / DRF (Python 3.11 Backend)
                 ↑
        REST APIs (JSON / JWT)
                 ↑
     React / Vite (Future Frontend Phase)
                 ↑
          Web Browser
```

### Architectural Principles
- **No Docker**: Docker and container runtimes are **NOT required** and not used.
- **No Cloud Infrastructure**: AWS, Azure, SDC, and MeghRaj are out of scope.
- **Native Execution**: Python, Django, and PostgreSQL run natively on the developer workstation.

---

## 2. Prerequisites

Ensure the following tools are installed on your local laptop:
1. **Python 3.11+** (x86_64, Windows, macOS, or Linux)
2. **PostgreSQL 16+** (Native installer or bundled `pgserver`)
3. **Git**
4. **Web Browser** (Chrome, Edge, or Firefox)

---

## 3. PostgreSQL Database Setup

Namma Clinic connects to a dedicated local PostgreSQL 16 database.

### Database Details
- **Engine**: PostgreSQL 16+
- **Host**: `127.0.0.1` (localhost)
- **Port**: `5432` (or bundled local port, e.g., `49392` / `52322`)
- **Database Name**: `namma_clinic_local`
- **Username**: `postgres`
- **Password**: *(Blank or developer local password)*

### Creating the Local Database
Using `psql` or SQL management tool:
```sql
CREATE DATABASE namma_clinic_local;
```

If using the bundled repository `pgserver`, PostgreSQL can be started natively using `pg_ctl`:
```powershell
# Start local PostgreSQL
pg_ctl -D "D:\project\namma_clinic\pgdata" -l "D:\project\namma_clinic\pgdata\logfile.txt" start

# Stop local PostgreSQL
pg_ctl -D "D:\project\namma_clinic\pgdata" stop
```

---

## 4. Python Virtual Environment & Dependencies

From the repository root:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### `requirements.txt`
```text
Django>=4.2.0,<5.0.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
django-cors-headers>=4.3.0
psycopg2-binary>=2.9.9
```

---

## 5. Environment Configuration

Namma Clinic uses sensible, zero-configuration local defaults:
- `DJANGO_ENV=local`
- `DEBUG=True`
- `SECRET_KEY=django-insecure-namma-clinic-digital-health-platform-key-demo-only`
- `ALLOWED_HOSTS=['*']`
- `CORS_ALLOW_ALL_ORIGINS=True`
- `DATABASE_NAME=namma_clinic_local`

### Optional Environment Overrides
If your local PostgreSQL runs on a custom port or credentials, set the following environment variables (or define in a local shell profile):
```bash
# Optional overrides
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=your_password
```
*(On Windows PowerShell, use `$env:DATABASE_PORT="5432"`)*.

---

## 6. Database Migrations

Apply the complete 50-table physical schema to your local PostgreSQL instance:

```bash
python manage.py migrate
```

Verify that zero schema drift exists:
```bash
python manage.py makemigrations --check
```

---

## 7. Django System Check & Startup

Validate your Django configuration:
```bash
python manage.py check
```

Start the native development server:
```bash
python manage.py runserver 127.0.0.1:8000
```

The backend server is now live at `http://127.0.0.1:8000/`.

---

## 8. Health & Readiness Probe Verification

Namma Clinic exposes two lightweight operational probe endpoints:

### Liveness Probe
```bash
curl http://127.0.0.1:8000/healthz
```
**Expected Response**:
```json
{"status": "ok"}
```

### Readiness Probe
```bash
curl http://127.0.0.1:8000/readyz
```
**Expected Response (when PostgreSQL is running)**:
```json
{"status": "ready", "database": "connected"}
```

**Expected Response (when PostgreSQL is stopped)**:
HTTP Status `503 Service Unavailable`:
```json
{"status": "not ready", "database": "unavailable"}
```

---

## 9. Running the Automated Test Suite

To run the complete 113-test regression suite against the native local environment:

```bash
python manage.py test apps.accounts.tests_phase11 apps.accounts.tests_phase12_services apps.accounts.tests_services apps.visits.tests_services apps.laboratory.tests_services apps.pharmacy.tests_services apps.referrals.tests_services apps.audit.tests_services apps.accounts.tests_phase13_api apps.accounts.tests_phase14_integration apps.accounts.tests_phase15_reliability apps.accounts.tests_phase16_postgres apps.accounts.tests_phase18_deployment --noinput
```

**Expected Result**:
`Ran 113 tests in ~60-180s. OK.`

---

## 10. Local API Access & Endpoints

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Health** | `/healthz` | GET | Process liveness probe |
| **Readiness**| `/readyz` | GET | Database connectivity probe |
| **Auth** | `/api/auth/token/` | POST | Obtain JWT access/refresh token pair |
| **Patients** | `/api/v1/patients/` | GET/POST | Patient registry & search |
| **Visits** | `/api/v1/visits/` | GET/POST | Visit lifecycle & encounter management |
| **Token** | `/api/v1/visits/{id}/issue-opd-token/` | POST | OPD token queue allocation |
| **Triage** | `/api/v1/clinical/triage/` | GET/POST | Nurse triage assessment & vitals |
| **Consultation**| `/api/v1/clinical/consultations/` | GET/POST | Doctor clinical notes, diagnosis, plans |
| **Lab Tests**| `/api/v1/diagnostics/tests/` | GET | Diagnostic test master catalog |
| **Lab Orders**| `/api/v1/diagnostics/orders/` | GET/POST | Doctor diagnostic order placement |
| **Pharmacy** | `/api/v1/pharmacy/medicines/` | GET | Medicine master catalog |
| **Batches** | `/api/v1/pharmacy/batches/` | GET | Batch inventory bucket stock |
| **Dispense** | `/api/pharmacy/dispense/` | POST | Pharmacist medication dispensing |

---

## 11. Troubleshooting

### Problem: `connection refused on port 5432`
- **Cause**: Local PostgreSQL service is not started.
- **Fix**: Start your local PostgreSQL service or execute `pg_ctl start`. Verify active port using `netstat -ano | findstr 5432`.

### Problem: `Database "namma_clinic_local" does not exist`
- **Cause**: The dedicated local database has not been initialized.
- **Fix**: Connect to PostgreSQL and run `CREATE DATABASE namma_clinic_local;`, then rerun `python manage.py migrate`.

### Problem: `Port collision / Address already in use`
- **Fix**: If port 8000 is occupied, start Django on another port:
  ```bash
  python manage.py runserver 127.0.0.1:8080
  ```

---

## 12. Safe Local Database Reset Procedure

If you ever need to reset your local test data to a pristine state:
```bash
# 1. Flush database records
python manage.py flush --noinput

# 2. Re-apply migrations
python manage.py migrate
```

---

## 13. Frontend Startup Placeholder (Future Phase)

In a future phase, the React / Vite frontend will run alongside the backend:
```bash
# (Placeholder for future frontend phase)
cd frontend
npm install
npm run dev
```
The React frontend will communicate directly with `http://127.0.0.1:8000/api/v1/`.
