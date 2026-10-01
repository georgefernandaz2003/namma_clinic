# Namma Clinic — Current Application Inventory
**Branch:** `feature/namma-clinic-demo-data-model`  
**Audit Date:** September 21, 2026  
**Auditor:** Implementation Engineer (PM + RSA Review Process)  
**Status Gate:** Phase C Quality Audit  

---

## 1. Executive Summary & Inventory Scope

This inventory comprehensively documents all active client-visible routes, frontend components, underlying backend APIs, Django applications, relational database models, role authorizations, and operational readiness classifications across the Namma Clinic Digital Healthcare platform.

### Classification Taxonomy
- **COMPLETE**: Full vertical integration (UI $\leftrightarrow$ API $\leftrightarrow$ DB), realistic data, error handling, role scoped.
- **PARTIAL**: Operational, but has design gaps, missing validations, partial workflows, or UI fallbacks.
- **BROKEN**: Route registered but unreachable (HTTP 403 for all roles), broken API, or unhandled crashes.
- **MOCKED**: Hardcoded client-side components with simulated delays, dummy data, or disconnected APIs.
- **STATIC**: Read-only display without dynamic CRUD or interactive persistence.
- **UNUSED**: Backend models/endpoints exist but have 0 database rows and are unlinked in active workflows.
- **UNKNOWN**: Status cannot be verified against current specifications.

---

## 2. Complete Application Inventory Table

