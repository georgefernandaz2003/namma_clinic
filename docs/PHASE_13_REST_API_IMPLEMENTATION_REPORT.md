# PHASE 13 — REST API FOUNDATION & SERVICE-BOUNDARY INTEGRATION REPORT

## 1. EXECUTIVE SUMMARY & GATE STATUS

- **Phase Status:** `PHASE_13_COMPLETE`
- **Authorized Git Baseline:** `3d6756c4418c1cbe12fc488f41cbd75ac0afef0f`
- **Current Git Branch:** `feature/namma-clinic-demo-data-model`
- **Target REST API Namespace:** `/api/v1/`
- **Database Schema Changes:** None (`makemigrations --check`: `No changes detected`).

Phase 13 establishes the authoritative REST API foundation for the Namma Clinic platform. The REST API layer is strictly coupled to the domain service layer established in Phase 12/12A. Under no circumstances do ViewSets or Serializers directly implement business workflows, bypass authorization, alter verified clinical states, or manipulate physical inventory balances. 

---

## 2. GIT BASELINE VERIFICATION

The exact repository status at the beginning of Phase 13:
- **Baseline HEAD:** `3d6756c4418c1cbe12fc488f41cbd75ac0afef0f`
- **Branch:** `feature/namma-clinic-demo-data-model`
- **Commit Checkpoint:** Approved Phase 12A domain service hardening.

---

## 3. ARCHITECTURE & LAYERED REQUEST FLOW

Every mutating API endpoint adheres to the approved flow:

```
HTTP Request (e.g. POST /api/v1/pharmacy/dispensations/)
         ↓
  Authentication (`request.user`) & Inactive Account Check
         ↓
  Active StaffProfile Resolution (`get_request_staff`)
         ↓
  Authorization & Facility Scope (`FacilityScopedPermission`, `IsAdministrativeStaff`)
         ↓
  DRF Serializer (Input validation, field constraints, schema mapping)
         ↓
  Authoritative Domain Service (e.g. `dispense_prescription`)
         ↓
  Atomic Transaction (`transaction.atomic`) & Concurrency Lock (`select_for_update`)
         ↓
  Model Mutation & Immutable Audit Logging (`record_audit_event`)
         ↓
  HTTP Response (200/201 or translated domain exception envelope)
```

---

## 4. ENDPOINT INVENTORY (/api/v1/ NAMESPACE)

### 4.1 IAM & Professional Identity (`/api/v1/accounts/`)
| Method | Endpoint | Description | Service Invoked |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/accounts/staff-profiles/` | List active staff profiles | N/A (ORM read) |
| `POST` | `/api/v1/accounts/staff-profiles/` | Create staff profile | `create_staff_profile` |
| `POST` | `/api/v1/accounts/staff-profiles/{id}/update-status/` | Update probation/active/suspended | `update_staff_status` |
| `GET` | `/api/v1/accounts/role-assignments/` | List role assignments | N/A (ORM read) |
| `POST` | `/api/v1/accounts/role-assignments/` | Assign dynamic role to staff | `assign_role` |
| `POST` | `/api/v1/accounts/role-assignments/{id}/end-assignment/` | Terminate active role | `end_role_assignment` |
| `GET` | `/api/v1/accounts/facility-assignments/` | List facility assignments | N/A (ORM read) |
| `POST` | `/api/v1/accounts/facility-assignments/` | Assign facility to staff | `assign_facility` |
| `POST` | `/api/v1/accounts/facility-assignments/transfer/` | Transfer staff to new facility | `transfer_staff` |

### 4.2 Organization Structure (`/api/v1/organization/`)
| Method | Endpoint | Description | Guard |
| :--- | :--- | :--- | :--- |
| `GET/POST` | `/api/v1/organization/states/` | State governance | Admin write |
| `GET/POST` | `/api/v1/organization/districts/` | District administration | Admin write |
| `GET/POST` | `/api/v1/organization/taluks/` | Taluk hierarchy | Admin write |
| `GET/POST` | `/api/v1/organization/wards/` | Ward mapping | Admin write |
| `GET/POST` | `/api/v1/organization/facilities/` | Health facilities (PHC, CHC, etc.) | Facility scoped / Admin write |
| `GET/POST` | `/api/v1/organization/departments/` | Clinical/OPD/Lab departments | Admin write |

### 4.3 Patients & Encounters (`/api/v1/patients/`, `/api/v1/visits/`)
| Method | Endpoint | Description | Service Invoked |
| :--- | :--- | :--- | :--- |
| `GET/POST`| `/api/v1/patients/` | Register / search patients | Facility-scoped |
| `GET` | `/api/v1/visits/` | Encounter listing | Facility-scoped |
| `POST` | `/api/v1/visits/` | Create visit encounter | Automatic `issue_opd_token` |
| `POST` | `/api/v1/visits/{id}/issue-opd-token/` | Issue sequential OPD token | `issue_opd_token` |
| `POST` | `/api/v1/visits/{id}/issue-lab-token/` | Issue sequential Lab token | `issue_lab_token` |

### 4.4 Clinical Care & Consultations (`/api/v1/clinical/`)
| Method | Endpoint | Description | Guard |
| :--- | :--- | :--- | :--- |
| `GET/POST` | `/api/v1/clinical/triage/` | Triage vital signs recording | Active staff required |
| `GET/POST` | `/api/v1/clinical/consultations/` | Doctor consultation & clinical notes | Durable `doctor_staff` context |

### 4.5 Diagnostics & Laboratory (`/api/v1/diagnostics/`)
| Method | Endpoint | Description | Service Invoked |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/diagnostics/tests/` | Investigation test master | Read-only |
| `GET/POST`| `/api/v1/diagnostics/orders/` | Encounter diagnostic requisitions | `create_diagnostic_order` |
| `GET/POST`| `/api/v1/diagnostics/requests/` | Test line item requisitions | `create_test_request` |
| `GET/POST`| `/api/v1/diagnostics/specimens/` | Biological specimen collection | `collect_specimen` |
| `POST` | `/api/v1/diagnostics/results/` | Record laboratory test result | `record_diagnostic_result` |
| `POST` | `/api/v1/diagnostics/results/{id}/verify/` | Verify result (immutability lock) | `verify_diagnostic_result` |
| `POST` | `/api/v1/diagnostics/results/{id}/amend/` | Formal result amendment audit | `amend_diagnostic_result` |

