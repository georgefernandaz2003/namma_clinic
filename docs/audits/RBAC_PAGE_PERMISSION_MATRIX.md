# Namma Clinic — Master RBAC Page Permission Matrix

**Release Baseline**: `f3cd9ab421177b338959f88cf17ffa048a6ff093`  
**Branch**: `feature/namma-clinic-demo-data-model`  
**Standard**: Three-Tier Capability Model (`READ` / `WRITE` / `MANAGE`)  
**Scope Isolation**: Mandatory Facility and District Boundaries Enforced at Frontend & Backend

---

## 1. Capability Level Definitions

| Capability Level | Operational Scope & Authority | Allowed Actions & Examples | Forbidden Actions |
|---|---|---|---|
| **READ** | View, search, inspect, and export within authorized scope. | View patient demographics, inspect longitudinal EMR timeline, view active queues, review triage vitals, read lab investigation results, inspect drug inventory and expiring batches, view clinical alerts. | Cannot register patients, log vitals, create consultations, issue prescriptions, collect lab samples, dispense drugs, or alter facility configurations. |
| **WRITE** | Create, update, and transition transactional/operational records. | Register citizen, issue OPD token, record triage vitals, document consultation & ICD-10 diagnosis, prescribe medicines, order diagnostic tests, collect lab specimens & enter results, dispense pharmacy items, create referrals, complete follow-ups. | Cannot alter system configuration, approve purchase orders, reallocate facility budgets, bypass Kayakalp checklists, or perform district oversight mutations. |
| **MANAGE** | Administer, approve, configure, or govern within a specific operational domain. | Approve hospital purchase orders, register vendors, maintain facility infrastructure & oxygen banks, manage Arogya Raksha Samiti (ARS) governance meetings & untied funds, manage NQAS/Kayakalp checklists, export district aggregate data, audit trails. | Restricted to the role's authorized domain. MANAGE is **never** globally granted. Clinicians do not manage procurement; administrators do not manage clinical decisions. |

---

## 2. Master Page & Route Permission Matrix (All 25 Pages × 6 Roles)

### A. Login & Public Authentication

| Page | Route | Role | READ | WRITE | MANAGE | Sidebar | Direct URL | Backend API Permission | Facility Scope | District Scope | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Login | `/login` | Public (All) | YES | YES | NO | NO | YES | `rest_framework.permissions.AllowAny` | N/A | N/A | Entry authentication & JWT credential exchange. |

---

### B. Clinical Care & Nursing Workspaces

