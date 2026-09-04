# REST API Specifications
## Namma Clinic Integrated Digital Healthcare Network

Base URL: `http://localhost:8000/api/`

### Auth & User Management
- `POST /api/auth/token/` - Obtain JWT access/refresh tokens.
- `POST /api/auth/token/refresh/` - Refresh JWT access token.
- `GET /api/auth/me/` - Retrieve current logged-in user profile & facility access.
- `GET/POST /api/users/` - User management endpoints.

### Facilities & Network
- `GET/POST /api/facilities/` - List/create facilities.
- `GET /api/facilities/hierarchy/` - Hierarchical tree structure of facilities.
- `GET /api/facilities/network-graph/` - Network nodes & referral edge links for canvas visualization.
- `GET/POST /api/facility-relationships/` - Dynamic referral destination linkages.

### Patients & Visits
- `GET/POST /api/patients/` - Patient registration & search (by ID, mobile, name, ABHA).
- `GET /api/patients/{id}/timeline/` - Complete longitudinal patient timeline.
- `GET/POST /api/visits/` - Visit creation & queue state tracking.
- `POST /api/visits/{id}/token/` - Token generation & status update.

### Triage & Clinical
- `GET/POST /api/triage/` - Nurse vitals capture & workflow risk flags.
- `GET/POST /api/consultations/` - Doctor consultation, diagnosis, prescription & lab order creation.

### Pharmacy & Lab
- `GET/POST /api/laboratory/orders/` - Lab test orders & result entry/verification.
- `GET /api/pharmacy/medicines/` - Medicine master list.
- `GET /api/pharmacy/batches/` - FEFO batch inventory listing & alerts.
- `POST /api/pharmacy/dispense/` - Dispense prescribed items using FEFO auto-selection.

### Referrals & Follow-ups
- `GET/POST /api/referrals/` - Create cross-facility referral.
- `POST /api/referrals/{id}/respond/` - Hospital specialist response & status update.
- `GET/POST /api/followups/` - Patient follow-up tracking.

### Public Health & Analytics
- `GET /api/dashboard/summary/` - Dynamic metrics for Clinic, Hospital, District & Public Health dashboards.
- `GET /api/surveillance/cases/` - Communicable disease tracking & threshold alerts.
- `GET /api/alerts/` - Active automated alerts (low stock, near expiry, disease spikes).
- `GET /api/reports/export/` - Configurable CSV data exports.
- `GET /api/compliance/` - Namma Clinic booklet & K Mati proposal compliance matrix.
- `POST /api/admin/reset-demo/` - Trigger pristine demo state reset.
