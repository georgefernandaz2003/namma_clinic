"""
Visits Domain Service Tests (apps/visits/tests_services.py).
Tests OPD and LAB token allocation, namespace isolation, and monotonic sequence.
"""
import datetime
from apps.common.tests_base import DomainServiceBaseTestCase
from apps.laboratory.models import DiagnosticOrder
from apps.visits.services import issue_opd_token, issue_lab_token
from apps.visits.models import FacilityDailyCounter

class TokenDomainServiceTests(DomainServiceBaseTestCase):
    def test_token_namespaces_and_counter_isolation(self):
        today = datetime.date.today()
        opd_token = issue_opd_token(visit=self.visit, facility=self.clinic_a, token_date=today)
        self.assertEqual(opd_token.token_number, 1)

        diag_order = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff,
            order_number="ORD-TOK-001", order_date=today
        )
        lab_token_no = issue_lab_token(diagnostic_order=diag_order, facility=self.clinic_a, order_date=today)
        self.assertEqual(lab_token_no, 1)
        self.assertEqual(diag_order.lab_token_number, 1)

        counter_opd = FacilityDailyCounter.objects.get(facility=self.clinic_a, counter_type="OPD", counter_date=today)
        counter_lab = FacilityDailyCounter.objects.get(facility=self.clinic_a, counter_type="LAB", counter_date=today)
        self.assertEqual(counter_opd.last_token_number, 1)
        self.assertEqual(counter_lab.last_token_number, 1)
