# Phase 18 — Application Deployment Foundation & Production Configuration Hardening

## 1. Executive Summary & Baseline

Phase 18 establishes the application deployment foundation, containerization baseline, environment-driven configuration contract, and production security hardening for the Namma Clinic digital health platform.

### Baselines & Approvals
- **Phase 16A Approved Baseline (Code)**: `52e0ca417e826f41b9cc5710aad8ff59a3374cff`
- **Phase 17 Approved Baseline (Docs)**: `026f49035f86c182afcbf3f985eaeba63eb4bcd6`
- **Code Repository**: `d:\project\namma_clinic`
- **Active Branch**: `feature/namma-clinic-demo-data-model`

### Strict Scope Invariants
- **No frontend/UI development** (no React, HTML pages, or dashboards).
- **No cloud provider selection** (AWS, Azure, SDC, and MeghRaj remain strictly undecided).
- **No HA database or PgBouncer installation** (infrastructure-level connection pooling deferred).
- **No asynchronous task queue installation** (Redis, Celery, Django-Q, Huey deferred).
- **No live external integrations** (ABDM, e-Aushadha, HMIS remain mocked).
- **No database schema redesign** (the approved 50-table model is preserved intact).

---

## 2. Configuration Contract & Environment Variables

The application configuration in `backend/config/settings.py` is now fully environment-driven and supports three distinct environments: `local`, `staging`, and `production`.

### Configuration Variables Matrix

| Variable | Required In | Type | Default Value | Purpose / Description | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DJANGO_ENV` | All | String | `local` | Controls environment profile (`local`, `staging`, `production`) | **IMPLEMENTED** |
| `DJANGO_DEBUG` | Optional | Boolean | Env-specific | In `production`, strictly `False` (fails fast if set to True) | **IMPLEMENTED** |
| `DJANGO_SECRET_KEY` | Prod | String | Demo key in local only | Cryptographic secret for signing sessions and tokens | **IMPLEMENTED** |
| `DJANGO_ALLOWED_HOSTS`| Prod | List (CSV)| `*` in local; FQDN in prod | Host/domain header validation | **IMPLEMENTED** |
| `CORS_ALLOWED_ORIGINS`| Staging/Prod | List (CSV)| Empty list | Allowed web frontend origins | **IMPLEMENTED** |
| `CORS_ALLOW_ALL_ORIGINS`| Local | Boolean | `True` in local; `False` in prod | Permissive local development flag | **IMPLEMENTED** |
| `DATABASE_ENGINE` | Prod/Staging| String | `django.db.backends.sqlite3` | In prod, strictly `django.db.backends.postgresql` | **IMPLEMENTED** |
| `DATABASE_NAME` | Prod/Staging| String | `namma_clinic_staging` | PostgreSQL database name | **IMPLEMENTED** |
| `DATABASE_USER` | Prod/Staging| String | `postgres` | PostgreSQL username | **IMPLEMENTED** |
| `DATABASE_PASSWORD` | Prod/Staging| String | Empty in local | PostgreSQL user password | **IMPLEMENTED** |
| `DATABASE_HOST` | Prod/Staging| String | `127.0.0.1` | PostgreSQL host / socket | **IMPLEMENTED** |
| `DATABASE_PORT` | Prod/Staging| Integer | `5432` | PostgreSQL port | **IMPLEMENTED** |
| `DATABASE_CONN_MAX_AGE`| Optional | Integer | `60` in prod, `0` in staging | Persistent database connection lifetime (seconds) | **IMPLEMENTED** |
| `DJANGO_LOG_LEVEL` | Optional | String | `INFO` | Root console logging level (`DEBUG`, `INFO`, `WARNING`) | **IMPLEMENTED** |
| `JWT_ACCESS_TOKEN_MINUTES`| Optional | Integer | `10080` (7 days) | JWT access token validity duration | **IMPLEMENTED** |
| `JWT_REFRESH_TOKEN_DAYS` | Optional | Integer | `30` (30 days) | JWT refresh token validity duration | **IMPLEMENTED** |

---

## 3. Environment Behavior & Fail-Fast Rules

### Environment Profiles

```
+----------------------------------------------------------------------------------------------------+
|                                    ENVIRONMENT SPECIFICATION                                      |
+------------------------------------+-----------------------------------+---------------------------+
|          LOCAL (Development)       |              STAGING              |        PRODUCTION         |
+------------------------------------+-----------------------------------+---------------------------+
| - DJANGO_ENV: local                | - DJANGO_ENV: staging             | - DJANGO_ENV: production  |
| - DEBUG: True (default)            | - DEBUG: False (default)          | - DEBUG: False (MANDATORY)|
| - SECRET_KEY: Built-in demo key    | - SECRET_KEY: Staging default/env | - SECRET_KEY: From env    |
| - ALLOWED_HOSTS: ['*']             | - ALLOWED_HOSTS: Staging FQDNs    | - ALLOWED_HOSTS: Strict   |
| - CORS: Allow-all enabled          | - CORS: Whitelisted origins       | - CORS: Whitelisted only  |
| - Database: SQLite or PostgreSQL   | - Database: PostgreSQL 16+        | - Database: PostgreSQL 16+|
| - SSL Redirect: Disabled           | - SSL Redirect: Env-controlled    | - SSL Redirect: Enabled   |
| - Cookies Secure: False            | - Cookies Secure: True            | - Cookies Secure: True    |
+------------------------------------+-----------------------------------+---------------------------+
```

### Production Fail-Fast Assertions
When `DJANGO_ENV=production`, the application executes strict startup assertions and raises `django.core.exceptions.ImproperlyConfigured` if:
1. `DJANGO_DEBUG` is passed as `True` or `1`.
2. `DJANGO_SECRET_KEY` is missing, empty, or set to the default demo secret key.
3. `DJANGO_ALLOWED_HOSTS` is missing, empty, or contains wildcard `'*'`.
4. `DATABASE_ENGINE` is missing or is SQLite (`django.db.backends.sqlite3`).
5. `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, or `DATABASE_HOST` are missing.
6. `CORS_ALLOW_ALL_ORIGINS` is enabled.

