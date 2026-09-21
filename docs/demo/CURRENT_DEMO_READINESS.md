# Namma Clinic — Current Demo Readiness & Data Lineage Analysis

## 1. Executive Summary

This document evaluates the operational readiness of the Namma Clinic repository to deliver an end-to-end client demonstration. The evaluation contrasts the 19 critical demonstration touchpoints against actual source code implementation, database models, seed scripts, and UI interfaces.

---

## 2. 19-Point Demonstration Journey Evaluation

| # | Demonstration Journey Touchpoint | Current Status | System Evidence | Technical & Operational Reality |
| :-: | :--- | :---: | :--- | :--- |
| **1** | **Citizen Arrives at Clinic** | **Implemented** | `Queue.tsx`, `visits_visit` | Check-in creates a `Visit` record and issues an OPD token. |
| **2** | **Citizen Registration** | **Implemented** | `Patients.tsx`, `PatientViewSet.create()` | Captures demographics, mobile, ward, and auto-generates `NC-KA-2026-XXXX` UHID. Includes duplicate mobile+name check. |
| **3** | **ABHA-Enabled Identity** | **Partially Implemented** | `patients_patient.ABHA_ID_DEMO` | Stores static/simulated ABHA number string. ABDM gateway authentication is in `MOCK` simulation mode. |
| **4** | **Vulnerability / Slum Context** | **Implemented** | `patients_patient.vulnerability_information` | Tagged during registration (e.g. `Slum Household BPL`, `Senior Citizen / Diabetic`). |
| **5** | **OPD Priority Queue & Tokens** | **Implemented** | `Queue.tsx`, `visits_token` | Sequential daily token generation restarting at `#1` per facility per day with emergency priority badges. |
| **6** | **Nurse Vitals Triage** | **Implemented** | `Triage.tsx`, `triage_triagevitals` | Captures BP, Pulse, Temp, SpO2, Glucose, BMI. Automatically computes high-risk clinical alert flags. |
| **7** | **Doctor Consultation EMR** | **Implemented** | `Consultation.tsx`, `consultations_consultation` | Pre-loads triage vitals, records clinical notes, chief complaint, ICD-10 diagnosis code, and treatment plan. |
| **8** | **Approved 14 Diagnostics** | **Implemented** | `Laboratory.tsx`, `laboratory_laborder` | 14 essential tests catalogue, specimen collection with barcode logging, and lab technician result entry/verification. |
| **9** | **Electronic Prescription** | **Implemented** | `Consultation.tsx`, `consultations_prescription` | EMR outputs prescription with dosage, frequency, and duration. Linked 1:1 with consultation. |
| **10**| **FEFO Pharmacy Dispensing** | **Implemented** | `Pharmacy.tsx`, `DispenseMedicineView` | Automated First-Expiry First-Out (FEFO) batch allocation logic. Batch A vs Batch B comparison matrix active in UI. |
| **11**| **Inventory Control & POs** | **Implemented** | `apps/pharmacy/views.py`, `PurchaseOrder` | Batch stock decrementing, vendor purchase orders, approval flow, and inventory transaction audit logging. |
| **12**| **Two-Way Closed-Loop Referral**| **Implemented** | `Referrals.tsx`, `ReferralResponse` | Outbound referral created to KC General/Victoria Hospital; hospital specialist logs findings and return advice. |
| **13**| **Longitudinal Follow-up Care** | **Implemented** | `FollowUps.tsx`, `referrals_followup` | Follow-up schedule tracks chronic disease review dates and overdue statuses. Visible in patient timeline. |
| **14**| **NCD Screening & Registry** | **Partially Implemented** | `NCD.tsx`, `ncd_ncdrecord` | NCD registry console active, but records are stored as detached entries rather than auto-populated from triage/consultation. |
| **15**| **Maternal, Child & RCH** | **UI Only / Mocked** | `MaternalChild.tsx` | **CRITICAL DEMO RISK**: `apps/maternal` and `apps/child` are not installed in Django settings. The frontend screen displays 100% hardcoded static JSX without API calls. |
| **16**| **Community Field Outreach** | **Partially Implemented** | `Outreach.tsx`, `outreach_outreachactivity` | Outreach activity logs household surveys and slum health camps, but is not linked to individual citizen records. |
| **17**| **Public Health Intelligence** | **Partially Implemented** | `Surveillance.tsx`, `surveillance_diseasecase` | Disease cases listed in table, but the fever outbreak banner is hardcoded static JSX. |
| **18**| **DHO Command Centre** | **Partially Implemented** | `DistrictOfficerDashboard.tsx` | Aggregates district facility footfall and stock, but DHO is blocked from accessing `/patients`, `/ncd`, `/surveillance` by frontend route guards. |
| **19**| **District $\rightarrow$ Zone $\rightarrow$ Ward $\rightarrow$ Clinic Drill-down** | **Implemented** | `HealthcareNetwork.tsx`, `Facilities.tsx` | 4-tier interactive SVG graph and expandable tree view mapping network topology from District to Satellite clinics. |