| # | Module | Route | Frontend Component | Backend API Endpoint | Backend App & Database Model(s) | Authorized Roles | Status | Operational Observations |
|---|---|---|---|---|---|---|---|---|
| 1 | **Authentication** | `/login` | `Login.tsx` | `POST /api/auth/token/`<br>`GET /api/auth/me/` | `apps.accounts`<br>`User` | Public / All Roles | **COMPLETE** | Secure JWT issuance and profile retrieval. Quick-login role switcher for demo persona toggling. |
| 2 | **Executive Dashboard** | `/` | `Dashboard.tsx` | `GET /api/dashboard/summary/` | `apps.reports`<br>`Visit`, `Patient`, `MedicineBatch`, `Referral`, `FollowUp`, `LabOrder`, `Alert` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST` | **COMPLETE** | Live multi-metric aggregation, date-picker, facility selector, and role-tailored action items. Verified 0 global hardcoded KPI cards. |
| 3 | **Healthcare Network** | `/network` | `HealthcareNetwork.tsx` | `GET /api/facilities/hierarchy/`<br>`GET /api/facilities/network-graph/`<br>`GET /api/facilities/{id}/` | `apps.facilities`<br>`Facility`, `FacilityRelationship` | `DISTRICT_OFFICER` | **COMPLETE** | Interactive dual-mode visualizer (Hierarchical Tree and Network Graph). Displays parent-child referral topology. |
| 4 | **Facilities Master** | `/facilities` | `Facilities.tsx` | `GET /api/facilities/` | `apps.facilities`<br>`Facility`, `District`, `Zone`, `Ward` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | **COMPLETE** | Tabular directory of primary, secondary, and tertiary facilities with geo-coordinates and operational capacity. |
| 5 | **Patient Directory & Registration** | `/patients` | `Patients.tsx` | `GET /api/patients/`<br>`POST /api/patients/`<br>`POST /api/visits/` | `apps.patients`, `apps.visits`<br>`Patient`, `Visit`, `Token` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE` | **PARTIAL** | Duplicate detection only matches exact `name` + `mobile`. `vulnerability_information` is hardcoded to `'Slum Resident BPL'`. Random 4-digit ID generator (`NC-KA-2026-XXXX`) has collision risk. |
| 6 | **Patient Detail & Unified EMR** | `/patients/:id` | `PatientDetail.tsx` | `GET /api/patients/{id}/records/`<br>`GET /api/patients/{id}/timeline/`<br>`GET/POST /api/patients/{id}/documents/` | `apps.patients`, `apps.visits`, `apps.triage`, `apps.consultations`, `apps.laboratory`, `apps.referrals`<br>`Patient`, `Visit`, `TriageVitals`, `Consultation`, `Prescription`, `LabOrder`, `Referral`, `FollowUp`, `PatientDocument` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE` | **PARTIAL** | Complete longitudinal timeline. Document attachment subsystem exists but has 0 seeded records. Facility scope guard correctly enforces referral continuity access. |
| 7 | **OPD Queue & Token Engine** | `/queue` | `Queue.tsx` | `GET /api/visits/`<br>`GET /api/visits/history-summary/`<br>`POST /api/visits/call-next/`<br>`POST /api/visits/{id}/transition-status/` | `apps.visits`<br>`Visit`, `Token`, `VisitStatusHistory` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST` | **PARTIAL** | Tokens auto-generate sequentially. **Defect:** `DOCTOR` and `HOSPITAL_ADMIN` cannot invoke `call-next` or `transition-status` because backend requires `queue.update` which is only granted to `NURSE`. |
| 8 | **Nurse Vitals & Triage** | `/triage` | `Triage.tsx` | `GET /api/visits/?queue=TRIAGE`<br>`POST /api/triage/` | `apps.triage`, `apps.visits`<br>`TriageVitals`, `Visit` | `NURSE` | **COMPLETE** | Captures systolic/diastolic BP, pulse, glucose, temperature, height, weight. Auto-computes BMI and clinical warning flags (High BP, Fever, etc.). Auto-transitions queue to `DOCTOR`. |
| 9 | **Doctor Consultation & EMR** | `/consultation` | `Consultation.tsx` | `GET /api/visits/?queue=DOCTOR`<br>`POST /api/consultations/`<br>`POST /api/prescriptions/`<br>`POST /api/lab/orders/`<br>`POST /api/referrals/`<br>`POST /api/followups/` | `apps.consultations`, `apps.visits`, `apps.laboratory`, `apps.referrals`, `apps.pharmacy`<br>`Consultation`, `Prescription`, `PrescriptionItem`, `LabOrder`, `Referral`, `FollowUp` | `DOCTOR` | **PARTIAL** | Seamless multi-order form. **Defects:** Prepopulates hardcoded clinical text for complaints, history, and assessment. OneToOneField on `Visit` causes 500 error if doctor re-submits an already consulted visit. |
| 10 | **Diagnostics Laboratory** | `/lab` | `Laboratory.tsx` | `GET /api/lab/orders/`<br>`GET /api/lab/tests/`<br>`POST /api/lab/orders/{id}/collect-sample/`<br>`POST /api/lab/orders/{id}/save-result/` | `apps.laboratory`<br>`LabTestMaster`, `LabOrder`, `LabSample`, `LabResult` | `DOCTOR`, `LAB_TECHNICIAN` | **COMPLETE** | 14 Namma Clinic diagnostic test masters. Full sample accession barcode generation, result entry, reference range comparison, and technician verification workflow. |
| 11 | **Pharmacy & Inventory** | `/pharmacy` | `Pharmacy.tsx` | `GET /api/pharmacy/medicines/`<br>`GET /api/pharmacy/batches/`<br>`POST /api/pharmacy/dispense/`<br>`GET /api/pharmacy/dashboard/`<br>`GET /api/pharmacy/alerts/`<br>`GET /api/pharmacy/vendors/`<br>`GET /api/pharmacy/purchase-orders/` | `apps.pharmacy`<br>`MedicineMaster`, `MedicineBatch`, `InventoryTransaction`, `Prescription`, `PrescriptionItem`, `Vendor`, `PurchaseOrder` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `PHARMACIST` | **PARTIAL** | FEFO (First-Expiry-First-Out) dispensing functional and decrements stock. **Defects:** Vendor master and Purchase Order tabs have 0 seeded rows. `PrescriptionItem` status remains `PENDING` on dispense in seed data. |
| 12 | **Referral Network** | `/referrals` | `Referrals.tsx` | `GET /api/referrals/`<br>`POST /api/referrals/{id}/respond/` | `apps.referrals`, `apps.facilities`<br>`Referral`, `ReferralResponse`, `Facility` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR` | **COMPLETE** | Bidirectional cross-facility referral tracking with urgency triage (`ROUTINE`, `URGENT`, `EMERGENCY`). Hospital specialist findings and return advice loop. |
| 13 | **Continuity & Follow-up** | `/followups` | `FollowUps.tsx` | `GET /api/followups/` | `apps.referrals`<br>`FollowUp`, `Patient`, `Facility` | `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE` | **COMPLETE** | Tracks post-referral and chronic disease review dates with overdue/due-today status flags. |
| 14 | **NCD Registry** | `/ncd` | `NCD.tsx` | `GET /api/ncd/` | `apps.ncd`<br>`NCDRecord`, `Patient` | `DISTRICT_OFFICER`, `NURSE` | **COMPLETE** | Hypertension & Diabetes screening registers, CBAC scores, risk stratification, and control status. |
| 15 | **Disease Surveillance (IDSP)** | `/surveillance` | `Surveillance.tsx` | `GET /api/surveillance/` | `apps.surveillance`<br>`DiseaseCase`, `Facility`, `Ward` | `DISTRICT_OFFICER` | **COMPLETE** | S-Form/P-Form communicable disease surveillance, geographic clustering by ward, outbreak threshold alarms (Dengue, Cholera, Typhoid). |
| 16 | **Teleconsultation Workspace** | `/teleconsultation` | `Teleconsultation.tsx` | None (Disconnected) | `apps.telemedicine`<br>`Teleconsultation` (0 rows) | `DOCTOR` | **MOCKED** | Completely fake client-side video simulation. Displays hardcoded patient "Ramesh Kumar (52/M)". "Save Advice" button triggers browser `alert()` and makes zero backend API calls. |
| 17 | **Community Outreach** | `/outreach` | `Outreach.tsx` | `GET /api/outreach/` | `apps.outreach`<br>`OutreachActivity` | `NURSE` | **COMPLETE** | Mobile medical camp tracking, slum area coverage, beneficiaries screened. |
| 18 | **Wellness & Lifestyle** | `/wellness` | `Wellness.tsx` | `GET /api/wellness/` | `apps.wellness`<br>`WellnessSession` | `NURSE` | **COMPLETE** | Yoga, nutrition education, and tobacco cessation sessions conducted at clinic. |
| 19 | **ARS Committee** | `/ars` | `ARS.tsx` | `GET /api/ars/meetings/` | `apps.ars`<br>`ARSMeeting`, `ARSMember`, `ARSActionItem` | None (Blocked) | **BROKEN** | Route registered in `App.tsx` and sidebar, but **omitted from `ROLE_ALLOWED_PATHS` for all roles**. Produces HTTP 403 Forbidden Access Denied screen for every logged-in user. |
| 20 | **Quality & Bio-Medical Waste** | `/quality` | `Quality.tsx` | `GET /api/quality/checklists/`<br>`GET /api/quality/waste-logs/` | `apps.quality`<br>`QualityChecklist`, `BiomedicalWasteLog` | None (Blocked) | **BROKEN** | Route registered in `App.tsx` and sidebar, but **omitted from `ROLE_ALLOWED_PATHS` for all roles**. Produces HTTP 403 Forbidden Access Denied screen for every logged-in user. |
| 21 | **Clinic Infrastructure & Assets** | `/infrastructure` | `Infrastructure.tsx` | `GET/POST /api/facilities-infra/...` | `apps.facilities`<br>5 Infrastructure Models | `HOSPITAL_ADMIN`, `PHARMACIST` | **COMPLETE** | Real-time oxygen manifold monitoring, consumable buffer stock, maintenance ticket dispatch, bed allocation. |
| 22 | **Public Health Reports & CSV** | `/reports` | `Reports.tsx` | `GET /api/reports/export/` (Hardcoded URL) | `apps.reports`<br>`ReportExportLog` (0 rows) | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | **PARTIAL** | **Defects:** Hardcodes `http://localhost:8000/api/reports/export/` instead of environment API base. Exporting `ncd` or `surveillance` silently falls through to export Patient Master CSV. |
| 23 | **Alert & Escalation Engine** | `/alerts` | `Alerts.tsx` | `GET /api/alerts/`<br>`PATCH /api/alerts/{id}/` | `apps.alerts`<br>`Alert` | `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST` | **COMPLETE** | Multi-category alerts (Critical Vitals, Outbreak Spikes, Stock Out, Expired Batches) with role-based acknowledgement. |
| 24 | **Ecosystem Connectors (Mock)** | `/integrations` | `Integrations.tsx` | `GET /api/integrations/` | `apps.integrations`<br>`IntegrationConfiguration` | None (Blocked) | **BROKEN** | Route registered but **omitted from `ROLE_ALLOWED_PATHS` for all roles** (HTTP 403). UI has simulated sync button with hardcoded `setTimeout` and demo banner. |
| 25 | **Namma Compliance (IPHS)** | `/compliance` | `Compliance.tsx` | `GET /api/compliance/` | `apps.compliance`<br>`ComplianceItem` | `DISTRICT_OFFICER` | **COMPLETE** | Karnataka Urban HWC standard operating procedure checklist verification. |
| 26 | **Security Audit Trail** | `/audit` | `Audit.tsx` | `GET /api/audit/` | `apps.audit`<br>`AuditLog` | `DISTRICT_OFFICER` | **COMPLETE** | Immutable actor logging (IP address, user, role, action, target entity, timestamp). |

---

## 3. Statistical Inventory Breakdown

- **Total Registered Frontend Pages/Routes:** 26
- **Complete & Functionally Validated:** 17 (65.4%)
- **Partially Functional (Defects / Inconsistencies):** 5 (19.2%)
- **Broken / Unreachable Routes (HTTP 403 Guard Block):** 3 (11.5%) (`/ars`, `/quality`, `/integrations`)
- **Completely Mocked / Disconnected:** 1 (3.8%) (`/teleconsultation`)
- **Dormant Tables (0 Database Rows):** 7 (`Household`, `PatientDocument`, `Vendor`, `PurchaseOrder`, `PurchaseOrderItem`, `Teleconsultation`, `ReportExportLog`)
