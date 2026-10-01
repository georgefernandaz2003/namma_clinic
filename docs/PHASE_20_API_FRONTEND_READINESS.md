# PHASE 20 — BACKEND API CONTRACT & FRONTEND READINESS GATE REPORT

**Target Runtime Architecture:** Local Laptop Execution  
`PostgreSQL 16` $\rightarrow$ `Django 4.2 / DRF` $\rightarrow$ `React / Vite` $\rightarrow$ `Browser`  
**Execution Environment:** Windows Native Developer Environment (Docker & Cloud Out of Scope)  
**Readiness Status:** `PHASE_20_COMPLETE`  
**Date:** September 24, 2026  

---

## 1. Git Baseline Verification

- **Approved Phase 19 Commit:** `675f157c4ff706e78939f60d61fd132b5ae53605`
- **Initial Verification Output:**
  ```powershell
  git rev-parse HEAD
  675f157c4ff706e78939f60d61fd132b5ae53605
  git branch --show-current
  feature/namma-clinic-demo-data-model
  git status --short
  # clean working directory
  ```
- **Conclusion:** Git baseline matched exact expected HEAD.

---

## 2. API Inventory

Audit of `config/api_v1_urls.py` confirms **34 ViewSets** registered across 18 core clinical and administrative domains under `/api/v1/`:

| # | Endpoint Prefix | ViewSet Class | Backing Model | Operations Allowed | Custom Actions |
|---|---|---|---|---|---|
| 1 | `accounts/staff-profiles/` | `StaffProfileViewSet` | `StaffProfile` | GET, POST, PUT, PATCH, HEAD, OPTIONS | `update_status` (POST) |
| 2 | `accounts/role-assignments/` | `RoleAssignmentViewSet` | `StaffRoleAssignment` | GET, POST, HEAD, OPTIONS | `end_assignment` (POST) |
| 3 | `accounts/facility-assignments/` | `FacilityAssignmentViewSet` | `StaffFacilityAssignment` | GET, POST, HEAD, OPTIONS | `transfer` (POST) |
| 4 | `organization/states/` | `StateViewSet` | `State` | GET, HEAD, OPTIONS | — |
| 5 | `organization/districts/` | `DistrictViewSet` | `District` | GET, HEAD, OPTIONS | — |
| 6 | `organization/taluks/` | `TalukViewSet` | `Taluk` | GET, HEAD, OPTIONS | — |
| 7 | `organization/wards/` | `WardViewSet` | `Ward` | GET, HEAD, OPTIONS | — |
| 8 | `organization/facilities/` | `FacilityViewSet` | `Facility` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 9 | `organization/departments/` | `DepartmentViewSet` | `Department` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 10 | `patients/` | `PatientViewSet` | `Patient` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 11 | `visits/` | `VisitViewSet` | `Visit` | GET, POST, PUT, PATCH, HEAD, OPTIONS | `issue-opd-token`, `issue-lab-token` |
| 12 | `clinical/consultations/` | `ConsultationViewSet` | `Consultation` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 13 | `clinical/triage/` | `TriageVitalsViewSet` | `TriageVitals` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 14 | `diagnostics/tests/` | `DiagnosticTestMasterViewSet` | `DiagnosticTestMaster` | GET, HEAD, OPTIONS | — |
| 15 | `diagnostics/orders/` | `DiagnosticOrderViewSet` | `DiagnosticOrder` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 16 | `diagnostics/requests/` | `TestRequestViewSet` | `TestRequest` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 17 | `diagnostics/specimens/` | `SpecimenViewSet` | `Specimen` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 18 | `diagnostics/results/` | `DiagnosticResultViewSet` | `DiagnosticResult` | GET, POST, HEAD, OPTIONS | `verify` (POST), `amend` (POST) |
| 19 | `pharmacy/medicines/` | `MedicineMasterViewSet` | `MedicineMaster` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 20 | `pharmacy/batches/` | `MedicineBatchViewSet` | `MedicineBatch` | GET, HEAD, OPTIONS (Read-Only stock) | — |
| 21 | `pharmacy/prescriptions/` | `PrescriptionViewSet` | `Prescription` | GET, POST, PUT, PATCH, HEAD, OPTIONS | `verify`, `hold`, `reject` (POST) |
| 22 | `pharmacy/dispensations/` | `DispensationViewSet` | `Dispensation` | GET, POST, HEAD, OPTIONS | — |
| 23 | `pharmacy/ledger/` | `InventoryLedgerViewSet` | `InventoryLedger` | GET, HEAD, OPTIONS (Read-Only) | — |
| 24 | `procurement/vendors/` | `VendorViewSet` | `Vendor` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 25 | `procurement/purchase-orders/` | `PurchaseOrderViewSet` | `PurchaseOrder` | GET, POST, PUT, PATCH, HEAD, OPTIONS | `approve` (POST) |
| 26 | `procurement/grn/` | `GoodsReceiptNoteViewSet` | `GoodsReceiptNote` | GET, POST, HEAD, OPTIONS | — |
| 27 | `referrals/orders/` | `ReferralOrderViewSet` | `ReferralOrder` | GET, POST, PUT, PATCH, HEAD, OPTIONS | `transition` (POST) |
| 28 | `referrals/followups/` | `FollowUpTaskViewSet` | `FollowUpTask` | GET, POST, PUT, PATCH, HEAD, OPTIONS | `complete` (POST) |
| 29 | `ncd/conditions/` | `NCDConditionViewSet` | `NCDCondition` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 30 | `ncd/assessments/` | `NCDAssessmentViewSet` | `NCDAssessment` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 31 | `surveillance/cases/` | `DiseaseSurveillanceCaseViewSet`| `DiseaseSurveillanceCase` | GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 32 | `surveillance/notifications/` | `PublicHealthNotificationViewSet`| `PublicHealthNotification`| GET, POST, PUT, PATCH, HEAD, OPTIONS | — |
| 33 | `alerts/` | `OperationalAlertViewSet` | `OperationalAlert` | GET, POST, PUT, PATCH, HEAD, OPTIONS | `acknowledge` (POST) |
| 34 | `audit/` | `AuditLogEntryViewSet` | `AuditLogEntry` | GET, HEAD, OPTIONS (Admin Read-Only) | — |

