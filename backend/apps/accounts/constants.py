"""
Constants and definitions for Namma Clinic Role & Permission Catalogue.
Authoritative machine-readable role-permission mappings and seed data.
"""

# The Seven Approved Operational Roles
SEEDED_ROLES = [
    {
        "code": "DISTRICT_OFFICER",
        "name": "District Health Officer",
        "display_name": "District Health Officer",
        "description": "District-wide health oversight, facility management, and administrative appointment",
        "scope_level": "DISTRICT",
        "is_system_role": True,
        "is_active": True
    },
    {
        "code": "HOSPITAL_ADMIN",
        "name": "Hospital Administrator",
        "display_name": "Clinic Administrator",
        "description": "Facility-scoped administrative management, staff onboarding, and operational oversight",
        "scope_level": "FACILITY",
        "is_system_role": True,
        "is_active": True
    },
    {
        "code": "DOCTOR",
        "name": "Medical Officer",
        "display_name": "Doctor / Medical Officer",
        "description": "Clinical consultation, diagnosis, lab investigation ordering, and prescription creation",
        "scope_level": "FACILITY",
        "is_system_role": True,
        "is_active": True
    },
    {
        "code": "NURSE",
        "name": "Staff Nurse",
        "display_name": "Staff Nurse",
        "description": "Clinical triage, vital signs measurement, nursing assessment, and care coordination",
        "scope_level": "FACILITY",
        "is_system_role": True,
        "is_active": True
    },
    {
        "code": "COMPOUNDER",
        "name": "Compounder",
        "display_name": "Compounder / Registration Clerk",
        "description": "Front-desk patient registration, demographic updates, and OPD queue token issuance",
        "scope_level": "FACILITY",
        "is_system_role": True,
        "is_active": True
    },
    {
        "code": "LAB_TECHNICIAN",
        "name": "Lab Technician",
        "display_name": "Medical Laboratory Technologist",
        "description": "Specimen collection, diagnostic test execution, and laboratory result entry",
        "scope_level": "FACILITY",
        "is_system_role": True,
        "is_active": True
    },
    {
        "code": "PHARMACIST",
        "name": "Pharmacist",
        "display_name": "Pharmacist",
        "description": "Prescription verification, medicine dispensing, and clinical batch tracking",
        "scope_level": "FACILITY",
        "is_system_role": True,
        "is_active": True
    },
    {
        "code": "INVENTORY",
        "name": "Inventory Manager",
        "display_name": "Inventory Manager",
        "description": "Stock management, medicine batch tracking, purchase orders, and goods receipt notes",
        "scope_level": "FACILITY",
        "is_system_role": True,
        "is_active": True
    }
]

