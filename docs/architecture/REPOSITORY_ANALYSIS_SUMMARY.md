# Namma Clinic Digital Healthcare Network — Repository Analysis Summary

## 1. Executive Summary

This comprehensive analysis documents the technical, architectural, and operational state of the **Namma Clinic Digital Healthcare Platform** repository (`https://github.com/georgefernandaz2003/namma_clinic.git`) on the new development branch `feature/namma-clinic-demo-data-model`.

The repository represents an advanced, multi-tier digital health platform built for Urban Health & Wellness Centres (UHWC / Namma Clinics) and tiered secondary/tertiary hospital networks. The platform implements an end-to-end clinical journey (Intake, Triage, Consultation, Laboratory Diagnostics, FEFO Pharmacy, and Closed-Loop Specialist Referrals).

However, rigorous inspection of the source code reveals critical discrepancies between existing marketing documentation and the actual implementation:
- **Orphaned Modules**: Maternal (`apps/maternal`) and Child (`apps/child`) health apps exist in the filesystem with models, but are completely uninstalled from `settings.py`, have no database tables, and the frontend screen (`MaternalChild.tsx`) is 100% hardcoded static HTML.
- **Relational Disconnects**: `PrescriptionItem.medicine_name` is a string without foreign key linkage to `MedicineMaster`, and `Referral` lacks a foreign key link to the encounter (`Visit`).
- **Dashboard Data Integrity Gotchas**: Several KPIs rely on hardcoded backend fallbacks (e.g. `or 14`), client-side pagination slicing (caps at 50 items), and `DoctorDashboard.tsx` displays completed referrals under the title "Follow-ups".
- **DHO Route Guard Barrier**: The District Health Officer role is blocked from visiting `/patients`, `/ncd`, `/surveillance`, and `/maternal-child` due to frontend route guard restrictions in `ROLE_ALLOWED_PATHS`.

---

## 2. Architecture Overview

The system employs a client-server Single Page Application (SPA) architecture:
- **Frontend Layer**: React 19, TypeScript, Vite, TailwindCSS (v4), Lucide Icons, Recharts, Axios.
- **Backend Layer**: Python 3.11, Django 4.2, Django REST Framework (DRF), SimpleJWT Authentication.
- **Database Layer**: SQLite 3 (`backend/db.sqlite3`), with schema migrations tracked across 22 active local apps.
- **Topology Model**: 4-tier healthcare delivery tree connecting Village Satellite Clinics $\rightarrow$ Rural Primary Clinics $\rightarrow$ Sub-District UPHCs $\rightarrow$ District Tertiary Hospitals.

---

## 3. Backend Implementation

- **Django Version**: 4.2 LTS (`Django>=4.2.0,<5.0.0`)
- **DRF**: 3.14.0 with SimpleJWT Bearer tokens (7-day access token lifetime, 30-day refresh token).
- **Application Apps**: 24 directories exist inside `backend/apps/`. **22 are actively registered** in `INSTALLED_APPS`; **2 are uninstalled** (`child` and `maternal`).
- **Audit Middleware**: `apps.audit.middleware.AuditLogMiddleware` captures all incoming mutation and access requests with user snapshots, facility context, IP address, and timestamps.
- **Data Reset**: `/api/admin/reset-demo/` executes `seed_demo` management command atomically in SQLite to reset demo state on demand.

---

## 4. Frontend Implementation

- **React Version**: 19.2.8 with React Router DOM 7.18.3.
- **Design System**: Modern TailwindCSS v4 with glassmorphism panels, color-coded clinical urgency badges, and responsive tables.
- **Navigation & Routing**: Protected routes enforce `isPathAllowedForRole` based on `ROLE_ALLOWED_PATHS`.
- **API Client**: Centralized Axios instance (`frontend/src/services/api.ts`) configured with `baseURL = 'http://localhost:8000/api/'` and automatic bearer token injection.

---

## 5. Database & Schema

- **Engine**: SQLite 3 (`backend/db.sqlite3`).
- **Active Tables**: 54 physical database tables (including Django auth, sessions, contenttypes).
- **Entities Analyzed**: 38 active domain models.
- **Schema Snapshot**: Raw SQL backup stored in `database/db.sql`.

