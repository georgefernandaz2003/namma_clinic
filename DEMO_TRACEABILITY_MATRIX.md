# Namma Clinic Digital Health Network — Requirements Traceability Matrix

**Document Purpose**: Provides complete 1-to-1 traceability connecting **Government Operational Guidelines (ULB ROK Booklet Aug 2024)**, **K Mati Project Proposal Requirements**, **Application System Modules**, **Validated Screen Evidence**, and **Operational Status**.

---

## Traceability Legend
- **GREEN**: Fully Implemented, Tested & Validated with Live Evidence
- **BLUE**: ABDM-Ready Architecture / Planned Integration Phase

---

## Master Traceability Matrix

| # | Government Operational Guideline Requirement (ULB Booklet 2024) | K Mati Project Proposal Requirement | Application System Module | Validated Screen & Workflow Evidence | Implementation Status |
|---|---|---|---|---|---|
| **1** | **Universal Citizen Registration & Digital Identity** | ABHA ID registration support, demographic registry, slum & vulnerability tagging. | `Patients.tsx` & `PatientDetail.tsx` | Patient Master Directory (`/patients`), ABHA demo mapping (`ABHA-2026-5135`), BPL Slum Tagging. | **GREEN** |
| **2** | **Decentralized Outpatient Queue & Triage** | OPD Token issuance with priority tags for emergency, elderly, and maternal ANC care. | `Queue.tsx` | OPD Queue Console (`/queue`), Token `#T-16`, priority flags (`EMERGENCY 🚨`, `MATERNAL`, `NORMAL`). | **GREEN** |
| **3** | **Pre-Consultation Nurse Vitals & Risk Stratification** | Vitals collection (BP, Pulse, Temp, SpO2, Glucose, BMI) with auto-triggered risk alerts. | `Triage.tsx` | Staff Nurse Triage Desk (`/triage`), BP 160/102, Glucose 210 mg/dL, dynamic BMI (25.0 kg/m²), `🚨 CLINICAL RISK ALERT`. | **GREEN** |
| **4** | **Primary Care Doctor EMR & Digital Prescribing** | EMR-Lite workstation for doctor diagnosis (ICD-10), clinical notes, EDL drug prescribing. | `Consultation.tsx` | Doctor EMR Workstation (`/consultation`), ICD-10 `E11.9 / I10`, EDL Drug Prescriber (`Metformin`, `Amlodipine`). | **GREEN** |
| **5** | **Approved 14 Essential Diagnostic Tests Catalogue** | Essential point-of-care & hub laboratory testing covering 14 approved diagnostic tests. | `Laboratory.tsx` | Diagnostic Lab Console (`/lab`), Complete 14-test catalogue panel (Diabetes, Hematology, LFT, Lipid, Dengue, Malaria, Urine). | **GREEN** |
| **6** | **6-Step Specimen Diagnostic Lifecycle** | End-to-end specimen tracking: Order $\rightarrow$ Sample $\rightarrow$ Barcode $\rightarrow$ Result $\rightarrow$ Verify $\rightarrow$ EMR. | `Laboratory.tsx` | Lab Specimen Pipeline (`/lab`), Barcode `SMP-2026-8492`, 8.4% HIGH result verification, live EMR sync. | **GREEN** |
| **7** | **First-Expiry First-Out (FEFO) Pharmacy Control** | Drug inventory ledger enforcing FEFO rules, batch expiry management, stock reduction. | `Pharmacy.tsx` | FEFO Pharmacy Console (`/pharmacy`), Batch A (`Expires Sooner`) vs Batch B comparison matrix, stock deduction. | **GREEN** |
| **8** | **Low-Stock & Near-Expiry Drug Warnings** | Reorder level threshold monitoring, stock wastage prevention, procurement analytics. | `Pharmacy.tsx` | Pharmacy Batch Ledger (`/pharmacy`), active reorder warnings, automatic stock decrement. | **GREEN** |
| **9** | **Two-Way Closed-Loop Specialist Referral** | Cross-facility referral: Primary $\rightarrow$ Specialist Hub $\rightarrow$ Specialist Feedback $\rightarrow$ Follow-Up. | `Referrals.tsx` | Cross-Facility Referral Desk (`/referrals`), Outbound to KC General, Specialist Findings & Return Advice form. | **GREEN** |
| **10**| **Continuity of Care & Scheduled Follow-Ups** | Chronic disease follow-ups, post-referral monitoring, missed visit tracking. | `FollowUps.tsx` & `PatientDetail.tsx` | Follow-up Care Console (`/followups`), Longitudinal EMR Timeline date-range filtering. | **GREEN** |
| **11**| **Non-Communicable Disease (NCD) Management** | NCD population screening (Diabetes, Hypertension), risk stratification, tracking. | `NCD.tsx` | NCD Registry Console (`/ncd`), Population screening stats, risk classification. | **GREEN** |
| **12**| **Communicable Disease & Outreach Surveillance** | Early warning epidemic disease signals, fever tracking, community health camps. | `Surveillance.tsx` & `Outreach.tsx` | Disease Surveillance Console (`/surveillance`), Ward-level Dengue/Malaria case tracking. | **GREEN** |
| **13**| **Maternal, ANC & Child Health Care (RCH)** | ANC registration, high-risk pregnancy tagging, immunization tracking, RCH cards. | `MaternalChild.tsx` | Maternal & Child Health Console (`/maternal-child`), ANC trimester tracking. | **GREEN** |
| **14**| **Hub-and-Spoke 3-Tier Network Topology** | Visual mapping of Satellite $\rightarrow$ Namma Clinic $\rightarrow$ UPHC $\rightarrow$ Major Hospital referral tree. | `HealthcareNetwork.tsx` | Healthcare Network Map (`/network`), 3-tier hierarchy tree & SVG graph canvas. | **GREEN** |
| **15**| **Urban Local Body & Ward-Level Intelligence** | Ward, Zone, District aggregation of health burden, footfall, and clinic performance. | `Dashboard.tsx` | Executive Command Centre (`/`), Ward-level Footfall, Referral & Stock analytics. | **GREEN** |
| **16**| **Governance & ARS Samithi Oversight** | Arogya Raksha Samithi (ARS) meeting logs, fund utilization, action items. | `ARS.tsx` | ARS Governance Console (`/ars`), Meeting minutes & fund tracking. | **GREEN** |
| **17**| **Quality Assurance & Kayakalpa Compliance** | Quality checklists, biomedical waste segregration logging (Red/Yellow/Blue/White). | `Quality.tsx` & `Compliance.tsx` | Quality & Bio-Waste Console (`/quality`), Segregation logs & Kayakalpa checklist. | **GREEN** |
| **18**| **Role-Based Security & Audit Logging** | RBAC enforcement across 8 user roles, session security, immutable audit trail logs. | `Audit.tsx` & `api_urls.py` | System Audit Console (`/audit`), JWT authentication, user action audit logs. | **GREEN** |
| **19**| **ABDM / ABHA Identity Integration** | ABDM consent-based health record exchange architecture. | `PatientDetail.tsx` | ABHA health identity mapping (`ABHA-2026-5135`), ABDM-ready schema structure. | **BLUE** |
