# Namma Clinic Digital Health Network — Client Demo Runbook & Presenter Guide

**Target Audience**: Government Officials, BBMP & ULB Stakeholders, Health Department Evaluation Committee  
**Presentation Duration**: 15–20 Minutes  
**Demo Architecture**: Live Integrated 3-Tier Hub-and-Spoke Network  
**Demo Account Credentials**:
- **Medical Officer (Doctor)**: `doctor` / `doctor123`
- **Staff Nurse**: `nurse` / `nurse123`
- **Pharmacist**: `pharmacy` / `pharmacy123`
- **Lab Technician**: `lab` / `lab123`
- **District Health Officer**: `district` / `district123`

---

## 1. Pre-Demo System Launch Checklist

Before starting the client presentation, launch both backend and frontend servers:

```bash
# Terminal 1: Launch Backend REST API (Port 8000)
cd "d:\namma clinic\backend"
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Launch Frontend Console (Port 3000)
cd "d:\namma clinic\frontend"
npm run dev
```

Verify in browser:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/`

---

## 2. 15-Scene Client Presentation Script

### SCENE 1: Executive Command Centre & Network Topology (`/` & `/network`)
- **Presenter Script**:
  > *"Respected Committee, welcome to the Namma Clinic Digital Health & Urban Public Health Command Platform. Before stepping into the clinic, observe the macro picture: a real-time Executive Command Centre aggregating OPD footfall, referral traffic, and pharmacy stock across all 3 tiers of Karnataka's urban healthcare network."*
- **What to Demonstrate**:
  - Show Executive Dashboard metrics (`Total Patients`, `Today OPD`, `Active Referrals`).
  - Open `/network` to display the Hub-and-Spoke topology connecting Namma Clinics to KC General and Victoria Hospitals.
- **Government Value**: Instant executive visibility into ward-level healthcare utilization and referral efficiency.

---

### SCENE 2: Citizen Arrival & Digital Registration (`/patients`)
- **Presenter Script**:
  > *"A citizen arrives at the Indiranagar Namma Clinic. Registration is fast, digital, and ABHA-enabled. Observe how we capture demographic data alongside urban slum vulnerability tags to ensure priority care for vulnerable BPL populations."*
- **What to Demonstrate**:
  - Click `Issue OPD Token` or `Register New Patient`.
  - Enter Patient Name (`Ramesh Kumar Gowda`), Mobile, and Slum/Vulnerability classification (`BPL Slum Resident`).
- **Government Value**: Ensures equitable primary care access and digital identity tracking under ABDM.

---

### SCENE 3: OPD Priority Queue Management (`/queue`)
- **Presenter Script**:
  > *"The system isn't just registering the citizen. It controls patient flow through the clinic from registration → triage → doctor → pharmacy with priority tags for emergency, elderly, and maternal ANC care."*
- **What to Demonstrate**:
  - Show OPD Queue Console with Token `#T-16`.
  - Point out color-coded Priority Tags (`EMERGENCY 🚨`, `MATERNAL`, `NORMAL`).
- **Government Value**: Eliminates crowded clinic chaos, reducing patient wait times and prioritizing emergency cases.

---

### SCENE 4: Staff Nurse Triage & Clinical Risk Stratification (`/triage`)
- **Presenter Script**:
  > *"The doctor doesn't start from a blank screen. The staff nurse captures essential vitals, and the system automatically stratifies clinical risk before the doctor consultation."*
- **What to Demonstrate**:
  - Input Vitals: BP `160/102 mmHg`, Glucose `210 mg/dL`, Temp `98.6°F`, SpO2 `96%`, Height `165 cm`, Weight `68 kg`.
  - Highlight the dynamic BMI (`25.0 kg/m²`) and the animated **`🚨 AUTOMATIC CLINICAL RISK FLAGS DETECTED`** alert box.
- **Government Value**: Standardizes triage assessment, identifying high-risk hypertensive/diabetic patients immediately.

---

### SCENE 5: Doctor EMR Workstation & Digital Prescribing (`/consultation`)
- **Presenter Script**:
  > *"We are designing this EMR-lite for a busy primary-care doctor, not a heavy hospital ERP. In 60 seconds, the doctor reviews pre-triage vitals, selects ICD-10 diagnosis, prescribes EDL medications, and orders lab tests."*
