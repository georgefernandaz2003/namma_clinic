# Namma Clinic — Dashboard Data Lineage & KPI Architecture

## 1. Overview & Remediation Status (Phase A & B Complete)

This document provides the authoritative, post-remediation data-lineage pipeline for all dashboard KPIs, metric cards, charts, and operational summary figures across the Namma Clinic platform.

Following the completion of **Phase A (RBAC / DHO Route Access)** and **Phase B (Data Integrity & KPI Data Lineage)**:
- All artificial fallbacks (`or 14`, `or todays_opd`) have been eliminated.
- Client-side pagination slicing on Pharmacist and Lab dashboards has been replaced with authoritative backend aggregation.
- The Doctor Follow-up KPI has been re-bound to authoritative `FollowUp` table records.
- Maternal & Child static prototype has been completely removed from navigation, routing, and role permission tables.

---

## 2. Authoritative KPI Lineage & Resolution Matrix

| KPI / Metric Displayed | Dashboard Component | API Endpoint | Backend View / Service | Source Database Model | Backend Filter & Aggregation | Remediation Status | Lineage Verification |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Total Patients** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `patients_patient` | `filter(registered_at_facility_id__in=fac_ids).count()` | **RESOLVED** | Authoritative district-scoped count (matches DB: 34). |
| **OPD Patients Today** | All Dashboards | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(facility_id__in=fac_ids, opd_date=target_date).count()` | **AUTHORITATIVE** | Clean date-scoped count. |
| **Pending Referrals** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `referrals_referral` | `filter(source_facility_id__in=fac_ids, status__in=['CREATED', 'ACCEPTED', 'IN_TRANSIT', 'UNDER_TREATMENT']).count()` | **AUTHORITATIVE** | Accurate cross-facility outbound referral tally. |
| **Completed Referrals** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `referrals_referral` | `filter(source_facility_id__in=fac_ids, status='COMPLETED').count()` | **AUTHORITATIVE** | Closed-loop completed referrals. |
| **OPD Stage: Registration** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `patients_patient` | `Patient.objects.filter(registered_at_facility_id__in=fac_ids, registration_date=target_date).count()` | **FIXED (Zero-Safe)** | **Removed fallback `or todays_opd`**. Returns exact 0 when no new patients register today. |
| **OPD Stage: Triage** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(current_queue='TRIAGE').count()` | **AUTHORITATIVE** | Real-time queue aggregation. |
| **OPD Stage: Doctor** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(current_queue='DOCTOR').count()` | **AUTHORITATIVE** | Real-time doctor waiting + consultation. |
| **OPD Stage: Lab** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `laboratory_laborder` | `filter(facility_id__in=ids, order_date__date=date, status__in=['ORDERED', 'SAMPLE_COLLECTED']).count()` | **AUTHORITATIVE** | Diagnostic investigation queue. |
| **OPD Stage: Pharmacy** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `consultations_prescription` | `filter(facility_id__in=ids, date=date, status='PENDING').count()` | **AUTHORITATIVE** | Pending FEFO dispensation queue. |
| **OPD Stage: Completed** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(status='COMPLETED').count()` | **AUTHORITATIVE** | Discharged OPD visits today. |
| **Total Medicines (Stocked)** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `pharmacy_medicinebatch` | `batches.values('medicine').distinct().count()` | **FIXED (Zero-Safe)** | **Removed fallback `or 14`**. Returns true 0 when facility has no inventory. |
| **Low Stock Batches** | `HospitalAdminDashboard.tsx`, `PharmacistDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `pharmacy_medicinebatch` | `filter(quantity__gt=0, quantity__lte=100).count()` | **AUTHORITATIVE** | Inventory batch count below threshold. |
| **Doctor Follow-ups** | `DoctorDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `referrals_followup` | `summary?.followups_summary?.due_today ?? summary?.kpis?.followups_due ?? 0` | **CORRECTED SEMANTICS** | Replaced `summary?.referrals_summary?.completed`. Directly queries `FollowUp` table for `due_date=today, status__in=['PENDING', 'DUE_TODAY']`. |
| **Pharmacist: Total Prescriptions** | `PharmacistDashboard.tsx` | `GET /api/dashboard/summary/` & `GET /api/pharmacy/dashboard/` | `DashboardSummaryView` & `PharmacyDashboardSummaryView` | `consultations_prescription` | `summary?.pharmacy_summary?.total_prescriptions` | **FIXED PAGINATION BUG** | Replaced `prescriptions.length` from 50-slice API with authoritative backend total count. |
| **Pharmacist: Waiting Queue** | `PharmacistDashboard.tsx` | `GET /api/dashboard/summary/` & `GET /api/pharmacy/dashboard/` | `DashboardSummaryView` & `PharmacyDashboardSummaryView` | `consultations_prescription` | `summary?.pharmacy_summary?.pending` | **FIXED PAGINATION BUG** | Replaced `prescriptions.filter(...)` with backend authoritative count. |
| **Pharmacist: Dispensed Today** | `PharmacistDashboard.tsx` | `GET /api/dashboard/summary/` & `GET /api/pharmacy/dashboard/` | `DashboardSummaryView` & `PharmacyDashboardSummaryView` | `consultations_prescription` | `summary?.pharmacy_summary?.dispensed_today` | **FIXED PAGINATION BUG** | Replaced client-side filter with backend date-filtered count. |
| **Lab Tech: Queue KPIs** | `LabTechnicianDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `laboratory_laborder` | `summary?.lab_summary?.ordered / sample_collected / verified` | **FIXED PAGINATION BUG** | Replaced client-side array filters with authoritative backend counts. |
| **Maternal & Child Console** | `MaternalChild.tsx` | None | None | None | None | **COMPLETELY REMOVED** | Route `/maternal-child`, sidebar item, and page file deleted. No mock data exposed. |

---

## 3. Database vs API Validation Table

Verified via automated test script `scripts/validate_kpis.py` against active SQLite database:

| KPI | UI Component / Key | API Endpoint Value | Database Query Derived Value | Validation Match |
| :--- | :--- | :---: | :---: | :---: |
| **Total Patients** | `total_patients` | 34 | 34 | **PASS** |
| **Registered Today** | `registered_today` | 0 | 0 | **PASS** |
| **Today's OPD** | `todays_opd` | 0 | 0 | **PASS** |
| **Stage Flow — Reg** | `opd_stage_flow.registration` | 0 | 0 | **PASS** |
| **Stage Flow — Triage** | `opd_stage_flow.triage` | 0 | 0 | **PASS** |
| **Stage Flow — Doctor** | `opd_stage_flow.doctor` | 0 | 0 | **PASS** |
| **Stage Flow — Lab** | `opd_stage_flow.lab` | 0 | 0 | **PASS** |
| **Stage Flow — Pharmacy**| `opd_stage_flow.pharmacy` | 0 | 0 | **PASS** |
| **Stage Flow — Completed**| `opd_stage_flow.completed` | 0 | 0 | **PASS** |
| **Stocked Medicines** | `inventory_summary.total_medicines` | 4 | 4 | **PASS** |
| **Low Stock Batches** | `inventory_summary.low_stock` | 2 | 2 | **PASS** |
| **Pending Referrals** | `referrals_summary.pending` | 0 | 0 | **PASS** |
| **Completed Referrals**| `referrals_summary.completed` | 1 | 1 | **PASS** |
| **Follow-ups Due Today**| `followups_summary.due_today` | 0 | 0 | **PASS** |
| **Follow-ups Pending** | `followups_summary.pending` | 1 | 1 | **PASS** |
| **Total Prescriptions**| `pharmacy_summary.total_prescriptions` | 3 | 3 | **PASS** |
| **Dispensed Today** | `pharmacy_summary.dispensed_today` | 0 | 0 | **PASS** |

**Discrepancy Count: ZERO.**
