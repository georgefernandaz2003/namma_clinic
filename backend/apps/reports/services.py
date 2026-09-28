import datetime
from django.db import models
from django.db.models import Q, Sum, Count, Avg

from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription
from apps.laboratory.models import LabOrder, LabTestMaster
from apps.pharmacy.models import MedicineMaster, MedicineBatch, PurchaseOrder, InventoryTransaction, Vendor
from apps.referrals.models import Referral, FollowUp
from apps.ncd.models import NCDRecord
from apps.alerts.models import Alert
from apps.accounts.models import User

# Standardized application-wide threshold for expiring batches
EXPIRING_SOON_DAYS = 60


def get_stock_status(quantity, minimum_stock=25, reorder_level=None):
    """
    Authoritative single-source stock status rule:
    - OUT_OF_STOCK: quantity <= 0
    - LOW_STOCK: quantity > 0 and quantity <= threshold
    - NORMAL: quantity > threshold
    """
    qty = quantity or 0
    threshold = minimum_stock if (minimum_stock is not None and minimum_stock > 0) else (reorder_level or 0)
    if qty <= 0:
        return 'OUT_OF_STOCK'
    if threshold > 0 and qty <= threshold:
        return 'LOW_STOCK'
    return 'NORMAL'



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
            try:
                fac_id_int = int(requested_facility_id)
            except (ValueError, TypeError):
                fac_id_int = None

            if fac_id_int:
                selected_fac = district_fac_qs.filter(id=fac_id_int).first()
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
    """
    Authoritative patient metric calculations:
    - total: all registered patients at facility scope
    - registered_today: patients registered on the target_date
    - new_opd: distinct patients registered on target_date who attended OPD
    """
    total = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids).count()
    registered_today = Patient.objects.filter(
        registered_at_facility_id__in=target_fac_ids,
        registration_date=target_date
    ).count()

    new_opd = Visit.objects.filter(
        facility_id__in=target_fac_ids,
        opd_date=target_date,
        patient__registration_date=target_date
    ).values('patient').distinct().count()

    male_count = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids, gender__iexact='MALE').count()
    female_count = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids, gender__iexact='FEMALE').count()
    other_count = total - (male_count + female_count)

    return {
        'total': total,
        'registered_today': registered_today,
        'new_opd': new_opd,
        'male': male_count,
        'female': female_count,
        'other': max(0, other_count)
    }


def get_visit_and_queue_metrics(target_fac_ids, target_date, doctor_user=None):
    """
    Authoritative OPD visits and stage queue metrics:
    Single source of truth for:
    - TRIAGE_WAITING (WAITING_FOR_TRIAGE, WAITING)
    - IN_TRIAGE
    - DOCTOR_WAITING (WAITING_FOR_DOCTOR, TRIAGED, LAB_COMPLETED)
    - IN_CONSULTATION
    - LAB_WAITING (LAB_PENDING, LAB_IN_PROGRESS)
    - PHARMACY_WAITING (WAITING_FOR_PHARMACY, IN_PHARMACY)
    - COMPLETED
    """
    opd_visits_qs = Visit.objects.filter(facility_id__in=target_fac_ids, opd_date=target_date)
    if doctor_user:
        opd_visits_qs = opd_visits_qs.filter(assigned_doctor=doctor_user)

    total = opd_visits_qs.count()
    emergency = opd_visits_qs.filter(priority='EMERGENCY').count()
    completed = opd_visits_qs.filter(
        Q(status='COMPLETED') | Q(current_queue='COMPLETED')
    ).count()

    # Authoritative consultation completion tracking
    from apps.consultations.models import Consultation
    consult_qs = Consultation.objects.filter(facility_id__in=target_fac_ids, visit__opd_date=target_date)
    if doctor_user:
        consult_qs = consult_qs.filter(doctor=doctor_user)
    consultations_completed = consult_qs.count()
    doctor_completed_count = max(completed, consultations_completed) if doctor_user else completed

    # 1. Triage Queue
    triage_waiting = opd_visits_qs.filter(
        current_queue='TRIAGE',
        status__in=['WAITING', 'WAITING_FOR_TRIAGE']
    ).count()
    triage_in_progress = opd_visits_qs.filter(
        current_queue='TRIAGE',
        status='IN_TRIAGE'
    ).count()

    # 2. Doctor Queue (includes LAB_COMPLETED for re-consultation)
    doctor_waiting = opd_visits_qs.filter(
        current_queue='DOCTOR',
        status__in=['WAITING_FOR_DOCTOR', 'TRIAGED', 'LAB_COMPLETED']
    ).count()
    doctor_in_consultation = opd_visits_qs.filter(
        current_queue='DOCTOR',
        status='IN_CONSULTATION'
    ).count()

    # 3. Lab Queue (Visits in LAB stage)
    lab_pending_visits = opd_visits_qs.filter(
        current_queue='LAB',
        status__in=['LAB_PENDING', 'LAB_IN_PROGRESS']
    ).count()

    # 4. Pharmacy Queue (Visits in PHARMACY stage)
    pharmacy_waiting_visits = opd_visits_qs.filter(
        current_queue='PHARMACY',
        status__in=['WAITING_FOR_PHARMACY', 'IN_PHARMACY']
    ).count()

    total_waiting = triage_waiting + doctor_waiting + lab_pending_visits + pharmacy_waiting_visits

    return {
        'visits': {
            'total': total,
            'waiting': total_waiting,
            'in_consultation': doctor_in_consultation,
            'lab_pending': lab_pending_visits,
            'lab_pending_visits': lab_pending_visits,
            'pharmacy_waiting': pharmacy_waiting_visits,
            'pharmacy_waiting_visits': pharmacy_waiting_visits,
            'completed': doctor_completed_count,
            'consultations_completed': consultations_completed,
            'emergency': emergency
        },
        'queues': {
            'triage_waiting': triage_waiting,
            'triage_in_progress': triage_in_progress,
            'doctor_waiting': doctor_waiting,
            'doctor_in_consultation': doctor_in_consultation,
            'lab_pending': lab_pending_visits,
            'lab_pending_visits': lab_pending_visits,
            'pharmacy_waiting': pharmacy_waiting_visits,
            'pharmacy_waiting_visits': pharmacy_waiting_visits
        }
    }


def get_laboratory_metrics(target_fac_ids, target_date):
    """
    Authoritative laboratory order and diagnostic test metrics:
    Explicitly distinguishes between Lab Orders and Lab Visits.
    """
    lab_orders_qs = LabOrder.objects.filter(
        facility_id__in=target_fac_ids,
        order_date__date=target_date
    )

    total_orders = lab_orders_qs.count()
    ordered = lab_orders_qs.filter(status='ORDERED').count()
    sample_collected = lab_orders_qs.filter(status='SAMPLE_COLLECTED').count()
    result_pending = ordered + sample_collected
    verified = lab_orders_qs.filter(status='VERIFIED').count()

    # Laboratory Visits in queue
    lab_pending_visits = Visit.objects.filter(
        facility_id__in=target_fac_ids,
        opd_date=target_date,
        current_queue='LAB',
        status__in=['LAB_PENDING', 'LAB_IN_PROGRESS']
    ).count()

    return {
        'total_orders': total_orders,
        'ordered': ordered,
        'sample_collected': sample_collected,
        'result_pending': result_pending,
        'pending': ordered,
        'in_progress': sample_collected,
        'completed': verified,
        'verified': verified,
        'lab_pending_orders': result_pending,
        'lab_pending_visits': lab_pending_visits
    }


