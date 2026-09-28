# Namma Clinic — Git Repository & Workspace Reconciliation Report

**Audit Date:** September 28, 2026  
**Auditor:** Antigravity Agentic Assistant  
**Status:** WORKSPACE RECONCILED / STOPPED FOR REVIEW

---

## 1. Executive Summary & Root Cause of Discrepancy

A critical directory divergence was identified between two distinct folders present on drive `D:\`:

1. **Active Development Repository (Authoritative Project):**
   - **Path:** `D:\project\namma_clinic` (with an **underscore** `_`)
   - **Git Branch:** `feature/namma-clinic-demo-data-model`
   - **HEAD Commit:** `2a027deb201351e90a1fd10d528c430681884a17`
   - **Commit Description:** `feat(namma-clinic): prepare synthetic clinical demo dataset`
   - **Git Remote:** `https://github.com/georgefernandaz2003/namma_clinic.git`
   - **Active Services Execution:** Both the live Django development server (PID 39400 / 31776 using `D:\project\namma_clinic\backend\venv\Scripts\python.exe`) and the live Vite frontend dev server (PID 28224 using `D:\project\namma_clinic\frontend\node_modules`) are running directly out of this directory.
   - **Tracking State:** Clean. All clinical applications (`apps/patients`, `apps/visits`, `apps/triage`, `apps/consultations`, `apps/laboratory`, `apps/pharmacy`), tests, frontend components, and documentation through Phase 26A are fully tracked and committed.

2. **Secondary / Copied Workspace (Antigravity Context Root):**
   - **Path:** `D:\project\namma-clinic` (with a **hyphen** `-`)
   - **Git Branch:** `main`
   - **HEAD Commit:** `7023885d0058fea1d1fad5443c34c8d18c148d8d`
   - **Commit Description:** `docs(namma-clinic): add local laptop development guide and align architecture`
   - **Git Remote:** `https://github.com/Jeyarajkmati/namma-clinic.git`
   - **Tracking State:** Untracked folders (`backend/`, `frontend/`, `scratch/`, and newer Phase 20-26A documentation). These were copied into this directory from `D:\project\namma_clinic` without being committed to the `Jeyarajkmati/namma-clinic` git history.
   - **Virtual Environment:** None (`D:\project\namma-clinic\backend\venv` does not exist).

---

## 2. Detailed Workspace & Identity Verification Matrix

| Property | Active Execution Workspace (`D:\project\namma_clinic`) | Secondary Copied Workspace (`D:\project\namma-clinic`) |
| :--- | :--- | :--- |
| **Filesystem Directory** | `D:\project\namma_clinic` | `D:\project\namma-clinic` |
| **Git Repository Root (`--show-toplevel`)** | `D:/project/namma_clinic` | `D:/project/namma-clinic` |
| **Git Prefix (`--show-prefix`)** | *(root)* | *(root)* |
| **Git Remote Origin URL** | `https://github.com/georgefernandaz2003/namma_clinic.git` | `https://github.com/Jeyarajkmati/namma-clinic.git` |
| **Active Branch** | `feature/namma-clinic-demo-data-model` | `main` |
| **HEAD Commit Hash** | `2a027deb201351e90a1fd10d528c430681884a17` | `7023885d0058fea1d1fad5443c34c8d18c148d8d` |
| **HEAD Commit Subject** | `feat(namma-clinic): prepare synthetic clinical demo dataset` | `docs(namma-clinic): add local laptop development guide and align architecture` |
| **Does `feature/namma-clinic-demo-data-model` exist?** | **YES** (Current local branch & tracking remote) | **NO** (Only branch `main` exists) |
| **Running Django Server Root** | `D:\project\namma_clinic\backend\venv` | *(None running from here)* |
| **Running Vite Dev Server Root** | `D:\project\namma_clinic\frontend\node_modules` | *(None running from here)* |
| **Tracked Application Code** | Complete (Phases 1-26A fully tracked) | Untracked (Copied files) |

---

## 3. Investigation of Unexpected Git State

### 3.1 Why does this workspace differ from the previously validated repository?
The project has two distinct repository directories on disk:
- `D:\project\namma_clinic` (underscore) was the primary repository where feature work for Phase 20 through Phase 26A and the synthetic demo dataset was authored, tested, committed, and run.
- `D:\project\namma-clinic` (hyphen) was registered as the workspace root in Antigravity IDE configuration (`d:\project\namma-clinic -> Jeyarajkmati/namma-clinic`).
- When shell commands are run without specifying a directory, Antigravity defaults to its configured workspace root `d:\project\namma-clinic`. Consequently, `git status` queried the `Jeyarajkmati/namma-clinic` repository on branch `main` at commit `7023885d0058fea1d1fad5443c34c8d18c148d8d`, rather than the active repository at `D:\project\namma_clinic`.

### 3.2 Why do application directories appear untracked in `namma-clinic`?
Commit `7023885d0058fea1d1fad5443c34c8d18c148d8d` on `https://github.com/Jeyarajkmati/namma-clinic.git` reflects an earlier baseline (Phase 18). When `backend/`, `frontend/`, `docs/`, and `scratch/` were copied from `D:\project\namma_clinic` to `D:\project\namma-clinic` to provide local file visibility, they were never staged or committed in `namma-clinic`.

