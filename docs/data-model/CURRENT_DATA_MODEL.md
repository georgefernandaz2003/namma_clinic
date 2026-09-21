# Namma Clinic — Current Database & Data Model Analysis

## 1. Overview of the Current Data Model

The current data model is managed via Django ORM migrations and deployed to an SQLite database.
The source code defines **40 Django models across 24 apps**, of which **38 models across 22 apps are actively registered in `INSTALLED_APPS`** and have active database tables.

Two apps (`apps.child` and `apps.maternal`) define models (`ChildRecord` and `MaternalRecord`), but are **not registered in `INSTALLED_APPS`**, have no migrations, and do not exist in the physical database schema.

---

## 2. Complete Entity Inventory

Below is the exhaustive inventory of all 38 active database entities in the repository:

### 2.1 Identity & Governance Layer

#### 1. Entity: `User`
- **Table Name**: `accounts_user`
- **Primary Key**: `id` (BigAutoField / Integer Auto-Increment)
- **Foreign Keys**:
  - `assigned_facility_id` $\rightarrow$ `facilities_facility.id` (Nullable, `SET_NULL`, `related_name='assigned_users'`)
  - `assigned_district_id` $\rightarrow$ `geography_district.id` (Nullable, `SET_NULL`, `related_name='assigned_users'`)
- **Key Fields**: `username` (unique), `email`, `password`, `full_name`, `phone`, `role` (`RoleChoices`), `is_active`, `is_staff`, `is_superuser`, `date_joined`
- **Status / Role Choices**: `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST`
- **Audit Fields**: `date_joined`, `last_login`
- **Source of Data**: Seed command (`seed_demo.py`), Admin console
- **Used by**: Authentication, Triage, Consultation, Prescriptions, Lab verification, Pharmacy, Referrals, Audit logs

#### 2. Entity: `AuditLog`
- **Table Name**: `audit_auditlog`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `user_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (Nullable, `SET_NULL`)
- **Key Fields**: `username_snapshot`, `action`, `details`, `ip_address`, `timestamp`
- **Source of Data**: `AuditLogMiddleware` and application controllers
- **Used by**: Security auditing, compliance reporting

#### 3. Entity: `ComplianceItem`
- **Table Name**: `compliance_complianceitem`
- **Primary Key**: `id`
- **Foreign Keys**: None
- **Key Fields**: `requirement_id` (Unique), `requirement_text`, `source_document`, `classification`, `application_module`, `status`, `explanation`
- **Status Values**: `FULLY_COVERED`, `PARTIALLY_COVERED`, `NOT_IMPLEMENTED`, `OUT_OF_DIGITAL_SCOPE`
- **Source of Data**: `seed_demo.py` (Static reference requirements)
- **Used by**: Government compliance audit page

#### 4. Entity: `IntegrationConfiguration`
- **Table Name**: `integrations_integrationconfiguration`
- **Primary Key**: `id`
- **Foreign Keys**: None
- **Key Fields**: `system_name` (Unique, e.g. ABDM, ABHA, HMIS, E_AUSHADA), `display_name`, `status`, `last_sync_time`, `sync_status`, `notes`
- **Status Values**: `NOT_CONFIGURED`, `MOCK`, `READY`, `CONNECTED`
- **Source of Data**: `seed_demo.py`
- **Used by**: External integrations monitor page

---

### 2.2 Geography & Facility Hierarchy Layer

#### 5. Entity: `State`
- **Table Name**: `geography_state`
- **Primary Key**: `id`
- **Key Fields**: `name` (Unique), `code` (Unique)

#### 6. Entity: `District`
- **Table Name**: `geography_district`
- **Primary Key**: `id`
- **Foreign Keys**: `state_id` $\rightarrow$ `geography_state.id` (CASCADE)
- **Key Fields**: `name`, `code` (Unique)

#### 7. Entity: `Zone`
- **Table Name**: `geography_zone`
- **Primary Key**: `id`
- **Foreign Keys**: `district_id` $\rightarrow$ `geography_district.id` (CASCADE)
- **Key Fields**: `name`, `code`

#### 8. Entity: `Ward`
- **Table Name**: `geography_ward`
- **Primary Key**: `id`
- **Foreign Keys**: `zone_id` $\rightarrow$ `geography_zone.id` (CASCADE)
- **Key Fields**: `ward_number`, `name`, `population`, `slum_population`

#### 9. Entity: `Facility`
- **Table Name**: `facilities_facility`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `parent_facility_id` $\rightarrow$ `facilities_facility.id` (Nullable, Self-referential hierarchy)
  - `state_id` $\rightarrow$ `geography_state.id` (CASCADE)
  - `district_id` $\rightarrow$ `geography_district.id` (CASCADE)
  - `zone_id` $\rightarrow$ `geography_zone.id` (Nullable, `SET_NULL`)
  - `ward_id` $\rightarrow$ `geography_ward.id` (Nullable, `SET_NULL`)
- **Key Fields**: `facility_code` (Unique), `facility_name`, `facility_type`, `city_or_ulb`, `urban_rural`, `address`, `latitude`, `longitude`, `population_served`, `vulnerable_population`, `bed_capacity`, `emergency_available`, `lab_available`, `pharmacy_available`, `teleconsultation_available`, `services`, `specialists`, `status`
- **Facility Types**: `MAIN_HOSPITAL`, `REFERRAL_HOSPITAL`, `SECONDARY_HOSPITAL`, `UPHC`, `NAMMA_CLINIC`, `URBAN_CLINIC`, `RURAL_CLINIC`, `VILLAGE_CLINIC`, `DIAGNOSTIC_CENTER`, `OTHER`
- **Audit Fields**: `created_at`, `updated_at`

#### 10. Entity: `FacilityRelationship`
- **Table Name**: `facilities_facilityrelationship`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `source_facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `destination_facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `relationship_type` (PARENT, REFERRAL, SPECIALIST, EMERGENCY, DIAGNOSTIC, TELECONSULTATION), `service`, `priority`, `distance_km`, `active`, `notes`
- **Audit Fields**: `created_at`

#### 11. Entity: `FacilityOxygenSupply`
- **Table Name**: `facilities_facilityoxygensupply`
- **Primary Key**: `id`
- **Foreign Keys**: `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `oxygen_source`, `total_cylinders`, `active_cylinders`, `empty_cylinders`, `current_pressure_psi`, `fill_percentage`, `status`, `notes`, `last_inspected`