def get_pharmacy_and_inventory_metrics(target_fac_ids, target_date):
    """
    Authoritative pharmacy prescription orders and facility drug inventory metrics.
    Standardized:
    - Real-time inventory as of today (documented via inventory_as_of)
    - 60-day expiry window (EXPIRING_SOON_DAYS = 60)
    - Low-stock rule: facility medicine total quantity <= MedicineMaster.minimum_stock
    - Distinct master vs facility stock counts
    """
    # 1. Prescriptions for target_date
    rx_qs = Prescription.objects.filter(
        facility_id__in=target_fac_ids,
        date=target_date
    )
    total_prescriptions = rx_qs.count()
    pending_prescriptions = rx_qs.filter(status__in=['PENDING', 'ACTIVE']).count()
    partially_dispensed = rx_qs.filter(status='PARTIALLY_DISPENSED').count()
    dispensed_prescriptions = rx_qs.filter(status='DISPENSED').count()

    pharmacy_waiting_visits = Visit.objects.filter(
        facility_id__in=target_fac_ids,
        opd_date=target_date,
        current_queue='PHARMACY',
        status__in=['WAITING_FOR_PHARMACY', 'IN_PHARMACY']
    ).count()

    # 2. Inventory (Real-time snapshot as of current date)
    today = datetime.date.today()
    expiring_threshold = today + datetime.timedelta(days=EXPIRING_SOON_DAYS)

    inventory_batches = MedicineBatch.objects.filter(facility_id__in=target_fac_ids)
    all_master_meds = MedicineMaster.objects.all()
    total_medicine_master_records = all_master_meds.count()

    stocked_medicines_ids = set(inventory_batches.values_list('medicine_id', flat=True).distinct())
    total_medicines_stocked_at_facility = len(stocked_medicines_ids)

    low_stock_medicines = 0
    out_of_stock_medicines = 0

    for m in all_master_meds:
        m_batches = inventory_batches.filter(medicine=m, status__in=['ACTIVE', 'LOW_STOCK', 'EXPIRING_SOON'])
        tot_qty = m_batches.aggregate(t=Sum('quantity'))['t'] or 0
        st = get_stock_status(tot_qty, m.minimum_stock, m.reorder_level)
        if st == 'OUT_OF_STOCK':
            out_of_stock_medicines += 1
        elif st == 'LOW_STOCK':
            low_stock_medicines += 1

    low_stock_batches = 0
    for b in inventory_batches.filter(quantity__gt=0).select_related('medicine'):
        threshold = b.medicine.minimum_stock or b.medicine.reorder_level or 0
        if threshold > 0 and b.quantity <= threshold:
            low_stock_batches += 1

    expiring_soon_batches = inventory_batches.filter(
        quantity__gt=0,
        expiry_date__gte=today,
        expiry_date__lte=expiring_threshold
    ).count()

    expired_batches = inventory_batches.filter(
        Q(expiry_date__lt=today) | Q(status='EXPIRED')
    ).count()

    return {
        # Prescription metrics
        'total_prescriptions': total_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'partially_dispensed': partially_dispensed,
        'dispensed_prescriptions': dispensed_prescriptions,
        'waiting': pending_prescriptions + partially_dispensed,
        'dispensed': dispensed_prescriptions,
        'pharmacy_waiting_visits': pharmacy_waiting_visits,

        # Real-time inventory metrics
        'inventory_as_of': today.isoformat(),
        'total_medicine_master_records': total_medicine_master_records,
        'total_medicines_stocked_at_facility': total_medicines_stocked_at_facility,
        'total_medicines': total_medicine_master_records,
        'stocked_medicines': total_medicines_stocked_at_facility,
        'out_of_stock_medicines': out_of_stock_medicines,
        'out_of_stock': out_of_stock_medicines,
        'low_stock_medicines': low_stock_medicines,
        'low_stock': low_stock_medicines,
        'low_stock_batches': low_stock_batches,
        'expiring_soon_batches': expiring_soon_batches,
        'expiring_soon': expiring_soon_batches,
        'expired_batches': expired_batches,
        'expired': expired_batches
    }


def get_referral_metrics(target_fac_ids):
    """
    Authoritative cross-facility referral metrics with clear source vs destination semantics:
    - pending_outgoing: source facility = current scope AND status in pending statuses
    - incoming: destination facility = current scope AND status in active/incoming statuses
    - completed: source or destination in scope AND status completed
    - total: total referrals involving the facility scope
    """
    ref_qs = Referral.objects.filter(
        Q(source_facility_id__in=target_fac_ids) | Q(destination_facility_id__in=target_fac_ids)
    ).distinct()

    pending_outgoing = Referral.objects.filter(
        source_facility_id__in=target_fac_ids,
        status__in=['CREATED', 'IN_TRANSIT']
    ).count()

    incoming = Referral.objects.filter(
        destination_facility_id__in=target_fac_ids,
        status__in=['CREATED', 'ACCEPTED', 'IN_TRANSIT', 'REACHED', 'UNDER_TREATMENT']
    ).count()

    accepted = ref_qs.filter(status='ACCEPTED').count()
    completed = ref_qs.filter(status__in=['COMPLETED', 'CLOSED']).count()

    return {
        'pending_outgoing': pending_outgoing,
        'incoming': incoming,
        'pending': pending_outgoing,
        'accepted': accepted,
        'completed': completed,
        'total': ref_qs.count()
    }


def get_staff_metrics(target_fac_ids):
    """
    Authoritative staff count metrics partitioned by role and is_active.
    Enforces active + inactive == total for every role.
    """
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

    doctors = _role_stat('DOCTOR')
    nurses = _role_stat('NURSE')
    lab_techs = _role_stat('LAB_TECHNICIAN')
    pharmacists = _role_stat('PHARMACIST')
    admins = _role_stat('HOSPITAL_ADMIN')

    total_active = doctors['active'] + nurses['active'] + lab_techs['active'] + pharmacists['active'] + admins['active']

    return {
        'doctors': doctors,
        'nurses': nurses,
        'lab_technicians': lab_techs,
        'pharmacists': pharmacists,
        'admins': admins,
        'total_active_staff': total_active
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
        'active': new_count + ack_count,
        'total': alert_qs.count()
    }


