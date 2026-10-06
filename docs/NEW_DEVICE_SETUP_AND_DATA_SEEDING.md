# Namma Clinic — New Device Setup & Data Seeding Runbook

**Document Version:** 1.0.0  
**Target Environment:** Local Windows Workstation (Windows 10 / Windows 11 64-bit)  
**Authoritative Workspace:** `D:\project\namma_clinic`  
**Git Branch:** `feature/namma-clinic-demo-data-model`  
**Stack Baseline:** PostgreSQL 16 | Django 4.2.x / DRF | React 19 / Vite / TypeScript | Node.js 18+  

---

## Executive Summary & Scope

This document provides the authoritative, developer-operational, step-by-step procedure for deploying and initializing the **Namma Clinic Digital Healthcare Platform** on a completely new local Windows laptop or workstation.

It provides verified instructions to:
1. Prepare operating system dependencies and prerequisites.
2. Clone the authoritative repository and branch.
3. Configure the native Python virtual environment and PostgreSQL 16 database.
4. Execute Django schema migrations across all 21 applications.
5. Execute the approved, deterministic seed commands to populate the RBAC matrix, network facility infrastructure, procurement provenance, and clinical demonstration cohorts.
6. Verify database counts and integrity via both ORM and raw SQL.
7. Start the backend and frontend development servers.
8. Perform end-to-end browser and API verification across all 8 operational roles.
9. Troubleshoot common setup and seeding failures.
10. Execute clean re-seeding or resetting procedures.

---

## 1. Prerequisites

Before setting up Namma Clinic on a new Windows computer, install and configure the following required software tools:

| Tool | Minimum Version | Recommended Version | Verification Command | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10 (Build 19041+) | Windows 11 (64-bit) | `[System.Environment]::OSVersion.Version` | PowerShell 5.1+ or PowerShell 7+ |
| **Git for Windows** | 2.30.0+ | 2.44.0+ | `git --version` | Configured with credential helper |
| **Python** | 3.11.0 (64-bit) | 3.11.9 (64-bit) | `python --version` | Check *"Add python.exe to PATH"* during install |
| **PostgreSQL** | 16.0 | 16.4+ | `psql --version` | Standard port `5432` or local standalone cluster |
| **Node.js** | 18.18.0 LTS | 20.x or 22.x LTS | `node --version` | Bundled with `npm` |
| **npm** | 9.0.0+ | 10.x+ | `npm --version` | Node Package Manager |
| **Web Browser** | Evergreen | Google Chrome / Edge | `Start-Process msedge` | Chromium-based browser recommended |

> [!IMPORTANT]
> **No Docker or Cloud Services Required**:
> Namma Clinic is architected as a local-first application running directly on native Windows services. Docker, Kubernetes, WSL2, AWS, and cloud databases are **strictly not required** for local development and demonstration.

---

## 2. Repository Checkout

Open a Windows PowerShell terminal and clone the repository into the standard local directory.

```powershell
# Create project parent folder if needed
New-Item -ItemType Directory -Force -Path "D:\project"
Set-Location -Path "D:\project"

# Clone the repository
git clone https://github.com/georgefernandaz2003/namma_clinic.git namma_clinic

# Navigate into the authoritative workspace
Set-Location -Path "D:\project\namma_clinic"

# Check out the authoritative feature branch
git checkout feature/namma-clinic-demo-data-model

# Verify current git state
git branch --show-current
git rev-parse HEAD
git status --short
```

**Expected Verification Output:**
```text
feature/namma-clinic-demo-data-model
```

---

## 3. Python & Backend Environment Setup

Namma Clinic requires Python 3.11 with an isolated virtual environment in the `backend/` directory.

### 3.1 Create Virtual Environment

```powershell
# Navigate to the backend directory
Set-Location -Path "D:\project\namma_clinic\backend"

# Create a clean virtual environment
python -m venv venv
```

### 3.2 Activate Virtual Environment

```powershell
# PowerShell activation:
.\venv\Scripts\Activate.ps1

# If PowerShell script execution policy blocks activation, permit process-level execution:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

*(Your prompt will now display `(venv)`).*

### 3.3 Upgrade Package Tools and Install Dependencies

```powershell
# Upgrade core packaging tools
python -m pip install --upgrade pip setuptools wheel

