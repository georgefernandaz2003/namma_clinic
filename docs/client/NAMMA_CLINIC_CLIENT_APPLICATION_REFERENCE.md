![Kushagramati Analytics](kushagramati_logo.png)

# NAMMA CLINIC
## Digital Healthcare & Clinic Management Platform
### Client Application Reference Manual

---

# PART A — UNDERSTANDING THE APPLICATION

## 1. Document Overview & Executive Introduction

This document provides a comprehensive, non-technical reference guide to the **Namma Clinic Platform**. It is written for healthcare administrators, medical superintendents, clinical leaders, and frontline healthcare professionals.

Whether you are a District Health Officer reviewing network performance, a Medical Officer conducting consultations, a Staff Nurse prioritizing walk-in patients, a Pharmacist dispensing medications, or a Front Desk Officer welcoming citizens at reception, this guide explains how the platform supports your daily work and how patients move safely and efficiently through primary care.

---

## 2. What is Namma Clinic?

**Namma Clinic** is a unified digital health and clinic operations platform created specifically for primary healthcare facilities, including urban health centers, neighborhood clinics, and primary health centers (PHCs). 

The platform connects all primary healthcare disciplines within a clinic—reception, nursing vitals, clinical examination, laboratory diagnostics, and pharmacy dispensing—into an orderly, sequential workflow. Every action recorded by a staff member updates the operational clinic queue and creates an audit-ready record for continuity of care.

| Stage 1: Reception & Registration | Stage 2: Nursing Triage & Vitals | Stage 3: Doctor Consultation | Stage 4: Diagnostics & Dispensing |
| :--- | :--- | :--- | :--- |
| **Front Desk Officer**<br>&bull; Citizen verification<br>&bull; Demographic registration<br>&bull; Sequential OPD tokens | **Staff Nurse**<br>&bull; Physiological vitals<br>&bull; Automated BMI scoring<br>&bull; Triage acuity assignment | **Medical Officer**<br>&bull; Clinical examination<br>&bull; ICD-10 diagnoses<br>&bull; Electronic prescriptions | **Lab & Pharmacy**<br>&bull; Diagnostic lab results<br>&bull; FEFO stock allocation<br>&bull; Patient dispensing |
| **District Oversight**<br>Aggregated reporting & public health visibility | **Clinical Safety**<br>Standardized vital ranges & triage acuity checks | **Role Governance**<br>Strict separation of duties & role-based access | **Inventory Control**<br>FEFO batch dispensing & automated ledger audit |

The system is designed to run directly on standard clinic workstations and laptops at the clinic facility itself. Routine local clinic workflows operate against the on-premises database instance, allowing clinic intake, triage, consultation, and dispensing to remain locally accessible even when external WAN or internet connectivity is intermittent.

---

## 3. Problems Namma Clinic Solves

Urban primary clinics face significant operational hurdles when relying on manual registers, paper prescription slips, and fragmented single-purpose applications:

| Traditional Clinic Challenge | Namma Clinic Operational Solution |
| :--- | :--- |
| **Overcrowded Waiting Rooms & Queue Disputes**<br>Patients congregate around consultation doors without knowing when they will be seen. | **Automated Sequential OPD Tokens**<br>Every patient receives an individual daily token upon arrival. Workstations call patients sequentially, providing fair and orderly patient flow. |
| **Unrecognized Emergencies in Waiting Areas**<br>Critically ill walk-in patients wait alongside non-urgent cases without prompt clinical review. | **Standardized Nurse Triage & Acuity Flags**<br>Nurses measure vitals before the doctor consultation. Critical cases are flagged red/orange and prioritized in the doctor’s queue. |
| **Illegible Hand-Written Prescriptions**<br>Pharmacy errors, misread drug dosages, and dispensing mistakes caused by poor handwriting. | **Structured Electronic Prescriptions**<br>Doctors prescribe from standardized drug lists with verified strengths, dosage forms, frequencies, and duration instructions. |
| **Expired Drug Wastage & Unpredictable Stockouts**<br>Expensive medicine batches expire unseen in storage while clinics unexpectedly run out of vital medications. | **Automated First-Expired, First-Out (FEFO) Dispensing**<br>The system recommends the earliest-expiring active batch first and triggers automated alerts when minimum stock thresholds are crossed. |
| **Compromised Patient Medical Privacy**<br>Clerical staff and intake workers inadvertently view sensitive clinical notes and diagnoses in paper registers. | **Strict Separation of Duties & Privacy Boundaries**<br>Front-desk personnel only view demographic records. Clinical consultation history, diagnoses, and lab results are restricted to doctors and nurses. |
| **Delayed Disease Outbreak Detection**<br>District health authorities receive paper disease reports days or weeks after an outbreak has begun. | **Syndromic Disease Surveillance (Demonstration)**<br>Diagnosed fever, respiratory infection, and waterborne symptom categories aggregate into visual surveillance dashboards to demonstrate outbreak pattern tracking. |

---

## 4. Who Uses Namma Clinic?

The platform provides dedicated, custom-tailored workstations for eight operational roles:

1. **Front Desk Officer**: Welcomes citizens, searches existing patient records, registers new patients, and issues sequential daily outpatient (OPD) tokens.
2. **Staff Nurse**: Measures vital signs, computes Body Mass Index (BMI), assigns triage acuity scores, records follow-up care, and coordinates community health camps.
3. **Medical Officer (Doctor)**: Examines patients, documents clinical notes and diagnoses, requisitions diagnostic laboratory tests, writes electronic prescriptions, and arranges specialist referrals.
4. **Diagnostic Lab Technician**: Receives doctor-ordered laboratory tests, collects patient specimens, inputs test values, and publishes verified laboratory investigation reports.
5. **Pharmacist**: Verifies doctor prescriptions against available facility stock, dispenses medications according to First-Expired, First-Out rules, and counsels patients on drug usage.
6. **Inventory Officer**: Manages the clinic medicine store, generates purchase orders to suppliers, inspects incoming deliveries with Goods Receipt Notes (GRN), and audits stock balances.
7. **Clinic Administrator**: Manages facility operational schedules, configures clinic departments, onboards staff, assigns operational roles, and reviews daily attendance reports.
8. **District Health Officer (DHO)**: Oversees public health across all networked clinics in the district, monitors disease clusters, reviews clinic quality ratings, and governs staff allocations.

---

## 5. Overview of 21 Platform Capabilities

Namma Clinic organizes primary healthcare workflows, facility operations, supply chain logistics, and district governance into 21 structured platform capabilities. To ensure complete clarity for procurement officers, clinical leadership, and administrative stakeholders, these 21 capabilities are formally classified into three operational categories:

| 10 Implemented & Verified Core | 8 Demonstration & Extension Modules | 3 Cross-Cutting Platform Services |
| :--- | :--- | :--- |
| 1. Patient Demographics Registry<br>2. OPD Tokens & Queue Routing<br>3. Nursing Vitals & Clinical Triage<br>4. Doctor Clinical Consultation<br>5. Diagnostic Laboratory Orders<br>6. Pharmacy Dispensing & Stock<br>7. Warehouse Inventory Management<br>8. Purchase Orders & Procurement<br>9. Goods Receipt Notes (GRN)<br>10. Staff Administration & Multi-Role IAM | 11. Specialist Referrals<br>12. Patient Follow-up & Recalls<br>13. NCD Chronic Disease Registry<br>14. Syndromic Disease Surveillance<br>15. Outreach Camp Activity Logs<br>16. Community Wellness Sessions<br>17. Quality & Accreditation KPIs<br>18. Facility Infrastructure & Assets | 19. Operational Reporting Engine<br>20. Clinical & Supply Alerts Hub<br>21. Security & Audit Logging |

> [!NOTE]
> **Authoritative Capability Scope Breakdown**:
> - **10 Implemented & Verified Core Modules**: Fully operational end-to-end workflows backed by local database models, verified automated business logic, strict role authorization, and local clinic deployment. Dual-Role capability (*Small-Clinic Rule*) is built directly into Staff Administration rather than standing as an artificial separate module.
> - **8 Demonstration & Extension Modules**: Fully designed database schemas and user interface prototypes providing forward-looking workflows for specialized public health extensions (e.g., outreach camps, wellness programs, referral tracking). They currently operate in demonstration mode with mock or empty baselines.
> - **3 Cross-Cutting Platform Services**: Foundational system services providing operational reporting (implemented), dashboard alert aggregation (demonstration), and structured security audit logging (implemented).
> - **Administrative Capabilities**: Arogya Raksha Samiti (ARS) untied fund tracking is managed under Facility and District administrative governance.
> - **Maternal & Child Health (MCH / ANC / PNC / Immunization)**: Explicitly out of scope per Engineering Rule 10, as national and state maternal vertical health programs are managed through specialized state registries.

- **Universal Master Patient Index**: Rapid search by mobile number or patient name prevents duplicate paper files and maintains a single longitudinal medical record.
- **Five-Tier Clinical Acuity Triage**: Standardized prioritization (`IMMEDIATE`, `VERY_URGENT`, `URGENT`, `STANDARD`, `NON_URGENT`) ensures acute conditions receive rapid care.
- **Closed-Loop Diagnostic Flow**: Test orders recorded in the consultation room become immediately available in the laboratory worklist; completed results flow directly back to the doctor.
- **Warehouse vs. Dispensary Separation**: Warehouse Inventory Officers cannot dispense medicines to patients; dispensary pharmacists cannot arbitrarily modify bulk warehouse balances without verified receiving documentation.
- **Full Historical Audit Trails**: Every clinical diagnosis, prescription item, token cancellation, and stock deduction is stamped with the author’s name, time, and facility location.

---

## 6. How the Overall Clinic Operates

In a typical clinic morning, all healthcare disciplines work in harmony through connected platform screens:

1. **8:00 AM — Inventory Officer & Pharmacist Check**: The Inventory Officer and Pharmacist check the alerts screen to review near-expiry batches and verify stock levels for the day.
2. **8:30 AM — Front Desk Intake Starts**: As citizens arrive, the Front Desk Officer looks up existing cards or registers new patients, immediately issuing daily token numbers.
3. **8:35 AM — Triage Commences**: The Staff Nurse calls waiting tokens into the triage room, checks blood pressure, temperature, and pulse, and marks the clinical acuity.
4. **9:00 AM — Doctor Consultations**: The Medical Officer calls triaged patients in order of urgency, reviews vitals, conducts clinical examinations, and enters treatment plans.
5. **9:20 AM — Investigations & Dispensing**: Patients requiring tests proceed to the laboratory bench. Patients with prescriptions collect their medications at the pharmacy counter.
6. **1:30 PM — Operational Review**: The Clinic Administrator and District Health Officer review daily clinic throughput, waiting times, and disease surveillance summaries.

---

# PART B — USER WORKSTATIONS

---

## 1. District Health Officer (DHO) Workstation

### Purpose
The **District Health Officer Console** provides comprehensive executive governance, disease surveillance, and administrative supervision over all Primary Health Centers and Urban Clinics in the district.

### Core Responsibilities
- Monitor district-wide patient turnout, clinic operational status, and waiting times.
- Track communicable disease trends and syndromic outbreak indicators across reporting facilities.
- Supervise clinical quality scores, patient satisfaction metrics, and guideline adherence.
- Oversee staff deployment, postings, and transfers between district facilities.
- Supervise Arogya Raksha Samiti (ARS) development fund balances and expenditures.

