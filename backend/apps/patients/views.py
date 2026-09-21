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

from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'patients.view',
        'POST': 'patients.create',
        'PUT': 'patients.update',
        'PATCH': 'patients.update',
        'DELETE': 'patients.update'
    }

    def get_queryset(self):
        queryset = Patient.objects.all().select_related('ward', 'district', 'registered_at_facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        facility_param = self.request.query_params.get('facility')
        
        if accessible_ids is not None:
            from django.db.models import Q
            if self.request.user.role == 'DISTRICT_OFFICER':
                dho_dist_id = self.request.user.assigned_district_id
                queryset = queryset.filter(
                    Q(district_id=dho_dist_id) |
                    Q(registered_at_facility_id__in=accessible_ids) |
                    Q(visits__facility_id__in=accessible_ids) |
                    Q(referrals__destination_facility_id__in=accessible_ids)
                ).distinct()
            else:
                user_fac_id = facility_param or self.request.user.assigned_facility_id
                queryset = queryset.filter(
                    Q(registered_at_facility_id__in=accessible_ids) |
                    Q(visits__facility_id=user_fac_id) |
                    Q(referrals__destination_facility_id=user_fac_id)
                ).distinct()

        if facility_param:
            # If user has scoped facilities and requested facility is outside their scope, return none
            if accessible_ids is not None and int(facility_param) not in accessible_ids:
                return queryset.none()
            from django.db.models import Q
            queryset = queryset.filter(
                Q(registered_at_facility_id=facility_param) |
                Q(visits__facility_id=facility_param) |
                Q(referrals__destination_facility_id=facility_param)
            ).distinct()

        return queryset.order_by('-id')


    def create(self, request, *args, **kwargs):
        # Duplicate check by name & mobile
        mobile = request.data.get('mobile')
        name = request.data.get('name')
        if mobile and name:
            existing = Patient.objects.filter(mobile=mobile, name__iexact=name).first()
            if existing:
                return Response(
                    {'error': f"Duplicate patient record detected! Patient '{existing.name}' is already registered with Patient ID {existing.patient_id}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        data = request.data.copy()
        if not data.get('registered_at_facility') and request.user.assigned_facility_id:
            data['registered_at_facility'] = request.user.assigned_facility_id

        if not data.get('patient_id'):
            import random
            while True:
                candidate_id = f"NC-KA-2026-{random.randint(1000, 9999)}"
                if not Patient.objects.filter(patient_id=candidate_id).exists():
                    data['patient_id'] = candidate_id
                    break

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class PatientTimelineView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'patients.view'

    def get(self, request, pk=None):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        # Facility Scope Check for Patient Timeline
        if request.user.role != 'DISTRICT_OFFICER':
            user_fac_id = request.user.assigned_facility_id
            accessible_ids = get_accessible_facility_ids_for_user(request.user)
            if accessible_ids and patient.registered_at_facility_id not in accessible_ids:
                # Check for explicit referral path authorization
                has_referral = Referral.objects.filter(
                    patient=patient,
                    destination_facility_id=user_fac_id
                ).exists() or Visit.objects.filter(patient=patient, facility_id=user_fac_id).exists()
                if not has_referral:
                    return Response({'error': 'You do not have permission to access patient records outside your facility scope.'}, status=status.HTTP_403_FORBIDDEN)


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
                        'date': c.created_at.strftime('%Y-%m-%d %H:%M'),
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

        # 6. Uploaded Medical Documents
        documents = PatientDocument.objects.filter(patient=patient).select_related('facility', 'uploaded_by')
        for doc in documents:
            timeline.append({
                'date': doc.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'type': 'DOCUMENT',
                'title': f"Medical Document: {doc.title}",
                'facility': doc.facility.facility_name if doc.facility else 'Namma Clinic',
                'details': f"Type: {doc.get_document_type_display()}, Uploaded By: {doc.uploaded_by.full_name if doc.uploaded_by else 'Staff'}, File: {doc.file_name} ({int(doc.file_size/1024) if doc.file_size else 0} KB)",
                'document_id': doc.id,
                'file_name': doc.file_name,
                'download_url': f"/api/patients/{patient.id}/documents/{doc.id}/download/"
            })

        timeline.sort(key=lambda x: x['date'])
        return Response({'patient': PatientSerializer(patient).data, 'timeline': timeline})

import os
import mimetypes
from django.http import FileResponse, HttpResponse, Http404
from apps.patients.models import PatientDocument
from apps.patients.serializers import PatientDocumentSerializer
from apps.audit.models import AuditLog

class PatientRecordsView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'patients.view'

    def get(self, request, pk=None):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        # Security & Facility Scope Check
        if request.user.role != 'DISTRICT_OFFICER':
            user_fac_id = request.user.assigned_facility_id
            accessible_ids = get_accessible_facility_ids_for_user(request.user)
            if accessible_ids and patient.registered_at_facility_id not in accessible_ids:
                has_access = Referral.objects.filter(
                    patient=patient,
                    destination_facility_id=user_fac_id
                ).exists() or Visit.objects.filter(patient=patient, facility_id=user_fac_id).exists()
                if not has_access:
                    return Response({'error': 'You do not have permission to access patient records outside your facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        # 1. Visits History
        visits = Visit.objects.filter(patient=patient).select_related('facility', 'assigned_doctor', 'token').order_by('-visit_date')
        visits_data = []
        for v in visits:
            visits_data.append({
                'id': v.id,
                'visit_id': v.visit_id,
                'visit_date': v.visit_date.strftime('%Y-%m-%d %H:%M'),
                'facility_name': v.facility.facility_name,
                'token_number': v.token.token_number if hasattr(v, 'token') else None,
                'visit_type': v.visit_type,
                'chief_complaint': v.chief_complaint,
                'priority': v.priority,
                'status': v.status,
                'queue': v.current_queue
            })

        # 2. Consultations (Medical Records)
        consultations = Consultation.objects.filter(patient=patient).select_related('facility', 'doctor', 'visit').order_by('-created_at')
        consultations_data = []
        for c in consultations:
            consultations_data.append({
                'id': c.id,
                'visit_id': c.visit.visit_id if c.visit else None,
                'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
                'facility_name': c.facility.facility_name if c.facility else 'Namma Clinic',
                'doctor_name': c.doctor.full_name if c.doctor else 'Medical Officer',
                'chief_complaint': c.chief_complaint,
                'clinical_history': c.clinical_history,
                'clinical_assessment': c.clinical_assessment,
                'diagnosis_code': c.diagnosis_code,
                'diagnosis_name': c.diagnosis_name,
                'treatment_plan': c.treatment_plan,
                'clinical_notes': c.clinical_notes,
                'follow_up_date': c.follow_up_date.strftime('%Y-%m-%d') if c.follow_up_date else None
            })

        # 3. Lab Reports
        lab_orders = LabOrder.objects.filter(patient=patient).select_related('test_master', 'facility', 'doctor').order_by('-order_date')
        lab_data = []
        for lo in lab_orders:
            has_res = hasattr(lo, 'result')
            lab_data.append({
                'id': lo.id,
                'order_id': f"LAB-{lo.id:04d}",
                'order_date': lo.order_date.strftime('%Y-%m-%d %H:%M'),
                'test_name': lo.test_master.name,
                'test_code': lo.test_master.code,
                'facility_name': lo.facility.facility_name,
                'doctor_name': lo.doctor.full_name if lo.doctor else 'Clinician',
                'status': lo.status,
                'sample_code': lo.sample.sample_code if hasattr(lo, 'sample') else None,
                'result_value': lo.result.result_value if has_res else None,
                'unit': lo.result.unit if has_res else None,
                'interpretation_flag': lo.result.interpretation_flag if has_res else None,
                'verified_by': lo.result.verified_by.full_name if (has_res and lo.result.verified_by) else None,
                'verified_at': lo.result.verified_at.strftime('%Y-%m-%d %H:%M') if (has_res and lo.result.verified_at) else None
            })

        # 4. Prescriptions
        prescriptions = Prescription.objects.filter(patient=patient).select_related('facility', 'doctor', 'consultation').prefetch_related('items').order_by('-date')
        rx_data = []
        for p in prescriptions:
            items = []
            for item in p.items.all():
                items.append({
                    'id': item.id,
                    'medicine_name': item.medicine_name,
                    'dosage': item.dosage,
                    'frequency': item.frequency,
                    'duration_days': item.duration_days,
                    'quantity': item.quantity,
                    'status': item.status
                })
            rx_data.append({
                'id': p.id,
                'date': p.date.strftime('%Y-%m-%d'),
                'facility_name': p.facility.facility_name if p.facility else 'Namma Clinic',
                'doctor_name': p.doctor.full_name if p.doctor else 'Medical Officer',
                'status': p.status,
                'items': items
            })

        # 5. Documents
        documents = PatientDocument.objects.filter(patient=patient).select_related('facility', 'uploaded_by')
        documents_serializer = PatientDocumentSerializer(documents, many=True)

        return Response({
            'patient': PatientSerializer(patient).data,
            'visits': visits_data,
            'medical_records': consultations_data,
            'lab_reports': lab_data,
            'prescriptions': rx_data,
            'documents': documents_serializer.data
        })

from rest_framework import parsers

class PatientDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = PatientDocumentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'patients.view',
        'POST': 'patients.view',
        'PUT': 'patients.view',
        'PATCH': 'patients.view',
        'DELETE': 'patients.view'
    }

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        queryset = PatientDocument.objects.all().select_related('patient', 'facility', 'uploaded_by')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        # Scoping check
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)

        return queryset

    def create(self, request, patient_id=None, *args, **kwargs):
        # District Officer upload restriction
        if request.user.role == 'DISTRICT_OFFICER':
            return Response({'error': 'District Officers have read-only monitoring access and cannot upload clinical documents.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        # Security check: User must have facility access to patient
        if request.user.role != 'DISTRICT_OFFICER':
            user_fac_id = request.user.assigned_facility_id
            accessible_ids = get_accessible_facility_ids_for_user(request.user)
            if accessible_ids and patient.registered_at_facility_id not in accessible_ids:
                has_access = Referral.objects.filter(patient=patient, destination_facility_id=user_fac_id).exists() or Visit.objects.filter(patient=patient, facility_id=user_fac_id).exists()
                if not has_access:
                    return Response({'error': 'You do not have permission to upload documents for patients outside your facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['patient'] = patient.id
        
        file_obj = request.FILES.get('file') or request.data.get('file')
        if not file_obj:
            return Response({'error': 'Please select a valid document file.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        target_facility_id = request.user.assigned_facility_id or patient.registered_at_facility_id

        doc = serializer.save(
            patient=patient,
            uploaded_by=request.user,
            facility_id=target_facility_id,
            file_name=file_obj.name,
            file_size=file_obj.size,
            mime_type=file_obj.content_type or mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'
        )

        # Log Audit Trail
        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PATIENT_DOCUMENT_UPLOAD',
            facility=doc.facility,
            details=f"Uploaded document '{doc.title}' ({doc.document_type}) for Patient {patient.name} [{patient.patient_id}]"
        )

        return Response(PatientDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

class PatientDocumentDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id=None, document_id=None):
        try:
            doc = PatientDocument.objects.select_related('patient', 'facility').get(pk=document_id, patient_id=patient_id)
        except PatientDocument.DoesNotExist:
            return Response({'error': 'Document record not found'}, status=status.HTTP_404_NOT_FOUND)

        patient = doc.patient

        # Security check: User must have facility scope access
        if request.user.role != 'DISTRICT_OFFICER':
            user_fac_id = request.user.assigned_facility_id
            accessible_ids = get_accessible_facility_ids_for_user(request.user)
            if accessible_ids and doc.facility_id not in accessible_ids and patient.registered_at_facility_id not in accessible_ids:
                has_access = Referral.objects.filter(patient=patient, destination_facility_id=user_fac_id).exists() or Visit.objects.filter(patient=patient, facility_id=user_fac_id).exists()
                if not has_access:
                    return Response({'error': 'You do not have permission to view or download documents outside your facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        if not doc.file or not os.path.exists(doc.file.path):
            return Response({'error': 'Physical document file missing on server.'}, status=status.HTTP_404_NOT_FOUND)

        # Log Audit Trail
        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PATIENT_DOCUMENT_DOWNLOAD',
            facility=doc.facility,
            details=f"Viewed/Downloaded document '{doc.title}' ({doc.file_name}) for Patient {patient.name} [{patient.patient_id}]"
        )

        mime_type = doc.mime_type or mimetypes.guess_type(doc.file.path)[0] or 'application/octet-stream'
        response = FileResponse(open(doc.file.path, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'inline; filename="{doc.file_name}"'
        return response