# The Canonical 57 Permissions across 13 Functional Domains
SEEDED_PERMISSIONS = [
    # PATIENT (3)
    {
        "code": "patients.read",
        "name": "Read Patient Demographics",
        "display_name": "Read Patient Demographics",
        "domain": "PATIENT",
        "action": "read",
        "description": "View citizen demographic profile and basic identifiers"
    },
    {
        "code": "patients.create",
        "name": "Register Citizen",
        "display_name": "Register Citizen",
        "domain": "PATIENT",
        "action": "create",
        "description": "Register a new citizen in the clinic / state health registry"
    },
    {
        "code": "patients.update_demographics",
        "name": "Update Demographics",
        "display_name": "Update Demographics",
        "domain": "PATIENT",
        "action": "update_demographics",
        "description": "Update whitelisted non-clinical demographic fields (name, mobile, address, emergency contact)"
    },

    # QUEUE (6)
    {
        "code": "queue.view",
        "name": "View OPD Queue",
        "display_name": "View OPD Queue",
        "domain": "QUEUE",
        "action": "view",
        "description": "View outpatient waiting queues, token statuses, and congestion metrics"
    },
    {
        "code": "queue.create",
        "name": "Create OPD Encounter",
        "display_name": "Create OPD Encounter",
        "domain": "QUEUE",
        "action": "create",
        "description": "Create an outpatient visit encounter for a patient"
    },
    {
        "code": "queue.issue_token",
        "name": "Issue OPD Token",
        "display_name": "Issue OPD Token",
        "domain": "QUEUE",
        "action": "issue_token",
        "description": "Atomically generate sequential daily token and place in triage queue"
    },
    {
        "code": "queue.call_next",
        "name": "Call Next Patient",
        "display_name": "Call Next Patient",
        "domain": "QUEUE",
        "action": "call_next",
        "description": "Call next waiting patient into service room for specific queue role"
    },
    {
        "code": "queue.transition",
        "name": "Transition Queue Status",
        "display_name": "Transition Queue Status",
        "domain": "QUEUE",
        "action": "transition",
        "description": "Advance visit encounter through workflow stages"
    },
    {
        "code": "queue.void",
        "name": "Void Duplicate Token",
        "display_name": "Void Duplicate Token",
        "domain": "QUEUE",
        "action": "void",
        "description": "Cancel an un-triaged duplicate token issued in error within 30 minutes"
    },

    # VITALS (2)
    {
        "code": "vitals.create",
        "name": "Record Vital Signs",
        "display_name": "Record Vital Signs",
        "domain": "VITALS",
        "action": "create",
        "description": "Measure and record clinical vital signs for an encounter"
    },
    {
        "code": "vitals.update",
        "name": "Update Vital Signs",
        "display_name": "Update Vital Signs",
        "domain": "VITALS",
        "action": "update",
        "description": "Modify or correct recorded clinical vital signs"
    },

    # TRIAGE (2)
    {
        "code": "triage.create",
        "name": "Record Triage Assessment",
        "display_name": "Record Triage Assessment",
        "domain": "TRIAGE",
        "action": "create",
        "description": "Conduct clinical triage grading and assign emergency acuity level"
    },
    {
        "code": "triage.update",
        "name": "Update Triage Assessment",
        "display_name": "Update Triage Assessment",
        "domain": "TRIAGE",
        "action": "update",
        "description": "Modify nursing triage notes or clinical acuity assessment"
    },

    # CONSULTATION (3)
    {
        "code": "consultation.create",
        "name": "Create Clinical Consultation",
        "display_name": "Create Clinical Consultation",
        "domain": "CONSULTATION",
        "action": "create",
        "description": "Conduct physician medical consultation and record clinical notes"
    },
    {
        "code": "consultation.read",
        "name": "View Clinical Consultation",
        "display_name": "View Clinical Consultation",
        "domain": "CONSULTATION",
        "action": "read",
        "description": "Access past clinical consultation notes and medical history"
    },
    {
        "code": "consultation.update",
        "name": "Update Clinical Consultation",
        "display_name": "Update Clinical Consultation",
        "domain": "CONSULTATION",
        "action": "update",
        "description": "Modify clinical consultation notes within allowable edit window"
    },

    # DIAGNOSIS (3)
    {
        "code": "diagnosis.create",
        "name": "Record Medical Diagnosis",
        "display_name": "Record Medical Diagnosis",
        "domain": "DIAGNOSIS",
        "action": "create",
        "description": "Assign provisional, differential, or ICD-10 diagnosis"
    },
    {
        "code": "diagnosis.read",
        "name": "View Medical Diagnosis",
        "display_name": "View Medical Diagnosis",
        "domain": "DIAGNOSIS",
        "action": "read",
        "description": "View patient diagnostic history and disease profiles"
    },
    {
        "code": "diagnosis.update",
        "name": "Update Medical Diagnosis",
        "display_name": "Update Medical Diagnosis",
        "domain": "DIAGNOSIS",
        "action": "update",
        "description": "Update or resolve assigned medical diagnoses"
    },

    # PRESCRIPTION (6)
    {
        "code": "prescription.create",
        "name": "Create Medical Prescription",
        "display_name": "Create Medical Prescription",
        "domain": "PRESCRIPTION",
        "action": "create",
        "description": "Prescribe medications and dosage regimens"
    },
    {
        "code": "prescription.read",
        "name": "View Medical Prescription",
        "display_name": "View Medical Prescription",
        "domain": "PRESCRIPTION",
        "action": "read",
        "description": "View prescription orders and medication history"
    },
    {
        "code": "prescription.update",
        "name": "Update Medical Prescription",
        "display_name": "Update Medical Prescription",
        "domain": "PRESCRIPTION",
        "action": "update",
        "description": "Modify medication prescription before dispensation"
    },
    {
        "code": "prescription.verify",
        "name": "Verify Prescription",
        "display_name": "Verify Prescription",
        "domain": "PRESCRIPTION",
        "action": "verify",
        "description": "Pharmacist clinical verification of prescription safety"
    },
    {
        "code": "prescription.hold",
        "name": "Hold Prescription",
        "display_name": "Hold Prescription",
        "domain": "PRESCRIPTION",
        "action": "hold",
        "description": "Temporarily hold prescription pending clinical clarification"
    },
    {
        "code": "prescription.reject",
        "name": "Reject Prescription",
        "display_name": "Reject Prescription",
        "domain": "PRESCRIPTION",
        "action": "reject",
        "description": "Reject prescription due to contraindication or error"
    },

    # LABORATORY (8)
    {
        "code": "lab_order.create",
        "name": "Create Lab Investigation Order",
        "display_name": "Create Lab Investigation Order",
        "domain": "LABORATORY",
        "action": "create",
        "description": "Order diagnostic laboratory investigations"
    },
    {
        "code": "lab_order.read",
        "name": "View Lab Investigation Orders",
        "display_name": "View Lab Investigation Orders",
        "domain": "LABORATORY",
        "action": "read",
        "description": "View laboratory test orders and statuses"
    },
    {
        "code": "specimen.collect",
        "name": "Collect Diagnostic Specimen",
        "display_name": "Collect Diagnostic Specimen",
        "domain": "LABORATORY",
        "action": "collect",
        "description": "Collect and label biological sample for testing"
    },
    {
        "code": "lab_result.create",
        "name": "Record Laboratory Test Result",
        "display_name": "Record Laboratory Test Result",
        "domain": "LABORATORY",
        "action": "create",
        "description": "Enter raw diagnostic test findings and values"
    },
    {
        "code": "lab_result.read",
        "name": "View Laboratory Test Results",
        "display_name": "View Laboratory Test Results",
        "domain": "LABORATORY",
        "action": "read",
        "description": "Access completed diagnostic investigation reports"
    },
    {
        "code": "lab_result.update",
        "name": "Update Laboratory Test Result",
        "display_name": "Update Laboratory Test Result",
        "domain": "LABORATORY",
        "action": "update",
        "description": "Edit preliminary diagnostic test result values"
    },
    {
        "code": "lab_result.verify",
        "name": "Verify Laboratory Test Result",
        "display_name": "Verify Laboratory Test Result",
        "domain": "LABORATORY",
        "action": "verify",
        "description": "Medical Officer review and clinical validation of report"
    },
    {
        "code": "lab_result.amend",
        "name": "Amend Verified Lab Result",
        "display_name": "Amend Verified Lab Result",
        "domain": "LABORATORY",
        "action": "amend",
        "description": "Formal amendment of verified report with recorded audit reason"
    },

    # PHARMACY (5)
    {
        "code": "inventory.read",
        "name": "View Pharmacy Stock",
        "display_name": "View Pharmacy Stock",
        "domain": "PHARMACY",
        "action": "read",
        "description": "View drug inventory stock levels and ledger balances"
    },
    {
        "code": "inventory.adjust",
        "name": "Adjust Pharmacy Inventory",
        "display_name": "Adjust Pharmacy Inventory",
        "domain": "PHARMACY",
        "action": "adjust",
        "description": "Record stock adjustment, wastage, or physical count discrepancy"
    },
    {
        "code": "dispensation.create",
        "name": "Dispense Medication",
        "display_name": "Dispense Medication",
        "domain": "PHARMACY",
        "action": "create",
        "description": "Dispense prescribed medications and deduct batch stock"
    },
    {
        "code": "dispensation.read",
        "name": "View Dispensation History",
        "display_name": "View Dispensation History",
        "domain": "PHARMACY",
        "action": "read",
        "description": "View medication dispensation logs and patient issues"
    },
    {
        "code": "medicine_batch.read",
        "name": "View Medicine Batches",
        "display_name": "View Medicine Batches",
        "domain": "PHARMACY",
        "action": "read",
        "description": "View batch numbers, expiries, and cold chain statuses"
    },

    # PROCUREMENT (5)
    {
        "code": "purchase_order.create",
        "name": "Create Purchase Order",
        "display_name": "Create Purchase Order",
        "domain": "PROCUREMENT",
        "action": "create",
        "description": "Draft facility medicine / consumable purchase order"
    },
    {
        "code": "purchase_order.read",
        "name": "View Purchase Orders",
        "display_name": "View Purchase Orders",
        "domain": "PROCUREMENT",
        "action": "read",
        "description": "View purchase orders and vendor fulfillment statuses"
    },
    {
        "code": "purchase_order.update",
        "name": "Update Purchase Order",
        "display_name": "Update Purchase Order",
        "domain": "PROCUREMENT",
        "action": "update",
        "description": "Edit line items or quantities on draft purchase order"
    },
    {
        "code": "purchase_order.approve",
        "name": "Approve Purchase Order",
        "display_name": "Approve Purchase Order",
        "domain": "PROCUREMENT",
        "action": "approve",
        "description": "Administrative approval authorizing purchase order issue to vendor"
    },
    {
        "code": "goods_receipt.create",
        "name": "Record Goods Receipt",
        "display_name": "Record Goods Receipt",
        "domain": "PROCUREMENT",
        "action": "create",
        "description": "Log incoming shipment delivery and inspect batch lots"
    },

    # STAFF (9)
    {
        "code": "staff.read",
        "name": "View Staff Directory",
        "display_name": "View Staff Directory",
        "domain": "STAFF",
        "action": "read",
        "description": "View clinic staff members, postings, and roles"
    },
    {
        "code": "staff.create",
        "name": "Register Staff Profile",
        "display_name": "Register Staff Profile",
        "domain": "STAFF",
        "action": "create",
        "description": "Create professional staff identity record linked to a Person"
    },
    {
        "code": "staff.invite",
        "name": "Invite Staff Member",
        "display_name": "Invite Staff Member",
        "domain": "STAFF",
        "action": "invite",
        "description": "Issue activation link or initial system credentials"
    },
    {
        "code": "staff.assign_role",
        "name": "Assign Operational Role",
        "display_name": "Assign Operational Role",
        "domain": "STAFF",
        "action": "assign_role",
        "description": "Grant operational role assignment with effective date window"
    },
    {
        "code": "staff.end_role",
        "name": "End Operational Role",
        "display_name": "End Operational Role",
        "domain": "STAFF",
        "action": "end_role",
        "description": "Terminate an active role assignment"
    },
    {
        "code": "staff.assign_facility",
        "name": "Assign Facility Posting",
        "display_name": "Assign Facility Posting",
        "domain": "STAFF",
        "action": "assign_facility",
        "description": "Post staff member to healthcare facility or department"
    },
    {
        "code": "staff.transfer",
        "name": "Transfer Staff Member",
        "display_name": "Transfer Staff Member",
        "domain": "STAFF",
        "action": "transfer",
        "description": "Initiate or authorize inter-facility staff transfer"
    },
    {
        "code": "staff.suspend",
        "name": "Suspend Staff Member",
        "display_name": "Suspend Staff Member",
        "domain": "STAFF",
        "action": "suspend",
        "description": "Temporarily suspend staff access during leave or inquiry"
    },
    {
        "code": "staff.deactivate",
        "name": "Deactivate Staff Member",
        "display_name": "Deactivate Staff Member",
        "domain": "STAFF",
        "action": "deactivate",
        "description": "Permanently deactivate separated, retired, or resigned staff"
    },

    # FACILITY (4)
    {
        "code": "facility.read",
        "name": "View Facility Details",
        "display_name": "View Facility Details",
        "domain": "FACILITY",
        "action": "read",
        "description": "View healthcare facility infrastructure and services"
    },
    {
        "code": "facility.create",
        "name": "Create Health Facility",
        "display_name": "Create Health Facility",
        "domain": "FACILITY",
        "action": "create",
        "description": "Register new primary healthcare clinic or health center"
    },
    {
        "code": "facility.update",
        "name": "Update Facility Details",
        "display_name": "Update Facility Details",
        "domain": "FACILITY",
        "action": "update",
        "description": "Update facility operational hours, beds, or service capabilities"
    },
    {
        "code": "facility.deactivate",
        "name": "Deactivate Health Facility",
        "display_name": "Deactivate Health Facility",
        "domain": "FACILITY",
        "action": "deactivate",
        "description": "Decommission or suspend clinic operations"
    },

    # AUDIT (1)
    {
        "code": "audit.read",
        "name": "View Security Audit Logs",
        "display_name": "View Security Audit Logs",
        "domain": "AUDIT",
        "action": "read",
        "description": "Access immutable regulatory and security audit logs"
    }
]

