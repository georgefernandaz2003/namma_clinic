from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.geography.models import State, District
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices
from apps.accounts.permissions import ROLE_PERMISSIONS
from apps.pharmacy.models import MedicineMaster

User = get_user_model()

class MedicineMasterRBACSecurityTests(APITestCase):
    def setUp(self):
        # Setup Geography & Facility
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR-U', state=self.state)
        self.facility = Facility.objects.create(
            facility_code='FAC-001',
            facility_name='Namma Clinic Jayanagar',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district
        )

        # Setup Users for each role
        self.pharmacist = User.objects.create_user(
            username='pharmacist_user',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility,
            full_name='Pharmacist User'
        )

        self.hospital_admin = User.objects.create_user(
            username='hospital_admin_user',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.facility,
            full_name='Hospital Admin User'
        )

        self.doctor = User.objects.create_user(
            username='doctor_user',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility,
            full_name='Doctor User'
        )

        self.nurse = User.objects.create_user(
            username='nurse_user',
            password='password123',
            role=RoleChoices.NURSE,
            assigned_facility=self.facility,
            full_name='Nurse User'
        )

        self.lab_tech = User.objects.create_user(
            username='lab_tech_user',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.facility,
            full_name='Lab Technician User'
        )

        self.district_officer = User.objects.create_user(
            username='district_officer_user',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district,
            full_name='District Officer User'
        )

        # Create baseline MedicineMaster
        self.medicine = MedicineMaster.objects.create(
            generic_name='Paracetamol',
            brand_name='Dolo 650',
            strength='650 mg',
            dosage_form='Tablet',
            unit='Tablets',
            category='Analgesic',
            minimum_stock=50,
            reorder_level=100
        )

    # 1. Unauthenticated user checks
    def test_unauthenticated_user_cannot_create_medicine(self):
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Ibuprofen',
            'brand_name': 'Brufen',
            'strength': '400 mg',
            'dosage_form': 'Tablet',
            'unit': 'Tablets',
            'category': 'NSAID',
            'minimum_stock': 20,
            'reorder_level': 40
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_list_medicines(self):
        res = self.client.get('/api/pharmacy/medicines/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # 2. DOCTOR cannot mutate medicine master
    def test_doctor_cannot_create_medicine(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amoxicillin',
            'brand_name': 'Mox',
            'strength': '500 mg',
            'dosage_form': 'Capsule',
            'unit': 'Capsules',
            'category': 'Antibiotic',
            'minimum_stock': 30,
            'reorder_level': 60
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_patch_medicine(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'brand_name': 'Hacked Brand'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.brand_name, 'Dolo 650')

    def test_doctor_cannot_delete_medicine(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MedicineMaster.objects.filter(id=self.medicine.id).exists())

    # 3. NURSE cannot mutate medicine master
    def test_nurse_cannot_create_medicine(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amoxicillin',
            'brand_name': 'Mox'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_nurse_cannot_patch_medicine(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'generic_name': 'Modified by Nurse'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_nurse_cannot_delete_medicine(self):
        self.client.force_authenticate(user=self.nurse)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 4. LAB_TECHNICIAN cannot mutate medicine master
    def test_lab_technician_cannot_create_medicine(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amoxicillin',
            'brand_name': 'Mox'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_lab_technician_cannot_patch_medicine(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'generic_name': 'Modified by Lab'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_lab_technician_cannot_delete_medicine(self):
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 5. PHARMACIST cannot mutate medicine master (read-only for medicine master)
    def test_pharmacist_cannot_create_medicine(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Metformin HCl',
            'brand_name': 'Glycomet',
            'strength': '500 mg',
            'dosage_form': 'Tablet',
            'unit': 'Tablets',
            'category': 'Anti-Diabetic',
            'minimum_stock': 50,
            'reorder_level': 100
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(MedicineMaster.objects.filter(generic_name='Metformin HCl').exists())

    def test_pharmacist_cannot_patch_medicine(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'brand_name': 'Calpol 650',
            'reorder_level': 150
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.brand_name, 'Dolo 650')

    def test_pharmacist_cannot_delete_medicine(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MedicineMaster.objects.filter(id=self.medicine.id).exists())

    # 6. Authorized role (HOSPITAL_ADMIN ONLY) can create, update, delete
    def test_hospital_admin_can_manage_medicine(self):
        self.client.force_authenticate(user=self.hospital_admin)
        # Create (POST -> 201)
        res_post = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'Amlodipine',
            'brand_name': 'Amlopres',
            'strength': '5 mg',
            'dosage_form': 'Tablet',
            'unit': 'Tablets',
            'category': 'Anti-Hypertensive',
            'minimum_stock': 20,
            'reorder_level': 40
        })
        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        med_id = res_post.data['id']
        self.assertTrue(MedicineMaster.objects.filter(id=med_id).exists())

        # Patch (PATCH -> 200)
        res_patch = self.client.patch(f'/api/pharmacy/medicines/{med_id}/', {
            'strength': '10 mg'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        med = MedicineMaster.objects.get(id=med_id)
        self.assertEqual(med.strength, '10 mg')

        # Delete (DELETE -> 204)
        res_del = self.client.delete(f'/api/pharmacy/medicines/{med_id}/')
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MedicineMaster.objects.filter(id=med_id).exists())

    # 7. Unauthorized role (DISTRICT_OFFICER) direct mutation is blocked
    def test_district_officer_cannot_mutate_medicine(self):
        self.client.force_authenticate(user=self.district_officer)
        res_post = self.client.post('/api/pharmacy/medicines/', {
            'generic_name': 'DO Medicine'
        })
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        res_patch = self.client.patch(f'/api/pharmacy/medicines/{self.medicine.id}/', {
            'generic_name': 'DO Mutated'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_delete = self.client.delete(f'/api/pharmacy/medicines/{self.medicine.id}/')
        self.assertEqual(res_delete.status_code, status.HTTP_403_FORBIDDEN)

    # 8. Permission mapping verification (create/update/delete exist ONLY for HOSPITAL_ADMIN)
    def test_medicine_master_permission_mapping(self):
        # View permission
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['DISTRICT_OFFICER'])
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['DOCTOR'])
        self.assertIn('medicine_master.view', ROLE_PERMISSIONS['PHARMACIST'])
        self.assertNotIn('medicine_master.view', ROLE_PERMISSIONS['NURSE'])
        self.assertNotIn('medicine_master.view', ROLE_PERMISSIONS['LAB_TECHNICIAN'])

        # Create/Update/Delete permissions exist ONLY for HOSPITAL_ADMIN
        for perm in ['medicine_master.create', 'medicine_master.update', 'medicine_master.delete']:
            self.assertIn(perm, ROLE_PERMISSIONS['HOSPITAL_ADMIN'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['PHARMACIST'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['DISTRICT_OFFICER'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['DOCTOR'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['NURSE'])
            self.assertNotIn(perm, ROLE_PERMISSIONS['LAB_TECHNICIAN'])

    # 8. Read access verification across roles
    def test_read_access_for_authorized_readers(self):
        for user in [self.doctor, self.pharmacist, self.hospital_admin, self.district_officer]:
            self.client.force_authenticate(user=user)
            res = self.client.get('/api/pharmacy/medicines/')
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"Failed for {user.role}")
            res_detail = self.client.get(f'/api/pharmacy/medicines/{self.medicine.id}/')
            self.assertEqual(res_detail.status_code, status.HTTP_200_OK, f"Detail failed for {user.role}")


from datetime import datetime, date, timedelta
from django.utils import timezone
from apps.pharmacy.models import MedicineBatch, Vendor, PurchaseOrder, PurchaseOrderItem, InventoryTransaction
from apps.pharmacy.views import InventoryTransactionSerializer
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem


class PharmacyReconciliationAndDataScopeTests(APITestCase):
    """
    Comprehensive test suite verifying data isolation, authoritative KPI reconciliation,
    facility scoping, and vendor/inventory/procurement accuracy across all 23 scenarios.
    """
    def setUp(self):
        # 1. Geography Setup
        self.state = State.objects.create(name='Karnataka', code='KA_PHARM')
        self.district1 = District.objects.create(name='District 1', code='D1', state=self.state)
        self.district2 = District.objects.create(name='District 2', code='D2', state=self.state)

        # 2. Facilities
        self.facility_a = Facility.objects.create(
            facility_code='FAC-PHARM-A',
            facility_name='Facility A (D1)',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district1
        )
        self.facility_b = Facility.objects.create(
            facility_code='FAC-PHARM-B',
            facility_name='Facility B (D1)',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district1
        )
        self.facility_c = Facility.objects.create(
            facility_code='FAC-PHARM-C',
            facility_name='Facility C (D2)',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district2
        )

        # 3. Users for Facility A
        self.pharmacist_a = User.objects.create_user(
            username='pharm_user_a',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility_a,
            full_name='Pharmacist Alice'
        )
        self.admin_a = User.objects.create_user(
            username='admin_user_a',
            password='password123',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.facility_a,
            full_name='Admin Alice'
        )
        self.doctor_a = User.objects.create_user(
            username='doctor_user_a',
            password='password123',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_a,
            full_name='Dr. Alice'
        )
        self.nurse_a = User.objects.create_user(
            username='nurse_user_a',
            password='password123',
            role=RoleChoices.NURSE,
            assigned_facility=self.facility_a,
            full_name='Nurse Alice'
        )
        self.lab_tech_a = User.objects.create_user(
            username='lab_tech_user_a',
            password='password123',
            role=RoleChoices.LAB_TECHNICIAN,
            assigned_facility=self.facility_a,
            full_name='Lab Tech Alice'
        )

        # Users for Facility B
        self.pharmacist_b = User.objects.create_user(
            username='pharm_user_b',
            password='password123',
            role=RoleChoices.PHARMACIST,
            assigned_facility=self.facility_b,
            full_name='Pharmacist Bob'
        )

        # District Officer for District 1
        self.district_officer_d1 = User.objects.create_user(
            username='do_d1_user',
            password='password123',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district1,
            full_name='DO District One'
        )

        # State Admin (Superuser)
        self.state_admin = User.objects.create_superuser(
            username='state_admin_user',
            password='password123',
            email='admin@state.gov.in',
            full_name='State Super Admin'
        )

        # 4. Medicines
        self.med_normal = MedicineMaster.objects.create(
            generic_name='Paracetamol Normal',
            brand_name='Dolo 500',
            strength='500 mg',
            dosage_form='Tablet',
            unit='Tablets',
            category='Analgesic',
            minimum_stock=50,
            reorder_level=100
        )
        self.med_low = MedicineMaster.objects.create(
            generic_name='Azithromycin Low',
            brand_name='Azi 500',
            strength='500 mg',
            dosage_form='Tablet',
            unit='Tablets',
            category='Antibiotic',
            minimum_stock=50,
            reorder_level=100
        )
        self.med_zero = MedicineMaster.objects.create(
            generic_name='Metformin Zero',
            brand_name='Glycomet 500',
            strength='500 mg',
            dosage_form='Tablet',
            unit='Tablets',
            category='Anti-Diabetic',
            minimum_stock=25,
            reorder_level=50
        )

        # 5. Batches
        future_date = date.today() + timedelta(days=400)
        self.batch_a = MedicineBatch.objects.create(
            facility=self.facility_a,
            medicine=self.med_normal,
            batch_number='BATCH-A-001',
            expiry_date=future_date,
            quantity=250,
            unit_cost=2.00,
            status='ACTIVE'
        )
        self.batch_b = MedicineBatch.objects.create(
            facility=self.facility_b,
            medicine=self.med_normal,
            batch_number='BATCH-B-001',
            expiry_date=future_date,
            quantity=180,
            unit_cost=2.00,
            status='ACTIVE'
        )
        self.batch_c = MedicineBatch.objects.create(
            facility=self.facility_c,
            medicine=self.med_normal,
            batch_number='BATCH-C-001',
            expiry_date=future_date,
            quantity=300,
            unit_cost=2.00,
            status='ACTIVE'
        )
        # Low stock batch for facility A (quantity 30 <= minimum_stock 50)
        self.batch_low_a = MedicineBatch.objects.create(
            facility=self.facility_a,
            medicine=self.med_low,
            batch_number='BATCH-LOW-A',
            expiry_date=future_date,
            quantity=30,
            unit_cost=10.00,
            status='ACTIVE'
        )
        # Out of stock batch for facility A (quantity 0)
        self.batch_zero_a = MedicineBatch.objects.create(
            facility=self.facility_a,
            medicine=self.med_zero,
            batch_number='BATCH-ZERO-A',
            expiry_date=future_date,
            quantity=0,
            unit_cost=3.00,
            status='EXHAUSTED'
        )

        # 6. Transactions
        self.tx_a = InventoryTransaction.objects.create(
            facility=self.facility_a,
            medicine=self.med_normal,
            batch=self.batch_a,
            transaction_type='PURCHASE_RECEIVED',
            quantity=250,
            reference_id='REF-TX-A1',
            created_by=self.pharmacist_a,
            notes='Initial stock'
        )
        self.tx_b = InventoryTransaction.objects.create(
            facility=self.facility_b,
            medicine=self.med_normal,
            batch=self.batch_b,
            transaction_type='PURCHASE_RECEIVED',
            quantity=180,
            reference_id='REF-TX-B1',
            created_by=self.pharmacist_b,
            notes='Initial stock for B'
        )
        self.tx_dispensed_today = InventoryTransaction.objects.create(
            facility=self.facility_a,
            medicine=self.med_normal,
            batch=self.batch_a,
            transaction_type='DISPENSED',
            quantity=-10,
            reference_id='DISP-TODAY-01',
            created_by=self.pharmacist_a,
            notes='Dispensed today'
        )

        # 7. Vendors
        self.central_vendor = Vendor.objects.create(
            vendor_name='KSMSCL Central Supplier',
            facility=None,
            status='ACTIVE'
        )
        self.vendor_a = Vendor.objects.create(
            vendor_name='Local Vendor Alpha',
            facility=self.facility_a,
            status='ACTIVE'
        )
        self.vendor_b = Vendor.objects.create(
            vendor_name='Local Vendor Beta',
            facility=self.facility_b,
            status='ACTIVE'
        )

        # 8. Purchase Orders
        self.po_a_draft = PurchaseOrder.objects.create(
            po_number='PO-A-DRAFT-01',
            vendor=self.vendor_a,
            facility=self.facility_a,
            status='DRAFT',
            total_amount=1000.00,
            created_by=self.pharmacist_a
        )
        self.po_a_pending = PurchaseOrder.objects.create(
            po_number='PO-A-PENDING-01',
            vendor=self.vendor_a,
            facility=self.facility_a,
            status='PENDING_APPROVAL',
            total_amount=2000.00,
            created_by=self.pharmacist_a
        )
        self.po_a_ordered = PurchaseOrder.objects.create(
            po_number='PO-A-ORDERED-01',
            vendor=self.central_vendor,
            facility=self.facility_a,
            status='ORDERED',
            total_amount=4000.00,
            created_by=self.pharmacist_a
        )
        self.po_a_received = PurchaseOrder.objects.create(
            po_number='PO-A-RECEIVED-01',
            vendor=self.central_vendor,
            facility=self.facility_a,
            status='RECEIVED',
            total_amount=6000.00,
            created_by=self.pharmacist_a
        )
        self.po_b_received = PurchaseOrder.objects.create(
            po_number='PO-B-RECEIVED-01',
            vendor=self.central_vendor,
            facility=self.facility_b,
            status='RECEIVED',
            total_amount=3000.00,
            created_by=self.pharmacist_b
        )

        # 9. Patients, Visits, Prescriptions
        self.patient_a = Patient.objects.create(
            patient_id='PAT-A-001',
            name='Patient Alpha',
            gender='MALE',
            mobile='9988776655',
            address='Bengaluru',
            registered_at_facility=self.facility_a,
            district=self.district1
        )
        self.visit_a = Visit.objects.create(
            visit_id='VISIT-A-001',
            patient=self.patient_a,
            facility=self.facility_a,
            status='WAITING_FOR_PHARMACY',
            current_queue='PHARMACY'
        )
        self.consultation_a = Consultation.objects.create(
            visit=self.visit_a,
            patient=self.patient_a,
            doctor=self.doctor_a,
            facility=self.facility_a,
            chief_complaint='Fever'
        )
        self.prescription_a = Prescription.objects.create(
            consultation=self.consultation_a,
            patient=self.patient_a,
            doctor=self.doctor_a,
            facility=self.facility_a,
            status='ACTIVE'
        )
        self.rx_item_a = PrescriptionItem.objects.create(
            prescription=self.prescription_a,
            medicine_name='Paracetamol Normal',
            quantity=10,
            status='PENDING'
        )

        self.patient_b = Patient.objects.create(
            patient_id='PAT-B-001',
            name='Patient Beta',
            gender='FEMALE',
            mobile='9988776644',
            address='Bengaluru',
            registered_at_facility=self.facility_b,
            district=self.district1
        )
        self.visit_b = Visit.objects.create(
            visit_id='VISIT-B-001',
            patient=self.patient_b,
            facility=self.facility_b,
            status='WAITING_FOR_PHARMACY',
            current_queue='PHARMACY'
        )
        self.consultation_b = Consultation.objects.create(
            visit=self.visit_b,
            patient=self.patient_b,
            doctor=self.doctor_a,
            facility=self.facility_b,
            chief_complaint='Cough'
        )
        self.prescription_b = Prescription.objects.create(
            consultation=self.consultation_b,
            patient=self.patient_b,
            doctor=self.doctor_a,
            facility=self.facility_b,
            status='ACTIVE'
        )

    # 1. Transaction serializer returns created_at as valid ISO timestamp
    def test_01_transaction_serializer_returns_created_at_as_iso_timestamp(self):
        serializer = InventoryTransactionSerializer(self.tx_a)
        created_at_val = serializer.data.get('created_at')
        self.assertIsNotNone(created_at_val)
        # Parse to ensure valid ISO-8601 string
        parsed = datetime.fromisoformat(created_at_val.replace('Z', '+00:00'))
        self.assertIsInstance(parsed, datetime)

        self.client.force_authenticate(user=self.pharmacist_a)
        res = self.client.get('/api/pharmacy/transactions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertTrue(len(results) > 0)
        self.assertIn('created_at', results[0])
        parsed_api = datetime.fromisoformat(results[0]['created_at'].replace('Z', '+00:00'))
        self.assertIsInstance(parsed_api, datetime)

    # 2. Transaction serializer returns performed_by_name matching the user who performed it
    def test_02_transaction_serializer_returns_performed_by_name(self):
        serializer = InventoryTransactionSerializer(self.tx_a)
        self.assertEqual(serializer.data.get('performed_by_name'), self.pharmacist_a.full_name)

        self.client.force_authenticate(user=self.pharmacist_a)
        res = self.client.get('/api/pharmacy/transactions/')
        results = res.data.get('results', res.data)
        tx_match = next((t for t in results if t['id'] == self.tx_a.id), None)
        self.assertIsNotNone(tx_match)
        self.assertEqual(tx_match['performed_by_name'], self.pharmacist_a.full_name)

    # 3. Facility A pharmacist cannot see Facility B transactions (even with ?facility=B)
    def test_03_facility_a_pharmacist_cannot_see_facility_b_transactions_even_with_param(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res = self.client.get(f'/api/pharmacy/transactions/?facility={self.facility_b.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        for t in results:
            self.assertEqual(t['facility'], self.facility_a.id)
            self.assertNotEqual(t['facility'], self.facility_b.id)

    # 4. Facility A hospital admin cannot see Facility B batches
    def test_04_facility_a_hospital_admin_cannot_see_facility_b_batches(self):
        self.client.force_authenticate(user=self.admin_a)
        res = self.client.get(f'/api/pharmacy/batches/?facility={self.facility_b.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        for b in results:
            self.assertEqual(b['facility'], self.facility_a.id)
            self.assertNotEqual(b['facility'], self.facility_b.id)

    # 5. Facility A doctor cannot see Facility B prescriptions
    def test_05_facility_a_doctor_cannot_see_facility_b_prescriptions(self):
        self.client.force_authenticate(user=self.doctor_a)
        res = self.client.get(f'/api/pharmacy/prescriptions/?facility={self.facility_b.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        for p in results:
            self.assertEqual(p['facility'], self.facility_a.id)
            self.assertNotEqual(p['facility'], self.facility_b.id)

    # 6. Facility A nurse cannot see Facility B purchase orders
    def test_06_facility_a_nurse_cannot_see_facility_b_purchase_orders(self):
        self.client.force_authenticate(user=self.nurse_a)
        res = self.client.get(f'/api/pharmacy/purchase-orders/?facility={self.facility_b.id}')
        if res.status_code == status.HTTP_200_OK:
            results = res.data.get('results', res.data)
            for po in results:
                self.assertNotEqual(po['facility'], self.facility_b.id)
        else:
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 7. Facility A lab tech cannot see Facility B stock alerts
    def test_07_facility_a_lab_tech_cannot_see_facility_b_stock_alerts(self):
        self.client.force_authenticate(user=self.lab_tech_a)
        res = self.client.get(f'/api/pharmacy/alerts/?facility={self.facility_b.id}')
        if res.status_code == status.HTTP_200_OK:
            for alt in res.data:
                self.assertNotEqual(alt.get('facility_id'), self.facility_b.id)
        else:
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 8. District Officer assigned to District 1 can see Facility A (in District 1)
    def test_08_district_officer_can_see_facility_a_in_assigned_district(self):
        self.client.force_authenticate(user=self.district_officer_d1)
        res = self.client.get(f'/api/pharmacy/batches/?facility={self.facility_a.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        fac_ids = {b['facility'] for b in results}
        self.assertIn(self.facility_a.id, fac_ids)

    # 9. District Officer assigned to District 1 CANNOT see Facility C (in District 2)
    def test_09_district_officer_cannot_see_facility_c_in_other_district(self):
        self.client.force_authenticate(user=self.district_officer_d1)
        res = self.client.get(f'/api/pharmacy/batches/?facility={self.facility_c.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        fac_ids = {b['facility'] for b in results}
        self.assertNotIn(self.facility_c.id, fac_ids)

    # 10. District Officer with no ?facility= sees aggregate across their district
    def test_10_district_officer_no_param_sees_district_aggregate(self):
        self.client.force_authenticate(user=self.district_officer_d1)
        res = self.client.get('/api/pharmacy/batches/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        fac_ids = {b['facility'] for b in results}
        self.assertNotIn(self.facility_c.id, fac_ids)
        self.assertTrue(fac_ids.issubset({self.facility_a.id, self.facility_b.id}))

    # 11. State admin can see across all facilities
    def test_11_state_admin_can_see_across_all_facilities(self):
        self.client.force_authenticate(user=self.state_admin)
        res = self.client.get('/api/pharmacy/batches/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        fac_ids = {b['facility'] for b in results}
        self.assertIn(self.facility_a.id, fac_ids)
        self.assertIn(self.facility_c.id, fac_ids)

    # 12. Vendor PO count is facility-scoped (Vendor V has 2 POs at Fac A, 1 at Fac B; Fac A sees 2)
    def test_12_vendor_po_count_is_facility_scoped(self):
        # Pharmacist A queries vendors
        self.client.force_authenticate(user=self.pharmacist_a)
        res_a = self.client.get('/api/pharmacy/vendors/')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        results_a = res_a.data.get('results', res_a.data)
        cv_a = next(v for v in results_a if v['id'] == self.central_vendor.id)
        self.assertEqual(cv_a['po_count'], 2)

        # Pharmacist B queries vendors
        self.client.force_authenticate(user=self.pharmacist_b)
        res_b = self.client.get('/api/pharmacy/vendors/')
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        results_b = res_b.data.get('results', res_b.data)
        cv_b = next(v for v in results_b if v['id'] == self.central_vendor.id)
        self.assertEqual(cv_b['po_count'], 1)

    # 13. Vendor spend is facility-scoped (Fac A sees only spend from Fac A POs)
    def test_13_vendor_spend_is_facility_scoped(self):
        # Fac A spend for central vendor: po_a_ordered (4000) + po_a_received (6000) = 10000.00
        self.client.force_authenticate(user=self.pharmacist_a)
        res_a = self.client.get('/api/pharmacy/vendors/')
        cv_a = next(v for v in res_a.data.get('results', res_a.data) if v['id'] == self.central_vendor.id)
        self.assertEqual(float(cv_a['total_spend']), 10000.00)

        # Fac B spend for central vendor: po_b_received (3000) = 3000.00
        self.client.force_authenticate(user=self.pharmacist_b)
        res_b = self.client.get('/api/pharmacy/vendors/')
        cv_b = next(v for v in res_b.data.get('results', res_b.data) if v['id'] == self.central_vendor.id)
        self.assertEqual(float(cv_b['total_spend']), 3000.00)

    # 14. Vendor with facility=None (central) is visible to all facilities
    def test_14_vendor_with_facility_none_visible_to_all(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res_a = self.client.get('/api/pharmacy/vendors/')
        ids_a = [v['id'] for v in res_a.data.get('results', res_a.data)]
        self.assertIn(self.central_vendor.id, ids_a)

        self.client.force_authenticate(user=self.pharmacist_b)
        res_b = self.client.get('/api/pharmacy/vendors/')
        ids_b = [v['id'] for v in res_b.data.get('results', res_b.data)]
        self.assertIn(self.central_vendor.id, ids_b)

    # 15. Vendor with facility=A is NOT visible to Facility B
    def test_15_vendor_with_facility_a_not_visible_to_facility_b(self):
        self.client.force_authenticate(user=self.pharmacist_b)
        res_b = self.client.get('/api/pharmacy/vendors/')
        ids_b = [v['id'] for v in res_b.data.get('results', res_b.data)]
        self.assertNotIn(self.vendor_a.id, ids_b)

    # 16. Prescriptions pending count on dashboard matches queue count for same facility
    def test_16_prescriptions_pending_count_matches_queue(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res_dash = self.client.get('/api/pharmacy/dashboard/')
        self.assertEqual(res_dash.status_code, status.HTTP_200_OK)
        pending_count = res_dash.data.get('pending_prescriptions_count')

        res_q = self.client.get(f'/api/pharmacy/prescriptions/?facility={self.facility_a.id}')
        q_results = [p for p in res_q.data.get('results', res_q.data) if p['status'] in ['ACTIVE', 'PENDING', 'PARTIALLY_DISPENSED']]
        self.assertEqual(pending_count, len(q_results))

    # 17. PO KPI draft count matches purchase_orders/?status=DRAFT count
    def test_17_po_kpi_draft_count_matches_status_draft(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res_kpi = self.client.get('/api/pharmacy/purchase-orders/procurement_summary/')
        self.assertEqual(res_kpi.status_code, status.HTTP_200_OK)
        draft_kpi = res_kpi.data.get('draft', 0)

        res_list = self.client.get('/api/pharmacy/purchase-orders/?status=DRAFT')
        list_count = res_list.data.get('count', len(res_list.data.get('results', res_list.data)))
        self.assertEqual(draft_kpi, list_count)

    # 18. PO KPI pending_approval count matches purchase_orders/?status=PENDING_APPROVAL count
    def test_18_po_kpi_pending_approval_matches_status_pending(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res_kpi = self.client.get('/api/pharmacy/purchase-orders/procurement_summary/')
        self.assertEqual(res_kpi.status_code, status.HTTP_200_OK)
        pending_kpi = res_kpi.data.get('pending_approval', 0)

        res_list = self.client.get('/api/pharmacy/purchase-orders/?status=PENDING_APPROVAL')
        list_count = res_list.data.get('count', len(res_list.data.get('results', res_list.data)))
        self.assertEqual(pending_kpi, list_count)

    # 19. PO KPI ordered count matches purchase_orders/?status=ORDERED count
    def test_19_po_kpi_ordered_matches_status_ordered(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res_kpi = self.client.get('/api/pharmacy/purchase-orders/procurement_summary/')
        self.assertEqual(res_kpi.status_code, status.HTTP_200_OK)
        ordered_kpi = res_kpi.data.get('ordered', 0)

        res_list = self.client.get('/api/pharmacy/purchase-orders/?status=ORDERED')
        list_count = res_list.data.get('count', len(res_list.data.get('results', res_list.data)))
        self.assertEqual(ordered_kpi, list_count)

    # 20. PO KPI received count matches purchase_orders/?status=RECEIVED count
    def test_20_po_kpi_received_matches_status_received(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res_kpi = self.client.get('/api/pharmacy/purchase-orders/procurement_summary/')
        self.assertEqual(res_kpi.status_code, status.HTTP_200_OK)
        received_kpi = res_kpi.data.get('received', 0)

        res_list = self.client.get('/api/pharmacy/purchase-orders/?status=RECEIVED')
        list_count = res_list.data.get('count', len(res_list.data.get('results', res_list.data)))
        self.assertEqual(received_kpi, list_count)

    # 21. Medicine with stock <= minimum_stock appears in alerts as LOW_STOCK
    def test_21_medicine_with_stock_le_minimum_appears_in_alerts_as_low_stock(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res = self.client.get('/api/pharmacy/alerts/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        low_alert = next((a for a in res.data if a.get('medicine_id') == self.med_low.id), None)
        self.assertIsNotNone(low_alert)
        self.assertIn(low_alert.get('alert_type', low_alert.get('type')), ['LOW_STOCK', 'REORDER_LEVEL'])

    # 22. Medicine with stock == 0 appears in alerts as OUT_OF_STOCK
    def test_22_medicine_with_stock_zero_appears_in_alerts_as_out_of_stock(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res = self.client.get('/api/pharmacy/alerts/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        zero_alert = next((a for a in res.data if a.get('medicine_id') == self.med_zero.id), None)
        self.assertIsNotNone(zero_alert)
        self.assertEqual(zero_alert.get('alert_type', zero_alert.get('type')), 'OUT_OF_STOCK')

    # 23. Dispensed transactions today count matches report dispensing count
    def test_23_dispensed_transactions_today_matches_report(self):
        self.client.force_authenticate(user=self.pharmacist_a)
        res_rep = self.client.get('/api/pharmacy/reports/')
        self.assertEqual(res_rep.status_code, status.HTTP_200_OK)
        disp_today_rep = res_rep.data.get('dispensed_today', 0)

        today = timezone.localdate()
        tx_count = InventoryTransaction.objects.filter(
            facility=self.facility_a,
            transaction_type='DISPENSED',
            created_at__date=today
        ).count()
        self.assertEqual(disp_today_rep, tx_count)

