# Namma Clinic — Frontend API Contract (v1)

**Target Architecture:** Local Laptop (`PostgreSQL 16` -> `Django 4.2 / DRF` -> `React / Vite` -> `Browser`)  
**Base URL:** `http://127.0.0.1:8000/api/v1/`  
**Authentication Root:** `http://127.0.0.1:8000/api/auth/`  
**API Specification Version:** 1.0.0  
**Authority:** Authoritative Django/DRF Serializers & Domain Service Layer

---

## 1. Global API Conventions

### 1.1 Headers
All authenticated API calls must include:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

### 1.2 Pagination Envelope
All `GET` list endpoints return the standard DRF paginated envelope:
```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/v1/patients/?page=2",
  "previous": null,
  "results": []
}
```
*Default Page Size:* 20 items.

### 1.3 Standard Error Format
DRF and the custom `domain_exception_handler` produce standard error bodies:

#### Validation Error (`400 Bad Request`)
```json
{
  "field_name": [
    "This field is required."
  ]
}
```

#### Domain Conflict / Invariant Violation (`409 Conflict` or `400 Bad Request`)
```json
{
  "error": "Prescription #3 is in status 'PENDING_VERIFICATION'. Only VERIFIED or ACTIVE prescriptions can be dispensed.",
  "code": "VALIDATION_ERROR",
  "details": {}
}
```

#### Authentication Error (`401 Unauthorized`)
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

#### Permission / Facility Isolation Error (`403 Forbidden`)
```json
{
  "detail": "Cross-facility operation blocked. User is not assigned to facility #2."
}
```

---

## 2. Authentication & IAM (`/api/auth/` & `/api/v1/accounts/`)

### 2.1 Login (`POST /api/auth/token/`)
Exchanges credentials for JWT access and refresh token pair.

- **Request:**
  ```json
  {
    "username": "localdoc",
    "password": "DoctorPassword123!"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
    "access": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```
- **Security Invariant:** Passwords, password hashes, and secrets are NEVER returned in response payloads.

