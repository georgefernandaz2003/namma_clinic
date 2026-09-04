# Demo Guide & Multi-Role Walkthrough
## Namma Clinic Integrated Digital Healthcare Network

This guide details the step-by-step procedure to demonstrate the full end-to-end multi-role healthcare network workflow.

---

## 1. Demo Credentials Matrix (DEMO ONLY)

| Role | Username | Password | Default Facility | Access Scope |
|---|---|---|---|---|
| Super Admin | `admin` | `admin123` | System-Wide | All System Configuration & Network Admin |
| District Officer | `district` | `district123` | District Health Office A | District-Wide Dashboards & Surveillance |
| Hospital Admin | `hospital` | `hospital123` | Main Hospital B | Connected Clinics & Specialist Referrals |
| Medical Officer | `doctor` | `doctor123` | Rural Clinic A4 | OPD Queue, Consultations, EMR, Prescriptions, Referrals |
| Staff Nurse | `nurse` | `nurse123` | Rural Clinic A4 | Registration, Token Queue, Triage Vitals |
| Lab Technician | `lab` | `lab123` | Rural Clinic A4 | Lab Orders, Sample Collection, Result Verification |
| Pharmacist | `pharmacy` | `pharmacy123` | Rural Clinic A4 | Prescriptions, FEFO Batch Dispensing, Inventory |
| Public Health Officer | `officer` | `officer123` | City Health Dept | Public Health Dashboards, Disease Anomalies, Alerts |

---

## 2. Complete Live Demo Scenario

### Step 1: Patient Arrival & Triage (Login as `nurse` / `nurse123`)
1. Log in as **Staff Nurse** (`nurse`).
2. Select **Rural Clinic A4** from the facility header switcher if needed.
3. Navigate to **Patients** -> Click **Register Patient** (or search existing demo patient *Ramesh Kumar*).
4. Generate a new daily OPD Token.
5. In **Nurse Triage**, open the patient entry and record vitals:
   - Blood Pressure: `145 / 95 mmHg` (Flags: *High BP*)
   - Pulse: `82 bpm`, Temperature: `99.2 °F`, SpO2: `98%`
   - Blood Glucose: `185 mg/dL` (Flags: *High Glucose*)
6. Save vitals and route patient to Doctor Queue.

### Step 2: Doctor Consultation & Referral (Login as `doctor` / `doctor123`)
1. Log in as **Medical Officer** (`doctor`).
2. Navigate to **Queue / Consultations** -> Select patient *Ramesh Kumar*.
3. Review recorded triage vitals and clinical warning flags.
4. Record assessment:
   - Chief Complaint: *Dizziness and fatigue for 5 days*
   - Diagnosis: *Type 2 Diabetes Mellitus with Uncontrolled Hypertension*
5. Add Prescription: *Metformin 500mg (1-0-1)* and *Amlodipine 5mg (1-0-0)*.
6. Order Lab Investigation: *HbA1c & Fasting Blood Sugar*.
7. Create Cross-Facility Referral:
   - Destination Facility: Select **Main Hospital B** (Cardiology / General Medicine Specialist Hub).
   - Reason: *Specialist evaluation for uncontrolled hypertension*.
   - Urgency: *High*.
8. Save Consultation.

### Step 3: Diagnostic Lab Processing (Login as `lab` / `lab123`)
1. Log in as **Lab Technician** (`lab`).
2. Navigate to **Laboratory** -> Select pending order for *Ramesh Kumar*.
3. Mark **Sample Collected** -> Enter Result (`HbA1c: 8.2 %`, `Fasting Glucose: 178 mg/dL`).
4. Click **Verify & Release Result**.

### Step 4: FEFO Pharmacy Dispensing (Login as `pharmacy` / `pharmacy123`)
1. Log in as **Pharmacist** (`pharmacy`).
2. Navigate to **Pharmacy** -> Select prescription for *Ramesh Kumar*.
3. System automatically selects nearest-expiry FEFO batch (`BATCH-MET-2026A`).
4. Click **Dispense Medicines**.
5. Observe batch inventory decreasing dynamically in stock ledger.

### Step 5: Main Hospital Specialist Referral Response (Login as `hospital` / `hospital123`)
1. Log in as **Hospital Admin / Specialist** (`hospital`) at **Main Hospital B**.
2. Navigate to **Referrals Management** -> Open incoming referral from **Rural Clinic A4**.
3. Accept referral -> Record Specialist Response:
   - Specialist Findings: *Essential Hypertension with mild LVH*.
   - Advice: *Continue Amlodipine 5mg, add Telmisartan 40mg, low salt diet, review in 15 days*.
4. Mark Referral **Completed & Returned to Primary Clinic**.

### Step 6: Unified Patient Timeline & Healthcare Network Visualization
1. Re-open patient profile for *Ramesh Kumar* as Doctor or Nurse.
2. View **Patient Timeline**: Observe chronological history spanning Registration -> Triage -> Consultation -> Lab -> Pharmacy -> Hospital Referral -> Specialist Response -> Follow-up.
3. Open **Healthcare Network** Page:
   - Explore interactive tree: District 1 -> Main Hospital B -> Rural Clinic A4 -> Village Satellites.
   - View dynamic SVG graph canvas displaying organizational parent-child links vs. cross-referral pathways.

### Step 7: Public Health Surveillance & Command Dashboards
1. Log in as **Public Health Officer** (`officer`).
2. Open **Public Health Dashboard**: Review Ward-wise fever trends, NCD screening metrics, and automated disease anomaly alerts (e.g. *Fever cluster warning in Ward 12*).
3. Open **Namma Clinic Compliance Page**: Review 100% feature coverage matrix against Booklet & Proposal requirements.