---

## 6. Data Model Integrity

The core clinical tables form a clean 1:1 progression:
`Visit` $\leftrightarrow$ `Token` (1:1)  
`Visit` $\leftrightarrow$ `TriageVitals` (1:1)  
`Visit` $\leftrightarrow$ `Consultation` (1:1)  
`Consultation` $\leftrightarrow$ `Prescription` (1:1)  
`LabOrder` $\leftrightarrow$ `LabSample` (1:1)  
`LabOrder` $\leftrightarrow$ `LabResult` (1:1)  
`Referral` $\leftrightarrow$ `ReferralResponse` (1:1)  

However, key relational bridges are missing:
1. `PrescriptionItem` has no foreign key to `MedicineMaster`.
2. `Referral` has no foreign key to `Visit` or `Consultation`.
3. `NCDRecord` and `DiseaseCase` are standalone tables not linked to encounters.

---

## 7. Patient Journey Traceability

The platform supports a continuous patient journey:
1. **Intake**: Citizen registered $\rightarrow$ UHID issued $\rightarrow$ Slum vulnerability tagged.
2. **Queue**: OPD token allocated with emergency prioritization.
3. **Triage**: Nurse vitals collected $\rightarrow$ Dynamic risk flags triggered.
4. **Consultation**: Doctor reviews pre-triage vitals, diagnoses ICD-10 condition, issues e-prescription, and orders lab tests.
5. **Diagnostics**: Specimen collected $\rightarrow$ Barcode generated $\rightarrow$ Result verified $\rightarrow$ Result synced to patient timeline.
6. **Pharmacy**: Doctor prescription retrieved $\rightarrow$ FEFO engine auto-selects earliest expiring batch $\rightarrow$ Stock deducted.
7. **Referral**: Urgency-tagged referral routed to higher-tier specialist hospital $\rightarrow$ Specialist logs findings and return advice $\rightarrow$ Loop closed.
8. **Continuity**: Follow-up appointment scheduled and tracked on EMR timeline.

---

## 8. Dashboard Architecture

The main dashboard (`/`) dispatches role-specific components based on `user.role`:
- `DistrictOfficerDashboard`: High-level district footfall, active facility table, referrals, and alert console.
- `HospitalAdminDashboard`: Facility-level stage flow progression (Registration $\rightarrow$ Triage $\rightarrow$ Doctor $\rightarrow$ Lab $\rightarrow$ Pharmacy $\rightarrow$ Completed).
- `DoctorDashboard`: Active called patient queue, triage vitals banner, lab pending count.
- `NurseDashboard`: Triage vitals entry station, emergency risk flags.
- `LabTechnicianDashboard`: Diagnostic test verification console.
- `PharmacistDashboard`: FEFO automated dispensing desk.

---

## 9. Dashboard Data Lineage & Discrepancies

1. **Hardcoded Fallbacks**:
   - `total_medicines` uses `batches.values('medicine').distinct().count() or 14`.
   - `registration` flow uses `registered_today or todays_opd`.
2. **Misattributed Metric**:
   - In `DoctorDashboard.tsx`, the **Follow-ups** card renders `summary?.referrals_summary?.completed` instead of counting `FollowUp` rows.
3. **Frontend Pagination Slicing**:
   - `PharmacistDashboard.tsx` computes counts using `.filter()` on the first 50 items returned by `prescriptions/`.
4. **Hardcoded Alert Text**:
   - In `Surveillance.tsx`, the fever outbreak alert banner is static text.

---

## 10. Demo Data Generation

All demonstration data is generated by `apps/accounts/management/commands/seed_demo.py`:
- Flushes existing records in atomic transaction.
- Seeds 4 interconnected facilities (Victoria Hospital, Indiranagar UPHC, Varthur Rural Clinic, Gunjur Satellite Clinic).
- Creates 12 pre-configured user accounts covering every operational role.
- Generates 38 registered citizens with ABHA identities and slum tags.
- Establishes a complete 8-step clinical journey for patient **Ramesh Kumar Gowda** (UHID: `NC-20260901-001`).

