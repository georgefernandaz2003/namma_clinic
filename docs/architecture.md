# System Architecture Document
## Namma Clinic Integrated Digital Healthcare Network

### 1. High-Level Architecture Overview
The Namma Clinic Digital Healthcare Network Application is designed as an offline-first, locally-contained web application.

```
+-------------------------------------------------------------------------+
|                         React + Vite + Tailwind UI                      |
|                  Responsive Web Application (TypeScript)                |
+------------------------------------┬------------------------------------+
                                     | JSON REST API (HTTP + JWT)
                                     v
+-------------------------------------------------------------------------+
|                  Django 4.2+ & Django REST Framework                    |
|  [Accounts] [Geography] [Facilities] [Patients] [Visits] [Clinical]     |
|  [Lab] [Pharmacy] [Referrals] [NCD] [Surveillance] [Alerts] [Audit]     |
+------------------------------------┬------------------------------------+
                                     | Django ORM
                                     v
+-------------------------------------------------------------------------+
|                           SQLite Database                               |
|                     backend/db.sqlite3 & db.sql                         |
+-------------------------------------------------------------------------+
```

### 2. Core Modules & Responsibilities
1. **Accounts & Auth (`apps.accounts`)**: User authentication, JWT tokens, RBAC, facility scoping.
2. **Geography (`apps.geography`)**: Administrative boundaries (State, District, Zone, Ward).
3. **Facilities & Network (`apps.facilities`)**: Facility master, dynamic facility tree, and dynamic multi-facility referral links (`FacilityRelationship`).
4. **Patient Management (`apps.patients`)**: Patient demographics, ABHA ID simulation, duplicate check, and timeline.
5. **Visits & Queue (`apps.visits`)**: Daily token generation, priority flags, OPD queue states.
6. **Triage (`apps.triage`)**: Nurse vitals capture (BP, Pulse, Temp, SpO2, Glucose, BMI) & warning flags.
7. **Consultations & EMR (`apps.consultations`)**: Doctor consultation console, clinical notes, diagnosis, prescriptions, lab orders, referrals.
8. **Laboratory (`apps.laboratory`)**: Lab test master, sample collection, result entry, verification, reports.
9. **Pharmacy & Inventory (`apps.pharmacy`)**: Generic medicine master, batch management with FEFO, stock transactions, low stock & expiry alerts.
10. **Referrals & Continuity (`apps.referrals`)**: Cross-facility referrals, hospital specialist receiving console, response generation, follow-up tracking.
11. **Public Health & Programs (`apps.ncd`, `apps.maternal`, `apps.child`, `apps.surveillance`, `apps.telemedicine`, `apps.outreach`, `apps.wellness`, `apps.quality`, `apps.ars`)**: Specialized clinical and public health program management.
12. **Dashboards & Analytics (`apps.reports`, `apps.alerts`)**: Dynamic role-based analytics, Recharts visualizations, automated decision support alerts.
13. **Integrations & Compliance (`apps.integrations`, `apps.compliance`, `apps.audit`)**: Simulated government APIs (ABDM, ABHA, HMIS, RCH, E-Aushada), audit logs, compliance matrix.

### 3. Security Architecture
- **Authentication**: JWT Access & Refresh Tokens.
- **Authorization**: Custom DRF permissions checking user roles (`SUPER_ADMIN`, `DOCTOR`, `STAFF_NURSE`, etc.) and facility access restrictions.
- **Audit Logging**: Mandatory audit entries created for sensitive events (login, patient registration, consultation, prescription, dispensing, referral, facility update).