| Page | Route | Role | READ | WRITE | MANAGE | Sidebar | Direct URL | Backend API Permission | Facility Scope | District Scope | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Dashboard** | `/` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `dashboard.view` | NO | YES | District-wide operational and public health governance deck. |
| Dashboard | `/` | `HOSPITAL_ADMIN` | YES | NO | YES | YES | YES | `dashboard.view` | YES | NO | Facility command desk for bed, staff, and OPD operational oversight. |
| Dashboard | `/` | `DOCTOR` | YES | YES | NO | YES | YES | `dashboard.view`, `queue.view`, `triage.view` | YES | NO | Clinical encounter deck: called patients, triage vitals, EMR consultation. |
| Dashboard | `/` | `NURSE` | YES | YES | NO | YES | YES | `dashboard.view`, `queue.view`, `triage.view` | YES | NO | OPD desk: arrivals, vitals waiting list, triage warnings, outreach. |
| Dashboard | `/` | `LAB_TECHNICIAN` | YES | YES | NO | YES | YES | `dashboard.view`, `lab_orders.view` | YES | NO | Diagnostics lab console: pending specimens, urgent test orders. |
| Dashboard | `/` | `PHARMACIST` | YES | YES | YES | YES | YES | `dashboard.view`, `pharmacy.view`, `inventory.view` | YES | NO | Drug store console: pending e-prescriptions, FEFO alerts, low stock. |
| **Patients** | `/patients` | `DISTRICT_OFFICER` | YES | NO | NO | YES | YES | `patients.view` | NO | YES | Citizen master index inspection across district clinics. Read-only. |
| Patients | `/patients` | `HOSPITAL_ADMIN` | YES | YES | NO | YES | YES | `patients.view`, `patients.create`, `patients.update` | YES | NO | Patient registration and administrative demographic maintenance. |
| Patients | `/patients` | `DOCTOR` | YES | NO | NO | YES | YES | `patients.view`, `patients.update` | YES | NO | Patient clinical history lookup. Registration performed at desk. |
| Patients | `/patients` | `NURSE` | YES | YES | NO | YES | YES | `patients.view`, `patients.create`, `patients.update` | YES | NO | Frontline citizen registration and demographic verification. |
| Patients | `/patients` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Unnecessary full patient directory; lab tech works from order queue. |
| Patients | `/patients` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Unnecessary patient master; pharmacist works from prescription queue. |
| **Patient Detail** | `/patients/:id` | `DISTRICT_OFFICER` | YES | NO | NO | NO | YES | `patients.view` | NO | YES | Read-only longitudinal clinical timeline audit. |
| Patient Detail | `/patients/:id` | `HOSPITAL_ADMIN` | YES | NO | NO | NO | YES | `patients.view` | YES | NO | Longitudinal EMR verification and referral audit. |
| Patient Detail | `/patients/:id` | `DOCTOR` | YES | NO | NO | NO | YES | `patients.view` | YES | NO | Comprehensive patient medical history, past diagnoses, lab trends. |
| Patient Detail | `/patients/:id` | `NURSE` | YES | NO | NO | NO | YES | `patients.view` | YES | NO | Nursing timeline review, immunization and triage history. |
| Patient Detail | `/patients/:id` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Access Denied (HTTP 403). Lab tech accesses test results in `/lab`. |
| Patient Detail | `/patients/:id` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Access Denied (HTTP 403). Pharmacist accesses medications in `/pharmacy`. |
| **OPD Queue** | `/queue` | `DISTRICT_OFFICER` | YES | NO | NO | YES | YES | `queue.view` | NO | YES | District clinic OPD workflow monitoring. Read-only. No action buttons. |
| OPD Queue | `/queue` | `HOSPITAL_ADMIN` | YES | YES | YES | YES | YES | `queue.view`, `queue.create`, `queue.transition` | YES | NO | Facility OPD token issuing, queue flow oversight. |
| OPD Queue | `/queue` | `DOCTOR` | YES | YES | NO | YES | YES | `queue.view`, `queue.call_next`, `queue.transition` | YES | NO | OPD consultation queue: calls triaged patients ("Consult →"). |
| OPD Queue | `/queue` | `NURSE` | YES | YES | NO | YES | YES | `queue.view`, `queue.create`, `queue.transition` | YES | NO | Issues OPD tokens, performs nurse triage ("Triage →"). |
| OPD Queue | `/queue` | `LAB_TECHNICIAN` | YES | NO | NO | YES | YES | `queue.view` | YES | NO | Monitors lab transit status for queued OPD patients. |
| OPD Queue | `/queue` | `PHARMACIST` | YES | YES | NO | YES | YES | `queue.view` | YES | NO | Monitors pharmacy transit status ("Dispense →"). |
| **Nurse Triage** | `/triage` | `DISTRICT_OFFICER` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical nursing workflow. Access Denied (HTTP 403). |
| Nurse Triage | `/triage` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | Administrative role. Access Denied (HTTP 403). |
| Nurse Triage | `/triage` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Doctor reviews vitals in Consultation/Dashboard; does not log triage. |
| Nurse Triage | `/triage` | `NURSE` | YES | YES | NO | YES | YES | `triage.view`, `triage.create`, `triage.update` | YES | NO | Primary nursing vital signs logging, BMI, risk alerts. |
| Nurse Triage | `/triage` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-laboratory workflow. Access Denied (HTTP 403). |
| Nurse Triage | `/triage` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-pharmacy workflow. Access Denied (HTTP 403). |
| **Doctor Consultation** | `/consultation` | `DISTRICT_OFFICER` | NO | NO | NO | NO | NO | None | N/A | N/A | Confidential doctor encounter. Access Denied (HTTP 403). |
| Doctor Consultation | `/consultation` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | Confidential medical encounter. Access Denied (HTTP 403). |
| Doctor Consultation | `/consultation` | `DOCTOR` | YES | YES | NO | YES | YES | `consultation.create`, `prescription.create`, `lab_orders.create`, `referrals.create` | YES | NO | Primary medical examination, ICD diagnosis, e-prescription, lab orders. |
| Doctor Consultation | `/consultation` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Medical officer prerogative. Access Denied (HTTP 403). |
| Doctor Consultation | `/consultation` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-laboratory workflow. Access Denied (HTTP 403). |
| Doctor Consultation | `/consultation` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-pharmacy workflow. Access Denied (HTTP 403). |
| **Diagnostics Lab** | `/lab` | `DISTRICT_OFFICER` | NO | NO | NO | NO | NO | None | N/A | N/A | Operational lab station. Access Denied (HTTP 403). |
| Diagnostics Lab | `/lab` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | Operational laboratory station. Access Denied (HTTP 403). |
| Diagnostics Lab | `/lab` | `DOCTOR` | YES | NO | NO | YES | YES | `lab_orders.view`, `lab_results.view` | YES | NO | Clinician inspection of lab orders, specimen status, and release values. |
| Diagnostics Lab | `/lab` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Diagnostic station. Access Denied (HTTP 403). |
| Diagnostics Lab | `/lab` | `LAB_TECHNICIAN` | YES | YES | NO | YES | YES | `lab_orders.view`, `lab_orders.update`, `lab_results.create`, `lab_results.update` | YES | NO | Sample collection, barcode generation, test execution, verification. |
| Diagnostics Lab | `/lab` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Diagnostic station. Access Denied (HTTP 403). |
| **Pharmacy & FEFO** | `/pharmacy` | `DISTRICT_OFFICER` | YES | NO | NO | YES | YES | `inventory.view`, `reports.view` | NO | YES | District drug inventory monitoring, stockout detection. Read-only. |
| Pharmacy & FEFO | `/pharmacy` | `HOSPITAL_ADMIN` | YES | NO | YES | YES | YES | `inventory.view`, `po.view`, `po.create`, `po.update`, `vendor.view`, `vendor.create` | YES | NO | Facility drug inventory oversight, vendor contracts, PO approvals. |
| Pharmacy & FEFO | `/pharmacy` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Doctor prescribes in Consultation; does not manage dispensary. |
| Pharmacy & FEFO | `/pharmacy` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Nursing scope. Access Denied (HTTP 403). |
| Pharmacy & FEFO | `/pharmacy` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Laboratory scope. Access Denied (HTTP 403). |
| Pharmacy & FEFO | `/pharmacy` | `PHARMACIST` | YES | YES | YES | YES | YES | `pharmacy.view`, `pharmacy.dispense`, `inventory.update`, `po.view`, `po.update` | YES | NO | Controlled FEFO dispensing, stock receipts, inventory ledger. |
| **Referrals** | `/referrals` | `DISTRICT_OFFICER` | YES | NO | NO | YES | YES | `referrals.view` | NO | YES | District secondary/tertiary referral linkage analytics. Read-only. |
| Referrals | `/referrals` | `HOSPITAL_ADMIN` | YES | YES | NO | YES | YES | `referrals.view`, `referrals.create` | YES | NO | Facility incoming/outgoing transfer tracking and specialist liaison. |
| Referrals | `/referrals` | `DOCTOR` | YES | YES | NO | YES | YES | `referrals.view`, `referrals.create` | YES | NO | Inter-facility patient referrals, specialist consultation advice. |
| Referrals | `/referrals` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Referral decisions handled by Medical Officer. Access Denied (HTTP 403). |
| Referrals | `/referrals` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-laboratory workflow. Access Denied (HTTP 403). |
| Referrals | `/referrals` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-pharmacy workflow. Access Denied (HTTP 403). |
| **Follow-up Care** | `/followups` | `DISTRICT_OFFICER` | NO | NO | NO | NO | NO | None | N/A | N/A | Patient-level clinical schedule. DHO inspects aggregate via Reports. |
| Follow-up Care | `/followups` | `HOSPITAL_ADMIN` | YES | YES | NO | YES | YES | `appointments.view`, `appointments.update` | YES | NO | Facility outpatient review scheduling and clinic volume tracking. |
| Follow-up Care | `/followups` | `DOCTOR` | YES | YES | NO | YES | YES | `appointments.view`, `appointments.create`, `appointments.update` | YES | NO | Chronic care review scheduling, treatment plan adjustments. |
| Follow-up Care | `/followups` | `NURSE` | YES | YES | NO | YES | YES | `appointments.view`, `appointments.update` | YES | NO | Outreach follow-up call tracking and attendance marking. |
| Follow-up Care | `/followups` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-laboratory workflow. Access Denied (HTTP 403). |
| Follow-up Care | `/followups` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-pharmacy workflow. Access Denied (HTTP 403). |
| **NCD Management** | `/ncd` | `DISTRICT_OFFICER` | YES | NO | NO | YES | YES | `ncd.view` | NO | YES | District non-communicable disease control program analytics. |
| NCD Management | `/ncd` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical chronic care cohort. Handled by Doctor and Nurse. |
| NCD Management | `/ncd` | `DOCTOR` | YES | YES | NO | YES | YES | `ncd.view`, `ncd.create`, `ncd.update` | YES | NO | Hypertension & diabetes staging, medication adjustment, risk flags. |
| NCD Management | `/ncd` | `NURSE` | YES | YES | NO | YES | YES | `ncd.view`, `ncd.create`, `ncd.update` | YES | NO | Population screening, blood pressure/glucose tracking registers. |
| NCD Management | `/ncd` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Diagnostic station. Access Denied (HTTP 403). |
| NCD Management | `/ncd` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Dispensary station. Access Denied (HTTP 403). |

