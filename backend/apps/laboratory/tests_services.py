"""
Laboratory Domain Service Tests (apps/laboratory/tests_services.py).
Tests orders, test requests, specimen sharing, 1:1 result lock, verified immutability,
and unauthorized verification failure.
"""
import datetime
from apps.common.tests_base import DomainServiceBaseTestCase
from apps.laboratory.models import DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest, DiagnosticResult
from apps.laboratory.services import (
    create_diagnostic_order, create_test_request, collect_specimen,
    record_diagnostic_result, verify_diagnostic_result, amend_diagnostic_result
)
from apps.common.exceptions import (
    UnauthorizedDomainAction, DiagnosticResultAlreadyExistsError, VerifiedResultImmutableError
)

class LaboratoryDomainServiceTests(DomainServiceBaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_cbc = DiagnosticTestMaster.objects.create(test_code="CBC", test_name="Complete Blood Count", specimen_type="WHOLE_BLOOD")
        self.test_esr = DiagnosticTestMaster.objects.create(test_code="ESR", test_name="Erythrocyte Sedimentation Rate", specimen_type="WHOLE_BLOOD")

    def test_diagnostic_order_multiple_requests_and_shared_specimen(self):
        order = create_diagnostic_order(self.visit, self.clinic_a, self.doc_staff)
        req_cbc = create_test_request(order, self.test_cbc)
        req_esr = create_test_request(order, self.test_esr)

        specimen = collect_specimen(order, "BARCODE-MULTI-01", "WHOLE_BLOOD", self.doc_staff, test_requests=[req_cbc, req_esr])
        req_cbc.refresh_from_db()
        req_esr.refresh_from_db()
        self.assertEqual(req_cbc.specimen, specimen)
        self.assertEqual(req_esr.specimen, specimen)

    def test_diagnostic_result_uniqueness_and_verification(self):
        order = create_diagnostic_order(self.visit, self.clinic_a, self.doc_staff)
        req = create_test_request(order, self.test_cbc)

        res = record_diagnostic_result(req, entered_by_staff=self.doc_staff, result_value_text="14.2 g/dL")
        with self.assertRaises(DiagnosticResultAlreadyExistsError):
            record_diagnostic_result(req, entered_by_staff=self.doc_staff, result_value_text="15.0 g/dL")

        verified = verify_diagnostic_result(res, verified_by_staff=self.doc_staff)
        self.assertEqual(verified.status, "VERIFIED")

        # Failure 9: re-verification raises VerifiedResultImmutableError
        with self.assertRaises(VerifiedResultImmutableError):
            verify_diagnostic_result(verified, verified_by_staff=self.doc_staff)

    def test_unauthorized_diagnostic_verification_inactive_actor(self):
        """Failure 3: Inactive staff cannot verify diagnostic results."""
        order = create_diagnostic_order(self.visit, self.clinic_a, self.doc_staff)
        req = create_test_request(order, self.test_cbc)
        res = record_diagnostic_result(req, entered_by_staff=self.doc_staff, result_value_text="12.0 g/dL")

        with self.assertRaises(UnauthorizedDomainAction):
            verify_diagnostic_result(res, verified_by_staff=self.suspended_staff)

    def test_amend_verified_diagnostic_result(self):
        order = create_diagnostic_order(self.visit, self.clinic_a, self.doc_staff)
        req = create_test_request(order, self.test_cbc)
        res = record_diagnostic_result(req, entered_by_staff=self.doc_staff, result_value_text="10.5 g/dL")
        verify_diagnostic_result(res, verified_by_staff=self.doc_staff)

        amended_res, amendment = amend_diagnostic_result(
            res, amended_by_staff=self.doc_staff, amendment_reason="Dilution factor correction", amended_value_text="11.2 g/dL"
        )
        self.assertEqual(amended_res.status, "AMENDED")
        self.assertEqual(amendment.previous_value_text, "10.5 g/dL")
        self.assertEqual(amendment.amended_value_text, "11.2 g/dL")
