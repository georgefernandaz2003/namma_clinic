# Namma Clinic — Pharmacy Current State Audit & Baseline Analysis

**Audit Cycle:** Phase 1 — Pharmacy Baseline & Capability Assessment  
**Baseline Commit:** `4cedfb9200e59e7e2442d81cb3d7be800600f13f`  
**Branch:** `feature/namma-clinic-demo-data-model`  
**Target Subsystems:**
- `backend/apps/pharmacy/` (`models.py`, `views.py`, `serializers.py`)
- `backend/apps/consultations/` (`models.py`, `views.py`)
- `frontend/src/pages/Pharmacy.tsx`
- `frontend/src/components/dashboards/PharmacistDashboard.tsx`
- `backend/config/api_urls.py`

---

## 1. Executive Summary

An exhaustive current-state audit of the Namma Clinic Pharmacy subsystem was conducted against:
1. **WHO Good Pharmacy Practice (GPP)** (safe dispensing, prescription assessment, traceability, counselling, safety monitoring).
2. **Indian Primary Care Guidelines** (IPHS Revised Guidelines 2022 for HWC-PHC).
3. **Drugs Rules, 1945** (schedule handling, storage, expiry control, batch traceability).

The application currently has a functional operational foundation for:
- Prescription-driven FEFO dispensing (`DispenseMedicineView` in `views.py:746`)
- Basic medicine master and batch management (`MedicineMaster`, `MedicineBatch`)
- Basic inventory transaction logging (`InventoryTransaction`)
- Purchase Order draft, approval, and order lifecycle (`PurchaseOrderViewSet`)
- Basic receiving of goods (`receive_items` action on `PurchaseOrderViewSet`)
- Role-based access control gating pharmacist and admin permissions

