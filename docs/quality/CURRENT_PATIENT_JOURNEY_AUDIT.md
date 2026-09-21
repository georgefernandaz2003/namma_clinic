# Namma Clinic — End-to-End Patient Journey Audit
**Branch:** `feature/namma-clinic-demo-data-model`  
**Audit Date:** September 21, 2026  
**Auditor:** Implementation Engineer (PM + RSA Review Process)  
**Status Gate:** Phase C Quality Audit  

---

## 1. Journey Architecture Overview

The citizen healthcare lifecycle in Namma Clinic encompasses 10 transactional transitions across primary, secondary, and tertiary care touchpoints:

```
[1. Registration]  ──>  [2. Visit/Token]    ──>  [3. Queue Waiting]
                              │
                              ▼
                        [4. Nurse Triage]
                              │
                              ▼
                    [5. Doctor Consultation]
                         │         │         │
           ┌─────────────┘         │         └──────────────┐
           ▼                       ▼                        ▼
    [6. Lab Diagnostics]    [7. Prescription]      [9. Referral Network]
           │                       │                        │
           ▼                       ▼                        ▼
    [Result/Verify]         [8. FEFO Dispense]    [10. Hospital Follow-up]
```

---

## 2. Transition-by-Transition Transactional Audit

### Transition 1: Citizen Onboarding $\rightarrow$ Patient Master Registration
- **Source Entity:** Citizen demographic credentials / ABHA ID
- **Destination Entity:** `apps.patients.models.Patient`
- **Foreign Keys:**
  - `Patient.registered_at_facility` $\rightarrow$ `Facility.id` (`on_delete=SET_NULL`, nullable)
  - `Patient.district` $\rightarrow$ `District.id` (`on_delete=SET_NULL`, nullable)
  - `Patient.ward` $\rightarrow$ `Ward.id` (`on_delete=SET_NULL`, nullable)
- **API Endpoint:** `POST /api/patients/` (Handled by `PatientViewSet.create`)
- **Frontend View:** `Patients.tsx` (`PatientRegistrationModal`)
- **Status Transition:** Initial registration (`registration_date = today`)
- **Patient Identity:** Sequential or auto-generated `patient_id` (`NC-KA-2026-XXXX`). Name + Mobile duplicate check implemented.
- **Facility Identity:** Defaults to assigned facility of logged-in staff user (`request.user.assigned_facility_id`).
- **Defects & Broken Links Identified:**
  1. **Seed Data Anomaly:** Patient #216 (`NC-KA-2026-8717`, `Ramesh Kumar Gowda`) has `registered_at_facility = NULL` and `district = NULL`. When a District Officer filters by District 11, Patient #216 is excluded, yet Visit #41 for this exact patient exists at Facility 68.
  2. **Vulnerability Hardcoding:** In `Patients.tsx`, `vulnerability_information` is statically preset to `'Slum Resident BPL'` without any UI dropdown or field for other vulnerable categories (e.g., Construction Worker, Street Vendor, Migrant Laborer).
  3. **ABHA Verification Mock:** `ABHA_ID_DEMO` auto-generates a random string `ABHA-2026-XXXX` if left blank. It does not validate against any checksum, leading to demo confusion regarding whether ABDM M1/M2 verification took place.

---

### Transition 2: Patient Master $\rightarrow$ Daily OPD Visit & Token Generation
- **Source Entity:** `Patient`
- **Destination Entities:** `apps.visits.models.Visit` & `apps.visits.models.Token`
- **Foreign Keys:**
  - `Visit.patient` $\rightarrow$ `Patient.id` (`on_delete=CASCADE`)
  - `Visit.facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
  - `Token.visit` $\rightarrow$ `Visit.id` (`OneToOneField`, `on_delete=CASCADE`, `related_name='token'`)
  - `Token.facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
