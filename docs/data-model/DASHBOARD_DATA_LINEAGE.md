# Namma Clinic — Dashboard Data Lineage Analysis

## 1. Overview

This document maps the complete data-lineage pipeline for all dashboard KPIs, metric cards, charts, and operational summary figures across the Namma Clinic platform.

Each KPI is traced from the **UI presentation component**, through the **API endpoint and backend view**, to the **database query, filtering, and aggregation logic**, concluding with an audit classification:
- **`DATABASE-DERIVED`**: Computed dynamically from real transactional database rows.
- **`CALCULATED IN BACKEND`**: Computed dynamically via Django ORM aggregation in the backend.
- **`CALCULATED IN FRONTEND`**: Computed via JavaScript array methods (`.filter()`, `.length`) on the client side from paginated payload slices.
- **`HARDCODED`**: Embedded as static constants in frontend JSX or backend fallback operators.
- **`SEEDED`**: Loaded via database fixture/seed command and read statically without dynamic recalculation.
- **`MOCKED`**: Simulated values disconnected from live operational workflows.

---

## 2. Comprehensive KPI Lineage Table

| KPI / Metric Displayed | Dashboard Component | API Endpoint | Backend View / Function | Source Database Model | Backend Filter & Aggregation | Calculation Classification | Potential Issue / Data Integrity Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Total Patients** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `patients_patient` | `filter(registered_at_facility_id__in=fac_ids).count()` | **CALCULATED IN BACKEND** | Counts only patients whose `registered_at_facility` is in district; excludes visiting patients registered elsewhere. |
| **OPD Patients Today** | `DistrictOfficerDashboard.tsx`, `HospitalAdminDashboard.tsx`, `DoctorDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(facility_id__in=fac_ids, opd_date=target_date).count()` | **CALCULATED IN BACKEND** | Clean date-scoped count. |
| **Pending Referrals** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `referrals_referral` | `filter(source_facility_id__in=fac_ids, status__in=['CREATED', 'ACCEPTED', 'IN_TRANSIT', 'UNDER_TREATMENT']).count()` | **CALCULATED IN BACKEND** | Filters only outbound referrals from source facilities in scope. |
| **Total Facilities** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `facilities_facility` | `fac_qs.count()` or fallback `|| 4` in UI | **CALCULATED IN BACKEND** | Frontend fallback `|| 4` masks API response errors. |
| **Facility Waiting Queue** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(facility=fac, opd_date=date, status__in=['WAITING_FOR_TRIAGE', 'WAITING_FOR_DOCTOR', 'WAITING_FOR_PHARMACY']).count()` | **CALCULATED IN BACKEND** | Accurately aggregates waiting visits per facility. |
| **Facility Active Referrals** | `DistrictOfficerDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `referrals_referral` | `filter(source_facility=fac, status__in=['CREATED', 'IN_TRANSIT']).count()` | **CALCULATED IN BACKEND** | Outbound active transfers only. |
| **OPD Stage: Registration** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `patients_patient` / `visits_visit` | `registered_today or todays_opd` | **HARDCODED FALLBACK** | **CRITICAL**: If 0 patients registered today, backend substitutes `todays_opd` volume! |
| **OPD Stage: Triage** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(current_queue='TRIAGE').count()` | **CALCULATED IN BACKEND** | Sums waiting and active triage. |
| **OPD Stage: Doctor** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(current_queue='DOCTOR').count()` | **CALCULATED IN BACKEND** | Sums waiting for doctor and in-consultation. |
| **OPD Stage: Lab** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `laboratory_laborder` | `filter(facility_id__in=ids, order_date__date=date, status__in=['ORDERED', 'SAMPLE_COLLECTED']).count()` | **CALCULATED IN BACKEND** | Accurate pending diagnostic count. |
| **OPD Stage: Pharmacy** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `consultations_prescription` | `filter(facility_id__in=ids, date=date, status='PENDING').count()` | **CALCULATED IN BACKEND** | Prescription pending count. |
| **OPD Stage: Completed** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `filter(status='COMPLETED').count()` | **CALCULATED IN BACKEND** | Completed visits for target date. |
| **Total Medicines** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `pharmacy_medicinebatch` | `batches.values('medicine').distinct().count() or 14` | **HARDCODED FALLBACK** | **CRITICAL**: Backend code explicitly specifies `or 14` if query evaluates to 0! |
| **Low Stock Count** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `pharmacy_medicinebatch` | `filter(quantity__gt=0, quantity__lte=100).count()` | **CALCULATED IN BACKEND** | Hardcoded threshold of 100 units used instead of individual `MedicineMaster.reorder_level`. |
| **Expiring Soon Count** | `HospitalAdminDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `pharmacy_medicinebatch` | `filter(expiry_date__gt=today, expiry_date__lte=today+90d).count()` | **CALCULATED IN BACKEND** | 90-day threshold. |
| **Waiting for Doctor** | `DoctorDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `kpis.doctor_waiting` | **CALCULATED IN BACKEND** | Derived from OPD visits query. |
| **Doctor Follow-ups** | `DoctorDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `referrals_referral` | `summary?.referrals_summary?.completed` | **CRITICAL DISCREPANCY** | **CRITICAL BUG**: Displays completed **Referrals** count in place of actual **FollowUp** review schedule! |
| **Triage Vitals Pending** | `NurseDashboard.tsx` | `GET /api/dashboard/summary/` | `DashboardSummaryView.get()` | `visits_visit` | `kpis.triage_waiting` | **CALCULATED IN BACKEND** | Real-time queue count. |
| **Pharmacist Prescriptions Total** | `PharmacistDashboard.tsx` | `GET /api/prescriptions/` | `PrescriptionViewSet.list()` | `consultations_prescription` | `prescriptions.length` in frontend | **CALCULATED IN FRONTEND** | **CRITICAL ISSUE**: Computed on frontend from paginated response; caps at 50 if more rows exist! |
| **Pharmacist Dispensed Today** | `PharmacistDashboard.tsx` | `GET /api/prescriptions/` | `PrescriptionViewSet.list()` | `consultations_prescription` | `prescriptions.filter(p => p.status === 'DISPENSED').length` in frontend | **CALCULATED IN FRONTEND** | Computed from paginated first page; ignores date filtering if historical dates selected! |
| **Fever Outbreak Alert Banner** | `Surveillance.tsx` | None | None | None | None | **HARDCODED** | The banner *"Fever cases in Varthur Ward exceeded weekly threshold (15 cases reported)"* is pure static JSX text. |
| **Maternal ANC Cohort** | `MaternalChild.tsx` | None | None | None | None | **HARDCODED** | Entire page is static HTML with mock citizen "Anita Devi (Age 30)". No API or DB call. |
| **Child Immunization Schedule** | `MaternalChild.tsx` | None | None | None | None | **HARDCODED** | Static HTML with mock child "Baby of Anita". No API or DB call. |

---

## 3. High-Risk Discrepancy Breakdown

### Discrepancy 1: Hardcoded Fallback Values in Backend Aggregations
In `apps/reports/views.py`:
- Line 79: `total_medicines = inventory_batches.values('medicine').distinct().count() or 14`
- Line 161: `'registration': registered_today or todays_opd`
These logical fallback statements artificially guarantee that numbers appear on the dashboard even when underlying database tables have zero matching records.

### Discrepancy 2: Misattributed KPI Mapping in Doctor Dashboard
In `frontend/src/components/dashboards/DoctorDashboard.tsx`:
- Line 134: `<h3 className="text-2xl font-black text-emerald-900 mt-1">{summary?.referrals_summary?.completed || 0}</h3>`
Under the label **"Follow-ups - Scheduled Reviews"**, the UI renders the count of **completed cross-facility referrals** instead of querying the `FollowUp` table.

### Discrepancy 3: Client-Side Pagination Slicing in Pharmacy Desk
In `frontend/src/components/dashboards/PharmacistDashboard.tsx`:
- Line 22: `const res = await api.get('prescriptions/');`
- Line 95: `prescriptions.filter(p => p.status === 'PENDING').length`
- Line 101: `prescriptions.filter(p => p.status === 'DISPENSED').length`
Because DRF paginates at `PAGE_SIZE = 50`, if there are 120 total prescriptions in the database, the pharmacist dashboard will only count within the first 50 items returned on page 1, resulting in inaccurate inventory and dispensing statistics.
