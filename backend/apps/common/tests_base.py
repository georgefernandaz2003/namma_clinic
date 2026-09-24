import datetime
from django.test import TestCase
from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation

class DomainServiceBaseTestCase(TestCase):
    """
    Unified base test case providing standard geography, facilities,
    active and suspended staff profiles, roles, patients, and encounters.
    """
    def setUp(self):
        # 1. Geography
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.taluk = Taluk.objects.create(name="Bengaluru East", code="TAL-BLR-E", district=self.district)
        self.zone = Zone.objects.create(name="Mahadevapura Zone", district=self.district)
        self.ward = Ward.objects.create(name="Varthur", ward_number=149, zone=self.zone)

        # 2. Facilities & Departments
        self.clinic_a = Facility.objects.create(
            facility_code="PHC-VARTHUR", facility_name="Varthur Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district, state=self.state,
            zone=self.zone, ward=self.ward
        )
        self.clinic_b = Facility.objects.create(
            facility_code="PHC-WHITEFIELD", facility_name="Whitefield Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district, state=self.state,
            zone=self.zone, ward=self.ward
        )
        self.dept_opd = Department.objects.create(facility=self.clinic_a, code="OPD", name="Outpatient")
        self.dept_lab = Department.objects.create(facility=self.clinic_a, code="LAB", name="Laboratory")

        # 3. Roles
        self.role_admin = RoleMaster.objects.create(code="ADMIN", name="Facility Administrator")
        self.role_doc = RoleMaster.objects.create(code="DOCTOR", name="Medical Officer")
        self.role_nurse = RoleMaster.objects.create(code="NURSE", name="Staff Nurse")

        # 4. Staff Profiles
        self.person_admin = Person.objects.create(
            first_name="Admin", last_name="User", gender="MALE",
            date_of_birth=datetime.date(1975, 1, 1), phone_number="9800099999"
        )
        self.admin_staff = StaffProfile.objects.create(
            person=self.person_admin, employee_id="ADM-001", designation="Hospital Administrator",
            department=self.dept_opd, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(
            staff=self.admin_staff, role=self.role_admin, effective_from=datetime.date(2026, 1, 1), is_active=True
        )

        self.person_doc = Person.objects.create(
            first_name="Anil", last_name="Sharma", gender="MALE",
            date_of_birth=datetime.date(1980, 1, 1), phone_number="9800011111"
        )
        self.doc_staff = StaffProfile.objects.create(
            person=self.person_doc, employee_id="DOC-001", designation="Medical Officer",
            department=self.dept_opd, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(
            staff=self.doc_staff, role=self.role_doc, effective_from=datetime.date(2026, 1, 1), is_active=True
        )

        self.person_nurse = Person.objects.create(
            first_name="Deepa", last_name="Rao", gender="FEMALE",
            date_of_birth=datetime.date(1990, 2, 2), phone_number="9800022222"
        )
        self.nurse_staff = StaffProfile.objects.create(
            person=self.person_nurse, employee_id="NUR-001", designation="Staff Nurse",
            department=self.dept_opd, status="ACTIVE"
        )

        self.suspended_staff = StaffProfile.objects.create(
            person=self.person_nurse, employee_id="SUSP-001", designation="Staff Nurse",
            department=self.dept_opd, status="SUSPENDED"
        )

        # 5. Patients
        self.patient = Patient.objects.create(
            patient_id="PAT-001", person=self.person_doc, name="Raju G",
            age=35, gender="MALE", mobile="9800033333", address="Varthur Main Rd",
            registered_at_facility=self.clinic_a
        )
        self.patient2 = Patient.objects.create(
            patient_id="PAT-002", person=self.person_nurse, name="Meena S",
            age=28, gender="FEMALE", mobile="9800044444", address="Whitefield Main Rd",
            registered_at_facility=self.clinic_b
        )

        # 6. Visits
        self.visit = Visit.objects.create(
            visit_id="VIS-001", patient=self.patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), current_queue="DOCTOR", status="IN_CONSULTATION"
        )
        self.completed_visit = Visit.objects.create(
            visit_id="VIS-COMP-001", patient=self.patient, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), current_queue="PHARMACY", status="COMPLETED"
        )
        self.consultation = Consultation.objects.create(
            visit=self.visit, patient=self.patient, facility=self.clinic_a,
            doctor_staff=self.doc_staff, consultation_sequence=1, chief_complaint="Fever"
        )