### 4.6 Pharmacy, Inventory & Dispensation (`/api/v1/pharmacy/`)
| Method | Endpoint | Description | Constraints & Service Invoked |
| :--- | :--- | :--- | :--- |
| `GET/POST` | `/api/v1/pharmacy/medicines/` | Medication catalog | Read & Admin create |
| `GET` | `/api/v1/pharmacy/batches/` | Physical batch inventory | **Read-only** (`PATCH/PUT/DELETE` 405) |
| `GET/POST` | `/api/v1/pharmacy/prescriptions/` | Prescription management | Facility-scoped |
| `POST` | `/api/v1/pharmacy/dispensations/` | Dispense prescription | `dispense_prescription` (FEFO) |
| `GET` | `/api/v1/pharmacy/ledger/` | Authoritative stock audit ledger | **Read-only** |

### 4.7 Procurement (`/api/v1/procurement/`)
| Method | Endpoint | Description | Service Invoked |
| :--- | :--- | :--- | :--- |
| `GET/POST` | `/api/v1/procurement/vendors/` | Vendor management | Active staff |
| `GET/POST` | `/api/v1/procurement/purchase-orders/` | Purchase order lifecycle | `create_purchase_order` |
| `POST` | `/api/v1/procurement/purchase-orders/{id}/approve/` | PO tier approval | `approve_purchase_order` |
| `POST` | `/api/v1/procurement/grn/` | Goods receipt & inventory sync | `receive_goods_receipt` |

### 4.8 Referrals & Follow-Up (`/api/v1/referrals/`)
| Method | Endpoint | Description | Service Invoked |
| :--- | :--- | :--- | :--- |
| `GET/POST` | `/api/v1/referrals/orders/` | Create cross-facility referral | `create_referral_order` |
| `POST` | `/api/v1/referrals/orders/{id}/transition/` | Progress state machine | `transition_referral_state` |
| `GET/POST` | `/api/v1/referrals/followups/` | Patient follow-up recall tasks | `create_followup_task` |
| `POST` | `/api/v1/referrals/followups/{id}/complete/` | Complete follow-up task | `complete_followup` |

