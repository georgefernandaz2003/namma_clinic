# Namma Clinic — Data Model Gap Analysis

This document provides a gap analysis comparing the **Current Repository Data Model** against the full operational scope required for the Namma Clinic Digital Health Network and Urban Public Health Command Platform.

---

## Comparative Domain Evaluation Matrix

| Conceptual Domain | Sub-Component / Entity Requirement | Current Implementation Status | Existing Repository Evidence | Identified Deficiencies & Critical Gaps |
| :--- | :--- | :---: | :--- | :--- |
| **A. Organization** | **District** | **CURRENTLY EXISTS** | `geography_district` | Maps to State, code, name. |
| | **Zone** | **CURRENTLY EXISTS** | `geography_zone` | Maps to District. |
| | **Ward** | **CURRENTLY EXISTS** | `geography_ward` | Captures ward number, population, slum population. |
| | **Facility** | **CURRENTLY EXISTS** | `facilities_facility` | Covers 10 facility types, hierarchy, lat/lng, bed count, services. |
| | **Facility Topology Graph** | **CURRENTLY EXISTS** | `facilities_facilityrelationship` | Connects facilities with distance, urgency, referral priority. |
| **B. Citizen** | **Household** | **PARTIAL** | `patients_household` | Model exists, but has no foreign key linking individual `Patient` records to the `Household`. |
| | **Patient Master** | **CURRENTLY EXISTS** | `patients_patient` | UHID, demographics, address, ward, mobile, registration date. |
| | **ABHA Identity** | **PARTIAL** | `patients_patient.ABHA_ID_DEMO` | Stores simulated ABHA string. Lacks ABHA Address, Care Contexts, ABDM linking artifacts. |
| | **Slum / Vulnerability Context**| **CURRENTLY EXISTS** | `patients_patient.vulnerability_information` | Captures text tag (e.g. BPL Slum Resident, Senior Citizen, High Risk ANC). |
| | **Patient Documents / Records** | **CURRENTLY EXISTS** | `patients_patientdocument` | Categorized file uploads with mime type and patient linking. |
| **C. Workforce** | **User Accounts** | **CURRENTLY EXISTS** | `accounts_user` | Extends AbstractUser with full name, phone. |
| | **Roles (RBAC)** | **PARTIAL** | `accounts_user.role` | 6 roles: `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST`. `PUBLIC_HEALTH_OFFICER` missing from model enum. |
| | **Facility / District Scope** | **CURRENTLY EXISTS** | `accounts_user.assigned_facility`, `assigned_district` | Scope enforcement middleware and query filtering active. |
| **D. Clinical** | **Encounter / Visit** | **CURRENTLY EXISTS** | `visits_visit` | Encapsulates arrival time, OPD date, queue state, assigned doctor. |
| | **Token / Queue Engine** | **CURRENTLY EXISTS** | `visits_token` | Token sequencing per facility per day with emergency priority. |
| | **Triage Vitals** | **CURRENTLY EXISTS** | `triage_triagevitals` | BP, Pulse, SpO2, Temp, Glucose, BMI, auto-computed risk flags. |
| | **Consultation EMR** | **CURRENTLY EXISTS** | `consultations_consultation` | Chief complaint, history, assessment, notes, follow-up date. |
| | **Diagnosis Coding** | **PARTIAL** | `consultations_consultation.diagnosis_code` | Stored as plain CharField string (e.g. 'E11.9 / I10') rather than a structured ICD-10 Master entity. |
| **E. Diagnostics** | **Approved 14 Lab Catalogue** | **CURRENTLY EXISTS** | `laboratory_labtestmaster` | Seeded with 14 essential tests, units, reference ranges. |
| | **Lab Orders** | **CURRENTLY EXISTS** | `laboratory_laborder` | Linked to patient, doctor, facility, consultation. |
| | **Specimen Collection** | **CURRENTLY EXISTS** | `laboratory_labsample` | 1:1 with LabOrder, sample barcode, collection timestamp. |
| | **Lab Result & Verification** | **CURRENTLY EXISTS** | `laboratory_labresult` | Result value, interpretation flag (NORMAL, HIGH, LOW, CRITICAL), tech verification. |
| **F. Pharmacy** | **Essential Drug List (EDL)** | **CURRENTLY EXISTS** | `pharmacy_medicinemaster` | Generic name, brand, dosage form, strength, reorder levels. |
| | **FEFO Batch Inventory** | **CURRENTLY EXISTS** | `pharmacy_medicinebatch` | Batch number, expiry date, mfg date, quantity, ordered by expiry. |
| | **Vendor / Procurement PO** | **CURRENTLY EXISTS** | `pharmacy_vendor`, `purchaseorder`, `purchaseorderitem` | Full PO lifecycle, approval flow, order items, spend tracking. |
| | **Inventory Transactions** | **CURRENTLY EXISTS** | `pharmacy_inventorytransaction` | Audit ledger for purchases, dispensing, wastage, returns. |
| | **Prescriptions** | **CURRENTLY EXISTS** | `consultations_prescription` | 1:1 with Consultation, tracks dispense status. |
| | **Prescription Items** | **PARTIAL** | `consultations_prescriptionitem` | **CRITICAL GAP**: `medicine_name` is stored as plain string, with **no Foreign Key** to `MedicineMaster` or `MedicineBatch`. |
| | **FEFO Automated Dispensing** | **CURRENTLY EXISTS** | `DispenseMedicineView` | Matches medicine name string to earliest non-expired batch and decrements stock. |
| **G. Referral** | **Referral Initiation** | **PARTIAL** | `referrals_referral` | Has patient, source, destination, urgency. **Missing Foreign Key to `Visit` or `Consultation`**. |
| | **Destination Tracking** | **CURRENTLY EXISTS** | `referrals_referral.destination_facility` | Enforces routing across network hierarchy. |
| | **Specialist Feedback Loop** | **CURRENTLY EXISTS** | `referrals_referralresponse` | Findings, treatment summary, return advice to primary clinic. |
| | **Scheduled Follow-up** | **CURRENTLY EXISTS** | `referrals_followup` | Due dates, overdue calculation, category tracking. |
| **H. Public Health** | **NCD Registry** | **PARTIAL** | `ncd_ncdrecord` | Captures HTN/DM diagnosis and control status. **Not linked to clinical encounter or vitals**. |
| | **Maternal Health (ANC/PNC)** | **MISSING** | `apps/maternal/models.py` (Orphaned) | Model exists in directory but **not in `INSTALLED_APPS`**, no DB table, no API endpoints. Frontend is static HTML. |
| | **Child Health / Immunization** | **MISSING** | `apps/child/models.py` (Orphaned) | Model exists in directory but **not in `INSTALLED_APPS`**, no DB table, no API endpoints. Frontend is static HTML. |
| | **Disease Surveillance** | **PARTIAL** | `surveillance_diseasecase` | Records disease cases by ward/facility. **Not derived from clinical consultation diagnosis codes**. |
| | **Community Outreach** | **CURRENTLY EXISTS** | `outreach_outreachactivity` | Slum surveys, persons screened, vulnerable population identified. |
| | **Wellness Sessions** | **CURRENTLY EXISTS** | `wellness_wellnesssession` | AYUSH yoga sessions, participants count, venue, instructor. |
| **I. Governance** | **Arogya Raksha Samithi (ARS)** | **CURRENTLY EXISTS** | `ars_arsmeeting`, `arsmember`, `arsactionitem` | Committee members, meetings, untied funds expenditure, action items. |
| | **Quality & Kayakalpa** | **CURRENTLY EXISTS** | `quality_qualitychecklist` | Cleanliness scores, infection control audit status, corrective actions. |
| | **Biomedical Waste (BMW)** | **CURRENTLY EXISTS** | `quality_biomedicalwastelog` | Color-coded 4-category disposal logging (Yellow, Red, White, Blue). |
| | **Facility Infrastructure** | **CURRENTLY EXISTS** | Oxygen, Consumables, Maintenance Tickets, Bed Capacity & Allocations. | High completeness across physical clinic infrastructure assets. |
| **J. Security** | **Role-Based Access Control** | **CURRENTLY EXISTS** | `apps.accounts.permissions` | Permission codes mapped per role, facility scoping enforced. |
| | **Audit Trail Logging** | **CURRENTLY EXISTS** | `apps.audit.middleware`, `audit_auditlog` | Captures request action, user, facility, IP, timestamp. |
| | **Consent Management** | **MISSING** | None | No ABDM-style electronic consent artifact table exists yet. |

---

## Summary of Critical Gaps Requiring Target Architecture

1. **Orphaned Maternal & Child RCH Models**:
   - `MaternalRecord` and `ChildRecord` must be integrated into `INSTALLED_APPS`, migrated, and wired into REST endpoints so that `MaternalChild.tsx` functions on dynamic database records.
2. **Disconnected Prescription Items**:
   - `PrescriptionItem` requires a direct foreign key to `MedicineMaster` (and batch allocation tracking) rather than relying on string matching during dispensing.
3. **Disconnected Referral & Clinical Journey**:
   - `Referral` must maintain a foreign key to `Visit` / `Consultation` so the specialist referral can be traced directly to the encounter during which it was recommended.
4. **Independent Public Health Islands**:
   - `NCDRecord` and `DiseaseCase` should be generated or updated automatically as side-effects of Doctor Consultations and Nurse Triage, rather than remaining detached standalone data entries.
5. **DHO Role Scope Restriction**:
   - Route guard `ROLE_ALLOWED_PATHS` must grant `DISTRICT_OFFICER` access to `/patients`, `/ncd`, `/surveillance`, and `/maternal-child`.
