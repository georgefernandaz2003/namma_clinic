import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DATABASE_ENGINE'] = 'postgresql'
django.setup()

from django.db import transaction, connection
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, VisitStatusHistory, FacilityDailyCounter
from apps.triage.models import TriageVitals, Triage
from apps.consultations.models import Consultation, Prescription, PrescriptionItem, Diagnosis
from apps.laboratory.models import (
    DiagnosticOrder, Specimen, TestRequest, DiagnosticResult, DiagnosticResultAmendment,
    LabOrder, LabSample, LabResult, LabToken
)
from apps.pharmacy.models import (
    MedicineBatch, Dispensation, DispensationItem, InventoryLedger,
    DispensationReturn, PatientCounselling, BatchRecall
)
from apps.referrals.models import (
    Referral, ReferralResponse, ReferralOrder, ReferralEvent,
    FollowUp, FollowUpTask
)
from apps.ncd.models import NCDRecord, NCDCondition, NCDAssessment
from apps.surveillance.models import DiseaseCase, DiseaseSurveillanceCase, PublicHealthNotification
from apps.outreach.models import OutreachActivity
from apps.wellness.models import WellnessSession
from apps.quality.models import BiomedicalWasteLog
from apps.alerts.models import Alert
from apps.audit.models import AuditLog, AuditLogEntry
from apps.accounts.models import User, StaffProfile
from apps.facilities.models import Facility
from apps.pharmacy.models import MedicineMaster
from apps.laboratory.models import DiagnosticTestMaster

def flush_all_generated_data():
    print("======================================================================")
    print("NAMMA CLINIC — COMPLETE OPERATIONAL DATA FLUSH (SCRATCH CLEAN-SLATE)")
    print("======================================================================")

    with transaction.atomic():
        # 1. Quality & Community Logs
        print("Flushing quality & community logs...")
        BiomedicalWasteLog.objects.all().delete()
        OutreachActivity.objects.all().delete()
        WellnessSession.objects.all().delete()

        # 2. Disease Surveillance
        print("Flushing disease surveillance...")
        PublicHealthNotification.objects.all().delete()
        DiseaseSurveillanceCase.objects.all().delete()
        DiseaseCase.objects.all().delete()

        # 3. NCD Registry
        print("Flushing NCD records & longitudinal assessments...")
        NCDAssessment.objects.all().delete()
        NCDCondition.objects.all().delete()
        NCDRecord.objects.all().delete()

        # 4. Care Continuity & Referrals
        print("Flushing referrals & follow-ups...")
        FollowUpTask.objects.all().delete()
        FollowUp.objects.all().delete()
        ReferralEvent.objects.all().delete()
        ReferralOrder.objects.all().delete()
        ReferralResponse.objects.all().delete()
        Referral.objects.all().delete()

        # 5. Pharmacy Dispensations & Ledger Reversal
        print("Flushing pharmacy dispensations...")
        DispensationItem.objects.all().delete()
        Dispensation.objects.all().delete()
        DispensationReturn.objects.all().delete()
        PatientCounselling.objects.all().delete()
        BatchRecall.objects.all().delete()

        print("Resetting InventoryLedger to initial purchase receipts...")
        # Remove all DISPENSE transactions
        InventoryLedger.objects.filter(transaction_type='DISPENSE').delete()
        
        # Reset each batch's available_quantity back to its purchase receipt quantity
        for b in MedicineBatch.objects.all():
            receipt = InventoryLedger.objects.filter(batch=b, transaction_type='PURCHASE_RECEIPT').first()
            if receipt:
                b.available_quantity = receipt.quantity_delta
                b.quantity = receipt.quantity_delta
            else:
                b.available_quantity = 500
                b.quantity = 500
            b.save()

        # 6. Laboratory Transactions & Results
        print("Flushing laboratory orders, tokens & results...")
        DiagnosticResult.objects.all().delete()
        TestRequest.objects.all().delete()
        Specimen.objects.all().delete()
        DiagnosticOrder.objects.all().delete()

        DiagnosticResultAmendment.objects.all().delete()
        LabResult.objects.all().delete()
        LabSample.objects.all().delete()
        LabOrder.objects.all().delete()
        LabToken.objects.all().delete()

        # 7. Consultations & Prescriptions
        print("Flushing consultations, diagnoses & prescriptions...")
        PrescriptionItem.objects.all().delete()
        Prescription.objects.all().delete()
        Diagnosis.objects.all().delete()
        Consultation.objects.all().delete()

        # 8. Triage
        print("Flushing triage vitals...")
        TriageVitals.objects.all().delete()
        Triage.objects.all().delete()

        # 9. Visits & Tokens
        print("Flushing visits, tokens & status history...")
        Token.objects.all().delete()
        VisitStatusHistory.objects.all().delete()
        Visit.objects.all().delete()
        FacilityDailyCounter.objects.all().delete()

        # 10. Patients
        print("Flushing patients master table...")
        Patient.objects.all().delete()

        # 11. Alerts & Audit Logs
        print("Flushing operational alerts & audit logs...")
        Alert.objects.all().delete()
        AuditLog.objects.all().delete()
        AuditLogEntry.objects.all().delete()

    print("\n----------------------------------------------------------------------")
    print("VERIFICATION OF CLEAN-SLATE POST-FLUSH STATE:")
    print("----------------------------------------------------------------------")
    print(f"  Patients count:               {Patient.objects.count()} (MUST BE 0)")
    print(f"  Visits count:                 {Visit.objects.count()} (MUST BE 0)")
    print(f"  Tokens count:                 {Token.objects.count()} (MUST BE 0)")
    print(f"  Triage count:                 {TriageVitals.objects.count()} (MUST BE 0)")
    print(f"  Consultations count:          {Consultation.objects.count()} (MUST BE 0)")
    print(f"  Prescriptions count:          {Prescription.objects.count()} (MUST BE 0)")
    print(f"  Diagnostic Orders count:      {DiagnosticOrder.objects.count()} (MUST BE 0)")
    print(f"  Dispensations count:          {Dispensation.objects.count()} (MUST BE 0)")
    print(f"  Follow-ups count:             {FollowUp.objects.count()} (MUST BE 0)")
    print(f"  NCD Records count:            {NCDRecord.objects.count()} (MUST BE 0)")
    print(f"  Surveillance cases count:     {DiseaseSurveillanceCase.objects.count()} (MUST BE 0)")
    print(f"  Audit logs count:             {AuditLog.objects.count()} (MUST BE 0)")
    print("\nVERIFICATION OF PRESERVED MASTER INFRASTRUCTURE:")
    print(f"  Facilities count:             {Facility.objects.count()} (Expected: 7)")
    print(f"  Staff Users count:            {User.objects.count()} (Expected: 39)")
    print(f"  Medicine Masters count:       {MedicineMaster.objects.count()} (Expected: 14)")
    print(f"  Diagnostic Test Masters count:{DiagnosticTestMaster.objects.count()} (Expected: 14)")
    print(f"  Medicine Batches in stock:    {MedicineBatch.objects.count()} (Expected: 24)")

    assert Patient.objects.count() == 0, "Patient count is not 0!"
    assert Visit.objects.count() == 0, "Visit count is not 0!"
    assert Consultation.objects.count() == 0, "Consultation count is not 0!"
    assert Facility.objects.count() >= 7, "Facilities missing!"
    assert User.objects.count() >= 39, "Staff users missing!"

    print("\nSUCCESS: All generated operational data has been flushed cleanly to 0!")
    print("The system is now completely empty and ready to be used from scratch!")

if __name__ == '__main__':
    flush_all_generated_data()