# Install production and development dependencies
pip install -r requirements.txt
```

### 3.4 Dependency Inventory (`requirements.txt`)
The backend installs the following verified packages:
- `Django>=4.2.0,<5.0.0` (Django 4.2 LTS)
- `djangorestframework>=3.14.0` (Django REST Framework)
- `djangorestframework-simplejwt>=5.3.0` (JWT Authentication)
- `django-cors-headers>=4.3.0` (CORS headers for Vite frontend)
- `psycopg2-binary>=2.9.9` (PostgreSQL adapter)

---

## 4. PostgreSQL Installation & Configuration

Namma Clinic utilizes a local PostgreSQL 16 database.

### 4.1 Service Verification
Verify that the PostgreSQL 16 service is active and listening on port `5432`:

```powershell
# Test TCP connection to PostgreSQL port 5432
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
```

**Expected Output:**
```text
TcpTestSucceeded : True
```

If using the Windows Service Manager:
```powershell
Get-Service -Name "postgresql*"
```
Ensure the service status is `Running`. If stopped, start it via:
```powershell
Start-Service -Name "postgresql-x64-16"
```

### 4.2 Standalone / Portable Cluster Startup (Optional)
If running PostgreSQL via a local cluster directory (`pgdata`):
```powershell
pg_ctl -D "D:\project\namma_clinic\pgdata" -l "D:\project\namma_clinic\pgdata\logfile.txt" start
```

---

## 5. Database Creation

Create the dedicated local database `namma_clinic_local`.

### 5.1 Create Database via `psql` or `createdb`

```powershell
# Using createdb:
createdb -U postgres -h 127.0.0.1 -p 5432 namma_clinic_local

# OR using psql command-line:
psql -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE namma_clinic_local;"
```

### 5.2 Verify Database Existence

```powershell
psql -U postgres -h 127.0.0.1 -p 5432 -lqt | Select-String "namma_clinic_local"
```

**Expected Output:**
```text
namma_clinic_local | postgres | UTF8 ...
```

---

## 6. Environment Variables & Configuration

The application uses zero-configuration sensible defaults for local development configured in [settings.py](file:///d:/project/namma-clinic/backend/config/settings.py).

### 6.1 Default Local Settings (`DJANGO_ENV=local`)
When no environment variables are defined, the system automatically defaults to:
- `DJANGO_ENV`: `local`
- `DEBUG`: `True`
- `DATABASE_NAME`: `namma_clinic_local`
- `DATABASE_USER`: `postgres`
- `DATABASE_PASSWORD`: `""` (empty string)
- `DATABASE_HOST`: `127.0.0.1`
- `DATABASE_PORT`: `5432` (or dynamic local cluster port)
- `CORS_ALLOW_ALL_ORIGINS`: `True`

### 6.2 Custom Local Database Credentials (Optional Overrides)
If your local PostgreSQL installation requires a non-blank password or runs on a non-standard port, configure your PowerShell session before running commands:

```powershell
$env:DATABASE_PORT = "5432"
$env:DATABASE_USER = "postgres"
$env:DATABASE_PASSWORD = "<YOUR_POSTGRES_PASSWORD>"
$env:DATABASE_HOST = "127.0.0.1"
$env:DATABASE_NAME = "namma_clinic_local"
```

---

## 7. Django Schema Migrations

> [!IMPORTANT]
> **Distinction Between Schema Migrations and Data Seeding**:
> - **Migrations (`migrate`)**: Create physical database tables, column types, primary keys, foreign keys, unique constraints, and indices. Migrations do **NOT** populate clinical or demo records.
> - **Seed Commands (`seed_*`)**: Populate the database with master catalogs, user accounts, facilities, inventory ledger entries, and clinical patients.

### 7.1 Execute Migrations

From the `backend/` directory with the virtual environment activated:

```powershell
python manage.py migrate
```

**Expected Success Output:**
```text
Operations to perform:
  Apply all migrations: accounts, admin, alerts, ars, audit, auth, compliance, consultations, contenttypes, facilities, geography, integrations, laboratory, ncd, outreach, patients, pharmacy, quality, referrals, reports, sessions, surveillance, telemedicine, triage, visits, wellness
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_alter_user_role... OK
  Applying accounts.0003_person_rolemaster_staffprofile_staffroleassignment_and_more... OK
  Applying accounts.0004_permissionmaster_alter_rolemaster_options_and_more... OK
  Applying accounts.0005_staffroleassignment_assigned_by_and_more... OK
  ...
  Applying pharmacy.0008_reconcile_procurement_demo_data... OK
  Applying pharmacy.0009_dispensation_inventoryledger_dispensationitem_and_more... OK
  Applying triage.0002_triage_triage_chk_triages_bp_sys_and_more... OK
  Applying visits.0005_sync_facility_daily_counters... OK
  Applying wellness.0001_initial... OK
