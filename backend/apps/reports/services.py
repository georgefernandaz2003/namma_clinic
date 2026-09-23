import datetime
from django.db import models
from django.db.models import Q, Sum

from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Prescription
from apps.laboratory.models import LabOrder
from apps.pharmacy.models import MedicineMaster, MedicineBatch
from apps.referrals.models import Referral
from apps.alerts.models import Alert
from apps.accounts.models import User

# Standardized application-wide threshold for expiring batches
EXPIRING_SOON_DAYS = 60


def get_facility_scope(user, requested_facility_id=None):
    """
    Authoritative facility scoping resolution:
    - DISTRICT_OFFICER:
      Default to district-wide monitoring (active_facility_id: None) over all facilities in assigned district.
      If a specific facility is requested and belongs to assigned district, scopes to that single facility.
      If requested facility is outside district, clamps to district-wide scope.
    - Operational Roles (HOSPITAL_ADMIN, DOCTOR, NURSE, LAB_TECHNICIAN, PHARMACIST):
      Strictly locked to assigned_facility_id. Any requested facility param is ignored.
    """
    role = getattr(user, 'role', '')

    if role == 'DISTRICT_OFFICER':
        if user.assigned_district:
            district_fac_qs = Facility.objects.filter(district=user.assigned_district)
            district_name = user.assigned_district.name
            district_id = user.assigned_district.id
        else:
            district_fac_qs = Facility.objects.all()
            district_name = "District"
            district_id = None

        if requested_facility_id:
            selected_fac = district_fac_qs.filter(id=requested_facility_id).first()
            if selected_fac:
                return {
                    'target_fac_ids': [selected_fac.id],
                    'active_facility_id': selected_fac.id,
                    'active_fac_name': selected_fac.facility_name,
                    'active_fac_type': selected_fac.get_facility_type_display(),
                    'district_name': district_name,
                    'district_id': district_id,
                    'fac_qs': district_fac_qs.filter(id=selected_fac.id),
                    'total_facilities': 1
                }

        # District-wide default
        target_fac_ids = list(district_fac_qs.values_list('id', flat=True))
        return {
            'target_fac_ids': target_fac_ids,
            'active_facility_id': None,
            'active_fac_name': f"{district_name} District Network",
            'active_fac_type': "District Network",
            'district_name': district_name,
            'district_id': district_id,
            'fac_qs': district_fac_qs,
            'total_facilities': district_fac_qs.count()
        }

    # Operational roles: strictly locked to assigned_facility
    assigned_fac = getattr(user, 'assigned_facility', None)
    if assigned_fac:
        return {
            'target_fac_ids': [assigned_fac.id],
            'active_facility_id': assigned_fac.id,
            'active_fac_name': assigned_fac.facility_name,
            'active_fac_type': assigned_fac.get_facility_type_display(),
            'district_name': assigned_fac.district.name if assigned_fac.district else None,
            'district_id': assigned_fac.district.id if assigned_fac.district else None,
            'fac_qs': Facility.objects.filter(id=assigned_fac.id),
            'total_facilities': 1
        }

    return {
        'target_fac_ids': [],
        'active_facility_id': None,
        'active_fac_name': "Unassigned Facility",
        'active_fac_type': "Unknown",
        'district_name': None,
        'district_id': None,
        'fac_qs': Facility.objects.none(),
        'total_facilities': 0
    }


def get_patient_metrics(target_fac_ids, target_date):
    """Authoritative patient metric calculations."""
    total = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids).count()
    registered_today = Patient.objects.filter(
        registered_at_facility_id__in=target_fac_ids,
        registration_date=target_date
    ).count()

    # New OPD patients: distinct patients whose registration date equals target_date and who attended OPD
    new_opd = Visit.objects.filter(
        facility_id__in=target_fac_ids,
        opd_date=target_date,
        patient__registration_date=target_date
    ).values('patient').distinct().count()

    return {
        'total': total,
        'registered_today': registered_today,
        'new_opd': new_opd
    }


