# Namma Clinic — Target Data Model Proposal

> **DOCUMENT CLASSIFICATION**: PROPOSED ARCHITECTURE — NOT YET IMPLEMENTED  
> **PURPOSE**: Technical specification for the future data model refactoring to eliminate dashboard discrepancies, integrate orphaned modules, establish strict referential integrity, and provide a unified operational-to-analytical pipeline.

---

## 1. Architectural Principles of the Target Model

1. **Strict Relational Traceability**:
   Every clinical action (triage, diagnosis, lab order, prescription item, referral, and follow-up) must branch directly from a single core `Encounter` (`Visit`) record.
2. **Foreign Key Referential Integrity for Prescriptions**:
   `PrescriptionItem` must reference `MedicineMaster` directly via Foreign Key, ensuring unambiguous inventory lookup and preventing drug name typographical errors.
3. **Integration of Maternal & Child RCH**:
   Register and migrate `MaternalRecord` and `ChildRecord` into the core schema, linking them to `Patient` and `Encounter`.
4. **Dynamic Event-Driven Public Health**:
   `DiseaseCase` and `NCDRecord` must be derived automatically from `Consultation` (ICD-10 codes) and `TriageVitals` (elevated blood pressure and blood glucose values), eliminating detached standalone records.
5. **Separation of Operational OLTP and Analytical Aggregates**:
   Implement database views / materialized aggregates for DHO dashboards to prevent costly table scans, eliminate client-side pagination errors, and discard hardcoded fallback values.

---

## 2. Proposed Target Data Model Architecture

```
+-----------------------------------------------------------------------------------+
|                            OPERATIONAL LAYER (OLTP)                               |
|                                                                                   |
|  [Citizen / Patient]                                                              |
|         |                                                                         |
|         v                                                                         |
|  [Encounter (Visit)] <---------- [OPD Priority Token]                             |
|         |                                                                         |
|         +---> [Triage Vitals] ---------> [Dynamic Clinical Risk Flag Trigger]     |
|         |                                                                         |
|         +---> [Consultation / EMR] ----> [ICD-10 Master Coding]                   |
|         |           |                                                             |
|         |           +---> [Lab Order] -> [Specimen Barcode] -> [Verified Result]  |
|         |           |                                                             |
|         |           +---> [Prescription] -> [Prescription Item (FK Medicine)]     |
|         |           |                                     |                       |
|         |           |                                     v                       |
|         |           |                       [FEFO Batch Allocation Ledger]        |
|         |           |                                                             |
|         |           +---> [Closed-Loop Specialist Referral]                       |
|         |                                                                         |
|         +---> [Scheduled Follow-Up Review]                                        |
+-----------------------------------------------------------------------------------+
                                          |
                                          | Trigger / View Materialization
                                          v
+-----------------------------------------------------------------------------------+
|                           ANALYTICS & REPORTING LAYER                             |
|                                                                                   |
|  +---------------------------+  +--------------------------+                      |
|  | Daily Clinic Aggregates   |  | Ward Epidemic Surveillance|                      |
|  | - Footfall & Queues       |  | - 7-Day Fever Cluster Map|                      |
|  | - Consultations by ICD-10 |  | - Threshold Anomaly Score|                      |
|  | - Completed Referrals     |  +--------------------------+                      |
|  +---------------------------+                                                    |
|                |                                                                  |
|                v                                                                  |
|  +---------------------------------------------------------+                      |
|  | DHO & Executive Command Centre Dashboards               |                      |
|  | - 100% Database-Derived Metrics (Zero Hardcoding)       |                      |
|  | - Multi-Tier District -> Zone -> Ward -> Clinic Drill-down|                     |
|  +---------------------------------------------------------+                      |
+-----------------------------------------------------------------------------------+
```

---

## 3. Proposed Target ERD

> **LABEL**: PROPOSED — NOT YET IMPLEMENTED