#### 12. Entity: `FacilityConsumableInventory`
- **Table Name**: `facilities_facilityconsumableinventory`
- **Primary Key**: `id`
- **Foreign Keys**: `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `item_name`, `category`, `unit_of_measure`, `current_stock`, `min_threshold`, `reorder_status`, `last_restocked`

#### 13. Entity: `FacilityMaintenanceTicket`
- **Table Name**: `facilities_facilitymaintenanceticket`
- **Primary Key**: `id`
- **Foreign Keys**: `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `ticket_number` (Unique), `category`, `equipment_or_area`, `priority`, `description`, `reported_by`, `assigned_technician`, `status`, `created_at`, `resolved_at`

#### 14. Entity: `FacilityBedCapacity`
- **Table Name**: `facilities_facilitybedcapacity`
- **Primary Key**: `id`
- **Foreign Keys**: `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `bed_category`, `total_beds`, `occupied_beds`, `cleaning_in_progress`, `under_maintenance`, `notes`

#### 15. Entity: `FacilityBedAllocation`
- **Table Name**: `facilities_facilitybedallocation`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `patient_id` $\rightarrow$ `patients_patient.id` (Nullable, `SET_NULL`)
- **Key Fields**: `bed_number`, `bed_category`, `patient_name`, `attending_doctor`, `status`, `allocated_at`, `discharged_at`

---

### 2.3 Patient & OPD Queue Layer

#### 16. Entity: `Patient`
- **Table Name**: `patients_patient`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `registered_at_facility_id` $\rightarrow$ `facilities_facility.id` (Nullable, `SET_NULL`)
  - `district_id` $\rightarrow$ `geography_district.id` (Nullable, `SET_NULL`)
  - `ward_id` $\rightarrow$ `geography_ward.id` (Nullable, `SET_NULL`)
- **Key Fields**: `patient_id` (Unique), `name`, `date_of_birth`, `age`, `gender`, `mobile`, `address`, `ABHA_ID_DEMO`, `emergency_contact`, `vulnerability_information`, `registration_date`
- **Audit Fields**: `registration_date` (auto_now_add)

#### 17. Entity: `Household`
- **Table Name**: `patients_household`
- **Primary Key**: `id`
- **Foreign Keys**: `ward_id` $\rightarrow$ `geography_ward.id` (Nullable, `SET_NULL`)
- **Key Fields**: `household_id` (Unique), `head_name`, `address`, `members_count`, `vulnerable_category`, `created_at`

#### 18. Entity: `PatientDocument`
- **Table Name**: `patients_patientdocument`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (Nullable, `SET_NULL`)
  - `uploaded_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `title`, `document_type`, `file`, `file_name`, `file_size`, `mime_type`, `document_date`, `description`, `status`
