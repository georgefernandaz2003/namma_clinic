from django.db import models

class FacilityTypeChoices(models.TextChoices):
    MAIN_HOSPITAL = 'MAIN_HOSPITAL', 'Main Hospital'
    REFERRAL_HOSPITAL = 'REFERRAL_HOSPITAL', 'Referral Hospital'
    SECONDARY_HOSPITAL = 'SECONDARY_HOSPITAL', 'Secondary Hospital'
    UPHC = 'UPHC', 'Urban Primary Health Centre (UPHC)'
    NAMMA_CLINIC = 'NAMMA_CLINIC', 'Namma Clinic (Urban HWC)'
    URBAN_CLINIC = 'URBAN_CLINIC', 'Urban Clinic'
    RURAL_CLINIC = 'RURAL_CLINIC', 'Rural Clinic'
    VILLAGE_CLINIC = 'VILLAGE_CLINIC', 'Village Clinic'
    DIAGNOSTIC_CENTER = 'DIAGNOSTIC_CENTER', 'Diagnostic Center'
    OTHER = 'OTHER', 'Other Health Facility'

class Facility(models.Model):
    facility_code = models.CharField(max_length=50, unique=True)
    facility_name = models.CharField(max_length=200)
    facility_type = models.CharField(max_length=30, choices=FacilityTypeChoices.choices, default=FacilityTypeChoices.NAMMA_CLINIC)
    parent_facility = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    
    state = models.ForeignKey('geography.State', on_delete=models.CASCADE, related_name='facilities')
    district = models.ForeignKey('geography.District', on_delete=models.CASCADE, related_name='facilities')
    zone = models.ForeignKey('geography.Zone', on_delete=models.SET_NULL, null=True, blank=True, related_name='facilities')
    ward = models.ForeignKey('geography.Ward', on_delete=models.SET_NULL, null=True, blank=True, related_name='facilities')
    
    city_or_ulb = models.CharField(max_length=100, default='BBMP')
    urban_rural = models.CharField(max_length=10, choices=[('URBAN', 'Urban'), ('RURAL', 'Rural')], default='URBAN')
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, default=12.9716)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, default=77.5946)
    
    population_served = models.IntegerField(default=20000)
    vulnerable_population = models.IntegerField(default=5000)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    opening_time = models.CharField(max_length=20, default='09:00 AM')
    closing_time = models.CharField(max_length=20, default='04:30 PM')
    
    emergency_available = models.BooleanField(default=False)
    lab_available = models.BooleanField(default=True)
    pharmacy_available = models.BooleanField(default=True)
    teleconsultation_available = models.BooleanField(default=True)
    bed_capacity = models.IntegerField(default=0)
    
    services = models.TextField(default='General OPD, NCD Screening, ANC/PNC Care, Immunization, Basic Diagnostics, Pharmacy')
    specialists = models.TextField(default='General Physician, Staff Nurse, Lab Tech, Pharmacist')
    status = models.CharField(max_length=20, default='ACTIVE')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_all_descendant_ids(self):
        """Recursively fetch IDs of self and all child/descendant facilities."""
        descendants = [self.id]
        children = Facility.objects.filter(parent_facility=self)
        for child in children:
            descendants.extend(child.get_all_descendant_ids())
        return list(set(descendants))

    def __str__(self):
        return f"{self.facility_name} ({self.get_facility_type_display()})"

class RelationshipTypeChoices(models.TextChoices):
    PARENT = 'PARENT', 'Parent Organization'
    REFERRAL = 'REFERRAL', 'Routine Referral'
    SPECIALIST = 'SPECIALIST', 'Specialist Referral'
    EMERGENCY = 'EMERGENCY', 'Emergency Referral'
    DIAGNOSTIC = 'DIAGNOSTIC', 'Diagnostic Referral'
    SUPPORT = 'SUPPORT', 'Operational Support'
    TELECONSULTATION = 'TELECONSULTATION', 'Teleconsultation Hub'