- **What to Demonstrate**:
  - Show pre-triage vitals card loaded automatically.
  - Enter ICD-10 Diagnosis (`E11.9 / I10 Type 2 Diabetes & Hypertension`).
  - Add EDL Medicines (`Metformin 500mg`, `Amlodipine 5mg`).
- **Government Value**: High-speed, intuitive clinical documentation tailored for high-volume primary health clinics.

---

### SCENE 6: Approved 14 Essential Diagnostic Tests & 6-Step Specimen Workflow (`/lab`)
- **Presenter Script**:
  > *"The Government mandates 14 essential diagnostic tests for Urban HWCs. Here, we track the complete specimen lifecycle end-to-end: Order → Sample Collection → Barcode Logging → Result Entry → Verification → Patient EMR Sync."*
- **What to Demonstrate**:
  - Show Approved 14 Diagnostic Test Catalogue panel (Diabetes, LFT, Lipid, Dengue, Malaria, Urine).
  - Click `Collect Sample` $\rightarrow$ shows barcode generated (`SMP-2026-8492`).
  - Click `Enter Result` $\rightarrow$ input `8.4% HIGH` $\rightarrow$ verify result and release to EMR timeline.
- **Government Value**: Guarantees point-of-care lab accuracy and full sample traceability.

---

### SCENE 7: First-Expiry First-Out (FEFO) Pharmacy & Stock Control (`/pharmacy`)
- **Presenter Script**:
  > *"Government guidelines explicitly require near-expiry medicines to be dispensed first. Our automated FEFO engine compares Batch A (expires sooner) against Batch B (expires later) and auto-selects Batch A. Dispensing updates stock in real-time."*
- **What to Demonstrate**:
  - Show FEFO Priority Batch Matrix (`Batch A — FEFO Auto-Selected` vs `Batch B`).
  - Click `Auto-FEFO Dispense` $\rightarrow$ stock decrements instantly, eliminating expired drug wastage.
- **Government Value**: **Less Expiry $\rightarrow$ Less Wastage $\rightarrow$ Better Stock Availability $\rightarrow$ Optimized Procurement Planning.**

---

### SCENE 8: Two-Way Closed-Loop Hospital Referral Network (`/referrals`)
- **Presenter Script**:
  > *"The Government model is not: Namma Clinic → send patient away. It is: Namma Clinic → Referral → Specialist → Feedback → Namma Clinic Follow-Up (Continuity of Care)."*
- **What to Demonstrate**:
  - Show outbound referral to KC General Hospital (`URGENT`).
  - Switch to Specialist view $\rightarrow$ click `Enter Specialist Feedback` $\rightarrow$ log Findings & Return Advice $\rightarrow$ status updates to `Closed-Loop Synced`.
- **Government Value**: Establishes seamless two-way care continuity between primary clinics and specialist hospitals.

---

### SCENE 9: Longitudinal EMR Timeline & Date-Based Navigation (`/patients/108`)
- **Presenter Script**:
  > *"When the patient returns, the doctor views their complete longitudinal medical history grouped by date, with quick date filters and dynamic history summaries."*
- **What to Demonstrate**:
  - Open Patient Detail (`/patients/108`).
  - Filter by `Last 30 Days` / `Clinic Visits`. Show collapsible date accordion (`16 Sep 2026 — 8 Events`).
- **Government Value**: Complete historical medical memory for every citizen across visits.

---

### SCENE 10: Ward-Level Public Health Intelligence & Executive Wrap-Up (`/`)
- **Presenter Script**:
  > *"Data captured during normal daily clinical operations becomes public-health intelligence. District health officers monitor ward-level fever spikes, NCD prevalence, and pharmacy stock risk to take proactive public health actions."*
- **What to Demonstrate**:
  - Show Ward-level Footfall, Dengue/Fever Surveillance alerts, and Stock Risk tables.
- **Government Value**: Transforms primary care into a proactive public health intelligence network.

---

## 3. Backup & Quick Test Commands

If asked to verify system functionality during QA or setup:

```bash
# Run System-Wide Operations Test Suite
python scripts/test_every_operation.py

# Run Live Patient Journey E2E Test Suite
python scripts/test_new_patient_flow.py

# Check TypeScript Compilation
cd frontend && npx tsc --noEmit
```