---

## 11. Role-Based Access Control (RBAC)

- 6 active roles in `RoleChoices`: `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST`.
- Backend enforces facility and district boundary scoping (`HasFacilityScope`).
- District Officer has read-only access and is blocked from clinical/procurement mutations.

---

## 12. DHO Readiness Assessment

- **Overall Status**: **PARTIAL**
- **Strengths**: Can view district facility matrix, total patient footfall, active referral transfers, and clinic exceptions.
- **Deficiencies**: DHO is blocked from accessing `/patients`, `/ncd`, `/surveillance`, and `/maternal-child` due to frontend route guard configurations in `ROLE_ALLOWED_PATHS`.

---

## 13. Demo Readiness Scorecard

- **Overall Client Demo Readiness**: **85%**
- **Core Citizen Care Flow**: **100% (READY)**
- **Pharmacy FEFO Dispensing**: **100% (READY)**
- **Closed-Loop Specialist Referrals**: **100% (READY)**
- **Diagnostics Pipeline**: **100% (READY)**
- **Maternal & Child Health Module**: **0% (MOCKED / HARDCODED)**
- **DHO Public Health Navigation**: **50% (ROUTE GUARD BLOCKED)**

---

## 14. Data Discrepancy Classification

| Issue ID | Severity | Category | Description |
| :--- | :---: | :--- | :--- |
| **DISC-01** | **CRITICAL** | Data Architecture | `PrescriptionItem.medicine_name` is an unconstrained string, lacking FK to `MedicineMaster`. |
| **DISC-02** | **CRITICAL** | Module Completeness | `apps.maternal` and `apps.child` are uninstalled; `MaternalChild.tsx` renders static mock JSX. |
| **DISC-03** | **HIGH** | Dashboard Accuracy | `DoctorDashboard.tsx` displays completed referrals under the title "Follow-ups". |
| **DISC-04** | **HIGH** | Dashboard Accuracy | Backend reports view uses fallback `or 14` for medicine counts. |
| **DISC-05** | **HIGH** | Dashboard Accuracy | `PharmacistDashboard.tsx` computes metrics via `.filter()` on paginated 50-record slices. |
| **DISC-06** | **HIGH** | RBAC / Authorization | `DISTRICT_OFFICER` cannot navigate to `/patients`, `/ncd`, or `/surveillance` due to route guards. |
| **DISC-07** | **MEDIUM** | Referential Integrity| `Referral` entity does not link to `Visit` or `Consultation`. |
| **DISC-08** | **MEDIUM** | Surveillance | Fever cluster alert banner in `Surveillance.tsx` is static text. |
| **DISC-09** | **LOW** | Schema Dump | `database/db.sql` is an older export missing `Vendor`, `PurchaseOrder`, and `PatientDocument`. |

---

## 15. Recommended Implementation Phases

Following client review and approval of this analysis, development should proceed in 4 phases:

```
+-------------------------------------------------------------------------+
| PHASE A: RBAC & ROUTE GUARD CORRECTION                                  |
| - Update ROLE_ALLOWED_PATHS to permit DHO access to public health pages |
| - Correct Doctor Dashboard Follow-up metric to query FollowUp table     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| PHASE B: DATA INTEGRITY & REFERENTIAL INTEGRITY FIXES                   |
| - Add Foreign Key from PrescriptionItem to MedicineMaster               |
| - Add Foreign Key from Referral to Visit / Consultation                 |
| - Eliminate backend fallback operators ('or 14') in DashboardSummaryView|
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| PHASE C: MATERNAL & CHILD (RCH) ACTIVATION                              |
| - Register apps.maternal and apps.child in settings.py                  |
| - Create Django migrations and DRF ViewSets / serializers               |
| - Connect frontend MaternalChild.tsx to live API endpoints              |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| PHASE D: DHO COMMAND CENTRE & EPIDEMIC ANALYTICS ENHANCEMENT            |
| - Build dynamic 7-day fever anomaly calculation for Surveillance        |
| - Finalize multi-facility aggregation reports and CSV data export       |
+-------------------------------------------------------------------------+
```
