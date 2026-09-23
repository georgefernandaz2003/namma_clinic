from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db import models
from django.http import HttpResponse
from django.core.management import call_command
import csv
import datetime

from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription
from apps.laboratory.models import LabOrder
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction
from apps.referrals.models import Referral, FollowUp
from apps.ncd.models import NCDRecord
from apps.surveillance.models import DiseaseCase
from apps.alerts.models import Alert
from apps.accounts.models import User
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission
from apps.reports.services import get_full_dashboard_summary

class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'dashboard.view'

    def get(self, request):
        facility_param = request.query_params.get('facility')
        date_param = request.query_params.get('date')

        summary_data = get_full_dashboard_summary(
            user=request.user,
            requested_facility_id=facility_param,
            target_date=date_param
        )
        return Response(summary_data)

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
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'demo.reset'
    required_permissions = {
        'POST': 'demo.reset',
    }

    def post(self, request):
        from apps.audit.models import AuditLog
        user = request.user
        try:
            call_command('seed_demo')
            AuditLog.objects.create(
                user=user,
                username_snapshot=user.username,
                action='RESET_DEMO',
                facility=getattr(user, 'assigned_facility', None),
                details=f"Demo database reset triggered by {user.username} ({user.role})",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({'status': 'SUCCESS', 'message': 'Demo dataset reset to pristine demonstration state!'})
        except Exception as e:
            AuditLog.objects.create(
                user=user,
                username_snapshot=user.username,
                action='RESET_DEMO_FAILED',
                facility=getattr(user, 'assigned_facility', None),
                details=f"Demo reset failed: {str(e)}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({'status': 'ERROR', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
