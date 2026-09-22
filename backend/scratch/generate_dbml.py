import os
import sys
import django

# Setup django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps

type_map = {
    'AutoField': 'integer',
    'BigAutoField': 'bigint',
    'CharField': 'varchar',
    'TextField': 'text',
    'IntegerField': 'integer',
    'PositiveIntegerField': 'integer',
    'DecimalField': 'decimal(10,2)',
    'BooleanField': 'boolean',
    'DateField': 'date',
    'DateTimeField': 'datetime',
    'GenericIPAddressField': 'varchar',
    'FileField': 'varchar',
    'BigIntegerField': 'bigint',
    'EmailField': 'varchar',
}

dbml = []
dbml.append('// ==============================================================')
dbml.append('// NAMMA CLINIC - DBDiagram.io (DBML) Healthcare Database Schema')
dbml.append('// Generated from active Django production models')
dbml.append('// Copy and paste this directly into https://dbdiagram.io/d')
dbml.append('// ==============================================================\n')
dbml.append('Project namma_clinic {')
dbml.append('  database_type: \'SQLite\'')
dbml.append('  Note: \'Namma Clinic Comprehensive Healthcare System Database Model\'')
dbml.append('}\n')

table_groups = {
    'Geographic_Hierarchy': ['State', 'District', 'Zone', 'Ward', 'Facility', 'FacilityRelationship'],
    'Facility_Infrastructure': ['FacilityOxygenSupply', 'FacilityConsumableInventory', 'FacilityMaintenanceTicket', 'FacilityBedCapacity', 'FacilityBedAllocation'],
    'Accounts_And_Patients': ['User', 'Patient', 'Household', 'PatientDocument'],
    'OPD_Clinical_Engine': ['Visit', 'Token', 'VisitStatusHistory', 'TriageVitals', 'Consultation', 'Prescription', 'PrescriptionItem'],
    'Laboratory_Diagnostics': ['LabTestMaster', 'LabOrder', 'LabSample', 'LabResult'],
    'Pharmacy_And_Procurement': ['MedicineMaster', 'Vendor', 'MedicineBatch', 'PurchaseOrder', 'PurchaseOrderItem', 'InventoryTransaction'],
    'Referrals_And_Outreach': ['Referral', 'ReferralResponse', 'FollowUp', 'Teleconsultation', 'OutreachActivity', 'WellnessSession', 'NCDRecord', 'DiseaseCase'],
    'Governance_And_Audit': ['QualityChecklist', 'BiomedicalWasteLog', 'ARSMember', 'ARSMeeting', 'ARSActionItem', 'ReportExportLog', 'Alert', 'IntegrationConfiguration', 'ComplianceItem', 'AuditLog']
}

all_models = {}
for app in apps.get_app_configs():
    if app.name.startswith('apps.'):
        for model in app.get_models():
            all_models[model.__name__] = model

refs = []

for grp_name, model_names in table_groups.items():
    dbml.append(f'// --------------------------------------------------------------')
    dbml.append(f'// Table Group: {grp_name}')
    dbml.append(f'// --------------------------------------------------------------')
    for m_name in model_names:
        if m_name not in all_models:
            continue
        model = all_models[m_name]
        dbml.append(f'Table {m_name} {{')
        for f in model._meta.fields:
            if f.is_relation and f.related_model:
                col_name = f.column
                ftype = 'bigint'
            else:
                col_name = f.name
                ftype = type_map.get(f.get_internal_type(), 'varchar')

            attrs = []
            if f.primary_key:
                attrs.append('pk')
                attrs.append('increment')
            if f.unique and not f.primary_key:
                attrs.append('unique')
            if not f.null and not f.primary_key:
                attrs.append('not null')
            
            # Custom clinical notes
            if f.name == 'token_number':
                attrs.append("note: 'Daily unique per facility'")
            elif f.name == 'ABHA_ID_DEMO':
                attrs.append("note: 'Ayushman Bharat Digital Health ID'")
            elif f.name == 'diagnosis_code':
                attrs.append("note: 'ICD-10 Diagnostic Code'")
            elif f.name == 'expiry_date':
                attrs.append("note: 'FEFO sorting key'")
            elif f.name == 'transaction_type':
                attrs.append("note: 'PURCHASE_RECEIVED, DISPENSED, etc.'")
                
            attr_str = f" [{', '.join(attrs)}]" if attrs else ''
            dbml.append(f'  {col_name} {ftype}{attr_str}')
            
            if f.is_relation and f.related_model and f.related_model.__name__ in all_models:
                rel_model = f.related_model.__name__
                if f.one_to_one:
                    refs.append(f'Ref: {m_name}.{col_name} - {rel_model}.id')
                else:
                    refs.append(f'Ref: {m_name}.{col_name} > {rel_model}.id')
        dbml.append('}\n')

dbml.append('// ==============================================================')
dbml.append('// RELATIONSHIPS (FOREIGN KEYS & INTEGRITY CONSTRAINTS)')
dbml.append('// ==============================================================')
for r in refs:
    dbml.append(r)

dbml.append('\n// ==============================================================')
dbml.append('// TABLE GROUPS (ORGANIZED VISUAL CLUSTERS)')
dbml.append('// ==============================================================')
for grp_name, model_names in table_groups.items():
    valid_members = [m for m in model_names if m in all_models]
    if valid_members:
        dbml.append(f'TableGroup {grp_name} {{')
        for m in valid_members:
            dbml.append(f'  {m}')
        dbml.append('}\n')

output_text = '\n'.join(dbml)
out_path = os.path.join(os.path.dirname(__file__), 'dbdiagram_schema.dbml')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output_text)

print(f'Successfully generated {out_path} with {len(all_models)} tables and {len(refs)} relationships!')