Local development remains unhindered: running `python manage.py runserver` or running test suites requires zero environment variables and safely defaults to local SQLite.

---

## 4. Security Hardening

### HTTP & Session Security Settings
- **`SECURE_SSL_REDIRECT`**: Automatically set to `True` in production (enforcing HTTPS on all traffic).
- **`SESSION_COOKIE_SECURE`**: Set to `True` in staging and production (cookies transmitted over HTTPS only).
- **`CSRF_COOKIE_SECURE`**: Set to `True` in staging and production (CSRF tokens transmitted over HTTPS only).
- **`SECURE_HSTS_SECONDS`**: Configured to `31536000` (1 year) in production.
- **`SECURE_HSTS_INCLUDE_SUBDOMAINS`**: Configured to `True` in production.
- **`SECURE_HSTS_PRELOAD`**: Configured to `True` in production.
- **`SECURE_CONTENT_TYPE_NOSNIFF`**: Configured to `True` in staging and production.
- **`SECURE_BROWSER_XSS_FILTER`**: Configured to `True` in staging and production.
- **`X_FRAME_OPTIONS`**: Configured to `'DENY'` in staging and production (prevents clickjacking).

### Password Validation
Standard Django password validators have been enabled in `AUTH_PASSWORD_VALIDATORS`:
1. `UserAttributeSimilarityValidator` (rejects passwords similar to username/email).
2. `MinimumLengthValidator` (min length 8 characters).
3. `CommonPasswordValidator` (rejects top 20,000 common passwords like "password123").
4. `NumericPasswordValidator` (rejects purely numeric passwords like "12345678").

Verified: Weak passwords are mathematically rejected by `validate_password`. User serializers and API error envelopes never expose raw passwords or password hashes.

### JWT Token Lifetime & Status
- **Current Defaults (Preserved for Backward Compatibility)**:
  - `ACCESS_TOKEN_LIFETIME = 7 days` (10,080 minutes)
  - `REFRESH_TOKEN_LIFETIME = 30 days`
- **Environment Overrides**:
  - `JWT_ACCESS_TOKEN_MINUTES` and `JWT_REFRESH_TOKEN_DAYS` allow fine-grained operational tuning without code changes.
- **Production Recommendation**:
  - `ACCESS_TOKEN_LIFETIME = 15 to 30 minutes`
  - `REFRESH_TOKEN_LIFETIME = 7 days` with token rotation and blacklisting.
- **Decision Status**: **UNDECIDED** (Pending clinical shift workflow and security stakeholder review).

---

## 5. Health & Readiness Probe Contract

Dedicated unauthenticated probe endpoints have been implemented in `backend/config/health.py` and routed via `backend/config/urls.py`:

### Liveness Probe (`GET /healthz`, `GET /healthz/`)
- **Purpose**: Verifies that the Python WSGI process is alive and responsive to HTTP requests.
- **Authentication**: Unauthenticated (accessible by container runtimes, Kubernetes kubelet, AWS ALB).
- **HTTP Response**: `200 OK`
- **Payload**: `{"status": "ok"}`
- **Overhead**: $< 1\text{ ms}$, zero database queries.

### Readiness Probe (`GET /readyz`, `GET /readyz/`)
- **Purpose**: Verifies that critical backing services (specifically PostgreSQL database connectivity) are available.
- **Authentication**: Unauthenticated.
- **Healthy HTTP Response**: `200 OK`
- **Healthy Payload**: `{"status": "ready", "database": "connected"}`
- **Unhealthy HTTP Response**: `503 Service Unavailable`
- **Unhealthy Payload**: `{"status": "not ready", "database": "unavailable"}`
- **Information Leakage Guard**: Tracebacks, database hostnames, usernames, and raw error messages are caught, logged to internal application logs, and **never** returned to the caller.

