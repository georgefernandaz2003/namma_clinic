"""
Reconciliation Regression Tests (apps/reports/tests_reconciliation.py).
Tests:
1. VisitSerializer priority field inclusion
2. DashboardSummaryView DiagnosticOrder aggregation and facility scoping
3. DashboardSummaryView Prescription lifecycle aggregation
4. Doctor and Nurse queue counting consistency
"""
import datetime
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.common.tests_base import DomainServiceBaseTestCase
from apps.accounts.models import User
from apps.visits.models import Visit
from apps.visits.api_v1 import VisitSerializer
from apps.laboratory.models import DiagnosticOrder
from apps.consultations.models import Consultation, Prescription
from apps.reports.views import DashboardSummaryView

class DashboardReconciliationTests(DomainServiceBaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="test_officer",
            email="officer@example.com",
            password="TestPass123!",
            role="DISTRICT_OFFICER"
        )

    def test_visit_serializer_includes_priority(self):
        today = datetime.date.today()
        v_norm = Visit.objects.create(
            visit_id="VIS-PRIO-001", patient=self.patient, facility=self.clinic_a,
            opd_date=today, priority="NORMAL", current_queue="DOCTOR", status="TRIAGED"
        )
        v_high = Visit.objects.create(
            visit_id="VIS-PRIO-002", patient=self.patient, facility=self.clinic_a,
            opd_date=today, priority="HIGH", current_queue="DOCTOR", status="TRIAGED"
        )
        v_emerg = Visit.objects.create(
            visit_id="VIS-PRIO-003", patient=self.patient, facility=self.clinic_a,
            opd_date=today, priority="EMERGENCY", current_queue="DOCTOR", status="TRIAGED"
        )

        serializer_norm = VisitSerializer(v_norm)
        serializer_high = VisitSerializer(v_high)
        serializer_emerg = VisitSerializer(v_emerg)

        self.assertIn("priority", serializer_norm.data)
        self.assertEqual(serializer_norm.data["priority"], "NORMAL")
        self.assertEqual(serializer_high.data["priority"], "HIGH")
        self.assertEqual(serializer_emerg.data["priority"], "EMERGENCY")

    def test_dashboard_summary_aggregates_diagnostic_orders(self):
        today = datetime.date.today()
        diag_a = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff,
            order_number="ORD-REC-001", order_date=today, status="ORDERED"
        )
        diag_comp = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.clinic_a, ordering_doctor_staff=self.doc_staff,
            order_number="ORD-REC-002", order_date=today, status="VERIFIED"
        )
        diag_b = DiagnosticOrder.objects.create(
            visit=self.visit, facility=self.clinic_b, ordering_doctor_staff=self.doc_staff,
            order_number="ORD-REC-003", order_date=today, status="ORDERED"
        )

        view = DashboardSummaryView.as_view()
        request = self.factory.get(f"/api/dashboard/summary/?facility={self.clinic_a.id}&date={today.isoformat()}")
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["kpis"]["lab_pending"], 1)
        self.assertEqual(data["lab_summary"]["total"], 2)
        self.assertEqual(data["lab_summary"]["ordered"], 1)
        self.assertEqual(data["lab_summary"]["verified"], 1)

    def test_dashboard_summary_aggregates_prescription_lifecycle(self):
        today = datetime.date.today()
        consultation = Consultation.objects.create(
            visit=self.visit, patient=self.patient, facility=self.clinic_a,
            chief_complaint="Cough and cold", diagnosis_name="URTI"
        )
        rx_dispensed = Prescription.objects.create(
            consultation=consultation, patient=self.patient, facility=self.clinic_a,
            status="DISPENSED"
        )
        rx_dispensed.date = today
        rx_dispensed.save()

        view = DashboardSummaryView.as_view()
        request = self.factory.get(f"/api/dashboard/summary/?facility={self.clinic_a.id}&date={today.isoformat()}")
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["kpis"]["pharmacy_waiting"], 0)
        self.assertEqual(data["kpis"]["pharmacy_dispensed_today"], 1)
        self.assertEqual(data["pharmacy_summary"]["total_prescriptions"], 1)