class FacilityRelationship(models.Model):
    source_facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='outgoing_relationships')
    destination_facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='incoming_relationships')
    relationship_type = models.CharField(max_length=30, choices=RelationshipTypeChoices.choices, default=RelationshipTypeChoices.REFERRAL)
    service = models.CharField(max_length=100, default='General Referral')
    priority = models.CharField(max_length=20, default='PRIMARY')
    distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_facility.facility_name} -> {self.destination_facility.facility_name} [{self.relationship_type}]"


# ============================================================================
# CLINIC INFRASTRUCTURE, CONSUMABLES, BEDS & MAINTENANCE MODELS
# ============================================================================

class OxygenSourceChoices(models.TextChoices):
    CYLINDER_MANIFOLD = 'CYLINDER_MANIFOLD', 'B/D Type Cylinder Manifold'
    CONCENTRATOR = 'CONCENTRATOR', 'Medical Oxygen Concentrator'
    PSA_PLANT = 'PSA_PLANT', 'On-Site PSA Oxygen Plant'
    LIQUID_TANK = 'LIQUID_TANK', 'Liquid Medical Oxygen (LMO) Tank'

class OxygenStatusChoices(models.TextChoices):
    OPTIMAL = 'OPTIMAL', 'Optimal Supply (>75%)'
    ADEQUATE = 'ADEQUATE', 'Adequate Supply (50-75%)'
    REFILL_REQUIRED = 'REFILL_REQUIRED', 'Refill Required (<50%)'
    CRITICAL_LOW = 'CRITICAL_LOW', 'Critical Low Stock (<25%)'

class FacilityOxygenSupply(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='oxygen_supplies')
    oxygen_source = models.CharField(max_length=30, choices=OxygenSourceChoices.choices, default=OxygenSourceChoices.CYLINDER_MANIFOLD)
    total_cylinders = models.IntegerField(default=10)
    active_cylinders = models.IntegerField(default=7)
    empty_cylinders = models.IntegerField(default=3)
    current_pressure_psi = models.IntegerField(default=1850) # e.g. 1850 PSI
    fill_percentage = models.IntegerField(default=85)
    status = models.CharField(max_length=30, choices=OxygenStatusChoices.choices, default=OxygenStatusChoices.OPTIMAL)
    last_inspected = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, default='Primary oxygen manifold operational and pressure tested.')

    def __str__(self):
        return f"{self.facility.facility_name} - Oxygen ({self.get_status_display()})"


class ConsumableCategoryChoices(models.TextChoices):
    CLEANING_SANITATION = 'CLEANING_SANITATION', 'Floor Cleaning & Disinfectants'
    INFECTION_CONTROL = 'INFECTION_CONTROL', 'Infection Control & Biohazard'
    PERSONAL_PROTECTION = 'PERSONAL_PROTECTION', 'Personal Protective Equipment (PPE)'
    GENERAL_FACILITY = 'GENERAL_FACILITY', 'General Facility Supplies'

class FacilityConsumableInventory(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='consumable_inventory')
    item_name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=ConsumableCategoryChoices.choices, default=ConsumableCategoryChoices.CLEANING_SANITATION)
    unit_of_measure = models.CharField(max_length=30, default='Litres') # Litres, Bottles, Boxes, Packs
    current_stock = models.IntegerField(default=50)
    min_threshold = models.IntegerField(default=15)
    reorder_status = models.CharField(max_length=20, default='ADEQUATE')
    last_restocked = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.facility.facility_name} - {self.item_name} ({self.current_stock} {self.unit_of_measure})"


class TicketCategoryChoices(models.TextChoices):
    ELECTRICAL = 'ELECTRICAL', 'Electrical & Wiring Maintenance'
    PLUMBING = 'PLUMBING', 'Plumbing & Water Supply'
    OXYGEN_SYSTEM = 'OXYGEN_SYSTEM', 'Oxygen Manifold & Tubing'
    SOLAR_UPS = 'SOLAR_UPS', 'Solar Power & UPS Battery Backup'
    MEDICAL_EQUIPMENT = 'MEDICAL_EQUIPMENT', 'Medical Equipment Repair'
    SANITY_CLEANING = 'SANITY_CLEANING', 'Facility Cleaning & Deep Sanitation'
    BUILDING_STRUCTURE = 'BUILDING_STRUCTURE', 'Building & Structural Repair'