def get_facility_overview(fac_qs, target_date):
    """
    Facility Operation Overview: Evaluates each healthcare facility using
    the EXACT same shared metric calculations used by the rest of the dashboard.
    """
    facility_overview = []
    for fac in fac_qs:
        v_met = get_visit_and_queue_metrics([fac.id], target_date)
        pats = v_met['visits']['total']
        wait = v_met['visits']['waiting']
        refs = get_referral_metrics([fac.id])['pending_outgoing']
        alerts_cnt = get_alert_metrics([fac.id])['new']

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
                'title': f'{lab_pending} Lab Orders Pending Sample or Result Verification',
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

    role = getattr(user, 'role', '')
    doctor_scope = user if role == 'DOCTOR' else None

    # Authoritative entity calculations
    patients = get_patient_metrics(target_fac_ids, target_date)
    v_metrics = get_visit_and_queue_metrics(target_fac_ids, target_date, doctor_user=doctor_scope)
    laboratory = get_laboratory_metrics(target_fac_ids, target_date)
    pharmacy = get_pharmacy_and_inventory_metrics(target_fac_ids, target_date)
    referrals = get_referral_metrics(target_fac_ids)
    staff = get_staff_metrics(target_fac_ids)
    alerts = get_alert_metrics(target_fac_ids)
    facility_overview = get_facility_overview(scope['fac_qs'], target_date)

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

        # Role-specific summary contracts
        'pharmacy_summary': {
            'total_prescriptions': pharmacy['total_prescriptions'],
            'pending_prescriptions': pharmacy['pending_prescriptions'],
            'partially_dispensed': pharmacy['partially_dispensed'],
            'dispensed_prescriptions': pharmacy['dispensed_prescriptions'],
            'low_stock': pharmacy['low_stock'],
            'out_of_stock': pharmacy['out_of_stock'],
            'expiring_soon': pharmacy['expiring_soon'],
            'expired': pharmacy['expired']
        },
        'lab_summary': {
            'total_orders': laboratory['total_orders'],
            'ordered': laboratory['ordered'],
            'sample_collected': laboratory['sample_collected'],
            'result_pending': laboratory['result_pending'],
            'verified': laboratory['verified'],
            'completed': laboratory['completed'],
            'lab_pending_orders': laboratory['lab_pending_orders'],
            'lab_pending_visits': laboratory['lab_pending_visits']
        },
        'queue_summary': {
            'todays_opd': v_metrics['visits']['total'],
            'waiting': v_metrics['visits']['waiting'],
            'triage_waiting': v_metrics['queues']['triage_waiting'],
            'triage_in_progress': v_metrics['queues']['triage_in_progress'],
            'doctor_waiting': v_metrics['queues']['doctor_waiting'],
            'doctor_in_consultation': v_metrics['queues']['doctor_in_consultation'],
            'lab_pending': v_metrics['queues']['lab_pending'],
            'pharmacy_waiting': v_metrics['queues']['pharmacy_waiting'],
            'completed': v_metrics['visits']['completed'],
            'emergency': v_metrics['visits']['emergency']
        },

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
            'inventory_as_of': pharmacy['inventory_as_of'],
            'total_medicines': pharmacy['total_medicine_master_records'],
            'total_medicine_master_records': pharmacy['total_medicine_master_records'],
            'total_medicines_stocked_at_facility': pharmacy['total_medicines_stocked_at_facility'],
            'stocked_medicines': pharmacy['total_medicines_stocked_at_facility'],
            'low_stock': pharmacy['low_stock_medicines'],
            'low_stock_medicines': pharmacy['low_stock_medicines'],
            'low_stock_batches': pharmacy['low_stock_batches'],
            'out_of_stock': pharmacy['out_of_stock_medicines'],
            'out_of_stock_medicines': pharmacy['out_of_stock_medicines'],
            'expiring_soon': pharmacy['expiring_soon_batches'],
            'expiring_soon_batches': pharmacy['expiring_soon_batches'],
            'expired': pharmacy['expired_batches'],
            'expired_batches': pharmacy['expired_batches']
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
            'low_stock': pharmacy['low_stock_medicines'],
            'expiring_soon': pharmacy['expiring_soon_batches'],
            'expired': pharmacy['expired_batches']
        }
    }


# ==============================================================================
# ENHANCED HOSPITAL ADMIN REPORTS SERVICE
# ==============================================================================

def get_period_date_range(period, target_date=None):
    """
    Standardized period definitions across all reports:
    - DAY: Selected calendar date.
    - WEEK: Monday 00:00 through Sunday 23:59 for the selected week.
    - MONTH: First day through last day of selected month.
    - YEAR: January 1 through December 31 of selected year.
    """
    if target_date is None:
        target_date = datetime.date.today()
    elif isinstance(target_date, str):
        try:
            target_date = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            target_date = datetime.date.today()

    period = (period or 'day').lower()

    if period == 'day':
        start_date = target_date
        end_date = target_date
    elif period == 'week':
        start_date = target_date - datetime.timedelta(days=target_date.weekday())
        end_date = start_date + datetime.timedelta(days=6)
    elif period == 'month':
        start_date = target_date.replace(day=1)
        if start_date.month == 12:
            next_month = datetime.date(start_date.year + 1, 1, 1)
        else:
            next_month = datetime.date(start_date.year, start_date.month + 1, 1)
        end_date = next_month - datetime.timedelta(days=1)
    elif period == 'year':
        start_date = datetime.date(target_date.year, 1, 1)
        end_date = datetime.date(target_date.year, 12, 31)
    else:
        start_date = target_date
        end_date = target_date

    return start_date, end_date


def get_previous_period_date_range(period, start_date, end_date):
    """
    Computes prior period range for period-over-period comparison:
    - DAY: Previous calendar day.
    - WEEK: Monday to Sunday of previous week (7 days prior).
    - MONTH: Full calendar month immediately preceding start_date.
    - YEAR: Full calendar year immediately preceding start_date.
    """
    period = (period or 'day').lower()
    if period == 'day':
        return start_date - datetime.timedelta(days=1), end_date - datetime.timedelta(days=1)
    elif period == 'week':
        return start_date - datetime.timedelta(days=7), end_date - datetime.timedelta(days=7)
    elif period == 'month':
        prev_month_end = start_date - datetime.timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        return prev_month_start, prev_month_end
    elif period == 'year':
        return datetime.date(start_date.year - 1, 1, 1), datetime.date(start_date.year - 1, 12, 31)
    return start_date - datetime.timedelta(days=1), end_date - datetime.timedelta(days=1)


def calculate_metric_change(current, previous):
    """
    Calculates change difference and percentage.
    Guards against division by zero: if previous == 0, shows "+X" instead of inflated %.
    """
    diff = current - previous
    if previous == 0:
        return {
            'current': current,
            'previous': previous,
            'difference': diff,
            'percent': None,
            'display': f"+{diff}" if diff > 0 else (str(diff) if diff < 0 else "0")
        }
    pct = round(((current - previous) / previous) * 100, 1)
    disp = f"+{pct}%" if pct > 0 else f"{pct}%"
    return {
        'current': current,
        'previous': previous,
        'difference': diff,
        'percent': pct,
        'display': disp
    }


