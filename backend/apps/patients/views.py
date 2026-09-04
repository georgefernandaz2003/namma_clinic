from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.patients.models import Patient, Household
from apps.patients.serializers import PatientSerializer, HouseholdSerializer
from apps.visits.models import Visit
from apps.triage.models import TriageVitals
from apps.consultations.models import Consultation, Prescription
from apps.laboratory.models import LabOrder
from apps.referrals.models import Referral, FollowUp

from apps.accounts.permissions import get_accessible_facility_ids_for_user

class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Patient.objects.all().select_related('ward', 'district', 'registered_at_facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            # Patients registered at accessible facility or having visits at accessible facility
            queryset = queryset.filter(registered_at_facility_id__in=accessible_ids)
        return queryset

    def create(self, request, *args, **kwargs):
        # Duplicate check by name & mobile
        mobile = request.data.get('mobile')
        name = request.data.get('name')
        if mobile and name:
            existing = Patient.objects.filter(mobile=mobile, name__iexact=name).first()
            if existing:
                return Response(
                    {'error': 'Duplicate patient record detected!', 'patient': PatientSerializer(existing).data},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return super().create(request, *args, **kwargs)

class PatientTimelineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=44)

        timeline = []

        # 1. Registration event
        timeline.append({
            'date': patient.registration_date.strftime('%Y-%m-%d'),
            'type': 'REGISTRATION',
            'title': 'Patient Registered',
            'facility': patient.registered_at_facility.facility_name if patient.registered_at_facility else 'Namma Clinic',
            'details': f"Registered with Patient ID {patient.patient_id}, Mobile: {patient.mobile}, ABHA: {patient.ABHA_ID_DEMO or 'N/A'}"
        })

        # 2. Visits & Clinical events
        visits = Visit.objects.filter(patient=patient).order_by('visit_date')
        for v in visits:
            v_date = v.visit_date.strftime('%Y-%m-%d %H:%M')
            timeline.append({
                'date': v_date,
                'type': 'VISIT',
                'title': f"Clinic Visit (#{v.token.token_number if hasattr(v, 'token') else v.id})",
                'facility': v.facility.facility_name,
                'details': f"Visit Type: {v.visit_type}, Chief Complaint: {v.chief_complaint or 'General Checkup'}"
            })

            if hasattr(v, 'triage'):
                tr = v.triage
                timeline.append({
                    'date': tr.created_at.strftime('%Y-%m-%d %H:%M'),
                    'type': 'TRIAGE',
                    'title': 'Nurse Triage Vitals Captured',
                    'facility': v.facility.facility_name,
                    'details': f"BP: {tr.blood_pressure_systolic}/{tr.blood_pressure_diastolic} mmHg, Pulse: {tr.pulse_bpm} bpm, Temp: {tr.temperature_f}°F, SpO2: {tr.spo2_percent}%, Glucose: {tr.blood_glucose_mgdl} mg/dL"
                })

            if hasattr(v, 'consultation'):
                c = v.consultation
                timeline.append({
                    'date': c.created_at.strftime('%Y-%m-%d %H:%M'),
                    'type': 'CONSULTATION',
                    'title': f"Doctor Consultation - {c.diagnosis_name}",
                    'facility': v.facility.facility_name,
                    'details': f"Doctor: {c.doctor.full_name if c.doctor else 'Medical Officer'}. Diagnosis: [{c.diagnosis_code}] {c.diagnosis_name}. Notes: {c.clinical_notes}"
                })

                if hasattr(c, 'prescription'):
                    p = c.prescription
                    meds = ", ".join([f"{item.medicine_name} ({item.dosage})" for item in p.items.all()])
                    timeline.append({
                        'date': p.date.strftime('%Y-%m-%d'),
                        'type': 'PRESCRIPTION',
                        'title': 'Prescription Issued & Dispensed',
                        'facility': v.facility.facility_name,
                        'details': f"Prescribed Medicines: {meds or 'Standard EDL Medication'}"
                    })

        # 3. Lab Orders
        lab_orders = LabOrder.objects.filter(patient=patient).select_related('test_master', 'facility')
        for lo in lab_orders:
            res_str = f"Result: {lo.result.result_value} ({lo.result.interpretation_flag})" if hasattr(lo, 'result') else "Status: Pending Verification"
            timeline.append({
                'date': lo.order_date.strftime('%Y-%m-%d %H:%M'),
                'type': 'LAB',
                'title': f"Lab Investigation: {lo.test_master.name}",
                'facility': lo.facility.facility_name,
                'details': f"Test: {lo.test_master.name}. {res_str}"
            })

        # 4. Referrals
        referrals = Referral.objects.filter(patient=patient).select_related('source_facility', 'destination_facility')
        for r in referrals:
            timeline.append({
                'date': r.referral_date.strftime('%Y-%m-%d %H:%M'),
                'type': 'REFERRAL',
                'title': f"Referral to {r.destination_facility.facility_name}",
                'facility': r.source_facility.facility_name,
                'details': f"Urgency: {r.urgency}. Reason: {r.reason}. Status: {r.get_status_display()}"
            })

            if hasattr(r, 'response'):
                resp = r.response
                timeline.append({
                    'date': resp.responded_at.strftime('%Y-%m-%d %H:%M'),
                    'type': 'HOSPITAL_RESPONSE',
                    'title': f"Specialist Response from {r.destination_facility.facility_name}",
                    'facility': r.destination_facility.facility_name,
                    'details': f"Findings: {resp.specialist_findings}. Return Advice: {resp.return_advice}"
                })

        # 5. Follow-ups
        followups = FollowUp.objects.filter(patient=patient)
        for fu in followups:
            timeline.append({
                'date': fu.due_date.strftime('%Y-%m-%d'),
                'type': 'FOLLOWUP',
                'title': f"Follow-up Scheduled [{fu.category}]",
                'facility': fu.facility.facility_name,
                'details': f"Category: {fu.category}, Status: {fu.get_status_display()}, Notes: {fu.notes}"
            })

        timeline.sort(key=lambda x: x['date'])
        return Response({'patient': PatientSerializer(patient).data, 'timeline': timeline})