```

### 7.2 Verify Schema Migration State

```powershell
# Confirm zero unapplied migrations remain
python manage.py showmigrations | Select-String "\[ \]"

# Confirm zero model drift
python manage.py makemigrations --check
```

**Expected Output:** Both commands must return **no output** and exit code 0 (`No changes detected`).

---

## 8. Exact Approved Seed-Data Commands

Namma Clinic provides three deterministic, repository-native management commands to seed application data.

### 8.1 Order of Operations on a Clean Database

Execute the seed commands in the exact sequence shown below:

```
[Clean PostgreSQL DB]
        ↓
1. python manage.py migrate
        ↓
2. python manage.py seed_role_permissions
        ↓
3. python manage.py seed_demo --confirm-demo-reset
        ↓
4. python manage.py seed_demo_patients --confirm-demo-reset
```

---

### Command 1: `seed_role_permissions` (Idempotent RBAC Catalog)

Populates the canonical role master catalog, domain permissions, and role-permission mappings.

```powershell
python manage.py seed_role_permissions
```

**Command Characteristics:**
- **Idempotency:** 100% idempotent. Safe to run multiple times without creating duplicates.
- **Scope:** Reconciles the 8 canonical roles, 57 permissions, and 124 role-permission mappings.
- **Safety:** Automatically migrates any legacy `COMPOUNDER` references to `FRONT_DESK_OFFICER`.

**Expected Output:**
```text
Role & Permission Catalogue Seed Complete: Roles (0 created, 0 updated, 8 total), Permissions (0 created, 0 updated, 57 total), RolePermissions (0 created, 124 active).
```

---

### Command 2: `seed_demo --confirm-demo-reset` (Network Masters & Procurement Lifecycle)

Resets operational transaction tables while strictly preserving master data, then seeds the multi-facility network hierarchy, user credentials, medicine master catalog, vendors, and the procurement provenance chain.

```powershell
python manage.py seed_demo --confirm-demo-reset
```

> [!CAUTION]
> **Mandatory Safety Flag**:
> The `--confirm-demo-reset` flag is required. Executing without this flag will safely abort execution.

**Command Characteristics:**
- **Dependency Graph Discovery:** Inspects live Django model metadata, FK dependencies, and deletion constraints dynamically.
- **Topological Purge:** Flushes operational transactional records inside `transaction.atomic()` while preserving master geographic and administrative models.
- **Append-Only Ledger Safety:** Uses direct SQL execution to flush append-only immutable tables (`pharmacy_inventorytransaction`, `pharmacy_dispensationreturn`) strictly for demo reset.
- **Scope:** Creates 4 facilities, 19 users, 9 diagnostic tests, 7 medicine masters, 2 vendors, 4 purchase orders with full GRN receipt lifecycle, and initial demonstration patients.
- **Audit Logging:** Automatically records post-reseed audit log verification.

**Expected Output Snippet:**
```text
======================================================================
NAMMA CLINIC — PRE-DELETE DEPENDENCY DISCOVERY & VALIDATION
======================================================================
Discovered 12 Preserved Master/Configuration Models:
  [PRESERVE] geography.State (geography_state)
  ...
--- RESOLVED SAFE DELETION PLAN (TOPOLOGICAL ORDER) ---
...
All operational records successfully purged (0 surviving records).
...
DEMO DATASET SUCCESSFULLY PREPARED & AUDIT-VERIFIED!
```

---

### Command 3: `seed_demo_patients --confirm-demo-reset` (10 Synthetic Outpatient Cohort)

Prepares the local primary health centre (Facility ID 1) with active dispensary stock, initial `InventoryLedger` purchase receipts, and seeds exactly **10 unique synthetic demo patients** representing the entire outpatient clinical workflow.

```powershell
python manage.py seed_demo_patients --confirm-demo-reset
```

**Command Characteristics:**
- **Idempotency:** Cleans temporary test clinical tables cleanly before re-inserting the 10-patient cohort.
- **Inventory Ledger Provenance:** Generates 6 batches across essential medicines and logs double-entry purchase receipts into `InventoryLedger` before any clinical dispensation occurs.
- **Clinical Queue Realism:** Populates visits, tokens, vitals, doctor notes, diagnostic orders, lab results, prescriptions, and dispensed medications.

**Expected Output Snippet:**
```text
======================================================================
NAMMA CLINIC — CLEAN DEMO DATA & 10 SYNTHETIC DEMO PATIENTS SEED
======================================================================
Primary Facility: Namma Clinic Local PHC (ID: 1)
Cleaning existing temporary clinical demonstration records...
  [CLEAN] Truncated temporary operational tables cleanly.

