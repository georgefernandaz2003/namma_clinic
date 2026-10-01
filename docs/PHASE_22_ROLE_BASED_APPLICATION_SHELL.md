# PHASE 22 — ROLE-BASED APPLICATION SHELL & DASHBOARD ROUTING

## 1. Executive Summary & Verification Baselines
- **Target Runtime**: Local Laptop Architecture (PostgreSQL 16 -> Django 4.2 / DRF -> React 19 / Vite 8 -> Browser)
- **Phase 21 Baseline Commit**: 6eb4abfcee640842732cc81a0be171f6c92b8920
- **Branch**: eature/namma-clinic-demo-data-model
- **Objective**: Establish frontend navigation architecture, role-aware dashboard landing routes, facility/scope context display, and route guards for the six authoritative backend roles without implementing clinical/domain workflows and strictly adhering to the **Zero Fake Business Data** principle.

---

## 2. Role-Aware Navigation Architecture
The navigation model is centralized in rontend/src/navigation/navigationConfig.ts and driven strictly by the authoritative backend session (/api/auth/me/):
- **Authoritative Roles Matrix**:
  1. DISTRICT_OFFICER: District Health Officer Oversight Console (/dashboard/district)
  2. HOSPITAL_ADMIN: Hospital Administrator Operations Console (/dashboard/admin)
  3. DOCTOR: Medical Officer Clinical Console (/dashboard/doctor)
  4. NURSE: Nursing & Triage Station Console (/dashboard/nurse)
  5. LAB_TECHNICIAN: Diagnostic Laboratory Console (/dashboard/lab)
  6. PHARMACIST: Pharmacy Dispensing & Inventory Console (/dashboard/pharmacy)
- **Backend Authorization Authority**: Navigation items and landing routes are presented as a UX convenience. Backend API permissions remain strictly authoritative for all data access and operations.
- **Data-Driven Configuration**:
  - ROLE_NAVIGATION_CONFIG: Mapping each role to its landing route, title, subtitle, and grouped navigation items.
  - getRoleLandingRoute(role): Maps role to landing destination (/dashboard/<role>) or /login.
  - getRoleNavigation(role): Returns navigation items strictly for the authenticated role.
  - getRoleAllowedRoutes(role): Computes accessible frontend route paths for client-side routing guards.
  - isRouteAllowedForRole(role, pathname): Validates route authorization.

---

## 3. Scope & Facility Context Handling
User scope is extracted authoritatively from the backend session profile:
- **District Scope (DISTRICT)**: Formatted as district oversight (e.g. District Oversight: Vellore District). District officers have visibility into district metrics and facilities across their jurisdiction.
- **Facility Scope (FACILITY)**: Formatted as operational facility scope (e.g. UPHC-01 (Urban Primary Health Centre - Saidapet)). Operational roles (DOCTOR, NURSE, PHARMACIST, LAB_TECHNICIAN, HOSPITAL_ADMIN) operate within their assigned facility.
- **Unassigned / Unknown Scope**: Safely handled with clear fallback indicators (Scope: Unassigned Facility) without crashing or assuming global access on 
ull.

---

## 4. Route Guards & Fallback Architecture
Frontend route guarding is implemented via ProtectedRoute (rontend/src/components/common/ProtectedRoute.tsx):
- **Authentication Guard**: Unauthenticated requests to protected routes intercept and redirect to /login with location preservation in state.
- **Role Isolation Guard**: Explicit llowedRoles or matrix-evaluated route protection checks the authenticated user's role against target paths.
- **403 ForbiddenCard**: When a user attempts to manually enter an unauthorized route (e.g. Doctor navigating to /dashboard/admin), the shell presents an accessible, polite ForbiddenCard explaining that access is restricted to authorized roles, offering a button back to their role dashboard.
- **404 Not Found Handling**: Unrecognized routes (*) render NotFound.tsx (Page Not Found - HTTP 404), rendering within DashboardLayout for authenticated staff and standalone for unauthenticated visitors.

---

## 5. Dashboard Foundation & Zero Fake Data Compliance
- Each role dashboard renders via RoleDashboardFoundation.tsx:
  - Current user name and username badge.
  - Role badge and authoritative facility/scope indicator.
  - Console title and descriptive operational subtitle.
  - Navigation cards summarizing authorized clinical/operational domains.
  - Clean EmptyState component explicitly indicating that live clinical workflows, consultation queues, and operational telemetry will connect in subsequent phases.
- **Data Integrity Rule**: No fake KPIs, no hardcoded patient numbers, no mock revenue, no fake appointment charts, and no simulated inventory counts exist in the dashboards.

---

## 6. Verification & Quality Gates

### A. Frontend Unit & Integration Tests