### Screens Available
1. **District Dashboard**: High-level network KPIs, facility occupancy, and active caseload.
2. **Healthcare Network Map**: Geographic representation of clinics, health centers, and referral hospitals.
3. **Public Health Surveillance**: Disease incidence curves, syndromic fever tracking, and cluster warnings.
4. **District Staff Directory**: Comprehensive personnel roster across all district health facilities.
5. **Quality & Compliance Hub**: Clinic evaluation indicators, inspection checklists, and statutory licenses.

### Step-by-Step Workflow
1. The DHO logs in and reviews the **District Dashboard** to assess total patient visits across all clinics today.
2. The DHO opens **Public Health Surveillance** to check for unexpected clusters of respiratory illness or acute diarrheal disease.
3. If an outbreak pattern is detected in a specific zone, the DHO opens the **Healthcare Network Map**, identifies nearby clinics, and issues an operational advisory.
4. The DHO inspects the **Staff Administration Directory** to verify physician attendance and reassign relief personnel if a clinic is short-staffed.

### Information Visible to the DHO
- Total district outpatient count, consultations completed, and prescriptions dispensed.
- Active clinic count, facility operational status, and system uptime.
- Aggregated disease patterns and top clinical diagnoses across the district.
- Facility-by-facility stock alerts indicating critical antibiotic or vaccine shortages.

### Representative Screenshots

![Figure 1 — District Health Officer Executive Dashboard](../../scratch/ui_audit_screenshots/dho/01_dashboard_district.png)
*Figure 1 — District Health Officer Executive Dashboard — Displays total district attendance, active clinics, and district-wide healthcare delivery indicators.*

![Figure 2 — Regional Healthcare Network Map](../../scratch/ui_audit_screenshots/dho/02_network.png)
*Figure 2 — Regional Healthcare Network Map — Interactive geographical view showing Primary Health Centers, Urban Clinics, and tertiary referral hospitals.*

![Figure 3 — District Public Health Surveillance Console](../../scratch/ui_audit_screenshots/dho/10_surveillance.png)
*Figure 3 — District Public Health Surveillance Console — Epidemiological tracking console highlighting disease clusters and syndromic outbreak alerts.*

---

## 2. Clinic / Hospital Administrator Workstation

### Purpose
The **Clinic Administrator Console** equips the facility superintendent with day-to-day administrative oversight of clinic operations, staff scheduling, department setup, and operational compliance.

### Core Responsibilities
- Supervise facility staff attendance, employee postings, and active duty assignments.
- Assign operational roles (Doctor, Nurse, Front Desk Officer, Pharmacist, Lab Technician).
- Oversee outpatient department flow and manage clinic overcrowding.
- Monitor critical facility stock depletion and equipment cold-chain temperatures.
- Review daily attendance logs and clinic operational reports.

### Screens Available
1. **Clinic Admin Dashboard**: Overview of facility outpatient volume, queue length, and stock alerts.
2. **Staff Administration Console**: Employee directory, onboarding forms, and role assignment controls.
3. **Facility Operational Scope**: Clinic department management, operating hours, and room definitions.
4. **Facility Inventory Overview**: High-level stock balances and Inventory Officer purchase requisitions.
5. **Operational Reports**: Outpatient attendance summaries, morbidity distributions, and throughput.

### Step-by-Step Workflow
1. The Administrator begins the day by checking the **Clinic Admin Dashboard** to verify that all clinical stations (Triage, Doctor Room, Lab, Pharmacy) are staffed.
2. If a newly hired nurse arrives, the Administrator opens **Staff Administration**, enters the nurse's details, assigns the `NURSE` role, and designates their primary clinic.
3. Mid-day, the Administrator monitors queue wait times to ensure patients move from triage to consultation within approved clinic standards.
4. At end of shift, the Administrator generates the **Daily Operational Report** for submission to district management.

### Representative Screenshots

![Figure 4 — Hospital Administrator Operational Dashboard](../../scratch/ui_audit_screenshots/admin/01_dashboard_admin.png)
*Figure 4 — Hospital Administrator Operational Dashboard — Facility-level operational KPIs showing waiting queue sizes, doctor availability, and daily attendance.*

![Figure 5 — Clinic Staff Administration & Role Allocation](../../scratch/ui_audit_screenshots/admin/03_admin_staff.png)
*Figure 5 — Clinic Staff Administration & Role Allocation — Personnel management screen for inviting staff, assigning operational roles, and managing credentials.*

![Figure 6 — Daily Clinic Reporting Engine](../../scratch/ui_audit_screenshots/admin/13_reports.png)
*Figure 6 — Daily Clinic Reporting Engine — Comprehensive reporting module detailing patient demographics, diagnoses, and outpatient attendance summaries.*

---

## 3. Medical Officer (Doctor) Workstation

### Purpose
The **Doctor Consultation Workstation** provides clinicians with a clean, focused electronic medical record interface designed for rapid outpatient clinical decision-making.

### Core Responsibilities
- Review waiting patient lists and call patients sequentially into the consultation room.
- Review pre-recorded vital signs, derived BMI, and triage acuity flags recorded by the nurse.
- Document presenting symptoms, clinical observations, and physical examination findings.
- Enter formal clinical diagnoses aligned with medical standards.
- Prescribe electronic medications with precise dosage, frequency, and duration instructions.
- Order diagnostic laboratory investigations and initiate specialty hospital referrals.

### Screens Available
1. **Doctor Dashboard**: Summary of consultations completed today, waiting patients, and urgent alerts.
2. **Doctor Consultation Queue**: Prioritized list of triaged patients waiting for clinician examination.
3. **Clinical Consultation Form**: Integrated entry screen for clinical notes, diagnoses, and orders.
4. **Lab Results Review**: Diagnostic reports returned by the on-site lab technician.
5. **Referral Management**: Outgoing patient transfer documents for higher-tier specialty hospitals.

### Step-by-Step Workflow
1. The Doctor opens the **Doctor Queue** and clicks **Call Next Patient**. The highest-priority waiting patient is displayed.
2. The Doctor reviews the nurse’s triage findings—blood pressure, heart rate, temperature, SpO2, and nurse triage notes.
3. The Doctor interviews and examines the patient, recording clinical notes and selecting the confirmed or provisional diagnosis.
4. If testing is required, the Doctor checks the required diagnostic tests (e.g., Blood Sugar, Hemoglobin, Urine Routine), which automatically routes to the lab.
5. The Doctor selects medications from the clinic formulary, specifying instructions (e.g., *1 tablet twice daily after food for 5 days*).
6. Clicking **Complete Consultation** automatically updates the patient's record, dispatches the e-prescription to the dispensary, and calls the next patient.

### Representative Screenshots

![Figure 7 — Doctor Workstation Consultation Dashboard](../../scratch/ui_audit_screenshots/doctor/01_dashboard_doctor.png)
*Figure 7 — Doctor Workstation Consultation Dashboard — Clinician home screen showing waiting consultation queue, completed patient encounters, and urgent clinical flags.*

![Figure 8 — Clinical Examination & Diagnosis Form](../../scratch/ui_audit_screenshots/doctor/consultation_form_detailed.png)
*Figure 8 — Clinical Examination & Diagnosis Form — Consultation documentation screen displaying nurse triage vitals, clinical note inputs, and diagnostic ordering fields.*

![Figure 9 — Doctor Outpatient Queue View](../../scratch/ui_audit_screenshots/doctor/03_queue.png)
*Figure 9 — Doctor Outpatient Queue View — Prioritized waiting list displaying patient token numbers, triage acuity colors, and arrival times.*

---

## 4. Staff Nurse Workstation

### Purpose
The **Nurse Triage & Clinical Workstation** enables nurses to prioritize incoming walk-in patients through standardized vital sign measurements, acuity assessments, and community wellness tracking.

### Core Responsibilities
- Call waiting walk-in patients from reception into the nursing station.
- Measure and document vital signs: Systolic/Diastolic Blood Pressure, Pulse, Temperature, SpO2, Respiratory Rate, Height, and Weight.
- Review automated BMI calculations and evaluate vital abnormalities.
- Assign clinical acuity scores (`IMMEDIATE`, `VERY_URGENT`, `URGENT`, `STANDARD`, `NON_URGENT`).
- Screen citizens for chronic Non-Communicable Diseases (Hypertension and Diabetes).
- Coordinate patient follow-up recall lists and community health education sessions (Note: Dedicated Maternal/Child Health and immunization vertical programs are explicitly out of scope).

### Screens Available
1. **Nurse Dashboard**: Overview of waiting walk-ins, triage completion rates, and vitals alerts.
2. **Triage Queue**: Active waiting queue of registered patients awaiting nursing assessment.
3. **Vitals Recording Form**: Clean clinical interface for entering physiological measurements.
4. **NCD Registry**: Screening and tracking panel for chronic hypertensive and diabetic patients.
5. **Community Outreach & Wellness**: Logs for community health camp visits, hypertension screenings, and health education.

### Step-by-Step Workflow
1. The Nurse views the **Triage Queue** and calls the next patient token issued by reception.
2. The Nurse measures the patient’s vital signs and enters the numbers into the **Vitals Form**.
3. The platform computes the Body Mass Index automatically and highlights any abnormal values in amber or red.
4. The Nurse records presenting symptoms and assigns an acuity level based on clinical evaluation.
5. Upon saving, the patient's status transitions to `TRIAGED` and appears immediately in the Doctor’s consultation queue.

### Representative Screenshots

![Figure 10 — Staff Nurse Triage Dashboard](../../scratch/ui_audit_screenshots/nurse/01_dashboard_nurse.png)
*Figure 10 — Staff Nurse Triage Dashboard — Nursing home screen displaying walk-in intake numbers, pending vitals assessments, and chronic care alerts.*

![Figure 11 — Clinical Vitals Assessment Form](../../scratch/ui_audit_screenshots/nurse/triage_form_detailed.png)
*Figure 11 — Clinical Vitals Assessment Form — Standardized vitals capture form with automated BMI computation and clinical acuity prioritization.*

![Figure 12 — Non-Communicable Disease Screening Panel](../../scratch/ui_audit_screenshots/nurse/06_ncd.png)
*Figure 12 — Non-Communicable Disease Screening Panel — Chronic disease registry tracking blood pressure readings, glucose monitoring, and recall dates.*

---

## 5. Front Desk Officer Workstation

### Purpose
The **Front Desk Officer Workstation** handles the initial reception, demographic verification, new citizen onboarding, and sequential OPD token dispatch.

### Core Responsibilities
- Greet citizens arriving at the clinic reception desk.
- Search the Master Patient Index by mobile phone number, full name, or health ID.
- Register new citizens with contact details, residential address, and vulnerability group.
- Generate sequential daily OPD tokens (e.g., `T-001`, `T-002`) and assign patients to clinic departments.
- Void or cancel tokens issued in error before nursing triage commences.
- **Privacy Boundary**: Front Desk Officers cannot view clinical consultations, medical notes, diagnoses, or prescriptions.

### Screens Available
1. **Front Desk Console**: Reception overview with daily token statistics and rapid search.
2. **Patient Directory**: Master citizen demographic registry.
3. **New Patient Registration Modal**: Intake form for demographic and contact information.
4. **OPD Queue View**: Facility-wide token status monitor.

### Step-by-Step Workflow
1. The Front Desk Officer asks the patient for their mobile number or name and searches the registry.
2. If the patient exists, the officer verifies their address and clicks **Issue OPD Token**.
3. If the patient is new, the officer clicks **Register Patient**, enters their demographics, and clicks **Register & Issue Token**.
4. A daily sequential token is minted, and the patient is directed to the nursing triage waiting area.

### Representative Screenshots

![Figure 13 — Front Desk Reception Console](../../scratch/ui_audit_screenshots/compounder/01_dashboard_compounder.png)
*Figure 13 — Front Desk Reception Console — Intake workstation showing daily registration counts, search bar, and token queue statistics.*