---

### C. Public Health, Outreach & Community Governance

| Page | Route | Role | READ | WRITE | MANAGE | Sidebar | Direct URL | Backend API Permission | Facility Scope | District Scope | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Disease Surveillance**| `/surveillance` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `surveillance.view` | NO | YES | IDSP communicable disease cluster tracking and epidemic alert engine. |
| Disease Surveillance| `/surveillance` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | District public health jurisdiction. Access Denied (HTTP 403). |
| Disease Surveillance| `/surveillance` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Doctor reports cases in Consultation; does not monitor district clusters. |
| Disease Surveillance| `/surveillance` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Community nurse reports via Outreach; does not run surveillance portal. |
| Disease Surveillance| `/surveillance` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Diagnostic station. Access Denied (HTTP 403). |
| Disease Surveillance| `/surveillance` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Dispensary station. Access Denied (HTTP 403). |
| **Outreach & Camps** | `/outreach` | `DISTRICT_OFFICER` | NO | NO | NO | NO | NO | None | N/A | N/A | Operational field camp ledger. Access Denied (HTTP 403). |
| Outreach & Camps | `/outreach` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | Field nursing workflow. Access Denied (HTTP 403). |
| Outreach & Camps | `/outreach` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | OPD medical officer desk. Access Denied (HTTP 403). |
| Outreach & Camps | `/outreach` | `NURSE` | YES | YES | NO | YES | YES | `outreach.view` | YES | NO | Slum outreach screening, mobile camp logs, vulnerable group tracking. |
| Outreach & Camps | `/outreach` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Diagnostic station. Access Denied (HTTP 403). |
| Outreach & Camps | `/outreach` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Dispensary station. Access Denied (HTTP 403). |
| **Wellness Sessions**| `/wellness` | `DISTRICT_OFFICER` | NO | NO | NO | NO | NO | None | N/A | N/A | Operational wellness log. Access Denied (HTTP 403). |
| Wellness Sessions| `/wellness` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | Nursing wellness log. Access Denied (HTTP 403). |
| Wellness Sessions| `/wellness` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical consultation scope. Access Denied (HTTP 403). |
| Wellness Sessions| `/wellness` | `NURSE` | YES | YES | NO | YES | YES | `wellness.view` | YES | NO | Yoga, dietary lifestyle counseling, preventive wellness sessions. |
| Wellness Sessions| `/wellness` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Diagnostic station. Access Denied (HTTP 403). |
| Wellness Sessions| `/wellness` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Dispensary station. Access Denied (HTTP 403). |
| **ARS Committee** | `/ars` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `ars.view` | NO | YES | District Arogya Raksha Samiti community governance oversight. |
| ARS Committee | `/ars` | `HOSPITAL_ADMIN` | YES | YES | YES | YES | YES | `ars.view` | YES | NO | Facility ARS meeting minutes, expenditure tracking, untied funds. |
| ARS Committee | `/ars` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Administrative committee. Access Denied (HTTP 403). |
| ARS Committee | `/ars` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Administrative committee. Access Denied (HTTP 403). |
| ARS Committee | `/ars` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-administrative role. Access Denied (HTTP 403). |
| ARS Committee | `/ars` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Non-administrative role. Access Denied (HTTP 403). |
| **Quality & Waste** | `/quality` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `quality.view` | NO | YES | District Kayakalp/NQAS compliance audit & biomedical waste monitoring. |
| Quality & Waste | `/quality` | `HOSPITAL_ADMIN` | YES | YES | YES | YES | YES | `quality.view` | YES | NO | Facility Kayakalp checklists, color-coded biomedical waste logs. |
| Quality & Waste | `/quality` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Quality assurance administration. Access Denied (HTTP 403). |
| Quality & Waste | `/quality` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Quality assurance administration. Access Denied (HTTP 403). |
| Quality & Waste | `/quality` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Quality assurance administration. Access Denied (HTTP 403). |
| Quality & Waste | `/quality` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Quality assurance administration. Access Denied (HTTP 403). |