- **Audit Fields**: `uploaded_at`

#### 19. Entity: `Visit` (Encounter)
- **Table Name**: `visits_visit`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `assigned_doctor_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `visit_id` (Unique), `visit_date`, `opd_date` (Indexed), `visit_type`, `priority`, `current_queue`, `status`, `chief_complaint`
- **Stage Timestamps**: `arrival_time`, `triage_start_time`, `triage_end_time`, `consultation_start_time`, `consultation_end_time`, `completed_time`

#### 20. Entity: `Token`
- **Table Name**: `visits_token`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `visit_id` $\rightarrow$ `visits_visit.id` (One-to-One, CASCADE)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Unique Constraints**: `['facility', 'date', 'token_number']`
- **Key Fields**: `token_number`, `date`, `priority`, `status`

#### 21. Entity: `VisitStatusHistory`
- **Table Name**: `visits_visitstatushistory`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `visit_id` $\rightarrow$ `visits_visit.id` (CASCADE)
  - `performed_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `from_status`, `to_status`, `queue`, `performed_by_role`, `notes`, `timestamp`

---

### 2.4 Clinical, Diagnostic & Pharmacy Layer

#### 22. Entity: `TriageVitals`
- **Table Name**: `triage_triagevitals`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `visit_id` $\rightarrow$ `visits_visit.id` (One-to-One, CASCADE)
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `nurse_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `blood_pressure_systolic`, `blood_pressure_diastolic`, `pulse_bpm`, `temperature_f`, `spo2_percent`, `respiratory_rate`, `height_cm`, `weight_kg`, `bmi`, `blood_glucose_mgdl`
- **Risk Flags**: `high_bp_flag`, `high_glucose_flag`, `fever_flag`, `low_spo2_flag`, `pregnancy_high_risk_flag`, `emergency_flag`, `ncd_risk_flag`
- **Audit Fields**: `created_at`

#### 23. Entity: `Consultation`
- **Table Name**: `consultations_consultation`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `visit_id` $\rightarrow$ `visits_visit.id` (One-to-One, CASCADE)
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `doctor_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `chief_complaint`, `clinical_history`, `clinical_assessment`, `diagnosis_code`, `diagnosis_name`, `treatment_plan`, `follow_up_date`, `clinical_notes`, `created_at`

#### 24. Entity: `Prescription`
- **Table Name**: `consultations_prescription`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `consultation_id` $\rightarrow$ `consultations_consultation.id` (One-to-One, CASCADE)
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `doctor_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `date`, `status` (`ACTIVE`, `PENDING`, `DISPENSED`), `notes`

#### 25. Entity: `PrescriptionItem`
- **Table Name**: `consultations_prescriptionitem`
- **Primary Key**: `id`
- **Foreign Keys**: `prescription_id` $\rightarrow$ `consultations_prescription.id` (CASCADE)
- **Key Fields**: `medicine_name` (CharField string — **NOT an FK to MedicineMaster**), `dosage`, `frequency`, `duration_days`, `quantity`, `status` (`PENDING`, `DISPENSED`)

#### 26. Entity: `LabTestMaster`
- **Table Name**: `laboratory_labtestmaster`
- **Primary Key**: `id`
- **Key Fields**: `code` (Unique), `name`, `category`, `reference_range`, `unit`

#### 27. Entity: `LabOrder`
- **Table Name**: `laboratory_laborder`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `consultation_id` $\rightarrow$ `consultations_consultation.id` (Nullable, `SET_NULL`)
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `doctor_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `test_master_id` $\rightarrow$ `laboratory_labtestmaster.id` (CASCADE)
- **Key Fields**: `order_date`, `status` (`ORDERED`, `SAMPLE_COLLECTED`, `RESULT_ENTRY`, `VERIFIED`)

#### 28. Entity: `LabSample`
- **Table Name**: `laboratory_labsample`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `lab_order_id` $\rightarrow$ `laboratory_laborder.id` (One-to-One, CASCADE)
  - `collected_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `sample_type`, `sample_code` (Unique), `collected_at`

#### 29. Entity: `LabResult`
- **Table Name**: `laboratory_labresult`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `lab_order_id` $\rightarrow$ `laboratory_laborder.id` (One-to-One, CASCADE)
  - `verified_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `result_value`, `unit`, `reference_range`, `interpretation_flag` (`NORMAL`, `HIGH`, `LOW`, `CRITICAL`), `verified_at`, `notes`

