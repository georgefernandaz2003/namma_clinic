from django.test import TestCase


class PharmacyHardeningTestCase(TestCase):
    def test_all_52_pharmacy_hardening_tests(self):
        import test_pharmacy_hardening
        exit_code = test_pharmacy_hardening.run_tests()
        self.assertEqual(exit_code, 0, "All 52 pharmacy hardening tests must pass.")

    def test_procurement_lifecycle_tests(self):
        import test_pharmacy_procurement
        exit_code = test_pharmacy_procurement.run_procurement_tests()
        self.assertEqual(exit_code, 0, "All 23 procurement lifecycle assertions across 18 scenarios must pass.")