---

### D. Facility Operations, Infrastructure & District Governance

| Page | Route | Role | READ | WRITE | MANAGE | Sidebar | Direct URL | Backend API Permission | Facility Scope | District Scope | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Healthcare Network**| `/network` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `clinic.view`, `hospital.view`, `district.view` | NO | YES | District facility hierarchy and referral network topology tree. |
| Healthcare Network| `/network` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | District-level network design. Access Denied (HTTP 403). |
| Healthcare Network| `/network` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | District topology view. Access Denied (HTTP 403). |
| Healthcare Network| `/network` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | District topology view. Access Denied (HTTP 403). |
| Healthcare Network| `/network` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | District topology view. Access Denied (HTTP 403). |
| Healthcare Network| `/network` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | District topology view. Access Denied (HTTP 403). |
| **Facilities Master** | `/facilities` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `hospital.view`, `clinic.view` | NO | YES | District clinic directory, bed capacities, service capabilities. |
| Facilities Master | `/facilities` | `HOSPITAL_ADMIN` | YES | NO | YES | YES | YES | `hospital.view`, `clinic.view` | YES | NO | Facility profile, department capabilities, bed capacity management. |
| Facilities Master | `/facilities` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Administrative facility setup. Access Denied (HTTP 403). |
| Facilities Master | `/facilities` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Administrative facility setup. Access Denied (HTTP 403). |
| Facilities Master | `/facilities` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Administrative facility setup. Access Denied (HTTP 403). |
| Facilities Master | `/facilities` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Administrative facility setup. Access Denied (HTTP 403). |
| **Clinic Infra** | `/infrastructure`| `DISTRICT_OFFICER` | YES | NO | NO | YES | YES | `clinic.view` | NO | YES | District infrastructure oversight: oxygen cylinders, maintenance tickets. |
| Clinic Infra | `/infrastructure`| `HOSPITAL_ADMIN` | YES | YES | YES | YES | YES | `clinic.view` | YES | NO | Oxygen bank replenishment, equipment maintenance tickets, bed allocation. |
| Clinic Infra | `/infrastructure`| `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Physical maintenance. Access Denied (HTTP 403). |
| Clinic Infra | `/infrastructure`| `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Physical maintenance. Access Denied (HTTP 403). |
| Clinic Infra | `/infrastructure`| `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Physical maintenance. Access Denied (HTTP 403). |
| Clinic Infra | `/infrastructure`| `PHARMACIST` | YES | NO | NO | YES | YES | `clinic.view` | YES | NO | Cold-chain, oxygen, and consumable stock inspection. Read-only. |
| **Reports & CSV** | `/reports` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `reports.view`, `reports.export` | NO | YES | District authenticated RFC 4180 CSV extract (OPD, Rx, NCD, IDSP). |
| Reports & CSV | `/reports` | `HOSPITAL_ADMIN` | YES | NO | YES | YES | YES | `reports.view`, `reports.export` | YES | NO | Facility authenticated CSV operational and clinical reports export. |
| Reports & CSV | `/reports` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical consultation scope. Access Denied (HTTP 403). |
| Reports & CSV | `/reports` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Nursing scope. Access Denied (HTTP 403). |
| Reports & CSV | `/reports` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Laboratory scope. Access Denied (HTTP 403). |
| Reports & CSV | `/reports` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Pharmacy scope. Access Denied (HTTP 403). |
| **Alert Engine** | `/alerts` | `DISTRICT_OFFICER` | YES | YES | YES | YES | YES | `alerts.view`, `alerts.update` | NO | YES | District clinical, disease epidemic, and supply chain alert review. |
| Alert Engine | `/alerts` | `HOSPITAL_ADMIN` | YES | YES | YES | YES | YES | `alerts.view`, `alerts.update` | YES | NO | Facility operational, stockout, and referral alert management. |
| Alert Engine | `/alerts` | `DOCTOR` | YES | YES | NO | YES | YES | `alerts.view`, `alerts.update` | YES | NO | Critical lab result alerts, emergency triage alerts, drug alerts. |
| Alert Engine | `/alerts` | `NURSE` | YES | YES | NO | YES | YES | `alerts.view`, `alerts.update` | YES | NO | Severe triage alerts, high-risk patient arrival alerts. |
| Alert Engine | `/alerts` | `LAB_TECHNICIAN` | YES | YES | NO | YES | YES | `alerts.view`, `alerts.update` | YES | NO | Critical diagnostic value notifications and urgent stat orders. |
| Alert Engine | `/alerts` | `PHARMACIST` | YES | YES | NO | YES | YES | `alerts.view`, `alerts.update` | YES | NO | Drug stockout alarms, batch expiry (<30 days) warnings. |
| **Integrations** | `/integrations` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `integrations.view` | NO | YES | National digital health connectors status (ABDM, ABHA, HMIS). |
| Integrations | `/integrations` | `HOSPITAL_ADMIN` | YES | NO | YES | YES | YES | `integrations.view` | YES | NO | Facility gateway synchronization status and transaction ledger. |
| Integrations | `/integrations` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | IT connector administration. Access Denied (HTTP 403). |
| Integrations | `/integrations` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | IT connector administration. Access Denied (HTTP 403). |
| Integrations | `/integrations` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | IT connector administration. Access Denied (HTTP 403). |
| Integrations | `/integrations` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | IT connector administration. Access Denied (HTTP 403). |
| **Compliance** | `/compliance` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `audit_logs.view` | NO | YES | Namma Clinic regulatory mandate & requirements compliance checklist. |
| Compliance | `/compliance` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | District oversight mandate. Access Denied (HTTP 403). |
| Compliance | `/compliance` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical care scope. Access Denied (HTTP 403). |
| Compliance | `/compliance` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical care scope. Access Denied (HTTP 403). |
| Compliance | `/compliance` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Laboratory scope. Access Denied (HTTP 403). |
| Compliance | `/compliance` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Pharmacy scope. Access Denied (HTTP 403). |
| **Audit Trail** | `/audit` | `DISTRICT_OFFICER` | YES | NO | YES | YES | YES | `audit_logs.view` | NO | YES | Immutable security, access, and clinical change audit ledger. |
| Audit Trail | `/audit` | `HOSPITAL_ADMIN` | NO | NO | NO | NO | NO | None | N/A | N/A | Independent district auditor scope. Access Denied (HTTP 403). |
| Audit Trail | `/audit` | `DOCTOR` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical care scope. Access Denied (HTTP 403). |
| Audit Trail | `/audit` | `NURSE` | NO | NO | NO | NO | NO | None | N/A | N/A | Clinical care scope. Access Denied (HTTP 403). |
| Audit Trail | `/audit` | `LAB_TECHNICIAN` | NO | NO | NO | NO | NO | None | N/A | N/A | Laboratory scope. Access Denied (HTTP 403). |
| Audit Trail | `/audit` | `PHARMACIST` | NO | NO | NO | NO | NO | None | N/A | N/A | Pharmacy scope. Access Denied (HTTP 403). |

---

## 3. Role-Specific Sidebar Architecture & Functional Grouping

### 1. DOCTOR (9 Items — Matches UI Quality Reference Exactly)
```text
CLINICAL CARE
├── Dashboard                     [/]
├── Patients                      [/patients]
├── OPD Queue                     [/queue]
├── Doctor Consultation           [/consultation]
├── Diagnostics Lab               [/lab]
├── Referral Network              [/referrals]
├── Follow-up Care                [/followups]
└── NCD Management                [/ncd]

