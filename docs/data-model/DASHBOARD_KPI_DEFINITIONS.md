# Namma Clinic — Dashboard KPI Standard Definitions

## 1. Objective

To ensure absolute analytical integrity, prevent data discrepancies, and eliminate hardcoded fallbacks or client-side calculation errors, this document defines unambiguous, mathematically precise standard definitions for all dashboard KPIs across the Namma Clinic platform.

---

## 2. Standardized KPI Definitions

### KPI 01: TOTAL REGISTERED PATIENTS (DISTRICT SCOPE)
- **Business Meaning**: The cumulative count of unique individual citizens registered in the patient master directory within the administrative boundaries of the selected district or facility.
- **Ambiguity Eliminated**: Resolves ambiguity between patients physically registered at a facility versus external patients receiving emergency care via referral.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(DISTINCT p.id)
  FROM patients_patient p
  WHERE (:facility_id IS NULL OR p.registered_at_facility_id = :facility_id)
    AND (:district_id IS NULL OR p.district_id = :district_id);
  ```

---

### KPI 02: OPD FOOTFALL / PATIENTS TODAY
- **Business Meaning**: The count of distinct individual patients who checked in for an Outpatient Department (OPD) visit on the specified date at the selected facility.
- **Ambiguity Eliminated**: Eliminates counting multiple token re-prints or duplicate queue advancements for the same citizen on the same date.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(DISTINCT v.patient_id)
  FROM visits_visit v
  WHERE v.opd_date = :target_date
    AND (:facility_id IS NULL OR v.facility_id = :facility_id)
    AND v.status NOT IN ('CANCELLED', 'NO_SHOW');
  ```

---

### KPI 03: ACTIVE OPD WAITING QUEUE
- **Business Meaning**: The current number of OPD visits awaiting nurse triage, doctor consultation, or pharmacy dispensing on the selected date.
- **Ambiguity Eliminated**: Prevents completed or cancelled visits from inflating active queue counts.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(v.id)
  FROM visits_visit v
  WHERE v.opd_date = :target_date
    AND (:facility_id IS NULL OR v.facility_id = :facility_id)
    AND v.status IN ('WAITING_FOR_TRIAGE', 'WAITING_FOR_DOCTOR', 'TRIAGED', 'WAITING_FOR_PHARMACY');
  ```

---

### KPI 04: TOTAL CONSULTATIONS COMPLETED
- **Business Meaning**: The count of finalized doctor consultations conducted and recorded in the EMR during the specified timeframe.
- **Ambiguity Eliminated**: Disconnects consultation metrics from generic OPD visit creations; counts only visits where a clinical note and diagnosis were recorded.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(c.id)
  FROM consultations_consultation c
  JOIN visits_visit v ON c.visit_id = v.id
  WHERE v.opd_date = :target_date
    AND (:facility_id IS NULL OR c.facility_id = :facility_id);
  ```

---

### KPI 05: DIAGNOSTIC LAB ORDERS PENDING
- **Business Meaning**: Diagnostic tests ordered by Medical Officers where samples have either not been collected or laboratory analysis is awaiting technician verification.
- **Ambiguity Eliminated**: Restricts pending status strictly to non-finalized orders; excludes completed/verified results.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(lo.id)
  FROM laboratory_laborder lo
  WHERE (:facility_id IS NULL OR lo.facility_id = :facility_id)
    AND (:target_date IS NULL OR DATE(lo.order_date) = :target_date)
    AND lo.status IN ('ORDERED', 'SAMPLE_COLLECTED', 'RESULT_ENTRY');
  ```

---

### KPI 06: PHARMACY DISPENSATIONS TODAY
- **Business Meaning**: The total number of doctor prescriptions successfully fulfilled and dispensed to citizens on the specified date.
- **Ambiguity Eliminated**: Fixes the frontend slicing issue in `PharmacistDashboard.tsx` where `.filter()` was run on the first 50 paginated rows.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(DISTINCT p.id)
  FROM consultations_prescription p
  WHERE p.date = :target_date
    AND (:facility_id IS NULL OR p.facility_id = :facility_id)
    AND p.status = 'DISPENSED';
  ```

---

