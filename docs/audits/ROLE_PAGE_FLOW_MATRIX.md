# Namma Clinic — Role-Page Flow Matrix & Contract Analysis

## 1. Application Page Inventory

Total Active Pages: **25** | Total Active Routes: **25** | Total Active Production Roles: **6**

| # | Page Component | Route Path | Permitted Roles | Primary Operational Purpose | Input Data | Backend APIs Called | Data Created / Mutated | Expected Next Page |
|---|---|---|---|---|---|---|---|---|
| 1 | `Login.tsx` | `/login` | Public (Unauthenticated) | System authentication & demo role selection | Username, password | `POST /api/auth/token/`, `GET /api/auth/me/` | JWT access/refresh tokens in localStorage | `/` (Dashboard) |
| 2 | `Dashboard.tsx` | `/` | All 6 Roles | Role-specific primary operational command deck | Date filter, facility context | `GET /api/dashboard/summary/`, role-specific sub-APIs | None (read-only telemetry) | Role workflow pages (`/triage`, `/queue`, `/consultation`, etc.) |
| 3 | `HealthcareNetwork.tsx` | `/network` | `DISTRICT_OFFICER` | Interactive facility hierarchy and referral network topology | View mode toggle (TREE/GRAPH), facility selection | `GET /api/facilities/hierarchy/`, `GET /api/facilities/network-graph/`, `GET /api/facilities/{id}/` | None (read-only visualization) | `/facilities`, `/reports` |
| 4 | `Facilities.tsx` | `/facilities` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Clinic directory, service capability master, bed allocations | Facility search/filter | `GET /api/facilities/` | None (directory view) | `/infrastructure`, `/network` |
| 5 | `Patients.tsx` | `/patients` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE` | Citizen master index, registration, OPD token issuing | Demographics, mobile, ABHA, address, vulnerability | `GET /api/patients/`, `POST /api/patients/`, `POST /api/visits/` | Creates `Patient`, generates UHID, creates `Visit` & `Token` | `/patients/:id`, `/queue` |
| 6 | `PatientDetail.tsx` | `/patients/:id` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE` | Unified 360-degree patient longitudinal EMR history & documents | Tab selection, file upload | `GET /api/patients/{id}/timeline/`, `GET /api/patients/{id}/records/`, `POST/GET /api/patients/{id}/documents/` | Uploads `PatientDocument` | `/patients`, `/queue` |
| 7 | `Queue.tsx` | `/queue` | All 6 Roles | Real-time multi-stage date-based OPD queue management | Date selector, queue tab, search | `GET /api/visits/`, `POST /api/visits/call-next/`, `POST /api/visits/` | Transitions `Visit.status` & `Visit.current_queue` | `/triage`, `/consultation`, `/lab`, `/pharmacy` |
| 8 | `Triage.tsx` | `/triage` | `NURSE` | Pre-consultation physiological vitals logging & risk alerts | BP, pulse, temp, SpO2, glucose, height, weight, notes | `GET /api/visits/?queue=TRIAGE`, `POST /api/triage/` | Creates `TriageVitals`, transitions visit to `WAITING_FOR_DOCTOR` | `/queue` |
| 9 | `Consultation.tsx` | `/consultation` | `DOCTOR` | Clinical encounter EMR, diagnoses, prescription, lab, referral | History, exam, ICD diagnosis, medicines, lab tests, referral | `GET /api/visits/?queue=DOCTOR`, `GET /api/triage/?visit={id}`, `GET /api/lab/tests/`, `GET /api/pharmacy/medicines/`, `POST /api/consultations/`, `POST /api/referrals/`, `POST /api/lab/orders/`, `POST /api/followups/` | Creates `Consultation`, `Prescription`, `PrescriptionItem`, `LabOrder`, `Referral`, `FollowUp`; updates `Visit` | `/queue` |
| 10 | `Laboratory.tsx` | `/lab` | `DOCTOR`, `LAB_TECHNICIAN` | Diagnostic test catalogue, specimen barcodes, results release | Specimen type, barcode, test value, unit, flags, notes | `GET /api/lab/orders/`, `GET /api/lab/tests/`, `POST /api/lab/orders/{id}/collect-sample/`, `POST /api/lab/orders/{id}/save-result/` | Creates `LabSample`, creates `LabResult`, updates `LabOrder.status` to `COMPLETED` | `/queue`, `/patients/:id` |
| 11 | `Pharmacy.tsx` | `/pharmacy` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `PHARMACIST` | Prescriptions, FEFO batch dispensing, inventory, POs, vendors | Dispense confirmation, PO forms, vendor details | `GET /api/pharmacy/dashboard/`, `GET /api/pharmacy/prescriptions/`, `POST /api/pharmacy/dispense/`, `POST/PATCH /api/pharmacy/purchase-orders/`, `POST /api/pharmacy/vendors/` | Creates `InventoryTransaction`, decrements `MedicineBatch`, updates `Prescription.status` to `DISPENSED` | `/queue`, `/infrastructure` |
| 12 | `Referrals.tsx` | `/referrals` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR` | Inter-facility patient transfer management & specialist advice | Specialist response form, findings, advice | `GET /api/referrals/`, `POST /api/referrals/{id}/respond/` | Creates `ReferralResponse`, transitions `Referral.status` | `/patients/:id`, `/network` |
| 13 | `FollowUps.tsx` | `/followups` | `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE` | Outpatient chronic disease follow-up tracking register | Date filter, completion notes | `GET /api/followups/`, `PATCH /api/followups/{id}/` | Updates `FollowUp.status` to `COMPLETED` | `/patients/:id`, `/queue` |
| 14 | `NCD.tsx` | `/ncd` | `DISTRICT_OFFICER`, `NURSE`, `DOCTOR` | Non-communicable disease (HTN, DM) cohort screening register | Search, risk category filter | `GET /api/ncd/` | Aggregates screening records | `/patients/:id`, `/followups` |
| 15 | `Surveillance.tsx` | `/surveillance` | `DISTRICT_OFFICER` | Integrated disease surveillance & ward-level outbreak alarms | Time window, disease filter | `GET /api/surveillance/` | Aggregates communicable disease signals | `/alerts`, `/reports` |
| 16 | `Outreach.tsx` | `/outreach` | `NURSE` | Community field screening camps & slum outreach records | Facility filter | `GET /api/outreach/` | Records outreach event telemetry | `/patients` |
| 17 | `Wellness.tsx` | `/wellness` | `NURSE` | Preventive yoga, lifestyle modification & wellness sessions | Facility filter | `GET /api/wellness/` | Records session attendance metrics | `/dashboard` |
| 18 | `ARS.tsx` | `/ars` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Arogya Raksha Samiti community governance & funds register | Facility filter | `GET /api/ars/meetings/` | Governance audit records | `/quality` |
| 19 | `Quality.tsx` | `/quality` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Kayakalp/NQAS compliance checklist & biomedical waste logs | Facility filter, checklist tab | `GET /api/quality/checklists/`, `GET /api/quality/waste-logs/` | Quality certification tracking | `/compliance` |
| 20 | `Infrastructure.tsx`| `/infrastructure` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `PHARMACIST` | Oxygen cylinder bank, bed capacity, maintenance tickets | Resource tabs, ticket status | `GET /api/facilities-infra/*` (oxygen, beds, consumables, tickets) | Infrastructure logs & tickets | `/facilities` |
| 21 | `Reports.tsx` | `/reports` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Authoritative aggregate clinical reporting & CSV extraction | Report type (OPD, Pharmacy, Referral, NCD, Surveillance) | `GET /api/reports/export/?type=...&facility=...` | Streams authenticated RFC 4180 CSV attachment | `/dashboard` |
| 22 | `Alerts.tsx` | `/alerts` | All 6 Roles | Real-time automated clinical & operational alert feed | Severity filter, acknowledge button | `GET /api/alerts/`, `PATCH /api/alerts/{id}/` | Updates `Alert.is_acknowledged = true` | Return to referring page |
| 23 | `Integrations.tsx` | `/integrations` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | National digital health connectors status (ABDM, ABHA, HMIS) | Simulated sync button | `GET /api/integrations/` | Local simulated sync feedback | `/dashboard` |
| 24 | `Compliance.tsx` | `/compliance` | `DISTRICT_OFFICER` | Namma Clinic regulatory mandate & requirements checklist | Category filter | `GET /api/compliance/` | Compliance scoring view | `/audit` |
| 25 | `Audit.tsx` | `/audit` | `DISTRICT_OFFICER` | Immutable security, access, and clinical change audit ledger | Search, event type filter | `GET /api/audit/` | Audit event query log | `/reports` |

---

## 2. Page Contract Analysis (Representative Workflows)

### A. Nurse Triage (`/triage`)
- **Entry**: Staff Nurse (`nurse`) from navigation or from OPD Queue row ("Triage →").
- **Display**: Waiting visits in `TRIAGE` queue for selected facility. Dynamic BMI calculation, high-risk flag evaluation.
- **Actions**:
  - `Select Patient`: Populates vitals form with patient demographics and initial chief complaint.
  - `Log Nurse Triage & Forward to Doctor Queue`: Sends `POST /api/triage/`.
  - **Correction Applied (FND-FLOW-01)**: Successfully updated to `navigate('/queue')`. Post-triage flow returns cleanly to `/queue` without HTTP 403.
- **Exit**: Successfully triaged visit transitions to `status: WAITING_FOR_DOCTOR`, `current_queue: DOCTOR`.

### B. Doctor Consultation (`/consultation`)
- **Entry**: Medical Officer (`doctor`) from navigation or from Doctor Dashboard ("Start EMR Consultation →").
- **Display**: List of triaged patients waiting in `DOCTOR` queue. Pre-recorded triage vitals (BP, glucose, pulse, temp, SpO2).
- **Actions**:
  - `Add Medicine`: Appends item to prescription list.
  - `Order Lab Tests`: Selects test from 14 Essential Diagnostic Tests catalogue.
  - `Referral`: Selects destination specialist hospital, urgency (`ROUTINE`, `URGENT`, `EMERGENCY`).
  - `Follow-up`: Sets next review date and notes.
  - `Complete Consultation & Issue E-Prescription`: Sends `POST /api/consultations/`, creating Consultation, Prescription, and items.
- **Exit**: Visit transitions to `WAITING_FOR_PHARMACY` in `PHARMACY` queue. Doctor navigates to `/queue`.

### C. Diagnostics Lab (`/lab`)
- **Entry**: Lab Technician (`lab`) or Doctor (`doctor`).
- **Display**: Pending orders in `ORDERED` status.
- **Actions**:
  - `Collect Sample`: Calls `POST /api/lab/orders/{id}/collect-sample/`. Generates unique specimen barcode.
  - `Enter & Verify Result`: Calls `POST /api/lab/orders/{id}/save-result/`. Records value, unit, reference range, flag.
- **Exit**: Order status becomes `COMPLETED`. Result is immediately visible in patient EMR timeline.

### D. Pharmacy & FEFO (`/pharmacy`)
- **Entry**: Pharmacist (`pharmacy`), Hospital Admin (`hospital`), District Officer (`district`).
- **Display**: Pending prescriptions, active batches, near-expiry alerts, stock ledger.
- **Actions**:
  - `Dispense Prescription`: Calls `POST /api/pharmacy/dispense/`. Evaluates earliest expiry batch, decrements stock, records `InventoryTransaction`.
  - `Purchase Orders`: Creates and receives POs against approved vendors.
- **Exit**: Prescription becomes `DISPENSED`. Visit marked `COMPLETED`.

---

## 3. Every-Button Test Table

| Page Component | Button Label / Action | Expected Result | Actual Result | API Called | Status |
|---|---|---|---|---|---|
| `Login.tsx` | "Sign In to Demo Console" | Authenticates user and redirects to `/` | Authenticates, sets JWT, routes to `/` | `POST /api/auth/token/` | **PASS** |
| `DashboardLayout.tsx` | "Reset Demo" | Cleans and resets demo data to pristine state | Confirms via prompt, runs seed command, resets | `POST /api/admin/reset-demo/` | **PASS** |
| `Patients.tsx` | "Register Patient" | Opens registration modal | Opens modal | None (UI State) | **PASS** |
| `Patients.tsx` | "Register & Verify Duplicate Status" | Registers citizen and closes modal | Creates patient, alerts UHID, refreshes list | `POST /api/patients/` | **PASS** |
| `Patients.tsx` | "Issue Daily Token" | Opens token modal for selected patient | Opens modal with patient context | None (UI State) | **PASS** |
| `Patients.tsx` | "Generate Token & Add to Queue" | Creates daily OPD visit | Creates visit with token, closes modal | `POST /api/visits/` | **PASS** |
| `Triage.tsx` | "Log Nurse Triage & Forward" | Saves vitals and returns to queue | Saves vitals, but calls `navigate('/consultation')` (403) | `POST /api/triage/` | **DEFECT (FND-FLOW-01)** |
| `DoctorDashboard.tsx` | "Call Next Waiting Patient" | Calls next patient in DOCTOR queue | Transitions visit to `IN_CONSULTATION` | `POST /api/visits/call-next/` | **PASS** |
| `DoctorDashboard.tsx` | "Start EMR Consultation →" | Opens consultation with called patient | Navigates to `/consultation?visit=X` but patient not preselected | None (URL Nav) | **DEFECT (FND-FLOW-02)** |
| `Consultation.tsx` | "Add Medicine" | Adds item to prescription form | Adds row with dosage/quantity | None (UI State) | **PASS** |
| `Consultation.tsx` | "Complete Consultation & Save" | Saves encounter, prescriptions, orders | Saves consultation, updates visit to PHARMACY | `POST /api/consultations/` | **PASS** |
| `Laboratory.tsx` | "Collect Sample" | Collects specimen and generates barcode | Creates LabSample, updates order to SAMPLE_COLLECTED | `POST /api/lab/orders/{id}/collect-sample/` | **PASS** |
| `Laboratory.tsx` | "Verify & Release Result" | Verifies test result and updates EMR | Creates LabResult, updates order to COMPLETED | `POST /api/lab/orders/{id}/save-result/` | **PASS** |
| `Pharmacy.tsx` | "Dispense Medicines (FEFO)" | Deducts earliest batch and dispenses | Deducts stock, creates InventoryTx, updates Rx | `POST /api/pharmacy/dispense/` | **PASS** |
| `Queue.tsx` | "Call Next Waiting Patient" | Calls next patient in selected queue | Atomically assigns next patient to doctor | `POST /api/visits/call-next/` | **PASS** |
| `Queue.tsx` | Row Action: "Triage →" | Routes nurse to triage for this visit | Navigates to `/triage` (works for nurse, 403 for doctor) | None (URL Nav) | **DEFECT (FND-FLOW-04)** |
| `Queue.tsx` | Row Action: "Consult →" | Routes doctor to consultation | Navigates to `/consultation` (works for doc, 403 for nurse) | None (URL Nav) | **DEFECT (FND-FLOW-04)** |
| `Referrals.tsx` | "Record Specialist Findings" | Saves specialist reply to primary clinic | Creates ReferralResponse, marks completed | `POST /api/referrals/{id}/respond/` | **PASS** |
| `FollowUps.tsx` | "Mark Completed" | Completes scheduled review | Patches status to COMPLETED | `PATCH /api/followups/{id}/` | **PASS** |
| `Reports.tsx` | "Download CSV Export" | Streams CSV file attachment | Downloads authenticated CSV scoped to facility/district | `GET /api/reports/export/` | **PASS** |

---

## 4. Route and Permission Matrix

| Route Path | DISTRICT_OFFICER | HOSPITAL_ADMIN | DOCTOR | NURSE | LAB_TECHNICIAN | PHARMACIST |
|---|---|---|---|---|---|---|
| `/` (Dashboard) | READ | READ | READ | READ | READ | READ |
| `/network` | READ | DENIED | DENIED | DENIED | DENIED | DENIED |
| `/facilities` | READ | READ | DENIED | DENIED | DENIED | DENIED |
| `/patients` | READ | CREATE, READ | READ | CREATE, READ | DENIED | DENIED |
| `/patients/:id` | READ | READ | READ | READ | DENIED | DENIED |
| `/queue` | READ | READ, UPDATE | READ, CALL | READ, CREATE | READ | READ |
| `/triage` | DENIED | DENIED | DENIED | CREATE, UPDATE | DENIED | DENIED |
| `/consultation` | DENIED | DENIED | CREATE, UPDATE | DENIED | DENIED | DENIED |
| `/lab` | DENIED | DENIED | READ | DENIED | CREATE, UPDATE | DENIED |
| `/pharmacy` | READ | READ, CREATE (PO) | DENIED | DENIED | DENIED | CREATE, DISPENSE |
| `/referrals` | READ | READ, UPDATE | CREATE, READ | DENIED | DENIED | DENIED |
| `/followups` | DENIED | READ, UPDATE | CREATE, READ | READ, UPDATE | DENIED | DENIED |
| `/ncd` | READ | DENIED | READ (Granted) | CREATE, READ | DENIED | DENIED |
| `/surveillance` | READ | DENIED | DENIED | DENIED | DENIED | DENIED |
| `/outreach` | DENIED | DENIED | DENIED | READ | DENIED | DENIED |
| `/wellness` | DENIED | DENIED | DENIED | READ | DENIED | DENIED |
| `/ars` | READ | READ | DENIED | DENIED | DENIED | DENIED |
| `/quality` | READ | READ | DENIED | DENIED | DENIED | DENIED |
| `/infrastructure` | READ | READ, UPDATE | DENIED | DENIED | DENIED | READ |
| `/reports` | READ, EXPORT | READ, EXPORT | DENIED | DENIED | DENIED | DENIED |
| `/alerts` | READ, UPDATE | READ, UPDATE | READ, UPDATE | READ, UPDATE | READ, UPDATE | READ, UPDATE |
| `/integrations` | READ | READ | DENIED | DENIED | DENIED | DENIED |
| `/compliance` | READ | DENIED | DENIED | DENIED | DENIED | DENIED |
| `/audit` | READ | DENIED | DENIED | DENIED | DENIED | DENIED |