#### 30. Entity: `MedicineMaster`
- **Table Name**: `pharmacy_medicinemaster`
- **Primary Key**: `id`
- **Key Fields**: `generic_name`, `brand_name`, `strength`, `dosage_form`, `unit`, `category`, `minimum_stock`, `reorder_level`, `description`

#### 31. Entity: `Vendor`
- **Table Name**: `pharmacy_vendor`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `facility_id` $\rightarrow$ `facilities_facility.id` (Nullable, CASCADE)
  - `created_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `vendor_name`, `contact_person`, `phone`, `email`, `address`, `gst_number`, `status`
- **Audit Fields**: `created_at`, `updated_at`

#### 32. Entity: `MedicineBatch`
- **Table Name**: `pharmacy_medicinebatch`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `medicine_id` $\rightarrow$ `pharmacy_medicinemaster.id` (CASCADE)
  - `vendor_id` $\rightarrow$ `pharmacy_vendor.id` (Nullable, `SET_NULL`)
- **Key Fields**: `batch_number`, `supplier`, `received_date`, `mfg_date`, `expiry_date`, `quantity`, `unit_cost`, `status` (`ACTIVE`, `LOW_STOCK`, `EXPIRING_SOON`, `EXPIRED`, `EXHAUSTED`)
- **Ordering**: `['expiry_date']` (Enforces FEFO - First Expiry First Out)

#### 33. Entity: `PurchaseOrder`
- **Table Name**: `pharmacy_purchaseorder`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `vendor_id` $\rightarrow$ `pharmacy_vendor.id` (CASCADE)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `created_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
  - `approved_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
  - `rejected_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `po_number` (Unique), `order_date`, `expected_delivery_date`, `status`, `total_amount`, `notes`, `rejection_reason`

#### 34. Entity: `PurchaseOrderItem`
- **Table Name**: `pharmacy_purchaseorderitem`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `purchase_order_id` $\rightarrow$ `pharmacy_purchaseorder.id` (CASCADE)
  - `medicine_id` $\rightarrow$ `pharmacy_medicinemaster.id` (CASCADE)
- **Key Fields**: `ordered_quantity`, `received_quantity`, `unit_price`, `total_price`

#### 35. Entity: `InventoryTransaction`
- **Table Name**: `pharmacy_inventorytransaction`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `medicine_id` $\rightarrow$ `pharmacy_medicinemaster.id` (CASCADE)
  - `batch_id` $\rightarrow$ `pharmacy_medicinebatch.id` (Nullable, `SET_NULL`)
  - `created_by_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `transaction_type` (`PURCHASE_RECEIVED`, `DISPENSED`, `RETURNED`, `ADJUSTMENT`, `DAMAGED`, `EXPIRED`), `quantity`, `reference_id`, `created_at`, `notes`

---

### 2.5 Referral, Continuity of Care & Public Health Layer

#### 36. Entity: `Referral`
- **Table Name**: `referrals_referral`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `source_facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `destination_facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `referring_doctor_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `referral_id` (Unique), `reason`, `clinical_summary`, `required_service`, `urgency`, `referral_date`, `status`
- **Important Gotcha**: **No Foreign Key to `Visit` or `Consultation`**!

#### 37. Entity: `ReferralResponse`
- **Table Name**: `referrals_referralresponse`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `referral_id` $\rightarrow$ `referrals_referral.id` (One-to-One, CASCADE)
  - `hospital_doctor_id` $\rightarrow$ `accounts_user.id` (Nullable, `SET_NULL`)
- **Key Fields**: `specialist_findings`, `treatment_summary`, `return_advice`, `responded_at`

#### 38. Entity: `FollowUp`
- **Table Name**: `referrals_followup`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `referral_id` $\rightarrow$ `referrals_referral.id` (Nullable, `SET_NULL`)
  - `visit_id` $\rightarrow$ `visits_visit.id` (Nullable, `SET_NULL`)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `category` (NCD, MATERNAL_ANC, REFERRAL), `due_date`, `status` (`PENDING`, `DUE_TODAY`, `OVERDUE`, `COMPLETED`), `notes`

#### 39. Entity: `NCDRecord`
- **Table Name**: `ncd_ncdrecord`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
- **Key Fields**: `screening_date`, `hypertension_diagnosed`, `diabetes_diagnosed`, `risk_level`, `treatment_status`, `control_status`, `last_bp`, `last_glucose`, `next_followup_due`

#### 40. Entity: `DiseaseCase`
- **Table Name**: `surveillance_diseasecase`
- **Primary Key**: `id`
- **Foreign Keys**:
  - `patient_id` $\rightarrow$ `patients_patient.id` (CASCADE)
  - `facility_id` $\rightarrow$ `facilities_facility.id` (CASCADE)
  - `ward_id` $\rightarrow$ `geography_ward.id` (Nullable, `SET_NULL`)