![Figure 14 — Citizen Intake Registration Modal](../../scratch/ui_audit_screenshots/compounder/modal_01_registration_opened.png)
*Figure 14 — Citizen Intake Registration Modal — Clean registration dialog capturing demographic details, emergency contacts, and neighborhood vulnerability.*

![Figure 15 — Outpatient Token Queue Monitor](../../scratch/ui_audit_screenshots/compounder/03_queue.png)
*Figure 15 — Outpatient Token Queue Monitor — Active facility waiting queue displaying waiting tokens, patient identifiers, and priority designations.*

---

## 6. Diagnostic Lab Technician Workstation

### Purpose
The **Diagnostic Laboratory Workstation** enables laboratory technicians to manage test orders, track sample collection, input numeric test results, and publish verified diagnostic reports.

### Core Responsibilities
- Monitor incoming laboratory requisitions ordered by clinic doctors through electronic charts.
- Verify patient identity and record specimen collection (Blood, Urine, Sputum, etc.).
- Perform diagnostic investigations and enter numeric parameters.
- Verify results against standard biological reference ranges and publish verified reports.

### Screens Available
1. **Lab Dashboard**: Summary of pending test orders, samples collected, and reports completed today.
2. **Diagnostic Test Queue**: List of patients waiting for sample collection or test processing.
3. **Investigation Entry Screen**: Structured data form for entering diagnostic test parameters.

### Step-by-Step Workflow
1. When a doctor orders tests, the order appears immediately on the **Lab Queue**.
2. When the patient arrives at the lab, the technician clicks **Collect Specimen**, confirming sample receipt.
3. After completing the bench analysis, the technician opens the patient’s order and enters the numeric values.
4. The system validates the input against biological reference ranges and highlights abnormal results.
5. The technician clicks **Publish Report**, which securely updates the patient's record for physician review.

### Representative Screenshots

![Figure 16 — Diagnostic Laboratory Dashboard](../../scratch/ui_audit_screenshots/lab_technician/01_dashboard_lab.png)
*Figure 16 — Diagnostic Laboratory Dashboard — Lab home screen showing pending investigations, collected samples, and completed diagnostic reports.*

![Figure 17 — Diagnostic Investigation Test Queue](../../scratch/ui_audit_screenshots/lab_technician/03_lab.png)
*Figure 17 — Diagnostic Investigation Test Queue — Specimen intake list allowing technicians to verify samples and publish clinical parameters.*

---

## 7. Pharmacist Workstation

### Purpose
The **Pharmacy Workstation** allows pharmacists to review doctor prescriptions, select First-Expired, First-Out (FEFO) medicine batches, and dispense medications safely.

### Core Responsibilities
- Review electronic prescriptions issued by clinic doctors.
- Check medication availability, dosage forms, and prescribed durations.
- Verify system-recommended First-Expired, First-Out (FEFO) drug batches.
- Place invalid prescriptions on hold with clinical explanation notes.
- Dispense medications, record patient counseling, and automatically decrement facility pharmacy stock.

### Screens Available
1. **Pharmacy Dashboard**: Active prescription queue, dispensing metrics, and stock alerts.
2. **Dispensing Workstation**: Detailed prescription verification and batch selection screen.
3. **Pharmacy Drug Stock View**: Available medication inventory within the dispensary.
4. **Storage & Infrastructure**: Storage condition logs (e.g., refrigerator cold-chain monitoring).

### Step-by-Step Workflow
1. The Pharmacist views the **Pharmacy Dashboard** as new electronic prescriptions arrive.
2. The Pharmacist calls the patient token and opens the electronic prescription.
3. For each prescribed drug, the platform displays the prescribed quantity and automatically highlights the earliest-expiring active batch in stock.
4. The Pharmacist verifies the physical medicine against the screen and clicks **Dispense Prescription**.
5. The platform logs the dispensation, displays structured dispensing instructions, and decrements stock from the dispensary ledger.

### Representative Screenshots

![Figure 18 — Pharmacy Dispensing Dashboard](../../scratch/ui_audit_screenshots/pharmacist/01_dashboard_pharmacy.png)
*Figure 18 — Pharmacy Dispensing Dashboard — Pharmacist home screen tracking pending prescriptions, dispensed tokens, and low-stock warnings.*

![Figure 19 — Electronic Prescription Verification & Dispensing](../../scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png)
*Figure 19 — Electronic Prescription Verification & Dispensing — Prescription verification table showing doctor orders, recommended FEFO batches, and dispense controls.*

---

## 8. Inventory Officer Workstation

### Purpose
The **Inventory & Procurement Console** enables Inventory Officers to manage central clinic warehouse stock, raise vendor purchase orders, receive shipments with Goods Receipt Notes (GRN), and perform stock reconciliations.

### Core Responsibilities
- Monitor bulk warehouse stock balances and minimum reserve thresholds.
- Create formal Purchase Orders (PO) to approved pharmaceutical suppliers.
- Inspect incoming shipments and process Goods Receipt Notes with batch numbers and expiry dates.
- Perform physical inventory audits and log signed adjustments.
- **Separation of Duties**: Inventory Officers manage warehouse receiving; they cannot dispense medications directly to patients.

### Screens Available
1. **Inventory Workstation**: Bulk warehouse balances, batch listings, and expiry dates.
2. **Procurement & Purchase Orders**: Purchase order creation, approval status, and supplier records.
3. **Goods Receipt (GRN) Module**: Shipment intake dialog for verifying delivered quantities.
4. **Inventory Movement Ledger**: Authoritative chronological history of all stock additions and transfers.

### Step-by-Step Workflow
1. The Inventory Officer checks the **Inventory Workstation** to review items approaching reorder levels.
2. To order supplies, the officer opens **Purchase Orders**, selects the supplier, adds medicine items with requested quantities, and submits the order.
3. When the shipment arrives, the officer opens the PO and clicks **Create Goods Receipt Note (GRN)**.
4. The officer enters the manufacturer's batch numbers, manufacturing dates, expiry dates, and received quantities.
5. Saving the GRN automatically updates the warehouse stock ledger and makes the batches available for clinic dispensing.

### Representative Screenshots

![Figure 20 — Inventory Workstation & Batch Ledger](../../scratch/ui_audit_screenshots/inventory/01_inventory.png)
*Figure 20 — Inventory Workstation & Batch Ledger — Facility warehouse stock ledger displaying batch quantities, expiry dates, and unit prices.*

![Figure 21 — Procurement Purchase Orders Tab](../../scratch/ui_audit_screenshots/inventory/inventory_01_po_tab.png)
*Figure 21 — Procurement Purchase Orders Tab — Procurement dashboard showing active vendor purchase orders, delivery statuses, and creation modal controls.*

![Figure 22 — Purchase Order Generation Modal](../../scratch/ui_audit_screenshots/inventory/inventory_02_po_modal.png)
*Figure 22 — Purchase Order Generation Modal — Supplier order creation dialog specifying ordered drug quantities, unit costs, and delivery terms.*

---

# PART C — DUAL-ROLE OPERATIONS (SMALL-CLINIC RULE)

Primary healthcare facilities across urban and rural sectors often operate with lean personnel. A neighborhood clinic or health outpost may have only one nurse or one pharmacist on duty during a shift.

Rather than compromising administrative controls by creating informal or combined roles (which introduce severe security and auditing risks), the Namma Clinic Platform supports the **Small-Clinic Rule**: an administrator can grant **two distinct, standard operational roles** to a single verified staff member. The employee carries out each duty under its dedicated operational rules, distinct screens, and audit tracking.

---

## 1. Nurse + Front Desk Officer Dual Role

In a neighborhood clinic without a dedicated reception clerk, the Staff Nurse holds two distinct role assignments: `NURSE` and `FRONT_DESK_OFFICER`.

| Operational Phase | Active Role & Station | Role-Governed Workflow Steps |
| :--- | :--- | :--- |
| **Phase 1: Reception Intake** | **Front Desk Officer**<br>*(Reception Console)* | &bull; Nurse switches active role context to Front Desk Officer.<br>&bull; Searches citizen registry by phone, name, or UHID to prevent duplicate records.<br>&bull; Enters new walk-in demographic details or verifies returning patient profile.<br>&bull; Issues daily sequential OPD queue token (e.g., `T-101`) routed to General OPD. |
| **Phase 2: Clinical Triage** | **Staff Nurse**<br>*(Triage Station)* | &bull; Nurse switches active role context back to Staff Nurse.<br>&bull; Calls token `T-101` from the waiting queue into the triage workstation.<br>&bull; Records physiological vitals (BP, Pulse, Temperature, SpO2, Respiratory Rate).<br>&bull; System calculates BMI; nurse records triage acuity and hands off to Doctor queue. |

### Operational Separation of Responsibilities
* **Strict Privacy Boundaries**: When greeting citizens and issuing tokens at reception, the nurse uses front-desk screens and cannot see confidential clinical consultation notes or diagnostic history of past visits. This prevents accidental exposure of sensitive diagnoses in the public reception area.
* **Clinical Triage Integrity**: When measuring physiological vitals and assessing acute symptoms, the nurse switches to the clinical workstation. The vital signs immediately appear on the Doctor's queue with color-coded acuity flags.
* **Audit Trail Accountability**: Every token generated is logged under the `FRONT_DESK_OFFICER` role permission, while every blood pressure reading is logged under the `NURSE` role permission.
* **Flexible Clinic Scaling**: When patient volume increases and a dedicated front desk officer is hired, the administrator simply revokes the `FRONT_DESK_OFFICER` assignment from the nurse's profile. The nurse immediately returns to standard single-role nursing without data loss or administrative disruption.

![Step 1: Reception Intake via Front Desk Duty](../../scratch/ui_audit_screenshots/compounder/01_dashboard_compounder.png)
*Figure 23 — Step 1: Reception Intake via Front Desk Duty — The nurse accesses the reception console to look up walk-in citizens, verify demographic profiles, and issue sequential OPD tokens.*

![Step 2: Clinical Vitals Triage via Nurse Duty](../../scratch/ui_audit_screenshots/nurse/01_dashboard_nurse.png)
*Figure 24 — Step 2: Clinical Vitals Triage via Nurse Duty — Switching to the nursing console, the nurse calls the token into the triage station to document vital signs, compute BMI, and assign priority flags.*

---

## 2. Pharmacist + Inventory Officer Dual Role

In clinics where a single pharmacy professional manages both the warehouse drug stockroom and the outpatient dispensing counter, the employee holds both `PHARMACIST` and `INVENTORY` role assignments.

| Operational Domain | Active Role & Station | Workflow Responsibilities & Governance Rules |
| :--- | :--- | :--- |
| **Warehouse Procurement & Receipt** | **Inventory Officer**<br>*(Store Room)* | &bull; Creates and manages Purchase Orders (PO) for pharmaceutical vendors.<br>&bull; Inspects physical supplier deliveries against authorized purchase orders.<br>&bull; Receives items via Goods Receipt Note (GRN), logging batch numbers, expiry dates, and unit costs into the central InventoryLedger. |
| **Dispensary & Patient Dispensing** | **Pharmacist**<br>*(Pharmacy Counter)* | &bull; Accesses doctor e-prescriptions for queued consultation visits.<br>&bull; Verifies prescribed dosages, durations, and potential interactions.<br>&bull; System allocates stock strictly using First-Expired, First-Out (FEFO) batches.<br>&bull; Confirms dispensing, automatically writing decrement transactions to the InventoryLedger. |