def get_visit_and_queue_metrics(target_fac_ids, target_date):
    """Authoritative OPD visits and stage queue metrics."""
    opd_visits_qs = Visit.objects.filter(facility_id__in=target_fac_ids, opd_date=target_date)

    total = opd_visits_qs.count()
    emergency = opd_visits_qs.filter(priority='EMERGENCY').count()
    completed = opd_visits_qs.filter(status='COMPLETED').count()

    # Queues:
    # 1. Triage Queue
    triage_waiting = opd_visits_qs.filter(
        current_queue='TRIAGE',
        status__in=['WAITING', 'WAITING_FOR_TRIAGE']
    ).count()
    triage_in_progress = opd_visits_qs.filter(
        current_queue='TRIAGE',
        status='IN_TRIAGE'
    ).count()

    # 2. Doctor Queue
    doctor_waiting = opd_visits_qs.filter(
        current_queue='DOCTOR',
        status__in=['WAITING_FOR_DOCTOR', 'TRIAGED', 'LAB_COMPLETED']
    ).count()
    doctor_in_consultation = opd_visits_qs.filter(
        current_queue='DOCTOR',
        status='IN_CONSULTATION'
    ).count()

    # 3. Lab Queue (Visits in LAB stage)
    lab_pending = opd_visits_qs.filter(
        current_queue='LAB',
        status__in=['LAB_PENDING', 'LAB_IN_PROGRESS']
    ).count()

    # 4. Pharmacy Queue (Visits in PHARMACY stage)
    pharmacy_waiting = opd_visits_qs.filter(
        current_queue='PHARMACY',
        status__in=['WAITING_FOR_PHARMACY', 'IN_PHARMACY']
    ).count()

    total_waiting = triage_waiting + doctor_waiting + lab_pending + pharmacy_waiting

    return {
        'visits': {
            'total': total,
            'waiting': total_waiting,
            'in_consultation': doctor_in_consultation,
            'lab_pending': lab_pending,
            'pharmacy_waiting': pharmacy_waiting,
            'completed': completed,
            'emergency': emergency
        },
        'queues': {
            'triage_waiting': triage_waiting,
            'triage_in_progress': triage_in_progress,
            'doctor_waiting': doctor_waiting,
            'doctor_in_consultation': doctor_in_consultation,
            'lab_pending': lab_pending,
            'pharmacy_waiting': pharmacy_waiting
        }
    }


def get_laboratory_metrics(target_fac_ids, target_date):
    """Authoritative laboratory order and diagnostic test metrics."""
    lab_orders_qs = LabOrder.objects.filter(
        facility_id__in=target_fac_ids,
        order_date__date=target_date
    )

    total_orders = lab_orders_qs.count()
    pending = lab_orders_qs.filter(status='ORDERED').count()
    sample_collected = lab_orders_qs.filter(status='SAMPLE_COLLECTED').count()
    result_pending = pending + sample_collected
    verified = lab_orders_qs.filter(status='VERIFIED').count()

    return {
        'total_orders': total_orders,
        'pending': pending,
        'sample_collected': sample_collected,
        'result_pending': result_pending,
        'completed': verified,
        'verified': verified
    }


def get_pharmacy_and_inventory_metrics(target_fac_ids, target_date):
    """Authoritative pharmacy prescription orders and facility drug inventory metrics."""
    # Prescriptions
    rx_qs = Prescription.objects.filter(
        facility_id__in=target_fac_ids,
        date=target_date
    )
    total_prescriptions = rx_qs.count()
    waiting = rx_qs.filter(status__in=['PENDING', 'ACTIVE', 'PARTIALLY_DISPENSED']).count()
    dispensed = rx_qs.filter(status='DISPENSED').count()

    # Inventory
    inventory_batches = MedicineBatch.objects.filter(facility_id__in=target_fac_ids)
    all_master_meds = MedicineMaster.objects.all()
    medicine_master_total = all_master_meds.count()

    stocked_medicines_ids = inventory_batches.values_list('medicine_id', flat=True).distinct()
    stocked_medicines = len(stocked_medicines_ids)

    today = datetime.date.today()
    expiring_threshold = today + datetime.timedelta(days=EXPIRING_SOON_DAYS)

    low_stock_count = 0
    out_of_stock_count = 0

    for m in all_master_meds:
        m_batches = inventory_batches.filter(medicine=m)
        tot_qty = m_batches.aggregate(t=Sum('quantity'))['t'] or 0
        threshold = m.minimum_stock or m.reorder_level or 0
        if tot_qty == 0:
            out_of_stock_count += 1
        elif threshold > 0 and tot_qty <= threshold:
            low_stock_count += 1

    low_stock_batches = 0
    for b in inventory_batches.filter(quantity__gt=0).select_related('medicine'):
        threshold = b.medicine.minimum_stock or b.medicine.reorder_level or 0
        if threshold > 0 and b.quantity <= threshold:
            low_stock_batches += 1

    expiring_soon_count = inventory_batches.filter(
        quantity__gt=0,
        expiry_date__gt=today,
        expiry_date__lte=expiring_threshold
    ).count()

    expired_count = inventory_batches.filter(
        Q(expiry_date__lte=today) | Q(status='EXPIRED')
    ).count()

    return {
        'total_prescriptions': total_prescriptions,
        'waiting': waiting,
        'dispensed': dispensed,
        'medicine_master_total': medicine_master_total,
        'stocked_medicines': stocked_medicines,
        'low_stock': low_stock_count,
        'low_stock_medicines': low_stock_count,
        'low_stock_batches': low_stock_batches,
        'out_of_stock': out_of_stock_count,
        'expiring_soon': expiring_soon_count,
        'expired': expired_count
    }