However, critical safety, traceability, and lifecycle gaps exist that require hardening:
- **No Formal Pharmacist Verification Step:** Prescriptions go directly from doctor creation to dispensing without a recorded verification/safety review gate.
- **Dispensation Records Lack Deep Traceability:** `InventoryTransaction` records `quantity`, `medicine`, `batch`, and `reference_id="PRESCR-<id>"`, but does not record before/after stock quantities, prescription item IDs, patient IDs, visit IDs, or dosage directions directly.
- **Partial Dispensing Incomplete:** While `PARTIALLY_DISPENSED` status exists on prescription items, there is no explicit `dispensed_quantity` field on `PrescriptionItem`, preventing precise calculation of remaining quantities on multi-step dispensations.
- **No Dispensing Return / Reversal Workflow:** Returned medications cannot be reversed in an auditable manner into stock, quarantine, or disposal.
- **No Quarantine / Recall Mechanism:** Batches only have statuses `ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, and `EXHAUSTED`. Quarantining or recalling a contaminated/substandard batch is not supported in the data model.
- **Goods Receipt (GRN) Not Decoupled:** Receiving is implemented directly on `PurchaseOrderViewSet` without a distinct Goods Receipt Note (GRN) entity for multi-batch physical inspection, rejection logging, or vendor invoice matching.
- **Medicine Master Lacks Regulatory & Safety Metadata:** Fields for NLEM, AWaRe classification, high-alert flags, cold-chain requirements, and regulatory schedules are absent.

---

## 2. Detailed Capability Assessment Matrix

| # | Pharmacy Capability | Current Status | Code Location | Observed Behavior | Required Hardening | Priority |
|:---|:---|:---:|:---|:---|:---|:---:|
| 1 | **Prescription Verification** | **Missing** | `consultations/models.py:24`, `pharmacy/views.py:746` | Doctor saves prescription with `status='ACTIVE'`. Pharmacist immediately dispenses without recorded verification. | Add `PENDING_VERIFICATION`, `VERIFIED`, `ON_HOLD`, `REJECTED` lifecycle. Add verification endpoint with safety checklist. | **P0** |
| 2 | **Batch-Level Dispensing Traceability** | **Partial** | `pharmacy/models.py:112`, `pharmacy/views.py:842` | `InventoryTransaction` links to `batch`, but lacks before/after quantities, patient, visit, and explicit prescription item link. | Add before/after stock balances, direct prescription/item foreign keys, and structured dispense record. | **P0** |
| 3 | **Expired Medicine Hard Block** | **Existing (Needs Hardening)** | `pharmacy/views.py:808, 826` | Backend validates `batch.expiry_date <= today` during dispense and rejects with 400. | Add explicit `EXPIRED` status check, hard-block at query level, and UI disablement with clear visual alerts. | **P0** |
| 4 | **FEFO Batch Selection** | **Existing** | `pharmacy/views.py:800-820` | Automatically queries `expiry_date__gt=today` ordered by `expiry_date`. | Preserve and extend FEFO to exclude `QUARANTINED`, `EXPIRED`, `RECALLED` batches. | **P0** |
| 5 | **Quarantine & Batch Statuses** | **Missing** | `pharmacy/models.py:51` | Choices limited to `ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, `EXHAUSTED`. | Add `QUARANTINED`, `RECALLED`, `DAMAGED`, `DISPOSED`. Add quarantine/release actions with audit logs. | **P0** |
| 6 | **Immutable Inventory Transaction Ledger** | **Partial** | `pharmacy/models.py:112` | Only 8 transaction types; lacks before/after quantities and structured reference metadata. | Add before/after stock tracking, expanded transaction types (`QUARANTINE`, `RELEASE`, `RETURN`, `DISPOSAL`, `RECALL`), and immutability guard. | **P0** |
| 7 | **Dispensing Reversal / Return** | **Missing** | `pharmacy/views.py` | No endpoint or UI to accept returned medication or reverse accidental dispense. | Implement return/reversal workflow with disposition choices (`RETURN_TO_STOCK`, `QUARANTINE`, `DISPOSAL`) and transaction reversal logging. | **P0** |
| 8 | **Partial Dispensing** | **Partial** | `consultations/models.py:54`, `pharmacy/views.py:853` | `PrescriptionItem.status` sets to `PARTIALLY_DISPENSED`, but lacks `dispensed_quantity` field to track cumulative fulfillment. | Add `dispensed_quantity` field to `PrescriptionItem`, enforce `dispensed_quantity <= quantity`, allow multiple partial dispense events. | **P0** |
| 9 | **Prescription Lifecycle Normalization** | **Partial** | `consultations/models.py:24` | Status defaults to `ACTIVE` and transitions to `DISPENSED`. No rejection, hold, or cancellation audit. | Support full normalized lifecycle: `PENDING_VERIFICATION`, `VERIFIED`, `ON_HOLD`, `PARTIALLY_DISPENSED`, `DISPENSED`, `CANCELLED`, `EXPIRED`. | **P0** |
| 10 | **Goods Receipt / GRN** | **Partial** | `pharmacy/models.py:64`, `pharmacy/views.py:567` | Receiving logic is embedded inside `PurchaseOrderViewSet._execute_goods_receiving`. No separate GRN entity. | Create `GoodsReceiptNote` (GRN) and `GoodsReceiptItem` models for physical inspection, rejection logging, and inventory receipt decoupling. | **P1** |
| 11 | **Expiry Management & Bucketing** | **Partial** | `pharmacy/views.py:931, 1031` | Fixed 60-day and 30-day thresholds in code. No standardized bucketing. | Add standardized expiry buckets (`EXPIRED`, `0-30 DAYS`, `31-60 DAYS`, `61-90 DAYS`, `>90 DAYS`) in dashboard and batch views. | **P1** |
| 12 | **Controlled Stock Disposal** | **Missing** | `pharmacy/views.py` | Expired stock remains in `MedicineBatch` forever or is deleted via generic DELETE API. | Implement controlled disposal action requiring quantity, reason, disposal method, authorized user, creating `DISPOSAL` transaction. | **P1** |
| 13 | **Batch Recall Mechanism** | **Missing** | `pharmacy/views.py` | No ability to declare a batch recalled across the facility or network. | Implement batch recall action: marks batch `RECALLED`, locks remaining stock into quarantine, generates transaction impact report. | **P1** |
| 14 | **Medicine Master Regulatory Metadata** | **Missing** | `pharmacy/models.py:4` | Has only generic_name, brand_name, strength, dosage_form, unit, category, min/reorder stock. | Add `regulatory_schedule`, `prescription_required`, `high_alert`, `cold_chain_required`, `route`, `essential_medicine`. | **P1** |
| 15 | **NLEM Reference Support** | **Missing** | `pharmacy/models.py:4` | No NLEM field. | Add `nlem_reference` (CharField) and `essential_medicine` (BooleanField) to `MedicineMaster`. | **P2** |
| 16 | **AWaRe Antibiotic Metadata** | **Missing** | `pharmacy/models.py:4` | No classification for antibiotics. | Add `antibiotic` (Boolean) and `aware_category` (`ACCESS`, `WATCH`, `RESERVE`, `NONE`) metadata fields for reporting. | **P2** |
| 17 | **High-Alert Medication Warnings** | **Missing** | `pharmacy/models.py:4`, `Pharmacy.tsx` | No indicator for high-alert medications (e.g. insulin, anticoagulants). | Add `high_alert` flag and render distinct warning banners during verification and dispensing. | **P1** |
| 18 | **Patient Counselling Record** | **Missing** | `consultations/models.py` | No structured counselling tracking. | Add `PatientCounselling` model and UI checklist (dose, frequency, food, storage, warning signs). | **P1** |
| 19 | **Cold-Chain / Temperature Logging** | **Missing** | `pharmacy/models.py` | No temperature log for cold-chain medicines. | Add `ColdChainLog` model for manual recording of storage temperature (min, max, recorded, status). | **P1** |
| 20 | **Pharmacy Audit Trail** | **Partial** | `pharmacy/views.py:886` | Records basic `AuditLog` entries for create/update/dispense. | Standardize audit logging across all new operations (verification, hold, reject, return, quarantine, disposal, recall, counselling). | **P0** |
| 21 | **Pharmacy Dashboard Scoping** | **Existing (Needs Expansion)** | `pharmacy/views.py:901`, `PharmacistDashboard.tsx` | Scoped to facility, uses real queries. Lacks verification and safety metrics. | Add metrics for pending verification, holds, returns, quarantined batches, and GRNs. | **P1** |
| 22 | **Pharmacy RBAC Boundaries** | **Existing** | `accounts/permissions.py`, `pharmacy/views.py` | Enforces `pharmacy.dispense` and `inventory.*` permissions. Barred doctors/nurses/DHO from dispensing. | Preserve existing strict RBAC model; restrict GRN/reversal/quarantine to authorized roles. | **P0** |