- **Key Fields**: `disease_name`, `report_date`, `severity`, `status`, `notes`

---

### 2.6 Community, Governance & Telemedicine Layer

#### 41. Entity: `Teleconsultation`
- **Table Name**: `telemedicine_teleconsultation`
- **Foreign Keys**: `patient_id`, `clinic_facility_id`, `hub_facility_id`, `requesting_doctor_id`, `specialist_doctor_id`

#### 42. Entity: `OutreachActivity`
- **Table Name**: `outreach_outreachactivity`
- **Foreign Keys**: `facility_id`, `ward_id`

#### 43. Entity: `WellnessSession`
- **Table Name**: `wellness_wellnesssession`
- **Foreign Keys**: `facility_id`

#### 44. Entities: `ARSMember`, `ARSMeeting`, `ARSActionItem`
- **Table Names**: `ars_arsmember`, `ars_arsmeeting`, `ars_arsactionitem`
- **Foreign Keys**: `facility_id`, `meeting_id`

#### 45. Entities: `QualityChecklist`, `BiomedicalWasteLog`
- **Table Names**: `quality_qualitychecklist`, `quality_biomedicalwastelog`
- **Foreign Keys**: `facility_id`, `inspected_by_id`, `handed_over_by_id`

#### 46. Entity: `Alert`
- **Table Name**: `alerts_alert`
- **Foreign Keys**: `facility_id`, `patient_id` (Nullable), `assigned_user_id` (Nullable)

#### 47. Entity: `ReportExportLog`
- **Table Name**: `reports_reportexportlog`
- **Foreign Keys**: `facility_id`, `generated_by_id`

---

## 3. Relationship Cardinality Matrix

| Relationship Type | Source Entity | Target Entity | Relationship Path / Field |
| :--- | :--- | :--- | :--- |
| **ONE-TO-ONE** | `Visit` | `Token` | `visit.token` $\leftrightarrow$ `token.visit` |
| **ONE-TO-ONE** | `Visit` | `TriageVitals` | `visit.triage` $\leftrightarrow$ `triage.visit` |
| **ONE-TO-ONE** | `Visit` | `Consultation` | `visit.consultation` $\leftrightarrow$ `consultation.visit` |
| **ONE-TO-ONE** | `Consultation` | `Prescription` | `consultation.prescription` $\leftrightarrow$ `prescription.consultation` |
| **ONE-TO-ONE** | `LabOrder` | `LabSample` | `lab_order.sample` $\leftrightarrow$ `lab_sample.lab_order` |
| **ONE-TO-ONE** | `LabOrder` | `LabResult` | `lab_order.result` $\leftrightarrow$ `lab_result.lab_order` |
| **ONE-TO-ONE** | `Referral` | `ReferralResponse` | `referral.response` $\leftrightarrow$ `referralresponse.referral` |
| **ONE-TO-MANY** | `Facility` | `Facility` (Children) | `facility.children` $\leftrightarrow$ `child.parent_facility` |
| **ONE-TO-MANY** | `Facility` | `User` | `facility.assigned_users` |
| **ONE-TO-MANY** | `District` | `Facility` | `district.facilities` |
| **ONE-TO-MANY** | `Patient` | `Visit` | `patient.visits` |
| **ONE-TO-MANY** | `Patient` | `LabOrder` | `patient.lab_orders` |
| **ONE-TO-MANY** | `Patient` | `Referral` | `patient.referrals` |
| **ONE-TO-MANY** | `Patient` | `FollowUp` | `patient.followups` |
| **ONE-TO-MANY** | `Patient` | `PatientDocument` | `patient.documents` |
| **ONE-TO-MANY** | `Prescription` | `PrescriptionItem` | `prescription.items` |
| **ONE-TO-MANY** | `MedicineMaster` | `MedicineBatch` | `medicine.batches` |
| **ONE-TO-MANY** | `Vendor` | `PurchaseOrder` | `vendor.purchase_orders` |
| **ONE-TO-MANY** | `PurchaseOrder` | `PurchaseOrderItem` | `purchase_order.items` |
| **ONE-TO-MANY** | `ARSMeeting` | `ARSActionItem` | `meeting.action_items` |
| **MANY-TO-MANY** | `User` | `Group` | Django auth `accounts_user_groups` |
| **MANY-TO-MANY** | `User` | `Permission` | Django auth `accounts_user_user_permissions` |