def get_referral_metrics(target_fac_ids):
    """
    Authoritative cross-facility referral metrics.
    A referral belongs to the facility scope if the facility is either the source or destination.
    """
    ref_qs = Referral.objects.filter(
        Q(source_facility_id__in=target_fac_ids) | Q(destination_facility_id__in=target_fac_ids)
    ).distinct()

    pending = ref_qs.filter(status__in=['CREATED', 'IN_TRANSIT']).count()
    accepted = ref_qs.filter(status='ACCEPTED').count()
    in_transit = ref_qs.filter(status='IN_TRANSIT').count()
    under_treatment = ref_qs.filter(status='UNDER_TREATMENT').count()
    completed = ref_qs.filter(status__in=['COMPLETED', 'CLOSED']).count()

    return {
        'pending': pending,
        'accepted': accepted,
        'in_transit': in_transit,
        'under_treatment': under_treatment,
        'completed': completed,
        'total': ref_qs.count()
    }


def get_staff_metrics(target_fac_ids):
    """Authoritative staff count metrics partitioned by role and is_active."""
    staff_qs = User.objects.filter(assigned_facility_id__in=target_fac_ids)

    def _role_stat(role_code):
        role_qs = staff_qs.filter(role=role_code)
        active = role_qs.filter(is_active=True).count()
        inactive = role_qs.filter(is_active=False).count()
        return {
            'active': active,
            'inactive': inactive,
            'total': active + inactive
        }

    return {
        'doctors': _role_stat('DOCTOR'),
        'nurses': _role_stat('NURSE'),
        'lab_technicians': _role_stat('LAB_TECHNICIAN'),
        'pharmacists': _role_stat('PHARMACIST')
    }


def get_alert_metrics(target_fac_ids):
    """Authoritative operational alerts metrics."""
    alert_qs = Alert.objects.filter(facility_id__in=target_fac_ids)

    new_count = alert_qs.filter(status='NEW').count()
    ack_count = alert_qs.filter(status='ACKNOWLEDGED').count()
    resolved_count = alert_qs.filter(status='RESOLVED').count()

    return {
        'new': new_count,
        'acknowledged': ack_count,
        'resolved': resolved_count,
        'total': alert_qs.count()
    }


def get_facility_overview(fac_qs, target_date):
    """
    Facility Operation Overview: Evaluates each healthcare facility using
    identical backend business rules.
    """
    facility_overview = []
    for fac in fac_qs:
        fac_opd = Visit.objects.filter(facility=fac, opd_date=target_date)
        pats = fac_opd.count()
        wait = fac_opd.filter(
            status__in=['WAITING_FOR_TRIAGE', 'WAITING_FOR_DOCTOR', 'WAITING_FOR_PHARMACY', 'WAITING', 'TRIAGED']
        ).count()
        refs = Referral.objects.filter(
            Q(source_facility=fac) | Q(destination_facility=fac),
            status__in=['CREATED', 'IN_TRANSIT']
        ).count()
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

    return facility_overview


