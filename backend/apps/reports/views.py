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
from apps.reports.services import (
    get_full_dashboard_summary,
    get_hospital_admin_report_data,
    get_facility_scope,
    get_period_date_range,
    get_stock_status
)

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

class HospitalAdminReportView(APIView):
    """
    Authoritative single-source endpoint for Hospital Admin Reports.
    Strictly scopes to assigned facility for Hospital Admin.
    Supports Day, Week, Month, Year periods.
    """
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'reports.view'

    def get(self, request):
        facility_param = request.query_params.get('facility')
        period_param = request.query_params.get('period', 'day')
        date_param = request.query_params.get('date')

        data = get_hospital_admin_report_data(
            user=request.user,
            requested_facility_id=facility_param,
            period=period_param,
            target_date=date_param
        )
        return Response(data)

class CSVExportView(APIView):
    """
    Structured CSV report generator with authoritative facility scoping and period filtering.
    Hospital Admin is strictly scoped to assigned facility.
    """
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'reports.export'

    def get(self, request):
        report_type = request.query_params.get('type', 'opd')
        facility_param = request.query_params.get('facility')
        period_param = request.query_params.get('period', 'day')
        date_param = request.query_params.get('date')

        scope = get_facility_scope(request.user, facility_param)
        target_fac_ids = scope['target_fac_ids']
        start_date, end_date = get_period_date_range(period_param, date_param)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="namma_clinic_{report_type}_{period_param}_{start_date}.csv"'

        writer = csv.writer(response)

        if report_type == 'opd':
            writer.writerow(['Visit ID', 'Patient Name', 'Facility', 'OPD Date', 'Queue Stage', 'Status', 'Priority', 'Assigned Doctor'])
            visits = Visit.objects.filter(
                facility_id__in=target_fac_ids,
                opd_date__gte=start_date,
                opd_date__lte=end_date
            ).select_related('patient', 'facility', 'assigned_doctor')
            for v in visits:
                doc_name = v.assigned_doctor.full_name if v.assigned_doctor else 'Unassigned'
                writer.writerow([v.visit_id, v.patient.name, v.facility.facility_name, v.opd_date, v.current_queue, v.status, v.priority, doc_name])

        elif report_type == 'pharmacy':
            writer.writerow(['Medicine Name', 'Brand', 'Facility', 'Batch Number', 'Expiry Date', 'Quantity', 'Status', 'Days Remaining'])
            batches = MedicineBatch.objects.filter(facility_id__in=target_fac_ids).select_related('medicine', 'facility').order_by('expiry_date')
            today = datetime.date.today()
            for b in batches:
                days_left = (b.expiry_date - today).days
                writer.writerow([b.medicine.generic_name, b.medicine.brand_name, b.facility.facility_name, b.batch_number, b.expiry_date, b.quantity, b.status, days_left])

        elif report_type == 'stock_consumption':
            writer.writerow(['Medicine', 'Brand', 'Dosage Form', 'Unit', 'Opening Stock', 'Received', 'Dispensed', 'Adjusted', 'Closing Stock'])
            from apps.reports.services import get_pharmacy_report_metrics_for_period
            pharm_data = get_pharmacy_report_metrics_for_period(target_fac_ids, start_date, end_date, period_param)
            for item in pharm_data['stock_movement']['items']:
                op_val = item['opening_stock'] if item['opening_stock'] is not None else 'UNAVAILABLE'
                cl_val = item['closing_stock'] if item['closing_stock'] is not None else 'UNAVAILABLE'
                writer.writerow([item['medicine'], item['brand_name'], item['dosage_form'], item['unit'], op_val, item['received'], item['dispensed'], item['adjusted'], cl_val])

        elif report_type == 'expiry':
            writer.writerow(['Medicine Name', 'Batch Number', 'Quantity', 'Expiry Date', 'Days Remaining', 'Status', 'Category'])
            from apps.reports.services import get_pharmacy_report_metrics_for_period
            pharm_data = get_pharmacy_report_metrics_for_period(target_fac_ids, start_date, end_date, period_param)
            for b in pharm_data['expiry_monitoring']['batches']:
                writer.writerow([b['medicine_name'], b['batch_number'], b['quantity'], b['expiry_date'], b['days_remaining'], b['status'], b['category']])

        elif report_type == 'low_stock':
            writer.writerow(['Medicine Name', 'Brand', 'Category', 'Current Stock', 'Minimum Stock', 'Reorder Level', 'Status'])
            from apps.reports.services import get_pharmacy_report_metrics_for_period
            pharm_data = get_pharmacy_report_metrics_for_period(target_fac_ids, start_date, end_date, period_param)
            for item in pharm_data['low_stock_report']:
                writer.writerow([item['generic_name'], item['brand_name'], item['category'], item['current_stock'], item['minimum_stock'], item['reorder_level'], item['status']])

        elif report_type == 'procurement':
            writer.writerow(['PO Number', 'Vendor', 'Order Date', 'Status', 'Total Amount'])
            from apps.reports.services import get_pharmacy_report_metrics_for_period
            pharm_data = get_pharmacy_report_metrics_for_period(target_fac_ids, start_date, end_date, period_param)
            for po in pharm_data['purchases']['purchase_orders_list']:
                writer.writerow([po['po_number'], po['vendor_name'], po['order_date'], po['status'], po['total_amount']])

        elif report_type == 'doctor_activity':
            writer.writerow(['Doctor Name', 'Username', 'Active', 'Patients Consulted', 'Consultations Completed', 'Lab Orders', 'Prescriptions', 'Referrals'])
            from apps.reports.services import get_doctor_staff_report_metrics
            doc_data = get_doctor_staff_report_metrics(target_fac_ids, start_date, end_date)
            for d in doc_data['doctor_activity']:
                writer.writerow([d['name'], d['username'], d['is_active'], d['patients_consulted'], d['consultations_completed'], d['lab_orders'], d['prescriptions'], d['referrals']])

        elif report_type == 'laboratory':
            writer.writerow(['Order ID', 'Patient Name', 'Test Code', 'Test Name', 'Order Date', 'Status'])
            lab_orders = LabOrder.objects.filter(
                facility_id__in=target_fac_ids,
                order_date__date__gte=start_date,
                order_date__date__lte=end_date
            ).select_related('patient', 'test_master')
            for o in lab_orders:
                writer.writerow([o.id, o.patient.name, o.test_master.code, o.test_master.name, o.order_date.strftime('%Y-%m-%d %H:%M'), o.status])

        elif report_type == 'referrals':
            writer.writerow(['Referral ID', 'Patient Name', 'Source Facility', 'Destination Facility', 'Urgency', 'Status', 'Service', 'Date'])
            refs = Referral.objects.filter(
                models.Q(source_facility_id__in=target_fac_ids) | models.Q(destination_facility_id__in=target_fac_ids),
                referral_date__date__gte=start_date,
                referral_date__date__lte=end_date
            ).select_related('patient', 'source_facility', 'destination_facility')
            for r in refs:
                writer.writerow([r.referral_id, r.patient.name, r.source_facility.facility_name, r.destination_facility.facility_name, r.urgency, r.status, r.required_service, r.referral_date.strftime('%Y-%m-%d %H:%M')])

        elif report_type == 'ncd':
            writer.writerow(['Patient Name', 'Screening Date', 'Hypertension Diagnosed', 'Diabetes Diagnosed', 'Risk Level', 'Control Status', 'Last BP', 'Last Glucose'])
            ncds = NCDRecord.objects.filter(
                facility_id__in=target_fac_ids,
                screening_date__gte=start_date,
                screening_date__lte=end_date
            ).select_related('patient')
            for n in ncds:
                writer.writerow([n.patient.name, n.screening_date, n.hypertension_diagnosed, n.diabetes_diagnosed, n.risk_level, n.control_status, n.last_bp, n.last_glucose])

        else: # patients directory
            writer.writerow(['Patient ID', 'Name', 'Age', 'Gender', 'Mobile', 'Registration Date', 'Registered Facility'])
            patients = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids).select_related('registered_at_facility')
            for p in patients[:1000]:
                fac_name = p.registered_at_facility.facility_name if p.registered_at_facility else 'Unassigned'
                writer.writerow([p.patient_id, p.name, p.age, p.gender, p.mobile, p.registration_date, fac_name])

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
