import datetime
from django.utils import timezone
from django.db.models import Q
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
from apps.pharmacy.models import InventoryTransaction

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
        queryset = Patient.objects.all().select_related('ward', 'district', 'registered_at_facility').order_by('-registration_date', '-id')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        facility_param = self.request.query_params.get('facility')
        
        if accessible_ids is not None:
            from django.db.models import Q
            user_fac_id = facility_param or self.request.user.assigned_facility_id
            queryset = queryset.filter(
                Q(registered_at_facility_id__in=accessible_ids) |
                Q(visits__facility_id=user_fac_id) |
                Q(referrals__destination_facility_id=user_fac_id)
            ).distinct()

        if facility_param:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(registered_at_facility_id=facility_param) |
                Q(visits__facility_id=facility_param) |
                Q(referrals__destination_facility_id=facility_param)
            ).distinct()

        # Support exact registration_date filtering for audit and reconciliation
        req_reg_date = self.request.query_params.get('registration_date')
        if req_reg_date and req_reg_date != 'all':
            import datetime
            try:
                t_date = datetime.datetime.strptime(req_reg_date, '%Y-%m-%d').date()
                queryset = queryset.filter(registration_date=t_date)
            except ValueError:
                pass

        return queryset

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
            patient = Patient.objects.select_related('ward', 'district', 'registered_at_facility').get(pk=pk)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        # Facility Scope Check for Patient Timeline
        if request.user.role != 'DISTRICT_OFFICER':
            user_fac_id = request.user.assigned_facility_id
            accessible_ids = get_accessible_facility_ids_for_user(request.user)
            if accessible_ids and patient.registered_at_facility_id not in accessible_ids:
                has_referral = Referral.objects.filter(
                    patient=patient,
                    destination_facility_id=user_fac_id
                ).exists() or Visit.objects.filter(patient=patient, facility_id=user_fac_id).exists()
                if not has_referral:
                    return Response({'error': 'You do not have permission to access patient records outside your facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        timeline = []

        # 1. Patient Registration Event
        reg_date_str = patient.registration_date.strftime('%Y-%m-%d')
        timeline.append({
            'id': f"REG_{patient.id}",
            'type': 'REGISTRATION',
            'title': 'Patient Registered',
            'timestamp': f"{reg_date_str}T00:00:00",
            'date': reg_date_str,
            'has_time': False,
            'time_display': 'Registration time not recorded',
            'facility': patient.registered_at_facility.facility_name if patient.registered_at_facility else 'Namma Clinic',
            'doctor_or_staff': None,
            'details': f"Registered with UHID {patient.patient_id} | Mobile: {patient.mobile} | ABHA: {patient.ABHA_ID_DEMO or 'Not Assigned'} | Age: {patient.age} | Gender: {patient.gender}",
            'structured_data': {
                'patient_id': patient.patient_id,
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'mobile': patient.mobile,
                'address': patient.address or 'Not recorded',
                'abha_id': patient.ABHA_ID_DEMO or 'Not Assigned',
                'vulnerability': patient.vulnerability_information or 'General',
                'emergency_contact': patient.emergency_contact or 'None',
                'registered_facility': patient.registered_at_facility.facility_name if patient.registered_at_facility else 'Namma Clinic',
                'registration_date': reg_date_str
            }
        })

        # 2. Visits and associated clinical records
        processed_rx_ids = set()
        visits = Visit.objects.filter(patient=patient).select_related(
            'facility', 'assigned_doctor', 'token',
            'triage', 'triage__nurse',
            'consultation', 'consultation__doctor', 'consultation__facility'
        ).prefetch_related(
            'consultation__prescription', 'consultation__prescription__items',
            'status_history', 'status_history__performed_by'
        ).order_by('visit_date')

        for v in visits:
            v_token = v.token.token_number if hasattr(v, 'token') and v.token else v.id
            v_time = v.visit_date
            v_date_str = v_time.strftime('%Y-%m-%d')
            v_time_display = v_time.strftime('%I:%M %p')

            # 2a. Visit Check-in Event
            timeline.append({
                'id': f"VISIT_{v.id}",
                'type': 'VISIT',
                'title': f"Clinic Visit Check-in (#{v_token})",
                'timestamp': v_time.isoformat(),
                'date': v_date_str,
                'has_time': True,
                'time_display': v_time_display,
                'facility': v.facility.facility_name,
                'doctor_or_staff': v.assigned_doctor.full_name if v.assigned_doctor else None,
                'details': f"Token #{v_token} | Category: {v.visit_type} | Priority: {v.priority} | Chief Complaint: {v.chief_complaint or 'Routine Checkup'}",
                'structured_data': {
                    'visit_id': v.visit_id,
                    'token_number': v_token,
                    'visit_type': v.visit_type,
                    'priority': v.priority,
                    'chief_complaint': v.chief_complaint or 'None logged',
                    'current_queue': v.current_queue,
                    'status': v.status,
                    'assigned_doctor': v.assigned_doctor.full_name if v.assigned_doctor else 'Unassigned',
                    'facility': v.facility.facility_name,
                    'arrival_time': v.arrival_time.strftime('%Y-%m-%d %I:%M %p') if v.arrival_time else v_time_display
                }
            })

            # 2b. Nurse Triage Event
            if hasattr(v, 'triage') and v.triage:
                tr = v.triage
                tr_time = tr.created_at
                flags = []
                if tr.high_bp_flag: flags.append('Elevated Blood Pressure')
                if tr.high_glucose_flag: flags.append('Elevated Blood Glucose')
                if tr.fever_flag: flags.append('Febrile / Elevated Temperature')
                if tr.low_spo2_flag: flags.append('Low Oxygen Saturation (<95%)')
                if tr.emergency_flag: flags.append('Emergency Clinical Warning')
                if tr.ncd_risk_flag: flags.append('NCD High Risk Profile')

                flag_str = f" [Alerts: {', '.join(flags)}]" if flags else ""
                nurse_name = tr.nurse.full_name if tr.nurse else 'Triage Nurse'

                timeline.append({
                    'id': f"TRIAGE_{tr.id}",
                    'type': 'TRIAGE',
                    'title': 'Nurse Triage & Vital Signs',
                    'timestamp': tr_time.isoformat(),
                    'date': tr_time.strftime('%Y-%m-%d'),
                    'has_time': True,
                    'time_display': tr_time.strftime('%I:%M %p'),
                    'facility': v.facility.facility_name,
                    'doctor_or_staff': nurse_name,
                    'details': f"BP: {tr.blood_pressure_systolic}/{tr.blood_pressure_diastolic} mmHg, Pulse: {tr.pulse_bpm} bpm, SpO2: {tr.spo2_percent}%, Temp: {tr.temperature_f}°F, Glucose: {tr.blood_glucose_mgdl} mg/dL, BMI: {tr.bmi}{flag_str}",
                    'structured_data': {
                        'blood_pressure': f"{tr.blood_pressure_systolic}/{tr.blood_pressure_diastolic} mmHg",
                        'systolic': tr.blood_pressure_systolic,
                        'diastolic': tr.blood_pressure_diastolic,
                        'pulse_bpm': tr.pulse_bpm,
                        'temperature_f': float(tr.temperature_f),
                        'spo2_percent': tr.spo2_percent,
                        'respiratory_rate': tr.respiratory_rate,
                        'blood_glucose_mgdl': tr.blood_glucose_mgdl,
                        'height_cm': float(tr.height_cm),
                        'weight_kg': float(tr.weight_kg),
                        'bmi': float(tr.bmi),
                        'nurse': nurse_name,
                        'nurse_notes': tr.nurse_notes or 'No additional remarks',
                        'active_flags': flags,
                        'visit_id': v.visit_id
                    }
                })

            # 2c. Doctor Consultation
            if hasattr(v, 'consultation') and v.consultation:
                c = v.consultation
                c_time = c.created_at
                doc_name = c.doctor.full_name if c.doctor else 'Medical Officer'

                timeline.append({
                    'id': f"CONSULT_{c.id}",
                    'type': 'CONSULTATION',
                    'title': f"Doctor Clinical Consultation - {c.diagnosis_name}",
                    'timestamp': c_time.isoformat(),
                    'date': c_time.strftime('%Y-%m-%d'),
                    'has_time': True,
                    'time_display': c_time.strftime('%I:%M %p'),
                    'facility': c.facility.facility_name if c.facility else v.facility.facility_name,
                    'doctor_or_staff': doc_name,
                    'details': f"Dr. {doc_name} | Diagnosis: [{c.diagnosis_code}] {c.diagnosis_name}. Assessment: {c.clinical_assessment or 'Clinical evaluation recorded'}.",
                    'structured_data': {
                        'doctor': doc_name,
                        'visit_id': v.visit_id,
                        'facility': c.facility.facility_name if c.facility else v.facility.facility_name,
                        'chief_complaint': c.chief_complaint,
                        'clinical_history': c.clinical_history or 'None recorded',
                        'clinical_assessment': c.clinical_assessment or 'None recorded',
                        'diagnosis_code': c.diagnosis_code,
                        'diagnosis_name': c.diagnosis_name,
                        'treatment_plan': c.treatment_plan or 'None specified',
                        'clinical_notes': c.clinical_notes or 'None recorded',
                        'follow_up_date': c.follow_up_date.strftime('%Y-%m-%d') if c.follow_up_date else 'None scheduled'
                    }
                })

                # 2d. Doctor Re-consultation (post-lab review)
                # Check if this visit had lab orders that reached VERIFIED
                has_verified_lab = LabOrder.objects.filter(visit=v, status='VERIFIED').exists()
                if has_verified_lab:
                    latest_lab = LabOrder.objects.filter(visit=v, status='VERIFIED').select_related('result').order_by('-result__verified_at').first()
                    reconsult_time = None
                    if latest_lab and hasattr(latest_lab, 'result') and latest_lab.result and latest_lab.result.verified_at:
                        if v.consultation_end_time and v.consultation_end_time > latest_lab.result.verified_at:
                            reconsult_time = v.consultation_end_time
                        else:
                            post_lab_history = v.status_history.filter(timestamp__gte=latest_lab.result.verified_at).order_by('timestamp').first()
                            if post_lab_history:
                                reconsult_time = post_lab_history.timestamp
                            else:
                                reconsult_time = latest_lab.result.verified_at + datetime.timedelta(minutes=5)

                    if reconsult_time:
                        timeline.append({
                            'id': f"RECONSULT_{c.id}",
                            'type': 'RE_CONSULTATION',
                            'title': 'Doctor Re-Consultation (Post-Lab Diagnostic Review)',
                            'timestamp': reconsult_time.isoformat(),
                            'date': reconsult_time.strftime('%Y-%m-%d'),
                            'has_time': True,
                            'time_display': reconsult_time.strftime('%I:%M %p'),
                            'facility': c.facility.facility_name if c.facility else v.facility.facility_name,
                            'doctor_or_staff': doc_name,
                            'details': f"Consultation updated after lab result: Dr. {doc_name} reviewed diagnostic lab findings, confirmed diagnosis [{c.diagnosis_code}] {c.diagnosis_name}, and finalized treatment regime.",
                            'structured_data': {
                                'doctor': doc_name,
                                'visit_id': v.visit_id,
                                'diagnosis': f"[{c.diagnosis_code}] {c.diagnosis_name}",
                                'clinical_notes': c.clinical_notes or 'Post-lab consultation review completed.',
                                'treatment_plan': c.treatment_plan or 'Therapeutic medication issued.',
                                'facility': c.facility.facility_name if c.facility else v.facility.facility_name,
                                'review_status': 'Consultation updated after lab result'
                            }
                        })

                # 2e. Prescription Event
                if hasattr(c, 'prescription') and c.prescription:
                    p = c.prescription
                    processed_rx_ids.add(p.id)
                    p_items = list(p.items.all())
                    items_desc = ", ".join([f"{item.medicine_name} ({item.dosage}, {item.quantity} units)" for item in p_items])
                    p_time = c.created_at
                    timeline.append({
                        'id': f"PRESCR_{p.id}",
                        'type': 'PRESCRIPTION',
                        'title': f"Medical Prescription Issued (#{p.id})",
                        'timestamp': p_time.isoformat(),
                        'date': p.date.strftime('%Y-%m-%d'),
                        'has_time': True,
                        'time_display': p_time.strftime('%I:%M %p'),
                        'facility': p.facility.facility_name if p.facility else v.facility.facility_name,
                        'doctor_or_staff': doc_name,
                        'details': f"Prescription #{p.id} ({p.status}) | Prescribed Medicines: {items_desc or 'Standard formulation'}",
                        'structured_data': {
                            'prescription_id': p.id,
                            'prescription_date': p.date.strftime('%Y-%m-%d'),
                            'created_at': p_time.strftime('%Y-%m-%d %I:%M %p'),
                            'doctor': doc_name,
                            'facility': p.facility.facility_name if p.facility else v.facility.facility_name,
                            'status': p.status,
                            'notes': p.notes or 'None',
                            'items_count': len(p_items),
                            'items': [{
                                'medicine_name': item.medicine_name,
                                'dosage': item.dosage,
                                'frequency': item.frequency,
                                'duration_days': item.duration_days,
                                'quantity': item.quantity,
                                'status': item.status
                            } for item in p_items]
                        }
                    })

            # 2f. Visit Completed Event
            if v.completed_time and v.status == 'COMPLETED':
                comp_time = v.completed_time
                dur_mins = max(0, int((comp_time - v.arrival_time).total_seconds() // 60)) if v.arrival_time else None
                timeline.append({
                    'id': f"VISIT_COMPL_{v.id}",
                    'type': 'VISIT_COMPLETED',
                    'title': f"OPD Visit Completed (#{v_token})",
                    'timestamp': comp_time.isoformat(),
                    'date': comp_time.strftime('%Y-%m-%d'),
                    'has_time': True,
                    'time_display': comp_time.strftime('%I:%M %p'),
                    'facility': v.facility.facility_name,
                    'doctor_or_staff': v.assigned_doctor.full_name if v.assigned_doctor else None,
                    'details': f"Patient OPD visit concluded. Duration: {f'{dur_mins} mins' if dur_mins is not None else 'Completed'}.",
                    'structured_data': {
                        'visit_id': v.visit_id,
                        'token_number': v_token,
                        'facility': v.facility.facility_name,
                        'arrival_time': v.arrival_time.strftime('%Y-%m-%d %I:%M %p') if v.arrival_time else 'N/A',
                        'completed_time': comp_time.strftime('%Y-%m-%d %I:%M %p'),
                        'duration_minutes': dur_mins
                    }
                })

        # Process any stand-alone prescriptions for patient not attached to visited consultations
        other_prescriptions = Prescription.objects.filter(patient=patient).exclude(id__in=processed_rx_ids).select_related('facility', 'doctor', 'consultation').prefetch_related('items')
        for p in other_prescriptions:
            p_items = list(p.items.all())
            items_desc = ", ".join([f"{item.medicine_name} ({item.dosage}, {item.quantity} units)" for item in p_items])
            has_c = hasattr(p, 'consultation') and p.consultation is not None
            p_time = p.consultation.created_at if has_c else datetime.datetime.combine(p.date, datetime.time.min)
            p_doc = p.doctor.full_name if p.doctor else 'Medical Officer'
            timeline.append({
                'id': f"PRESCR_{p.id}",
                'type': 'PRESCRIPTION',
                'title': f"Medical Prescription Issued (#{p.id})",
                'timestamp': p_time.isoformat(),
                'date': p.date.strftime('%Y-%m-%d'),
                'has_time': has_c,
                'time_display': p_time.strftime('%I:%M %p') if has_c else 'Prescription date only',
                'facility': p.facility.facility_name if p.facility else 'Namma Clinic',
                'doctor_or_staff': p_doc,
                'details': f"Prescription #{p.id} ({p.status}) | Prescribed Medicines: {items_desc or 'Standard formulation'}",
                'structured_data': {
                    'prescription_id': p.id,
                    'prescription_date': p.date.strftime('%Y-%m-%d'),
                    'created_at': p_time.strftime('%Y-%m-%d %I:%M %p') if has_c else p.date.strftime('%Y-%m-%d'),
                    'doctor': p_doc,
                    'facility': p.facility.facility_name if p.facility else 'Namma Clinic',
                    'status': p.status,
                    'notes': p.notes or 'None',
                    'items_count': len(p_items),
                    'items': [{
                        'medicine_name': item.medicine_name,
                        'dosage': item.dosage,
                        'frequency': item.frequency,
                        'duration_days': item.duration_days,
                        'quantity': item.quantity,
                        'status': item.status
                    } for item in p_items]
                }
            })

        # 3. Lab Orders, Sample Collections, and Verified Results
        lab_orders = LabOrder.objects.filter(patient=patient).select_related(
            'test_master', 'facility', 'doctor', 'visit',
            'sample', 'sample__collected_by',
            'result', 'result__verified_by'
        ).order_by('order_date')

        for lo in lab_orders:
            # 3a. Lab Order Creation Event
            lo_time = lo.order_date
            timeline.append({
                'id': f"LAB_ORD_{lo.id}",
                'type': 'LAB_ORDER',
                'title': f"Diagnostic Lab Order: {lo.test_master.name}",
                'timestamp': lo_time.isoformat(),
                'date': lo_time.strftime('%Y-%m-%d'),
                'has_time': True,
                'time_display': lo_time.strftime('%I:%M %p'),
                'facility': lo.facility.facility_name,
                'doctor_or_staff': lo.doctor.full_name if lo.doctor else 'Ordering Doctor',
                'details': f"Order LAB-{lo.id:04d} [{lo.test_master.code}] | Category: {lo.test_master.category} | Status: {lo.status}",
                'structured_data': {
                    'order_id': f"LAB-{lo.id:04d}",
                    'test_name': lo.test_master.name,
                    'test_code': lo.test_master.code,
                    'category': lo.test_master.category,
                    'ordering_doctor': lo.doctor.full_name if lo.doctor else 'Clinician',
                    'facility': lo.facility.facility_name,
                    'status': lo.status,
                    'order_time': lo_time.strftime('%Y-%m-%d %I:%M %p')
                }
            })

            # 3b. Sample Collection Event
            if hasattr(lo, 'sample') and lo.sample and lo.sample.collected_at:
                s = lo.sample
                s_time = s.collected_at
                tech_name = s.collected_by.full_name if s.collected_by else 'Lab Technician'
                timeline.append({
                    'id': f"LAB_SMP_{s.id}",
                    'type': 'SAMPLE_COLLECTION',
                    'title': f"Lab Specimen Collected: {lo.test_master.name}",
                    'timestamp': s_time.isoformat(),
                    'date': s_time.strftime('%Y-%m-%d'),
                    'has_time': True,
                    'time_display': s_time.strftime('%I:%M %p'),
                    'facility': lo.facility.facility_name,
                    'doctor_or_staff': tech_name,
                    'details': f"Specimen: {s.sample_type} | Sample Barcode: {s.sample_code} | Collected by: {tech_name}",
                    'structured_data': {
                        'order_id': f"LAB-{lo.id:04d}",
                        'test_name': lo.test_master.name,
                        'sample_code': s.sample_code,
                        'sample_type': s.sample_type,
                        'collected_by': tech_name,
                        'facility': lo.facility.facility_name,
                        'collection_time': s_time.strftime('%Y-%m-%d %I:%M %p')
                    }
                })

            # 3c. Lab Result Verification Event
            if hasattr(lo, 'result') and lo.result and lo.result.verified_at:
                res = lo.result
                res_time = res.verified_at
                verifier = res.verified_by.full_name if res.verified_by else 'Lab In-Charge'
                ref_str = f" (Ref: {res.reference_range or lo.test_master.reference_range})" if (res.reference_range or lo.test_master.reference_range) else ""
                timeline.append({
                    'id': f"LAB_RES_{res.id}",
                    'type': 'LAB_RESULT',
                    'title': f"Lab Result Verified: {lo.test_master.name}",
                    'timestamp': res_time.isoformat(),
                    'date': res_time.strftime('%Y-%m-%d'),
                    'has_time': True,
                    'time_display': res_time.strftime('%I:%M %p'),
                    'facility': lo.facility.facility_name,
                    'doctor_or_staff': verifier,
                    'details': f"Result: {res.result_value} {res.unit or lo.test_master.unit} [{res.interpretation_flag}]{ref_str} | Verified by {verifier}",
                    'structured_data': {
                        'order_id': f"LAB-{lo.id:04d}",
                        'test_name': lo.test_master.name,
                        'test_code': lo.test_master.code,
                        'result_value': res.result_value,
                        'unit': res.unit or lo.test_master.unit,
                        'reference_range': res.reference_range or lo.test_master.reference_range,
                        'interpretation_flag': res.interpretation_flag,
                        'verified_by': verifier,
                        'facility': lo.facility.facility_name,
                        'verification_time': res_time.strftime('%Y-%m-%d %I:%M %p'),
                        'notes': res.notes or 'Result verified within protocol'
                    }
                })

        # 4. Pharmacy Dispensing Events (from InventoryTransaction)
        patient_rx_ids = list(Prescription.objects.filter(patient=patient).values_list('id', flat=True))
        rx_ref_keys = [f"PRESCR-{pid}" for pid in patient_rx_ids] + [f"RX-{pid}" for pid in patient_rx_ids] + [f"PRESCRIPTION-{pid}" for pid in patient_rx_ids]
        
        dispense_txs = InventoryTransaction.objects.filter(
            transaction_type='DISPENSED'
        ).filter(
            Q(reference_id__in=rx_ref_keys) |
            Q(notes__icontains=patient.patient_id) |
            Q(notes__icontains=patient.name)
        ).select_related('medicine', 'batch', 'facility', 'created_by').order_by('created_at')

        for tx in dispense_txs:
            tx_time = tx.created_at
            pharma_name = tx.created_by.full_name if tx.created_by else 'Pharmacist'
            batch_num = tx.batch.batch_number if tx.batch else 'FEFO'
            exp_date = tx.batch.expiry_date.strftime('%Y-%m-%d') if (tx.batch and tx.batch.expiry_date) else 'N/A'
            timeline.append({
                'id': f"DISP_{tx.id}",
                'type': 'DISPENSING',
                'title': f"Pharmacy Dispensed: {tx.medicine.generic_name}",
                'timestamp': tx_time.isoformat(),
                'date': tx_time.strftime('%Y-%m-%d'),
                'has_time': True,
                'time_display': tx_time.strftime('%I:%M %p'),
                'facility': tx.facility.facility_name,
                'doctor_or_staff': pharma_name,
                'details': f"Dispensed {tx.quantity} units of {tx.medicine.generic_name} (Batch: {batch_num}, Exp: {exp_date}) by {pharma_name}",
                'structured_data': {
                    'medicine_name': tx.medicine.generic_name,
                    'brand_name': tx.medicine.brand_name or 'Generic',
                    'batch_number': batch_num,
                    'expiry_date': exp_date,
                    'quantity_dispensed': tx.quantity,
                    'dispensed_by': pharma_name,
                    'facility': tx.facility.facility_name,
                    'reference_id': tx.reference_id or 'Rx Dispensing',
                    'notes': tx.notes or 'Stock deducted via FEFO batch allocation'
                }
            })

        # 5. Clinical Referrals and Specialist Responses
        referrals = Referral.objects.filter(patient=patient).select_related(
            'source_facility', 'destination_facility', 'referring_doctor',
            'response', 'response__hospital_doctor'
        ).order_by('referral_date')

        for r in referrals:
            ref_time = r.referral_date
            ref_doc = r.referring_doctor.full_name if r.referring_doctor else 'Referring Clinician'
            timeline.append({
                'id': f"REF_{r.id}",
                'type': 'REFERRAL',
                'title': f"Referral to {r.destination_facility.facility_name}",
                'timestamp': ref_time.isoformat(),
                'date': ref_time.strftime('%Y-%m-%d'),
                'has_time': True,
                'time_display': ref_time.strftime('%I:%M %p'),
                'facility': r.source_facility.facility_name,
                'doctor_or_staff': ref_doc,
                'details': f"Referral {r.referral_id} | Urgency: {r.urgency} | Service: {r.required_service} | Reason: {r.reason} | Status: {r.get_status_display()}",
                'structured_data': {
                    'referral_id': r.referral_id,
                    'source_facility': r.source_facility.facility_name,
                    'destination_facility': r.destination_facility.facility_name,
                    'referring_doctor': ref_doc,
                    'urgency': r.urgency,
                    'required_service': r.required_service,
                    'reason': r.reason,
                    'clinical_summary': r.clinical_summary,
                    'status': r.get_status_display()
                }
            })

            if hasattr(r, 'response') and r.response:
                resp = r.response
                resp_time = resp.responded_at
                hosp_doc = resp.hospital_doctor.full_name if resp.hospital_doctor else 'Specialist Physician'
                timeline.append({
                    'id': f"REF_RESP_{resp.id}",
                    'type': 'REFERRAL_RESPONSE',
                    'title': f"Specialist Response from {r.destination_facility.facility_name}",
                    'timestamp': resp_time.isoformat(),
                    'date': resp_time.strftime('%Y-%m-%d'),
                    'has_time': True,
                    'time_display': resp_time.strftime('%I:%M %p'),
                    'facility': r.destination_facility.facility_name,
                    'doctor_or_staff': hosp_doc,
                    'details': f"Dr. {hosp_doc} | Findings: {resp.specialist_findings} | Return Advice: {resp.return_advice}",
                    'structured_data': {
                        'referral_id': r.referral_id,
                        'specialist_doctor': hosp_doc,
                        'hospital': r.destination_facility.facility_name,
                        'findings': resp.specialist_findings,
                        'treatment_summary': resp.treatment_summary,
                        'return_advice': resp.return_advice,
                        'responded_at': resp_time.strftime('%Y-%m-%d %I:%M %p')
                    }
                })

        # 6. Follow-up Scheduled
        followups = FollowUp.objects.filter(patient=patient).select_related('facility', 'visit').order_by('due_date')
        for fu in followups:
            fu_date_str = fu.due_date.strftime('%Y-%m-%d')
            timeline.append({
                'id': f"FU_{fu.id}",
                'type': 'FOLLOWUP',
                'title': f"Follow-up Scheduled [{fu.category}]",
                'timestamp': f"{fu_date_str}T00:00:00",
                'date': fu_date_str,
                'has_time': False,
                'time_display': 'Scheduled for date',
                'facility': fu.facility.facility_name,
                'doctor_or_staff': None,
                'details': f"Category: {fu.category} | Status: {fu.get_status_display()} | Notes: {fu.notes or 'Routine clinical review'}",
                'structured_data': {
                    'category': fu.category,
                    'due_date': fu_date_str,
                    'status': fu.get_status_display(),
                    'facility': fu.facility.facility_name,
                    'notes': fu.notes or 'No additional notes'
                }
            })

        # 7. Uploaded Medical Documents
        documents = PatientDocument.objects.filter(patient=patient).select_related('facility', 'uploaded_by').order_by('uploaded_at')
        for doc in documents:
            doc_time = doc.uploaded_at
            uploader = doc.uploaded_by.full_name if doc.uploaded_by else 'Clinical Staff'
            timeline.append({
                'id': f"DOC_{doc.id}",
                'type': 'DOCUMENT',
                'title': f"Medical Document: {doc.title}",
                'timestamp': doc_time.isoformat(),
                'date': doc_time.strftime('%Y-%m-%d'),
                'has_time': True,
                'time_display': doc_time.strftime('%I:%M %p'),
                'facility': doc.facility.facility_name if doc.facility else 'Namma Clinic',
                'doctor_or_staff': uploader,
                'details': f"Type: {doc.get_document_type_display()} | File: {doc.file_name} ({round(doc.file_size/1024.0, 1) if doc.file_size else 0} KB) | Uploaded by {uploader}",
                'document_id': doc.id,
                'file_name': doc.file_name,
                'download_url': f"/api/patients/{patient.id}/documents/{doc.id}/download/",
                'structured_data': {
                    'title': doc.title,
                    'document_type': doc.get_document_type_display(),
                    'file_name': doc.file_name,
                    'file_size_kb': round(doc.file_size / 1024.0, 1) if doc.file_size else 0,
                    'mime_type': doc.mime_type,
                    'uploaded_by': uploader,
                    'uploaded_at': doc_time.strftime('%Y-%m-%d %I:%M %p'),
                    'description': doc.description or 'No description'
                }
            })

        # 8. Sort timeline in reverse chronological order (Newest First) by actual timestamp
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)

        return Response({
            'patient': PatientSerializer(patient).data,
            'timeline': timeline
        })

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
            patient = Patient.objects.select_related('ward', 'district', 'registered_at_facility').get(pk=pk)
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
                'arrival_time': v.arrival_time.strftime('%Y-%m-%d %H:%M') if v.arrival_time else None,
                'completed_time': v.completed_time.strftime('%Y-%m-%d %H:%M') if v.completed_time else None,
                'facility_name': v.facility.facility_name,
                'token_number': v.token.token_number if hasattr(v, 'token') and v.token else None,
                'visit_type': v.visit_type,
                'chief_complaint': v.chief_complaint,
                'priority': v.priority,
                'status': v.status,
                'queue': v.current_queue,
                'assigned_doctor_name': v.assigned_doctor.full_name if v.assigned_doctor else None
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
        lab_orders = LabOrder.objects.filter(patient=patient).select_related(
            'test_master', 'facility', 'doctor',
            'sample', 'sample__collected_by',
            'result', 'result__verified_by'
        ).order_by('-order_date')
        lab_data = []
        for lo in lab_orders:
            has_res = hasattr(lo, 'result') and lo.result is not None
            has_smp = hasattr(lo, 'sample') and lo.sample is not None
            lab_data.append({
                'id': lo.id,
                'order_id': f"LAB-{lo.id:04d}",
                'order_date': lo.order_date.strftime('%Y-%m-%d %H:%M'),
                'test_name': lo.test_master.name,
                'test_code': lo.test_master.code,
                'category': lo.test_master.category,
                'facility_name': lo.facility.facility_name,
                'doctor_name': lo.doctor.full_name if lo.doctor else 'Clinician',
                'status': lo.status,
                'sample_code': lo.sample.sample_code if has_smp else None,
                'sample_type': lo.sample.sample_type if has_smp else None,
                'sample_collected_at': lo.sample.collected_at.strftime('%Y-%m-%d %H:%M') if (has_smp and lo.sample.collected_at) else None,
                'sample_collected_by': lo.sample.collected_by.full_name if (has_smp and lo.sample.collected_by) else None,
                'result_value': lo.result.result_value if has_res else None,
                'unit': lo.result.unit or lo.test_master.unit if has_res else lo.test_master.unit,
                'reference_range': lo.result.reference_range or lo.test_master.reference_range if has_res else lo.test_master.reference_range,
                'interpretation_flag': lo.result.interpretation_flag if has_res else None,
                'verified_by': lo.result.verified_by.full_name if (has_res and lo.result.verified_by) else None,
                'verified_at': lo.result.verified_at.strftime('%Y-%m-%d %H:%M') if (has_res and lo.result.verified_at) else None,
                'notes': lo.result.notes if has_res else ''
            })

        # 4. Prescriptions
        prescriptions = Prescription.objects.filter(patient=patient).select_related('facility', 'doctor', 'consultation').prefetch_related('items').order_by('-date')
        rx_ids = [p.id for p in prescriptions]
        rx_ref_keys = [f"PRESCR-{pid}" for pid in rx_ids] + [f"RX-{pid}" for pid in rx_ids]
        dispense_txs = list(InventoryTransaction.objects.filter(
            transaction_type='DISPENSED'
        ).filter(
            Q(reference_id__in=rx_ref_keys) |
            Q(notes__icontains=patient.patient_id) |
            Q(notes__icontains=patient.name)
        ).select_related('medicine', 'batch', 'facility', 'created_by'))

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

            p_ref = f"PRESCR-{p.id}"
            matched_dispenses = [
                {
                    'id': tx.id,
                    'medicine_name': tx.medicine.generic_name,
                    'batch_number': tx.batch.batch_number if tx.batch else 'FEFO',
                    'quantity': tx.quantity,
                    'dispensed_at': tx.created_at.strftime('%Y-%m-%d %H:%M'),
                    'dispensed_by': tx.created_by.full_name if tx.created_by else 'Pharmacist'
                }
                for tx in dispense_txs if tx.reference_id == p_ref or str(p.id) in tx.reference_id
            ]

            rx_data.append({
                'id': p.id,
                'date': p.date.strftime('%Y-%m-%d'),
                'created_at': p.consultation.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(p, 'consultation') and p.consultation else None,
                'facility_name': p.facility.facility_name if p.facility else 'Namma Clinic',
                'doctor_name': p.doctor.full_name if p.doctor else 'Medical Officer',
                'status': p.status,
                'notes': p.notes,
                'items': items,
                'dispensed_transactions': matched_dispenses
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