def get_action_required(role, v_metrics, lab_metrics, pharm_metrics, ref_metrics):
    """Generates consistent high-priority action alerts from authoritative metrics."""
    action_required = []

    triage_waiting = v_metrics['queues']['triage_waiting']
    doctor_waiting = v_metrics['queues']['doctor_waiting']
    emergency_count = v_metrics['visits']['emergency']
    lab_pending = lab_metrics['result_pending']
    pharmacy_waiting = pharm_metrics['waiting']
    low_stock = pharm_metrics['low_stock']
    pending_refs = ref_metrics['pending']

    if role == 'DISTRICT_OFFICER':
        if pending_refs > 0:
            action_required.append({
                'id': 'act-dist-1',
                'title': f'{pending_refs} Urgent Cross-Facility Referrals Pending Review',
                'severity': 'HIGH',
                'module': 'Referrals'
            })
        if low_stock > 0:
            action_required.append({
                'id': 'act-dist-2',
                'title': f'{low_stock} Essential Drug Stocks Below Critical Threshold',
                'severity': 'HIGH',
                'module': 'Pharmacy Supply'
            })
        if emergency_count > 0:
            action_required.append({
                'id': 'act-dist-3',
                'title': f'{emergency_count} Emergency Priority Patients Currently in Facility Queue',
                'severity': 'HIGH',
                'module': 'Clinical Queue'
            })
    elif role == 'HOSPITAL_ADMIN':
        if emergency_count > 0:
            action_required.append({
                'id': 'act-adm-1',
                'title': f'{emergency_count} Emergency Cases Need Active Monitoring',
                'severity': 'HIGH',
                'module': 'OPD Triage'
            })
        if low_stock > 0:
            action_required.append({
                'id': 'act-adm-2',
                'title': f'{low_stock} Medicines Below Reorder Threshold',
                'severity': 'MEDIUM',
                'module': 'Pharmacy Inventory'
            })
        if pending_refs > 0:
            action_required.append({
                'id': 'act-adm-3',
                'title': f'{pending_refs} Outgoing Transfer Referrals Pending',
                'severity': 'MEDIUM',
                'module': 'Referral Network'
            })
    elif role == 'DOCTOR':
        if doctor_waiting > 0:
            action_required.append({
                'id': 'act-doc-1',
                'title': f'{doctor_waiting} Patients Waiting for Clinical Consultation',
                'severity': 'HIGH',
                'module': 'OPD Queue'
            })
        if emergency_count > 0:
            action_required.append({
                'id': 'act-doc-2',
                'title': f'{emergency_count} Red Flag / Emergency Patients Ready for Immediate Call',
                'severity': 'HIGH',
                'module': 'Emergency Triage'
            })
    elif role == 'NURSE':
        if triage_waiting > 0:
            action_required.append({
                'id': 'act-nur-1',
                'title': f'{triage_waiting} Patients Awaiting Vital Signs Screening',
                'severity': 'HIGH',
                'module': 'Triage Desk'
            })
        if emergency_count > 0:
            action_required.append({
                'id': 'act-nur-2',
                'title': f'{emergency_count} Emergency Triage Cases Flagged',
                'severity': 'HIGH',
                'module': 'Emergency Vitals'
            })
    elif role == 'LAB_TECHNICIAN':
        if lab_pending > 0:
            action_required.append({
                'id': 'act-lab-1',
                'title': f'{lab_pending} Lab Samples Pending Result Verification',
                'severity': 'HIGH',
                'module': 'Laboratory'
            })
    elif role == 'PHARMACIST':
        if pharmacy_waiting > 0:
            action_required.append({
                'id': 'act-pha-1',
                'title': f'{pharmacy_waiting} Prescriptions Pending FEFO Dispense',
                'severity': 'HIGH',
                'module': 'Pharmacy Queue'
            })
        if low_stock > 0:
            action_required.append({
                'id': 'act-pha-2',
                'title': f'{low_stock} Medicines Low on Stock',
                'severity': 'MEDIUM',
                'module': 'Stock Inventory'
            })

    return action_required