---

## 3. Authentication Contract

- **Token Endpoint:** `POST /api/auth/token/` (SimpleJWT `TokenObtainPairView`)
  - Request: `{"username": "<username>", "password": "<password>"}`
  - Response (`200 OK`): `{"access": "<jwt_string>", "refresh": "<jwt_string>"}`
- **Refresh Endpoint:** `POST /api/auth/token/refresh/`
  - Request: `{"refresh": "<jwt_string>"}`
  - Response (`200 OK`): `{"access": "<jwt_string>"}`
- **Unauthenticated API Behavior:** Returns HTTP `401 Unauthorized` with `{ "detail": "Authentication credentials were not provided." }`.
- **Expired/Invalid Token:** Returns HTTP `401 Unauthorized` with `{ "code": "token_not_valid", "detail": "Given token not valid for any token type" }`.
- **Credential Hygiene:** Audit verified that no password hashes, secrets, or internal authentication salts are ever exposed in any viewset or serializer output.

---

## 4. RBAC Contract Matrix

Authoritative enforcement matrix audited across active roles:

| Domain / Operation | DISTRICT_OFFICER | HOSPITAL_ADMIN | DOCTOR | NURSE | LAB_TECHNICIAN | PHARMACIST |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Auth / Login** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| **Staff Profile List** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| **Staff Status Mutation** | ALLOW | ALLOW | DENY | DENY | DENY | DENY |
| **Role Assignment** | ALLOW | ALLOW | DENY | DENY | DENY | DENY |
| **Facility Transfer** | ALLOW | ALLOW | DENY | DENY | DENY | DENY |
| **Patient Registration** | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY |
| **Visit Creation** | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY |
| **OPD Token Allocation** | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY |
| **Triage Vitals** | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY |
| **Consultation Write** | DENY | DENY | ALLOW | DENY | DENY | DENY |
| **Diagnostic Order** | DENY | DENY | ALLOW | DENY | DENY | DENY |
| **Diagnostic Result Entry** | DENY | DENY | ALLOW | DENY | ALLOW | DENY |
| **Diagnostic Verification** | DENY | DENY | ALLOW | DENY | ALLOW | DENY |
| **Prescription Write** | DENY | DENY | ALLOW | DENY | DENY | DENY |
| **Prescription Verify** | DENY | DENY | DENY | DENY | DENY | ALLOW |
| **Prescription Dispense** | DENY | DENY | DENY | DENY | DENY | ALLOW |
| **Inventory Ledger View** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| **PO Approval** | ALLOW | ALLOW | DENY | DENY | DENY | DENY |
| **GRN Receipt** | ALLOW | ALLOW | DENY | DENY | DENY | ALLOW |
| **Referral Create** | DENY | DENY | ALLOW | DENY | DENY | DENY |
| **Follow-up Task Create**| ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY |
| **Audit Log Read** | ALLOW | ALLOW | DENY | DENY | DENY | DENY |