### 2.2 Token Refresh (`POST /api/auth/token/refresh/`)
- **Request:**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```

### 2.3 Staff Profiles (`GET /api/v1/accounts/staff-profiles/`)
- **Allowed Roles:** All Active Staff
- **Response Item Fields:**
  - `id` (int, read-only)
  - `employee_id` (string, required)
  - `designation` (string, required)
  - `department` (int ID, optional)
  - `status` (string: `ACTIVE`, `ON_LEAVE`, `SUSPENDED`, `RESIGNED`, `RETIRED`)
  - `person` (int ID, required)

### 2.4 Staff Status Mutation (`POST /api/v1/accounts/staff-profiles/{id}/update-status/`)
- **Allowed Roles:** `HOSPITAL_ADMIN`, `DISTRICT_OFFICER`
- **Request:**
  ```json
  {
    "status": "ON_LEAVE"
  }
  ```

### 2.5 Role Assignment (`POST /api/v1/accounts/role-assignments/`)
- **Allowed Roles:** `HOSPITAL_ADMIN`, `DISTRICT_OFFICER`
- **Request:**
  ```json
  {
    "staff": 1,
    "role": 2,
    "effective_from": "2026-09-24",
    "effective_to": null
  }
  ```

### 2.6 Facility Transfer (`POST /api/v1/accounts/facility-assignments/transfer/`)
- **Allowed Roles:** `HOSPITAL_ADMIN`, `DISTRICT_OFFICER`
- **Request:**
  ```json
  {
    "staff_profile_id": 1,
    "new_facility_id": 2,
    "new_department_id": null,
    "effective_date": "2026-10-01"
  }
  ```

---

## 3. Organization & Facilities (`/api/v1/organization/`)

### 3.1 Facility Directory (`GET /api/v1/organization/facilities/`)
- **Query Parameters:** `?facility_type=PRIMARY_HEALTH_CENTRE&district=1`
- **Response Item Fields:**
  - `id` (int)
  - `facility_code` (string)
  - `facility_name` (string)
  - `facility_type` (string: `PRIMARY_HEALTH_CENTRE`, `COMMUNITY_HEALTH_CENTRE`, `SUB_CENTRE`, `URBAN_PRIMARY_HEALTH_CENTRE`, `DISTRICT_HOSPITAL`, `TERTIARY_HOSPITAL`)
  - `state` (int ID)
  - `district` (int ID)
  - `zone` (int ID, nullable)
  - `ward` (int ID, nullable)
  - `status` (string: `ACTIVE`, `INACTIVE`)
  - `emergency_available` (bool)
  - `lab_available` (bool)
  - `pharmacy_available` (bool)

---

## 4. Patients (`/api/v1/patients/`)

### 4.1 Register Patient (`POST /api/v1/patients/`)
- **Allowed Roles:** `DOCTOR`, `NURSE`, `HOSPITAL_ADMIN`
- **Request:**
  ```json
  {
    "name": "Murugan Kumar",
    "age": 35,
    "gender": "MALE",
    "mobile": "9840123456",
    "address": "42 South Mada Street, Mylapore",
    "registered_at_facility": 1
  }
  ```
  *Validation Rules:*
  - `name`: string, required
  - `gender`: choices: `MALE`, `FEMALE`, `OTHER`
  - `age`: integer (0-150)
  - `registered_at_facility`: integer ID, must match staff permitted facility scope
- **Response (`201 Created`):**
  ```json
  {
    "id": 2,
    "patient_id": "PAT-20260924-C9CE94",
    "person": 12,
    "name": "Murugan Kumar",
    "age": 35,
    "gender": "MALE",
    "mobile": "9840123456",
    "address": "42 South Mada Street, Mylapore",
    "registered_at_facility": 1,
    "registration_date": "2026-09-24T11:06:53Z"
  }
  ```
  *Note:* `patient_id` is server-generated and read-only.

---

## 5. Visits & Tokens (`/api/v1/visits/`)

### 5.1 Create Visit (`POST /api/v1/visits/`)
- **Request:**
  ```json
  {
    "patient": 2,
    "facility": 1,
    "visit_type": "OUTPATIENT"
  }
  ```
  *Choices for `visit_type`:* `OUTPATIENT`, `EMERGENCY`, `FOLLOW_UP`, `REFERRAL_ARRIVAL`
- **Response (`201 Created`):**
  ```json
  {
    "id": 6,
    "visit_id": "VIS-20260924-44F838",
    "patient": 2,
    "facility": 1,
    "visit_type": "OUTPATIENT",
    "opd_date": "2026-09-24",
    "current_queue": "REGISTRATION",
    "status": "IN_PROGRESS",
    "token_number": null
  }
  ```

### 5.2 Allocate OPD Token (`POST /api/v1/visits/{id}/issue-opd-token/`)
- **Response (`200 OK`):**
  ```json
  {
    "token_number": "5",
    "status": "ISSUED"
  }
  ```

### 5.3 Allocate Lab Token (`POST /api/v1/visits/{id}/issue-lab-token/`)
- **Request:**
  ```json
  {
    "diagnostic_order_id": 4
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "lab_token_number": "L-012",
    "status": "ISSUED"
  }
  ```

---

## 6. Clinical Triage (`/api/v1/clinical/triage/`)

### 6.1 Record Triage Vitals (`POST /api/v1/clinical/triage/`)
- **Allowed Roles:** `NURSE`, `DOCTOR`
- **Request:**
  ```json
  {
    "visit": 6,
    "patient": 2,
    "blood_pressure_systolic": 130,
    "blood_pressure_diastolic": 85,
    "pulse_bpm": 76,
    "temperature_f": "98.6",
    "spo2_percent": 99,
    "respiratory_rate": 18,
    "nurse_notes": "Patient conscious, mild fever"
  }
  ```
  *Validation Rules:*
  - `temperature_f`: Decimal with maximum 1 decimal place (e.g. `98.6`).
  - `spo2_percent`: Integer percentage (0-100).
- **Response (`201 Created`):**
  ```json
  {
    "id": 1,
    "blood_pressure_systolic": 130,
    "blood_pressure_diastolic": 85,
    "pulse_bpm": 76,
    "temperature_f": "98.6",
    "spo2_percent": 99,
    "respiratory_rate": 18,
    "bmi": null,
    "high_bp_flag": false,
    "fever_flag": false,
    "emergency_flag": false,
    "nurse": 3,
    "created_at": "2026-09-24T11:08:12Z"
  }
  ```

---

## 7. Consultations (`/api/v1/clinical/consultations/`)

### 7.1 Record Consultation (`POST /api/v1/clinical/consultations/`)
- **Allowed Roles:** `DOCTOR` (Enforced at service layer)
- **Request:**
  ```json
  {
    "visit": 6,
    "patient": 2,
    "facility": 1,
    "chief_complaint": "Headache and low grade fever for 2 days",
    "clinical_assessment": "Mild pharyngeal congestion, systemic exam normal",
    "diagnosis_code": "R50.9",
    "diagnosis_name": "Fever, unspecified",
    "treatment_plan": "Oral hydration, antipyretic, follow up if unresolved"
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": 5,
    "visit": 6,
    "patient": 2,
    "facility": 1,
    "doctor_staff": 1,
    "consultation_sequence": 1,
    "chief_complaint": "Headache and low grade fever for 2 days",
    "clinical_history": "",
    "clinical_assessment": "Mild pharyngeal congestion, systemic exam normal",
    "diagnosis_code": "R50.9",
    "diagnosis_name": "Fever, unspecified",
    "treatment_plan": "Oral hydration, antipyretic, follow up if unresolved",
    "follow_up_date": null,
    "clinical_notes": "",
    "created_at": "2026-09-24T11:09:44Z"
  }
  ```

---

## 8. Diagnostics & Laboratory (`/api/v1/diagnostics/`)

### 8.1 Place Diagnostic Order (`POST /api/v1/diagnostics/orders/`)
- **Allowed Roles:** `DOCTOR`
- **Request:**
  ```json
  {
    "visit": 6,
    "facility": 1,
    "priority": "ROUTINE",
    "clinical_indication": "Suspected viral illness, check baseline parameters"
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": 4,
    "order_number": "ORD-20260924-EC8F3F",
    "order_date": "2026-09-24",
    "lab_token_number": null,
    "priority": "ROUTINE",
    "status": "ORDERED",
    "clinical_indication": "Suspected viral illness, check baseline parameters",
    "visit": 6,
    "facility": 1,
    "ordering_doctor_staff": 1,
    "created_at": "2026-09-24T11:10:02Z"
  }
  ```

### 8.2 Create Test Request (`POST /api/v1/diagnostics/requests/`)
- **Request:**
  ```json
  {
    "diagnostic_order": 4,
    "test_master": 1,
    "specimen": null
  }
  ```

### 8.3 Enter Diagnostic Result Draft (`POST /api/v1/diagnostics/results/`)
- **Allowed Roles:** `LAB_TECHNICIAN`
- **Request:**
  ```json
  {
    "test_request": 4,
    "result_value": "Negative",
    "reference_range": "Negative",
    "abnormal_flag": false,
    "clinical_remarks": "No viral antigen detected"
  }
  ```
- **Response (`201 Created`):** Status is `DRAFT`. Direct PUT/PATCH is disabled.

### 8.4 Verify Diagnostic Result (`POST /api/v1/diagnostics/results/{id}/verify/`)
- **Allowed Roles:** `DOCTOR`, `LAB_TECHNICIAN` (Verified by Pathologist/Officer)
- **Response (`200 OK`):** Result status transitions to `VERIFIED`.

---

## 9. Pharmacy & Prescriptions (`/api/v1/pharmacy/`)

### 9.1 Create Prescription (`POST /api/v1/pharmacy/prescriptions/`)
- **Allowed Roles:** `DOCTOR`
- **Request:**
  ```json
  {
    "consultation": 5,
    "patient": 2,
    "facility": 1,
    "notes": "Paracetamol 500mg TID after food for 3 days"
  }
  ```
- **Response (`201 Created`):** Initial status is `PENDING_VERIFICATION`.

### 9.2 Pharmacist Verification (`POST /api/v1/pharmacy/prescriptions/{id}/verify/`)
- **Allowed Roles:** `PHARMACIST`
- **Request:**
  ```json
  {
    "notes": "Dosage verified, no drug interactions"
  }
  ```
- **Response (`200 OK`):** Status transitions to `VERIFIED`.

### 9.3 Place Prescription on Hold (`POST /api/v1/pharmacy/prescriptions/{id}/hold/`)
- **Allowed Roles:** `PHARMACIST`
- **Request:** `{"notes": "Querying dosage with prescriber"}`
- **Response (`200 OK`):** Status transitions to `ON_HOLD`.

### 9.4 Reject Prescription (`POST /api/v1/pharmacy/prescriptions/{id}/reject/`)
- **Allowed Roles:** `PHARMACIST`
- **Request:** `{"reason": "Incompatible medicine combination"}`
- **Response (`200 OK`):** Status transitions to `REJECTED`.

### 9.5 Dispense Prescription (`POST /api/v1/pharmacy/dispensations/`)
- **Allowed Roles:** `PHARMACIST`
- **Prerequisite:** Prescription status MUST be `VERIFIED` or `ACTIVE`.
- **Request:**
  ```json
  {
    "prescription_id": 5,
    "facility_id": 1,
    "items": [
      {
        "prescription_item_id": 4,
        "batch_id": 1,
        "quantity": 10
      }
    ]
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": 4,
    "dispensation_number": "DISP-20260924-B6B85D",
    "dispensed_at": "2026-09-24T11:14:48Z",
    "remarks": "",
    "prescription": 5,
    "facility": 1,
    "dispensed_by_staff": 3
  }
  ```

### 9.6 Inventory Ledger (`GET /api/v1/pharmacy/ledger/`)
- **Access:** Read-only audit trail scoped to user's permitted facilities.
- **Response Item Fields:**
  - `id` (int)
  - `batch` (int ID)
  - `facility` (int ID)
  - `performed_by_staff` (int ID)
  - `transaction_type` (`GRN_RECEIPT`, `DISPENSATION`, `RETURN`, `QUARANTINE`, `DAMAGE`, `ADJUSTMENT`)
  - `quantity_delta` (int)
  - `balance_after` (int)
  - `transaction_timestamp` (datetime)

---

## 10. Procurement (`/api/v1/procurement/`)

### 10.1 Purchase Orders (`/api/v1/procurement/purchase-orders/`)
- **Create (`POST`):** Requires `po_number`, `vendor`, `facility`.
- **Approve (`POST /{id}/approve/`):**
  - **Allowed Roles:** `HOSPITAL_ADMIN`, `DISTRICT_OFFICER`
  - Transitions PO status to `APPROVED`.

### 10.2 Goods Receipt Note (`POST /api/v1/procurement/grn/`)
- **Allowed Roles:** `PHARMACIST`, `HOSPITAL_ADMIN`
- **Request:**
  ```json
  {
    "purchase_order_id": 1,
    "grn_number": "GRN-20260924-001",
    "facility_id": 1,
    "items_received": [
      {
        "medicine_id": 1,
        "batch_number": "BATCH-2026-A",
        "expiry_date": "2027-09-24",
        "unit_cost": "2.50",
        "quantity_received": 500,
        "quantity_accepted": 500,
        "quantity_rejected": 0,
        "rejection_reason": ""
      }
    ]
  }
  ```
- **Service Operation:** Automatically posts inventory increments to `InventoryLedger` and creates active `MedicineBatch`.

---

## 11. Referrals & Continuity (`/api/v1/referrals/`)

### 11.1 Create Referral Order (`POST /api/v1/referrals/orders/`)
- **Allowed Roles:** `DOCTOR`
- **Request:**
  ```json
  {
    "visit": 6,
    "patient": 2,
    "source_facility": 1,
    "destination_facility": 2,
    "urgency": "ROUTINE",
    "reason": "Specialist consultation for persisting headache",
    "clinical_summary": "Initial treatment ineffective"
  }
  ```
  *Choices for `urgency`:* `ROUTINE`, `URGENT`, `EMERGENCY`
- **Response (`201 Created`):**
  ```json
  {
    "id": 2,
    "referral_number": "REF-20260924-E5952F",
    "urgency": "ROUTINE",
    "reason": "Specialist consultation for persisting headache",
    "status": "INITIATED",
    "visit": 6,
    "patient": 2,
    "source_facility": 1,
    "destination_facility": 2,
    "referring_doctor": 1
  }
  ```

### 11.2 Referral State Transition (`POST /api/v1/referrals/orders/{id}/transition/`)
- **Request:**
  ```json
  {
    "new_status": "ACCEPTED",
    "notes": "Appointment scheduled at secondary clinic"
  }
  ```
  *Allowed States:* `INITIATED`, `ACCEPTED`, `ARRIVED`, `COMPLETED`, `CANCELLED`

### 11.3 Schedule Follow-up (`POST /api/v1/referrals/followups/`)
- **Request:**
  ```json
  {
    "patient": 2,
    "facility": 1,
    "originating_visit": 6,
    "referral": 2,
    "due_date": "2026-10-01",
    "category": "POST_REFERRAL",
    "clinical_instructions": "Review symptom resolution and lab reports"
  }
  ```
  *Choices for `category`:* `NCD_ROUTINE`, `POST_REFERRAL`, `LAB_REVIEW`, `GENERAL`
- **Response (`201 Created`):**
  ```json
  {
    "id": 1,
    "due_date": "2026-10-01",
    "category": "POST_REFERRAL",
    "status": "PENDING",
    "clinical_instructions": "Review symptom resolution and lab reports",
    "patient": 2,
    "facility": 1
  }
  ```

### 11.4 Complete Follow-up (`POST /api/v1/referrals/followups/{id}/complete/`)
- **Request:**
  ```json
  {
    "completed_in_visit_id": 9
  }
  ```
- **Response (`200 OK`):** Follow-up status transitions to `COMPLETED`.

---

## 12. Non-Communicable Diseases & Surveillance (`/api/v1/ncd/` & `/api/v1/surveillance/`)

### 12.1 Register NCD Condition (`POST /api/v1/ncd/conditions/`)
- **Request:**
  ```json
  {
    "condition_code": "HYPERTENSION",
    "patient": 2,
    "registering_facility": 1,
    "staging": "STAGE_1",
    "control_status": "CONTROLLED",
    "treatment_plan": "Amlodipine 5mg OD"
  }
  ```

### 12.2 Report Surveillance Case (`POST /api/v1/surveillance/cases/`)
- **Request:**
  ```json
  {
    "disease": 1,
    "patient": 2,
    "facility": 1,
    "severity": "MODERATE",
    "status": "SUSPECTED",
    "investigation_notes": "Suspected Dengue case in ward 12"
  }
  ```

---

## 13. Operational Alerts (`/api/v1/alerts/`)

### 13.1 Acknowledge Alert (`POST /api/v1/alerts/{id}/acknowledge/`)
- **Allowed Roles:** All Active Staff
- **Response (`200 OK`):** Sets `is_active = false`, records `acknowledged_by_staff` and timestamp.

---

## 14. Audit Trail (`/api/v1/audit/`)

### 14.1 List Audit Log (`GET /api/v1/audit/`)
- **Allowed Roles:** `HOSPITAL_ADMIN`, `DISTRICT_OFFICER` (`IsAdministrativeStaff`)
- **Arbitrary Creation/Mutation:** Strictly 405 Method Not Allowed (`ReadOnlyModelViewSet`).
- **Response Item Fields:**
  - `id` (int)
  - `event_timestamp` (datetime)
  - `actor_username` (string)
  - `actor_role_snapshot` (string)
  - `action_type` (string: `INSERT`, `UPDATE`, `DELETE`)
  - `table_name` (string)
  - `record_id` (string)
  - `correlation_id` (UUID)
  - `facility` (int ID)