# Explicit Role -> Permission Mapping for the 7 Operational Roles
ROLE_PERMISSION_MAP = {
    "COMPOUNDER": [
        "patients.read",
        "patients.create",
        "patients.update_demographics",
        "queue.view",
        "queue.create",
        "queue.issue_token",
        "queue.void"
    ],
    "NURSE": [
        "patients.read",
        "queue.view",
        "queue.call_next",
        "queue.transition",
        "vitals.create",
        "vitals.update",
        "triage.create",
        "triage.update",
        "consultation.read",
        "diagnosis.read",
        "prescription.read",
        "lab_order.read",
        "lab_result.read",
        "specimen.collect",
        "medicine_batch.read"
    ],
    "DOCTOR": [
        "patients.read",
        "queue.view",
        "queue.call_next",
        "queue.transition",
        "vitals.create",
        "vitals.update",
        "triage.create",
        "triage.update",
        "consultation.create",
        "consultation.read",
        "consultation.update",
        "diagnosis.create",
        "diagnosis.read",
        "diagnosis.update",
        "prescription.create",
        "prescription.read",
        "prescription.update",
        "lab_order.create",
        "lab_order.read",
        "lab_result.read",
        "lab_result.verify",
        "medicine_batch.read"
    ],
    "LAB_TECHNICIAN": [
        "patients.read",
        "queue.view",
        "queue.call_next",
        "queue.transition",
        "lab_order.read",
        "specimen.collect",
        "lab_result.create",
        "lab_result.read",
        "lab_result.update",
        "lab_result.amend"
    ],
    "PHARMACIST": [
        "patients.read",
        "queue.view",
        "queue.call_next",
        "queue.transition",
        "prescription.read",
        "prescription.verify",
        "prescription.hold",
        "prescription.reject",
        "dispensation.create",
        "dispensation.read",
        "inventory.read",
        "medicine_batch.read"
    ],
    "INVENTORY": [
        "inventory.read",
        "inventory.adjust",
        "medicine_batch.read",
        "purchase_order.create",
        "purchase_order.read",
        "purchase_order.update",
        "goods_receipt.create"
    ],
    "HOSPITAL_ADMIN": [
        "patients.read",
        "patients.create",
        "patients.update_demographics",
        "queue.view",
        "queue.create",
        "queue.issue_token",
        "queue.void",
        "inventory.read",
        "purchase_order.read",
        "purchase_order.approve",
        "staff.read",
        "staff.create",
        "staff.invite",
        "staff.assign_role",
        "staff.end_role",
        "staff.assign_facility",
        "staff.transfer",
        "staff.suspend",
        "staff.deactivate",
        "facility.read",
        "facility.update",
        "audit.read"
    ],
    "DISTRICT_OFFICER": [
        "patients.read",
        "queue.view",
        "consultation.read",
        "diagnosis.read",
        "prescription.read",
        "lab_order.read",
        "lab_result.read",
        "inventory.read",
        "purchase_order.read",
        "purchase_order.approve",
        "staff.read",
        "staff.create",
        "staff.invite",
        "staff.assign_role",
        "staff.end_role",
        "staff.assign_facility",
        "staff.transfer",
        "staff.suspend",
        "staff.deactivate",
        "facility.read",
        "facility.create",
        "facility.update",
        "facility.deactivate",
        "audit.read"
    ]
}

def generate_role_permission_matrix():
    """
    Generates an explicit machine-readable matrix of (Role, Permission, Access, Scope, Reason)
    for all 7 operational roles and all 57 permissions.
    """
    matrix = []
    all_perm_codes = [p["code"] for p in SEEDED_PERMISSIONS]
    roles_dict = {r["code"]: r for r in SEEDED_ROLES}

    for role_code, role_info in roles_dict.items():
        allowed_perms = set(ROLE_PERMISSION_MAP.get(role_code, []))
        scope = role_info["scope_level"]

        for perm_code in all_perm_codes:
            if perm_code in allowed_perms:
                access = "ALLOW"
                reason = f"Authorized operational capability for {role_info['display_name']} within {scope} scope"
            else:
                access = "DENY"
                reason = f"Explicitly prohibited: {role_info['display_name']} lacks authority for {perm_code}"

            matrix.append({
                "role": role_code,
                "role_name": role_info["display_name"],
                "permission": perm_code,
                "access": access,
                "scope": scope,
                "reason": reason
            })
    return matrix