### Operational Separation of Responsibilities
* **Inventory Intake Before Dispensing**: The professional cannot dispense medicines directly out of shipping boxes. When a shipment arrives from the district warehouse, they must log into the Inventory workstation and record a verified Goods Receipt Note (GRN) capturing batch numbers, expiry dates, and unit quantities.
* **Automated FEFO Enforcement**: When dispensing at the pharmacy counter, the system automatically allocates the earliest-expiring active batch first, preventing older stock from expiring unnoticed on back shelves.
* **Strict Double-Entry Accountability**: Dispensing deductions cannot be fabricated; every medicine issued must be tied to a valid Doctor consultation and electronic prescription.
* **Clean Responsibility Handoff**: If the facility expands and hires a dedicated Inventory Officer, the administrator reassigns the `INVENTORY` role to the new hire. The pharmacist retains dispensing responsibilities with zero operational downtime.

![Step 1: Warehouse Stock Management via Inventory Duty](../../scratch/ui_audit_screenshots/dual_role/inventory_01_po_tab.png)
*Figure 25 — Step 1: Warehouse Stock Management via Inventory Duty — The dual-role officer monitors clinic stock levels, creates purchase orders, and logs verified Goods Receipt Notes into the store ledger.*

![Step 2: Outpatient Prescription Dispensing via Pharmacist Duty](../../scratch/ui_audit_screenshots/dual_role/01_dashboard_pharmacy.png)
*Figure 26 — Step 2: Outpatient Prescription Dispensing via Pharmacist Duty — Switching to the dispensary view, the officer validates doctor e-prescriptions, confirms FEFO batch allocations, and dispenses medications.*

---

# PART D — COMPLETE PATIENT JOURNEY

Every patient visit follows a standardized, chronological clinical lifecycle. This section traces a citizen through all seven operational stages, detailing who acts, what data is recorded, and what happens next.

| Stage | Operational Role | Care Setting | Workflow Steps & Clinical Outputs |
| :---: | :--- | :--- | :--- |
| **1** | **Front Desk Officer** | Reception Desk | Citizen arrival, demographic search, duplicate prevention, and UHID assignment. |
| **2** | **Front Desk Officer** | Reception Queue | Sequential OPD token generated, patient routed to nurse triage waiting queue. |
| **3** | **Staff Nurse** | Triage Station | Vitals measurement (BP, pulse, temp, SpO2, BMI), triage acuity classification. |
| **4** | **Medical Officer** | Consultation Room | Clinical examination, chief complaints, ICD-10 diagnosis, Rx & lab orders. |
| **5** | **Lab Technician** | Laboratory Station | Specimen collection, diagnostic test execution, result entry & validation. |
| **6** | **Pharmacist** | Pharmacy Counter | e-Prescription validation, FEFO batch allocation, medicine dispensing & counseling. |
| **7** | **System & Care Team** | Longitudinal EHR | Visit record sealed, inventory ledger updated, patient recall scheduled. |

### Stage-by-Stage Operational Walkthrough

#### Stage 1: Patient Arrival & Demographic Search
* **Who Performs It**: Front Desk Officer (or Staff Nurse under dual-role rule).
* **What They Do**: Greets citizen, searches phone number or name in the central patient registry. If new, opens the registration modal and captures primary demographics (Name, Age, Gender, Mobile, Address, Emergency Contact).
* **Information Captured**: National health identifier, full name, age, biological sex, phone number, residential neighborhood, and guardian details.
* **What Happens Next**: The patient's permanent record is saved and opened for outpatient token creation.
* **What the Next User Sees**: The triage nurse sees the patient appear on the incoming triage waiting list.
* **Why it Matters**: Eliminates duplicate medical charts, establishes verifiable citizen identity, and protects clinical privacy by restricting front desk staff from viewing past medical notes.
* **Management Monitoring**: Tracks total daily walk-in registrations, demographic completeness rates, and peak arrival hours.

![Figure 27 — Citizen Demographic Registration Screen](../../scratch/ui_audit_screenshots/compounder/modal_01_registration_opened.png)
*Figure 27 — Citizen Demographic Registration Screen — Front desk interface capturing essential citizen demographic details (name, age, gender, mobile, address) to establish a permanent clinic record without exposing medical history.*