### KPI 07: ACTIVE MEDICINE BATCHES IN STOCK
- **Business Meaning**: The number of unique essential drug batches currently available in physical store inventory with non-zero stock and unexpired validity.
- **Ambiguity Eliminated**: Removes the hardcoded backend fallback `or 14` and accurately counts active batches.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(mb.id)
  FROM pharmacy_medicinebatch mb
  WHERE (:facility_id IS NULL OR mb.facility_id = :facility_id)
    AND mb.quantity > 0
    AND mb.expiry_date > CURRENT_DATE
    AND mb.status != 'EXPIRED';
  ```

---

### KPI 08: LOW-STOCK DRUG ALERTS
- **Business Meaning**: Generic medicines whose combined available stock across all active, unexpired batches at a facility falls at or below the medicine's defined reorder threshold.
- **Ambiguity Eliminated**: Replaces the generic arbitrary hardcoded `100` unit cutoff with each generic drug's specific `minimum_stock` or `reorder_level`.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(m.id)
  FROM pharmacy_medicinemaster m
  WHERE (
      SELECT COALESCE(SUM(mb.quantity), 0)
      FROM pharmacy_medicinebatch mb
      WHERE mb.medicine_id = m.id
        AND (:facility_id IS NULL OR mb.facility_id = :facility_id)
        AND mb.expiry_date > CURRENT_DATE
        AND mb.quantity > 0
  ) <= m.reorder_level;
  ```

---

### KPI 09: PENDING CROSS-FACILITY REFERRALS
- **Business Meaning**: Outbound patient referral transfers initiated from a primary health clinic to a higher-tier specialist hospital that are actively in progress and awaiting specialist feedback.
- **Ambiguity Eliminated**: Clarifies directional ownership (source vs destination facility) and status transitions.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(r.id)
  FROM referrals_referral r
  WHERE (:facility_id IS NULL OR r.source_facility_id = :facility_id)
    AND r.status IN ('CREATED', 'ACCEPTED', 'IN_TRANSIT', 'UNDER_TREATMENT');
  ```

---

### KPI 10: SCHEDULED LONGITUDINAL FOLLOW-UPS
- **Business Meaning**: The count of chronic disease reviews and post-referral routine return appointments due on or before the specified date.
- **Ambiguity Eliminated**: Corrects the critical bug where `DoctorDashboard.tsx` was displaying `referrals_summary.completed` under the label "Follow-ups". Now directly bound to `summary.followups_summary.due_today` backed by `referrals_followup`.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(fu.id)
  FROM referrals_followup fu
  WHERE (:facility_id IS NULL OR fu.facility_id = :facility_id)
    AND fu.due_date = :target_date
    AND fu.status IN ('PENDING', 'DUE_TODAY');
  ```

---

### KPI 11: NCD COHORT UNDER ACTIVE TREATMENT
- **Business Meaning**: The number of registered citizens identified with Hypertension or Diabetes receiving regular treatment and monitoring.
- **Formal SQL Definition**:
  ```sql
  SELECT COUNT(DISTINCT n.patient_id)
  FROM ncd_ncdrecord n
  WHERE (:facility_id IS NULL OR n.facility_id = :facility_id)
    AND (n.hypertension_diagnosed = TRUE OR n.diabetes_diagnosed = TRUE)
    AND n.treatment_status = 'UNDER_TREATMENT';
  ```

---

### KPI 12: WARD DISEASE SURVEILLANCE ANOMALY INDEX
- **Business Meaning**: The rolling 7-day cumulative count of communicable fever or diarrheal illness cases within a specific municipal ward.
- **Ambiguity Eliminated**: Translates the hardcoded "15 cases" text banner into a dynamically computable metric against baseline thresholds.
- **Formal SQL Definition**:
  ```sql
  SELECT dc.ward_id, dc.disease_name, COUNT(dc.id) AS weekly_case_count
  FROM surveillance_diseasecase dc
  WHERE dc.report_date BETWEEN DATE('now', '-7 days') AND DATE('now')
    AND (:ward_id IS NULL OR dc.ward_id = :ward_id)
  GROUP BY dc.ward_id, dc.disease_name;
  ```
