from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from apps.patients.models import Patient, Household, PatientDocument
from apps.visits.models import Visit, Token, VisitStatusHistory
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import LabOrder, LabSample, LabResult
from apps.referrals.models import Referral, ReferralResponse, FollowUp
from apps.ncd.models import NCDRecord
from apps.surveillance.models import DiseaseCase
from apps.telemedicine.models import Teleconsultation
from apps.alerts.models import Alert
from apps.pharmacy.models import InventoryTransaction


class Command(BaseCommand):
    help = "Safely clear all patients, visits, triage vitals, consultations, lab orders, and related clinical data while preserving staff logins, facilities, and inventory catalog."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Clearing all patient clinical data, visits, and queues..."))

        patient_alerts_q = Q(patient__isnull=False) | Q(alert_type__in=['REFERRAL_OVERDUE', 'FOLLOWUP_OVERDUE', 'LAB_PENDING', 'HIGH_RISK_FOLLOWUP', 'DISEASE_THRESHOLD'])

        counts = {
            'Prescription Items': PrescriptionItem.objects.count(),
            'Prescriptions': Prescription.objects.count(),
            'Consultations': Consultation.objects.count(),
            'Lab Results': LabResult.objects.count(),
            'Lab Samples': LabSample.objects.count(),
            'Lab Orders': LabOrder.objects.count(),
            'Triage Vitals': TriageVitals.objects.count(),
            'Visit Status History': VisitStatusHistory.objects.count(),
            'Tokens': Token.objects.count(),
            'Visits': Visit.objects.count(),
            'Patient Documents': PatientDocument.objects.count(),
            'FollowUps': FollowUp.objects.count(),
            'Referral Responses': ReferralResponse.objects.count(),
            'Referrals': Referral.objects.count(),
            'NCD Records': NCDRecord.objects.count(),
            'Disease Cases': DiseaseCase.objects.count(),
            'Teleconsultations': Teleconsultation.objects.count(),
            'Patients': Patient.objects.count(),
            'Households': Household.objects.count(),
            'Patient Alerts': Alert.objects.filter(patient_alerts_q).count(),
            'Dispensed Transactions': InventoryTransaction.objects.filter(transaction_type='DISPENSED').count(),
        }

        # Clear clinical child models first, then visits and patients
        PrescriptionItem.objects.all().delete()
        Prescription.objects.all().delete()
        Consultation.objects.all().delete()
        LabResult.objects.all().delete()
        LabSample.objects.all().delete()
        LabOrder.objects.all().delete()
        TriageVitals.objects.all().delete()
        VisitStatusHistory.objects.all().delete()
        Token.objects.all().delete()
        FollowUp.objects.all().delete()
        ReferralResponse.objects.all().delete()
        Referral.objects.all().delete()
        NCDRecord.objects.all().delete()
        DiseaseCase.objects.all().delete()
        Teleconsultation.objects.all().delete()
        Visit.objects.all().delete()
        PatientDocument.objects.all().delete()
        Patient.objects.all().delete()
        Household.objects.all().delete()
        Alert.objects.filter(patient_alerts_q).delete()
        InventoryTransaction.objects.filter(transaction_type='DISPENSED').delete()

        self.stdout.write(self.style.SUCCESS("Successfully cleared all patient and visit data!"))
        for k, v in counts.items():
            self.stdout.write(f"  - Deleted {v} {k}")
