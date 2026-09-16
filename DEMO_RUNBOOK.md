# Namma Clinic Digital Health & Urban Public Health Command Platform
## Executive Client Demonstration Runbook & Presenter Script Guide

**Target Presentation Audience**: Government Officials, BBMP / ULB Stakeholders, Health Department Committee, Technical Evaluation Team  
**Presentation Duration**: 15–20 Minutes  
**Primary Focus**: Namma Clinic Primary Healthcare Operations, Slum Vulnerability Intelligence, Continuity of Care & Executive Command Analytics  
**Demo Citizen Profile**: Lakshmi Devi | 38F | Patient ID: `NC-2026-00892` | ABHA: `91-4829-1029-4819` | Slum Area: Laggere Slum Cluster (Ward 68)

---

## 1. System Launch & Credentials

Before starting the client demonstration, launch the application servers:

```bash
# Terminal 1: Launch Django REST API Backend (Port 8000)
cd "d:\namma clinic\backend"
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Launch Vite React Console Frontend (Port 3000)
cd "d:\namma clinic\frontend"
npm run dev
```

### Operational Workstation Credentials
- **Medical Officer (Doctor)**: `doctor` / `doctor123`
- **Staff Nurse**: `nurse` / `nurse123`
- **Pharmacist**: `pharmacy` / `pharmacy123`
- **Lab Technician**: `lab` / `lab123`
- **District Health Officer**: `district` / `district123`

---

## 2. 15–20 Minute Executive Presenter Runbook

### SCENE 1: Executive Command Centre Overview (`/`) — Time: 0–2 min
- **Problem**: Municipal health leaders lack high-level visibility across scattered urban clinics, making resource allocation reactive.
- **Platform Solution**: Exception-driven command dashboard highlighting patient inflow, FEFO pharmacy dispensing, referral bottlenecks, and disease alerts.
- **Presenter Script**:
  > *"Respected Committee, welcome to the Namma Clinic Digital Health & Urban Public Health Command Platform. Before stepping into the clinic, observe the macro picture: an executive command console aggregating OPD footfall, pharmacy stock risks, and referral traffic across urban wards."*
