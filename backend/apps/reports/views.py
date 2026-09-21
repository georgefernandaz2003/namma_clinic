from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.http import HttpResponse
from django.core.management import call_command
import csv
import datetime

from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription
from apps.laboratory.models import LabOrder
from apps.pharmacy.models import MedicineBatch, InventoryTransaction
from apps.referrals.models import Referral, FollowUp
from apps.ncd.models import NCDRecord
from apps.surveillance.models import DiseaseCase
from apps.alerts.models import Alert
from apps.accounts.permissions import get_accessible_facility_ids_for_user

class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        facility_param = request.query_params.get('facility')
        date_param = request.query_params.get('date')

        # Date parsing
        if date_param:
            try:
                target_date = datetime.datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                target_date = datetime.date.today()
        else:
            target_date = datetime.date.today()

        fac_qs = Facility.objects.all()
        if accessible_ids is not None:
            fac_qs = fac_qs.filter(id__in=accessible_ids)
        if facility_param:
            fac_qs = fac_qs.filter(id=facility_param)

        target_fac_ids = list(fac_qs.values_list('id', flat=True))

        active_fac_name = "All District Facilities"
        active_fac_type = "District Network"
        if facility_param:
            selected_fac = Facility.objects.filter(id=facility_param).first()
            if selected_fac:
                active_fac_name = selected_fac.facility_name
                active_fac_type = selected_fac.get_facility_type_display()
        elif request.user.assigned_facility:
            active_fac_name = request.user.assigned_facility.facility_name
            active_fac_type = request.user.assigned_facility.get_facility_type_display()

        # Facility Counts
        total_facilities = fac_qs.count()

        # OPD Visits for target date
        opd_visits_qs = Visit.objects.filter(facility_id__in=target_fac_ids, opd_date=target_date)
        todays_opd = opd_visits_qs.count()

        # Stage Queue Counts for target date
        triage_waiting = opd_visits_qs.filter(current_queue='TRIAGE', status__in=['WAITING', 'WAITING_FOR_TRIAGE']).count()
        in_triage = opd_visits_qs.filter(current_queue='TRIAGE', status='IN_TRIAGE').count()
        doctor_waiting = opd_visits_qs.filter(current_queue='DOCTOR', status__in=['WAITING_FOR_DOCTOR', 'TRIAGED']).count()
        in_consultation = opd_visits_qs.filter(current_queue='DOCTOR', status='IN_CONSULTATION').count()
        lab_pending = LabOrder.objects.filter(facility_id__in=target_fac_ids, order_date__date=target_date, status__in=['ORDERED', 'SAMPLE_COLLECTED']).count()
        pharmacy_waiting = Prescription.objects.filter(facility_id__in=target_fac_ids, date=target_date, status='PENDING').count()
        completed_count = opd_visits_qs.filter(status='COMPLETED').count()

        # Overall Totals
        total_patients = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids).count()
        registered_today = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids, registration_date=target_date).count()

        # Inventory Counts
        inventory_batches = MedicineBatch.objects.filter(facility_id__in=target_fac_ids)
        total_medicines = inventory_batches.values('medicine').distinct().count() or 14
        low_stock_count = inventory_batches.filter(quantity__gt=0, quantity__lte=100).count()
        out_of_stock_count = inventory_batches.filter(quantity=0).count()
        near_expiry_count = inventory_batches.filter(expiry_date__gt=datetime.date.today(), expiry_date__lte=datetime.date.today() + datetime.timedelta(days=90)).count()
        expired_count = inventory_batches.filter(expiry_date__lte=datetime.date.today()).count()

        # Referral Counts
        pending_referrals = Referral.objects.filter(source_facility_id__in=target_fac_ids, status__in=['CREATED', 'ACCEPTED', 'IN_TRANSIT', 'UNDER_TREATMENT']).count()
        accepted_referrals = Referral.objects.filter(destination_facility_id__in=target_fac_ids, status='ACCEPTED').count()
        completed_referrals = Referral.objects.filter(source_facility_id__in=target_fac_ids, status='COMPLETED').count()

        # Staff Counts
        from apps.accounts.models import User
        staff_qs = User.objects.filter(assigned_facility_id__in=target_fac_ids)
        doctors_count = staff_qs.filter(role='DOCTOR').count()
        nurses_count = staff_qs.filter(role='NURSE').count()
        labs_count = staff_qs.filter(role='LAB_TECHNICIAN').count()
        pharmacists_count = staff_qs.filter(role='PHARMACIST').count()

        # Facility Overview List for District Officer / Admin
        facility_overview = []
        for fac in fac_qs:
            fac_opd = Visit.objects.filter(facility=fac, opd_date=target_date)
            pats = fac_opd.count()
            wait = fac_opd.filter(status__in=['WAITING_FOR_TRIAGE', 'WAITING_FOR_DOCTOR', 'WAITING_FOR_PHARMACY']).count()
            refs = Referral.objects.filter(source_facility=fac, status__in=['CREATED', 'IN_TRANSIT']).count()
            alerts_cnt = Alert.objects.filter(facility=fac, status='NEW').count()
            
            if wait > 5 or alerts_cnt > 0:
                op_status = 'Attention Required'
            elif wait >= 2:
                op_status = 'Busy'
            else:
                op_status = 'Active'

            facility_overview.append({
                'id': fac.id,
                'name': fac.facility_name,
                'type': fac.get_facility_type_display(),
                'patients': pats,
                'waiting': wait,
                'referrals': refs,
                'status': op_status
            })

        # Action Required Items tailored per role
        action_required = []
        role = getattr(request.user, 'role', '')
        if role == 'DISTRICT_OFFICER':
            if pending_referrals > 0:
                action_required.append({'id': 'act-1', 'title': f'{pending_referrals} Cross-Facility Referrals Pending', 'severity': 'HIGH', 'module': 'Referrals'})
            if low_stock_count > 0:
                action_required.append({'id': 'act-2', 'title': f'{low_stock_count} Drug Batches Below Low-Stock Threshold', 'severity': 'MEDIUM', 'module': 'Pharmacy'})
            if expired_count > 0:
                action_required.append({'id': 'act-3', 'title': f'{expired_count} Expired Medication Batches Quarantined', 'severity': 'HIGH', 'module': 'Pharmacy'})
        elif role == 'DOCTOR':
            if doctor_waiting > 0:
                action_required.append({'id': 'act-doc-1', 'title': f'{doctor_waiting} Patients Waiting in OPD Queue', 'severity': 'HIGH', 'module': 'OPD Queue'})
            if lab_pending > 0:
                action_required.append({'id': 'act-doc-2', 'title': f'{lab_pending} Diagnostic Orders Awaiting Results', 'severity': 'MEDIUM', 'module': 'Lab'})
        elif role == 'NURSE':
            if triage_waiting > 0:
                action_required.append({'id': 'act-nur-1', 'title': f'{triage_waiting} Patients Waiting for Vitals Triage', 'severity': 'HIGH', 'module': 'Triage Queue'})
        elif role == 'LAB_TECHNICIAN':
            if lab_pending > 0:
                action_required.append({'id': 'act-lab-1', 'title': f'{lab_pending} Lab Samples Pending Result Verification', 'severity': 'HIGH', 'module': 'Laboratory'})
        elif role == 'PHARMACIST':
            if pharmacy_waiting > 0:
                action_required.append({'id': 'act-pha-1', 'title': f'{pharmacy_waiting} Prescriptions Pending FEFO Dispense', 'severity': 'HIGH', 'module': 'Pharmacy Queue'})
            if low_stock_count > 0:
                action_required.append({'id': 'act-pha-2', 'title': f'{low_stock_count} Medicines Low on Stock', 'severity': 'MEDIUM', 'module': 'Stock Inventory'})

        return Response({
            'date': target_date.strftime('%Y-%m-%d'),
            'is_today': target_date == datetime.date.today(),
            'active_facility': active_fac_name,
            'active_facility_type': active_fac_type,
            'total_facilities': total_facilities,
            'total_patients': total_patients,
            'registered_today': registered_today,
            'todays_opd': todays_opd,
            'opd_stage_flow': {
                'registration': registered_today or todays_opd,
                'triage': triage_waiting + in_triage,
                'doctor': doctor_waiting + in_consultation,
                'lab': lab_pending,
                'pharmacy': pharmacy_waiting,
                'completed': completed_count
            },
            'staff_status': {
                'doctors': {'active': doctors_count, 'total': doctors_count},
                'nurses': {'active': nurses_count, 'total': nurses_count},
                'lab_technicians': {'active': labs_count, 'total': labs_count},
                'pharmacists': {'active': pharmacists_count, 'total': pharmacists_count}
            },
            'inventory_summary': {
                'total_medicines': total_medicines,
                'low_stock': low_stock_count,
                'out_of_stock': out_of_stock_count,
                'expiring_soon': near_expiry_count,
                'expired': expired_count
            },
            'referrals_summary': {
                'pending': pending_referrals,
                'accepted': accepted_referrals,
                'completed': completed_referrals
            },
            'kpis': {
                'triage_waiting': triage_waiting,
                'in_triage': in_triage,
                'vitals_pending': triage_waiting,
                'doctor_waiting': doctor_waiting,
                'in_consultation': in_consultation,
                'lab_pending': lab_pending,
                'pharmacy_waiting': pharmacy_waiting,
                'completed': completed_count,
                'low_stock': low_stock_count,
                'expiring_soon': near_expiry_count
            },
            'facility_overview': facility_overview,
            'action_required': action_required
        })

class CSVExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        report_type = request.query_params.get('type', 'opd')
        facility_param = request.query_params.get('facility')
        accessible_ids = get_accessible_facility_ids_for_user(request.user)

        target_fac_ids = accessible_ids
        if facility_param:
            if target_fac_ids is not None:
                target_fac_ids = [int(facility_param)] if int(facility_param) in target_fac_ids else []
            else:
                target_fac_ids = [int(facility_param)]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="namma_clinic_{report_type}_report.csv"'

        writer = csv.writer(response)

        if report_type == 'opd':
            writer.writerow(['Visit ID', 'Patient Name', 'Facility', 'Visit Type', 'Date', 'Status'])
            visits = Visit.objects.all().select_related('patient', 'facility')
            if target_fac_ids is not None:
                visits = visits.filter(facility_id__in=target_fac_ids)
            for v in visits[:500]:
                writer.writerow([v.visit_id, v.patient.name, v.facility.facility_name, v.visit_type, v.visit_date, v.status])

        elif report_type == 'pharmacy':
            writer.writerow(['Medicine Name', 'Facility', 'Batch Number', 'Supplier', 'Expiry Date', 'Quantity', 'Status'])
            batches = MedicineBatch.objects.all().select_related('medicine', 'facility')
            if target_fac_ids is not None:
                batches = batches.filter(facility_id__in=target_fac_ids)
            for b in batches:
                writer.writerow([b.medicine.generic_name, b.facility.facility_name, b.batch_number, b.supplier, b.expiry_date, b.quantity, b.status])

        elif report_type == 'referrals':
            writer.writerow(['Referral ID', 'Patient Name', 'Source Facility', 'Destination Facility', 'Urgency', 'Status', 'Date'])
            refs = Referral.objects.all().select_related('patient', 'source_facility', 'destination_facility')
            if target_fac_ids is not None:
                from django.db.models import Q
                refs = refs.filter(Q(source_facility_id__in=target_fac_ids) | Q(destination_facility_id__in=target_fac_ids))
            for r in refs:
                writer.writerow([r.referral_id, r.patient.name, r.source_facility.facility_name, r.destination_facility.facility_name, r.urgency, r.status, r.referral_date])

        else:
            writer.writerow(['Patient ID', 'Name', 'Age', 'Gender', 'Mobile', 'District', 'Registration Date'])
            patients = Patient.objects.all().select_related('district')
            if target_fac_ids is not None:
                from django.db.models import Q
                patients = patients.filter(
                    Q(registered_at_facility_id__in=target_fac_ids) |
                    Q(visits__facility_id__in=target_fac_ids) |
                    Q(referrals__destination_facility_id__in=target_fac_ids)
                ).distinct()
            for p in patients[:500]:
                writer.writerow([p.patient_id, p.name, p.age, p.gender, p.mobile, p.district.name if p.district else '', p.registration_date])

        return response

class ResetDemoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            call_command('seed_demo')
            return Response({'status': 'SUCCESS', 'message': 'Demo dataset reset to pristine demonstration state!'})
        except Exception as e:
            return Response({'status': 'ERROR', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