def get_opd_patient_report_metrics(target_fac_ids, start_date, end_date, period='day'):
    """
    Section 4: OPD & Patient Report.
    Returns demographics, age groups, visit breakdown, and time/period-based OPD trend.
    """
    all_registered_patients = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids)
    total_registered = all_registered_patients.count()

    # New patients registered within the selected reporting period
    new_patients = all_registered_patients.filter(
        registration_date__gte=start_date,
        registration_date__lte=end_date
    ).count()

    # Visits in selected period
    visits_qs = Visit.objects.filter(
        facility_id__in=target_fac_ids,
        opd_date__gte=start_date,
        opd_date__lte=end_date
    ).select_related('patient')

    total_opd_visits = visits_qs.count()
    completed_visits = visits_qs.filter(Q(status='COMPLETED') | Q(current_queue='COMPLETED')).count()
    cancelled_visits = visits_qs.filter(status='CANCELLED').count()
    emergency_visits = visits_qs.filter(priority='EMERGENCY').count()

    # Returning patients: distinct patients visited in period who registered prior to start_date
    returning_patients = visits_qs.filter(
        patient__registration_date__lt=start_date
    ).values('patient').distinct().count()

    # Demographics across all facility registered patients
    male_count = all_registered_patients.filter(gender__iexact='MALE').count()
    female_count = all_registered_patients.filter(gender__iexact='FEMALE').count()
    other_count = max(0, total_registered - (male_count + female_count))

    # Age Groups: 0-5, 6-18, 19-30, 31-45, 46-60, 60+
    age_0_5 = all_registered_patients.filter(age__gte=0, age__lte=5).count()
    age_6_18 = all_registered_patients.filter(age__gte=6, age__lte=18).count()
    age_19_30 = all_registered_patients.filter(age__gte=19, age__lte=30).count()
    age_31_45 = all_registered_patients.filter(age__gte=31, age__lte=45).count()
    age_46_60 = all_registered_patients.filter(age__gte=46, age__lte=60).count()
    age_60_plus = all_registered_patients.filter(age__gt=60).count()

    # OPD Trend Chart
    trend = []
    period = (period or 'day').lower()

    if period == 'day':
        # Hourly breakdown between 08:00 and 18:00
        hour_labels = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]
        for h_str in hour_labels:
            h = int(h_str.split(':')[0])
            cnt = visits_qs.filter(arrival_time__hour=h).count()
            trend.append({'label': h_str, 'visits': cnt})
    elif period == 'week':
        # 7 days Monday to Sunday
        curr = start_date
        while curr <= end_date:
            cnt = visits_qs.filter(opd_date=curr).count()
            trend.append({
                'label': curr.strftime('%a'),
                'date': curr.strftime('%Y-%m-%d'),
                'visits': cnt
            })
            curr += datetime.timedelta(days=1)
    elif period == 'month':
        # Daily distribution throughout the month
        curr = start_date
        while curr <= end_date:
            cnt = visits_qs.filter(opd_date=curr).count()
            trend.append({
                'label': str(curr.day),
                'date': curr.strftime('%Y-%m-%d'),
                'visits': cnt
            })
            curr += datetime.timedelta(days=1)
    elif period == 'year':
        # 12 months Jan through Dec
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for m_idx, m_name in enumerate(month_names, start=1):
            cnt = visits_qs.filter(opd_date__month=m_idx).count()
            trend.append({'label': m_name, 'visits': cnt})

    return {
        'total_registered_patients': total_registered,
        'new_patients': new_patients,
        'returning_patients': returning_patients,
        'total_opd_visits': total_opd_visits,
        'completed_visits': completed_visits,
        'cancelled_visits': cancelled_visits,
        'emergency_visits': emergency_visits,
        'demographics': {
            'male': male_count,
            'female': female_count,
            'other': other_count
        },
        'age_groups': {
            '0_5': age_0_5,
            '6_18': age_6_18,
            '19_30': age_19_30,
            '31_45': age_31_45,
            '46_60': age_46_60,
            '60_plus': age_60_plus
        },
        'trend': trend
    }


def get_queue_service_report_metrics(target_fac_ids, start_date, end_date):
    """
    Section 5: Queue & Service Report.
    Stages: Registration, Triage, Doctor, Laboratory, Pharmacy, Completed.
    Computes Waiting, In Progress, Completed, Average Waiting Time, Peak Queue Period.
    """
    visits_qs = Visit.objects.filter(
        facility_id__in=target_fac_ids,
        opd_date__gte=start_date,
        opd_date__lte=end_date
    )

    # 1. Registration
    reg_completed = visits_qs.count()

    # 2. Triage
    triage_waiting = visits_qs.filter(current_queue='TRIAGE', status__in=['WAITING', 'WAITING_FOR_TRIAGE']).count()
    triage_in_progress = visits_qs.filter(current_queue='TRIAGE', status='IN_TRIAGE').count()
    triage_completed = visits_qs.filter(triage_end_time__isnull=False).count() or visits_qs.exclude(current_queue='TRIAGE').count()

    # 3. Doctor
    doc_waiting = visits_qs.filter(current_queue='DOCTOR', status__in=['WAITING_FOR_DOCTOR', 'TRIAGED', 'LAB_COMPLETED']).count()
    doc_in_progress = visits_qs.filter(current_queue='DOCTOR', status='IN_CONSULTATION').count()
    doc_completed = visits_qs.filter(
        Q(status='COMPLETED') | Q(current_queue__in=['LAB', 'PHARMACY', 'COMPLETED'])
    ).count()

    # 4. Laboratory
    lab_waiting = visits_qs.filter(current_queue='LAB', status='LAB_PENDING').count()
    lab_in_progress = visits_qs.filter(current_queue='LAB', status='LAB_IN_PROGRESS').count()
    lab_completed = visits_qs.filter(status='LAB_COMPLETED').count()

    # 5. Pharmacy
    pharm_waiting = visits_qs.filter(current_queue='PHARMACY', status='WAITING_FOR_PHARMACY').count()
    pharm_in_progress = visits_qs.filter(current_queue='PHARMACY', status='IN_PHARMACY').count()
    pharm_completed = visits_qs.filter(status='COMPLETED', current_queue='COMPLETED').count()

    # 6. Overall Completed
    overall_completed = visits_qs.filter(Q(status='COMPLETED') | Q(current_queue='COMPLETED')).count()

    # Timestamp-derived Average Waiting Times (only when reliable timestamps exist)
    triage_wait_deltas = []
    doctor_wait_deltas = []
    total_visit_deltas = []

    for v in visits_qs.filter(arrival_time__isnull=False)[:500]:
        if v.triage_start_time and v.triage_start_time > v.arrival_time:
            triage_wait_deltas.append((v.triage_start_time - v.arrival_time).total_seconds() / 60.0)
        start_doc = v.consultation_start_time
        ref_time = v.triage_end_time or v.arrival_time
        if start_doc and ref_time and start_doc > ref_time:
            doctor_wait_deltas.append((start_doc - ref_time).total_seconds() / 60.0)
        if v.completed_time and v.completed_time > v.arrival_time:
            total_visit_deltas.append((v.completed_time - v.arrival_time).total_seconds() / 60.0)

    avg_triage_wait = round(sum(triage_wait_deltas) / len(triage_wait_deltas), 1) if triage_wait_deltas else None
    avg_doctor_wait = round(sum(doctor_wait_deltas) / len(doctor_wait_deltas), 1) if doctor_wait_deltas else None
    avg_total_visit = round(sum(total_visit_deltas) / len(total_visit_deltas), 1) if total_visit_deltas else None

    # Peak Queue Period based on arrival hour frequencies
    peak_queue_period = "N/A"
    hour_counts = {}
    for v in visits_qs.filter(arrival_time__isnull=False):
        h = v.arrival_time.hour
        hour_counts[h] = hour_counts.get(h, 0) + 1

    if hour_counts:
        peak_h = max(hour_counts, key=hour_counts.get)
        peak_queue_period = f"{peak_h:02d}:00 - {(peak_h + 1):02d}:00"

    return {
        'stages': {
            'registration': {'waiting': 0, 'in_progress': 0, 'completed': reg_completed},
            'triage': {'waiting': triage_waiting, 'in_progress': triage_in_progress, 'completed': triage_completed},
            'doctor': {'waiting': doc_waiting, 'in_progress': doc_in_progress, 'completed': doc_completed},
            'laboratory': {'waiting': lab_waiting, 'in_progress': lab_in_progress, 'completed': lab_completed},
            'pharmacy': {'waiting': pharm_waiting, 'in_progress': pharm_in_progress, 'completed': pharm_completed},
            'completed': {'waiting': 0, 'in_progress': 0, 'completed': overall_completed}
        },
        'avg_triage_wait_minutes': avg_triage_wait,
        'avg_doctor_wait_minutes': avg_doctor_wait,
        'avg_total_duration_minutes': avg_total_visit,
        'peak_queue_period': peak_queue_period
    }


