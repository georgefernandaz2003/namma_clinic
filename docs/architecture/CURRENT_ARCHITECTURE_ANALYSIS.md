# Namma Clinic — Current Architecture Analysis

## 1. Executive Overview

The **Namma Clinic Digital Healthcare Platform** is an urban and rural primary healthcare clinic management system designed to support Primary Health Centres (Urban Health & Wellness Centres - UHWC / Namma Clinics), Community Clinics, and multi-tier hospital referral networks. 

The architecture is implemented as a decoupled Single Page Application (SPA) client-server system consisting of:
- **Backend**: Python 3.11 / Django 4.2 REST Framework API with SimpleJWT authentication and SQLite runtime storage.
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS (v4), Lucide React icon suite, and Recharts.
- **Data Protocol**: Stateless RESTful JSON communication over HTTP with Bearer Token Authorization.

---

## 2. Technology Stack & Runtime Profile

### 2.1 Backend Layer
| Component | Implementation Specification | Source Evidence |
| :--- | :--- | :--- |
| **Language** | Python 3.11.9 runtime | System environment inspection |
| **Framework** | Django 4.2 (`Django>=4.2.0,<5.0.0`) | `backend/requirements.txt:1` |
| **API Framework** | Django REST Framework (`djangorestframework>=3.14.0`) | `backend/requirements.txt:2` |
| **Authentication** | JSON Web Tokens (`djangorestframework-simplejwt>=5.3.0`) | `backend/requirements.txt:3`, `backend/config/settings.py:114` |
| **CORS** | `django-cors-headers>=4.3.0` (`CORS_ALLOW_ALL_ORIGINS = True`) | `backend/requirements.txt:4`, `backend/config/settings.py:111` |
| **Timezone** | `Asia/Kolkata` (`USE_TZ = True`) | `backend/config/settings.py:99` |
| **Custom User Model** | `accounts.User` extending `AbstractUser` | `backend/config/settings.py:93` |
| **Audit Middleware** | `apps.audit.middleware.AuditLogMiddleware` | `backend/config/settings.py:60` |

### 2.2 Frontend Layer
| Component | Implementation Specification | Source Evidence |
| :--- | :--- | :--- |
| **Framework** | React 19.2.8 / React-DOM 19.2.8 | `frontend/package.json:16-17` |
| **Build Tool** | Vite 8.2.2 with `@vitejs/plugin-react` | `frontend/package.json:26,29` |
| **Language** | TypeScript ~6.0.2 | `frontend/package.json:28` |
| **Styling** | TailwindCSS 4.3.3 (`@tailwindcss/vite`) | `frontend/package.json:13,20` |
| **Routing** | React Router DOM 7.18.3 (`BrowserRouter`, `Routes`, `Route`) | `frontend/package.json:18`, `frontend/src/App.tsx` |
| **HTTP Client** | Axios 1.20.0 with request/response interceptors | `frontend/package.json:14`, `frontend/src/services/api.ts` |
| **Icons** | Lucide React 1.39.0 | `frontend/package.json:15` |
| **Visual Charts** | Recharts 3.10.1 | `frontend/package.json:19` |
| **Linter** | Oxlint 1.79.0 | `frontend/package.json:27` |

### 2.3 Database & Storage Layer
| Component | Specification | Source Evidence |
| :--- | :--- | :--- |
| **Database Engine** | SQLite 3 | `backend/config/settings.py:87` |
| **Database File** | `backend/db.sqlite3` (Generated on migration/seed) | `backend/config/settings.py:88` |
| **Static Schema Dump** | `database/db.sql` (Raw SQL snapshot dump) | `database/db.sql` |
| **Media Root** | `backend/media/` for document uploads | `backend/config/settings.py:107` |

---

## 3. High-Level System Architecture