def get_full_dashboard_summary(user, requested_facility_id=None, target_date=None):
    """
    Authoritative single entry point for dashboard summaries across all 6 roles.
    Returns both the structured unified contract and backward-compatible top-level fields.
    """
    if target_date is None:
        target_date = datetime.date.today()
    elif isinstance(target_date, str):
        try:
            target_date = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            target_date = datetime.date.today()

    scope = get_facility_scope(user, requested_facility_id)
    target_fac_ids = scope['target_fac_ids']

    # Authoritative entity calculations
    patients = get_patient_metrics(target_fac_ids, target_date)
    v_metrics = get_visit_and_queue_metrics(target_fac_ids, target_date)
    laboratory = get_laboratory_metrics(target_fac_ids, target_date)
    pharmacy = get_pharmacy_and_inventory_metrics(target_fac_ids, target_date)
    referrals = get_referral_metrics(target_fac_ids)
    staff = get_staff_metrics(target_fac_ids)
    alerts = get_alert_metrics(target_fac_ids)
    facility_overview = get_facility_overview(scope['fac_qs'], target_date)

    role = getattr(user, 'role', '')
    action_required = get_action_required(role, v_metrics, laboratory, pharmacy, referrals)

    is_today = target_date == datetime.date.today()

    return {
        # Unified authoritative contract
        'date': target_date.strftime('%Y-%m-%d'),
        'is_today': is_today,
        'scope': {
            'role': role,
            'district': scope['district_name'],
            'district_id': scope['district_id'],
            'active_facility': scope['active_fac_name'],
            'active_facility_id': scope['active_facility_id'],
            'active_facility_type': scope['active_fac_type'],
            'facility_ids': target_fac_ids,
            'total_facilities': scope['total_facilities']
        },
        'patients': patients,
        'visits': v_metrics['visits'],
        'queues': v_metrics['queues'],
        'laboratory': laboratory,
        'pharmacy': pharmacy,
        'referrals': referrals,
        'staff': staff,
        'alerts': alerts,
        'facility_overview': facility_overview,
        'action_required': action_required,

        # Backward-compatible top-level keys
        'active_facility_id': scope['active_facility_id'],
        'active_facility': scope['active_fac_name'],
        'active_facility_type': scope['active_fac_type'],
        'total_facilities': scope['total_facilities'],
        'total_patients': patients['total'],
        'registered_today': patients['registered_today'],
        'new_opd_patients': patients['new_opd'],
        'total_registered_today': patients['registered_today'],
        'todays_opd': v_metrics['visits']['total'],
        'emergency_count': v_metrics['visits']['emergency'],
        'opd_stage_flow': {
            'registration': patients['registered_today'],
            'triage': v_metrics['queues']['triage_waiting'] + v_metrics['queues']['triage_in_progress'],
            'doctor': v_metrics['queues']['doctor_waiting'] + v_metrics['queues']['doctor_in_consultation'],
            'lab': laboratory['result_pending'],
            'pharmacy': pharmacy['waiting'],
            'completed': v_metrics['visits']['completed']
        },
        'staff_status': staff,
        'inventory_summary': {
            'total_medicines': pharmacy['medicine_master_total'],
            'stocked_medicines': pharmacy['stocked_medicines'],
            'low_stock': pharmacy['low_stock'],
            'low_stock_medicines': pharmacy['low_stock_medicines'],
            'low_stock_batches': pharmacy['low_stock_batches'],
            'out_of_stock': pharmacy['out_of_stock'],
            'expiring_soon': pharmacy['expiring_soon'],
            'expiring_soon_batches': pharmacy['expiring_soon'],
            'expired': pharmacy['expired'],
            'expired_batches': pharmacy['expired']
        },
        'referrals_summary': {
            'pending': referrals['pending'],
            'accepted': referrals['accepted'],
            'completed': referrals['completed']
        },
        'kpis': {
            'triage_waiting': v_metrics['queues']['triage_waiting'],
            'in_triage': v_metrics['queues']['triage_in_progress'],
            'vitals_pending': v_metrics['queues']['triage_waiting'],
            'doctor_waiting': v_metrics['queues']['doctor_waiting'],
            'in_consultation': v_metrics['queues']['doctor_in_consultation'],
            'lab_pending': laboratory['result_pending'],
            'pharmacy_waiting': pharmacy['waiting'],
            'completed': v_metrics['visits']['completed'],
            'emergency': v_metrics['visits']['emergency'],
            'registered_today': patients['registered_today'],
            'new_opd_patients': patients['new_opd'],
            'low_stock': pharmacy['low_stock'],
            'expiring_soon': pharmacy['expiring_soon'],
            'expired': pharmacy['expired']
        }
    }