Seeding legitimate pharmacy batches at Namma Clinic Local PHC...
  [STOCK] Paracetamol 500mg (BATCH-LOC-PCM01): 500 units (Expiry: 2027-06-30)
  [STOCK] Amoxicillin 500mg (BATCH-LOC-AMX01): 300 units (Expiry: 2027-08-31)
  [STOCK] Cetirizine 10mg (BATCH-LOC-CTZ01): 250 units (Expiry: 2027-10-31)
  [STOCK] Metformin 500mg (BATCH-LOC-MET01): 400 units (Expiry: 2027-12-31)
  [STOCK] Amlodipine 5mg (BATCH-LOC-AML01): 350 units (Expiry: 2027-09-30)
  [STOCK] ORS Oral Rehydration Salts 21.8g (BATCH-LOC-ORS01): 200 units (Expiry: 2028-01-31)

Seeding exactly 10 UNIQUE, realistic SYNTHETIC demo patients...
  [PATIENT 01] Arun Kumar (NC-KA-2026-0001) — PRIMARY LIVE WALKTHROUGH PATIENT
  [PATIENT 02] Priya Nair (NC-KA-2026-0002) — IN_NURSE_QUEUE
  [PATIENT 03] Ravi Shankar (NC-KA-2026-0003) — TRIAGED_WAITING_DOCTOR
  [PATIENT 04] Meena Devi (NC-KA-2026-0004) — IN_CONSULTATION
  [PATIENT 05] Suresh Babu (NC-KA-2026-0005) — LAB_ORDERED_PENDING_SAMPLE
  [PATIENT 06] Kavya Reddy (NC-KA-2026-0006) — LAB_RESULT_ENTERED
  [PATIENT 07] Manoj Kumar (NC-KA-2026-0007) — PHARMACY_PENDING_VERIFY
  [PATIENT 08] Anitha Rao (NC-KA-2026-0008) — PHARMACY_VERIFIED_FEFO_READY
  [PATIENT 09] Sanjay Patel (NC-KA-2026-0009) — DISPENSED_COMPLETED
  [PATIENT 10] Deepa Menon (NC-KA-2026-0010) — REGISTERED_FOLLOWUP

