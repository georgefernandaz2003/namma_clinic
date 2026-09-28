# Namma Clinic — IAM & Staff Role Design: Compounder Separation & Multi-Role Authority Architecture

**Document ID:** ARCH-IAM-2026-001  
**Status:** FINAL PROPOSED / PM & RSA REVIEW REVISION  
**Baseline Commit:** `e60cfdfa60cf6ebee96116192d59dc23bd634525`  
**Target Branch:** `feature/namma-clinic-demo-data-model`  
**Author:** Antigravity AI Engineering / Namma Clinic Architecture Guild  
**Date:** September 28, 2026  

---

## Table of Contents
1. [Executive Summary & Architectural Objective](#1-executive-summary--architectural-objective)
2. [Current IAM Implementation Findings & Gap Analysis](#2-current-iam-implementation-findings--gap-analysis)
3. [Current Patient Registration Workflow](#3-current-patient-registration-workflow)
4. [Current OPD Queue Workflow](#4-current-opd-queue-workflow)
5. [Proposed Seven-Role Model & Administrative Terminology](#5-proposed-seven-role-model--administrative-terminology)
6. [Compounder Responsibility Definition & Field-Level Access Control](#6-compounder-responsibility-definition--field-level-access-control)
7. [Nurse vs. Compounder Responsibility Separation](#7-nurse-vs-compounder-responsibility-separation)
8. [OPD Queue State Machine & Transition Rules](#8-opd-queue-state-machine--transition-rules)
9. [Special Small-Clinic Rule: Nurse + Compounder Dual Assignment](#9-special-small-clinic-rule-nurse--compounder-dual-assignment)
10. [Facility Staffing Rules & Administrative Workflows](#10-facility-staffing-rules--administrative-workflows)
11. [Explicit Domain Actions & Permission Vocabulary](#11-explicit-domain-actions--permission-vocabulary)
12. [Comprehensive Seven-Role Authority & Permission Matrix](#12-comprehensive-seven-role-authority--permission-matrix)
13. [Facility + Role Authorization Tuple Invariant](#13-facility--role-authorization-tuple-invariant)
14. [District Health Officer (DHO) Authority & Scope Invariant](#14-district-health-officer-dho-authority--scope-invariant)
15. [Hospital Admin / Clinic Admin Authority & Delegation Model](#15-hospital-admin--clinic-admin-authority--delegation-model)
16. [Staff Lifecycle Management, State Transitions & Session Semantics](#16-staff-lifecycle-management-state-transitions--session-semantics)
17. [Security Architecture & Threat Mitigation Matrix](#17-security-architecture--threat-mitigation-matrix)
18. [Required Backend Changes](#18-required-backend-changes)
19. [Required Frontend Changes](#19-required-frontend-changes)
20. [Required Database & Migration Changes](#20-required-database--migration-changes)
21. [API Changes & Contract Specifications](#21-api-changes--contract-specifications)
22. [Audit & Regulatory Compliance Framework](#22-audit--regulatory-compliance-framework)
23. [Phased Implementation Roadmap](#23-phased-implementation-roadmap)
24. [Testing Strategy & Test Specifications](#24-testing-strategy--test-specifications)
25. [Risks, Assumptions & Open Questions](#25-risks-assumptions--open-questions)
26. [IAM Security Invariants (`IAM_SECURITY_INVARIANTS`)](#26-iam-security-invariants-iam_security_invariants)

---

## 1. Executive Summary & Architectural Objective

The Namma Clinic digital health platform is engineered to support primary healthcare delivery across Urban Primary Health Centres (UPHCs) and Namma Clinics in Karnataka. Primary health clinics represent high-throughput, community-facing environments where clear delineation of professional responsibilities is critical for patient safety, clinical efficacy, and data privacy.

### 1.1 The Operational Problem
In the initial development phases of Namma Clinic, the `NURSE` role was assigned broad front-desk responsibilities, including citizen demographic registration, search, and OPD queue token issuance, in addition to core clinical duties (triage, vitals recording, nursing assessment, and care coordination). This created critical operational and security liabilities:
1. **Clinical Bottlenecks**: Nurses spent up to 40% of their operational time performing front-desk clerical data entry instead of conducting timely clinical vitals measurement and triage grading.
2. **Excessive Privilege Exposure**: Front-desk operators required clinical credentials to register patients, violating the Principle of Least Privilege and creating risks of unauthorized clinical data viewing or alteration.
3. **Role Conflation**: The term "Compounder" is often colloquially used in Indian primary healthcare. However, in modern Karnataka PHCs, the Compounder acts strictly as a **registration desk clerk and queue coordinator**, not as a dispensing pharmacist or clinical provider.

### 1.2 The Architectural Objective
This architectural specification establishes the authoritative Staff / Identity & Access Management (IAM) authority model for Namma Clinic:
- **Introduce `COMPOUNDER`**: Create a dedicated front-desk intake and queue management role with zero clinical or pharmacy privileges (`COMPOUNDER = PATIENT REGISTRATION + OPD QUEUE ONLY`).
- **Field-Level Patient Isolation**: Restrict Compounder to a strict demographic whitelist for viewing and updates. Prevent `patients.read` from granting generic EMR/clinical access.
- **Isolate `NURSE`**: Refocus the `NURSE` role strictly on clinical triage, vitals, and nursing workflows, removing automatic patient registration and token issuance rights.
- **Enable Multi-Role Dual Assignment**: Formalize the **Small-Clinic Rule**, where a single nurse in a small PHC can hold both `NURSE` and `COMPOUNDER` role assignments concurrently on a single user account, computing effective permissions dynamically as a union without introducing an anti-pattern hybrid role (such as `NURSE_COMPOUNDER`).
- **Enforce Authoritative Scoping & Tuple Validation**: Establish that a role assignment never grants access by itself; valid access requires `UserAccount + active StaffProfile + active FacilityAssignment + active RoleAssignment + valid effective dates + permission + facility/district scope`.
- **Eliminate DHO District Vulnerability**: Eliminate the `NULL district == global access` vulnerability for District Health Officers (DHOs) by failing closed.
- **Define Accurate Session Semantics**: Acknowledge that `User.is_active=False` alone does not magically revoke stateless JWT tokens; mandate that every protected API independently validates active staff/role/facility status.

---

## 2. Current IAM Implementation Findings & Gap Analysis

A thorough inspection of the active codebase at HEAD (`e60cfdfa60cf6ebee96116192d59dc23bd634525`) reveals an architectural duality between the legacy authentication model and the domain-driven enterprise IAM model introduced in Phases 11–13.

### 2.1 Codebase Inspection Findings

#### A. User & Identity Models (`backend/apps/accounts/models.py`)
1. **Legacy User Model**:
   - `apps.accounts.models.User` inherits from Django's `AbstractUser`.
   - The user has a single role column: `role = models.CharField(max_length=30, choices=RoleChoices.choices, default=RoleChoices.DOCTOR)`.
   - `RoleChoices` currently defines exactly 6 roles: `DISTRICT_OFFICER`, `HOSPITAL_ADMIN`, `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `PHARMACIST`.
   - The user also contains foreign keys: `assigned_facility` (`ForeignKey('facilities.Facility')`), `assigned_district` (`ForeignKey('geography.District')`), and `staff_profile` (`OneToOneField(StaffProfile)`).
2. **Enterprise Domain Identity Models (Phase 11)**:
   - `Person`: Encapsulates natural identity (`first_name`, `last_name`, `gender`, `date_of_birth`, `phone_number`, `aadhaar_hash`).
   - `StaffProfile`: Decouples professional clinical identity from mutable authentication accounts (`employee_id`, `designation`, `medical_council_reg_number`, `status`, `department`).
   - `RoleMaster`: Master table of system roles (`code`, `name`, `description`, `is_active`).
   - `StaffRoleAssignment`: Many-to-one relationship between `StaffProfile` and `RoleMaster`, supporting multi-role assignment with `effective_from`, `effective_to`, and `is_active` status, enforced by a database check constraint (`chk_staff_role_dates`).
   - `StaffFacilityAssignment`: Many-to-one relationship between `StaffProfile` and `Facility`, with `is_primary`, `effective_from`, `effective_to`, and `is_active`.

#### B. Permission Evaluation & Resolution (`backend/apps/accounts/permissions.py`)
1. **Single-Role Static Mapping**:
   - Permission strings are mapped in a static dictionary: `ROLE_PERMISSIONS: Dict[str, Set[str]]`.
   - The permission resolution helper is implemented as:
     ```python
     def has_role_permission(user, permission_name):
         if not user or not user.is_authenticated:
             return False
         user_perms = ROLE_PERMISSIONS.get(user.role, set())
         return permission_name in user_perms
     ```
   - **Critical Architectural Disconnect**: `has_role_permission` indexes `user.role` (a single string attribute) and completely ignores `user.staff_profile.role_assignments`. Consequently, any user with multiple assignments in `StaffRoleAssignment` cannot exercise their additional permissions through the active permission checks!
2. **Current Permission Class Implementation**:
   - `HasPermission`: Evaluates view-level or method-level permissions (`view.required_permissions` or `view.required_permission`) against `has_role_permission(request.user, req_perm)`.
   - `HasFacilityScope`: Validates that operational staff access only records matching `request.user.assigned_facility_id`.
   - `IsActiveStaff` / `IsAdministrativeStaff` (`apps/common/permissions.py`): Validates `request.user.staff_profile.status == "ACTIVE"` and verifies whether the staff holds administrative designations or privileged roles (`ADMIN`, `SYSTEM_ADMIN`, `HOSPITAL_ADMIN`, `DHO`).

#### C. Facility & District Scoping Vulnerability (`backend/apps/accounts/permissions.py`)
- Lines 52–65 in `get_accessible_facility_ids_for_user(user)` contain a critical vulnerability:
  ```python
  if user.role == 'DISTRICT_OFFICER':
      if user.assigned_district_id:
          return list(Facility.objects.filter(district_id=user.assigned_district_id).values_list('id', flat=True))
      return None  # <-- CRITICAL SECURITY FLAW: Returns None when assigned_district_id is NULL!
  ```
- In Django REST Framework querysets (e.g. `PatientViewSet.get_queryset`), a return value of `None` is interpreted as **unrestricted statewide access**:
  ```python
  accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
  if accessible_ids is not None:
      queryset = queryset.filter(...)
  # If accessible_ids is None, NO FILTER IS APPLIED!
  ```
- Furthermore, in `can_access_facility(user, facility_id)`:
  ```python
  if user.role == 'DISTRICT_OFFICER':
      if user.assigned_district_id:
          return Facility.objects.filter(id=facility_id, district_id=user.assigned_district_id).exists()
      return True  # <-- CRITICAL SECURITY FLAW: Returns True for ANY facility if district is NULL!
  ```
- This completely violates the mandate: **A District Health Officer MUST have an explicit District Assignment; NULL district must NEVER grant global/statewide access.**

#### D. Frontend Permission & Route Guards (`frontend/src/utils/permissions.ts`)
1. **Single-Role Typing**:
   - `type Role = 'DISTRICT_OFFICER' | 'HOSPITAL_ADMIN' | 'DOCTOR' | 'NURSE' | 'LAB_TECHNICIAN' | 'PHARMACIST';`
   - `ROLE_PERMISSIONS: Record<Role, Set<string>>` mirrors the backend dictionary.
   - `hasPermission(role: Role | undefined, permission: string): boolean` accepts only a single role parameter.
   - `ROLE_ALLOWED_PATHS: Record<Role, string[]>` restricts URL routing per single role.
2. **Session Profile Initialization (`frontend/src/context/AuthContext.tsx`)**:
   - `refreshUserData()` calls `GET /api/auth/me/`.
   - `CurrentUserProfileView` (`backend/apps/accounts/views.py`) serializes `request.user` with `UserProfileSerializer`, which exposes `user.role` and `ROLE_PERMISSIONS.get(obj.role)`.
   - If a user has multiple roles assigned in the database, the frontend receives only the primary role and cannot unlock multi-role screens.

### 2.2 Summary of Gaps to Address
| # | Identified Architectural Gap | Risk Level | Target Remediation |
|---|---|:---:|---|
| 1 | Lack of `COMPOUNDER` role in `RoleChoices`, `RoleMaster`, and frontend types | High | Add `COMPOUNDER` to enum, master tables, and frontend types. |
| 2 | Front-desk intake permissions (`patients.create`, `queue.create`) granted to `NURSE` | Medium | Move front-desk intake permissions to `COMPOUNDER`; isolate `NURSE` to clinical triage. |
| 3 | Single-role permission resolution in `has_role_permission` and `UserProfileSerializer` | Critical | Implement multi-role dynamic permission union resolver across active `StaffRoleAssignment`s. |
| 4 | DHO `NULL district` returning `None` / `True` (unrestricted statewide bypass) | Critical | Enforce invariant: `DISTRICT_OFFICER` with `NULL district` fails closed with HTTP 403 Forbidden. |
| 5 | Lack of administrative scoping in `RoleAssignmentViewSet` (cross-facility privilege escalation) | High | Enforce that Clinic Admin can only assign roles to staff in their assigned facility. |
| 6 | Incomplete staff lifecycle states in `StaffProfile.status` (`INVITED`, `TRANSFER_PENDING`, `DEACTIVATED` missing) | Medium | Expand lifecycle state machine to formalize onboarding, suspension, transfer, and deactivation. |
| 7 | Stateless JWT session invalidation gap upon account suspension | High | Mandate active verification of staff/role/facility status on every protected API request. |

---

## 3. Current Patient Registration Workflow

### 3.1 Operational Entrypoints & Endpoints
The platform currently exposes two endpoints for patient registration:
1. **Legacy Frontend API**: `POST /api/patients/` handled by `PatientViewSet` in `backend/apps/patients/views.py`.
2. **Domain Service API (v1)**: `POST /api/v1/patients/` handled by `PatientViewSet` in `backend/apps/patients/api_v1.py`.

### 3.2 Workflow Step-by-Step Execution
1. **Citizen Arrival**: Citizen arrives at the clinic front desk.
2. **Search / Duplicate Verification**:
   - The operator enters citizen mobile number, name, or National Health ID (ABHA) in the search field.
   - Frontend issues `GET /api/patients/?search={query}`.
   - Backend evaluates `search_fields = ['name', 'mobile', 'patient_id']`.
   - Continuity-of-care policy allows cross-facility demographic search across the state to identify existing health records.
3. **Registration Form Submission**:
   - If no record exists, the operator opens the registration modal.
   - Form fields captured: First Name, Last Name, Gender, Date of Birth / Age, Mobile Number, Street Address, Ward/Zone, Emergency Contact, ABHA ID (optional).
   - Operator submits form to `POST /api/patients/`.
4. **Backend Authorization & Validation**:
   - `PatientViewSet` checks `permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]`.
   - `required_permissions = {'POST': 'patients.create'}`.
   - **Current Enforcement**: Currently, `HOSPITAL_ADMIN` and `NURSE` possess `'patients.create'`.
   - Duplicate prevention check:
     ```python
     if mobile and name:
         existing = Patient.objects.filter(mobile=mobile, name__iexact=name).first()
         if existing:
             return Response({'error': f"Duplicate patient record detected! Patient '{existing.name}' is already registered with Patient ID {existing.patient_id}."}, status=400)
     ```
5. **Identifier Generation & Persistence**:
   - Server generates sequential identifier: `NC-KA-2026-XXXX` (or `PAT-YYYYMMDD-HEX6`).
   - Facility scoping: If `registered_at_facility` is not provided, the server defaults to `request.user.assigned_facility_id`.
   - Record persisted to `patients` table in PostgreSQL.
6. **Audit Event Generation**:
   - System records audit log entry with action `PATIENT_CREATE`, actor ID, facility ID, and timestamp.

### 3.3 Critical Findings in Registration Workflow
- **Coupling with Nursing Role**: Because only `NURSE` (and `HOSPITAL_ADMIN`) has `patients.create`, the application forces clinical staff to perform non-clinical registration, or forces clinics to assign the `NURSE` role to front-desk clerical staff.
- **Unrestricted EMR Timeline Access**: Once a patient is registered, `PatientTimelineView` (`GET /api/patients/{id}/timeline/`) returns full clinical notes, vitals, doctor diagnoses, and lab results, protected only by `patients.view`. When a registration clerk needs to search a patient, granting `patients.view` inadvertently exposes the patient's full clinical medical history.

---

## 4. Current OPD Queue Workflow

### 4.1 Operational Entrypoints & Endpoints
The OPD Queue and token management are governed by:
- `POST /api/visits/`: Visit creation & OPD token issuance.
- `GET /api/visits/?queue={queue}&facility={facility}&date={date}`: Queue viewing and filtering.
- `POST /api/visits/call-next/`: Atomic queue dequeuing.
- `POST /api/visits/{id}/transition-status/`: Workflow stage advancement.

### 4.2 Workflow Step-by-Step Execution
1. **Visit Request Initiation**:
   - Following patient registration or lookup, operator clicks "Create OPD Visit / Issue Token".
   - Operator selects: Registered Patient, Facility, Visit Type (`GENERAL_OPD`, `NCD_SCREENING`, `ANC_PNC`, `IMMUNIZATION`), Priority (`NORMAL`, `HIGH`, `EMERGENCY`), and Chief Complaint.
2. **Backend Authorization & Scope Check**:
   - `VisitViewSet.create` requires `'queue.create'` via `HasPermission`.
   - Facility validation: `can_access_facility(request.user, facility_id)` verifies that the operator is assigned to the specified facility.
3. **Atomic Token Generation**:
   - Transaction locks existing tokens for today at facility:
     ```python
     with transaction.atomic():
         max_token = Token.objects.select_for_update().filter(
             facility_id=facility_id, date=today
         ).aggregate(models.Max('token_number'))['token_number__max'] or 0
         token_number = max_token + 1
         visit_id = f"VIS-F{facility_id}-{today.strftime('%Y%m%d')}-{token_number:03d}"
         
         visit = Visit.objects.create(
             visit_id=visit_id,
             patient_id=patient_id,
             facility_id=facility_id,
             opd_date=today,
             visit_type=visit_type,
             priority=priority,
             chief_complaint=chief_complaint,
             current_queue='TRIAGE',
             status='WAITING_FOR_TRIAGE',
             arrival_time=timezone.now()
         )
         token = Token.objects.create(
             token_number=token_number,
             visit=visit,
             facility_id=facility_id,
             date=today,
             priority=priority,
             status='WAITING'
         )
     ```
   - An initial entry is recorded in `VisitStatusHistory` (`from_status='NONE'`, `to_status='WAITING_FOR_TRIAGE'`, `queue='TRIAGE'`).
4. **Queue Calling (`call_next_patient`)**:
   - When a clinician or nurse is ready, they trigger `POST /api/visits/call-next/`.
   - **Role Restriction Check in Code**:
     ```python
     if user_role == 'DOCTOR' and target_queue != 'DOCTOR':
         return Response({'error': 'Doctors are only authorized to call patients from the DOCTOR consultation queue.'}, status=403)
     elif user_role == 'NURSE' and target_queue != 'TRIAGE':
         return Response({'error': 'Nurses are only authorized to call patients from the TRIAGE queue.'}, status=403)
     ```
   - Database locks next waiting patient ordered by priority weight (`EMERGENCY > HIGH > NORMAL`) and `arrival_time`.
   - Visit status advances to `IN_TRIAGE` (for Nurse) or `IN_CONSULTATION` (for Doctor).
5. **Status Transition (`transition-status`)**:
   - Enforces clinical integrity: A visit cannot advance to `DOCTOR` queue without recorded triage vitals:
     ```python
     if to_status in ['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION'] or target_queue == 'DOCTOR':
         if not hasattr(visit, 'triage') and not TriageVitals.objects.filter(visit=visit).exists():
             return Response({'error': 'Cannot advance visit to DOCTOR queue without recorded triage vitals.'}, status=400)
     ```

### 4.3 Key Observations for Role Separation
- Token issuance is strictly clerical and administrative; it places the patient in the queue waiting for triage. This duty belongs entirely to `COMPOUNDER`.
- Status transition from `WAITING_FOR_TRIAGE` to `IN_TRIAGE` and from `IN_TRIAGE` to `WAITING_FOR_DOCTOR` requires clinical measurement of vitals. This duty belongs strictly to `NURSE` and must never be permitted to `COMPOUNDER`.

---

## 5. Proposed Seven-Role Model & Administrative Terminology

### 5.1 Clarification on Administrative Terminology
A key question resolved during the PM/RSA review is the relationship between `HOSPITAL_ADMIN` and `CLINIC ADMIN`:
- **DECISION**: **`HOSPITAL_ADMIN` is the authoritative technical role code representing the requested `CLINIC ADMIN`.**
- Under no circumstances shall a second administrative role (e.g. `CLINIC_ADMIN`) be introduced into the database or codebase merely because institutional nomenclature varies between hospitals and primary clinics.
- In all user-facing documentation and UI labels for Namma Clinics, `HOSPITAL_ADMIN` is presented as **"Clinic Administrator"** or **"Facility Admin"**. In secondary hospitals, it is presented as **"Hospital Administrator"**.
- The authority of `HOSPITAL_ADMIN` is strictly facility-scoped.

### 5.2 The Canonical Seven-Role Topology

```
+-----------------------------------------------------------------------------------------+
|                              NAMMA CLINIC SEVEN-ROLE MODEL                              |
+-----------------------------------------------------------------------------------------+
| 1. DISTRICT_OFFICER            | District Health Officer (DHO) / Municipal Health Officer |
| 2. HOSPITAL_ADMIN (CLINIC ADMIN)| Clinic Administrator / Hospital Superintendent           |
| 3. DOCTOR                      | Medical Officer / General Physician / Consultant        |
| 4. NURSE                       | Staff Nurse / Clinical Care Coordinator                  |
| 5. COMPOUNDER                  | Front Desk Intake Clerk / OPD Queue Coordinator          |
| 6. LAB_TECHNICIAN              | Medical Laboratory Technologist (MLT)                   |
| 7. PHARMACIST                  | Registered Pharmacist / Dispensary Officer               |
+-----------------------------------------------------------------------------------------+
```

### 5.3 Institutional Scope and Personas

| # | Role Code | Human UI Label | Institutional Persona | Scope Level | Scope Invariant |
|---|---|---|---|---|---|
| 1 | `DISTRICT_OFFICER` | District Health Officer | DHO, CMO, BBMP Health Officer | District-Wide | Explicit `assigned_district` required; NULL fails closed. |
| 2 | `HOSPITAL_ADMIN` | Clinic Administrator | Clinic In-Charge, Facility Admin | Single Facility | Explicit `assigned_facility` required; strictly facility-scoped. |
| 3 | `DOCTOR` | Medical Officer | General Physician, Specialist Doctor | Single Facility | Assigned facility; clinical mutations allowed. |
| 4 | `NURSE` | Staff Nurse | Staff Nurse, Community Nurse | Single Facility | Assigned facility; triage & vitals allowed. |
| 5 | `COMPOUNDER` | Compounder / Registration Clerk | Front-desk clerk, registration operator | Single Facility | Assigned facility; registration & queue token issuance only. |
| 6 | `LAB_TECHNICIAN` | Lab Technician | Medical Lab Technologist (MLT) | Single Facility | Assigned facility; specimen collection & lab results only. |
| 7 | `PHARMACIST` | Pharmacist | Registered Pharmacist | Single Facility | Assigned facility; prescription verification & dispensing only. |
---

## 6. Compounder Responsibility Definition & Field-Level Access Control

### 6.1 Core Mandate: Registration and OPD Queue Only
The central approved business requirement for the Compounder is:
$$\mathbf{COMPOUNDER = PATIENT\ REGISTRATION + OPD\ QUEUE\ ONLY}$$

The Compounder is **NOT** a pharmacy role and possesses **NO clinical authority**. The historical colloquial term must not be confused with compounding or dispensing medicines.

### 6.2 Field-Level Patient Visibility Whitelist vs. Blacklist
A fundamental vulnerability identified during the PM/RSA review is that generic permission codes like `patients.read` or `patients.view` have historically granted access to the entire patient object graph, including confidential clinical history. 

**Under this design, `patients.read` MUST NOT automatically imply unrestricted Patient/EMR access.**

```
+-----------------------------------------------------------------------------------+
|                        COMPOUNDER PATIENT DATA VISIBILITY                         |
+-----------------------------------------------------------------------------------+
| [PERMITTED WHITELIST]                              | [STRICT CLINICAL BLACKLIST]  |
| - Patient Identifier (e.g. NC-KA-2026-1042)        | - Medical Diagnoses (ICD-10) |
| - Full Name (First Name, Last Name)                | - Physician Consultation Notes|
| - Date of Birth & Age (Registration verification)  | - Nursing Assessments        |
| - Gender (Demographic intake)                      | - Clinical Triage & Vitals   |
| - Mobile Phone Number                              | - Prescription Items & Drugs |
| - Residential Address (Street, Ward, Zone)         | - Laboratory Test Results    |
| - Emergency Contact Name & Phone                   | - NCD Clinical Screening Data|
| - Registration Metadata (Facility, Date)           | - Longitudinal EMR Timeline  |
| - Relevant OPD Queue Status & Waiting Token        | - Confidential Clinical Files|
+-----------------------------------------------------------------------------------+
```

#### A. Compounder Patient Read Whitelist
The Compounder may read ONLY:
1. `patient_id` (Unique system registration identifier)
2. `name` (`first_name`, `last_name`)
3. `date_of_birth` / `age` (Required strictly for age-bracket demographic verification)
4. `gender` (Required for public health demographic categorization)
5. `mobile` (Primary citizen contact identifier)
6. `address` (Street address, door number, ward, zone)
7. `emergency_contact_name` and `emergency_contact_phone`
8. `registered_at_facility` and `registration_date`
9. Relevant OPD queue information (Token number, current queue status, priority, waiting time)

#### B. Compounder Patient Read Blacklist (Categorically Prohibited)
The Compounder must NOT read:
1. Medical diagnosis (provisional, differential, final, or ICD-10 codes)
2. Doctor consultation notes and clinical history
3. Nursing clinical assessments
4. Triage notes and recorded vital signs (BP, pulse, SpO2, temperature, BMI, blood sugar)
5. Prescription clinical details, dosage instructions, and active medication regimens
6. Laboratory investigation orders and diagnostic results
7. Non-communicable disease (NCD) clinical screening questionnaires (CBAC score, hypertension/diabetes records)
8. Confidential longitudinal clinical timeline notes and physician referral letters

### 6.3 Demographic Update Whitelist
The platform strictly rejects generic, unrestricted patient update authority for the Compounder role. Compounder demographic updates are restricted to an explicit field whitelist:

#### A. Allowed Updatable Fields:
- `name` (Correction of spelling errors upon presentation of valid ID)
- `mobile` (Update of contact phone number)
- `address` (Update of residential dwelling or ward)
- `emergency_contact` (Update of primary caregiver or emergency phone)

#### B. Categorically Prohibited Update Fields:
Under no circumstances may a Compounder modify:
- `patient_id` (System-generated permanent healthcare identifier; immutable)
- Any clinical data field
- Any medical diagnosis
- Any doctor consultation record
- Any triage record or clinical vital sign
- Any medical prescription or drug line item
- Any laboratory order, specimen status, or test result
- ABHA verification status or national identifier hashes (managed via dedicated citizen consent workflows)

Any API payload submitted by a Compounder containing fields outside the demographic whitelist will be rejected with `HTTP 400 Bad Request` or silently stripped by the serializer, raising a security violation log.

---

## 7. Nurse vs. Compounder Responsibility Separation

### 7.1 Distinguishing Registration Authority from Clinical Access
To ensure both clinical safety and operational throughput, the platform establishes a strict architectural boundary between:
1. **Patient Registration Authority** (Clerical/Intake): The institutional authority to create new citizen records, edit demographic identifiers, and mint new OPD encounter tokens.
2. **Patient Clinical Access** (Clinical Care): The professional authority to review medical history, measure vital signs, assign triage acuity, and administer patient care.

```
+-----------------------------------------------------------------------------------+
|                        RESPONSIBILITY & AUTHORITY BOUNDARY                        |
+-----------------------------------------------------------------------------------+
| CAPABILITY / DOMAIN ACTION        | COMPOUNDER AUTHORITY    | NURSE AUTHORITY     |
+-----------------------------------+-------------------------+---------------------+
| Patient Demographic Search        | PERMITTED (Intake)      | PERMITTED (Clinical)|
| Register New Patient Profile      | PERMITTED (Sole Owner)  | PROHIBITED          |
| Update Patient Demographics       | PERMITTED (Whitelisted) | PROHIBITED          |
| Access Full Clinical EMR / Notes  | PROHIBITED (Blacklist)  | PERMITTED (Clinical)|
| Create OPD Visit & Issue Token    | PERMITTED (Sole Owner)  | PROHIBITED          |
| View OPD Queue                    | PERMITTED (Arrival/Desk)| PERMITTED (Triage)  |
| Call Next Patient for Triage      | PROHIBITED              | PERMITTED           |
| Record Triage & Vital Signs       | PROHIBITED              | PERMITTED           |
| Complete Nursing Assessment       | PROHIBITED              | PERMITTED           |
| Advance Patient to Doctor Queue   | PROHIBITED              | PERMITTED           |
| Void Unstarted Duplicate Token    | PERMITTED (Rule-bound)  | PROHIBITED          |
+-----------------------------------------------------------------------------------+
```

### 7.2 Explicit Nurse Boundary
- **What the Nurse Retains**:
  - Patient search and demographic read access strictly necessary to locate patients for clinical work.
  - Full clinical access to triage history, EMR summaries, past visit notes, and nursing care records.
  - Real-time queue viewing for the facility.
  - Authority to call the next waiting patient into the triage room (`queue.call_next` for `TRIAGE`).
  - Authority to measure and record clinical vitals (`vitals.create`, `vitals.update`).
  - Authority to conduct nursing assessments and emergency triage grading (`triage.create`, `triage.update`).
  - Authority to advance the triaged patient to the physician queue (`queue.transition` to `WAITING_FOR_DOCTOR`).
- **What the Nurse Does NOT Retain**:
  - The Nurse does **not** retain citizen registration creation authority (`patients.create`).
  - The Nurse does **not** retain demographic update authority (`patients.update_demographics`).
  - The Nurse does **not** retain OPD token issuance authority (`queue.create`, `queue.issue_token`).

*(Note: If a nurse is stationed in a single-nurse clinic under the Small-Clinic Rule, they receive these capabilities via an explicit secondary `COMPOUNDER` role assignment, NOT as a baseline Nurse privilege).*

---

## 8. OPD Queue State Machine & Transition Rules

### 8.1 The Authoritative Compounder Intake State Machine
The front-desk intake workflow proceeds through an explicit, sequential, non-clinical state machine:

```
[Citizen Presents at Desk]
           |
           v
   (Search Directory)
           |
     +-----+-----+
     |           |
(Existing)    (New Citizen)
     |           |
     |           v
     |    [REGISTER PATIENT] (patients.create)
     |           |
     +-----+-----+
           |
           v
   [CREATE OPD VISIT] (queue.create)
           |
           v
   [ISSUE OPD TOKEN] (queue.issue_token)
           |
           v
[STATUS: WAITING_FOR_TRIAGE]
   (Current Queue: TRIAGE)
```

### 8.2 Allowed vs. Prohibited Queue Transitions
The matrix below details every state transition in the clinical encounter workflow, identifying which role possesses authority to execute it:

| From Status | Target To-Status | Target Queue | Authorized Role | Compounder Allowed? | Pre-conditions & Validation Rules |
|---|---|---|---|:---:|---|
| `NONE` | `WAITING_FOR_TRIAGE` | `TRIAGE` | `COMPOUNDER` | **ALLOWED** | Patient must be registered; valid facility context. |
| `WAITING_FOR_TRIAGE` | `CANCELLED` | `NONE` | `COMPOUNDER` | **ALLOWED** | **Duplicate/Unstarted Token Rule only** (see 8.3). |
| `WAITING_FOR_TRIAGE` | `IN_TRIAGE` | `TRIAGE` | `NURSE` | **PROHIBITED** | Triggered via `queue.call_next` by Nurse. |
| `IN_TRIAGE` | `WAITING_FOR_DOCTOR` | `DOCTOR` | `NURSE` | **PROHIBITED** | Vitals record MUST exist in database. |
| `WAITING_FOR_DOCTOR` | `IN_CONSULTATION` | `DOCTOR` | `DOCTOR` | **PROHIBITED** | Triggered via `queue.call_next` by Doctor. |
| `IN_CONSULTATION` | `WAITING_FOR_LAB` | `LAB` | `DOCTOR` | **PROHIBITED** | Diagnostic test order must be attached. |
| `WAITING_FOR_LAB` | `IN_LAB` | `LAB` | `LAB_TECHNICIAN` | **PROHIBITED** | Triggered via `queue.call_next` by Lab Tech. |
| `IN_LAB` | `DOCTOR_REVIEW` | `DOCTOR` | `LAB_TECHNICIAN` | **PROHIBITED** | Lab results entered for ordered tests. |
| `IN_CONSULTATION` | `WAITING_FOR_PHARMACY` | `PHARMACY` | `DOCTOR` | **PROHIBITED** | Prescription must be generated. |
| `WAITING_FOR_PHARMACY`| `IN_PHARMACY` | `PHARMACY` | `PHARMACIST` | **PROHIBITED** | Triggered via `queue.call_next` by Pharmacist. |
| `IN_PHARMACY` | `COMPLETED` | `COMPLETED` | `PHARMACIST` | **PROHIBITED** | Medication dispensation finalized. |
| `IN_CONSULTATION` | `COMPLETED` | `COMPLETED` | `DOCTOR` | **PROHIBITED** | Consultation finalized without Rx or Labs. |

### 8.3 Strict Rule for Voiding Duplicate / Unstarted Tokens
A Compounder is granted limited authority to void an issued token (`queue.void`) strictly under the following **Duplicate/Unstarted Token Invariant**:
1. **Status Condition**: The visit status must be strictly `WAITING_FOR_TRIAGE`. If status has progressed to `IN_TRIAGE` or any subsequent stage, voiding by Compounder is blocked.
2. **Time-Window Condition**: The token must have been created within the last **30 minutes** of the same calendar day.
3. **Reason Requirement**: Operator must supply a valid enum reason code (`ACCIDENTAL_DUPLICATE`, `CITIZEN_LEFT_BEFORE_TRIAGE`, `WRONG_FACILITY_SELECTED`).
4. **Audit Logging**: The cancellation event is immutably logged with actor ID, timestamp, and void reason in `VisitStatusHistory` and `audit_log_entries`.

---

## 9. Special Small-Clinic Rule: Nurse + Compounder Dual Assignment

### 9.1 Multi-Role Architectural Invariant
In small Namma Clinics with a single nurse, the nurse must handle both intake and triage.
**INVARIANT**: **One `StaffProfile` / `UserAccount` may hold multiple active role assignments concurrently.**
Under no circumstances shall a hybrid role such as `NURSE_COMPOUNDER` be created.

```
                          Staff Member: "Anitha"
                       User Account: anitha.nurse
                                    |
                     StaffProfile: EMP-KA-BLR-0042
                                    |
            +-----------------------+-----------------------+
            |                                               |
     RoleAssignment 1                                RoleAssignment 2
       Role: NURSE                                     Role: COMPOUNDER
   Facility: PHC Ward 150                          Facility: PHC Ward 150
     Status: ACTIVE                                  Status: ACTIVE
Effective: 2026-01-01 -> NULL                   Effective: 2026-01-01 -> NULL
```

### 9.2 Effective Permission Union Calculation
The effective authorization of a dual-assigned staff member is calculated authoritatively by the backend as the **union of permissions** across all active role assignments valid for the facility and date context:

$$\text{EffectivePermissions}(\text{Anitha}) = \mathcal{P}(\text{NURSE}) \cup \mathcal{P}(\text{COMPOUNDER})$$

Anitha receives:
- From `COMPOUNDER`: `patients.create`, `patients.update_demographics`, `queue.create`, `queue.issue_token`, `queue.void`.
- From `NURSE`: `vitals.create`, `vitals.update`, `triage.create`, `triage.update`, `queue.call_next` (Triage), `queue.transition` (Triage -> Doctor).

---

## 10. Facility Staffing Rules & Administrative Workflows

### 10.1 Headcount Staffing Rule
1. **Single-Nurse Clinic**: Exactly 1 active nurse and 0 active dedicated compounders -> Dual assignment (`NURSE` + `COMPOUNDER`) is permitted.
2. **Multi-Nurse Clinic**: $>1$ active nurses -> Operational standard requires dedicated roles: Nurse 1 = `NURSE`, Nurse 2 = `NURSE`, Compounder = `COMPOUNDER`.

### 10.2 Non-Destructive Protection Rule (No Auto-Revocation)
**MANDATE**: **If a second nurse is hired or posted to the facility, the system shall NOT automatically revoke `COMPOUNDER` from the existing staff member.**

Automatic revocation in a clinical environment is hazardous and could paralyze front-desk intake during shift changes, temporary leaves, or orientation periods.

### 10.3 Explicit Administrative De-Assignment Workflow
When the facility is ready to transition to dedicated intake staffing:
1. Clinic Admin navigates to the staff management console.
2. Selects Nurse Anitha -> Role Assignments table -> `COMPOUNDER` row.
3. Clicks **End Role Assignment**.
4. Enters effective end date (`today`) and administrative reason (`DEDICATED_COMPOUNDER_ONBOARDED`).
5. Domain service `end_role_assignment` executes atomically, setting `is_active=False` and `effective_to=today`.
6. Full audit log entry recorded.
7. Next API request by Anitha gracefully recalculates permissions, dropping intake authority while preserving uninterrupted nursing privileges.
---

## 11. Explicit Domain Actions & Permission Vocabulary

To move beyond ambiguous CRUD (C/R/U/D) notation, the Namma Clinic platform formalizes an authoritative **Domain Action Vocabulary**. Every protected API operation maps to a distinct domain action code, authorized roles, and scoping boundaries:

### 11.1 Patient Domain Actions
| Domain Action Code | Action Description | Authorized Roles | Enforced Scope |
|---|---|---|---|
| `patients.read` | View patient demographic profile (whitelist only for intake staff; full clinical for clinical staff). | `COMPOUNDER`, `NURSE`, `DOCTOR`, `HOSPITAL_ADMIN`, `DISTRICT_OFFICER`, `LAB_TECHNICIAN`, `PHARMACIST` | Compounder/Nurse/Doctor/Admin: Facility. DHO: District. |
| `patients.create` | Register new citizen in the health registry. | `COMPOUNDER`, `HOSPITAL_ADMIN` | Actor's assigned facility only. |
| `patients.update_demographics` | Update whitelisted demographic fields (`name`, `mobile`, `address`, `emergency_contact`). | `COMPOUNDER`, `HOSPITAL_ADMIN` | Actor's assigned facility only. |
| `patients.read_clinical_record` | Access longitudinal EMR, consultation history, diagnostic reports, and medical notes. | `DOCTOR`, `NURSE` (Nursing context), `DISTRICT_OFFICER` (Audit/Read-Only) | Clinical encounter context. **COMPOUNDER PROHIBITED.** |

### 11.2 OPD Queue Domain Actions
| Domain Action Code | Action Description | Authorized Roles | Enforced Scope |
|---|---|---|---|
| `queue.view` | View real-time OPD queue list and waiting token counts. | `COMPOUNDER`, `NURSE`, `DOCTOR`, `HOSPITAL_ADMIN`, `DISTRICT_OFFICER`, `LAB_TECHNICIAN`, `PHARMACIST` | Actor's assigned facility. DHO: District clinics. |
| `queue.create` | Create new outpatient visit encounter. | `COMPOUNDER`, `HOSPITAL_ADMIN` | Actor's assigned facility only. |
| `queue.issue_token` | Atomically mint sequential daily token for facility and place in `WAITING_FOR_TRIAGE`. | `COMPOUNDER`, `HOSPITAL_ADMIN` | Actor's assigned facility only. |
| `queue.call_next` | Dequeue highest priority waiting patient into active service room. | `NURSE` (Triage), `DOCTOR` (Consultation), `LAB_TECHNICIAN` (Lab), `PHARMACIST` (Pharmacy) | Specific clinical queue within actor's facility. **COMPOUNDER PROHIBITED.** |
| `queue.transition` | Advance encounter through clinical workflow stages. | `NURSE` (Triage->Doc), `DOCTOR` (Doc->Lab/Pharm/Complete), `LAB_TECHNICIAN`, `PHARMACIST` | Encounter context in actor's facility. **COMPOUNDER PROHIBITED.** |
| `queue.void` | Cancel an un-triaged duplicate token issued in error within 30 minutes. | `COMPOUNDER`, `HOSPITAL_ADMIN` | Actor's assigned facility. Status MUST be `WAITING_FOR_TRIAGE`. |

### 11.3 Triage & Clinical Domain Actions
| Domain Action Code | Action Description | Authorized Roles | Enforced Scope |
|---|---|---|---|
| `vitals.create` | Record initial clinical vital signs for an encounter. | `NURSE` | Encounter context in actor's facility. **COMPOUNDER PROHIBITED.** |
| `vitals.update` | Correct or update measured vital signs during triage. | `NURSE` | Encounter context in actor's facility. **COMPOUNDER PROHIBITED.** |
| `triage.create` | Complete triage assessment and assign clinical acuity level. | `NURSE` | Encounter context in actor's facility. **COMPOUNDER PROHIBITED.** |
| `triage.update` | Modify nursing triage notes or acuity classification. | `NURSE` | Encounter context in actor's facility. **COMPOUNDER PROHIBITED.** |
| `consultation.create` | Conduct clinical consultation, enter diagnoses, write prescriptions, and order tests. | `DOCTOR` | Encounter context in actor's facility. **NURSE/COMPOUNDER PROHIBITED.** |

### 11.4 Staff & IAM Administration Domain Actions
| Domain Action Code | Action Description | Authorized Roles | Enforced Scope |
|---|---|---|---|
| `staff.create` | Create new professional identity (`Person` + `StaffProfile`). | `HOSPITAL_ADMIN` (Facility staff), `DISTRICT_OFFICER` (District staff/admins) | Target facility must match actor's scope. |
| `staff.invite` | Issue initial activation credentials or invitation link to staff. | `HOSPITAL_ADMIN`, `DISTRICT_OFFICER` | Facility/District scope. |
| `staff.assign_role` | Assign an operational role (`StaffRoleAssignment`) to staff. | `HOSPITAL_ADMIN` (Facility operational roles), `DISTRICT_OFFICER` (Admins/DHO staff) | Cannot assign privileged roles beyond actor's authority. |
| `staff.end_role` | Terminate an active role assignment with effective end date. | `HOSPITAL_ADMIN`, `DISTRICT_OFFICER` | Staff within actor's operational scope. |
| `staff.assign_facility`| Post a staff member to a facility or department. | `HOSPITAL_ADMIN` (Own facility), `DISTRICT_OFFICER` (District facilities) | Target facility must match actor's administrative scope. |
| `staff.transfer` | Atomically transfer staff from Source to Destination facility. | `DISTRICT_OFFICER` (Authorizing authority), `HOSPITAL_ADMIN` (Initiating facility) | Both facilities must reside in DHO's district. |

---

## 12. Comprehensive Seven-Role Authority & Permission Matrix

The revised authority matrix explicitly separates **Resource Access**, **Domain Actions**, and **Scope Boundaries**. Crucially, it does **not** silently expand DHO or Clinic Admin access into clinical consultations or dispensing.

| Resource / Entity | Domain Action | DISTRICT_OFFICER (DHO) | HOSPITAL_ADMIN (CLINIC ADMIN) | DOCTOR | NURSE | COMPOUNDER | LAB_TECHNICIAN | PHARMACIST |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Patient Demographics** | `read` | ✔ (District) | ✔ (Facility) | ✔ (Facility) | ✔ (Facility) | **✔ (Whitelist)** | ✔ (Minimal) | ✔ (Minimal) |
| | `create` | ✖ | ✔ (Facility) | ✖ | ✖ | **✔ (Facility)** | ✖ | ✖ |
| | `update_demographics` | ✖ | ✔ (Facility) | ✖ | ✖ | **✔ (Whitelist)** | ✖ | ✖ |
| **Clinical Records / EMR** | `read_clinical_record` | ✔ (Read-Only Audit) | ✖ | **✔ (Full)** | **✔ (Nursing)** | **✖ PROHIBITED** | ✔ (Lab orders) | ✔ (Rx orders) |
| | `write_clinical_notes` | ✖ | ✖ | **✔ (Author)** | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| **OPD Visit & Queue** | `queue.view` | ✔ (District) | ✔ (Facility) | ✔ (Doctor queue) | ✔ (Triage queue) | **✔ (Arrival queue)**| ✔ (Lab queue) | ✔ (Pharm queue) |
| | `queue.create` | ✖ | ✔ (Facility) | ✖ | ✖ | **✔ (Facility)** | ✖ | ✖ |
| | `queue.issue_token` | ✖ | ✔ (Facility) | ✖ | ✖ | **✔ (Facility)** | ✖ | ✖ |
| | `queue.call_next` | ✖ | ✖ | ✔ (Doctor) | ✔ (Triage) | **✖ PROHIBITED** | ✔ (Lab) | ✔ (Pharmacy) |
| | `queue.transition` | ✖ | ✖ | ✔ (Consultation) | ✔ (Triage->Doc) | **✖ PROHIBITED** | ✔ (Test results)| ✔ (Dispense) |
| | `queue.void` | ✖ | ✔ (Facility) | ✖ | ✖ | **✔ (Duplicate/30m)**| ✖ | ✖ |
| **Triage & Vitals** | `vitals.create / update` | ✖ | ✖ | ✖ | **✔ (Facility)** | **✖ PROHIBITED** | ✖ | ✖ |
| | `triage.create / update` | ✖ | ✖ | ✖ | **✔ (Facility)** | **✖ PROHIBITED** | ✖ | ✖ |
| **Consultation & Rx** | `consultation.create` | ✖ | ✖ | **✔ (Facility)** | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| | `prescription.create` | ✖ | ✖ | **✔ (Facility)** | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| **Laboratory** | `specimen.collect` | ✖ | ✖ | ✖ | ✔ (Bedside) | **✖ PROHIBITED** | **✔ (Facility)** | ✖ |
| | `lab_results.create` | ✖ | ✖ | ✖ | ✖ | **✖ PROHIBITED** | **✔ (Facility)** | ✖ |
| **Pharmacy** | `prescription.verify` | ✖ | ✖ | ✖ | ✖ | **✖ PROHIBITED** | ✖ | **✔ (Facility)** |
| | `medicine.dispense` | ✖ | ✖ | ✖ | ✖ | **✖ PROHIBITED** | ✖ | **✔ (Facility)** |
| | `inventory.manage` | ✔ (District Audit) | ✔ (Facility Audit)| ✖ | ✖ | **✖ PROHIBITED** | ✖ | **✔ (Facility)** |
| **Procurement** | `po.create` | ✖ | ✖ | ✖ | ✖ | **✖ PROHIBITED** | ✖ | **✔ (Facility)** |
| | `po.approve` | ✔ (District review) | **✔ (Facility)** | ✖ | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| **Staff & IAM** | `staff.create / invite` | ✔ (District scope) | ✔ (Facility scope)| ✖ | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| | `staff.assign_role` | ✔ (Admins/DHO) | ✔ (Operational) | ✖ | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| | `staff.transfer` | **✔ (Authorize)** | ✔ (Initiate) | ✖ | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| **Facility Management** | `facility.create / edit` | **✔ (District)** | ✖ | ✖ | ✖ | **✖ PROHIBITED** | ✖ | ✖ |
| **Audit Logs** | `audit.view` | ✔ (District logs) | ✔ (Facility logs) | ✖ | ✖ | **✖ PROHIBITED** | ✖ | ✖ |

*(Governance Note: Any future expansion of administrative staff into direct clinical consultation or prescription modification requires formal Medical Directorate review and is strictly blocked).*

---

## 13. Facility + Role Authorization Tuple Invariant

### 13.1 The Authorization Tuple Requirement
A critical principle established by this architecture is that **a role assignment NEVER grants access by itself**. Holding a role code in isolation is necessary but insufficient.

**ARCHITECTURAL INVARIANT 3 (The Authorization Tuple)**:
$$\text{Authorized}(u, a, f, t) \iff \langle u, \text{StaffProfile}, \text{FacilityAssignment}, \text{RoleAssignment}, t, \text{Perm}, \text{Scope} \rangle = \text{VALID}$$

Every protected API transaction must successfully validate the complete **7-element authorization tuple**:
1. **Authenticated User Account (`UserAccount`)**: Request contains a cryptographically verified session credential.
2. **Active Staff Profile (`StaffProfile`)**: Linked `StaffProfile` exists and has `status == 'ACTIVE'`.
3. **Active Facility Assignment (`FacilityAssignment`)**: An active `StaffFacilityAssignment` exists linking the staff member to the target facility $f$, where `effective_from <= t <= (effective_to OR inf)` and `is_active == True`.
4. **Active Role Assignment (`RoleAssignment`)**: An active `StaffRoleAssignment` exists linking the staff member to a role possessing action $a$, where `effective_from <= t <= (effective_to OR inf)` and `is_active == True`.
5. **Valid Effective Dates ($t$)**: Current server execution timestamp falls strictly within the validity window of both facility and role assignments.
6. **Required Action Permission ($\text{Perm}$)**: The required domain action code is present in the role's assigned permission set.
7. **Spatial Scope Alignment ($\text{Scope}$)**: Target entity facility ID matches the actor's authorized facility (or district for DHO).

### 13.2 Concrete Cross-Facility Example
- Staff member **Ramesh** holds `COMPOUNDER` role at **Facility A (PHC Malleshwaram)**.
- Ramesh sends an API request to `POST /api/visits/` with `facility: B (PHC Rajajinagar)`.
- **Evaluation**:
  - `UserAccount`: Valid.
  - `StaffProfile`: Active.
  - `RoleAssignment`: `COMPOUNDER` (Valid).
  - `FacilityAssignment`: Valid for Facility A; **INVALID for Facility B**.
- **Outcome**: Authorization tuple fails element 3 and element 7. Request is rejected with **`HTTP 403 Forbidden`**. Ramesh cannot perform Compounder actions at Facility B without an explicit administrative posting to Facility B.

---

## 14. District Health Officer (DHO) Authority & Scope Invariant

### 14.1 DHO District-Scoped Governance Authority
The `DISTRICT_OFFICER` possesses executive health governance authority across their assigned district:
- **Facility Oversight**: Create and activate primary health facilities within their assigned district; view operational capacity, bed occupancy, and infrastructure tickets across all district facilities.
- **Administrative Appointment**: Appoint and assign Clinic Administrators (`HOSPITAL_ADMIN`) for facilities located in their district.
- **Workforce Visibility**: Review district-wide clinical and clerical staffing distributions and approve inter-facility staff transfers.
- **Epidemiological & Quality Surveillance**: Monitor district disease trends, fever outbreaks, quality audit scores, and medicine supply chain status.

### 14.2 The Fail-Closed District Invariant
**CRITICAL INVARIANT**: **`NULL district != global access`. A District Health Officer MUST have an explicit, non-null `assigned_district`. If `assigned_district` is `NULL`, all authorization checks fail closed with `HTTP 403 Forbidden`.**

```python
# Authoritative Fail-Closed District Scoping Logic
if user.role == 'DISTRICT_OFFICER':
    if not user.assigned_district_id:
        logger.security_alert(f"DISTRICT_OFFICER '{user.username}' attempted access with NULL district. Failing closed.")
        return [] # Zero facilities accessible
    return list(Facility.objects.filter(district_id=user.assigned_district_id).values_list('id', flat=True))
```

DHO authority is strictly supervisory: DHOs cannot perform clinical consultations, record vitals, write prescriptions, dispense drugs, or manage staff in other districts.

---

## 15. Hospital Admin / Clinic Admin Authority & Delegation Model

### 15.1 Facility-Scoped Staff Management Authority
The `HOSPITAL_ADMIN` role (representing the Clinic Administrator) holds staff management authority strictly bounded to their assigned facility:
- **Onboard Facility Staff**: Register new personnel and create `StaffProfile` records for `DOCTOR`, `NURSE`, `COMPOUNDER`, `LAB_TECHNICIAN`, and `PHARMACIST`.
- **Assign Facility Roles**: Grant operational roles (`StaffRoleAssignment`) to staff stationed at their facility.
- **Enact Small-Clinic Dual Assignment**: In single-nurse clinics, grant dual `(NURSE + COMPOUNDER)` roles to an existing staff nurse.
- **Terminate Facility Roles**: End operational role assignments when roles transition or dedicated staff are onboarded.
- **Initiate Transfers**: Initiate staff transfer requests to move personnel to other clinics (subject to DHO sign-off).

### 15.2 Anti-Escalation & Delegation Constraints
To eliminate horizontal and vertical privilege escalation, the domain services enforce the following boundaries:
1. **No Self-Elevation**: A Clinic Admin cannot assign any role to their own user account (`actor_staff.id != target_staff.id`).
2. **No Privileged Role Escalation**: A Clinic Admin cannot assign `DISTRICT_OFFICER`, `SYSTEM_ADMIN`, or `SUPERUSER`. Attempting to pass these role codes raises `UnauthorizedDomainAction`.
3. **No Cross-Facility Staff Mutations**: A Clinic Admin at Facility A cannot create staff, assign roles, or deactivate personnel assigned to Facility B.
4. **No Peer Admin Creation Outside Scope**: A Clinic Admin cannot create another `HOSPITAL_ADMIN` for a foreign facility.
5. **No Clinical Alteration**: A Clinic Admin cannot modify physician consultations, diagnoses, or clinical vitals.
---

## 16. Staff Lifecycle Management, State Transitions & Session Semantics

### 16.1 Canonical Staff Lifecycle States
To replace the incomplete status set in `StaffProfile`, the platform formalizes five canonical operational lifecycle states:

```
                +-------------------+
                |      INVITED      |
                +-------------------+
                          |
                          | (Account Activation / First Login)
                          v
                +-------------------+
   +----------->|      ACTIVE       |<----------+
   |            +-------------------+           |
   |              |               ^             |
   |   (Violation |               | (Reinstated)| (Transfer Completed)
   |    / Leave)  v               |             |
   |            +-------------------+           |
   |            |     SUSPENDED     |           |
   |            +-------------------+           |
   |                      |                     |
   |                      | (Separation)        |
   |                      v                     |
   |            +-------------------+           |
   |            |    DEACTIVATED    |           |
   |            +-------------------+           |
   |                      |                     |
   | (Initiate Transfer)  |                     |
   +----------------------+                     |
                          |                     |
                          v                     |
                +-------------------+           |
                | TRANSFER_PENDING  |-----------+
                +-------------------+
```

### 16.2 Accurate JWT Session Semantics & Authorization Invariants
During the PM/RSA review, a critical architectural clarification was established regarding stateless tokens:

**SECURITY REALITY**: **Setting `User.is_active = False` in the database does NOT by itself immediately revoke an already-issued, unexpired stateless JWT access token held in client memory.**

If relying solely on stateless JWT verification (which only cryptographically validates token signature and expiry), a suspended or rogue staff member could continue issuing API requests until the access token expires (typically 15 to 60 minutes).

#### Authoritative Invalidation Invariant:
**Every protected API request must reject access when the underlying account, staff profile, role assignment, or facility assignment is no longer active or valid.**

To enforce this without sacrificing performance:
1. **Request-Time State Validation**: DRF permission classes (`IsActiveStaff`, `HasFacilityScope`) query the live database/cache on every authenticated request to verify:
   - `request.user.is_active == True`
   - `request.user.staff_profile.status == 'ACTIVE'`
   - Target facility matches an active, non-expired `StaffFacilityAssignment`.
2. **Explicit Response Semantics**:
   - **`HTTP 401 Unauthorized`**: Returned when authentication fails (token missing, signature invalid, token expired, or user account not found).
   - **`HTTP 403 Forbidden`**: Returned when the user is cryptographically authenticated, but the account is `SUSPENDED` or `DEACTIVATED`, the staff profile is inactive, or the user lacks permission/facility scope.

---

## 17. Security Architecture & Threat Mitigation Matrix

The table below details the authoritative technical mitigation mechanisms against all primary security threats and privilege escalation vectors:

| # | Threat / Attack Vector | Severity | Vulnerability Mechanism in Legacy Code | Authoritative Backend Defense & Invariant |
|---|---|:---:|---|---|
| 1 | **Compounder changing medical diagnosis** | CRITICAL | Shared clinical write permissions or loose generic viewset update routes. | Blocked by DRF permission class `HasPermission` requiring `diagnosis.update` (exclusive to `DOCTOR`). Enforced by `IsMedicalOfficer` guard. HTTP 403 Forbidden returned. |
| 2 | **Compounder altering triage or vitals** | CRITICAL | Compounder submitting raw vitals payload to `/api/triage/`. | `TriageVitalsViewSet` requires `triage.create`/`triage.update` (exclusive to `NURSE`). Compounder lacks this permission in `ROLE_PERMISSIONS`. Attempt fails closed with HTTP 403. |
| 3 | **Compounder tampering with prescription** | CRITICAL | Direct REST mutation to `/api/prescriptions/`. | `PrescriptionViewSet` requires `prescription.create`/`prescription.update` (exclusive to `DOCTOR`). Compounder lacks code. Mutation rejected with HTTP 403. |
| 4 | **Compounder accessing foreign facility records** | HIGH | Forging `facility_id` in token issuance or registration payload. | `can_access_facility(request.user, facility_id)` checks `user.assigned_facility_id`. Object-level `FacilityScopedPermission` blocks cross-facility reads/writes. |
| 5 | **Nurse modifying doctor consultation notes** | HIGH | Nurse updating `/api/consultations/{id}/` via frontend or API. | `ConsultationViewSet` requires `consultation.update` (exclusive to `DOCTOR`). Object-level check ensures only attending physician or authorized chief medical officer can edit within 24h window. |
| 6 | **Clinic Admin assigning themselves DHO** | CRITICAL | Admin calling `/api/v1/accounts/role-assignments/` with role `DISTRICT_OFFICER`. | Domain service `assign_role` checks: If target role is `DISTRICT_OFFICER`, `SYSTEM_ADMIN`, or `SUPERUSER`, actor MUST possess `SUPERUSER` or State Health Director authority. |
| 7 | **Clinic Admin creating Admin in another clinic** | HIGH | Admin creating `StaffFacilityAssignment` for foreign facility. | `assign_facility` validates: If actor is `HOSPITAL_ADMIN`, target `facility` MUST strictly match actor's `assigned_facility`. Cross-facility assignment raises `UnauthorizedDomainAction`. |
| 8 | **Ordinary user elevating own role** | CRITICAL | User submitting `PUT /api/users/{id}/` with `role='HOSPITAL_ADMIN'`. | Direct update of `role` field on `UserViewSet` disabled; role assignment handled exclusively via domain service `assign_role`. Self-assignment strictly prohibited in service layer (`actor_staff.id != target_staff.id`). |
| 9 | **Privilege escalation via crafted API calls** | CRITICAL | Attacker bypassing frontend UI guards using `curl` / Postman. | Authoritative backend enforcement: Every endpoint independently checks authentication, active staff profile, dynamic permission union, and facility boundary before touching database. |

---

## 18. Required Backend Changes

### 18.1 Accounts Application (`backend/apps/accounts/`)
1. **`models.py`**:
   - Add `COMPOUNDER = 'COMPOUNDER', 'Compounder'` to `RoleChoices`.
   - Update `StaffProfile.status` choices: `INVITED`, `ACTIVE`, `SUSPENDED`, `TRANSFER_PENDING`, `DEACTIVATED`, `PROBATION`, `RETIRED`, `RESIGNED`.
2. **`permissions.py`**:
   - Add `'COMPOUNDER'` role definition to `ROLE_PERMISSIONS`:
     ```python
     'COMPOUNDER': {
         'patients.read', 'patients.create', 'patients.update_demographics',
         'queue.view', 'queue.create', 'queue.issue_token', 'queue.void',
         'clinic.view', 'dashboard.view'
     }
     ```
   - Remove `'patients.create'`, `'queue.create'`, and demographic update permissions from `NURSE` role in `ROLE_PERMISSIONS`.
   - Implement `get_effective_user_permissions(user)` computing the dynamic union of permissions across active `StaffRoleAssignment` records.
   - Refactor `has_role_permission(user, permission_name)` to evaluate against `get_effective_user_permissions(user)`.
   - Fix DHO scoping in `get_accessible_facility_ids_for_user`: If `user.role == 'DISTRICT_OFFICER'` and `not user.assigned_district_id`, return `[]` (fail-closed).
   - Fix `can_access_facility`: If `user.role == 'DISTRICT_OFFICER'` and `not user.assigned_district_id`, return `False`.
3. **`services.py`**:
   - Update `assign_role`:
     - Add security check: If actor is `HOSPITAL_ADMIN`, enforce that target staff belongs to actor's facility and target role is within operational staff roles (`DOCTOR`, `NURSE`, `COMPOUNDER`, `LAB_TECHNICIAN`, `PHARMACIST`).
     - Block self-assignment (`actor_staff.id != staff_profile.id`).
   - Update `update_staff_status`:
     - Synchronize `user.is_active = (new_status == 'ACTIVE')` when status transitions to `SUSPENDED` or `DEACTIVATED`.

### 18.2 Patients & Visits Applications
1. **`apps/patients/views.py`**:
   - Decouple clinical data access: Restrict `PatientTimelineView` to clinical roles (`DOCTOR`, `NURSE`, `HOSPITAL_ADMIN`, `DISTRICT_OFFICER`). Compounder accessing timeline receives `HTTP 403 Forbidden`.
   - Enforce Compounder demographic update whitelist: Reject modifications to clinical, diagnostic, or identifier fields.
2. **`apps/visits/views.py`**:
   - `VisitViewSet.create`: Verify actor has `queue.create`. Scoped strictly to actor's primary facility.
   - `VisitViewSet.call_next_patient`: Add check blocking `COMPOUNDER` from calling any clinical queue.
   - `VisitViewSet.transition_status`: Add explicit check preventing `COMPOUNDER` from advancing visits to `DOCTOR` or `TRIAGE` completed statuses.

---

## 19. Required Frontend Changes

### 19.1 Type Definitions (`frontend/src/types/index.ts`)
- Update `Role` union type:
  ```typescript
  export type Role =
    | 'DISTRICT_OFFICER'
    | 'HOSPITAL_ADMIN'
    | 'DOCTOR'
    | 'NURSE'
    | 'COMPOUNDER'
    | 'LAB_TECHNICIAN'
    | 'PHARMACIST';
  ```
- Update `UserProfile` interface to support multi-role array:
  ```typescript
  export interface UserProfile {
    id: number;
    username: string;
    full_name: string;
    email: string;
    role: Role; // Primary role
    roles?: Role[]; // Full active role assignment array
    permissions: string[];
  }
  ```

### 19.2 Permissions & Route Guards (`frontend/src/utils/permissions.ts`)
- Add `COMPOUNDER` to `ROLE_PERMISSIONS`:
  ```typescript
  COMPOUNDER: new Set([
    'patients.read', 'patients.create', 'patients.update_demographics',
    'queue.view', 'queue.create', 'queue.issue_token', 'queue.void',
    'clinic.view', 'dashboard.view'
  ]),
  ```
- Update `HUMAN_ROLE_LABELS`:
  ```typescript
  COMPOUNDER: 'Compounder / Registration Clerk',
  HOSPITAL_ADMIN: 'Clinic Administrator',
  ```
- Update `ROLE_ALLOWED_PATHS`:
  ```typescript
  COMPOUNDER: ['/', '/patients', '/queue', '/alerts'],
  ```

### 19.3 Context & Navigation (`frontend/src/context/AuthContext.tsx` & `navigationConfig.ts`)
- Update `AuthContext` to expose `hasPermission(permission: string)` derived from `user.permissions` payload.
- Update `navigationConfig.ts` to show registration and token management items for `COMPOUNDER`. For dual-role nurses, navigation renders both Intake and Clinical modules.

---

## 20. Required Database & Migration Changes

### 20.1 Database Schema Migrations
1. **Migration `0003_add_compounder_role` (`apps/accounts`)**:
   - Update `role` column choices on `users` table.
   - Add initial seed row to `role_masters` table for `COMPOUNDER`.
2. **Migration `0004_update_staff_status_choices` (`apps/accounts`)**:
   - Alter `status` field check constraint on `staff_profiles` table to accommodate `INVITED`, `ACTIVE`, `SUSPENDED`, `TRANSFER_PENDING`, `DEACTIVATED`, `PROBATION`, `RETIRED`, `RESIGNED`.

### 20.2 Data Integrity Constraints & Indexes
- Composite index on `staff_role_assignments(staff_id, is_active, effective_from, effective_to)`.
- Database constraint `chk_staff_role_dates`: `effective_to IS NULL OR effective_to >= effective_from`.

---

## 21. API Changes & Contract Specifications

### 21.1 Updated Profile Payload: `GET /api/auth/me/`
```json
{
  "id": 104,
  "username": "anitha.nurse",
  "full_name": "Nurse Anitha R",
  "email": "anitha@nammaclinic.kar.gov.in",
  "phone": "+91-9876543210",
  "role": "NURSE",
  "roles": ["NURSE", "COMPOUNDER"],
  "role_display": "Staff Nurse / Compounder (Dual Role)",
  "assigned_facility": 1,
  "assigned_district": 1,
  "facility_details": {
    "id": 1,
    "facility_code": "KA-BLR-PHC-001",
    "facility_name": "Namma Clinic Local PHC",
    "facility_type": "NAMMA_CLINIC",
    "district_name": "Bengaluru Urban"
  },
  "permissions": [
    "patients.read",
    "patients.create",
    "patients.update_demographics",
    "vitals.create",
    "vitals.update",
    "triage.create",
    "triage.update",
    "queue.view",
    "queue.create",
    "queue.issue_token",
    "queue.call_next",
    "queue.transition",
    "queue.void",
    "clinic.view",
    "dashboard.view",
    "ncd.view",
    "ncd.create",
    "surveillance.view"
  ],
  "scope_type": "FACILITY"
}
```

---

## 22. Audit & Regulatory Compliance Framework

### 22.1 Statutory Standards Alignment
1. **DISHA (Digital Information Security in Healthcare Act)**: Least privilege enforcement ensures intake operators cannot view sensitive clinical notes or diagnoses.
2. **ABDM (Ayushman Bharat Digital Mission)**: Strict separation between health professional identities (HPR) and administrative facility operators.

### 22.2 Audit Event Schema
All IAM mutations are logged in `audit_log_entries`:
- `actor_staff`, `actor_role_snapshot`, `facility`, `action_type`, `table_name`, `record_id`, `payload_before`, `payload_after`, `correlation_id`, `timestamp`.

---

## 23. Phased Implementation Roadmap

```
[Phase 1: DB & IAM Models]
  - RoleChoices & RoleMaster update
  - StaffProfile lifecycle states migration
        |
        v
[Phase 2: Backend Permission Union Engine]
  - get_effective_user_permissions implementation
  - Fix DHO NULL district scoping vulnerability
  - Update ROLE_PERMISSIONS matrix with new action vocabulary
        |
        v
[Phase 3: Domain Service & Viewset Enforcements]
  - Protect PatientViewSet & VisitViewSet
  - Implement Compounder field whitelists & clinical blacklists
  - Update RoleAssignmentViewSet with anti-escalation rules
        |
        v
[Phase 4: Frontend Types, AuthContext & Router]
  - Add COMPOUNDER role & human labels
  - Multi-role profile support in AuthContext
  - Update navigation shell & route guards
        |
        v
[Phase 5: Verification & End-to-End Regression]
  - IAM unit tests & security penetration tests
  - End-to-end browser walkthroughs of Compounder and Dual-Role Nurse
```

---

## 24. Testing Strategy & Test Specifications

### 24.1 IAM Unit & Service Tests (`test_iam_authority.py`)
- `test_compounder_has_intake_permissions`: Verify `COMPOUNDER` possesses `patients.create`, `queue.create`, and `queue.issue_token`.
- `test_nurse_lacks_default_registration_permissions`: Verify pure `NURSE` role lacks `patients.create` and `queue.issue_token`.
- `test_dual_role_nurse_compounder_union_permissions`: Verify a staff member with both active assignments receives the exact mathematical union of permissions.
- `test_expired_role_assignment_excluded_from_union`: Verify that an assignment where `effective_to < today` is excluded from effective permissions.
- `test_dho_null_district_fails_closed`: Verify that a `DISTRICT_OFFICER` with `assigned_district=None` receives `[]` accessible facilities and `HTTP 403 Forbidden`.

### 24.2 Security & Penetration Negative Tests (`test_security_rbac.py`)
- `test_compounder_cannot_enter_triage_vitals`: Assert `POST /api/triage/` by Compounder returns `HTTP 403 Forbidden`.
- `test_compounder_cannot_enter_diagnosis`: Assert `POST /api/consultations/` with diagnosis returns `HTTP 403 Forbidden`.
- `test_compounder_cannot_dispense_medicines`: Assert `POST /api/pharmacy/dispense/` returns `HTTP 403 Forbidden`.
- `test_compounder_cannot_read_clinical_timeline`: Assert `GET /api/patients/{id}/timeline/` returns `HTTP 403 Forbidden`.
- `test_compounder_cannot_access_foreign_facility_queue`: Assert `GET /api/visits/?facility={foreign}` returns empty queryset or 403.
- `test_clinic_admin_cannot_assign_dho_role`: Assert `HOSPITAL_ADMIN` attempting to assign `DISTRICT_OFFICER` raises `UnauthorizedDomainAction`.
- `test_clinic_admin_cannot_manage_foreign_staff`: Assert `HOSPITAL_ADMIN` assigning staff outside their facility raises `UnauthorizedDomainAction`.

---

## 25. Risks, Assumptions & Open Questions

1. **Risk: Legacy `/api/` endpoints bypass `StaffRoleAssignment`**: Refactoring `has_role_permission` to call `get_effective_user_permissions(user)` ensures all legacy endpoints inherit multi-role support.
2. **Open Question: Token Voiding Window**: Restricting unstarted token voiding to within 30 minutes of issuance provided `status == 'WAITING_FOR_TRIAGE'` balances clerical correction with queue auditability.
3. **Demo Persona Credentials**: A default demo user for Compounder (e.g. `compounder.phc1`) should be added to `seed_demo` and the login persona switcher during Phase 4.

---

## 26. IAM Security Invariants (`IAM_SECURITY_INVARIANTS`)

The Namma Clinic Staff IAM and Authority architecture mandates strict enforcement of the following sixteen core security invariants:

1. **DHO District Invariant**: `NULL DHO district != global access`. A `DISTRICT_OFFICER` without an active, non-null `assigned_district` must fail closed with `HTTP 403 Forbidden` on all facility and district queries.
2. **Facility Assignment Requirement**: A role assignment without an active, matching `StaffFacilityAssignment` grants zero facility access.
3. **Scope-Validity Invariant**: Every operational action must be executed strictly within the actor's authorized facility or district boundary.
4. **Clinical Action Prohibition**: The `COMPOUNDER` role is strictly non-clinical and cannot record vitals, measure clinical parameters, or enter diagnoses.
5. **Pharmacy Action Prohibition**: The `COMPOUNDER` role is strictly non-pharmacy and cannot verify prescriptions, dispense medications, or manage drug stock.
6. **Laboratory Result Prohibition**: The `COMPOUNDER` role cannot collect diagnostic specimens, enter lab results, or verify lab reports.
7. **Nurse Token Issuance Prohibition**: The baseline `NURSE` role cannot issue OPD tokens or register patients unless explicitly granted a secondary `COMPOUNDER` role assignment.
8. **Compounder Triage Prohibition**: The `COMPOUNDER` role cannot call patients for triage or advance encounters out of the `WAITING_FOR_TRIAGE` queue.
9. **Self-Assignment Prohibition**: No staff member or administrator may assign roles, extend dates, or alter status on their own account.
10. **Administrative Anti-Escalation**: Clinic Administrators (`HOSPITAL_ADMIN`) cannot assign roles outside permitted operational scope (`DISTRICT_OFFICER`, `SYSTEM_ADMIN`, `SUPERUSER` strictly blocked).
11. **Cross-Facility Mutation Block**: Clinic Administrators cannot onboard staff, post personnel, or assign roles for facilities other than their assigned facility.
12. **Temporal Validity Invariant**: Expired (`effective_to < today`) or inactive (`is_active = False`) role or facility assignments are completely ignored during permission resolution.
13. **Session Invalidation Invariant**: Suspended or deactivated staff accounts cannot execute protected APIs; every protected endpoint actively verifies live account and profile status.
14. **Dual-Role Strict Union**: Dual-role users receive strictly the mathematical union of their explicitly assigned, active roles with zero implicit privilege expansion.
15. **Non-Destructive Role Independence**: Modifying, ending, or removing one role assignment must never silently remove, alter, or compromise another concurrent role assignment on the same staff profile.
16. **Immutable Audit Invariant**: All additions, modifications, transfers, deactivations, and status transitions affecting staff, roles, or facility postings must produce an immutable audit log entry.

---
**End of Architecture Specification: IAM_STAFF_ROLE_AUTHORITY_DESIGN.md**
