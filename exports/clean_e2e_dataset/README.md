# Namma Clinic - Complete End-to-End Dataset Export

This package contains the complete, production-grade clinical dataset generated for **Namma Clinic Digital Healthcare Network (Karnataka)**.

Every patient record is an authentic Karnataka citizen identity with **zero numbers/digits in patient names** and full longitudinal clinical workflows.

---

## 1. Summary of Files in this Directory

| File Name | Section | Rows | Description |
| :--- | :--- | :--- | :--- |
| `01_patients_and_demographics.csv` | Patient Intake | 60 | Complete demographics, ABHA IDs, phone numbers, addresses, wards, zones, and districts |
| `02_households.csv` | Community Health | 7 | Community households mapped to urban and rural wards |
| `03_visits_and_tokens.csv` | Front-Desk & OPD Queue | 108 | Patient visits, daily tokens, priority flags, queues, and arrival/completion timestamps |
| `04_triage_vitals.csv` | Nurse Triage | 105 | Blood pressure, pulse, temperature, SpO2, respiratory rate, height, weight, and BMI |
| `05_doctor_consultations_and_diagnoses.csv` | Medical Officer | 102 | Clinical history, examination findings, ICD-10 diagnoses, and treatment plans |
| `06_laboratory_orders_and_results.csv` | Diagnostics Lab | 75 | Test orders, specimen barcodes, numerical/qualitative results, reference ranges, and flags |
| `07_pharmacy_prescriptions.csv` | Doctor Prescriptions | 134 | Prescribed medications, dosage instructions, frequency, duration, and prescribed vs dispensed quantities |
| `08_pharmacy_dispensations.csv` | Medicine Dispensary | 132 | Generic dispensations, batch numbers, pharmacist counseling logs, and adherence flags |
| `09_inventory_ledger_double_entry.csv` | KSMSCL Stock Ledger | 173 | Double-entry stock movements (Rule 12 & 13), PURCHASE_RECEIPT and DISPENSE transactions |
| `10_ncd_chronic_care_and_assessments.csv` | NCD Program | 78 | Longitudinal Hypertension and Type-2 Diabetes serial BP and fasting glucose tracking |
| `11_idsp_disease_surveillance_cases.csv` | IDSP Public Health | 12 | Dengue, Typhoid, Malaria, and Gastroenteritis statutory surveillance cases and DSO dispatches |
| `12_inter_facility_referrals_and_events.csv` | Referrals & Specialist | 8 | Referrals from PHC to KC General Hospital (SDH) and Victoria Hospital (District Hospital) |
| `13_followup_tasks.csv` | Continuity of Care | 68 | Automated post-referral and routine NCD follow-up clinical tasks |
| `namma_clinic_all_sections_master.json` | Master JSON Bundle | All | Hierarchical single-file JSON representation of all data above for API / programmatic usage |

---

## 2. How the Other Person Can Use This Data

### A. Opening in Excel / Google Sheets / BI Tools
The recipient can open any of the 13 `.csv` files directly in Microsoft Excel, Apple Numbers, Google Sheets, PowerBI, or Tableau.

### B. Using in Python / Pandas
```python
import pandas as pd
patients_df = pd.read_csv('01_patients_and_demographics.csv')
visits_df = pd.read_csv('03_visits_and_tokens.csv')
vitals_df = pd.read_csv('04_triage_vitals.csv')
print(patients_df.head())
```

### C. Ingesting / Migrating Data into PostgreSQL Database
The recipient can easily ingest and load all 13 CSV files directly into the PostgreSQL / Django database using either of the two authoritative ingestion tools:

#### Method 1: Using the Standalone Ingestion Script
```bash
python scripts/ingest_clean_e2e_dataset.py --source exports/clean_e2e_dataset
```
*(Optional: add `--dry-run` to test and validate without writing changes to the database)*

#### Method 2: Using the Django Management Command
```bash
python backend/manage.py ingest_clean_e2e_dataset --dir exports/clean_e2e_dataset
```
*(Optional: add `--dry-run` for dry-run simulation)*

#### Method 3: Regenerating or Seeding from Scratch
To completely flush and re-synthesize this dataset end-to-end:
```bash
python scripts/generate_clean_e2e_dataset.py
```

---
Generated on: 2026-10-08 15:45:00