### 4.9 NCD, Surveillance, Alerts & Audit
| Method | Endpoint | Description | Guard |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ncd/conditions/` | Register chronic condition | `register_ncd_condition` |
| `POST` | `/api/v1/ncd/assessments/` | Record periodic vitals/sugar | `record_ncd_assessment` |
| `POST` | `/api/v1/surveillance/cases/` | Report communicable disease | `report_surveillance_case` |
| `POST` | `/api/v1/surveillance/notifications/` | Dispatch alert to public health agency | `dispatch_public_health_notification` |
| `GET/POST` | `/api/v1/alerts/` | Facility operational alerts | Facility-scoped |
| `GET` | `/api/v1/audit/` | Audit log entry inspection | **Read-only, Admin restricted (403 for staff)** |

---

## 5. AUTHENTICATION & AUTHORIZATION CONTROLS

1. **Authentication:**
   - Handled via `JWTAuthentication` (SimpleJWT) with session fallback.
   - Unauthenticated requests are rejected with `401 Unauthorized`.
   - Inactive user accounts (`is_active == False`) are immediately rejected.
2. **Durable Actor Context:**
   - Every protected request extracts `request.user.staff_profile` via `get_request_staff(request)`.
   - Inactive staff members (`status != 'ACTIVE'`) are rejected with `403 Forbidden` (`UnauthorizedDomainAction`).
3. **Backend Authoritative Facility Scope:**
   - `FacilityScopedPermission` enforces that clinical users can only access entities matching their active `StaffFacilityAssignment`.
   - Client-supplied `facility_id` parameters are never blindly trusted; permissions are validated against the server-side assignment list.
4. **Administrative Privilege Isolation:**
   - Endpoints modifying organizational structure, audit logs, or privileged role assignments are restricted via `IsAdministrativeStaff` (`403 Forbidden` for normal clinicians/nurses).

---

## 6. ERROR MAPPING

Domain exceptions are centrally intercepted by `apps.common.api_exceptions.domain_exception_handler` and converted to stable JSON error envelopes:

```json
{
  "error": "Error description message",
  "code": "SPECIFIC_DOMAIN_CODE",
  "details": {}
}
```

| Domain Exception | HTTP Status Code | Meaning |
| :--- | :--- | :--- |
| `UnauthorizedDomainAction` | `403 Forbidden` | Actor lacks active status or requisite privileges |
| `DomainValidationError` | `400 Bad Request` | Input fields failed domain validation |
| `InvalidAssignmentPeriodError` | `400 Bad Request` | Malformed effective date range |
| `InvalidStateTransition` | `409 Conflict` | Illegal state machine transition |
| `DuplicateTokenError` | `409 Conflict` | Token collision |
| `DiagnosticResultAlreadyExistsError` | `409 Conflict` | Result already exists for TestRequest |
| `VerifiedResultImmutableError` | `409 Conflict` | Attempted modification of verified diagnostic result |
| `OverlappingAssignmentError` | `409 Conflict` | Conflicting active role or facility assignment |
| `InsufficientStockError` | `409 Conflict` | Requested deduction exceeds available batch balance |
| `InvalidFollowUpCompletionError` | `409 Conflict` | Non-completed visit or patient/facility mismatch |
| `InvalidBatchOperationError` | `409 Conflict` | Operation violates batch status or expiration |
| `InvalidProcurementStateError` | `409 Conflict` | Illegal PO or GRN state transition |

---

## 7. DEPRECATED LEGACY ENDPOINTS & COMPATIBILITY

- Legacy routes mounted under `/api/...` (e.g. `/api/pharmacy/dispense/`, `/api/patients/`, `/api/facilities/`) remain active for backwards compatibility during Phase 13.
- All new integrations and frontend clients must exclusively target `/api/v1/...`.
- Direct batch update mutations on `/api/pharmacy/batches/{id}/` are deprecated and will be removed in subsequent refactoring.

---

## 8. TEST EXECUTION & VERIFICATION

### 8.1 Phase 13 REST API Test Suite (`apps/accounts/tests_phase13_api.py`)
```
Found 11 test(s).
System check identified no issues (0 silenced).
...........
----------------------------------------------------------------------
Ran 11 tests in 14.931s

OK
```
1. `test_01_unauthenticated_access_rejected_401` [PASS]
2. `test_02_inactive_user_rejected` [PASS]
3. `test_03_authenticated_active_staff_succeeds` [PASS]
4. `test_04_forbidden_role_for_admin_endpoint_returns_403` [PASS]
5. `test_05_facility_scope_isolation_enforced` [PASS]
6. `test_06_visit_token_allocation_via_service` [PASS]
7. `test_07_diagnostics_order_result_verification_immutability_and_amendment` [PASS]
8. `test_08_pharmacy_batch_direct_mutation_prohibited_and_dispense_api` [PASS]
9. `test_09_procurement_po_approval_and_grn_posting_api` [PASS]
10. `test_10_followup_completion_and_mismatch_rejection_api` [PASS]
11. `test_11_alerts_facility_isolation_and_audit_admin_restriction` [PASS]

### 8.2 Full Cumulative Test Suite Results
```
Ran 65 tests in 14.842s

OK
```
- **Phase 13 REST API Tests:** 11 / 11 PASS (100%)
- **Phase 12A Domain Service Tests:** 22 / 22 PASS (100%)
- **Phase 12 Integration Tests:** 15 / 15 PASS (100%)
- **Phase 11 Model Integrity Tests:** 17 / 17 PASS (100%)
- **Total Passing Tests:** 65 tests.

---

## 9. CONCLUSION & FINAL GATE

All REST API endpoints for Phase 13 have been implemented, verified, and integrated with the authoritative domain service layer.

**GATE STATUS: PHASE_13_COMPLETE**
