# Namma Clinic — Role-Based Access Control (RBAC) & DHO Readiness Analysis

## 1. Executive Summary

This document inspects the Role-Based Access Control (RBAC), facility scoping mechanisms, data boundaries, and District Health Officer (DHO) operational visibility within the Namma Clinic repository.

Access control is enforced via a two-layer security framework:
1. **Frontend Route Guards (`isPathAllowedForRole` in `frontend/src/utils/permissions.ts`)**: Evaluates `user.role` against a whitelist of allowed URL paths.
2. **Backend API Scoping (`HasPermission`, `HasFacilityScope` in `apps/accounts/permissions.py`)**: Checks DRF permission codes against `ROLE_PERMISSIONS` and restricts querysets using `get_accessible_facility_ids_for_user(request.user)`.

---

## 2. Role & Permission Inventory

The system implements 6 primary roles defined in `apps.accounts.models.RoleChoices`, with Superuser inheriting administrative bypass:

| Role Name | Internal Enum | Permissions Set | Data Scope | Clinic Scope | District Scope | Allowed Frontend Routes |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Super Admin** | `is_superuser=True` | Full unrestricted access | System-Wide | All Facilities | All Districts | All Routes |
| **District Health Officer (DHO)** | `DISTRICT_OFFICER` | `district.view`, `hospital.view`, `clinic.view`, `reports.view`, `reports.export`, `audit_logs.view`, `dashboard.view`, `referrals.view`, `inventory.view`, `queue.view`, `lab_orders.view`, `patients.view`, `po.view`, `vendor.view` | District-Wide (Read-Only) | All facilities in assigned district | `assigned_district` | `/`, `/network`, `/facilities`, `/queue`, `/referrals`, `/pharmacy`, `/reports`, `/alerts`, `/compliance`, `/audit` |
| **Hospital Administrator** | `HOSPITAL_ADMIN` | `hospital.view`, `clinic.view`, `staff.*`, `patients.*`, `appointments.*`, `inventory.*`, `reports.*`, `dashboard.view`, `queue.view`, `referrals.view`, `po.*`, `vendor.*`, `lab_orders.*`, `lab_results.*` | Facility-Wide | `assigned_facility` only | None | `/`, `/patients`, `/queue`, `/facilities`, `/pharmacy`, `/referrals`, `/followups`, `/infrastructure`, `/reports`, `/alerts` |
| **Medical Officer (Doctor)** | `DOCTOR` | `patients.view`, `appointments.view`, `consultation.*`, `diagnosis.*`, `prescription.*`, `lab_orders.*`, `lab_results.*`, `referrals.*`, `clinic.view`, `queue.view`, `dashboard.view` | Clinical / Facility | `assigned_facility` only | None | `/`, `/patients`, `/queue`, `/consultation`, `/lab`, `/referrals`, `/followups`, `/teleconsultation`, `/alerts` |
| **Staff Nurse** | `NURSE` | `patients.*`, `vitals.*`, `triage.*`, `queue.*`, `clinic.view`, `dashboard.view`, `lab_orders.update`, `lab_results.view` | Triage / Facility | `assigned_facility` only | None | `/`, `/patients`, `/triage`, `/queue`, `/followups`, `/ncd`, `/maternal-child`, `/outreach`, `/wellness`, `/alerts` |
| **Lab Technician** | `LAB_TECHNICIAN` | `patients.view`, `lab_orders.*`, `lab_results.*`, `clinic.view`, `dashboard.view` | Lab / Facility | `assigned_facility` only | None | `/`, `/queue`, `/lab`, `/alerts` |
| **Pharmacist** | `PHARMACIST` | `prescription.view`, `pharmacy.*`, `inventory.*`, `po.*`, `vendor.*`, `reports.*`, `clinic.view`, `dashboard.view` | Pharmacy / Facility | `assigned_facility` only | None | `/`, `/queue`, `/pharmacy`, `/infrastructure`, `/alerts` |

---

## 3. Access Control Dimensionality

Access authorization in the repository is evaluated across multiple dimensions:

| Dimension | Implementation Mechanism | Enforcement Code |
| :--- | :--- | :--- |
| **ROLE** | Evaluated in DRF permission check `has_role_permission(user, permission_name)` and frontend route dispatcher. | `apps/accounts/permissions.py:41` |
| **PERMISSION** | Method-level or view-level permission strings (e.g. `pharmacy.dispense`, `consultation.create`). | `apps/accounts/permissions.py:84` |
| **FACILITY** | Primary operational scoping boundary. If `user.assigned_facility_id` is set, queries are restricted to that facility ID. Cross-facility access is permitted only when a referral explicitly lists the user's facility as source or destination. | `apps/accounts/permissions.py:48,145` |
| **DISTRICT** | Administrative boundary. `DISTRICT_OFFICER` has read-only access to all facilities where `facility.district_id == user.assigned_district_id`. | `apps/accounts/permissions.py:58` |
| **ZONE & WARD** | Descriptive organizational attributes on `Facility` and `Patient`. **Not currently used as active security isolation boundaries** in querysets. | `apps/facilities/models.py` |

---

## 4. DHO Operational Requirement Analysis

Evaluating the DHO profile against executive municipal health governance requirements:

| DHO Operational Requirement | Current Capability Status | Implementation Details in Code | Gap / Remediation Needed |
| :--- | :---: | :--- | :--- |
| **District Clinic Performance** | **EXISTS** | `DistrictOfficerDashboard.tsx` displays `Facility Operation Overview` table comparing patients, waiting queues, active referrals, and operational status across all district clinics. | Fully functional. |
| **Patient Volume Monitoring** | **EXISTS** | District total registered citizens and daily OPD footfall aggregated across district facilities. | Fully functional. |
| **Referral Status Tracking** | **EXISTS** | Tracks pending, accepted, and completed cross-facility transfers on the executive dashboard and `/referrals`. | Fully functional. |
| **NCD Follow-up Oversight** | **PARTIAL** | Follow-up counts appear in `/followups`, but the DHO is **blocked from navigating to `/ncd`** by frontend route guard `ROLE_ALLOWED_PATHS`. | Add `/ncd` to `ROLE_ALLOWED_PATHS['DISTRICT_OFFICER']`. |
| **Disease Surveillance Alerts** | **PARTIAL** | Epidemic alert items appear under `Action Required`, but navigating to `/surveillance` **triggers an HTTP 403 route guard error**. | Add `/surveillance` to `ROLE_ALLOWED_PATHS['DISTRICT_OFFICER']`. |
| **District Medicine Stock Monitoring** | **EXISTS** | District-wide inventory batches, low-stock drug alerts, expired batch lists, and PO statuses accessible on `/pharmacy`. | Fully functional. |
| **Vulnerable Population Tracking** | **EXISTS** | Slum populations per ward and facility displayed on `/network` and `/facilities`. | Fully functional. |
| **Clinic Exceptions & Alerts** | **EXISTS** | District-wide alert console on `/alerts` categorizing stockouts, fever thresholds, and delayed referrals. | Fully functional. |
| **Ward / Zone Drill-down** | **EXISTS** | `HealthcareNetwork.tsx` maps 4-tier tree from District down through Zones and Wards to individual clinics. | Fully functional. |

---

## 5. Security Architecture Weaknesses

1. **Mutation Restriction via Class Name String Matching**:
   In `HasFacilityScope` (`apps/accounts/permissions.py:127`):
   ```python
   mutation_restricted_views = {
       'ConsultationViewSet', 'PrescriptionViewSet', 'TriageVitalsViewSet', 'DispenseMedicineView',
       'PurchaseOrderViewSet', 'VendorViewSet'
   }
   if view.__class__.__name__ in mutation_restricted_views:
       return False
   ```
   Checking `view.__class__.__name__` is brittle and fails if viewsets are subclassed or renamed.
2. **Missing Granular Zone / Ward Officer Roles**:
   While `Zone` and `Ward` entities exist in `geography`, there are no corresponding user roles (e.g. `ZONE_OFFICER`, `WARD_SUPERVISOR`).