### 3.3 Are these the same repository?
**NO.** They point to two distinct GitHub remotes:
- `https://github.com/georgefernandaz2003/namma_clinic.git` (`D:\project\namma_clinic`)
- `https://github.com/Jeyarajkmati/namma-clinic.git` (`D:\project\namma-clinic`)

The branch `feature/namma-clinic-demo-data-model` exists **only** in `D:\project\namma_clinic`.

---

## 4. Status of the Expected Feature Branch

In `D:\project\namma_clinic`:
```
git -C "D:\project\namma_clinic" branch -a
* feature/namma-clinic-demo-data-model
  main
  remotes/origin/HEAD -> origin/main
  remotes/origin/feature/george
  remotes/origin/feature/namma-clinic-demo-data-model
  remotes/origin/main
```

Recent commits on `feature/namma-clinic-demo-data-model` in `D:\project\namma_clinic`:
```
2a027de (HEAD -> feature/namma-clinic-demo-data-model) feat(namma-clinic): prepare synthetic clinical demo dataset
08950f7 feat(namma-clinic): add synthetic demo dataset
3708131 fix(namma-clinic): harden pharmacy workflow integrity
d5bf521 feat(namma-clinic): implement pharmacy clinical workflow
13b0ad4 feat(namma-clinic): implement laboratory clinical workflow
5e36677 fix(namma-clinic): harden nurse triage workflow
cb861e6 feat(namma-clinic): implement nurse clinical workflow
7b58586 feat(namma-clinic): implement doctor clinical workflow
f3d6809 feat(namma-clinic): establish role based application shell
6eb4abf feat(namma-clinic): establish frontend foundation
```

The feature branch is completely intact, healthy, and located at HEAD `2a027deb201351e90a1fd10d528c430681884a17`.

---

## 5. Untracked Files and Scratch Artifacts Analysis

### 5.1 Playwright & Audit Artifacts (Created during Audit / Automation Repair)
- `scratch/verify_playwright.js`: Temporary Node.js verification script used to validate `playwright-core` and browser launching.
- `scratch/browser_validation_login.png`: Temporary validation screenshot captured during Playwright repair.
- `scratch/comprehensive_reconciliation_audit.py`: Reconciliation script used to query PostgreSQL and REST APIs.
- `scratch/reconciliation_audit_data.json`: Raw JSON snapshot of database queries and API payloads.
- `docs/PLAYWRIGHT_BROWSER_AUTOMATION_FIX.md`: Documentation of the Playwright browser driver fix.
- `docs/DASHBOARD_KPI_CHART_RECONCILIATION.md`: Master reconciliation audit report with live browser findings.

**Classification:**
- `scratch/*` are temporary validation artifacts (non-code, safe).
- `docs/*` are project audit reports intended for long-term tracking.

### 5.2 Protection of Current Work
Under no circumstances should any of the following destructive commands be executed:
- `git clean`
- `git reset --hard`
- `git checkout -- .`
- `git restore .`

No files were deleted, moved, or overwritten.

---

## 6. Risk Analysis & Safe Next Actions

### 6.1 Risk of Data Loss
- If a user or agent were to run `git clean -fd` in `D:\project\namma-clinic`, the copied files (`backend/`, `frontend/`, `docs/`) in that folder would be deleted. However, the authoritative files in `D:\project\namma_clinic` would remain completely unharmed.
- Switching branches in `D:\project\namma_clinic` is unnecessary because it is already on the exact target branch `feature/namma-clinic-demo-data-model` at commit `2a027deb201351e90a1fd10d528c430681884a17`.

### 6.2 Recommended Next Actions
1. **Clarify Workspace Identity with PM / RSA:**
   - Confirm whether the Antigravity workspace should point to `D:\project\namma_clinic` (`georgefernandaz2003/namma_clinic`) or `D:\project\namma-clinic` (`Jeyarajkmati/namma-clinic`).
   - If `Jeyarajkmati/namma-clinic` is intended to receive the work, the `feature/namma-clinic-demo-data-model` branch should be pushed or fetched between the repositories rather than relying on uncommitted copies.
2. **Synchronize Audit Reports:**
   - Copy `docs/DASHBOARD_KPI_CHART_RECONCILIATION.md`, `docs/PLAYWRIGHT_BROWSER_AUTOMATION_FIX.md`, and `docs/GIT_WORKSPACE_RECONCILIATION.md` into `D:\project\namma_clinic\docs\` so both trees have complete documentation.
3. **Maintain Audit-Only State:**
   - Keep the live dev servers running.
   - Do not modify source code or database records until PM/RSA approval is granted.

---

## 7. Stop Condition Adherence

- **Application code modified:** NO (0 files changed)
- **Dashboard calculations fixed:** NO (0 fixes applied)
- **Git commits made:** NO (0 commits)
- **Git pushes made:** NO (0 pushes)
- **Files deleted:** NO (0 deletions)
- **Branch switched:** NO (Workspace preserved as-is)
- **Audit status:** STOPPED. Standing by for PM/RSA review.