- **Demonstration Action**: Open `/` and highlight KPI cards and exception alert banners (**CLIENT WOW MOMENT #5**).
- **Government Value**: Data-driven municipal governance and real-time operational transparency.

---

### SCENE 2: Healthcare Network Topology (`/network`) — Time: 2–3 min
- **Problem**: Primary health centers operate in isolation without clear structural links to tertiary referral hospitals.
- **Platform Solution**: Visual 3-tier hub-and-spoke map linking neighborhood Namma Clinics to UPHCs and major referral hospitals (KC General, Victoria Hospital).
- **Presenter Script**:
  > *"Observe how our primary Namma Clinics connect seamlessly to parent UPHCs and major referral hospitals. This topology guarantees that patients receive neighborhood care while maintaining a direct link to specialist hospitals."*
- **Demonstration Action**: Open `/network` and display the interactive hub-and-spoke node graph.
- **Government Value**: Visual clarity on urban healthcare service delivery boundaries.

---

### SCENE 3: Citizen Intake & ABHA Identity (`/patients`) — Time: 3–5 min
- **Problem**: Crowded clinic waiting rooms suffer from long intake delays and duplicate patient registrations across facilities.
- **Platform Solution**: Rapid patient intake with instant duplicate matching, ABHA health ID linkage, and household slum vulnerability tagging.
- **Presenter Script**:
  > *"A citizen, Lakshmi Devi, arrives at Namma Clinic Laggere. Registration is fast, digital, and ABHA-enabled. Observe how we capture her demographics alongside her urban slum classification."*
- **Demonstration Action**: Open `/patients`, register Lakshmi Devi (Patient ID: `NC-2026-00892`, ABHA: `91-4829-1029-4819`), and tag `Laggere Slum Cluster (Ward 68)` (**CLIENT WOW MOMENT #1**).
- **Government Value**: Eliminates duplicate patient records and establishes standardized national health identity within the ABDM ecosystem.

---

### SCENE 4: OPD Priority Queue Management (`/queue`) — Time: 5–6 min
- **Problem**: Unorganized waiting lines result in delays for high-risk, elderly, and vulnerable patients.
- **Platform Solution**: Priority OPD token queueing with dynamic re-ordering based on vulnerability and clinical risk.
- **Presenter Script**:
  > *"The system controls patient flow through the clinic. Lakshmi Devi receives Token T-042, prioritized automatically under Vulnerable Slum Status."*
- **Demonstration Action**: View `/queue` and highlight token `#T-042` with its color-coded priority badge.
- **Government Value**: Streamlines clinic flow and ensures rapid care for vulnerable citizens.

---

### SCENE 5: Staff Nurse Triage & Clinical Risk Flags (`/triage`) — Time: 6–8 min
- **Problem**: Doctors spend valuable consultation time capturing basic vitals instead of treating complex clinical symptoms.
- **Platform Solution**: Nurse triage workstation capturing essential vitals and automatically calculating clinical risk scores.
- **Presenter Script**:
  > *"The doctor doesn't start from a blank screen. Nurse triage captures Lakshmi Devi's vitals: BP 148/92, Temp 101.2°F, SpO2 97%, Glucose 165. The system raises an Amber Clinical Risk Flag."*
- **Demonstration Action**: Open `/triage`, record vitals for Lakshmi Devi, and point out the automated risk alert banner.
- **Government Value**: Standardizes triage and alerts clinicians to high-risk conditions before consultation.

---

### SCENE 6: Doctor EMR Workstation & Prescribing (`/consultation`) — Time: 8–10 min
- **Problem**: Paper prescription registers lead to illegible notes, missing medical histories, and slow consultations.
- **Platform Solution**: Single-page EMR workstation featuring pre-loaded triage vitals, ICD-10 diagnosis entry, essential lab test ordering, and e-prescribing.
- **Presenter Script**:
  > *"Doctor reviews pre-triage vitals, diagnoses Acute Respiratory Infection (ICD-10 J06.9) & Essential Hypertension (ICD-10 I10), orders a CBC lab test, and prescribes Paracetamol and Amlodipine."*
- **Demonstration Action**: Open `/consultation`, select Lakshmi Devi, enter ICD-10 codes, order CBC test, and issue e-prescription.
- **Government Value**: High-speed, standardized clinical documentation tailored for high-volume primary clinics.

---

### SCENE 7: Essential Diagnostics & Lab Barcode Pipeline (`/lab`) — Time: 10–11 min
- **Problem**: Misplaced diagnostic orders and delayed result handoffs hinder clinical decision-making.
- **Platform Solution**: Complete laboratory pipeline covering the official 14 Essential Tests Catalogue, specimen barcoding, and automated result verification.
- **Presenter Script**:
  > *"Lab technician receives the CBC order, logs blood sample barcode SMP-2026-8492, inputs result values (WBC 11,500/µL), and verifies the report, instantly updating Lakshmi Devi's EMR."*
- **Demonstration Action**: Open `/lab`, collect specimen, record result, and verify report.
- **Government Value**: Guarantees point-of-care diagnostic accuracy aligned with Government UHWC guidelines.

---

### SCENE 8: FEFO Pharmacy & Drug Inventory Engine (`/pharmacy`) — Time: 11–13 min
- **Problem**: Primary clinic stores suffer heavy drug loss due to expired medicine stock and manual unmonitored inventory ledgers.
- **Platform Solution**: First-Expiry First-Out (FEFO) drug dispensing engine that auto-selects batches closest to expiry and updates store ledgers in real-time.
- **Presenter Script**:
  > *"Pharmacist retrieves Lakshmi Devi's prescription. The FEFO engine automatically selects Paracetamol Batch A (Expires Oct 2026) over Batch B (Expires Dec 2027), updating stock ledgers instantly."*
- **Demonstration Action**: Open `/pharmacy`, dispense Lakshmi Devi's prescription, and show the FEFO batch selection matrix (**CLIENT WOW MOMENT #2**).
- **Government Value**: Prevents medicine expiry wastage, maintains transparent ledgers, and triggers low-stock alerts.

---

### SCENE 9: Two-Way Closed-Loop Specialist Referrals (`/referrals`) — Time: 13–15 min
- **Problem**: Patients referred to tertiary hospitals get lost in the healthcare system without feedback to the primary clinic doctor.
- **Platform Solution**: Closed-loop referral network connecting primary clinics to major hospitals (Victoria Hospital) with returning specialist treatment notes.
- **Presenter Script**:
  > *"Doctor creates an urgent Cardiology referral to Victoria Hospital. Hospital specialist logs diagnostic findings and returns treatment advice to Namma Clinic Laggere."*
- **Demonstration Action**: Open `/referrals`, generate outbound referral for Lakshmi Devi, and log specialist feedback (**CLIENT WOW MOMENT #3**).
- **Government Value**: Eliminates patient referral drop-outs and establishes care continuity across healthcare tiers.

---

### SCENE 10: Longitudinal Follow-up & Care Continuity (`/followups`) — Time: 15–16 min
- **Problem**: Patients with chronic conditions miss review appointments, leading to severe health complications.
- **Platform Solution**: Automated follow-up schedule tracking post-consultation reviews, chronic disease monitoring, and post-referral return visits.
- **Presenter Script**:
  > *"Staff nurse views the clinic follow-up roster showing Lakshmi Devi's scheduled 14-day hypertension review on September 30, 2026."*
- **Demonstration Action**: Open `/followups` and filter by upcoming review dates.
- **Government Value**: Improves treatment adherence and long-term health outcomes for chronic disease patients.

---

### SCENE 11: NCD Population Screening & Registry (`/ncd`) — Time: 16–17 min
- **Problem**: Fragmented screening makes tracking population hypertension and diabetes prevalence difficult.
- **Platform Solution**: Dedicated NCD screening cohort registry for Hypertension, Diabetes, and Cancers with risk stratification.
- **Presenter Script**:
  > *"Public Health Officer reviews the Ward 68 NCD cohort register, identifying Lakshmi Devi under the Grade-1 Hypertension monitoring list."*
- **Demonstration Action**: View `/ncd` cohort register and filter by hypertension risk tier.
- **Government Value**: Supports national NCD control programs by building a comprehensive urban chronic disease registry.

---

### SCENE 12: Maternal & Child Health (RCH/ANC) (`/maternal-child`) — Time: 17–18 min
- **Problem**: High-risk pregnancies and child immunizations require tedious paper register tracking.
- **Platform Solution**: Specialized EMR modules for ANC checkups, High-Risk Pregnancy (HRP) flags, PNC monitoring, and child immunization schedules.
- **Presenter Script**:
  > *"Staff nurse views the clinic RCH workspace showing active ANC registrations and child vaccination rosters."*
- **Demonstration Action**: View `/maternal-child` console and highlight HRP tracking flags.
- **Government Value**: Reduces maternal and infant mortality through digital RCH tracking.

---

### SCENE 13: Urban Slum Health Outreach (`/outreach`) — Time: 18–19 min
- **Problem**: Field outreach by ASHA workers in urban slums is disconnected from primary clinic health records.
- **Platform Solution**: Digitized field outreach registers, household health surveys, and slum vulnerability mapping.
- **Presenter Script**:
  > *"ANM logs a field survey entry for Laggere Slum Cluster, linking household records directly to Namma Clinic Laggere."*
- **Demonstration Action**: View `/outreach` register and point out household slum mapping.
- **Government Value**: Bridges the gap between community field outreach and clinic care.

---

### SCENE 14: Ward Public Health Intelligence (`/surveillance`) — Time: 19–20 min
- **Problem**: Urban disease outbreaks go unnoticed until tertiary hospital emergency rooms become overwhelmed.
- **Platform Solution**: Real-time ward-level epidemic surveillance heatmaps (IDSP standards) aggregating daily clinical encounter diagnoses.
- **Presenter Script**:
  > *"Public Health Officer reviews fever surveillance. The system detects a localized spike of 24 fever cases in Ward 68 (Laggere) and issues an early outbreak alert."*
- **Demonstration Action**: Open `/surveillance` and highlight the Ward 68 fever cluster alert (**CLIENT WOW MOMENT #4**).
- **Government Value**: Transforms routine primary-care encounters into proactive early epidemic warning intelligence.

---

### SCENE 15: Government Governance & Executive Closing (`/`) — Time: 20 min
- **Problem**: Lack of administrative oversight over clinic untied funds and hygiene standards.
- **Platform Solution**: Integrated Arogya Raksha Samiti (ARS) governance ledgers, Kayakalpa sanitation scoring, and executive command analytics.
- **Presenter Script**:
  > *"In conclusion, our platform digitizes primary clinic operations while transforming encounter data into actionable Urban Public Health Intelligence for municipal decision-makers. Thank you."*
- **Demonstration Action**: Show ARS fund ledgers `/ars` and close on the main Executive Command Console `/`.
- **Government Value**: Complete operational, financial, and clinical governance for municipal healthcare systems.

---

## 3. Five Executive "WOW" Moments Summary

| # | Executive "WOW" Moment | Primary Demonstration Screen | Executive Client Impact |
| :-: | :--- | :--- | :--- |
| **WOW #1** | **Patient Care Continuity** | `Patient Intake (/patients)` | Single patient record moving cleanly across triage, doctor EMR, lab, pharmacy, and referral. |
| **WOW #2** | **Pharmacy FEFO Intelligence** | `Pharmacy Store (/pharmacy)` | Auto-selects near-expiry drug batches (Batch A vs Batch B), eliminating medicine expiry wastage. |
| **WOW #3** | **Two-Way Specialist Referrals** | `Referrals Desk (/referrals)` | Closed-loop referral tracking returning hospital specialist treatment notes to the primary doctor. |
| **WOW #4** | **Ward Public Health Intelligence** | `Surveillance (/surveillance)` | Aggregates daily clinical consultation diagnoses into ward fever cluster heatmaps. |
| **WOW #5** | **Government Command Centre** | `Command Console (/)` | Exception-driven administrative dashboard highlighting stockouts, fever spikes, and referral delays. |

---

## 4. Verification Test Suite Commands

To verify system functionality prior to presentation:

```bash
# Run 10-Point Operational Systems Test Suite
python scripts/test_every_operation.py

# Run End-to-End Citizen Care Journey Script
python scripts/test_new_patient_flow.py

# Compile Client Demo Manual PDF
python scripts/generate_pdf_manual.py
```