def get_doctor_staff_report_metrics(target_fac_ids, start_date, end_date):
    """
    Section 6: Doctor & Staff Report.
    Breakdown of staff roles (active/inactive) and authenticated Doctor activity in reporting period.
    """
    staff_qs = User.objects.filter(assigned_facility_id__in=target_fac_ids)

    def _role_breakdown(role_code):
        rqs = staff_qs.filter(role=role_code)
        act = rqs.filter(is_active=True).count()
        inact = rqs.filter(is_active=False).count()
        return {'active': act, 'inactive': inact, 'total': act + inact}

    doctors_stat = _role_breakdown('DOCTOR')
    nurses_stat = _role_breakdown('NURSE')
    lab_stat = _role_breakdown('LAB_TECHNICIAN')
    pharm_stat = _role_breakdown('PHARMACIST')
    admin_stat = _role_breakdown('HOSPITAL_ADMIN')

    total_staff = staff_qs.count()
    active_staff = staff_qs.filter(is_active=True).count()
    inactive_staff = staff_qs.filter(is_active=False).count()

    # Individual Doctor Activity Breakdown
    doctor_users = staff_qs.filter(role='DOCTOR').order_by('full_name')
    doctor_activity = []

    for doc in doctor_users:
        consults = Consultation.objects.filter(
            doctor=doc,
            facility_id__in=target_fac_ids,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        consult_count = consults.count()
        patients_consulted = consults.values('patient').distinct().count()

        lab_orders_count = LabOrder.objects.filter(
            doctor=doc,
            facility_id__in=target_fac_ids,
            order_date__date__gte=start_date,
            order_date__date__lte=end_date
        ).count()

        rx_count = Prescription.objects.filter(
            doctor=doc,
            facility_id__in=target_fac_ids,
            date__gte=start_date,
            date__lte=end_date
        ).count()

        referrals_count = Referral.objects.filter(
            referring_doctor=doc,
            source_facility_id__in=target_fac_ids,
            referral_date__date__gte=start_date,
            referral_date__date__lte=end_date
        ).count()

        doctor_activity.append({
            'doctor_id': doc.id,
            'name': doc.full_name or doc.username,
            'username': doc.username,
            'is_active': doc.is_active,
            'patients_consulted': patients_consulted,
            'consultations_completed': consult_count,
            'lab_orders': lab_orders_count,
            'prescriptions': rx_count,
            'referrals': referrals_count
        })

    return {
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': inactive_staff,
        'roles': {
            'doctors': doctors_stat,
            'nurses': nurses_stat,
            'lab_technicians': lab_stat,
            'pharmacists': pharm_stat,
            'admins': admin_stat
        },
        'doctor_activity': doctor_activity
    }


def get_laboratory_report_metrics_for_period(target_fac_ids, start_date, end_date):
    """
    Section 7: Laboratory Report.
    Orders, status breakdown, and diagnostics breakdown by LabTestMaster.
    """
    lab_orders = LabOrder.objects.filter(
        facility_id__in=target_fac_ids,
        order_date__date__gte=start_date,
        order_date__date__lte=end_date
    ).select_related('test_master')

    total_orders = lab_orders.count()
    ordered = lab_orders.filter(status='ORDERED').count()
    samples_collected = lab_orders.filter(status='SAMPLE_COLLECTED').count()
    in_progress = lab_orders.filter(status__in=['SAMPLE_COLLECTED', 'RESULT_ENTRY']).count()
    results_pending = lab_orders.filter(status__in=['ORDERED', 'SAMPLE_COLLECTED', 'RESULT_ENTRY']).count()
    verified_results = lab_orders.filter(status='VERIFIED').count()
    results_completed = verified_results
    cancelled = lab_orders.filter(status='CANCELLED').count()

    # Breakdown by Lab Test Master
    test_breakdown = []
    for test in LabTestMaster.objects.all():
        t_orders = lab_orders.filter(test_master=test)
        cnt = t_orders.count()
        test_breakdown.append({
            'code': test.code,
            'name': test.name,
            'category': test.category,
            'unit': test.unit,
            'reference_range': test.reference_range,
            'total_orders': cnt,
            'verified': t_orders.filter(status='VERIFIED').count(),
            'pending': t_orders.filter(status__in=['ORDERED', 'SAMPLE_COLLECTED', 'RESULT_ENTRY']).count()
        })

    return {
        'total_orders': total_orders,
        'samples_collected': samples_collected,
        'in_progress': in_progress,
        'results_pending': results_pending,
        'results_completed': results_completed,
        'verified_results': verified_results,
        'cancelled_tests': cancelled,
        'test_breakdown': test_breakdown
    }


def get_pharmacy_report_metrics_for_period(target_fac_ids, start_date, end_date, period='day'):
    """
    Sections 8–14: Complete Pharmacy Report.
    Prescriptions, Dispensing, Inventory, Purchases, Vendors, Stock Movement & Consumption,
    Top Dispensed Medicines, Expiry Monitoring, Low Stock Report.
    100% reconciled with Pharmacy module.
    """
    today = datetime.date.today()

    # 1. Prescriptions in reporting period
    rx_qs = Prescription.objects.filter(
        facility_id__in=target_fac_ids,
        date__gte=start_date,
        date__lte=end_date
    )
    total_prescriptions = rx_qs.count()
    pending_rx = rx_qs.filter(status__in=['PENDING', 'ACTIVE']).count()
    partially_dispensed_rx = rx_qs.filter(status='PARTIALLY_DISPENSED').count()
    dispensed_rx = rx_qs.filter(status='DISPENSED').count()
    cancelled_rx = rx_qs.filter(status='CANCELLED').count()

    # 2. Dispensing Transactions in reporting period
    tx_period = InventoryTransaction.objects.filter(
        facility_id__in=target_fac_ids,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('medicine', 'batch')

    dispense_tx = tx_period.filter(transaction_type='DISPENSED')
    total_medicines_dispensed = dispense_tx.aggregate(t=Sum('quantity'))['t'] or 0
    total_dispensing_transactions = dispense_tx.count()
    patients_served = dispense_tx.values('reference_id').distinct().count()

    # Top Dispensed Medicines (backend aggregated)
    top_dispensed = []
    top_records = dispense_tx.values('medicine_id', 'medicine__generic_name', 'medicine__brand_name', 'medicine__unit').annotate(
        qty=Sum('quantity'),
        rx_count=Count('reference_id', distinct=True)
    ).order_by('-qty')[:15]

    for tr in top_records:
        top_dispensed.append({
            'medicine_id': tr['medicine_id'],
            'generic_name': tr['medicine__generic_name'],
            'brand_name': tr.get('medicine__brand_name') or '',
            'unit': tr.get('medicine__unit') or 'Units',
            'quantity_dispensed': tr['qty'],
            'prescriptions_count': tr['rx_count']
        })

    # 3. Real-Time Inventory Snapshot
    batch_qs = MedicineBatch.objects.filter(facility_id__in=target_fac_ids).select_related('medicine')
    all_master = MedicineMaster.objects.all()
    total_medicine_master = all_master.count()
    stocked_ids = set(batch_qs.values_list('medicine_id', flat=True).distinct())
    total_medicines_stocked = len(stocked_ids)

    # Active available batches (unexpired and quantity > 0)
    unexpired_batches = batch_qs.filter(
        quantity__gt=0,
        expiry_date__gt=today
    ).exclude(status='EXPIRED')
    total_available_units = unexpired_batches.aggregate(t=Sum('quantity'))['t'] or 0

    # Low stock & Out of stock using authoritative get_stock_status
    low_stock_medicines = 0
    out_of_stock_medicines = 0
    low_stock_table = []

    for m in all_master:
        m_batches = batch_qs.filter(medicine=m, status__in=['ACTIVE', 'LOW_STOCK', 'EXPIRING_SOON'])
        tot_qty = m_batches.aggregate(t=Sum('quantity'))['t'] or 0
        st = get_stock_status(tot_qty, m.minimum_stock, m.reorder_level)
        if st == 'OUT_OF_STOCK':
            out_of_stock_medicines += 1
        elif st == 'LOW_STOCK':
            low_stock_medicines += 1

        low_stock_table.append({
            'id': m.id,
            'generic_name': m.generic_name,
            'brand_name': m.brand_name,
            'category': m.category,
            'unit': m.unit,
            'current_stock': tot_qty,
            'minimum_stock': m.minimum_stock,
            'reorder_level': m.reorder_level,
            'status': st
        })

    # Expiry Monitoring (Strictly actual batch expiry dates)
    expired_batches_qs = batch_qs.filter(Q(expiry_date__lte=today) | Q(status='EXPIRED'))
    expired_batches_count = expired_batches_qs.count()

    date_7d = today + datetime.timedelta(days=7)
    date_30d = today + datetime.timedelta(days=30)
    date_60d = today + datetime.timedelta(days=60)
    date_90d = today + datetime.timedelta(days=90)

    active_exp_batches = batch_qs.filter(quantity__gt=0, expiry_date__gt=today).exclude(status='EXPIRED')

    exp_7_count = active_exp_batches.filter(expiry_date__lte=date_7d).count()
    exp_30_count = active_exp_batches.filter(expiry_date__gt=date_7d, expiry_date__lte=date_30d).count()
    exp_60_count = active_exp_batches.filter(expiry_date__gt=date_30d, expiry_date__lte=date_60d).count()
    exp_90_count = active_exp_batches.filter(expiry_date__gt=date_60d, expiry_date__lte=date_90d).count()
    expiring_soon_count = exp_7_count + exp_30_count + exp_60_count

    # Detailed list of expiring/expired batches for table
    monitoring_batches_list = []
    for b in batch_qs.filter(Q(expiry_date__lte=date_90d) | Q(status='EXPIRED')).order_by('expiry_date'):
        days_left = (b.expiry_date - today).days
        is_exp = b.expiry_date <= today or b.status == 'EXPIRED'
        if is_exp:
            cat = 'EXPIRED'
        elif days_left <= 7:
            cat = 'EXPIRES_7_DAYS'
        elif days_left <= 30:
            cat = 'EXPIRES_30_DAYS'
        elif days_left <= 60:
            cat = 'EXPIRES_60_DAYS'
        else:
            cat = 'EXPIRES_90_DAYS'

        monitoring_batches_list.append({
            'batch_id': b.id,
            'medicine_name': b.medicine.generic_name,
            'brand_name': b.medicine.brand_name,
            'batch_number': b.batch_number,
            'quantity': b.quantity,
            'expiry_date': b.expiry_date.strftime('%Y-%m-%d'),
            'days_remaining': days_left,
            'status': 'EXPIRED' if is_exp else ('EXPIRING_SOON' if days_left <= 60 else 'ACTIVE'),
            'category': cat
        })

    # 4. Purchases in reporting period
    po_qs = PurchaseOrder.objects.filter(
        facility_id__in=target_fac_ids,
        order_date__gte=start_date,
        order_date__lte=end_date
    ).select_related('vendor')

    total_pos = po_qs.count()
    po_draft = po_qs.filter(status='DRAFT').count()
    po_pending = po_qs.filter(status__in=['PENDING_APPROVAL', 'PENDING']).count()
    po_approved = po_qs.filter(status='APPROVED').count()
    po_ordered = po_qs.filter(status='ORDERED').count()
    po_partially_received = po_qs.filter(status='PARTIALLY_RECEIVED').count()
    po_received = po_qs.filter(status='RECEIVED').count()
    po_cancelled = po_qs.filter(status='CANCELLED').count()

    procurement_amount = float(
        po_qs.filter(status__in=['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED']).aggregate(t=Sum('total_amount'))['t'] or 0.0
    )

    po_list = []
    for po in po_qs.order_by('-order_date')[:50]:
        po_list.append({
            'id': po.id,
            'po_number': po.po_number,
            'vendor_name': po.vendor.vendor_name if po.vendor else 'Direct KSMSCL',
            'order_date': po.order_date.strftime('%Y-%m-%d'),
            'status': po.status,
            'total_amount': float(po.total_amount)
        })

    # 5. Vendors
    vendor_qs = Vendor.objects.filter(Q(facility_id__in=target_fac_ids) | Q(facility__isnull=True))
    active_vendors = vendor_qs.filter(status='ACTIVE').count()
    inactive_vendors = vendor_qs.filter(status='INACTIVE').count()

    # 6. Reconciled Stock Movement & Consumption
    # Opening Stock + Received - Dispensed +/- Adjustments = Closing Stock
    stock_movement_items = []
    tot_rec = 0
    tot_disp = 0
    tot_adj = 0
    tot_close = 0
    tot_open = 0

    for m in all_master:
        m_batches = batch_qs.filter(medicine=m, quantity__gt=0, expiry_date__gt=today).exclude(status='EXPIRED')
        closing = m_batches.aggregate(t=Sum('quantity'))['t'] or 0

        m_tx = tx_period.filter(medicine=m)
        rec = m_tx.filter(transaction_type='PURCHASE_RECEIVED').aggregate(t=Sum('quantity'))['t'] or 0
        disp = m_tx.filter(transaction_type='DISPENSED').aggregate(t=Sum('quantity'))['t'] or 0
        adj = m_tx.filter(transaction_type='ADJUSTMENT').aggregate(t=Sum('quantity'))['t'] or 0

        opening = max(0, closing - rec + disp - adj)

        tot_rec += rec
        tot_disp += disp
        tot_adj += adj
        tot_close += closing
        tot_open += opening

        if closing > 0 or rec > 0 or disp > 0 or adj > 0:
            stock_movement_items.append({
                'medicine_id': m.id,
                'medicine': m.generic_name,
                'brand_name': m.brand_name,
                'dosage_form': m.dosage_form,
                'unit': m.unit,
                'opening_stock': opening,
                'received': rec,
                'dispensed': disp,
                'adjusted': adj,
                'closing_stock': closing
            })

    stock_movement_items.sort(key=lambda x: (x['dispensed'], x['closing_stock']), reverse=True)

    return {
        'prescriptions': {
            'total_prescriptions': total_prescriptions,
            'pending': pending_rx,
            'partially_dispensed': partially_dispensed_rx,
            'dispensed': dispensed_rx,
            'cancelled': cancelled_rx
        },
        'dispensing': {
            'total_medicines_dispensed': total_medicines_dispensed,
            'total_dispensing_transactions': total_dispensing_transactions,
            'patients_served': patients_served,
            'top_dispensed_medicines': top_dispensed
        },
        'inventory': {
            'total_medicines_master': total_medicine_master,
            'medicines_currently_stocked': total_medicines_stocked,
            'total_available_units': total_available_units,
            'low_stock_medicines': low_stock_medicines,
            'out_of_stock_medicines': out_of_stock_medicines,
            'expiring_soon_batches': expiring_soon_count,
            'expired_batches': expired_batches_count
        },
        'purchases': {
            'total_purchase_orders': total_pos,
            'draft': po_draft,
            'pending_approval': po_pending,
            'approved': po_approved,
            'ordered': po_ordered,
            'partially_received': po_partially_received,
            'received': po_received,
            'cancelled': po_cancelled,
            'procurement_amount': procurement_amount,
            'purchase_orders_list': po_list
        },
        'vendors': {
            'active_vendors': active_vendors,
            'inactive_vendors': inactive_vendors
        },
        'stock_movement': {
            'summary': {
                'opening_stock': tot_open,
                'stock_received': tot_rec,
                'stock_dispensed': tot_disp,
                'stock_adjusted': tot_adj,
                'closing_stock': tot_close
            },
            'items': stock_movement_items
        },
        'expiry_monitoring': {
            'categories': {
                'expired': expired_batches_count,
                'expires_within_7_days': exp_7_count,
                'expires_within_30_days': exp_30_count,
                'expires_within_60_days': exp_60_count,
                'expires_within_90_days': exp_90_count
            },
            'batches': monitoring_batches_list
        },
        'low_stock_report': low_stock_table
    }


def get_referral_report_metrics_for_period(target_fac_ids, start_date, end_date):
    """
    Section 15: Referral Report.
    Strictly scoped to facility: created, accepted, rejected, in transit, under treatment, completed.
    """
    ref_qs = Referral.objects.filter(
        Q(source_facility_id__in=target_fac_ids) | Q(destination_facility_id__in=target_fac_ids),
        referral_date__date__gte=start_date,
        referral_date__date__lte=end_date
    ).select_related('patient', 'source_facility', 'destination_facility', 'referring_doctor').distinct()

    total_referrals = ref_qs.count()
    created = ref_qs.filter(status='CREATED').count()
    accepted = ref_qs.filter(status='ACCEPTED').count()
    rejected = ref_qs.filter(status='REJECTED').count()
    in_transit = ref_qs.filter(status='IN_TRANSIT').count()
    under_treatment = ref_qs.filter(status__in=['REACHED', 'UNDER_TREATMENT']).count()
    completed = ref_qs.filter(status__in=['COMPLETED', 'CLOSED']).count()

    outgoing_count = ref_qs.filter(source_facility_id__in=target_fac_ids).count()
    incoming_count = ref_qs.filter(destination_facility_id__in=target_fac_ids).count()

    items = []
    for r in ref_qs.order_by('-referral_date')[:50]:
        items.append({
            'referral_id': r.referral_id,
            'patient_name': r.patient.name,
            'source_facility': r.source_facility.facility_name,
            'destination_facility': r.destination_facility.facility_name,
            'urgency': r.urgency,
            'status': r.status,
            'required_service': r.required_service,
            'date': r.referral_date.strftime('%Y-%m-%d %H:%M')
        })

    return {
        'total_referrals': total_referrals,
        'created': created,
        'accepted': accepted,
        'rejected': rejected,
        'in_transit': in_transit,
        'under_treatment': under_treatment,
        'completed': completed,
        'outgoing_count': outgoing_count,
        'incoming_count': incoming_count,
        'items': items
    }


def get_followup_report_metrics_for_period(target_fac_ids, start_date, end_date):
    """
    Section 16: Follow-up Report.
    Due, completed, pending, overdue for reporting period.
    """
    fu_qs = FollowUp.objects.filter(
        facility_id__in=target_fac_ids,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('patient')

    total_due = fu_qs.count()
    completed = fu_qs.filter(status='COMPLETED').count()
    pending = fu_qs.filter(status__in=['PENDING', 'DUE_TODAY']).count()
    overdue = fu_qs.filter(status='OVERDUE').count()

    items = []
    for fu in fu_qs.order_by('due_date')[:50]:
        items.append({
            'id': fu.id,
            'patient_name': fu.patient.name,
            'category': fu.category,
            'due_date': fu.due_date.strftime('%Y-%m-%d'),
            'status': fu.status,
            'notes': fu.notes
        })

    return {
        'total_due': total_due,
        'completed': completed,
        'pending': pending,
        'overdue': overdue,
        'items': items
    }


def get_ncd_report_metrics_for_period(target_fac_ids, start_date, end_date):
    """
    Section 17: NCD Report.
    Screenings, hypertension, diabetes, treatment status, and follow-ups.
    """
    ncd_qs = NCDRecord.objects.filter(
        facility_id__in=target_fac_ids,
        screening_date__gte=start_date,
        screening_date__lte=end_date
    ).select_related('patient')

    total_screenings = ncd_qs.count()
    all_ncd_patients = NCDRecord.objects.filter(facility_id__in=target_fac_ids).values('patient').distinct().count()

    htn_screened = ncd_qs.filter(hypertension_screened=True).count()
    htn_diagnosed = ncd_qs.filter(hypertension_diagnosed=True).count()

    dia_screened = ncd_qs.filter(diabetes_screened=True).count()
    dia_diagnosed = ncd_qs.filter(diabetes_diagnosed=True).count()

    high_risk = ncd_qs.filter(risk_level='HIGH').count()
    moderate_risk = ncd_qs.filter(risk_level='MODERATE').count()
    low_risk = ncd_qs.filter(risk_level='LOW').count()

    controlled = ncd_qs.filter(control_status='CONTROLLED').count()
    uncontrolled = ncd_qs.filter(control_status='UNCONTROLLED').count()

    return {
        'total_ncd_patients': all_ncd_patients,
        'new_screenings_in_period': total_screenings,
        'hypertension': {
            'screened': htn_screened,
            'diagnosed': htn_diagnosed
        },
        'diabetes': {
            'screened': dia_screened,
            'diagnosed': dia_diagnosed
        },
        'risk_levels': {
            'high': high_risk,
            'moderate': moderate_risk,
            'low': low_risk
        },
        'control_status': {
            'controlled': controlled,
            'uncontrolled': uncontrolled
        }
    }


def get_maternal_child_report_metrics_for_period(target_fac_ids, start_date, end_date):
    """
    Section 18: Maternal & Child Health Report.
    Only displays metrics where corresponding models and records exist.
    """
    try:
        from apps.maternal.models import MaternalRecord
        from apps.child.models import ChildRecord

        fac_patients = Patient.objects.filter(registered_at_facility_id__in=target_fac_ids)
        maternal_qs = MaternalRecord.objects.filter(patient__in=fac_patients)

        anc_visits = Visit.objects.filter(
            facility_id__in=target_fac_ids,
            opd_date__gte=start_date,
            opd_date__lte=end_date,
            visit_type='MATERNAL_ANC'
        ).count()

        total_maternal_cases = maternal_qs.count()
        high_risk_cases = maternal_qs.filter(high_risk_flag=True).count()
        tt_vaccine_given = maternal_qs.filter(tt_vaccine_given=True).count()
        ifa_tablets_issued = maternal_qs.filter(ifa_tablets_issued=True).count()

        child_qs = ChildRecord.objects.filter(patient__in=fac_patients)
        total_child_cases = child_qs.count()
        immunization_up_to_date = child_qs.filter(immunization_status='UP_TO_DATE').count()
        sam_mam_cases = child_qs.filter(sam_mam_status__in=['SAM', 'MAM']).count()

        return {
            'available': True,
            'maternal': {
                'anc_visits': anc_visits,
                'total_registered_mothers': total_maternal_cases,
                'high_risk_cases': high_risk_cases,
                'tt_vaccine_given': tt_vaccine_given,
                'ifa_tablets_issued': ifa_tablets_issued
            },
            'child': {
                'total_children': total_child_cases,
                'immunization_up_to_date': immunization_up_to_date,
                'sam_mam_cases': sam_mam_cases
            }
        }
    except Exception:
        return {'available': False}


def get_alert_report_metrics_for_period(target_fac_ids, start_date, end_date):
    """
    Section 19: Alert / Operational Report.
    Breakdown by category and resolution status for reporting period.
    """
    alert_qs = Alert.objects.filter(
        facility_id__in=target_fac_ids,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    total_alerts = alert_qs.count()
    new_alerts = alert_qs.filter(status='NEW').count()
    acknowledged_alerts = alert_qs.filter(status='ACKNOWLEDGED').count()
    resolved_alerts = alert_qs.filter(status='RESOLVED').count()

    category_map = {
        'inventory': ['LOW_STOCK', 'NEAR_EXPIRY', 'EXPIRED'],
        'clinical': ['LAB_PENDING', 'HIGH_RISK_FOLLOWUP', 'DISEASE_THRESHOLD'],
        'operational': ['FOLLOWUP_OVERDUE', 'MISSING_REPORT'],
        'referral': ['REFERRAL_OVERDUE'],
        'system': []
    }
    cat_breakdown = {}
    for cat_name, type_list in category_map.items():
        if type_list:
            c_qs = alert_qs.filter(alert_type__in=type_list)
        else:
            all_known = [t for lst in category_map.values() for t in lst]
            c_qs = alert_qs.exclude(alert_type__in=all_known)
        cat_breakdown[cat_name] = {
            'total': c_qs.count(),
            'new': c_qs.filter(status='NEW').count(),
            'resolved': c_qs.filter(status='RESOLVED').count()
        }

    return {
        'total_alerts': total_alerts,
        'new': new_alerts,
        'acknowledged': acknowledged_alerts,
        'resolved': resolved_alerts,
        'open_alerts': new_alerts + acknowledged_alerts,
        'categories': cat_breakdown
    }


def get_hospital_admin_report_data(user, requested_facility_id=None, period='day', target_date=None):
    """
    Authoritative single-source builder for Hospital Admin Reports.
    Enforces facility scope, resolves period boundaries, computes previous period comparisons,
    and returns authoritative data for all 11 categories without fabricating fake data.
    """
    scope = get_facility_scope(user, requested_facility_id)
    target_fac_ids = scope['target_fac_ids']

    start_date, end_date = get_period_date_range(period, target_date)
    prev_start_date, prev_end_date = get_previous_period_date_range(period, start_date, end_date)

    # 1. Authoritative Report Category Metrics for Current Period
    opd_patient = get_opd_patient_report_metrics(target_fac_ids, start_date, end_date, period)
    queue_service = get_queue_service_report_metrics(target_fac_ids, start_date, end_date)
    doctor_staff = get_doctor_staff_report_metrics(target_fac_ids, start_date, end_date)
    laboratory = get_laboratory_report_metrics_for_period(target_fac_ids, start_date, end_date)
    pharmacy = get_pharmacy_report_metrics_for_period(target_fac_ids, start_date, end_date, period)
    referrals = get_referral_report_metrics_for_period(target_fac_ids, start_date, end_date)
    follow_up = get_followup_report_metrics_for_period(target_fac_ids, start_date, end_date)
    ncd = get_ncd_report_metrics_for_period(target_fac_ids, start_date, end_date)
    maternal_child = get_maternal_child_report_metrics_for_period(target_fac_ids, start_date, end_date)
    alerts = get_alert_report_metrics_for_period(target_fac_ids, start_date, end_date)

    # 2. Previous Period Metrics for Period Comparison
    prev_opd = get_opd_patient_report_metrics(target_fac_ids, prev_start_date, prev_end_date, period)
    prev_pharm = get_pharmacy_report_metrics_for_period(target_fac_ids, prev_start_date, prev_end_date, period)
    prev_lab = get_laboratory_report_metrics_for_period(target_fac_ids, prev_start_date, prev_end_date)
    prev_ref = get_referral_report_metrics_for_period(target_fac_ids, prev_start_date, prev_end_date)

    comparison = {
        'period_label': period.upper(),
        'current_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        'previous_range': f"{prev_start_date.strftime('%Y-%m-%d')} to {prev_end_date.strftime('%Y-%m-%d')}",
        'metrics': {
            'opd_visits': calculate_metric_change(opd_patient['total_opd_visits'], prev_opd['total_opd_visits']),
            'new_patients': calculate_metric_change(opd_patient['new_patients'], prev_opd['new_patients']),
            'prescriptions_dispensed': calculate_metric_change(
                pharmacy['prescriptions']['dispensed'], prev_pharm['prescriptions']['dispensed']
            ),
            'lab_verified': calculate_metric_change(laboratory['verified_results'], prev_lab['verified_results']),
            'referrals_created': calculate_metric_change(referrals['total_referrals'], prev_ref['total_referrals'])
        }
    }

    # 3. High-level Grouped Summaries (Section 23: Report Summary Cards)
    summary_cards = {
        'patients': {
            'total_visits': opd_patient['total_opd_visits'],
            'new_patients': opd_patient['new_patients'],
            'completed': opd_patient['completed_visits'],
            'emergency': opd_patient['emergency_visits']
        },
        'services': {
            'triage_waiting': queue_service['stages']['triage']['waiting'],
            'doctor_waiting': queue_service['stages']['doctor']['waiting'],
            'lab_pending': queue_service['stages']['laboratory']['waiting'] + queue_service['stages']['laboratory']['in_progress'],
            'pharmacy_waiting': queue_service['stages']['pharmacy']['waiting']
        },
        'pharmacy': {
            'dispensed_units': pharmacy['dispensing']['total_medicines_dispensed'],
            'low_stock_medicines': pharmacy['inventory']['low_stock_medicines'],
            'out_of_stock_medicines': pharmacy['inventory']['out_of_stock_medicines'],
            'expiring_soon_batches': pharmacy['inventory']['expiring_soon_batches']
        },
        'procurement': {
            'pending_po': pharmacy['purchases']['pending_approval'] + pharmacy['purchases']['draft'],
            'received_po': pharmacy['purchases']['received'],
            'procurement_amount': pharmacy['purchases']['procurement_amount']
        },
        'referrals': {
            'created': referrals['created'],
            'in_transit': referrals['in_transit'],
            'completed': referrals['completed']
        }
    }

    t_date_str = target_date.strftime('%Y-%m-%d') if isinstance(target_date, (datetime.date, datetime.datetime)) else str(target_date or datetime.date.today())

    return {
        'facility': {
            'id': scope['active_facility_id'],
            'name': scope['active_fac_name'],
            'type': scope['active_fac_type'],
            'district': scope['district_name']
        },
        'period': {
            'type': period.lower(),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'target_date': t_date_str
        },
        'summary_cards': summary_cards,
        'comparison': comparison,
        'opd_patient': opd_patient,
        'queue_service': queue_service,
        'doctor_staff': doctor_staff,
        'laboratory': laboratory,
        'pharmacy': pharmacy,
        'referrals': referrals,
        'follow_up': follow_up,
        'ncd': ncd,
        'maternal_child': maternal_child,
        'alerts': alerts
    }

