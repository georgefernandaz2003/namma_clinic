# 🏥 Namma Clinic Digital Healthcare Network

A comprehensive, state-of-the-art **Digital Healthcare Management System** built for Primary Healthcare Centers (Urban Health & Wellness Centers - UHWC, Rural Clinics, Satellite Posts) and Tiered Secondary/Tertiary Hospitals. 

Designed for low-latency clinic operations, multi-tiered referral networks, OPD queueing, pharmacy dispensing, lab diagnostics, maternal & child tracking, disease surveillance, and clinic infrastructure & bed management.

---

## 🌟 Key Features & Functional Modules

1. **Hierarchy & Multi-Destination Referral Graph**:
   - Tiered healthcare routing across Village Satellite Clinics, Rural Clinics, Urban Namma Clinics, Diagnostic Centers, and Main Secondary/Tertiary Hospitals.
2. **OPD Queue & Token Engine**:
   - Automated token allocation, triage prioritization (Emergency, High Risk, Standard), real-time status transitions (`WAITING`, `IN_TRIAGE`, `IN_CONSULTATION`, `DISPENSED`, `COMPLETED`).
3. **Medical Officer Consultation & EHR**:
   - Digital clinical notes, ICD-10 diagnosis tagging, e-prescriptions, lab order generation, follow-up scheduling, and multi-tier specialist referrals.
4. **Pharmacy & Inventory Management**:
   - Batch-level drug tracking, stock reorder alerts, automated stock deduction upon dispensing, FEFO batch selection.
5. **Laboratory Diagnostics**:
   - Lab test requests, specimen collection logging, lab result entry with reference range validation.
6. **Maternal, Child & NCD Screening**:
   - Antenatal care (ANC) logging, child immunization schedules, hypertension & diabetes NCD tracking.
7. **Clinic Infrastructure, Consumables & Ward Bed Management**:
   - Real-time monitoring of medical oxygen cylinder levels, facility cleaning/sanitization consumables, electrical/facility maintenance ticket logging, and ward bed capacity & allocation tracking.
8. **Disease Surveillance & Teleconsultation**:
   - Outbreak reporting, epidemiology disease case tracking, remote specialist video/audio consultation logging.
9. **Role-Based Access Control (RBAC)**:
   - Granular permissions for Super Admin, District Health Officer, Hospital Admin, Medical Officer, Staff Nurse, Lab Tech, Pharmacist, and Public Health Officer.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Django 4.2, Django REST Framework (DRF), SimpleJWT Authentication, SQLite / PostgreSQL.
- **Frontend**: React 19, Vite, TypeScript, TailwindCSS, Lucide Icons, Recharts.
- **API Protocol**: RESTful JSON with JWT Bearer Token Authentication.

---

## 📋 Prerequisites

Make sure you have the following installed on your machine:

- **Python**: 3.10 or higher ([Download Python](https://www.python.org/downloads/))
- **Node.js**: v18.0.0 or higher ([Download Node.js](https://nodejs.org/))
- **Git**: ([Download Git](https://git-scm.com/))

---

## 🚀 Step-by-Step Installation & Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/georgefernandaz2003/namma_clinic.git
cd namma_clinic
```

---

### 2. Backend Setup (Django REST Framework)

Open a terminal window and navigate to the `backend` folder:

```bash
cd backend
```

#### Windows (PowerShell / Command Prompt):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Seed realistic demo data (Users, Clinics, Patients, Tokens, Pharmacy, Infra, Beds)
python manage.py seed_demo

# Start Django development server
python manage.py runserver 0.0.0.0:8000
```

#### macOS / Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python3 manage.py makemigrations
python3 manage.py migrate

# Seed realistic demo data
python3 manage.py seed_demo

# Start Django development server
python3 manage.py runserver 0.0.0.0:8000
```

> **Backend URL**: The API server will run at `http://127.0.0.1:8000`

---

### 3. Frontend Setup (React + Vite)

Open a **new terminal window** and navigate to the `frontend` folder:

```bash
cd namma_clinic/frontend
```

#### Install dependencies and start dev server:
```bash
# Install node packages
npm install

# Start Vite development server
npm run dev
```

> **Frontend URL**: Open your browser and go to `http://localhost:3000` (or `http://localhost:5173`).

---

## 🔑 Demo User Login Credentials

The `seed_demo` command automatically populates the system with pre-configured accounts representing every operational role:

| Role | Username | Password | Assigned Facility / Scope |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin` | `admin123` | System-wide full administrative access |
| **District Admin** | `district` | `district123` | District Health Officer (BBMP Central) |
| **Hospital Admin** | `hospital` | `hospital123` | KC General Secondary Hospital |
| **Medical Officer** | `doctor` | `doctor123` | Varthur Rural Primary Clinic A4 |
| **Staff Nurse** | `nurse` | `nurse123` | Varthur Rural Primary Clinic A4 |
| **Lab Technician** | `lab` | `lab123` | Varthur Rural Primary Clinic A4 |
| **Pharmacist** | `pharmacy` | `pharmacy123` | Varthur Rural Primary Clinic A4 |
| **Public Health Officer** | `officer` | `officer123` | BBMP Central District Surveillance |

---

## 📄 User Manual & Diagrams

- **PDF User Manual**: `Namma_Clinic_Digital_Healthcare_Network_Demo_Manual.pdf` (Comprehensive 30-page user guide covering all modules, workflows, and role capabilities).
- **System Architecture & Control Flow Diagrams**: Ultra-high-resolution flowcharts are available in the repository root and documentation folder.

---

## 📁 Repository Structure

```
namma_clinic/
├── backend/                  # Django REST API Backend
│   ├── apps/                 # Modular DRF Applications (24 sub-apps)
│   │   ├── accounts/         # Authentication & User RBAC
│   │   ├── facilities/       # Clinic Hierarchy, Oxygen, Beds, Consumables
│   │   ├── patients/         # Patient & Household Registration
│   │   ├── triage/           # Vitals & Emergency Queueing
│   │   ├── consultations/    # Clinical Notes & Prescriptions
│   │   ├── pharmacy/         # Inventory & Stock Dispensing
│   │   └── ...               # Additional modules
│   ├── config/               # Django Settings & URL Routing
│   ├── manage.py             # Django CLI
│   └── requirements.txt      # Python Dependencies
├── frontend/                 # React 19 + Vite Frontend
│   ├── src/                  # Components, Pages, State Hooks & API Services
│   ├── package.json          # Node Dependencies & Scripts
│   └── vite.config.ts        # Vite Build Configuration
├── database/                 # Raw SQL Backups / Data Schemas
├── docs/                     # Technical Specifications & Matrix Docs
├── scripts/                  # Helper Python Scripts & Manual Generator
├── .gitignore                # Git Ignore Configuration
├── Namma_Clinic_Digital_Healthcare_Network_Demo_Manual.pdf # PDF Manual
└── README.md                 # Project Overview & Setup Guide
```

---

## 📜 License & Compliance

Developed in alignment with **National Health Mission (NHM)** guidelines, **Ayushman Bharat Digital Mission (ABDM)** standards, and urban primary healthcare infrastructure specifications