---

## 3. Demo Data Lineage Analysis

The standard demo dataset is seeded via the Django management command:
```bash
python manage.py seed_demo
```

### 3.1 Primary Citizen Demo Journey Lineage: Ramesh Kumar Gowda

In `seed_demo.py`, a continuous end-to-end clinical journey is pre-seeded for patient **Ramesh Kumar Gowda**:

```
[PATIENT MASTER]
  Patient ID: NC-20260901-001
  Name: Ramesh Kumar (Age 52, Male, Mobile: 9876543210)
  ABHA: 91-8765-4321-0987 | Vulnerability: Slum Household BPL
  Registered At: Varthur Rural Primary Clinic A4 (RC-A4-04)
        |
        v
[ENCOUNTER / VISIT]
  Visit ID: VIS-RC-<TODAY>-001
  OPD Date: Today | Priority: HIGH | Current Queue: PHARMACY
  Status: WAITING_FOR_PHARMACY
  Chief Complaint: Dizziness, severe fatigue, blurred vision
        |
        +---> [TOKEN] Token #1 (Facility: RC-A4-04, Priority: HIGH)
        |
        v
[NURSE TRIAGE]
  Triage ID: Linked to Visit VIS-RC-<TODAY>-001
  Nurse: Sister Priya Nair
  Vitals: BP 148/96 mmHg, Pulse 84 bpm, Temp 99.1°F, SpO2 98%, Glucose 185 mg/dL
  Flags: high_bp_flag=True, high_glucose_flag=True, ncd_risk_flag=True
        |
        v
[DOCTOR CONSULTATION]
  Consultation ID: Linked to Visit VIS-RC-<TODAY>-001
  Doctor: Dr. Rajesh Kumar (Medical Officer)
  Diagnosis: ICD-10 [E11.9 / I10] Type 2 Diabetes Mellitus with Essential Hypertension
  Plan: Metformin 500mg BD + Amlodipine 5mg OD; Referral to Victoria Hospital
        |
        +---> [LAB ORDER]
        |       Order ID: Linked to Consultation
        |       Test: HbA1c Glycated Hemoglobin (L-HBA1C)
        |       Sample: SMP-RC-001 (Blood, collected by Suresh Gowda)
        |       Result: 8.4% [HIGH] (Verified by Suresh Gowda)
        |
        +---> [PRESCRIPTION]
        |       Prescription ID: Linked to Consultation (Status: PENDING)
        |       Item 1: Metformin 500 mg Tablet (Qty: 28, Dosage: 1-0-1 After Food)
        |       Item 2: Amlodipine 5 mg Tablet (Qty: 14, Dosage: 1-0-0 Morning)
        |
        +---> [SPECIALIST REFERRAL]
        |       Referral ID: REF-20260903-0001
        |       Source: Varthur Rural Clinic A4 -> Destination: Victoria District Hospital
        |       Urgency: HIGH | Status: COMPLETED
        |       Specialist Response: Dr. Vikram Seth (Cardiologist)
        |       Findings: Essential Hypertension with mild ECG changes; Diabetes uncontrolled
        |       Return Advice: Patient stable. Return to Rural Clinic A4 in 14 days
        |
        +---> [LONGITUDINAL FOLLOW-UP]
                Category: REFERRAL | Due Date: Today + 14 Days
                Status: PENDING | Notes: Review post-specialist referral response
```

---

## 4. Demo Risk Assessment

1. **High Risk — Maternal & Child Health Demonstration**:
   - If a presenter clicks into `/maternal-child`, the audience will see static cards that cannot be interacted with, edited, or dynamically updated from clinic registrations.
2. **Medium Risk — DHO Navigation Failure**:
   - If logged in as the District Officer (`district` / `district123`), clicking on `/patients`, `/ncd`, or `/surveillance` will immediately trigger a red `Access Denied (HTTP 403)` banner due to route guard restrictions in `frontend/src/utils/permissions.ts`.
3. **Low Risk — Reset Demo Action**:
   - The `/admin/reset-demo/` API endpoint executes `call_command('seed_demo')` synchronously inside SQLite atomic transaction, allowing instant recovery to pristine demonstration state in case of presentation data corruption.