```
+-------------------------------------------------------------------------+
|                           FRONTEND CLIENT                               |
|                  React 19 + TypeScript + Vite + TailwindCSS             |
|                                                                         |
|  +-------------------+  +-------------------+  +---------------------+  |
|  | Role-Based Routes |  | State Context     |  | API Client          |  |
|  | - Doctor Desk     |  | - AuthContext     |  | - Axios Instance    |  |
|  | - Nurse Desk      |  | - Facility Context|  | - Bearer Token Auth |  |
|  | - Pharmacy Desk   |  | - Role Guards     |  | - Auto-Refresh 401  |  |
|  | - District Officer|  +-------------------+  +---------------------+  |
|  +-------------------+                                                  |
+-------------------------------------------------------------------------+
                                    | HTTP / REST (JSON)
                                    v
+-------------------------------------------------------------------------+
|                           DJANGO BACKEND                                |
|             Django 4.2 + DRF + SimpleJWT + Audit Middleware             |
|                                                                         |
|  +-------------------+  +-------------------+  +---------------------+  |
|  | Middleware Stack  |  | Routers & URLs    |  | Permissions/Scoping |  |
|  | - CorsMiddleware  |  | - DefaultRouter   |  | - HasRolePermission |  |
|  | - SimpleJWT Auth  |  | - 38 ViewSets     |  | - HasFacilityScope  |  |
|  | - AuditLogMiddlew |  | - Custom APIViews |  | - get_accessible_ids|  |
|  +-------------------+  +-------------------+  +---------------------+  |
|                                   |                                     |
|  +-------------------------------------------------------------------+  |
|  | Modular Django Apps (22 Active Apps in INSTALLED_APPS)             |  |
|  | accounts, geography, facilities, patients, visits, triage,        |  |
|  | consultations, laboratory, pharmacy, referrals, ncd, surveillance |  |
|  | telemedicine, outreach, wellness, ars, quality, reports, alerts,   |  |
|  | integrations, compliance, audit                                    |  |
|  +-------------------------------------------------------------------+  |
|  | Orphaned Apps (Not in INSTALLED_APPS, no migrations/tables):       |  |
|  | - child (ChildRecord)                                              |  |
|  | - maternal (MaternalRecord)                                        |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
                                    | Django ORM
                                    v
+-------------------------------------------------------------------------+
|                           DATABASE LAYER                                |
|             SQLite 3 (db.sqlite3) / 54 Physical DB Tables               |
+-------------------------------------------------------------------------+
```

---

## 4. Backend Application Module Inventory

The repository contains 24 sub-apps inside `backend/apps/`. Inspection reveals that **22 apps are installed** and operational, while **2 apps are uninstalled/orphaned**:

| App Name | Installed in Settings | Tables in DB | Key Models / Entities | Key Views / Endpoints | Operational Status |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `accounts` | **YES** | 3 | `User` | `UserViewSet`, `CurrentUserProfileView`, `seed_demo` | Fully Functional |
| `geography` | **YES** | 4 | `State`, `District`, `Zone`, `Ward` | `StateViewSet`, `DistrictViewSet`, `ZoneViewSet`, `WardViewSet` | Fully Functional |
| `facilities` | **YES** | 7 | `Facility`, `FacilityRelationship`, `FacilityOxygenSupply`, `FacilityConsumableInventory`, `FacilityMaintenanceTicket`, `FacilityBedCapacity`, `FacilityBedAllocation` | `FacilityViewSet`, `FacilityHierarchyView`, `NetworkGraphView`, Infra ViewSets | Fully Functional |
| `patients` | **YES** | 3 | `Patient`, `Household`, `PatientDocument` | `PatientViewSet`, `PatientTimelineView`, `PatientRecordsView`, `PatientDocumentViewSet` | Fully Functional |
| `visits` | **YES** | 3 | `Visit`, `Token`, `VisitStatusHistory` | `VisitViewSet`, `call_next` action, `advance_queue` action | Fully Functional |
| `triage` | **YES** | 1 | `TriageVitals` | `TriageVitalsViewSet` | Fully Functional |
| `consultations` | **YES** | 3 | `Consultation`, `Prescription`, `PrescriptionItem` | `ConsultationViewSet`, `PrescriptionViewSet` | Fully Functional |
| `laboratory` | **YES** | 4 | `LabTestMaster`, `LabOrder`, `LabSample`, `LabResult` | `LabTestMasterViewSet`, `LabOrderViewSet` (`collect-sample`, `save-result`) | Fully Functional |
| `pharmacy` | **YES** | 6 | `MedicineMaster`, `Vendor`, `MedicineBatch`, `PurchaseOrder`, `PurchaseOrderItem`, `InventoryTransaction` | `MedicineMasterViewSet`, `MedicineBatchViewSet`, `DispenseMedicineView`, `PharmacyDashboardSummaryView` | Fully Functional |
| `referrals` | **YES** | 3 | `Referral`, `ReferralResponse`, `FollowUp` | `ReferralViewSet` (`respond` action), `FollowUpViewSet` | Fully Functional |
| `ncd` | **YES** | 1 | `NCDRecord` | `NCDRecordViewSet` | Functional |
| `surveillance` | **YES** | 1 | `DiseaseCase` | `DiseaseCaseViewSet` | Functional |
| `telemedicine` | **YES** | 1 | `Teleconsultation` | `TeleconsultationViewSet` | Functional |
| `outreach` | **YES** | 1 | `OutreachActivity` | `OutreachActivityViewSet` | Functional |
| `wellness` | **YES** | 1 | `WellnessSession` | `WellnessSessionViewSet` | Functional |
| `ars` | **YES** | 3 | `ARSMember`, `ARSMeeting`, `ARSActionItem` | `ARSMeetingViewSet`, `ARSMemberViewSet` | Functional |
| `quality` | **YES** | 2 | `QualityChecklist`, `BiomedicalWasteLog` | `QualityChecklistViewSet`, `BiomedicalWasteLogViewSet` | Functional |
| `reports` | **YES** | 1 | `ReportExportLog` | `DashboardSummaryView`, `CSVExportView`, `ResetDemoView` | Fully Functional |
| `alerts` | **YES** | 1 | `Alert` | `AlertViewSet` | Functional |
| `integrations` | **YES** | 1 | `IntegrationConfiguration` | `IntegrationConfigurationViewSet` | Mock Mode Only |
| `compliance` | **YES** | 1 | `ComplianceItem` | `ComplianceItemViewSet` | Functional |
| `audit` | **YES** | 1 | `AuditLog` | `AuditLogViewSet`, `AuditLogMiddleware` | Fully Functional |
| `child` | **NO** | 0 | `ChildRecord` | None | **ORPHANED** (Not in settings, no tables, no views) |
| `maternal` | **NO** | 0 | `MaternalRecord` | None | **ORPHANED** (Not in settings, no tables, no views) |