#### Stage 2: Token Issuance & Queue Placement
* **Who Performs It**: Front Desk Officer.
* **What They Do**: Generates a daily sequential outpatient (OPD) token (e.g., Token #T-104) and directs the patient to the nursing triage waiting area.
* **Information Captured**: Visit timestamp, assigned doctor clinic room, visit category (General OPD, Chronic Care, Acute Minor Illness).
* **What Happens Next**: The token enters the active facility outpatient queue.
* **What the Next User Sees**: The triage nurse workstation displays the token in bold with an elapsed wait timer.
* **Why it Matters**: Establishes transparent, orderly patient movement, eliminates hallway congestion, and creates an audit-ready timeline of patient wait durations.
* **Management Monitoring**: Monitors average check-in speed and total queue volume across morning and evening sessions.

![Figure 28 — Facility OPD Token Queue View](../../scratch/ui_audit_screenshots/compounder/03_queue.png)
*Figure 28 — Facility OPD Token Queue View — Active facility queue displaying sequential tokens, tracking citizen progression through registration, triage, consultation, laboratory testing, and pharmacy dispensing.*

#### Stage 3: Nurse Triage & Vital Signs Measurement
* **Who Performs It**: Staff Nurse.
* **What They Do**: Calls the patient into the triage room, conducts standardized physiological measurements, enters vital signs, and assesses clinical urgency.
* **Information Captured**: Systolic and diastolic Blood Pressure (mmHg), Pulse Rate (bpm), Body Temperature (°F), Respiratory Rate, Oxygen Saturation (SpO2 %), Height, Weight, and calculated Body Mass Index (BMI). Urgency classification (Green = Routine, Amber = Urgent, Red = Emergency).
* **What Happens Next**: The system automatically computes BMI and flags out-of-range values. The patient moves to the Doctor's consultation waiting queue.
* **What the Next User Sees**: The Doctor sees the token immediately on their queue, highlighted with the nurse's acuity color badge and vital signs summary.
* **Why it Matters**: Ensures unstable patients (e.g., severe hypertension, high fever, hypoxia) are immediately prioritized rather than waiting behind routine mild cases.
* **Management Monitoring**: Reviews vital signs capture compliance rates and identifies triage acuity distributions across clinics.

![Figure 29 — Nurse Triage Vitals Documentation Screen](../../scratch/ui_audit_screenshots/nurse/04_triage.png)
*Figure 29 — Nurse Triage Vitals Documentation Screen — Standardized nursing triage form recording blood pressure, pulse, temperature, SpO2, and BMI, with automated clinical acuity color flags.*

#### Stage 4: Doctor Consultation & Clinical Diagnosis
* **Who Performs It**: Medical Officer (Doctor).
* **What They Do**: Calls the patient into the consultation room, reviews nurse-entered vitals, records symptoms and clinical history, conducts physical examination, enters formal diagnoses, orders diagnostic lab tests, and creates electronic prescriptions.
* **Information Captured**: Chief complaints, duration of illness, clinical examination findings, standardized diagnosis codes, lab investigation requisitions, prescribed medications (drug name, strength, dosage form, frequency, duration, food relation, and quantity), and follow-up revisit dates.
* **What Happens Next**: Lab orders are queued for the diagnostic laboratory. Prescriptions become available in the pharmacy dispensing queue.
* **What the Next User Sees**: The Lab Technician sees ordered tests in their pending queue; the Pharmacist sees the electronic prescription waiting for dispensing.
* **Why it Matters**: Completely replaces illegible paper slips, enforces standardized clinical diagnostic terminology, and automatically prevents drug dosage and frequency misunderstandings.
* **Management Monitoring**: Evaluates doctor consultation throughput, diagnosis prevalence patterns, and antibiotic prescribing compliance.

![Figure 30 — Medical Officer Consultation Screen](../../scratch/ui_audit_screenshots/doctor/04_consultation.png)
*Figure 30 — Medical Officer Consultation Screen — Integrated clinician screen combining chief complaints, past visits, physical examination, standardized diagnoses, and electronic prescription generation.*

#### Stage 5: Diagnostic Laboratory Processing
* **Who Performs It**: Diagnostic Lab Technician.
* **What They Do**: Collects biological specimens (blood, urine, sputum), verifies specimen labeling against patient token, executes diagnostic tests, and enters quantitative results.
* **Information Captured**: Specimen collection timestamp, test result values (e.g., Random Blood Sugar: 178 mg/dL, Urine Albumin: 1+), reference range comparisons, abnormal value alerts, and technician sign-off.
* **What Happens Next**: Results are saved and reflected in the Doctor's consultation chart. The patient returns to the doctor or proceeds to pharmacy.
* **What the Next User Sees**: The Doctor receives a notification that lab results are ready for clinical interpretation and final prescription adjustment.
* **Why it Matters**: Eliminates lost paper lab slips, provides rapid turnaround for point-of-care testing, and flags critical values immediately.
* **Management Monitoring**: Tracks lab test turnaround times, test volume by category, and reagent consumption patterns.

![Figure 31 — Diagnostic Test Order & Specimen Intake Screen](../../scratch/ui_audit_screenshots/lab_technician/03_lab.png)
*Figure 31 — Diagnostic Test Order & Specimen Intake Screen — Laboratory interface for specimen intake, test execution, quantitative result recording, and electronic chart updates.*

#### Stage 6: Prescription Verification & FEFO Dispensing
* **Who Performs It**: Pharmacist (or Pharmacist/Inventory Officer under dual-role rule).
* **What They Do**: Reviews doctor electronic prescription on the pharmacy workstation, verifies dosage and directions, inspects system-recommended earliest-expiring active batches, issues medicines, and provides counseling to the patient.
* **Information Captured**: Dispensed batch numbers, expiration dates, unit quantities issued, pharmacist verification timestamp, and counseling confirmation.
* **What Happens Next**: The inventory ledger immediately deducts dispensed quantities from the facility stock balance. The prescription status changes to 'Dispensed'.
* **What the Next User Sees**: The Doctor and Administrator see the prescription marked completed in the longitudinal visit timeline.
* **Why it Matters**: Prevents expired drugs from reaching patients, automates stock deduction, eliminates manual ledger posting, and ensures patients receive accurate dosage instructions.
* **Management Monitoring**: Monitors stock turnover, expired drug avoidance rates, and daily pharmaceutical dispensing counts.

![Figure 32 — Pharmacy Prescription Verification & Dispensing Screen](../../scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png)
*Figure 32 — Pharmacy Prescription Verification & Dispensing Screen — Pharmacist validation screen displaying doctor electronic prescriptions, system-recommended FEFO batches, and medicine counseling notes.*

#### Stage 7: Visit Completion & Longitudinal Record
* **Who Performs It**: System-wide automated consolidation.
* **What They Do**: Consolidates registration demographics, nursing vitals, doctor notes, lab findings, and dispensed drugs into a permanent, longitudinal electronic health timeline.
* **Information Captured**: Total visit duration, complete clinical care summary, and scheduled follow-up reminders.
* **What Happens Next**: If a follow-up revisit is scheduled, the patient is entered into the nurse's chronic care recall register.
* **What the Next User Sees**: At the patient's next visit (even months later), any clinician across the clinic immediately views the complete chronological history.
* **Why it Matters**: Ensures continuous, coordinated healthcare rather than fragmented single encounters. Enables long-term chronic disease management.
* **Management Monitoring**: Computes facility overall turnaround time, patient satisfaction indicators, and clinic completion rates.

---

# PART E — CLINIC OPERATIONS REFERENCE (21 PLATFORM CAPABILITIES)

This section provides a structured operational reference for all twenty-one platform capabilities supporting primary healthcare workflows. Capabilities are classified into **Implemented & Verified Core Modules** (Items 1–10), **Demonstration & Extension Modules** (Items 11–18), and **Cross-Cutting Platform Services** (Items 19–21).

| Capability Category | Count | Module Scope & Capabilities | Operational Implementation Status |
| :--- | :---: | :--- | :--- |
| **Implemented & Verified Core** | 10 | 1. Demographic Registry<br>2. OPD Tokens & Queue Management<br>3. Clinical Triage & Physiological Vitals<br>4. Doctor Clinical Consultation & Diagnoses<br>5. Diagnostic Laboratory Workflow<br>6. Pharmacy Dispensing & FEFO Allocation<br>7. Warehouse Inventory & Stock Levels<br>8. Procurement & Purchase Orders (PO)<br>9. Goods Receipt Notes (GRN)<br>10. Staff Administration & Multi-Role Governance | **Production Ready & Verified**<br>Full Browser &rarr; API &rarr; PostgreSQL verification. Backed by automated regression tests and audit logging. |
| **Demonstration & Extension Modules** | 8 | 11. Specialist Referrals<br>12. Patient Follow-up & Recalls<br>13. NCD Chronic Disease Registry<br>14. Syndromic Public Disease Surveillance<br>15. Community Outreach Camp Activity Logs<br>16. Health Wellness & Education Sessions<br>17. Quality & Accreditation Indicators<br>18. Facility Infrastructure & Maintenance | **Demonstration Mode**<br>Functional UI prototypes and database schemas designed for future state expansion. Operates with mock/empty baselines. |
| **Cross-Cutting Platform Services** | 3 | 19. Operational Reporting Engine<br>20. Clinical & Supply Alerts Hub<br>21. Security, RBAC & Audit Logging | **Platform Foundational**<br>Reporting Engine (Implemented), Alerts Hub (Demonstration), Security & Audit Logging (Implemented). |

---

### 1. Patient Demographic Registry
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Maintains the single authoritative record of all registered citizens.
* **Primary Users**: Front Desk Officer, Staff Nurse, Doctor, Administrator.
* **Workflow**: Search by mobile/name → Review demographic summary → Update address/contact if changed.
* **Outcome**: Accurate patient demographic records without duplicate files.
* **Client Value**: Faster check-in times and complete demographic visibility across clinic departments.

![Figure 33 — Patient Demographic Registry Screen](../../scratch/ui_audit_screenshots/compounder/02_patients.png)
*Figure 33 — Patient Demographic Registry Screen — Searchable central directory of registered citizens providing contact verification, demographic updates, and duplicate record prevention across clinic visits.*

---

### 2. OPD Token & Queue Module
* **Purpose**: Coordinates fair, sequential patient movement between clinic departments.
* **Primary Users**: Front Desk Officer, Nurse, Doctor, Pharmacist.
* **Workflow**: Token issued at reception → Displayed on waiting queue → Called into service rooms sequentially.
* **Classification**: Implemented & Verified Core Module
* **Outcome**: Orderly patient flow with transparent queue visibility.
* **Client Value**: Eliminates waiting room disputes and provides transparent clinic wait times.

![Figure 34 — OPD Token & Waiting Queue Console](../../scratch/ui_audit_screenshots/compounder/03_queue.png)
*Figure 34 — OPD Token & Waiting Queue Console — Facility waiting monitor organizing citizen flow sequentially across triage, consultation, diagnostic sampling, and pharmacy dispensing.*

---

### 3. Clinical Triage Module
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Gathers physiological baseline measurements and identifies urgent walk-in cases.
* **Primary Users**: Staff Nurse.
* **Workflow**: Call token → Measure vitals → Calculate BMI → Assign acuity score → Route to Doctor.
* **Outcome**: Standardized vitals documentation and rapid prioritization of critical patients.
* **Client Value**: Protects patient safety by preventing critical emergencies from waiting unnoticed in general queues.

![Figure 35 — Clinical Vitals Assessment Form](../../scratch/ui_audit_screenshots/nurse/triage_form_detailed.png)
*Figure 35 — Clinical Vitals Assessment Form — Nursing documentation tool capturing physiological baselines, calculating BMI, and triggering emergency priority flags for the doctor consultation queue.*

---

### 4. Doctor Consultation Module
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Records clinical encounters, physical examinations, diagnoses, and medical orders.
* **Primary Users**: Medical Officer (Doctor).
* **Workflow**: Review vitals → Record history & examination → Select diagnosis → Order labs & prescribe drugs.
* **Outcome**: Standardized, legible clinical consultation record with digital orders.
* **Client Value**: Improves diagnostic consistency, eliminates handwriting errors, and structures clinical data.

![Figure 36 — Doctor Clinical Examination & Prescribing Interface](../../scratch/ui_audit_screenshots/doctor/consultation_form_detailed.png)
*Figure 36 — Doctor Clinical Examination & Prescribing Interface — Comprehensive consultation workspace recording symptoms, physical findings, ICD-standardized diagnoses, lab orders, and digital prescriptions.*

---

### 5. Laboratory Module
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Processes diagnostic investigation orders and logs quantitative test results.
* **Primary Users**: Diagnostic Lab Technician.
* **Workflow**: Receive order → Collect specimen → Perform test → Enter quantitative findings → Notify doctor.
* **Outcome**: Timely diagnostic results linked directly to the patient's visit.
* **Client Value**: Faster diagnosis confirmation and complete traceability of test requisitions.

![Figure 37 — Diagnostic Laboratory Queue & Results Entry Screen](../../scratch/ui_audit_screenshots/lab_technician/03_lab.png)
*Figure 37 — Diagnostic Laboratory Queue & Results Entry Screen — Specimen intake list enabling rapid result documentation, automatic abnormal range flagging, and electronic results delivery to the treating physician.*

---

### 6. Pharmacy Dispensing Module
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Dispenses prescribed medicines safely using First-Expired, First-Out (FEFO) allocation.
* **Primary Users**: Pharmacist.
* **Workflow**: Review doctor prescription → Confirm FEFO batch allocations → Dispense stock → Counsel patient.
* **Outcome**: Accurate drug fulfillment with automated inventory decrement.
* **Client Value**: Minimizes dispensing ambiguity, guides FEFO batch selection, and maintains complete dispensing records.

![Figure 38 — Pharmacy Outpatient Dispensing Workstation](../../scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png)
*Figure 38 — Pharmacy Outpatient Dispensing Workstation — Dispensing interface matching electronic doctor prescriptions against warehouse inventory with automated First-Expired, First-Out (FEFO) batch allocation.*

---

### 7. Warehouse Inventory Module
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Maintains authoritative facility stock ledgers, batch numbers, and reorder levels.
* **Primary Users**: Inventory Officer, Pharmacist.
* **Workflow**: Monitor balances → Inspect reorder warnings → Audit physical counts against system balances.
* **Outcome**: Accurate stock levels with complete batch-level traceability.
* **Client Value**: Prevents unexpected stockouts of vital life-saving drugs and eliminates expired medicine waste.

![Figure 39 — Clinic Warehouse Stock Ledger](../../scratch/ui_audit_screenshots/inventory/01_inventory.png)
*Figure 39 — Clinic Warehouse Stock Ledger — Comprehensive facility store ledger displaying active stock on hand, reorder thresholds, supplier batch tracking, and automated expiration warnings.*

---

### 8. Procurement & Purchase Orders
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Generates and tracks supplier purchase orders for medicines and clinical consumables.
* **Primary Users**: Inventory Officer, Administrator.
* **Workflow**: Review depleted stock → Generate PO with quantities and approved suppliers → Track vendor delivery.
* **Outcome**: Structured procurement cycle with vendor delivery tracking.
* **Client Value**: Transparent procurement timelines and orderly replenishment cycles.

![Figure 40 — Procurement Requisition & Purchase Order Tracker](../../scratch/ui_audit_screenshots/inventory/inventory_01_po_tab.png)
*Figure 40 — Procurement Requisition & Purchase Order Tracker — Supplier purchasing console tracking stock replenishments, order quantities, delivery commitments, and vendor fulfillment status.*

---

### 9. Goods Receipt Notes (GRN) Module
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Formally receives incoming vendor shipments and logs batches into clinic inventory.
* **Primary Users**: Inventory Officer.
* **Workflow**: Inspect delivery package → Verify batch numbers, quantities & expiry dates → Issue GRN receipt.
* **Outcome**: Incoming stock immediately active in inventory with verified expiry dates.
* **Client Value**: Eliminates inventory shrinkage upon receipt and ensures uninspected stock is never dispensed.

![Figure 41 — Goods Receipt Note (GRN) Inward Verification Modal](../../scratch/ui_audit_screenshots/inventory/inventory_02_po_modal.png)
*Figure 41 — Goods Receipt Note (GRN) Inward Verification Modal — Formal delivery receipt workflow capturing manufacturer batch identifiers, expiration dates, unit counts, and physical quality verification.*

---

### 10. Staff Administration Module
* **Classification**: Implemented & Verified Core Module
* **Purpose**: Manages healthcare personnel accounts, role allocations, dual-role configuration, and facility scoping.
* **Primary Users**: Clinic Administrator, District Health Officer.
* **Workflow**: Create staff profile → Assign standard operational roles → Enable/disable accounts.
* **Outcome**: Verified staff role assignments governed by administrative security.
* **Client Value**: Strict operational governance and audit-compliant workforce management.

![Figure 42 — Facility Staff Management & Role Allocation](../../scratch/ui_audit_screenshots/admin/03_admin_staff.png)
*Figure 42 — Facility Staff Management & Role Allocation — Personnel governance screen allowing administrators to configure user profiles, grant verified operational roles, and enforce facility access scoping.*

---

### 11. Referrals Management Module
* **Classification**: Demonstration & Extension Module
* **Purpose**: Coordinates outbound patient transfers to secondary and tertiary hospitals (Prototype workflow; operates in demonstration mode).
* **Primary Users**: Medical Officer, Clinic Administrator.
* **Workflow**: Initiate referral with clinical summary → Select target hospital → Monitor transfer progress.
* **Outcome**: Structured referral documentation with clear clinical reason for transfer.
* **Client Value**: Prevents patients from getting lost in the broader hospital network and provides clinical continuity.

![Figure 43 — Outbound Referral Coordination Console](../../scratch/ui_audit_screenshots/admin/08_referrals.png)
*Figure 43 — Outbound Referral Coordination Console — Referral management dashboard facilitating patient transfers to secondary hospitals and tracking tertiary care follow-up outcomes.*

---

### 12. Patient Follow-ups Module
* **Classification**: Demonstration & Extension Module
* **Purpose**: Manages scheduled recall dates for chronic disease patients and post-acute reviews (Prototype workflow; operates in demonstration mode).
* **Primary Users**: Staff Nurse, Medical Officer.
* **Workflow**: View daily due list → Contact patients due for review → Mark completed upon arrival.
* **Outcome**: Timely follow-up care for chronic hypertension, diabetes, and post-acute patients.
* **Client Value**: Drastically improves chronic disease control rates and reduces hospital readmissions.

![Figure 44 — Patient Follow-up & Recall Workstation](../../scratch/ui_audit_screenshots/nurse/05_followups.png)
*Figure 44 — Patient Follow-up & Recall Workstation — Longitudinal care calendar tracking scheduled revisit dates for hypertensive, diabetic, and post-acute review patients.*

---

### 13. Non-Communicable Diseases (NCD) Registry
* **Classification**: Demonstration & Extension Module
* **Purpose**: Tracks long-term management of hypertensive, diabetic, and chronic care cohorts (Prototype workflow; operates in demonstration mode).
* **Primary Users**: Staff Nurse, Medical Officer.
* **Workflow**: Identify chronic indicators → Enroll patient in NCD registry → Track BP and glucose trends over time.
* **Outcome**: Structured chronic disease management with historical control indicators.
* **Client Value**: Enables population-level management of common chronic conditions.

![Figure 45 — Non-Communicable Disease (NCD) Registry Screen](../../scratch/ui_audit_screenshots/nurse/06_ncd.png)
*Figure 45 — Non-Communicable Disease (NCD) Registry Screen — Chronic patient monitoring registry tracking community screening results, blood pressure trends, and glycemic management over time.*

---

### 14. Public Health Surveillance Module
* **Classification**: Demonstration & Extension Module
* **Purpose**: Monitors disease trends, fever spikes, and communicable outbreak signals (Prototype workflow; operates in demonstration mode without external WAN clustering).
* **Primary Users**: District Health Officer, Administrator.
* **Workflow**: Diagnostic codes aggregate into surveillance categories → System models disease pattern clusters → Health officers evaluate response workflows.
* **Outcome**: Outbreak trend modeling across reporting clinic categories.
* **Client Value**: Proactive public health evaluation and demonstration of surveillance response.

![Figure 46 — Public Health Epidemiological Surveillance Console](../../scratch/ui_audit_screenshots/dho/10_surveillance.png)
*Figure 46 — Public Health Epidemiological Surveillance Console — Automated syndromic surveillance map tracking acute fever, diarrheal illness, and vector-borne clusters across the health network.*

---

### 15. Community Outreach Module
* **Classification**: Demonstration & Extension Module
* **Purpose**: Plans and documents health screening camps in community halls, schools, and workplaces (Prototype workflow; operates in demonstration mode).
* **Primary Users**: Staff Nurse, Medical Officer.
* **Workflow**: Schedule camp → Record citizen screenings on-site → Flag identified cases for clinic follow-up.
* **Outcome**: Documented community screening sessions with clear patient follow-up pathways.
* **Client Value**: Extends healthcare access directly into underserved neighborhood communities.

![Figure 47 — Community Health Outreach Camp Documentation Screen](../../scratch/ui_audit_screenshots/nurse/07_outreach.png)
*Figure 47 — Community Health Outreach Camp Documentation Screen — Mobile camp tracking interface recording field screening dates, target demographics, and primary health outreach services delivered.*

---

### 16. Wellness & Health Education Module
* **Classification**: Demonstration & Extension Module
* **Purpose**: Logs lifestyle interventions, preventive counseling, yoga, and dietary education (Prototype workflow; operates in demonstration mode).
* **Primary Users**: Staff Nurse, Medical Officer.
* **Workflow**: Record patient counseling session → Document lifestyle guidance provided → Track follow-up adherence.
* **Outcome**: Documented preventive health interventions integrated into medical history.
* **Client Value**: Promotes wellness-first healthcare delivery and proactive illness prevention.

![Figure 48 — Preventive Wellness & Health Counseling Screen](../../scratch/ui_audit_screenshots/nurse/08_wellness.png)
*Figure 48 — Preventive Wellness & Health Counseling Screen — Patient education dashboard documenting lifestyle counseling sessions, smoking cessation support, and dietary guidance delivered.*

---

### 17. Quality Indicators & Facility KPIs
* **Classification**: Demonstration & Extension Module
* **Purpose**: Monitors clinical service benchmarks, waiting times, and patient throughput standards (Prototype workflow; operates in demonstration mode).
* **Primary Users**: Clinic Administrator, District Health Officer.
* **Workflow**: Track operational KPIs → Identify bottlenecks in triage or pharmacy → Implement operational improvements.
* **Outcome**: Objective quality metrics comparing facility performance over time.
* **Client Value**: Continuous healthcare delivery improvement and accountability to service charters.

![Figure 49 — Clinic Quality Indicators & Performance Dashboard](../../scratch/ui_audit_screenshots/admin/12_quality.png)
*Figure 49 — Clinic Quality Indicators & Performance Dashboard — Facility quality tracking screen showing average consultation durations, patient wait times, prescription completion rates, and service KPIs.*

---

### 18. Clinic Infrastructure & Storage Module
* **Classification**: Demonstration & Extension Module
* **Purpose**: Tracks facility equipment, storage temperatures, and backup power (Facility directory active; maintenance logging is a prototype workflow).
* **Primary Users**: Clinic Administrator, Inventory Officer.
* **Workflow**: Log daily temperature checks → Record routine equipment servicing → Flag maintenance needs.
* **Outcome**: Documented storage checks and operational clinical asset tracking.
* **Client Value**: Supports facility asset readiness and daily maintenance oversight.

![Figure 50 — Infrastructure & Cold-Chain Storage Monitoring](../../scratch/ui_audit_screenshots/admin/10_infrastructure.png)
*Figure 50 — Infrastructure & Cold-Chain Storage Monitoring — Facility asset registry tracking cold-chain vaccine refrigerators, diagnostic analyzers, backup power, and routine maintenance logs.*

---

### 19. Operational Reporting Engine
* **Classification**: Cross-Cutting Platform Service (Implemented)
* **Purpose**: Generates daily attendance registers, pharmacy consumption reports, and disease summaries.
* **Primary Users**: Clinic Administrator, District Health Officer.
* **Workflow**: Select reporting period → Filter by department or service → Generate and export verified operational reports.
* **Outcome**: Standardized administrative summaries without manual register counting.
* **Client Value**: Saves dozens of staff hours per week and eliminates manual reporting discrepancies.

![Figure 51 — Operational & Administrative Reporting Engine](../../scratch/ui_audit_screenshots/admin/13_reports.png)
*Figure 51 — Operational & Administrative Reporting Engine — Standardized analytics suite generating daily patient attendance tallies, pharmacy stock turnover, and disease incidence reports.*

---

### 20. Alerts & Early Warning Hub
* **Classification**: Cross-Cutting Platform Service (Demonstration)
* **Purpose**: Delivers visual dashboard notifications for critical lab findings, vital signs alerts, and stockout warnings.
* **Primary Users**: All Staff Roles.
* **Workflow**: Visual threshold met → Notification banner displays on responsible workstation → User reviews and acts.
* **Outcome**: Enhanced awareness of urgent operational and clinical indicator thresholds.
* **Client Value**: Timely awareness of patient priorities and early visibility of low inventory levels.

![Figure 52 — Operational Alerts & Notifications Hub](../../scratch/ui_audit_screenshots/admin/15_alerts.png)
*Figure 52 — Operational Alerts & Notifications Hub — Centralized alerting console displaying notifications for critical lab results, urgent triage scores, and low drug inventory thresholds.*

---

### 21. Security & Audit Logging
* **Classification**: Cross-Cutting Platform Service (Implemented)
* **Purpose**: Maintains a structured chronological audit trail of all logins, record views, and transactions.
* **Primary Users**: District Health Officer, System Administrator.
* **Workflow**: User performs action → Event is recorded with timestamp and role → Auditor reviews logs.
* **Outcome**: Complete, unalterable accountability for every record accessed or modified.
* **Client Value**: Supports regulatory audit readiness and ensures clear administrative accountability.

![Figure 53 — Security Audit Trail Console](../../scratch/ui_audit_screenshots/dho/16_audit.png)
*Figure 53 — Security Audit Trail Console — Structured digital event log documenting user authentication, role assumption, clinical records access, and administrative actions.*

---

# PART F — MANAGEMENT & DHO EXECUTIVE VIEW

Health Department Leadership and District Health Officers need clear, actionable visibility into healthcare delivery across their network. Namma Clinic translates frontline clinic data into executive intelligence.

| Executive Monitoring Dimension | Key Operational Metrics | Leadership Value & Actionable Insight |
| :--- | :--- | :--- |
| **Patient Services & Flow** | Daily OPD volume, average wait times, triage acuity ratios, token cancellation rates. | Identifies peak clinic congestion hours and patient throughput bottlenecks. |
| **Clinical Workload** | Consultations per doctor, diagnostic test volume, antibiotic prescription rates. | Evaluates physician workload distribution and rational antibiotic prescribing compliance. |
| **Medicine Supply & Pharmacy** | Warehouse stock balances, near-expiry batch counts, stockout warnings. | Guides procurement reorders and prevents wastage via proactive FEFO tracking. |
| **Public Health & Surveillance** | Syndromic disease trends, fever/diarrhea clusters, chronic NCD screening rates. | Provides early warning indicators for local disease outbreaks and seasonal spikes. |
| **Workforce Governance** | Staff attendance, active role assignments, dual-role coverage, facility postings. | Ensures adequate staffing coverage and enforces separation of duties. |
| **Administrative & ARS Oversight** | Untied fund balances, maintenance expenditures, compliance audit frequency. | Supports facility management committee governance and statutory audit compliance. |

### What Management Monitors & What it Tells Leadership

1. **Patient Attendance Trends**:
   - *What the screen shows*: Hourly walk-in arrivals, new citizen registrations, and total visits by clinic.
   - *What this tells leadership*: Identifies which clinics are facing high patient loads and where additional doctors or extended operating hours are required.
2. **Clinic Waiting Times & Bottlenecks**:
   - *What the screen shows*: Average minutes from registration to triage, triage to consultation, and consultation to medication collection.
   - *What this tells leadership*: Pinpoints exact workflow delays—revealing whether a clinic's bottleneck is at doctor consultation, laboratory testing, or the dispensing counter.
3. **Clinical Quality & Antibiotic Stewardship**:
   - *What the screen shows*: Percentage of patient visits resulting in antibiotic prescriptions, injection rates, and adherence to standard clinical guidelines.
   - *What this tells leadership*: Helps health leaders prevent antibiotic overuse and identify clinics requiring clinical training.
4. **District Pharmaceutical Stock Health**:
   - *What the screen shows*: Value and quantity of medicines expiring within 30, 60, and 90 days across all facilities; count of facilities with zero stock of essential drugs.
   - *What this tells leadership*: Enables proactive stock rebalancing—moving near-expiry medicines from quiet clinics to busy urban health centers before they expire.
5. **Syndromic Epidemiological Outbreak Alerts**:
   - *What the screen shows*: Spikes in presenting symptoms (fever with chills, acute respiratory distress, acute watery diarrhea) mapped by neighborhood pin code.
   - *What this tells leadership*: Provides early warning of vector-borne (Dengue, Malaria) or waterborne (Cholera) disease outbreaks days before hospital admissions surge.
6. **Workforce Attendance & Deployment**:
   - *What the screen shows*: Active staff on duty, facilities operating under dual-role staffing, and vacant medical officer positions.
   - *What this tells leadership*: Gives directors clear operational visibility into staff attendance without waiting for monthly paper attendance registers.

---

# PART G — SECURITY, ACCESS CONTROL & RESPONSIBILITY

Information security in Namma Clinic is designed around real healthcare operations, protecting patient privacy while ensuring clinical staff have immediate access to necessary medical data.

| Operational Role | Authorized Capabilities (ALLOW) | Strictly Denied Boundaries (DENY) |
| :--- | :--- | :--- |
| **Front Desk Officer** | Patient search, demographic updates, OPD token issuance, queue cancellation. | Medical history, clinical notes, diagnoses, prescriptions, lab ordering. |
| **Staff Nurse** | Physiological vitals entry, triage acuity assignment, nursing assessment, queue calls. | Electronic prescribing, medical diagnosis confirmation, drug dispensing. |
| **Medical Officer (Doctor)** | Clinical consultation, ICD-10 diagnosis, lab order generation, e-prescription creation. | Direct pharmacy stock removal, facility infrastructure decommissioning. |
| **Pharmacist** | Prescription verification, batch allocation by FEFO, medicine dispensing, batch lookup. | Clinical consultation, medical diagnosis, diagnostic lab ordering. |
| **Inventory Officer** | Warehouse purchase orders, Goods Receipt Notes (GRN), inventory ledger adjustments. | Patient clinical records, direct medication dispensing to citizens. |
| **Lab Technician** | Laboratory order review, specimen collection, test result recording and amendment. | Clinical consultation, prescription creation, pharmacy stock mutations. |

### Key Principles of Platform Security:

1. **Need-to-Know Privacy Boundaries**:
   Front-desk staff require citizen names and phone numbers to check patients in, but they have no legitimate clinical need to know that a citizen is undergoing treatment for depression or tuberculosis. The system strictly hides clinical notes from front desk screens.
2. **Clinical Safety Boundaries**:
   Staff Nurses play a vital triage role, but they cannot issue electronic drug prescriptions. Doctors diagnose and prescribe, but they do not dispense drugs directly from the pharmacy. Each professional operates strictly within their regulatory and clinical scope.
3. **Double-Entry Inventory Accountability**:
   Medicines cannot be added to or removed from clinic inventory informally. Stock enters via verified Goods Receipt Notes from approved suppliers and exits only through authenticated electronic doctor prescriptions.
4. **Facility Isolation & Scoping**:
   Clinic staff can only access records, queues, and inventory belonging to their assigned facility. They cannot view patient queues or drug stocks from other clinics unless authorized by the District Health Officer for district-wide oversight.
5. **Role-Based Audit Trail**:
   Every action in the system is stamped with the user's verified identity and their active operational role. If a nurse with dual front-desk and nursing roles registers a patient, it is audited under front-desk duty; when they enter vital signs, it is audited under nursing duty.

![Figure 54 — Clean Role Separation Enforcement](../../scratch/ui_audit_screenshots/compounder/unauth_consultation.png)
*Figure 54 — Clean Role Separation Enforcement — Clear access denial dialog ensuring administrative staff cannot view confidential clinical consultation records or diagnostic history.*

---

# PART H — ILLUSTRATIVE CLINICAL WALKTHROUGH — FICTIONAL PATIENT JOURNEY

> [!NOTE]
> **Fictional Illustrative Walkthrough Disclaimer**:
> The following clinical walkthrough depicts a fictional, representative patient scenario designed to illustrate how data, tokens, vitals, electronic orders, and dispensing instructions move across workstation roles in Namma Clinic. All patient names, registration IDs, clinical measurements, and operational metrics are simulated and illustrative. Real clinic patient throughput, consultation durations, and clinical outcomes naturally depend on individual medical urgency, facility staffing, and local operational factors.

To illustrate how Namma Clinic works in daily healthcare operations, consider the illustrative case of **Meenakshi**, a fictional 52-year-old resident who visits the clinic presenting with headaches, fatigue, and blurred vision over the past two weeks.

---

### Step 1: Arrival & Registration at Front Desk
Meenakshi walks into the clinic reception. Front Desk Officer **Kavitha** greets her and searches Meenakshi's mobile number in the patient directory. Finding no existing record, Kavitha opens the registration dialog, enters Meenakshi's demographic details, and issues outpatient **Token #T-104**. Kavitha gives Meenakshi her token slip and directs her to the triage waiting area.

* **Screen Used**: Citizen Intake & Token Registration.
* **Information Recorded**: Name, 52 yrs, Female, Phone number, Address.
* **What Happens Next**: Token T-104 immediately appears on Nurse Anitha's triage waiting queue.

![Figure 55 — Step 1: Front Desk Registers Meenakshi](../../scratch/ui_audit_screenshots/compounder/modal_01_registration_opened.png)
*Figure 55 — Step 1: Front Desk Registers Meenakshi — Reception intake dialog recording Meenakshi's demographic details and issuing sequential OPD Token T-104.*

---

### Step 2: Vital Signs Triage by Staff Nurse
Staff Nurse **Anitha** calls Token T-104 into the triage room. Anitha checks Meenakshi's blood pressure, pulse, temperature, oxygen saturation, height, and weight. The blood pressure reads **148/92 mmHg**, and a rapid fingerstick blood sugar reads **178 mg/dL**. The system automatically computes her BMI as **27.8** (Overweight) and assigns an **Amber (Urgent)** priority flag due to stage-1 hypertension.

* **Screen Used**: Nurse Triage & Vitals Assessment.
* **Information Recorded**: BP 148/92, Pulse 82 bpm, Temp 98.4°F, SpO2 98%, Random Blood Sugar 178 mg/dL, BMI 27.8, Acuity: Amber.
* **What Happens Next**: Meenakshi's token moves to Dr. Suresh's consultation queue, highlighted in amber with vitals pre-populated.

![Figure 56 — Step 2: Nurse Anitha Measures Meenakshi's Vitals](../../scratch/ui_audit_screenshots/nurse/04_triage.png)
*Figure 56 — Step 2: Nurse Anitha Measures Meenakshi's Vitals — Nursing triage assessment recording BP (148/92 mmHg), blood glucose (178 mg/dL), and BMI (27.8), triggering amber priority.*

---

### Step 3: Doctor Consultation, Examination & Prescribing
Medical Officer **Dr. Suresh** calls Meenakshi into the consultation room. Reviewing the elevated vitals recorded by Nurse Anitha, Dr. Suresh takes a detailed history, conducts an eye and cardiovascular examination, and confirms a clinical diagnosis of **Essential Hypertension (Primary)** and suspected **Type 2 Diabetes Mellitus**. 

Dr. Suresh orders a rapid **Urine Albumin test** at the clinic lab and electronically prescribes **Amlodipine 5mg** (once daily in the morning for 30 days) and **Metformin 500mg** (once daily with food for 30 days). He schedules a follow-up revisit in 30 days.

* **Screen Used**: Medical Officer Consultation Workstation.
* **Information Recorded**: Symptoms (headache, blurred vision), Physical Exam findings, ICD Diagnoses, Urine Albumin lab requisition, electronic prescriptions for Amlodipine and Metformin, 30-day revisit order.
* **What Happens Next**: The urine test order is queued on the laboratory workstation; the e-prescriptions are made available in the pharmacy queue.

![Figure 57 — Step 3: Dr. Suresh Records Meenakshi's Consultation](../../scratch/ui_audit_screenshots/doctor/04_consultation.png)
*Figure 57 — Step 3: Dr. Suresh Records Meenakshi's Consultation — Clinician workspace documenting hypertension, ordering rapid urine albumin screening, and generating electronic prescriptions.*

---

### Step 4: Laboratory Sample Collection & Rapid Testing
Meenakshi walks to the diagnostic lab window. Diagnostic Lab Technician **Prakash** collects her urine sample, runs a rapid dipstick test, and enters the result (**Trace Albumin**) directly into the laboratory console. 

* **Screen Used**: Diagnostic Laboratory Workstation.
* **Information Recorded**: Specimen collected, Test executed: Urine Albumin, Result: Trace, Status: Verified.
* **What Happens Next**: The result updates Dr. Suresh's chart immediately. With trace albumin noted, Dr. Suresh verifies that the prescribed Amlodipine remains clinically optimal and gives final electronic authorization.

![Figure 58 — Step 4: Lab Technician Prakash Enters Meenakshi's Test Results](../../scratch/ui_audit_screenshots/lab_technician/03_lab.png)
*Figure 58 — Step 4: Lab Technician Prakash Enters Meenakshi's Test Results — Laboratory queue screen recording urine test results and immediately updating Dr. Suresh's consultation chart.*

---

### Step 5: Pharmacy Verification & FEFO Dispensing
Meenakshi arrives at the clinic dispensary window. Pharmacist **Deepa** opens Meenakshi's prescription on the pharmacy workstation. The system automatically selects active batches of Amlodipine 5mg and Metformin 500mg with the earliest expiration dates. Deepa checks the shelf, matches the batch numbers, reviews the structured on-screen dosage schedule (Morning / Afternoon / Night with meals), and dispenses the medications to Meenakshi with clear counseling.

* **Screen Used**: Pharmacy Dispensing Workstation.
* **Information Recorded**: Dispensed Batches (AML-2026-B1, MET-2026-A4), Expiry dates, Quantities (30 tablets each), counseling confirmed.
* **What Happens Next**: The clinic warehouse ledger automatically decrements 30 tablets of each medication. The prescription status changes to 'Dispensed'.

![Figure 59 — Step 5: Pharmacist Deepa Verifies & Dispenses Medications](../../scratch/ui_audit_screenshots/pharmacist/03_pharmacy.png)
*Figure 59 — Step 5: Pharmacist Deepa Verifies & Dispenses Medications — Pharmacy console confirming FEFO batch allocations, deducting stock from clinic inventory, and providing dosage counseling.*

---

### Step 6: Follow-up Scheduling & Departure
Before leaving, Meenakshi is entered into Nurse Anitha's chronic care follow-up calendar for review in four weeks. Meenakshi completed intake, vital signs triage, physician consultation, diagnostic testing, and medication dispensing in a single orderly outpatient session without paper chart re-entry or lost prescription slips.

Meenakshi returns home with verified medicines, a structured care plan, and a recorded revisit date, while clinic management retains complete visibility into every clinical and operational milestone of her visit.

---

# PART I — CLIENT & STAKEHOLDER VALUE

Namma Clinic delivers concrete operational and clinical benefits across all stakeholder tiers:

| Stakeholder Tier | Direct Operational Value | Long-Term Health Impact |
| :--- | :--- | :--- |
| **Citizens & Patients** | Fair token-based queue numbers; standardized vital signs safety check; guaranteed First-Expired, First-Out fresh medicines; unified longitudinal medical record across clinic visits. | Eliminates queue confusion, prevents dispensing of degraded or expired medicines, and ensures personal health continuity. |
| **Clinical & Facility Staff** | Legible typed e-prescriptions; automated BMI calculations; direct digital laboratory result delivery; automated inventory deductions; reduced manual register paperwork. | Minimizes diagnostic turnaround times, eliminates handwriting transcription errors, and protects staff through verifiable audit trails. |
| **Health Leadership (DHO)** | Transparent real-time facility dashboards; early syndromic outbreak alerts; automated daily OPD and morbidity reporting; complete medicine ledger traceability. | Replaces delayed paper summaries with actionable operational visibility, strengthening primary healthcare governance. |

### Detailed Value Breakdown by Role

1. **For Citizens & Urban Patients**:
   - **Fair, Dignified Care**: Automated queue tokens prevent queue jumping and crowding.
   - **Medication Quality**: Automated First-Expired, First-Out (FEFO) dispensing ensures citizens receive fresh, potent medicines.
   - **Continuity of Care**: Longitudinal records mean patients do not have to repeat their medical history every time they visit.

2. **For Medical Officers (Doctors)**:
   - **Faster Consultations**: Pre-recorded nursing vitals and BMI save clinician time.
   - **Fewer Diagnostic Delays**: Laboratory orders and test results flow electronically.
   - **Safer Prescribing**: Standardized drug lists eliminate dosing ambiguities and transcription errors.

3. **For Staff Nurses**:
   - **Empowered Clinical Role**: Standardized vitals and acuity scoring allow nurses to actively prioritize urgent patients.
   - **Chronic Disease Tracking**: NCD and wellness registers make follow-up care organized and manageable.
   - **Elimination of Hand-Written Ledgers**: Replaces multiple paper logbooks with clean digital forms.

4. **For Front Desk Officers**:
   - **Fast Citizen Intake**: Mobile number search brings up existing records in seconds.
   - **Orderly Reception Area**: Sequential token issuance eliminates arguments at the reception window.
   - **Protection from Clinical Disputes**: Restricted demographic screens keep front desk work purely clerical.

5. **For Diagnostic Lab Technicians**:
   - **Clear Test Requests**: Legible electronic test orders eliminate confusion over hand-written test slips.
   - **Integrated Quality Checks**: Automatic reference range highlighting flags abnormal samples immediately.
   - **Audit-Ready Registers**: Test logs are stored electronically, ready for departmental inspection.

6. **For Pharmacists**:
   - **Zero Dispensing Ambiguity**: Typed, structured prescriptions eliminate handwriting misinterpretation.
   - **Automated Batch Guidance**: System points directly to the earliest-expiring active batch on shelf to minimize expiry risk.
   - **Accountability**: Dispensing-linked ledger deductions protect the pharmacist from unexplained inventory discrepancies.

7. **For Inventory Officers**:
   - **Procurement Control**: Structured purchase orders make vendor tracking straightforward.
   - **Accurate Deliveries**: Goods Receipt Notes verify batch numbers, expiry dates, and delivered counts.
   - **Stock Reconciliation**: Double-entry ledger prevents unexplained medicine losses.

8. **For Clinic / Hospital Administrators**:
   - **Workforce Governance**: Single-click role assignments ensure only qualified staff access each module.
   - **Operational Insights**: Queue dashboards identify clinic bottlenecks and departmental wait-time trends.
   - **Reporting Efficiency**: Daily outpatient and morbidity summaries export readily to standardized formats.

9. **For District Health Officers (DHO)**:
   - **Regional Visibility**: Comprehensive analytical dashboard demonstrates multi-facility tracking and governance capabilities.
   - **Early Outbreak Monitoring**: Syndromic surveillance models highlight disease trends to demonstrate early warning workflows.
   - **Optimized Resource Allocation**: Demonstrates monitoring workflows for clinics facing physician workload peaks or drug depletion.

10. **For Health Department & Government Leadership**:
    - **Demonstrated Return on Investment**: Higher patient throughput, lower administrative overhead, and minimized drug expiry waste.
    - **Policy-Ready Health Data**: Comprehensive, standardized morbidity data for public health planning.
    - **Local Infrastructure Resilience**: System runs reliably on local clinic hardware without expensive continuous cloud dependencies.

---

# PART J — SYSTEM REFERENCE & GLOSSARY

---

## 1. Authoritative Capability Scope Matrix (21 Platform Capabilities)

The table below provides an exact, verified accounting of the platform's 21 capabilities across operational tiers:

| # | Platform Capability | Authoritative Classification | Operational Scope & Verification Details |
| :- | :--- | :--- | :--- |
| **1** | **Patient Demographic Registry** | **Implemented & Verified** | Full citizen intake, search, deduplication, and demographic records. |
| **2** | **OPD Token & Queue State Machine** | **Implemented & Verified** | Daily sequential token generation, department routing, and status transitions. |
| **3** | **Clinical Nursing Triage & Vitals** | **Implemented & Verified** | Vitals capture (BP, pulse, temp, SpO2, RR, BMI) and clinical priority scoring. |
| **4** | **Doctor Consultation & E-Prescribing** | **Implemented & Verified** | Clinical notes, diagnosis entry, diagnostic test orders, and electronic prescriptions. |
| **5** | **Diagnostic Laboratory Workstation** | **Implemented & Verified** | Specimen collection intake, quantitative test result recording, and physician chart update. |
| **6** | **Pharmacy Dispensing & FEFO Allocation** | **Implemented & Verified** | Prescription verification, FEFO batch recommendation, and double-entry stock decrement. |
| **7** | **Warehouse Inventory & Stock Ledger** | **Implemented & Verified** | Batch-level ledger balances, expiration date tracking, and transaction audit trails. |
| **8** | **Procurement & Purchase Orders (PO)** | **Implemented & Verified** | Supplier purchase order creation, line-item quantities, and fulfillment tracking. |
| **9** | **Goods Receipt Notes (GRN)** | **Implemented & Verified** | Inbound delivery physical inspection, batch verification, and store ledger intake. |
| **10**| **Staff Administration & IAM Governance** | **Implemented & Verified** | Staff directory, role allocation, facility scoping, and **Dual-Role staffing** (*Small-Clinic Rule*). |
| **11**| **Specialist Referrals Management** | **Demonstration & Extension** | Database schema and interface prototype implemented; runs in demonstration mode (0 baseline records). |
| **12**| **Patient Follow-up & Recall Workstation** | **Demonstration & Extension** | Database schema and calendar interface implemented; runs in demonstration mode (0 baseline records). |
| **13**| **Non-Communicable Diseases (NCD) Registry**| **Demonstration & Extension** | Chronic cohort tracking schema and interface prototype; runs in demonstration mode (0 baseline records). |
| **14**| **Public Health Surveillance Console** | **Demonstration & Extension** | Disease category tracking prototype; runs in demonstration mode without external WAN clustering. |
| **15**| **Community Outreach Camp Logging** | **Demonstration & Extension** | Outreach camp event schema and interface prototype; runs in demonstration mode (0 baseline records). |
| **16**| **Wellness & Health Education Sessions** | **Demonstration & Extension** | Yoga/wellness session logging schema and interface; runs in demonstration mode (0 baseline records). |
| **17**| **Quality Indicators & Biomedical Waste** | **Demonstration & Extension** | Kayakalpa quality checklist and waste log interface; runs in demonstration mode (0 baseline records). |
| **18**| **Clinic Infrastructure & Asset Registry** | **Demonstration & Extension** | Facility directory active; maintenance tickets and cold-chain logging are demonstration prototypes. |
| **19**| **Operational Reporting Engine** | **Cross-Cutting Platform Service (Implemented)**| Facility attendance summaries and daily outpatient visit logs with CSV export. |
| **20**| **Alerts & Early Warning Notification Hub** | **Cross-Cutting Platform Service (Demonstration)**| Centralized visual warning banners on workstation dashboards; no external WebSocket server. |
| **21**| **Security & Audit Logging** | **Cross-Cutting Platform Service (Implemented)**| Relational audit logging active in backend middleware with 2,260+ verified database records. |
| **—**| **Local Clinic Execution** | **Standard Operational Mode** | Native execution on local clinic workstations/laptops backed by local PostgreSQL 16. |
| **—**| **Arogya Raksha Samiti (ARS)** | **Administrative Capability** | Untied facility maintenance fund tracking managed under clinic and district administration. |
| **—**| **Maternal & Child Health (MCH)** | **Explicitly Out of Scope** | Strictly out of scope per Engineering Rule 10 (no ANC, PNC, or child immunization models). |

---

## 2. Planned Future Capabilities (Roadmap)

To ensure full transparency with stakeholders, the following features are strategically planned for future phases:

* **Planned Phase 29 — National Health Gateway Integration (ABDM / ABHA)**:
  - *Status: Planned / Demonstration Prototype*.
  - *Capability*: Connecting citizen demographic data to national digital health servers for automated OTP-based health ID generation and QR code check-in. Current screens provide demonstration/simulation workflows.
* **Planned Phase 30 — Telemedicine & Specialist Consultation (e-Sanjeevani)**:
  - *Status: Planned / Architecture Prepared*.
  - *Capability*: Integrated video consultation connecting urban clinic medical officers with hospital specialty consultants.
* **Planned Phase 31 — Centralized District Data Sync Gateway**:
  - *Status: Planned / Architecture Prepared*.
  - *Capability*: Overnight encrypted batch synchronization transmitting local clinic databases to central state health department servers over secure WAN.
* **Planned Phase 32 — Barcode & QR Code Dispensing Hardware**:
  - *Status: Planned / Architecture Prepared*.
  - *Capability*: Handheld barcode scanner integration for rapid medicine packaging verification at the pharmacy counter.
* **Planned Phase 33 — Automated Cold-Chain IoT Telemetry**:
  - *Status: Planned / Architecture Prepared*.
  - *Capability*: Wireless IoT temperature probe integration streaming vaccine refrigerator telemetry into facility alerts.

---

## 3. Glossary of Healthcare & Administrative Terms

* **Acuity Level**: A standardized assessment of how urgently a patient requires medical care (`IMMEDIATE`, `VERY_URGENT`, `URGENT`, `STANDARD`, `NON_URGENT`).
* **ARS (Arogya Raksha Samiti)**: Untied health facility development and maintenance funds provided to public clinics for upkeep, emergency repairs, and citizen amenities.
* **Batch Number**: A unique identifier assigned by pharmaceutical manufacturers to a specific production lot of medication, essential for quality tracking and recall management.
* **BMI (Body Mass Index)**: A calculated ratio of body weight to height ($kg/m^2$) used by nurses to screen for underweight, healthy, overweight, or obese status.
* **Chief Complaint**: The primary symptom or health concern expressed by the citizen upon arrival at the clinic.
* **DHO (District Health Officer)**: The senior medical officer responsible for the administration and public health governance of all health centers across an administrative district.
* **Dual Role**: An administrative configuration allowing a single staff member in a small clinic to carry out two separate operational duties (e.g., Nurse + Front Desk Officer) without creating informal shortcuts.
* **Electronic Prescription (E-Rx)**: A digitally created medication order specifying drug name, strength, dosage form, frequency, and duration.
* **EMR (Electronic Medical Record)**: The longitudinal digital health file documenting a citizen's consultations, vitals, diagnoses, laboratory investigations, and medication history.
* **FEFO (First-Expired, First-Out)**: A strict inventory management discipline requiring that medication batches expiring earliest are dispensed before newer stock, preventing drug wastage.
* **Front Desk Officer**: The administrative reception worker responsible for citizen registration, demographic search, and daily OPD token issuance.
* **GRN (Goods Receipt Note)**: A certified administrative document verifying that delivered pharmaceuticals have been inspected, checked against purchase orders, and added to clinic stock.
* **NCD (Non-Communicable Diseases)**: Long-term chronic medical conditions (e.g., Hypertension, Type-2 Diabetes) requiring periodic monitoring and regular medication refills.
* **OPD (Outpatient Department)**: Ambulatory care services provided to walk-in citizens who receive diagnosis and treatment without requiring overnight hospital admission.
* **PHC (Primary Health Center)**: A frontline government healthcare facility providing comprehensive primary medical care and disease prevention (Note: Dedicated Maternal/Child Health and child immunization vertical programs are explicitly out of scope for Namma Clinic).
* **Purchase Order (PO)**: A formal procurement document sent to an authorized pharmaceutical supplier requesting specific medicines, quantities, and agreed delivery terms.
* **SpO2 (Blood Oxygen Saturation)**: The percentage of oxygen-saturated hemoglobin in the blood measured non-invasively using a pulse oximeter.
* **Syndromic Surveillance**: The continuous collection and analysis of presenting symptoms (e.g., acute fever, rash, respiratory distress) to detect communicable disease outbreaks early.
* **Triage**: The standardized process of examining walk-in patients immediately upon arrival to determine medical urgency and prioritize clinician examination.
* **Vitals**: Core physiological indicators of health status measured by the nurse: Blood Pressure, Heart Rate, Body Temperature, Respiratory Rate, and Oxygen Saturation.
* **Void Token**: The administrative cancellation of an OPD token issued in error, permitted only before clinical triage has begun.