---

## 3. Data Model Analysis & Schema Migration Strategy

To support the above capabilities without breaking existing data or regression invariants, the schema enhancements will be implemented via non-destructive Django migrations:

1. **`MedicineMaster` Extensions:**
   - `regulatory_schedule`: CharField choices (`SCHEDULE_H`, `SCHEDULE_H1`, `SCHEDULE_X`, `SCHEDULE_G`, `OTC`, `GENERAL`), default `'SCHEDULE_H'`.
   - `prescription_required`: BooleanField, default `True`.
   - `high_alert`: BooleanField, default `False`.
   - `cold_chain_required`: BooleanField, default `False`.
   - `essential_medicine`: BooleanField, default `True`.
   - `nlem_reference`: CharField, default `'NLEM 2022'`, blank=True.
   - `antibiotic`: BooleanField, default `False`.
   - `aware_category`: CharField choices (`ACCESS`, `WATCH`, `RESERVE`, `NONE`), default `'NONE'`.
   - `route`: CharField, default `'Oral'`.

2. **`MedicineBatch` Status Extension:**
   - Extend `status` choices to include `QUARANTINED`, `RECALLED`, `DAMAGED`, `DISPOSED`.

3. **`Prescription` Lifecycle Extension:**
   - Extend `status` choices to include `PENDING_VERIFICATION`, `VERIFIED`, `ON_HOLD`, `REJECTED`, `CANCELLED`, `EXPIRED`.
   - Add verification fields: `verified_by` (FK User), `verified_at` (DateTimeField), `verification_notes` (TextField).

4. **`PrescriptionItem` Dispensed Quantity:**
   - Add `dispensed_quantity`: IntegerField, default `0`.
   - Invariant: `dispensed_quantity <= quantity`. Status is `PENDING` if 0, `PARTIALLY_DISPENSED` if `0 < dispensed_quantity < quantity`, and `DISPENSED` if `dispensed_quantity == quantity`.

5. **`InventoryTransaction` Ledger Hardening:**
   - Add `before_quantity`: IntegerField, default `0`.
   - Add `after_quantity`: IntegerField, default `0`.
   - Add `patient`: ForeignKey Patient (null=True, blank=True).
   - Add `visit`: ForeignKey Visit (null=True, blank=True).
   - Add `prescription`: ForeignKey Prescription (null=True, blank=True).
   - Add `prescription_item`: ForeignKey PrescriptionItem (null=True, blank=True).
   - Extend `transaction_type` choices: `PURCHASE_RECEIVED`, `DISPENSED`, `RETURNED`, `ADJUSTMENT`, `DAMAGED`, `EXPIRED`, `QUARANTINE`, `RELEASE`, `DISPOSAL`, `RECALL`, `ISSUED`, `TRANSFERRED`.

6. **New Models:**
   - `GoodsReceiptNote` (GRN): `grn_number`, `purchase_order`, `vendor`, `facility`, `invoice_number`, `invoice_date`, `received_date`, `received_by`, `status`, `notes`.
   - `GoodsReceiptItem`: `grn`, `po_item`, `medicine`, `batch_number`, `mfg_date`, `expiry_date`, `ordered_quantity`, `received_quantity`, `rejected_quantity`, `rejection_reason`, `accepted_quantity`, `unit_cost`.
   - `DispensationReturn`: `prescription`, `prescription_item`, `batch`, `facility`, `returned_quantity`, `reason`, `disposition` (`RETURN_TO_STOCK`, `QUARANTINE`, `DISPOSAL`), `returned_by`, `created_at`.
   - `BatchRecall`: `batch`, `facility`, `recall_reference`, `reason`, `initiated_by`, `recalled_at`, `status`.
   - `PatientCounselling`: `prescription`, `patient`, `pharmacist`, `counselled_at`, checklist booleans, `notes`.
   - `ColdChainLog`: `facility`, `storage_location`, `min_temp`, `max_temp`, `recorded_temp`, `recorded_by`, `recorded_at`, `status`.

---

## 4. Immediate Next Steps & Implementation Road Map

1. Create `implementation_plan.md` artifact detailing all changes, API contracts, verification plan, and testing strategy.
2. Present the plan to the user for formal approval.
3. Upon approval, execute backend migrations, serializers, views, test suite, frontend updates, and UAT validation.