SYSTEM
└── Alert Engine                  [/alerts]
```

### 2. NURSE (9 Items)
```text
PRIMARY CARE & TRIAGE
├── Dashboard                     [/]
├── Patients                      [/patients]
├── OPD Queue                     [/queue]
├── Nurse Triage                  [/triage]
├── Follow-up Care                [/followups]
└── NCD Management                [/ncd]

COMMUNITY HEALTH
├── Outreach & Camps              [/outreach]
└── Wellness Sessions             [/wellness]

SYSTEM
└── Alert Engine                  [/alerts]
```

### 3. LAB TECHNICIAN (4 Items)
```text
DIAGNOSTICS
├── Dashboard                     [/]
├── OPD Queue                     [/queue]
└── Diagnostics Lab               [/lab]

SYSTEM
└── Alert Engine                  [/alerts]
```

### 4. PHARMACIST (5 Items)
```text
PHARMACY & DRUG LEDGER
├── Dashboard                     [/]
├── OPD Queue                     [/queue]
├── Pharmacy & FEFO               [/pharmacy]
└── Clinic Infra & Maintenance    [/infrastructure]

SYSTEM
└── Alert Engine                  [/alerts]
```

### 5. HOSPITAL ADMIN (13 Items)
```text
FACILITY OPERATIONS
├── Dashboard                     [/]
├── Facilities Master             [/facilities]
├── Patients                      [/patients]
├── OPD Queue                     [/queue]
├── Pharmacy & FEFO               [/pharmacy]
├── Referral Network              [/referrals]
├── Follow-up Care                [/followups]
└── Clinic Infra & Maintenance    [/infrastructure]