======================================================================
DEMO DATASET SUCCESSFULLY PREPARED & VALIDATED (10 UNIQUE PATIENTS)!
======================================================================
```

---

## 9. What Data is Seeded and Why

The seed commands populate data strictly according to domain models and operational constraints:

### 9.1 RBAC Master Catalogue (`seed_role_permissions`)
- **8 Canonical Roles (`RoleMaster`):**
  1. `DISTRICT_OFFICER` (District Health Officer)
  2. `HOSPITAL_ADMIN` (Clinic Administrator)
  3. `FRONT_DESK_OFFICER` (Front Desk Officer / Registration Clerk)
  4. `NURSE` (Staff Nurse)
  5. `DOCTOR` (Medical Officer)
  6. `LAB_TECHNICIAN` (Lab Technician)
  7. `PHARMACIST` (Pharmacist)
  8. `INVENTORY` (Inventory Officer)
- **57 Permissions (`PermissionMaster`):** Defined across 12 domains (`accounts`, `facilities`, `geography`, `patients`, `visits`, `clinical`, `diagnostics`, `pharmacy`, `inventory`, `referrals`, `surveillance`, `compliance`).
- **124 Role-Permission Mappings (`RolePermission`):** Authoritative access control mapping defining permissible backend API operations.

### 9.2 Geographic Hierarchy & Health Facilities (`seed_demo`)
- **Geographic Hierarchy:**
  - State: Karnataka (`KA`)
  - Districts: BBMP Central (`KA-BU`), Bengaluru Rural (`KA-BR`)
  - Zones: East Zone, South Zone, Hoskote Zone
  - Wards: Indiranagar Ward (12), Ulsoor Ward (14), Jayanagar Ward (45), Varthur Rural Ward (1)
- **Network Facilities:**
  - `HOSP-DIST-01` (Victoria District General Hospital & Specialist Center — Main Hospital)
  - `HOSP-SUB-01` (Indiranagar Sub-District Hospital & UPHC — Namma Clinic)
  - `RC-A4-01` (Varthur Rural Primary Clinic A4 — Rural Clinic)
  - `VC-A4-01` (Gunjur Village Satellite Clinic — Village Clinic)
  - `PHC-LOCAL-01` (Namma Clinic Local PHC — Primary Health Centre, Facility ID 1)

### 9.3 Medical Masters, Vendors & Procurement Chain (`seed_demo`)
- **Vendors:** Karnataka State Medical Supplies Corp Ltd (`KSMSCL`), Karnataka Antibiotics & Pharmaceuticals Ltd (`KAPL`).
- **Medicines:** Metformin 500mg, Amlodipine 5mg, Paracetamol 650mg, Amoxicillin 500mg, Telmisartan 40mg, Iron & Folic Acid, Cetirizine 10mg.
- **Diagnostic Catalog:** HbA1c, Fasting Blood Glucose, Random Blood Glucose, Hemoglobin, Lipid Profile, Dengue NS1 Antigen, Malaria Antigen, Urine Albumin, Sputum AFB.
- **Procurement Provenance:**
  - PO 1: Victoria District Hospital (Metformin + Amlodipine) — Status: `RECEIVED`, GRN: `ACCEPTED`, Batches initialized with ledger transactions.
  - PO 2: Indiranagar SDH (Paracetamol + Amoxicillin) — Demonstrates partial delivery and rejected quantity tracking (unusable damaged units excluded from usable inventory).
  - PO 3: Varthur Clinic (Telmisartan + IFA + Cetirizine) — Full delivery with batch expiry tracking.
  - PO 4: Victoria Hospital — Approved and ordered PO with zero delivery (demonstrates zero unreceived inventory stock mutation).

### 9.4 10-Patient Demonstration Cohort (`seed_demo_patients`)

The 10 synthetic demo patients cover every stage of outpatient care:

| Patient UHID | Patient Name | Age / Sex | Clinical Stage & Status | Clinical Purpose in Demo |
| :--- | :--- | :--- | :--- | :--- |
| `NC-KA-2026-0001` | Arun Kumar | 34 / M | `REGISTERED_CLEAN` (0 visits) | **Primary Walkthrough Patient**: Ready for live intake, vitals recording, consultation, and dispensing. |
| `NC-KA-2026-0002` | Priya Nair | 28 / F | `IN_NURSE_QUEUE` (`WAITING_FOR_TRIAGE`) | Waiting in nurse queue; demonstrates nurse vitals capture form. |
| `NC-KA-2026-0003` | Ravi Shankar | 45 / M | `TRIAGED_WAITING_DOCTOR` (`TRIAGED`) | Triaged by nurse; demonstrates doctor queue prioritization. |
| `NC-KA-2026-0004` | Meena Devi | 52 / F | `IN_CONSULTATION` | Active consultation with Medical Officer; shows clinical notes and diagnosis entry. |
| `NC-KA-2026-0005` | Suresh Babu | 39 / M | `LAB_ORDERED_PENDING_SAMPLE` | CBC and Dengue NS1 tests ordered; shows lab accessioning queue. |
| `NC-KA-2026-0006` | Kavya Reddy | 31 / F | `LAB_RESULT_ENTERED` | Urine specimen collected and results entered; shows MO result verification. |
| `NC-KA-2026-0007` | Manoj Kumar | 42 / M | `PHARMACY_PENDING_VERIFY` | Amoxicillin + Paracetamol prescribed; shows pharmacist verification workflow. |
| `NC-KA-2026-0008` | Anitha Rao | 36 / F | `PHARMACY_VERIFIED_FEFO_READY` | Prescription verified; ready for First-Expiry, First-Out (FEFO) dispensing. |
| `NC-KA-2026-0009` | Sanjay Patel | 58 / M | `DISPENSED_COMPLETED` (`COMPLETED`) | Completed encounter; proves double-entry deduction in `InventoryLedger`. |
| `NC-KA-2026-0010` | Deepa Menon | 49 / F | `REGISTERED_FOLLOWUP` | Chronic disease registry patient; demonstrates follow-up scheduling. |

---

## 10. Expected Record & Count Verification

Verify database consistency using either Django management commands or raw SQL.

### 10.1 ORM Verification Script

Execute the following one-liner in PowerShell:

```powershell
python manage.py shell -c "
from apps.accounts.models import RoleMaster, PermissionMaster, RolePermission, User, StaffProfile, StaffRoleAssignment
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit, Token
from apps.pharmacy.models import MedicineMaster, MedicineBatch, PurchaseOrder, InventoryLedger, Dispensation
from apps.laboratory.models import DiagnosticOrder, DiagnosticResult