- **API Endpoint:** `POST /api/visits/` (Handled by `VisitViewSet.create`)
- **Frontend View:** `Queue.tsx` (`NewVisitModal`) & `Patients.tsx` ("New Visit" quick action)
- **Status Transition:** `Visit.status = 'WAITING_FOR_TRIAGE'`, `Visit.current_queue = 'TRIAGE'`, `Token.status = 'WAITING'`
- **Patient & Facility Consistency:** Enforced within a database atomic transaction (`transaction.atomic()`). Tokens are strictly scoped per facility and date (`UniqueConstraint(fields=['facility', 'date', 'token_number'])`).
- **Defects & Broken Links Identified:**
  1. **Duplicate OPD Visit Risk:** There is no check preventing a patient from having multiple active OPD visits created on the exact same date at the same clinic.
  2. **Historic Visit Creation Hole:** While status transitions on past dates are blocked, new visits can theoretically be submitted without validating against future/past date constraints.

---

### Transition 3: OPD Queue $\rightarrow$ Active Queue Calling & Triage Stage
- **Source Entity:** `Visit` (`status='WAITING_FOR_TRIAGE'`) & `Token`
- **Destination Entity:** `apps.visits.models.VisitStatusHistory`
- **Foreign Keys:**
  - `VisitStatusHistory.visit` $\rightarrow$ `Visit.id` (`on_delete=CASCADE`)
  - `VisitStatusHistory.performed_by` $\rightarrow$ `User.id` (`on_delete=SET_NULL`)
- **API Endpoints:**
  - `POST /api/visits/call-next/`
  - `POST /api/visits/{id}/transition-status/`
- **Frontend View:** `Queue.tsx` (Stage columns & Call Next button)
- **Status Transition:** `WAITING_FOR_TRIAGE` $\rightarrow$ `IN_TRIAGE`
- **Defects & Broken Links Identified:**
  1. **CRITICAL RBAC DISCONNECT:** `VisitViewSet` requires permission `'queue.update'` for all `POST` actions. However, `ROLE_PERMISSIONS` in `backend/apps/accounts/permissions.py` only grants `'queue.update'` to `NURSE`. `DOCTOR` and `HOSPITAL_ADMIN` only have `'queue.view'`. Consequently, **any Doctor or Hospital Admin clicking "Call Next Patient" receives an HTTP 403 Forbidden Access Denied error.**
  2. **Skipped Triage in Seed Data:** Visit #39 (`VIS-20260917-003`, Anita Devi) is currently set to `status='WAITING_FOR_DOCTOR'` and `queue='DOCTOR'`, but has **no `TriageVitals` record**. The system permitted an un-triaged patient to bypass vitals assessment.
  3. **Ghost Completed Visits:** Visits #36 and #37 are marked `status='COMPLETED'`, but have 0 triage records, 0 consultation records, and 0 prescription records.

---

### Transition 4: Triage Queue $\rightarrow$ Clinical Vitals Assessment
- **Source Entity:** `Visit` (`IN_TRIAGE`) & `Patient`
- **Destination Entity:** `apps.triage.models.TriageVitals`
- **Foreign Keys:**
  - `TriageVitals.visit` $\rightarrow$ `Visit.id` (`OneToOneField`, `on_delete=CASCADE`, `related_name='triage'`)
  - `TriageVitals.patient` $\rightarrow$ `Patient.id` (`on_delete=CASCADE`)
  - `TriageVitals.nurse` $\rightarrow$ `User.id` (`on_delete=SET_NULL`)
- **API Endpoint:** `POST /api/triage/` (Handled by `TriageVitalsViewSet.create`)
- **Frontend View:** `Triage.tsx`
- **Status Transition:** `Visit.status = 'TRIAGED'`, `Visit.current_queue = 'DOCTOR'`, `Visit.triage_end_time = now()`
- **Defects & Broken Links Identified:**
  1. **OneToOne Crash on Re-entry:** Because `visit` is a `OneToOneField`, if a nurse attempts to adjust or re-submit triage vitals for a patient, the backend crashes with a `django.db.utils.IntegrityError: UNIQUE constraint failed: triage_triagevitals.visit_id` (HTTP 500) instead of executing an update (`PUT/PATCH`).
  2. **Alert Engine Desynchronization:** `TriageVitals.save()` computes clinical flags (`high_bp_flag`, `high_glucose_flag`, `fever_flag`), but **fails to insert an alert into `apps.alerts.models.Alert`**. Critical vitals are therefore invisible in the facility-wide Alert Banner (`Alerts.tsx`).

