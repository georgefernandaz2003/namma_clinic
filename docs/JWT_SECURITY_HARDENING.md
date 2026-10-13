# Namma Clinic — JWT & Bearer Authentication Security Architecture

## 1. Overview
This document details the hardened JSON Web Token (JWT) and Bearer Authentication configuration for the Namma Clinic Digital Health Platform, adhering to OWASP Application Security Verification Standards (ASVS) and healthcare data protection requirements.

---

## 2. Token Lifecycle & Specifications

| Parameter | Configuration | Security Rationale |
| :--- | :--- | :--- |
| **Access Token Lifetime** | 15 Minutes (`timedelta(minutes=15)`) | Short-lived bearer credentials minimize window of vulnerability in the event of access token interception. |
| **Refresh Token Lifetime** | 7 Days (`timedelta(days=7)`) | Controlled credential renewal window configurable per environment policy. |
| **Signing Algorithm** | `HS256` (HMAC with SHA-256) | Fixed, explicit algorithm. Arbitrary algorithm switching and `none` algorithm are strictly rejected. |
| **Token Rotation** | `ROTATE_REFRESH_TOKENS: True` | Every refresh exchange invalidates the previous refresh token and issues a new one. |
| **Token Blacklisting** | `BLACKLIST_AFTER_ROTATION: True` | SimpleJWT token blacklist tracks and blocks reused or revoked tokens on the database. |
| **Authorization Header** | `Authorization: Bearer <access_token>` | Standards-compliant HTTP header transmission. |
| **Claims Profile** | `user_id`, `token_type`, `exp`, `iat`, `jti` | Minimalist claims. No passwords, medical records, or sensitive clinical data are embedded in JWTs. |

---

## 3. Server-Side Revocation & Logout Flow

- **Revocation Endpoints**:
  - `POST /api/auth/logout/`: Accepts `{"refresh": "<refresh_token>"}` and adds the refresh token to the database blacklist table (`token_blacklist_blacklistedtoken`).
  - `POST /api/auth/token/blacklist/`: Standard SimpleJWT blacklist endpoint.
- **Reuse Prevention**: Attempting to reuse an old or blacklisted refresh token immediately returns `HTTP 401 Unauthorized` with `token_not_valid` / `Token is blacklisted`.
- **Client Logout**: Frontend `logout()` in `AuthContext` calls `/api/auth/logout/` before purging local credentials, ensuring server-side invalidation.

---

## 4. Authorization & User State Integrity

- **Authoritative Database Context**:
  JWT tokens authenticate user identity only. All permission checks (`HasPermission`, `HasFacilityScope`), facility isolation, and clinical RBAC are resolved dynamically from the live database `request.user` on every API call.
- **Immediate Deactivation Enforcement**:
  `JWTAuthentication` executes `default_user_authentication_rule` on each request. If `user.is_active` is `False` or the user has been deleted, the request is immediately rejected with `HTTP 401 Unauthorized`, even if the JWT has not yet expired.

---

## 5. Frontend Token Handling & Storage

- **Storage**: Tokens are maintained in browser `localStorage` for cross-tab persistence.
- **Risk Mitigation**: The residual XSS risk of local storage is mitigated by:
  1. Ultra-short access token expiration (15 minutes).
  2. One-time refresh token rotation and immediate server-side revocation on logout.
  3. Automatic silent refresh via Axios interceptors with queued retry, ensuring uninterrupted clinician workflow.
- **Exclusion from URLs/Logs**: Tokens are never passed via URL query parameters, logged to browser console, or included in error messages.

---

## 6. Production Environment Variables

| Variable Name | Default (Development) | Purpose |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` / `SECRET_KEY` | Development fallback string | Core cryptographic secret for Django session & signing. |
| `JWT_SIGNING_KEY` | Defaults to `SECRET_KEY` | Dedicated HMAC secret key for signing JWT tokens. |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | Configurable access token lifetime in minutes. |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Configurable refresh token lifetime in days. |
| `JWT_ISSUER` | `namma-clinic` | Explicit token issuer claim. |