---

## 5. Facility-Scope Contract

1. **Server-Side Enforcement:** Every clinical and inventory mutation passes through `check_facility_permission(fac, staff, request.user)`.
2. **Client Bypass Protection:** If a frontend client injects a `facility_id` or `facility` foreign key that does not belong to the authenticated user's active facility assignments (`StaffFacilityAssignment`), the backend rejects the request with HTTP `403 Forbidden` (`PermissionDenied`).
3. **Cross-Facility Queries:** `get_queryset()` strictly filters records by `facility_id__in=permitted_facilities`. Non-permitted facility records are filtered out at the SQL query level.
4. **Superuser Scope:** Superusers and District Officers hold global multi-facility visibility (`permitted_facilities = None`).

---

## 6. Request / Response Contract Audit

Key serialization rules identified for frontend integration:
- **Server-Generated Read-Only Fields:**
  - `patient_id` (MRN e.g. `PAT-20260924-XXXXXX`)
  - `visit_id` (e.g. `VIS-20260924-XXXXXX`)
  - `order_number` (e.g. `ORD-20260924-XXXXXX`)
  - `dispensation_number` (e.g. `DISP-20260924-XXXXXX`)
  - `referral_number` (e.g. `REF-20260924-XXXXXX`)
  - `token_number` (assigned sequentially per facility per day)
- **Strict Choices / Enums:**
  - `Patient.gender`: `['MALE', 'FEMALE', 'OTHER']`
  - `FollowUpTask.category`: `['NCD_ROUTINE', 'POST_REFERRAL', 'LAB_REVIEW', 'GENERAL']`
  - `ReferralOrder.urgency`: `['ROUTINE', 'URGENT', 'EMERGENCY']`
  - `Prescription.status`: `['PENDING_VERIFICATION', 'VERIFIED', 'ON_HOLD', 'REJECTED', 'PARTIALLY_DISPENSED', 'DISPENSED', 'CANCELLED']`
- **Decimal Precisions:**
  - `TriageVitals.temperature_f`: Max 1 decimal place (`98.6`).
  - `TriageVitals.spo2_percent`: Integer (0–100).
- **Stock Immutability:** Medicine batch stock cannot be patched directly (`MedicineBatchViewSet` is `ReadOnlyModelViewSet`). Stock changes occur exclusively via `dispensation` and `grn` service calls.

---

## 7. Error Contract

The application exception handler (`domain_exception_handler`) standardizes error returns:
- **HTTP 400 Bad Request:** Field validation failures (`{"field_name": ["Reason"]}`).
- **HTTP 401 Unauthorized:** Invalid, expired, or missing JWT token (`{"code": "token_not_valid", "detail": "..."}`).
- **HTTP 403 Forbidden:** Unauthorized role or out-of-scope facility access (`{"detail": "..."}`).
- **HTTP 404 Not Found:** Resource not found or blocked by facility query isolation (`{"detail": "Not found."}`).
- **HTTP 409 Conflict:** Domain service invariants (e.g. Insufficient stock, dispensing non-verified prescription).
- **HTTP 405 Method Not Allowed:** Immutable resources (e.g. `PUT /api/v1/pharmacy/ledger/1/`).

---

## 8. Clinical Workflow Contract

Authoritative 11-stage state transition sequence verified:

```
1. Patient Registration (POST /api/v1/patients/)
     ↓
2. Visit Creation (POST /api/v1/visits/)
     ↓
3. OPD Token Issuance (POST /api/v1/visits/{id}/issue-opd-token/)
     ↓
4. Triage Vitals (POST /api/v1/clinical/triage/)
     ↓
5. Consultation (POST /api/v1/clinical/consultations/)
     ↓
6. Diagnostics Order (POST /api/v1/diagnostics/orders/)
     ↓
7. Specimen Collection & Result (POST /api/v1/diagnostics/results/)
     ↓
8. Result Verification (POST /api/v1/diagnostics/results/{id}/verify/)
     ↓
9. Prescription Creation (POST /api/v1/pharmacy/prescriptions/) -> PENDING_VERIFICATION
     ↓
10. Pharmacist Verification (POST /api/v1/pharmacy/prescriptions/{id}/verify/) -> VERIFIED
     ↓
11. Dispensing (POST /api/v1/pharmacy/dispensations/) -> DISPENSED
     ↓
12. Referral Order & Follow-up (POST /api/v1/referrals/orders/ & /followups/)
```

---

## 9. Pharmacy Contract

- **Stock Authority:** The PostgreSQL `inventory_ledgers` table remains the sole and final authority on stock balances.
- **Verification Gate:** Dispensing enforces that prescriptions are in `VERIFIED` or `ACTIVE` status. Direct dispensing of unverified prescriptions is rejected with `409 Conflict`.
- **Batch Allocation:** Validated on server-side FIFO/FEFO allocation. Insufficient batch quantity raises atomic rollback.
- **Procurement Ingestion:** `POST /api/v1/procurement/grn/` updates purchase order received status, creates or links batches, and posts `GRN_RECEIPT` movements in an atomic database transaction.

---

## 10. Cross-Facility Contract

- **Clinical Continuity:** Patient demographics are accessible across the health network by verified patient ID.
- **Clinical Records Isolation:** Consultations, triage vitals, and lab orders are strictly isolated to the originating facility.
- **Referral Visibility:** A referral order is queryable by BOTH the originating source facility and the receiving destination facility (`Q(source_facility_id__in=permitted) | Q(destination_facility_id__in=permitted)`).
- **Inter-facility Actions:** Receiving facility staff can accept and complete incoming referrals without compromising other non-referred records.

---

## 11. Audit Contract

- **Mutations Tracked:** Every clinical encounter creation, diagnosis, prescription, verification, dispensation, and referral generates an immutable `AuditLogEntry` record.
- **Security & Privacy:** Patient identifiers in the audit log are restricted to `record_id` and resource types; sensitive clinical text and PII are excluded from audit summary streams.
- **Access Control:** `GET /api/v1/audit/` is strictly locked to `HOSPITAL_ADMIN` and `DISTRICT_OFFICER` (`IsAdministrativeStaff`). Non-admin staff receive HTTP `403 Forbidden`.

---

## 12. API Consistency Audit & Contract Defect Fixes

During the audit, three contract defects were detected and resolved:

### 12.1 Defect 1: `AuditLogEntrySerializer` Read-Only String (Critical / High)
- **Problem:** `apps/ncd/api_v1.py` had `read_only_fields = fields` where `fields = '__all__'`. DRF raised `TypeError: The read_only_fields option must be a list or tuple. Got str.`, causing HTTP 500 errors on `GET /api/v1/audit/`.
- **Fix:** Removed redundant `read_only_fields = fields` since `AuditLogEntryViewSet` is already a `viewsets.ReadOnlyModelViewSet`.

### 12.2 Defect 2: `InventoryLedgerSerializer` Read-Only String (Critical / High)
- **Problem:** `apps/pharmacy/api_v1.py` had `read_only_fields = fields` where `fields = '__all__'`. DRF threw a `TypeError` on evaluating serializer fields for `GET /api/v1/pharmacy/ledger/`.
- **Fix:** Removed redundant `read_only_fields = fields`.

### 12.3 Defect 3: Missing Prescription Verification Actions in V1 API (Critical / Blocker)
- **Problem:** `PrescriptionViewSet` in `apps/pharmacy/api_v1.py` was missing `@action` endpoints for `verify`, `hold`, and `reject`. Prescriptions remained stuck in `PENDING_VERIFICATION`, blocking dispensing.
- **Fix:** Added `@action(detail=True, methods=['post'], url_path='verify')`, `hold`, and `reject` to `PrescriptionViewSet` in `apps/pharmacy/api_v1.py`.

---

## 13. Frontend Readiness Matrix