---

### Transition 5: Doctor Queue $\rightarrow$ Consultation & Provisional Diagnosis
- **Source Entity:** `Visit` (`WAITING_FOR_DOCTOR`) & `TriageVitals`
- **Destination Entity:** `apps.consultations.models.Consultation`
- **Foreign Keys:**
  - `Consultation.visit` $\rightarrow$ `Visit.id` (`OneToOneField`, `on_delete=CASCADE`, `related_name='consultation'`)
  - `Consultation.patient` $\rightarrow$ `Patient.id` (`on_delete=CASCADE`, `related_name='consultations'`)
  - `Consultation.doctor` $\rightarrow$ `User.id` (`on_delete=SET_NULL`)
  - `Consultation.facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
- **API Endpoint:** `POST /api/consultations/` (Handled by `ConsultationViewSet.create`)
- **Frontend View:** `Consultation.tsx`
- **Status Transition:** `WAITING_FOR_DOCTOR` $\rightarrow$ `IN_CONSULTATION` $\rightarrow$ `WAITING_FOR_PHARMACY` / `COMPLETED`
- **Defects & Broken Links Identified:**
  1. **Hardcoded Clinical Content:** In `Consultation.tsx`, `history` is hardcoded to `'Known history of hypertension, poor compliance.'` and `notes` is hardcoded to `'Advised low salt diet, lifestyle modifications, and regular monitoring.'` Doctors during live testing see the same text prepopulated for all patients.
  2. **Queue-Status Desynchronization in Seed Data:** For Visit #40 and Visit #41:
     - `Visit.status = 'COMPLETED'`
     - `Visit.current_queue = 'DOCTOR'` (Should have been `'COMPLETED'`)
     This leaves completed patients visible in active doctor queue queries if filtered purely by `current_queue`.

---

### Transition 6: Consultation $\rightarrow$ Diagnostic Laboratory Orders
- **Source Entity:** `Consultation`
- **Destination Entities:** `apps.laboratory.models.LabOrder`, `LabSample`, `LabResult`
- **Foreign Keys:**
  - `LabOrder.consultation` $\rightarrow$ `Consultation.id` (`on_delete=SET_NULL`, nullable)
  - `LabOrder.patient` $\rightarrow$ `Patient.id` (`on_delete=CASCADE`)
  - `LabOrder.test_master` $\rightarrow$ `LabTestMaster.id` (`on_delete=CASCADE`)
  - `LabOrder.facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
  - `LabSample.lab_order` $\rightarrow$ `LabOrder.id` (`OneToOneField`)
  - `LabResult.lab_order` $\rightarrow$ `LabOrder.id` (`OneToOneField`)
- **API Endpoints:**
  - `POST /api/lab/orders/`
  - `POST /api/lab/orders/{id}/collect-sample/`
  - `POST /api/lab/orders/{id}/save-result/`
- **Frontend View:** `Consultation.tsx` (Test selector) $\rightarrow$ `Laboratory.tsx`
- **Status Transition:** `ORDERED` $\rightarrow$ `SAMPLE_COLLECTED` $\rightarrow$ `RESULT_ENTRY` $\rightarrow$ `VERIFIED`
- **Defects & Broken Links Identified:**
  1. **Missing Visit FK on LabOrder:** `LabOrder` only references `consultation` and `patient`, but lacks a direct foreign key to `Visit`. If a doctor orders a lab test directly from OPD triage or an emergency encounter without creating a `Consultation` record, the order cannot be tied back to the specific visit encounter.
  2. **Visit Queue Not Updated to LAB:** Ordering a lab test does not transition `Visit.current_queue` to `'LAB'`, nor does it set `Visit.status = 'LAB_PENDING'`. The patient remains in the doctor's queue.

---