GOVERNANCE & QUALITY
├── ARS Committee                 [/ars]
├── Quality & Waste               [/quality]
└── Reports & CSV                 [/reports]

SYSTEM
├── Integrations (Mock)           [/integrations]
└── Alert Engine                  [/alerts]
```

### 6. DISTRICT OFFICER (17 Items)
```text
DISTRICT OVERSIGHT
├── Dashboard                     [/]
├── Healthcare Network            [/network]
├── Facilities Master             [/facilities]
├── Patients                      [/patients]
├── OPD Queue                     [/queue]
├── Pharmacy & FEFO               [/pharmacy]
└── Referral Network              [/referrals]

PUBLIC HEALTH & EPIDEMIOLOGY
├── NCD Management                [/ncd]
└── Disease Surveillance          [/surveillance]

GOVERNANCE, AUDIT & COMPLIANCE
├── ARS Committee                 [/ars]
├── Quality & Waste               [/quality]
├── Clinic Infra & Maintenance    [/infrastructure]
├── Reports & CSV                 [/reports]
├── Namma Compliance              [/compliance]
└── Audit Trail                   [/audit]

SYSTEM
├── Integrations (Mock)           [/integrations]
└── Alert Engine                  [/alerts]
```

---

## 4. Page Action Button RBAC Rules (Preventing Predictable HTTP 403)

| Page | Action / Button | Allowed Roles | Disallowed Roles | Enforced UI Behavior for Disallowed Roles |
|---|---|---|---|---|
| `/patients` | "+ Register New Patient" | `NURSE`, `HOSPITAL_ADMIN` | `DISTRICT_OFFICER`, `DOCTOR` | Button hidden; DHO/Doctor have READ-only directory view. |
| `/patients` | "Issue Token" (Row) | `NURSE`, `HOSPITAL_ADMIN` | `DISTRICT_OFFICER`, `DOCTOR` | Action hidden; tokens issued at nursing reception station. |
| `/queue` | "Issue New OPD Token" (Top) | `NURSE`, `HOSPITAL_ADMIN` | `DISTRICT_OFFICER`, `DOCTOR`, `LAB_TECHNICIAN`, `PHARMACIST` | Button disabled/hidden. |
| `/queue` | "Triage" (Row) | `NURSE` | `DOCTOR`, `LAB_TECHNICIAN`, `PHARMACIST`, `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Render static status "Awaiting Triage"; non-clickable. |
| `/queue` | "Consult" (Row) | `DOCTOR` | `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST`, `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Render static status "Awaiting Doctor"; non-clickable. |
| `/queue` | "Lab" (Row) | `LAB_TECHNICIAN`, `DOCTOR` | `NURSE`, `PHARMACIST`, `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Render static status "In Lab"; non-clickable. |
| `/queue` | "Dispense" (Row) | `PHARMACIST` | `NURSE`, `DOCTOR`, `LAB_TECHNICIAN`, `DISTRICT_OFFICER`, `HOSPITAL_ADMIN` | Render static status "In Pharmacy"; non-clickable. |
| `/lab` | "Collect Sample" | `LAB_TECHNICIAN` | `DOCTOR` | Button hidden; Doctor inspects specimens in read-only mode. |
| `/lab` | "Enter Result" | `LAB_TECHNICIAN` | `DOCTOR` | Button hidden; Doctor inspects verified results. |
| `/pharmacy` | "+ Add Vendor" | `HOSPITAL_ADMIN`, `PHARMACIST` | `DISTRICT_OFFICER` | Button hidden; DHO has read-only inventory oversight. |
| `/pharmacy` | "+ Create PO" | `HOSPITAL_ADMIN`, `PHARMACIST` | `DISTRICT_OFFICER` | Button hidden; DHO cannot create procurement commitments. |
| `/pharmacy` | "Dispense" (Rx) | `PHARMACIST` | `HOSPITAL_ADMIN`, `DISTRICT_OFFICER` | Button hidden; dispensing is restricted to licensed pharmacist. |
| `/referrals` | "Specialist Feedback" | `DOCTOR`, `HOSPITAL_ADMIN` | `DISTRICT_OFFICER` | Button hidden; DHO has read-only network transfer visibility. |
| `/infrastructure` | "Log Cylinder Refill" | `HOSPITAL_ADMIN` | `DISTRICT_OFFICER`, `PHARMACIST` | Button hidden; DHO and Pharmacist have read-only inspection. |
| `/infrastructure` | "Report Maintenance Ticket" | `HOSPITAL_ADMIN` | `DISTRICT_OFFICER`, `PHARMACIST` | Button hidden. |
| `/infrastructure` | "Assign Bed to Patient" | `HOSPITAL_ADMIN` | `DISTRICT_OFFICER`, `PHARMACIST` | Button hidden. |

---

## 5. Security & Isolation Invariants

1. **Facility Scoping**:
   - Operational roles (`HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST`) are strictly confined to their assigned facility (`request.user.assigned_facility_id`).
   - Cross-facility data access returns HTTP 404 or empty querysets.
2. **District Scoping**:
   - `DISTRICT_OFFICER` has district-wide read-only visibility across all facilities belonging to their assigned district (`request.user.assigned_district_id`).
   - Cross-district access (e.g. attempting to query another district's facility) returns HTTP 404 or filtered querysets.
3. **Mutation Immunity for District Officer**:
   - Direct mutation attempts by `DISTRICT_OFFICER` on any clinical, demographic, surveillance, or procurement endpoint (`POST`, `PUT`, `PATCH`, `DELETE`) are hard-blocked by backend `HasFacilityScope` with HTTP 403.
4. **UI Defense-in-Depth**:
   - Frontend route guards and action button filtering prevent predictable 403 errors and present a clean, role-tailored operational workspace.
   - Backend DRF permissions and facility checks remain the authoritative enforcement barrier.