---

## 6. Structured Logging Foundation

Django `LOGGING` has been implemented with structured console output to standard streams (`stdout`/`stderr`):

### Log Output Format
`[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s`

### Application Logs vs. Audit Logs

| Dimension | Application Logs | Business Audit Logs |
| :--- | :--- | :--- |
| **Destination** | Standard Output (`stdout`/`stderr`) / Container logs | PostgreSQL table `apps.audit.models.AuditLog` |
| **Audience** | DevOps, SRE, Systems Administrators | Hospital Administrators, Medico-legal, Compliance |
| **Retention** | Ephemeral (rotated via Docker/systemd/fluentd) | Permanent, immutable, indexed by actor and facility |
| **Content** | Process lifecycle, HTTP errors, probe failures | Mutations (POST/PUT/PATCH/DELETE) on clinical/admin APIs |
| **Sensitive Data**| Passwords, tokens, and patient PII **strictly excluded** | Username snapshot, IP address, action path, HTTP status |

---

## 7. Static Files Configuration

- **`STATIC_URL`**: `'/static/'`
- **`STATIC_ROOT`**: `BASE_DIR / 'staticfiles'`
- **Operation Verification**: `python manage.py collectstatic --noinput` copies all 152 Django admin and DRF static assets into `staticfiles/`.
- **Git Cleanliness**: `staticfiles/` and `backend/staticfiles/` added to `.gitignore` to prevent tracking build artifacts.

---

## 8. Containerization Baseline

### Production Dockerfile (`Dockerfile`)
- **Base Image**: `python:3.11-slim`
- **Runtime User**: Dedicated non-root user `appuser` (UID 1001, GID 1001).
- **Deterministic Dependencies**: Installed via `pip install --no-cache-dir -r /app/backend/requirements.txt`.
- **WSGI Server**: `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60`.
- **Healthcheck**: Embedded Docker healthcheck invoking `curl -f http://localhost:8000/healthz`.
- **Zero Baked Secrets**: No `.env` files, passwords, or keys are copied into image layers.
- **Zero Build Migrations**: Migrations are strictly omitted during `docker build`.

### Staging Stack (`docker-compose.staging.yml`)
Minimal, reproducible two-tier staging composition:
1. `db`: `postgres:16-alpine` with healthcheck (`pg_isready`), persistent volume `postgres_staging_data`.
2. `backend`: Built from `Dockerfile`, depends on `db` (`condition: service_healthy`), environment-driven settings.

Explicitly omitted from Phase 18 compose stack (as per instructions):
- No Redis
- No Celery
- No PgBouncer
- No Nginx

---

## 9. Migration Safety & Operational Deployment Sequence

Container startup must **NEVER** execute automatic destructive migrations. The approved zero-downtime operational sequence is:

```
[1. BUILD]        docker build -t namma-clinic-backend:latest .
      │
[2. DEPLOY APP]   Spin up container instances in staging/production
      │
[3. MIGRATE]      docker compose run --rm backend python manage.py migrate --noinput
      │
[4. HEALTH]       curl -f http://localhost:8000/healthz && curl -f http://localhost:8000/readyz
      │
[5. SMOKE TEST]   Execute automated endpoint verification suite
```

---

## 10. Automated Test Results

### Suite Execution Summary
- **Test Modules Executed**: 13 test suites (12 existing domain modules + 1 Phase 18 deployment module)
- **Total Tests Discovered**: **113**
- **Passed**: **113**
- **Failed**: **0**
- **Errors**: **0**
- **Skipped**: **0**
- **Pass Rate**: **100.0%**
- **Duration (SQLite)**: **65.60s**
- **Duration (PostgreSQL 16.2)**: Verified on Phase 18 suite (19/19 passed in 4.75s)

### Phase 18 Test Coverage (`apps.accounts.tests_phase18_deployment`)
1. `test_healthz_liveness_probe_returns_200` — **PASS**
2. `test_healthz_with_trailing_slash_returns_200` — **PASS**
3. `test_healthz_requires_no_authentication` — **PASS**
4. `test_readyz_readiness_probe_database_connected` — **PASS**
5. `test_readyz_with_trailing_slash_returns_200` — **PASS**
6. `test_readyz_database_failure_returns_503_without_leaking_internals` — **PASS**
7. `test_password_validators_configured` — **PASS**
8. `test_short_password_rejected` — **PASS**
9. `test_purely_numeric_password_rejected` — **PASS**
10. `test_common_password_rejected` — **PASS**
11. `test_strong_password_accepted` — **PASS**
12. `test_static_root_configured` — **PASS**
13. `test_static_url_configured` — **PASS**
14. `test_media_root_configured` — **PASS**
15. `test_production_fails_when_secret_key_is_demo` — **PASS**
16. `test_production_fails_when_debug_is_true` — **PASS**
17. `test_production_fails_when_wildcard_hosts` — **PASS**
18. `test_production_fails_when_sqlite_engine` — **PASS**
19. `test_production_passes_with_valid_configuration` — **PASS**