```mermaid
erDiagram
    %% Core Citizen & Household
    HOUSEHOLD ||--o{ PATIENT : "encompasses"
    WARD ||--o{ HOUSEHOLD : "locates"
    WARD ||--o{ PATIENT : "resides_in"
    FACILITY ||--o{ PATIENT : "primary_registration"

    %% Clinical Core Encounter Pipeline
    PATIENT ||--o{ ENCOUNTER : "attends"
    FACILITY ||--o{ ENCOUNTER : "hosts"
    USER ||--o{ ENCOUNTER : "assigned_clinician"
    
    ENCOUNTER ||--|| TOKEN : "token_allocated"
    ENCOUNTER ||--|| TRIAGE_RECORD : "vitals_captured"
    ENCOUNTER ||--|| CONSULTATION_RECORD : "clinical_assessment"
    
    %% Diagnostics & Clinical Tools
    CONSULTATION_RECORD ||--o{ DIAGNOSIS_ENTRY : "diagnoses"
    ICD10_MASTER ||--o{ DIAGNOSIS_ENTRY : "codes"
    
    CONSULTATION_RECORD ||--o{ LAB_REQUEST : "orders"
    LAB_TEST_CATALOGUE ||--o{ LAB_REQUEST : "specifies"
    LAB_REQUEST ||--|| SPECIMEN_SAMPLE : "draws"
    LAB_REQUEST ||--|| LAB_RESULT_REPORT : "produces"

    %% Pharmacy & Inventory
    CONSULTATION_RECORD ||--|| PRESCRIPTION_ORDER : "authorizes"
    PRESCRIPTION_ORDER ||--o{ PRESCRIPTION_LINE_ITEM : "specifies"
    MEDICINE_CATALOGUE ||--o{ PRESCRIPTION_LINE_ITEM : "references_generic"
    
    PRESCRIPTION_LINE_ITEM ||--o{ DISPENSATION_RECORD : "allocates_fefo"
    MEDICINE_BATCH_INVENTORY ||--o{ DISPENSATION_RECORD : "deducts_stock"
    FACILITY ||--o{ MEDICINE_BATCH_INVENTORY : "stores"
    MEDICINE_CATALOGUE ||--o{ MEDICINE_BATCH_INVENTORY : "categorizes"
    VENDOR_SUPPLIER ||--o{ MEDICINE_BATCH_INVENTORY : "procures_from"

    %% Continuity of Care & Referral Network
    ENCOUNTER ||--o{ SPECIALIST_REFERRAL : "initiates_referral"
    FACILITY ||--o{ SPECIALIST_REFERRAL : "originating_clinic"
    FACILITY ||--o{ SPECIALIST_REFERRAL : "destination_hospital"
    SPECIALIST_REFERRAL ||--|| REFERRAL_COUNTER_RESPONSE : "completes_loop"
    
    ENCOUNTER ||--o{ FOLLOWUP_APPOINTMENT : "schedules_review"
    SPECIALIST_REFERRAL ||--o{ FOLLOWUP_APPOINTMENT : "post_referral_return"

    %% Public Health Integrations
    PATIENT ||--o{ MATERNAL_CARE_RECORD : "maternal_profile"
    ENCOUNTER ||--o{ MATERNAL_CARE_RECORD : "anc_visit"
    PATIENT ||--o{ CHILD_HEALTH_RECORD : "child_profile"
    
    ENCOUNTER ||--o{ EPIDEMIC_SURVEILLANCE_CASE : "detects_syndrome"
    WARD ||--o{ EPIDEMIC_SURVEILLANCE_CASE : "clusters_in"
    
    PATIENT ||--o{ NCD_LONGITUDINAL_COHORT : "enrolled_in"
    ENCOUNTER ||--o{ NCD_LONGITUDINAL_COHORT : "screening_trigger"

    %% Entities
    HOUSEHOLD {
        uuid id PK
        string household_code
        string head_name
        int member_count
        string vulnerability_tier
    }

    PATIENT {
        uuid id PK
        string uhid UK
        string abha_number
        string abha_address
        string full_name
        string gender
        date date_of_birth
        string mobile_primary
    }

    ENCOUNTER {
        uuid id PK
        uuid patient_id FK
        uuid facility_id FK
        uuid clinician_id FK
        string encounter_number UK
        date encounter_date
        string stage_queue
        string encounter_status
        datetime checkin_time
        datetime discharge_time
    }

    TRIAGE_RECORD {
        uuid id PK
        uuid encounter_id FK
        int systolic_bp
        int diastolic_bp
        decimal blood_glucose_mgdl
        decimal temperature_f
        int spo2_percentage
        decimal bmi
        boolean high_risk_flag
    }

    CONSULTATION_RECORD {
        uuid id PK
        uuid encounter_id FK
        uuid doctor_id FK
        text chief_complaints
        text clinical_notes
        text treatment_instructions
    }

    DIAGNOSIS_ENTRY {
        uuid id PK
        uuid consultation_id FK
        string icd10_code FK
        string clinical_certainty
    }

    ICD10_MASTER {
        string icd10_code PK
        string description
        string disease_category
    }

    PRESCRIPTION_ORDER {
        uuid id PK
        uuid consultation_id FK
        string prescription_number UK
        string status
    }

    PRESCRIPTION_LINE_ITEM {
        uuid id PK
        uuid prescription_id FK
        uuid medicine_id FK
        string dosage_pattern
        int duration_days
        int total_quantity_prescribed
    }

    MEDICINE_CATALOGUE {
        uuid id PK
        string generic_name UK
        string strength
        string dosage_form
        int min_stock_threshold
        int reorder_level
    }

    MEDICINE_BATCH_INVENTORY {
        uuid id PK
        uuid facility_id FK
        uuid medicine_id FK
        string batch_number
        date expiry_date
        int current_quantity
    }

    DISPENSATION_RECORD {
        uuid id PK
        uuid prescription_line_item_id FK
        uuid batch_id FK
        int quantity_dispensed
        datetime dispensed_at
    }

    SPECIALIST_REFERRAL {
        uuid id PK
        uuid encounter_id FK
        uuid origin_facility_id FK
        uuid destination_facility_id FK
        string urgency
        string referral_reason
        string transfer_status
    }

    REFERRAL_COUNTER_RESPONSE {
        uuid id PK
        uuid referral_id FK
        text specialist_findings
        text counter_advice_to_primary_mo
        datetime response_time
    }

    FOLLOWUP_APPOINTMENT {
        uuid id PK
        uuid encounter_id FK
        uuid patient_id FK
        date appointment_due_date
        string care_category
        string review_status
    }

    MATERNAL_CARE_RECORD {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        string rch_number
        date lmp_date
        date edd_date
        boolean high_risk_pregnancy_flag
    }

    CHILD_HEALTH_RECORD {
        uuid id PK
        uuid patient_id FK
        decimal birth_weight_kg
        string immunization_status
        string growth_faltering_grade
    }
```

---

## 4. Operational Transition & Migration Strategy

1. **Step 1 — Entity Normalization**:
   - Introduce `ICD10Master` and convert string-based diagnosis codes to normalized relations.
   - Refactor `PrescriptionItem` to enforce `medicine_id` foreign key against `MedicineMaster`.
2. **Step 2 — Encounter Anchoring**:
   - Add `encounter_id` foreign key to `Referral` and `FollowUp`.
3. **Step 3 — RCH Module Activation**:
   - Register `apps.maternal` and `apps.child` in `INSTALLED_APPS`, generate migration files, and connect serializers to `Patient` and `Encounter`.
4. **Step 4 — View Materialization for Dashboards**:
   - Create SQL views for DHO aggregate footfall, low stock, and referral statistics to eliminate client-side slicing and backend fallbacks.