---

## 5. Network Hierarchy & Topology Architecture

The application models a 4-tier healthcare delivery network across Bengaluru Urban (BBMP Central) and Bengaluru Rural:

```
[District Hospital & Specialist Center]
  Victoria District General Hospital (HOSP-DIST-01) - 750 Beds, ICU, Tertiary Cardiology
       ^
       | SPECIALIST / EMERGENCY (5.0 km)
       |
[Sub-District Hospital & UPHC]
  Indiranagar Sub-District Hospital & UPHC (HOSP-SUB-01) - 60 Beds, Maternal/ANC Hub
       ^
       | REFERRAL / SECONDARY CARE (4.2 km)
       |
[Rural Primary Health Clinic]
  Varthur Rural Primary Clinic A4 (RC-A4-04) - 10 Beds, General OPD, Nurse Triage
       ^
       | REFERRAL / PRIMARY (2.5 km)
       |
[Village Satellite Clinic]
  Gunjur Village Satellite Clinic (VC-A4-01) - 4 Beds, Primary Screening, Tele-referral
```

The relationships are tracked in `FacilityRelationship` with attributes for `distance_km`, `relationship_type` (PARENT, REFERRAL, SPECIALIST, EMERGENCY, DIAGNOSTIC, TELECONSULTATION), and `priority` (PRIMARY, EMERGENCY).

---

## 6. Frontend Layout & Navigation Architecture

The frontend is constructed using a unified layout structure:
- **`DashboardLayout.tsx`**: Provides the top navbar, active facility context switcher, user profile banner, and dynamic sidebar navigation.
- **Route Guards (`ProtectedRoute` in `App.tsx`)**: Validates active JWT authentication and enforces role-level URL path authorization via `isPathAllowedForRole(user?.role, location.pathname)`.
- **Active Facility Scoping**: Managed globally by `AuthContext`, allowing district officers to toggle between all facilities, while operational staff are locked to their assigned facility.

---

## 7. Key Architectural Deficiencies & Gotchas

1. **Orphaned RCH Apps (`child` and `maternal`)**:
   `apps/child` and `apps/maternal` define models but were never added to `INSTALLED_APPS` in `settings.py`. Consequently, the frontend `MaternalChild.tsx` page has no backend endpoints and renders entirely hardcoded static JSX.
2. **Missing Clinical Relational Bridges**:
   - `PrescriptionItem.medicine_name` is a CharField string and does not foreign-key to `MedicineMaster`.
   - `Referral` has no foreign key to `Visit` or `Consultation`.
   - `NCDRecord` and `DiseaseCase` are recorded as independent detached records rather than originating from clinical consultation or lab results.
3. **Frontend Calculation of Dashboard KPIs**:
   In `PharmacistDashboard.tsx`, total prescriptions, waiting prescriptions, and dispensed counts are computed on the client side using `.filter()` on the first page (max 50 items) of `prescriptions/` rather than querying database aggregate endpoints.
4. **District Officer Route Guard Barrier**:
   In `ROLE_ALLOWED_PATHS`, `DISTRICT_OFFICER` is missing paths `/patients`, `/ncd`, `/surveillance`, and `/maternal-child`, leading to 403 Access Denied errors if a DHO navigates to these public health modules.
