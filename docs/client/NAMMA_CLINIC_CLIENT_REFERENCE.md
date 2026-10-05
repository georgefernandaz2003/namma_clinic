# Namma Clinic — Digital Healthcare & Clinic Management Platform
## Client Application Reference Manual

**Platform:** Namma Clinic Integrated Digital Healthcare Network  
**Document Classification:** Client Application Reference & Operational Architecture  
**Release Target:** Phase 28B-0 Approved Baseline  
**Environment:** Local Laptop Demonstration / Edge Clinic Deployment  
**Author:** Namma Clinic Engineering Guild  
**Date:** October 2026  

---

## Executive Summary

The **Namma Clinic Platform** is an integrated, role-governed healthcare information and clinic operations management platform designed specifically for primary urban healthcare centers (PHCs, Namma Clinics, and Urban Health Centers). 

The platform delivers an end-to-end electronic patient care lifecycle:
- **Rapid Patient Registration & Demographics Registry**: Instant intake with deduplication protection, ABHA field capture, and neighborhood vulnerability classification.
- **Sequential Daily OPD Token Queue**: Governed outpatient flow moving patients sequentially through intake, nurse triage, clinician examination, laboratory investigation, and pharmaceutical dispensing.
- **Clinical Triage & Decision Support**: Vital sign recording, BMI computation, and clinical acuity classification (`IMMEDIATE`, `VERY_URGENT`, `URGENT`, `STANDARD`, `NON_URGENT`).
- **Clinician Workstation**: Comprehensive diagnostic consultation, SNOMED/ICD-aligned clinical recording, electronic prescription ordering, and diagnostic lab test requisitions.
- **Separation-of-Duties Pharmacy & Inventory**: Dual-boundary architecture guaranteeing that physical warehouse movements (purchase orders, GRN receipts, and inventory adjustments) and clinical dispensing operate through strict authorization and FEFO (First-Expired, First-Out) stock governance.
- **District Health Governance**: Comprehensive district-wide oversight covering staff lifecycle postings, public health disease surveillance, quality indicators, ARS funds, and administrative compliance.

---

## 1. Executive Overview

### 1.1 Purpose
Urban primary health centers require reliable, highly responsive software capable of running at the clinic edge without reliance on unstable internet links. Namma Clinic provides urban health facilities with a secure, responsive, single-pane-of-glass operational system that streamlines patient intake, enforces separation of clinical duties, and ensures strict data privacy.

### 1.2 Target Stakeholders & Primary Users
1. **Citizens / Patients**: Urban residents seeking walk-in primary care, chronic disease management, and free prescription fulfillment.
2. **Front Desk Officers**: Clerical intake staff responsible for citizen registration, demographic search, and daily OPD token generation.
3. **Staff Nurses**: Healthcare personnel conducting vital signs intake, triage acuity scoring, follow-ups, and community outreach.
4. **Medical Officers (Doctors)**: Clinicians conducting clinical examinations, issuing formal diagnoses, ordering lab investigations, and generating e-prescriptions.
5. **Lab Technicians**: Diagnostic specialists managing sample collections, specimen testing, and result reporting.
6. **Pharmacists**: Licensed dispensers verifying doctor prescriptions, verifying FEFO batch selections, and dispensing medications.
7. **Inventory Managers**: Storekeepers managing procurement, purchase orders, Goods Receipt Notes (GRN), and physical count reconciliations.
8. **Hospital / Clinic Administrators**: Clinic superintendents managing facility configuration, staff recruitment, operational roles, and administrative alerts.
9. **District Health Officers (DHO)**: Regional public health directors monitoring network-wide metrics, disease outbreak clusters, ARS expenditure, and healthcare compliance.

### 1.3 Key Business Capabilities
- **Strict Role-Based Access Control (RBAC)**: Eight mutually exclusive operational roles with authoritative backend enforcement.
- **Single-Facility & Multi-Facility Scoping**: Frontline staff are strictly locked to their assigned physical clinic; regional directors hold multi-clinic governance.
- **Immutable Inventory Ledger**: Stock can never be directly incremented or decremented; all stock modifications flow through an auditable, double-entry inventory movement ledger.
- **Longitudinal EMR Privacy**: Separation between demographic lookup and clinical records. Clerical and administrative staff cannot inspect clinical diagnoses or medical histories.

---

## 2. High-Level Application Architecture