### Transition 7: Consultation $\rightarrow$ Prescription Generation
- **Source Entity:** `Consultation`
- **Destination Entities:** `apps.consultations.models.Prescription` & `apps.consultations.models.PrescriptionItem`
- **Foreign Keys:**
  - `Prescription.consultation` $\rightarrow$ `Consultation.id` (`OneToOneField`, `related_name='prescription'`)
  - `Prescription.patient` $\rightarrow$ `Patient.id` (`on_delete=CASCADE`)
  - `Prescription.facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
  - `PrescriptionItem.prescription` $\rightarrow$ `Prescription.id` (`on_delete=CASCADE`, `related_name='items'`)
  - `PrescriptionItem.medicine` $\rightarrow$ `MedicineMaster.id` (`on_delete=SET_NULL`, nullable)
- **API Endpoints:**
  - `POST /api/prescriptions/`
  - `POST /api/consultations/` (Atomic composite save)
- **Frontend View:** `Consultation.tsx` (Prescription table) $\rightarrow$ `Pharmacy.tsx`
- **Status Transition:** `Prescription.status = 'ACTIVE'`
- **Defects & Broken Links Identified:**
  1. **Seed Data Inconsistency in Visit #41:**
     - `Prescription #26.status = 'DISPENSED'`
     - `PrescriptionItem #68.status = 'PENDING'`
     - `PrescriptionItem #69.status = 'PENDING'`
     The parent prescription header is marked as fully dispensed, while both individual line items remain in `'PENDING'` state with 0 dispensed units recorded.

---

### Transition 8: Prescription $\rightarrow$ FEFO Pharmacy Dispensing
- **Source Entity:** `Prescription` & `PrescriptionItem`
- **Destination Entities:** `apps.pharmacy.models.MedicineBatch` & `apps.pharmacy.models.InventoryTransaction`
- **Foreign Keys:**
  - `InventoryTransaction.batch` $\rightarrow$ `MedicineBatch.id` (`on_delete=SET_NULL`)
  - `InventoryTransaction.medicine` $\rightarrow$ `MedicineMaster.id` (`on_delete=CASCADE`)
  - `InventoryTransaction.facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
- **API Endpoint:** `POST /api/pharmacy/dispense/` (Handled by `DispenseMedicineView`)
- **Frontend View:** `Pharmacy.tsx` (`PrescriptionDispensingModal`)
- **Status Transition:** `Prescription.status = 'DISPENSED'`, `PrescriptionItem.status = 'DISPENSED'`, `Batch.quantity -= dispensed_qty`
- **Defects & Broken Links Identified:**
  1. **Missing Inventory Ledger Entry:** In seed data for Visit #35, Metformin (Item #64, 28 tablets) generated `InventoryTransaction` #6. However, Amlodipine (Item #65, 14 tablets) was marked dispensed with **no corresponding `InventoryTransaction` ledger entry**.
  2. **Lack of Stock-Out Exception Handling:** If a required medicine batch is exhausted, the API aborts with HTTP 400, but provides no structured alternative flow (such as splitting between batches, substituting equivalents, or recording an out-of-stock emergency requisition).

---

### Transition 9: Consultation $\rightarrow$ Referral Routing
- **Source Entity:** `Consultation` & `Visit`
- **Destination Entities:** `apps.referrals.models.Referral` & `apps.referrals.models.ReferralResponse`
- **Foreign Keys:**
  - `Referral.patient` $\rightarrow$ `Patient.id` (`on_delete=CASCADE`)
  - `Referral.visit` $\rightarrow$ `Visit.id` (`on_delete=SET_NULL`, nullable)
  - `Referral.consultation` $\rightarrow$ `Consultation.id` (`on_delete=SET_NULL`, nullable)
  - `Referral.source_facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
  - `Referral.destination_facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
  - `ReferralResponse.referral` $\rightarrow$ `Referral.id` (`OneToOneField`)
- **API Endpoints:**
  - `POST /api/referrals/`
  - `POST /api/referrals/{id}/respond/`
- **Frontend View:** `Consultation.tsx` (Referral section) $\rightarrow$ `Referrals.tsx`
- **Status Transition:** `CREATED` $\rightarrow$ `ACCEPTED` $\rightarrow$ `IN_TRANSIT` $\rightarrow$ `REACHED` $\rightarrow$ `UNDER_TREATMENT` $\rightarrow$ `COMPLETED`
- **Defects & Broken Links Identified:**
  1. **Referral Urgency Enum Discrepancy:** In `Consultation.tsx`, `refUrgency` defaults to `'HIGH'`, but `Referral.urgency` model choices in Django are `ROUTINE`, `URGENT`, and `EMERGENCY`. Submitting `'HIGH'` falls outside standard model choices.

---

### Transition 10: Referral / Consultation $\rightarrow$ Continuity Follow-Up
- **Source Entity:** `Referral` / `Consultation` / `Patient`
- **Destination Entity:** `apps.referrals.models.FollowUp`
- **Foreign Keys:**
  - `FollowUp.patient` $\rightarrow$ `Patient.id` (`on_delete=CASCADE`)
  - `FollowUp.referral` $\rightarrow$ `Referral.id` (`on_delete=SET_NULL`, nullable)
  - `FollowUp.visit` $\rightarrow$ `Visit.id` (`on_delete=SET_NULL`, nullable)
  - `FollowUp.facility` $\rightarrow$ `Facility.id` (`on_delete=CASCADE`)
- **API Endpoint:** `GET /api/followups/`
- **Frontend View:** `FollowUps.tsx`
- **Status Transition:** `PENDING` $\rightarrow$ `DUE_TODAY` $\rightarrow$ `OVERDUE` $\rightarrow$ `COMPLETED`
- **Defects & Broken Links Identified:**
  1. **CRITICAL CROSS-ENCOUNTER DATA CORRUPTION IN SEED DATA:**
     - `FollowUp #9` is linked to `referral_id = 16` and `visit_id = 35`.
     - BUT `Referral #16` belongs to `visit_id = 40`!
     - `FollowUp #9`'s foreign key contradicts `Referral #16`'s parent visit foreign key.
  2. **Read-Only Follow-Up UI:** `FollowUps.tsx` displays records with due dates, but has **no action button to mark a follow-up completed** or schedule an OPD token for the returning patient.