print('Roles:                    ', RoleMaster.objects.count(), '(Expected: 8)')
print('Permissions:              ', PermissionMaster.objects.count(), '(Expected: 57)')
print('Active RolePermissions:   ', RolePermission.objects.filter(is_active=True).count(), '(Expected: >= 119)')
print('Users:                    ', User.objects.count(), '(Expected: >= 19)')
print('Staff Profiles:           ', StaffProfile.objects.count(), '(Expected: >= 19)')
print('Facilities:               ', Facility.objects.count(), '(Expected: >= 4)')
print('Patients:                 ', Patient.objects.count(), '(Expected: 10 in demo cohort)')
print('Visits:                   ', Visit.objects.count(), '(Expected: 8 in demo cohort)')
print('Medicine Batches:         ', MedicineBatch.objects.count(), '(Expected: >= 6)')
print('Inventory Ledger Entries: ', InventoryLedger.objects.count(), '(Expected: >= 7)')
"
```

### 10.2 Raw PostgreSQL Verification Queries (`psql`)

Execute standard SQL queries against `namma_clinic_local`:

```sql
-- 1. Check Canonical Roles (Must equal 8)
SELECT count(*) AS total_roles FROM accounts_rolemaster;

-- 2. Check Permissions (Must equal 57)
SELECT count(*) AS total_permissions FROM accounts_permissionmaster;

-- 3. Check Active Role Mappings (Must be between 119 and 124)
SELECT count(*) AS active_role_permissions FROM accounts_rolepermission WHERE is_active = true;

-- 4. Check Demo Patients (Must equal 10 for clean demo cohort)
SELECT patient_id, name, gender, age FROM patients_patient ORDER BY patient_id;

-- 5. Check Inventory Ledger Entries (Must have initial purchase receipts and dispensations)
SELECT b.batch_number, l.transaction_type, l.quantity_delta, l.balance_after, l.created_at
FROM pharmacy_inventoryledger l
JOIN pharmacy_medicinebatch b ON l.batch_id = b.id
ORDER BY l.created_at DESC;
```

---

## 11. Backend Server Startup

Start the Django REST Framework development server.

```powershell
# From D:\project\namma_clinic\backend with venv activated:
python manage.py runserver 127.0.0.1:8000
```

**Expected Success Log:**
```text
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
Django version 4.2.x, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### 11.1 Health & Readiness Probe Checks
Open a separate PowerShell terminal to verify probe endpoints:

```powershell
# Liveness Probe (checks web process):
Invoke-RestMethod -Uri "http://127.0.0.1:8000/healthz"
# Expected Output: @{status=ok}

# Readiness Probe (checks database connectivity):
Invoke-RestMethod -Uri "http://127.0.0.1:8000/readyz"
# Expected Output: @{status=ready; database=connected}
```

---

## 12. Frontend Server Startup

The frontend is built with React 19, TypeScript, Tailwind CSS, and Vite.

### 12.1 Install Node Dependencies

```powershell
# Navigate to the frontend directory
Set-Location -Path "D:\project\namma_clinic\frontend"

# Install frontend packages
npm install
```

### 12.2 Configure Frontend Environment File
Verify or create the local environment file:

```powershell
# Copy template if .env is missing
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
```

The frontend defaults to `http://localhost:8000/api/` if `VITE_API_BASE_URL` is omitted. Ensure `.env` contains:
```env
VITE_API_BASE_URL=http://localhost:8000/api/
```

### 12.3 Start Vite Development Server

```powershell
npm run dev
```