pm test executes native Node 24 ESM test suites:
- src/api/client.test.ts (13 tests)
- src/navigation/navigation.test.ts (33 tests)
- **Total**: 46/46 tests passed (0 failures, 254ms duration)
- Tested scenarios:
  1. Role -> landing route mapping (all 6 roles + unauthenticated)
  2. Navigation visibility and domain grouping per role
  3. Cross-dashboard isolation and unauthorized route blocking
  4. Authenticated root/dashboard handling
  5. Facility/scope context formatting (district, facility, missing)
  6. Fallback and unsupported roles rejection

### B. Frontend Production Build

pm run build executes 	sc -b && vite build:
- **Modules Transformed**: 1,926
- **Build Time**: 409ms
- **Zero Errors, Clean Distribution Assets**.

### C. Backend Regression Suite
- python manage.py check: 0 issues identified.
- python manage.py makemigrations --check: No changes detected.
- Phase 20 Regression Suite:
  `powershell
  python manage.py test apps.accounts.tests_phase11 apps.accounts.tests_phase12_services apps.accounts.tests_services apps.visits.tests_services apps.laboratory.tests_services apps.pharmacy.tests_services apps.referrals.tests_services apps.audit.tests_services apps.accounts.tests_phase13_api apps.accounts.tests_phase14_integration apps.accounts.tests_phase15_reliability apps.accounts.tests_phase16_postgres apps.accounts.tests_phase18_deployment apps.accounts.tests_phase20_contract --noinput
  `
  **Result**: Ran 116 tests in 63.210s -> OK (116/116 passed).

### D. Live Browser & Shell Runtime Validation
Executed live automated Playwright suite with Google Chrome against live Django dev server (127.0.0.1:8000) and Vite dev server (127.0.0.1:5173):
1. **Unauthenticated access to /dashboard**: Redirected to /login (PASS).
2. **DOCTOR (localdoc)**:
   - Redirected to /dashboard/doctor (PASS).
   - Rendered "Medical Officer Clinical Console" and user badge localdoc (PASS).
   - Attempted manual navigation to /dashboard/admin -> Blocked with 403 ForbiddenCard (PASS).
   - Sign Out -> Session cleared, redirected to /login (PASS).
3. **NURSE (localnurse)**:
   - Redirected to /dashboard/nurse (PASS).
   - Rendered "Nursing & Triage Station Console" and user badge localnurse (PASS).
   - Attempted manual navigation to /dashboard/doctor -> Blocked with 403 ForbiddenCard (PASS).
   - Sign Out -> Session cleared, redirected to /login (PASS).
4. **PHARMACIST (localpharm)**:
   - Redirected to /dashboard/pharmacy (PASS).
   - Rendered "Pharmacy Dispensing & Inventory Console" and user badge localpharm (PASS).
   - Attempted manual navigation to /dashboard/lab -> Blocked with 403 ForbiddenCard (PASS).
   - Sign Out -> Session cleared, redirected to /login (PASS).
5. **HOSPITAL_ADMIN (	estadmin)**:
   - Redirected to /dashboard/admin (PASS).
   - Rendered "Hospital Administrator Operations Console" and user badge 	estadmin (PASS).
   - Attempted manual navigation to /dashboard/doctor -> Blocked with 403 ForbiddenCard (PASS).
   - Sign Out -> Session cleared, redirected to /login (PASS).
6. **LAB_TECHNICIAN (locallab)**:
   - Redirected to /dashboard/lab (PASS).
   - Rendered "Diagnostic Laboratory Console" and user badge locallab (PASS).
   - Attempted manual navigation to /dashboard/pharmacy -> Blocked with 403 ForbiddenCard (PASS).
   - Sign Out -> Session cleared, redirected to /login (PASS).
7. **DISTRICT_OFFICER (localdistrict)**:
   - Redirected to /dashboard/district (PASS).
   - Rendered "District Health Officer Oversight Console" and user badge localdistrict (PASS).
   - Attempted manual navigation to /dashboard/admin -> Blocked with 403 ForbiddenCard (PASS).
   - Sign Out -> Session cleared, redirected to /login (PASS).
8. **Authenticated 404 Handling**:
   - Navigating to /nonexistent-route-xyz renders NotFound component inside DashboardLayout (PASS).

---

## 7. Known Limitations & Next Steps
- **Clinical Workflows Out of Scope**: Phase 22 strictly establishes the application shell and routing architecture. Doctor OPD consultations, nurse vitals entry, lab accessioning/results, pharmacy FEFO dispensing, ARS meetings, and administrative configuration screens display active staging empty states and will be implemented in subsequent phases.
- **Frontend Security Boundary Reminder**: Client-side route blocking is a user convenience mechanism. All clinical and operational actions are enforced authoritatively by Django REST Framework permission classes and transaction services.