---

## 3. Summary of Patient Journey Integrity

| Transition | Step | FK Integrity | Status Flow | UI Action | Verdict |
|---|---|---|---|---|---|
| 1 | Onboarding $\rightarrow$ Patient | Intact | Valid | Valid | **PARTIAL** (Vulnerability hardcoded, Patient 216 unassigned) |
| 2 | Patient $\rightarrow$ Visit & Token | Intact | Valid | Valid | **COMPLETE** (Atomic token sequence) |
| 3 | Visit $\rightarrow$ Queue Calling | Intact | Broken | Broken | **BROKEN** (Doctor blocked by 403 on Call-Next; Visit 39 bypassed triage) |
| 4 | Queue $\rightarrow$ Nurse Triage | Intact | Valid | Partial | **PARTIAL** (OneToOne crash on re-entry; no Alert table push) |
| 5 | Triage $\rightarrow$ Doctor Consultation | Intact | Inconsistent | Partial | **PARTIAL** (Queue remains 'DOCTOR' after completion; static defaults) |
| 6 | Consultation $\rightarrow$ Laboratory | Missing Visit FK | Valid | Valid | **COMPLETE** (Sample barcode & verification verified) |
| 7 | Consultation $\rightarrow$ Prescription | Intact | Inconsistent | Valid | **PARTIAL** (Items stay PENDING on Visit 41 despite DISPENSED status) |
| 8 | Prescription $\rightarrow$ FEFO Dispense | Intact | Valid | Valid | **PARTIAL** (Amlodipine missing InventoryTransaction in seed data) |
| 9 | Consultation $\rightarrow$ Referral | Intact | Valid | Valid | **PARTIAL** (Urgency enum mismatch 'HIGH' vs 'URGENT') |
| 10 | Referral $\rightarrow$ Continuity Follow-up | Inconsistent | Incomplete | Read-Only | **BROKEN** (Cross-visit FK contradiction; UI cannot mark complete) |