---

## 11. Security Regression Check

| Security Invariant | Pre-Phase 18 State | Post-Phase 18 State | Status |
| :--- | :--- | :--- | :--- |
| **Authentication Flow** | SimpleJWT Bearer tokens | SimpleJWT Bearer tokens with env lifetimes | **VERIFIED** |
| **Facility Scoping** | Multi-facility isolation active | Multi-facility isolation active | **VERIFIED** |
| **Service Authorization** | Enforced at domain service layer | Enforced at domain service layer | **VERIFIED** |
| **Audit Middleware** | `AuditLogMiddleware` captures mutations | Preserved intact | **VERIFIED** |
| **Public Endpoints** | None | Only `/healthz` and `/readyz` | **VERIFIED** |
| **Probe Info Exposure** | N/A | Status code & generic status only | **VERIFIED** |

---

## 12. Explicit Undecided Infrastructure Decisions

The following architectural items are recorded as explicitly **UNDECIDED** pending stakeholder and infrastructure reviews:

| Decision Item | Candidate Options | Status | Note |
| :--- | :--- | :--- | :--- |
| **RPO Target** | Candidate: $< 15\text{ minutes}$ | **UNDECIDED** | Proposed target pending stakeholder review |
| **RTO Target** | Candidate: $< 60\text{ minutes}$ | **UNDECIDED** | Proposed target pending stakeholder review |
| **Cloud / Hosting Provider** | AWS, Azure India, MeghRaj (NIC), SDC | **UNDECIDED** | Cloud infrastructure not yet selected |
| **PostgreSQL HA Topology** | Primary + Hot Standby (Streaming replication) | **UNDECIDED** | Requires cloud host provisioning |
| **Connection Pooling** | PgBouncer vs native cloud connection pooling | **UNDECIDED** | Deferred to production staging phase |
| **Asynchronous Task Queue** | Celery + Redis vs Django-Q vs Huey | **UNDECIDED** | Not installed in Phase 18 |
| **Object Storage Provider** | AWS S3 vs Azure Blob vs MinIO (self-hosted) | **UNDECIDED** | Media storage contract remains local directory |
| **JWT Access Token Lifetime** | 15 min vs 30 min vs 60 min | **UNDECIDED** | Configurable via env; default preserved for tests |

---

## 13. Known Limitations

1. **Development Server on Windows**: `gunicorn` cannot run worker forks on Windows (due to missing `fcntl`). Gunicorn is intended for Linux staging/production containers. Local development on Windows continues to use `manage.py runserver`.
2. **Reverse Proxy TLS**: `SECURE_SSL_REDIRECT` in production assumes an SSL-terminating reverse proxy (Nginx or Cloud Load Balancer) that forwards `X-Forwarded-Proto: https`.
3. **External Gateway Connectivity**: ABDM and e-Aushadha integrations remain mocks; external network calls are buffered in PostgreSQL.

---

## 14. Phase 19 Prerequisites

Before authorizing Phase 19:
1. Review and formal approval of `PHASE_18_DEPLOYMENT_FOUNDATION.md` by PM/RSA.
2. Verification of git cleanliness (zero secrets, zero local database files, clean status).
3. Preservation of 113/113 automated tests.

---

## 15. Operational Direction Update (Phase 19 Realignment)

> [!IMPORTANT]
> **TARGET ENVIRONMENT REALIGNMENT (PHASE 19)**:
> Following architectural review, the Namma Clinic project targets a **local developer laptop** deployment.
> - **TARGET ENVIRONMENT**: LOCAL LAPTOP
> - **SUPPORTED BACKEND RUNTIME**: Python 3.11 + Django 4.2 + Django REST Framework
> - **DATABASE**: PostgreSQL 16+ (Native local execution)
> - **CONTAINERIZATION**: NOT REQUIRED (Docker & Docker Compose removed from architecture)
> - **CLOUD DEPLOYMENT**: NOT REQUIRED (AWS, Azure, SDC, MeghRaj out of scope)
> - **PRODUCTION INFRASTRUCTURE**: OUT OF SCOPE
> - **FRONTEND**: React / Vite (Scheduled for future phase)
> 
> See `docs/LOCAL_DEVELOPMENT_GUIDE.md` for native laptop installation and execution instructions.

---

**PHASE 18 APPLICATION DEPLOYMENT FOUNDATION COMPLETE.**