The platform follows a modern, robust, three-tier local architecture optimized for high performance, local data sovereignty, and offline resilience.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION TIER                             │
│       React 18 • TypeScript • Tailwind CSS • Vite Client Shell         │
│  (Role-Governed UI • Single Page Application • Dynamic Route Guards)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTP REST / JSON (JWT Session)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION TIER                             │
│             Django 4.2 LTS • Django REST Framework (DRF)               │
│  - Authoritative RBAC & Permission Enforcement Engine                  │
│  - Facility-Scoped Query Filtering & Privacy Redaction Engine          │
│  - State Machine Engines (Queue, Prescriptions, Orders, Staff Lifecycle│
│  - Inventory Movement Ledger Service & FEFO Validation                 │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ PostgreSQL Dialect / TCP
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                            DATA TIER                                   │
│                  PostgreSQL 16 Relational Engine                       │
│  - 26 Domain Schemas • Referential Integrity & Foreign Key Cascades    │
│  - Optimistic Concurrency & Row-Level Locking on Movement Ledgers      │
│  - Immutable Audit Trails & Historical Temporal Tracking               │
└────────────────────────────────────────────────────────────────────────┘
```

### Architectural Principles:
1. **Backend Authoritative Rule**: The browser client is an untrusted presentation layer. Every permission check, facility scope filter, and transition validation is executed authoritatively in the Django service layer.
2. **Stateless JWT Authentication**: Fast cryptographic verification of user identities with dynamic backend role-permission resolution.
3. **Local Laptop Portability**: Zero cloud dependency. The entire stack—PostgreSQL 16, Django 4.2, and React 18—runs completely on local workstations or on-premises clinic mini-servers.

---

## 3. Role-Based Application Workstations

The platform provides dedicated, custom-tailored user interfaces for each approved operational role.

### 3.1 District Health Officer (DHO)
* **Purpose**: District-wide oversight, administrative governance, and epidemiological surveillance across all networked clinics.
* **Responsibilities**: Overseeing clinic performance KPIs, tracking disease outbreaks, reviewing quality scores, managing staff postings across clinics, and monitoring ARS allocations.
* **Accessible Modules**: District Dashboard, Healthcare Network, Staff Directory, Facilities, Patients, Queue, Pharmacy, Referrals, NCD, Surveillance, ARS, Quality, Infrastructure, Reports, Compliance, Audit, Integrations, Alerts.

![Figure 1 — District Health Officer Dashboard](../../scratch/ui_audit_screenshots/dho/01_dashboard_district.png)
*Figure 1 — District Health Officer Dashboard — Executive view of district-wide patient counts, clinic uptime, and regional health indicators (demonstration data).*

![Figure 2 — Regional Healthcare Network Topology](../../scratch/ui_audit_screenshots/dho/02_network.png)
*Figure 2 — Regional Healthcare Network Topology — Interactive map visualizing Primary Health Centers, Urban Health Centers, and referral hospitals across the district.*

---

### 3.2 Hospital / Clinic Administrator
* **Purpose**: Facility-level governance, clinical operations management, and staff identity administration.
* **Responsibilities**: Onboarding clinic personnel, assigning operational roles, reviewing daily token volumes, and monitoring local operational alerts.
* **Accessible Modules**: Clinic Admin Dashboard, Staff Administration, Facilities, Patient Directory, OPD Queue, Pharmacy Overview, Inventory Overview, Referrals, Follow-ups, Infrastructure, Reports, Alerts.

![Figure 3 — Hospital Administrator Dashboard](../../scratch/ui_audit_screenshots/admin/01_dashboard_admin.png)
*Figure 3 — Hospital Administrator Dashboard — Facility-level operational KPIs, doctor availability, queue occupancy, and stock alerts (demonstration data).*

![Figure 4 — Staff Lifecycle & Administration Console](../../scratch/ui_audit_screenshots/admin/03_admin_staff.png)
*Figure 4 — Staff Lifecycle & Administration Console — Authoritative clinic staff directory showing active role assignments, employee IDs, and lifecycle management controls.*

---

### 3.3 Medical Officer (Doctor)
* **Purpose**: Patient consultation, clinical assessment, electronic diagnostics, and treatment plan generation.
* **Responsibilities**: Calling queued patients, recording symptoms and physical examination findings, entering formal diagnoses, requesting diagnostic laboratory investigations, and ordering electronic prescriptions.
* **Accessible Modules**: Doctor Dashboard, Patient Directory, Doctor Queue, Consultation Workstation, Lab Review, Referrals, Follow-ups, NCD Registry, Alerts.

![Figure 5 — Doctor Consultation Workstation Dashboard](../../scratch/ui_audit_screenshots/doctor/01_dashboard_doctor.png)
*Figure 5 — Doctor Consultation Workstation Dashboard — Overview of waiting patients, completed consultations, and active prescription metrics.*

![Figure 6 — Detailed Clinical Consultation & Prescription Form](../../scratch/ui_audit_screenshots/doctor/consultation_form_detailed.png)
*Figure 6 — Detailed Clinical Consultation & Prescription Form — Comprehensive electronic medical record entry form showing clinical diagnosis, vitals review, and e-prescription inputs.*

---

### 3.4 Staff Nurse
* **Purpose**: Patient intake triage, vital signs measurement, clinical acuity prioritization, and wellness tracking.
* **Responsibilities**: Measuring and recording blood pressure, pulse, temperature, SpO2, and respiratory rate; calculating derived BMI; assigning triage acuity colors; coordinating patient handoff to clinicians.
* **Accessible Modules**: Nurse Dashboard, Patient Directory, Triage Queue, Vitals Recording, Follow-ups, NCD Monitoring, Outreach Camps, Wellness Programs, Alerts.

![Figure 7 — Staff Nurse Triage Dashboard](../../scratch/ui_audit_screenshots/nurse/01_dashboard_nurse.png)
*Figure 7 — Staff Nurse Triage Dashboard — Nurse queue overview displaying incoming walk-ins, waiting triage counts, and vital monitoring alerts.*

![Figure 8 — Clinical Vitals & Triage Assessment Form](../../scratch/ui_audit_screenshots/nurse/triage_form_detailed.png)
*Figure 8 — Clinical Vitals & Triage Assessment Form — Standardized vitals capture form with automated BMI computation and triage acuity categorization.*

---

### 3.5 Front Desk Officer
* **Purpose**: Patient front-desk intake, demographic registry search, new citizen registration, and sequential OPD token generation.
* **Responsibilities**: Searching existing patient database by mobile/name/ABHA, registering newly presenting citizens with address and vulnerability indicators, minting daily sequential OPD tokens, and managing waiting queue tokens.
* **Accessible Modules**: Front Desk Console, Patient Directory, OPD Queue, Alerts.
* **Strict Privacy Isolation**: Front Desk Officers have zero access to clinical consultations, laboratory results, diagnoses, or pharmaceutical dispensing records.

![Figure 9 — Front Desk Intake Console](../../scratch/ui_audit_screenshots/compounder/01_dashboard_compounder.png)
*Figure 9 — Front Desk Intake Console — Front desk reception console displaying incoming patient intake numbers, quick search bar, and daily OPD token stats.*

![Figure 10 — Citizen Intake Registration Modal](../../scratch/ui_audit_screenshots/compounder/modal_01_registration_opened.png)
*Figure 10 — Citizen Intake Registration Modal — Intake form capturing citizen demographics, emergency contacts, vulnerability group, and demographic fields.*

---

### 3.6 Diagnostic Lab Technician
* **Purpose**: Diagnostic laboratory specimen processing, order tracking, and electronic test result reporting.
* **Responsibilities**: Receiving doctor-ordered diagnostic tests, collecting laboratory specimens, conducting investigations (CBC, Blood Glucose, Lipid Profiles, etc.), and publishing verified lab reports.
* **Accessible Modules**: Laboratory Dashboard, Lab Queue, Test Orders, Result Entry, Alerts.

![Figure 11 — Laboratory Diagnostic Workstation](../../scratch/ui_audit_screenshots/lab_technician/01_dashboard_lab.png)
*Figure 11 — Laboratory Diagnostic Workstation — Real-time diagnostic test queue displaying ordered tests, specimen collection statuses, and pending lab verifications.*

![Figure 12 — Diagnostic Investigation Orders & Results](../../scratch/ui_audit_screenshots/lab_technician/03_lab.png)
*Figure 12 — Diagnostic Investigation Orders & Results — Specimen intake list allowing technicians to verify specimens and enter numeric investigation parameters.*

---

### 3.7 Pharmacist
* **Purpose**: Prescription verification, medication dispensing, FEFO batch allocation, and facility pharmacy stock visibility.
* **Responsibilities**: Reviewing doctor e-prescriptions, placing invalid prescriptions on hold, selecting earliest expiring batches (FEFO), dispensing medications, and counseling patients.
* **Accessible Modules**: Pharmacy Dashboard, Dispensation Queue, Prescription Verification, Infrastructure (Drug Storage Conditions), Alerts.

![Figure 13 — Pharmacy Dispensing Dashboard](../../scratch/ui_audit_screenshots/pharmacist/01_dashboard_pharmacy.png)
*Figure 13 — Pharmacy Dispensing Dashboard — Pharmacist overview tracking pending doctor prescriptions, dispensed tokens, and low-stock alerts.*

![Figure 14 — Electronic Prescription Verification & Dispensing](../../scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png)
*Figure 14 — Electronic Prescription Verification & Dispensing — Prescription verification table showing doctor orders, batch recommendations, and dispense controls.*

---

### 3.8 Inventory Officer
* **Purpose**: Centralized facility stock management, procurement orders, vendor Goods Receipt Notes (GRN), and physical stock reconciliation.
* **Responsibilities**: Raising vendor purchase orders, receiving drug shipments against POs, recording batch numbers and expiry dates, and conducting physical inventory audits.
* **Accessible Modules**: Inventory Console, Procurement Workstation, Purchase Orders, Goods Receipt (GRN), Stock Adjustments, Movement Ledger, Alerts.
* **Strict Separation of Duties**: Inventory managers cannot dispense medications to patients; they strictly manage warehouse and facility stock tiers.

![Figure 15 — Inventory Workstation & Batch Stock Balances](../../scratch/ui_audit_screenshots/inventory/01_inventory.png)
*Figure 15 — Inventory Workstation & Batch Stock Balances — Real-time facility inventory ledger displaying batch quantities, expiry dates, and unit prices.*

![Figure 16 — Purchase Order Procurement Management](../../scratch/ui_audit_screenshots/inventory/inventory_01_po_tab.png)
*Figure 16 — Purchase Order Procurement Management — Procurement dashboard showing active vendor purchase orders, delivery statuses, and creation modal controls.*

---

### 3.9 Dual-Role Operational Configuration (Small-Clinic Rule)
* **Purpose**: Operational flexibility for small rural or urban health outposts where a single staff member must fulfill multiple administrative duties without creating combined hybrid roles.
* **Supported Combinations**:
  - `NURSE` + `FRONT_DESK_OFFICER`: Allows a single nurse in a small PHC to register incoming patients, mint OPD tokens, and then conduct clinical triage.
  - `PHARMACIST` + `INVENTORY`: Allows a facility pharmacist to manage both warehouse procurement/GRN receiving and dispensary patient-facing operations.
* **Authoritative Principle**: Dual roles are represented as **two distinct, independent role assignments** attached to a single staff profile. Permissions resolve dynamically as the union of both roles.

![Figure 17 — Dual-Role Pharmacy & Procurement Workstation](../../scratch/ui_audit_screenshots/dual_role/01_dashboard_pharmacy.png)
*Figure 17 — Dual-Role Pharmacy & Procurement Workstation — Integrated console for a dual-assigned user showing seamless access to both clinical dispensary and inventory operations.*

---

## 4. The Complete Patient Journey

The patient journey through Namma Clinic follows a governed, auditable state machine ensuring quality care, complete clinical documentation, and zero administrative bottlenecks.

```
┌─────────────────────────┐
│ 1. PATIENT REGISTRATION │  Front Desk Officer records demographics, contact info & vulnerability.
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│   2. OPD TOKEN ISSUE    │  Daily sequential token issued (e.g., T-101); visit encounter created.
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│   3. OPD WAITING QUEUE  │  Patient appears in live waiting queue; visible across clinic workstations.
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│     4. NURSE TRIAGE     │  Nurse measures vitals (BP, HR, SpO2, Temp), calculates BMI & assigns acuity.
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  5. DOCTOR CONSULTATION │  Doctor reviews vitals, conducts exam, records diagnoses & creates orders.
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 6. DIAGNOSTICS & ORDERS │  Doctor requisitions Lab Investigations and writes e-Prescriptions.
└─────┬─────────────┬─────┘
      ▼             ▼
┌───────────┐ ┌───────────┐
│ 7. LAB    │ │ 8. PHARM  │  Lab tech conducts tests & enters results. Pharmacist verifies & dispenses.
└─────┬─────┘ └─────┬─────┘
      └──────┬──────┘
             ▼
┌─────────────────────────┐
│  9. FOLLOW-UP & RECORD  │  Encounter marked COMPLETED; longitudinal EMR record updated for follow-up.
└─────────────────────────┘
```

### Stage 1: Citizen Intake & Registration
When a citizen arrives at the clinic, the Front Desk Officer searches the demographic registry by phone number, name, or health ID. If the citizen is new, an intake registration form captures their personal information, address, and vulnerability classification.

![Figure 18 — Patient Registration Interface](../../scratch/ui_audit_screenshots/compounder/modal_01_registration_opened.png)
*Figure 18 — Patient Registration Interface — Front Desk Officer enters citizen demographics, ensuring no synthetic ABHA identifiers are created.*

### Stage 2: Token Issuance & Queue Placement
Upon confirming registration, the Front Desk Officer generates an OPD Token. The system assigns a sequential daily queue number (e.g., `T-001`, `T-002`) and places the encounter in `WAITING_FOR_TRIAGE` status.

![Figure 19 — Live OPD Queue Management](../../scratch/ui_audit_screenshots/compounder/03_queue.png)
*Figure 19 — Live OPD Queue Management — Real-time facility waiting queue displaying waiting tokens, patient identifiers, and priority designations.*

### Stage 3: Nurse Triage & Vitals
The Staff Nurse calls the next patient from the triage queue into the nursing room. The nurse measures vital signs and records symptoms. The system automatically computes BMI and flags abnormal parameters.

![Figure 20 — Nurse Vitals Triage Screen](../../scratch/ui_audit_screenshots/nurse/triage_form_detailed.png)
*Figure 20 — Nurse Vitals Triage Screen — Nurse enters systolic/diastolic blood pressure, pulse, SpO2, and temperature, categorizing clinical acuity.*

### Stage 4: Doctor Examination & Electronic Prescription
The patient advances to the Doctor consultation queue. The Doctor calls the patient into the consultation room, reviews the nursing vitals, records symptoms, select diagnoses, and generates electronic prescriptions and diagnostic orders.

![Figure 21 — Doctor Consultation & E-Prescription Form](../../scratch/ui_audit_screenshots/doctor/consultation_form_detailed.png)
*Figure 21 — Doctor Consultation & E-Prescription Form — Doctor documents clinical findings and prescribes medications with dosage and frequency instructions.*

### Stage 5: Diagnostics & Dispensation Fulfillment
If diagnostic investigations were ordered, the patient visits the on-site lab where the Lab Technician collects samples and records test values. Simultaneously, the e-prescription flows to the dispensary where the Pharmacist verifies the order, reviews FEFO batch allocations, and dispenses the medications.

![Figure 22 — Pharmacist Dispensing Queue](../../scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png)
*Figure 22 — Pharmacist Dispensing Queue — Pharmacist inspects active prescriptions and dispenses items from eligible non-expired stock batches.*

---

## 5. Major Application Modules Reference

The Namma Clinic platform is composed of 23 functional modules, each addressing a critical pillar of clinic operations.

| # | Module Name | Primary User Roles | Core Business Capabilities |
| :--- | :--- | :--- | :--- |
| **01** | **Executive Dashboards** | All Roles (Role-Specific) | Role-tailored operational consoles, real-time KPI metrics, waiting queues, and high-priority alerts. |
| **02** | **Patient Demographic Registry** | DHO, Admin, Clinicians, Front Desk | Master patient index lookup, contact search, demographic records, and registration history. |
| **03** | **Patient Registration** | Front Desk Officer, Admin | Citizen onboarding, deduplication checks, emergency contact capture, and vulnerability tags. |
| **04** | **OPD Queue Management** | Front Desk, Nurse, Doctor, Admin | Sequential token dispatch, real-time waiting queues, call-next patient actions, and void token controls. |
| **05** | **Clinical Triage** | Staff Nurse | Vital signs measurement, automatic BMI derivation, clinical acuity scoring, and nurse-to-doctor handoff. |
| **06** | **Doctor Consultation** | Medical Officer (Doctor) | Clinical diagnosis, clinical note recording, diagnostic lab orders, and electronic prescribing. |
| **07** | **Laboratory Workstation** | Lab Technician, Doctor | Diagnostic test order queue, specimen collection tracking, numeric result entry, and reference ranges. |
| **08** | **Pharmacy Dispensing** | Pharmacist, Admin | E-prescription queue, prescription verification, on-hold reasoning, and FEFO medication dispensing. |
| **09** | **Inventory & Procurement** | Inventory Manager, Admin | Stock ledger, purchase order generation, Goods Receipt Notes (GRN), and physical stock reconciliation. |
| **10** | **Staff Administration** | Hospital Admin, DHO | Staff directory, employee onboarding, operational role assignments, transfers, and suspensions. |
| **11** | **Referrals Management** | Doctor, DHO, Admin | Inter-facility patient referrals, higher-tier hospital escalations, transfer notes, and specialty routing. |
| **12** | **Patient Follow-ups** | Nurse, Doctor, Admin | Scheduled recall visits, chronic care follow-up tracking, missed appointment monitoring, and reminders. |
| **13** | **NCD Registry** | Nurse, Doctor, DHO | Non-Communicable Disease screening (Hypertension, Diabetes), longitudinal tracking, and risk tiers. |
| **14** | **Public Health Surveillance** | DHO | Epidemiological syndromic surveillance, outbreak cluster detection, disease incidence tracking, and maps. |
| **15** | **Community Outreach** | Staff Nurse | Slum health camps, mobile outreach schedules, community immunization campaigns, and attendance logs. |
| **16** | **Wellness & Preventive** | Staff Nurse | Preventive wellness programs, nutrition guidance sessions, lifestyle counseling, and health education. |
| **17** | **Quality Indicators** | DHO, Hospital Admin | Patient wait times, consultation durations, clinical guideline compliance, and patient satisfaction KPIs. |
| **18** | **Infrastructure & Storage** | Admin, Pharmacist, DHO | Cold-chain equipment monitoring, drug storage conditions, power backup logs, and facility assets. |
| **19** | **Operational Reporting** | DHO, Hospital Admin | Daily outpatient summaries, morbidity breakdowns, pharmacy consumption trends, and exportable tables. |
| **20** | **Alerts & Notification Hub** | All Roles | Critical inventory depletion warnings, near-expiry drug batches, unverified prescriptions, and triage flags. |
| **21** | **Security & Audit Logs** | DHO, Hospital Admin | Tamper-evident audit trails, security event logging, login attempts, and permission change records. |
| **22** | **Interoperability Standards** | DHO, Hospital Admin | Readiness consoles for national health data standards (demonstration and local contract validation). |
| **23** | **Administrative Compliance** | DHO | Regulatory compliance monitoring, statutory facility licensing, inspection checklists, and audit tracking. |

### Module Visual Highlights

#### Staff Administration Module
The Staff Administration module enables clinic superintendents and district directors to manage healthcare personnel without granting full administrative privileges over the underlying server.

![Figure 23 — Clinic Staff Administration Table](../../scratch/ui_audit_screenshots/admin/staff_admin_table.png)
*Figure 23 — Clinic Staff Administration Table — Staff directory displaying active designations, facility postings, and role management actions.*

#### Non-Communicable Diseases (NCD) Module
Dedicated tracking for chronic conditions like hypertension and diabetes ensures longitudinal treatment adherence for urban populations.

![Figure 24 — Non-Communicable Disease Registry](../../scratch/ui_audit_screenshots/nurse/06_ncd.png)
*Figure 24 — Non-Communicable Disease Registry — Chronic disease patient tracking panel categorized by risk stage and screening dates.*

#### Public Health Surveillance Module
District directors monitor real-time symptom clustering to rapidly identify seasonal or communicable disease outbreaks.

![Figure 25 — Public Health Surveillance Console](../../scratch/ui_audit_screenshots/dho/10_surveillance.png)
*Figure 25 — Public Health Surveillance Console — Epidemiological monitoring dashboard displaying syndromic case counts and outbreak early warnings.*

#### Operational Reporting Module
Facility superintendents and district directors generate daily operational logs, morbidity distributions, and medication usage summaries.

![Figure 26 — Operational Reports & Healthcare Analytics](../../scratch/ui_audit_screenshots/admin/13_reports.png)
*Figure 26 — Operational Reports & Healthcare Analytics — Aggregate reporting engine detailing outpatient attendance, top clinical diagnoses, and throughput.*

#### Security Audit Trail Module
Every administrative action, role assignment, and security transition is recorded in an immutable audit ledger.

![Figure 27 — Security Audit Trail Console](../../scratch/ui_audit_screenshots/dho/16_audit.png)
*Figure 27 — Security Audit Trail Console — Immutable event log capturing user authentication, role assignments, and system security actions.*

---

## 6. Inventory & Pharmacy Separation of Duties

A core architectural strength of the Namma Clinic platform is the **strict separation between Warehouse Inventory Management and Clinical Pharmacy Dispensing**.

```
WAREHOUSE & PROCUREMENT DOMAIN (Inventory Manager)
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│ Purchase Order (PO)  │ ───► │ Goods Receipt Note   │ ───► │ Immutable Inventory  │
│ Vendor requisitions  │      │ Batch/Expiry intake  │      │ Movement Ledger      │
└──────────────────────┘      └──────────────────────┘      └──────────┬───────────┘
                                                                       │ Stock Inflow
                                                                       ▼
CLINICAL DISPENSARY DOMAIN (Pharmacist & Clinician)         ┌──────────────────────┐
┌──────────────────────┐      ┌──────────────────────┐      │ Available Clinic     │
│ Doctor Prescription  │ ───► │ Pharmacist           │ ───► │ Batch Stock (FEFO)   │
│ EMR Treatment Order  │      │ Verification & Hold  │      └──────────┬───────────┘
└──────────────────────┘      └──────────────────────┘                 │ Stock Outflow
                                                                       ▼
                                                            ┌──────────────────────┐
                                                            │ Patient Dispensation │
                                                            │ Deducts batch stock  │
                                                            └──────────────────────┘
```

### Architectural Guarantees:
1. **No Direct Balance Modification**: Storekeepers and pharmacists cannot directly alter stock totals. Every change must be backed by a Purchase Order receipt, a Patient Dispensation, or a formal signed adjustment.
2. **FEFO Principle Enforcement**: When a prescription is prepared, the system automatically surfaces and recommends the earliest-expiring active batch, eliminating expired drug waste.
3. **No Dispensing by Inventory Officers**: Inventory Officers cannot dispense medication to citizens. Only licensed Pharmacists holding active facility credentials can execute patient dispensations.

![Figure 28 — Purchase Order Modal in Inventory](../../scratch/ui_audit_screenshots/inventory/inventory_02_po_modal.png)
*Figure 28 — Purchase Order Modal in Inventory — Inventory workstation dialog for creating structured supplier purchase orders.*

![Figure 29 — Pharmacist Verification & Dispensation](../../scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png)
*Figure 29 — Pharmacist Verification & Dispensation — Clinical dispensing workstation verifying doctor e-prescriptions against real-time FEFO batches.*

---

## 7. Security Architecture & Role-Based Access Control (RBAC)

Namma Clinic implements enterprise-grade security standards tailored for sensitive medical data.

### 7.1 Authoritative Backend Authorization
All client interactions are validated against the PostgreSQL database using a strict authorization tuple:
$$\text{Access Granted} \iff \text{HasRolePermission}(\text{User}, \text{Action}) \land \text{CanAccessFacility}(\text{User}, \text{TargetFacility})$$

- **Frontend Route Protection**: If an unauthorized user attempts to enter a restricted URL (e.g., a Staff Nurse accessing `/consultation` or `/admin/staff`), the client route guard intercepts the attempt and displays a security-compliant `ForbiddenCard`.
- **Backend API Rejection**: If an unauthorized request bypasses the client and hits the API directly, the Django REST Framework permission classes return `HTTP 403 Forbidden` with a standardized error structure.

![Figure 30 — Security-Governed Unauthorized Route Interception](../../scratch/ui_audit_screenshots/nurse/unauth_consultation.png)
*Figure 30 — Security-Governed Unauthorized Route Interception — Clean, security-enforced card presented when an operational role attempts to navigate outside its authorized boundary.*

### 7.2 Patient Demographic & Clinical Record Scoping
To protect citizen privacy, patient data visibility is segmented by role responsibility:
- **Clerical Intake (Front Desk Officer)**: Permitted to read and update demographic data (Name, Age, Gender, Mobile, Address, Vulnerability). Strictly prohibited from viewing doctor consultation notes, past medical history, diagnoses, lab results, or prescriptions.
- **Diagnostics (Lab Technician)**: Permitted to view diagnostic test orders and submit results. Prohibited from editing longitudinal clinical notes or issuing prescriptions.
- **Clinicians (Doctor & Nurse)**: Permitted access to full longitudinal electronic medical records for active clinical encounters within their assigned facility.

![Figure 31 — Demographic Action Scoping in Patient Registry](../../scratch/ui_audit_screenshots/inventory/patients_action_visibility.png)
*Figure 31 — Demographic Action Scoping in Patient Registry — Patient directory demonstrating restricted action controls for non-clinical staff.*

---

## 8. Operational & Clinical Business Value

Deploying the Namma Clinic platform delivers measurable operational improvements across primary healthcare centers:

1. **Elimination of Clinic Congestion**:
   - Automated OPD token generation provides transparent queue visibility, reducing waiting room friction and patient anxiety.
2. **Clinical Safety & Acuity Management**:
   - Nurse vitals scoring ensures that critically ill patients (`IMMEDIATE` or `VERY_URGENT`) are flagged immediately for clinician intervention.
3. **Pharmaceutical Accuracy & Expiry Mitigation**:
   - Electronic prescribing eliminates illegible handwritten orders. Automated FEFO batch sorting prevents expired medication dispensation and reduces government stock loss.
4. **Zero-Trust Administrative Auditability**:
   - Every staff onboarding, role modification, token issuance, consultation, and stock movement is stamped with an immutable author attribution, timestamp, and facility identifier.
5. **Offline & Edge Network Resilience**:
   - The platform operates seamlessly on standalone local clinic hardware without requiring constant high-speed cloud connectivity, ensuring continuous clinic uptime during network interruptions.

---

## 9. Current Application Scope & Implementation Status

To maintain strict factual accuracy, the table below provides a transparent audit of the platform's current implementation status.

| Capability / Module | Current Implementation Status | Operational Details |
| :--- | :--- | :--- |
| **User Authentication & RBAC** | ✅ **Fully Implemented** | 8 canonical roles, JWT authentication, backend permission tables, and facility scoping. |
| **Front Desk Intake & Tokens** | ✅ **Fully Implemented** | Full citizen registration, mobile deduplication, and daily sequential OPD token generation. |
| **Nurse Triage & Acuity** | ✅ **Fully Implemented** | Vitals capture (BP, HR, SpO2, Temp, RR), BMI calculation, and 5-tier acuity classification. |
| **Doctor Consultation & E-Rx** | ✅ **Fully Implemented** | Symptom logging, clinical diagnoses, e-prescriptions, and diagnostic laboratory requisitions. |
| **Laboratory Diagnostics** | ✅ **Fully Implemented** | Diagnostic test order queue, specimen tracking, and numeric lab result publishing. |
| **Pharmacy Dispensation** | ✅ **Fully Implemented** | E-prescription verification, on-hold reason tracking, and FEFO-governed stock deduction. |
| **Inventory & Procurement** | ✅ **Fully Implemented** | Purchase orders, GRN entry, batch tracking, and double-entry movement ledger. |
| **Staff Lifecycle Administration** | ✅ **Fully Implemented** | Role assignments, dual-role configuration, staff transfers, and account suspensions. |
| **Public Health & Quality** | ✅ **Fully Implemented** | Syndromic surveillance, NCD tracking, ARS allocations, and quality KPI dashboards. |
| **Local Environment Execution** | ✅ **Active Operational Mode** | Tested and verified locally on PostgreSQL 16, Django 4.2 LTS, and React 18 / Vite. |
| **External Integrations (ABHA/ABDM)** | ⚠️ **Readiness / Simulated Mode** | UI fields and data models are ABDM-compliant; external government API endpoints operate in local demonstration/mock mode. |
| **Cloud Deployment Infrastructure** | ⚠️ **Local Workstation Scope** | Designed and certified for on-premises clinic servers and local laptops. Cloud containerization is out of current scope. |

---

## 10. Future Roadmap & Planned Capabilities

The following features represent strategic enhancements planned for future development phases:

* **Phase 29 — ABDM Production Gateway Integration**: Connecting the existing ABDM data models to live national health gateways (ABHA creation via OTP, Aarogya Setu QR scanning, and HIP/HIU record exchange).
* **Phase 30 — Telemedicine & Remote Consultation**: Integrated WebRTC video consultation enabling urban clinic doctors to connect patients with district hospital medical specialists.
* **Phase 31 — Centralized District Sync Gateway**: Asynchronous edge-to-cloud data replication allowing offline clinic servers to push nightly encrypted batches to central health department databases.
* **Phase 32 — Barcode & QR Code Dispensing**: Mobile camera-based barcode scanning for rapid medicine batch verification and patient token scanning.

---

## 11. Glossary of Terms

* **ABHA (Ayushman Bharat Health Account)**: The unique national digital health identifier issued to citizens under India's Digital Health Mission.
* **ABDM (Ayushman Bharat Digital Mission)**: The national digital healthcare interoperability ecosystem and specification standard.
* **ARS (Arogya Raksha Samiti)**: Untied clinic development and untied maintenance funds allocated to primary health centers for facility upkeep.
* **BMI (Body Mass Index)**: A derived mathematical value calculated from patient weight and height ($kg/m^2$).
* **DHO (District Health Officer)**: The regional administrative and public health director responsible for healthcare governance across an entire district.
* **EMR (Electronic Medical Record)**: The longitudinal digital health record containing all clinical consultations, diagnoses, prescriptions, and laboratory reports for a patient.
* **FEFO (First-Expired, First-Out)**: An inventory management rule requiring that medication batches expiring earliest must be dispensed before newer stock.
* **Front Desk Officer**: The administrative staff member stationed at clinic reception responsible for patient intake, identity search, and OPD token generation.
* **GRN (Goods Receipt Note)**: An authoritative warehouse receiving document verifying that ordered physical pharmaceuticals have been inspected and placed into clinic storage.
* **NCD (Non-Communicable Disease)**: Chronic medical conditions (e.g., Hypertension, Type-2 Diabetes) requiring ongoing monitoring and regular medication refills.
* **OPD (Outpatient Department)**: Clinic ambulatory care services provided to walk-in citizens not requiring overnight hospital admission.
* **PHC (Primary Health Center)**: Basic urban or rural government primary care health facility delivering frontline health services.
* **RBAC (Role-Based Access Control)**: A security framework that restricts application features and database records based on an authorized staff member's official role.
* **SpO2**: Blood oxygen saturation percentage measured via pulse oximetry.
* **Vitals**: Core physiological indicators of health status (Blood Pressure, Heart Rate, Respiratory Rate, Temperature, and Oxygen Saturation).