**Expected Success Output:**
```text
  VITE v8.2.2  ready in 345 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## 13. Browser & UI Verification

Navigate to `http://localhost:3000/login` in your web browser.

### 13.1 Verified Role Credentials Matrix

Namma Clinic includes interactive demo credentials on the login screen. You can log in using either the comprehensive operational accounts or legacy developer credentials:

| Role Title | Username | Password | Default Landing Route | Key Functional Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Front Desk Officer** | `e2e_compounder_user` | `Password123!` | `/dashboard/front-desk` | Patient registration, demographic search, OPD token queue issuance. |
| **Staff Nurse** | `e2e_nurse_user` | `Password123!` | `/dashboard/nurse` | Vitals triage recording, BP/temp alerts, doctor queue forwarding. |
| **Medical Officer (Doctor)** | `e2e_doctor_user` | `Password123!` | `/dashboard/doctor` | Clinical notes, ICD-10 diagnosis, e-prescriptions, diagnostic orders. |
| **Lab Technician** | `e2e_lab_user` | `Password123!` | `/dashboard/lab` | Diagnostic order intake, specimen collection, test results entry. |
| **Pharmacist** | `e2e_pharmacist_user` | `Password123!` | `/dashboard/pharmacy` | Prescription verification, FEFO batch selection, inventory dispensing. |
| **Inventory Officer** | `e2e_inventory_user` | `Password123!` | `/dashboard/inventory` | Purchase orders, GRN verification, stock audits, ledger view. |
| **Dual-Role (Inv + Pharm)** | `e2e_dual_user` | `Password123!` | `/dashboard/pharmacy` | Combined procurement administration and dispensary management. |
| **Hospital Administrator** | `e2e_admin_user` | `Password123!` | `/dashboard/admin` | Facility operational metrics, staff administration, audit logs. |
| **District Health Officer** | `e2e_dho_user` | `Password123!` | `/dashboard/district` | District disease surveillance, facility KPI monitoring, compliance. |

*Alternative Legacy Accounts:*  
- Doctor: `localdoc` / `DoctorPassword123!`  
- Nurse: `localnurse` / `NursePassword123!`  
- Pharmacist: `localpharm` / `PharmPassword123!`  
- Lab Tech: `locallab` / `LabPassword123!`  
- Hospital Admin: `testadmin` / `AdminPassword123!`  

### 13.2 Browser UI Validation Checklist
1. **Front Desk:** Log in as `e2e_compounder_user`. Verify landing at `/dashboard/front-desk`. Confirm Patient 01 (`Arun Kumar`) appears in the Patient Directory.
2. **Triage:** Log in as `e2e_nurse_user`. Open `/dashboard/nurse`. Confirm Patient 02 (`Priya Nair`) appears in the "Waiting for Triage" queue.
3. **Consultation:** Log in as `e2e_doctor_user`. Open `/dashboard/doctor`. Confirm Patient 03 (`Ravi Shankar`) appears in the "Ready for Doctor" queue.
4. **Lab Accessioning:** Log in as `e2e_lab_user`. Open `/dashboard/lab`. Confirm Patient 05 (`Suresh Babu`) has pending CBC and Dengue orders.
5. **Pharmacy Dispensing:** Log in as `e2e_pharmacist_user`. Open `/dashboard/pharmacy`. Confirm Patient 08 (`Anitha Rao`) has a verified prescription ready for dispensing.
6. **Inventory Ledger:** Open the Inventory Ledger tab to confirm batch counts and audit log history.

---

## 14. Common Setup & Seed Failures and Fixes