| Domain | API Exists | Auth | RBAC | Facility Scope | Request Contract | Response Contract | Error Contract | Frontend Ready |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Authentication** | READY | READY | READY | N/A | READY | READY | READY | **READY** |
| **IAM / Accounts** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Organization** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Patients** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Visits & Tokens** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Triage** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Consultation** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Diagnostics** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Pharmacy / Rx** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Procurement** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Referrals** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Follow-up** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **NCD Management**| READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Surveillance** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Alerts** | READY | READY | READY | READY | READY | READY | READY | **READY** |
| **Audit** | READY | READY | READY | READY | READY | READY | READY | **READY** |

**Overall Domain Readiness:** **100% READY across all 16 domains.**

---

## 14. Test Suite Execution

- **Baseline Test Count:** 113 tests
- **Targeted Contract Tests Added:** 3 tests in `apps/accounts/tests_phase20_contract.py`:
  1. `test_audit_log_endpoint_contract`
  2. `test_inventory_ledger_endpoint_contract`
  3. `test_prescription_verify_hold_reject_contract`
- **Total Test Count:** **116 tests**
- **Test Suite Results:**
  ```powershell
  python manage.py test apps.accounts.tests_phase11 apps.accounts.tests_phase12_services apps.accounts.tests_services apps.visits.tests_services apps.laboratory.tests_services apps.pharmacy.tests_services apps.referrals.tests_services apps.audit.tests_services apps.accounts.tests_phase13_api apps.accounts.tests_phase14_integration apps.accounts.tests_phase15_reliability apps.accounts.tests_phase16_postgres apps.accounts.tests_phase18_deployment apps.accounts.tests_phase20_contract --noinput
  
  Ran 116 tests in 64.239s
  OK
  ```

---

## 15. Native PostgreSQL API Smoke Test Results

Executed end-to-end integration smoke test directly against live PostgreSQL 16 on port 49392:

```
[PASS] 1. Auth: JWT token acquired successfully, credentials unexposed.
[PASS] 2. Patient: Registered ID=5, MRN=PAT-20260924-B1FB89
[PASS] 3. Visit: Created ID=9, VisitNumber=VIS-20260924-587572
[PASS] 4. Token: Allocated Token Number=8
[PASS] 5. Triage: Recorded vitals ID=3, BP=130/85
[PASS] 6. Consultation: Recorded Consultation ID=7, DoctorStaff=1
[PASS] 7. Diagnostics: Placed Diagnostic Order ID=6, OrderNumber=ORD-20260924-A92B0E
[PASS] 8. Prescription: Created Rx ID=5, Status=PENDING_VERIFICATION, Item ID=5
[PASS] 8B. Prescription Verification: Verified Rx ID=5, Status=VERIFIED
[PASS] 9. Dispensing: Executed Dispensation ID=4, DispNo=DISP-20260924-B6B85D
[PASS] 10. Referral: Order ID=2, RefNumber=REF-20260924-E5952F, Urgency=ROUTINE
[PASS] 11. Follow-up: Task ID=1, DueDate=2026-10-01, Status=PENDING
--- ALL 11 API SMOKE TESTS COMPLETED SUCCESSFULLY ---
```

---

## 16. Blocking Findings & Fixes Summary

- **Initial Status:** PARTIAL (Due to 3 defects: Audit serializer TypeError, Inventory Ledger serializer TypeError, missing Prescription verification action).
- **Fixes Applied:**
  1. Removed invalid `read_only_fields = fields` from `AuditLogEntrySerializer` in `apps/ncd/api_v1.py`.
  2. Removed invalid `read_only_fields = fields` from `InventoryLedgerSerializer` in `apps/pharmacy/api_v1.py`.
  3. Added `verify`, `hold`, and `reject` actions to `PrescriptionViewSet` in `apps/pharmacy/api_v1.py`.
- **Post-Fix Status:** 0 blocking defects remaining.

---

## 17. Phase 21 Prerequisites

The backend is completely ready for React frontend implementation under the following Phase 21 prerequisites:
1. **Frontend Architecture:** React 18+ with Vite running locally on developer laptop.
2. **API Client:** Use standardized client (e.g. Axios/Fetch) configured with `baseURL = http://127.0.0.1:8000/api/v1/` and automatic JWT bearer token injection from local storage.
3. **Data Contract Compliance:** Frontend forms and payloads must adhere strictly to `docs/FRONTEND_API_CONTRACT.md`.
4. **No Direct Model Assumptions:** Frontend must treat IDs, timestamps, token numbers, and status transitions as authoritative server outputs.