class TicketPriorityChoices(models.TextChoices):
    LOW = 'LOW', 'Low Priority'
    MEDIUM = 'MEDIUM', 'Medium Priority'
    HIGH = 'HIGH', 'High Priority'
    EMERGENCY = 'EMERGENCY', 'Emergency Work Order'

class TicketStatusChoices(models.TextChoices):
    LOGGED = 'LOGGED', 'Logged & Pending'
    ASSIGNED = 'ASSIGNED', 'Assigned to Technician'
    IN_PROGRESS = 'IN_PROGRESS', 'Work in Progress'
    RESOLVED = 'RESOLVED', 'Resolved & Tested'
    CLOSED = 'CLOSED', 'Ticket Closed'

class FacilityMaintenanceTicket(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='maintenance_tickets')
    ticket_number = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=30, choices=TicketCategoryChoices.choices, default=TicketCategoryChoices.ELECTRICAL)
    equipment_or_area = models.CharField(max_length=150)
    priority = models.CharField(max_length=20, choices=TicketPriorityChoices.choices, default=TicketPriorityChoices.MEDIUM)
    description = models.TextField()
    reported_by = models.CharField(max_length=100, default='Staff Nurse')
    assigned_technician = models.CharField(max_length=100, default='BBMP Electrical Division Team')
    status = models.CharField(max_length=20, choices=TicketStatusChoices.choices, default=TicketStatusChoices.LOGGED)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.ticket_number} [{self.get_category_display()}] - {self.status}"


class BedCategoryChoices(models.TextChoices):
    GENERAL_OBSERVATION = 'GENERAL_OBSERVATION', 'General OPD Observation Bed'
    EMERGENCY_TRIAGE = 'EMERGENCY_TRIAGE', 'Emergency Triage & Resuscitation Bed'
    OXYGEN_SUPPORTED = 'OXYGEN_SUPPORTED', 'Oxygen Supported High-Care Bed'
    DAY_CARE_ISOLATION = 'DAY_CARE_ISOLATION', 'Day-Care & Isolation Ward Bed'

class FacilityBedCapacity(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='bed_capacities')
    bed_category = models.CharField(max_length=30, choices=BedCategoryChoices.choices, default=BedCategoryChoices.GENERAL_OBSERVATION)
    total_beds = models.IntegerField(default=6)
    occupied_beds = models.IntegerField(default=2)
    cleaning_in_progress = models.IntegerField(default=1)
    under_maintenance = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default='Observation ward equipped with monitor & IV stands.')

    @property
    def available_beds(self):
        avail = self.total_beds - self.occupied_beds - self.cleaning_in_progress - self.under_maintenance
        return max(0, avail)

    def __str__(self):
        return f"{self.facility.facility_name} - {self.get_bed_category_display()} ({self.occupied_beds}/{self.total_beds} Occupied)"


class FacilityBedAllocation(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='bed_allocations')
    bed_number = models.CharField(max_length=30)
    bed_category = models.CharField(max_length=30, choices=BedCategoryChoices.choices, default=BedCategoryChoices.GENERAL_OBSERVATION)
    patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True, related_name='bed_allocations')
    patient_name = models.CharField(max_length=150, blank=True)
    allocated_at = models.DateTimeField(auto_now_add=True)
    discharged_at = models.DateTimeField(null=True, blank=True)
    attending_doctor = models.CharField(max_length=100, default='Dr. Medical Officer')
    status = models.CharField(max_length=20, default='OCCUPIED') # OCCUPIED, AVAILABLE, SANITIZING, MAINTENANCE

    def __str__(self):
        return f"{self.bed_number} - {self.patient_name or 'Unassigned'} ({self.status})"