| Issue / Error Symptom | Root Cause | Verified Resolution |
| :--- | :--- | :--- |
| **`connection to server at "127.0.0.1", port 5432 failed: Connection refused`** | PostgreSQL 16 service is not running. | Run `Start-Service postgresql-x64-16` or `pg_ctl start`. Confirm port listening via `Test-NetConnection -ComputerName 127.0.0.1 -Port 5432`. |
| **`FATAL: database "namma_clinic_local" does not exist`** | Database was not created before running migrations. | Run `createdb -U postgres -h 127.0.0.1 -p 5432 namma_clinic_local`. |
| **`ERROR: Demo reset aborted! Pass --confirm-demo-reset`** | Safety guard prevented accidental operational data deletion. | Provide the required flag: `python manage.py seed_demo --confirm-demo-reset`. |
| **`File ... Activate.ps1 cannot be loaded because running scripts is disabled`** | Windows PowerShell Execution Policy restricts script execution. | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your active PowerShell window. |
| **`Error: listen EADDRINUSE: address already in use 127.0.0.1:8000`** | Another Python or web server process is holding port 8000. | Find and terminate the process via `Get-Process python` or start Django on another port: `python manage.py runserver 127.0.0.1:8080`. |
| **`Vite: Port 3000 is in use, trying another one...`** | Port 3000 is occupied. | Terminate the occupying process or allow Vite to use port 3001. Ensure CORS origins allow the alternate port. |
| **`HTTP Error 401: Unauthorized on /api/auth/token/`** | Incorrect username or password entered. | Verify user credentials in the table above. For `e2e_*` accounts use `Password123!`. For `localdoc` use `DoctorPassword123!`. |
| **`ModuleNotFoundError: No module named 'psycopg2'`** | Dependencies not installed in active virtual environment. | Ensure `(venv)` is active and run `pip install -r requirements.txt`. |

---

## 15. Clean Re-Seed & Reset Procedure

If test data becomes corrupted or you wish to return the environment to a clean demonstration baseline, follow this clean reset procedure:

### Option A: Standard In-Place Reset (Preserves Schema & Masters)
This is the recommended standard procedure. It does not drop database tables:

```powershell
Set-Location -Path "D:\project\namma_clinic\backend"
.\venv\Scripts\Activate.ps1

# 1. Reset network infrastructure and master procurement
python manage.py seed_demo --confirm-demo-reset

# 2. Reconcile role catalogue and permissions
python manage.py seed_role_permissions

# 3. Reseed the 10-patient outpatient demonstration cohort
python manage.py seed_demo_patients --confirm-demo-reset
```

### Option B: Nuclear Reset (Full Database Drop & Rebuild)
Use this option if schema migrations fail or a corrupted schema requires complete reconstruction:

```powershell
Set-Location -Path "D:\project\namma_clinic\backend"
.\venv\Scripts\Activate.ps1

# 1. Terminate active server connections and drop database
psql -U postgres -h 127.0.0.1 -p 5432 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'namma_clinic_local' AND pid <> pg_backend_pid();"
dropdb -U postgres -h 127.0.0.1 -p 5432 namma_clinic_local

# 2. Recreate clean database
createdb -U postgres -h 127.0.0.1 -p 5432 namma_clinic_local

# 3. Apply schema migrations
python manage.py migrate

# 4. Seed role catalog
python manage.py seed_role_permissions

# 5. Seed network infrastructure
python manage.py seed_demo --confirm-demo-reset

# 6. Seed clinical outpatient demo cohort
python manage.py seed_demo_patients --confirm-demo-reset
```

---

## 16. Final New-Device Validation Checklist

Complete this checklist to verify a successful installation:

- [ ] **Prerequisites:** Python 3.11, PostgreSQL 16, Node.js 18+, Git verified via CLI.
- [ ] **Workspace:** Repository checked out to `feature/namma-clinic-demo-data-model`.
- [ ] **Virtualenv:** `backend/venv` created and all dependencies from `requirements.txt` installed.
- [ ] **Database:** PostgreSQL service active and database `namma_clinic_local` created.
- [ ] **Migrations:** `python manage.py migrate` executed with zero unapplied migrations.
- [ ] **RBAC Seed:** `seed_role_permissions` executed; 8 roles and 57 permissions verified.
- [ ] **Network Seed:** `seed_demo --confirm-demo-reset` executed with 4 facilities and procurement chain.
- [ ] **Patient Cohort:** `seed_demo_patients --confirm-demo-reset` executed with 10 synthetic patients.
- [ ] **Backend Health:** `http://127.0.0.1:8000/healthz` returns `{"status": "ok"}` and `/readyz` returns `{"status": "ready"}`.
- [ ] **Frontend Dev Server:** Vite dev server running at `http://localhost:3000/`.
- [ ] **Login Verification:** Logged in successfully as Front Desk Officer, Nurse, Doctor, Lab Tech, Pharmacist, and Administrator.
- [ ] **Clinical Flow:** Verified Patients 01 through 10 in their respective queues across Nurse, Doctor, Lab, and Pharmacy consoles.
- [ ] **Ledger Verification:** Verified that dispensing medication decrements inventory in `pharmacy_inventoryledger`.
