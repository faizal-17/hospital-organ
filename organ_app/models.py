import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

ORGAN_CHOICES = [
    ('KIDNEY', 'Kidney'),
    ('LIVER', 'Liver'),
    ('HEART', 'Heart'),
    ('LUNG', 'Lung'),
    ('PANCREAS', 'Pancreas'),
    ('CORNEA', 'Cornea'),
]

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+ (A Positive)'),
    ('A-', 'A- (A Negative)'),
    ('B+', 'B+ (B Positive)'),
    ('B-', 'B- (B Negative)'),
    ('AB+', 'AB+ (AB Positive)'),
    ('AB-', 'AB- (AB Negative)'),
    ('O+', 'O+ (O Positive)'),
    ('O-', 'O- (O Negative)'),
]

ROLE_CHOICES = [
    ('PATIENT', 'Patient'),
    ('DOCTOR', 'Doctor / Medical Officer'),
    ('GOVT', 'Government Official'),
    ('HOSPITAL', 'Hospital Transplant Coordinator'),
    ('MORTUARY', 'Mortuary Staff'),
    ('ADMIN', 'System Administrator'),
]

STATUS_CHOICES = [
    ('SUBMITTED', 'Submitted - Pending Medical Review'),
    ('DOCTOR_VERIFIED', 'Doctor Verified - Pending Govt Approval'),
    ('DOCTOR_REJECTED', 'Doctor Rejected'),
    ('GOVT_APPROVED', 'Government Approved - Waiting for Organ'),
    ('GOVT_REJECTED', 'Government Authorization Denied'),
    ('ALLOCATED', 'Organ Matched & Allocated'),
    ('TRANSPLANTED', 'Transplant Procedure Completed'),
    ('CANCELLED', 'Request Cancelled'),
]

PRIORITY_CHOICES = [
    ('EMERGENCY', 'Tier 1 - Emergency (Critical Condition)'),
    ('HIGH', 'Tier 2 - High Priority'),
    ('NORMAL', 'Tier 3 - Normal Priority'),
]

ORGAN_STATUS_CHOICES = [
    ('AVAILABLE', 'Available for Matching'),
    ('ALLOCATED', 'Allocated to Patient'),
    ('IN_TRANSIT', 'In Transit / Cold Storage'),
    ('TRANSPLANTED', 'Transplanted'),
    ('EXPIRED', 'Viability Expired'),
]


class Hospital(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    license_number = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    is_transplant_center = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    phone = models.CharField(max_length=20, blank=True)
    national_id = models.CharField(max_length=50, blank=True, help_text="National Identification / Aadhar")
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')
    license_or_emp_id = models.CharField(max_length=100, blank=True, help_text="Medical license / Govt ID / Employee number")
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} [{self.get_role_display()}]"


class DonorRecord(models.Model):
    donor_code = models.CharField(max_length=50, unique=True)
    donor_name = models.CharField(max_length=150)
    donor_type = models.CharField(
        max_length=20,
        choices=[('DECEASED', 'Deceased Donor (Cadaveric)'), ('LIVING', 'Living Donor')],
        default='DECEASED'
    )
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='donors')
    cause_of_death = models.CharField(max_length=255, blank=True)
    time_of_death = models.DateTimeField(null=True, blank=True)
    family_consent_verified = models.BooleanField(default=True)
    legal_clearance = models.BooleanField(default=True)
    medical_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor_code} - {self.donor_name} ({self.blood_group})"


class AvailableOrgan(models.Model):
    organ_id = models.CharField(max_length=50, unique=True)
    donor = models.ForeignKey(DonorRecord, on_delete=models.CASCADE, related_name='organs')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='organs_in_stock')
    organ_type = models.CharField(max_length=30, choices=ORGAN_CHOICES)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    harvested_at = models.DateTimeField(default=timezone.now)
    viability_hours = models.PositiveIntegerField(default=24, help_text="Cold ischemia time window in hours")
    condition_grade = models.CharField(
        max_length=20,
        choices=[('EXCELLENT', 'Grade A - Excellent'), ('GOOD', 'Grade B - Good'), ('FAIR', 'Grade C - Fair')],
        default='EXCELLENT'
    )
    status = models.CharField(max_length=20, choices=ORGAN_STATUS_CHOICES, default='AVAILABLE')
    storage_location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def expiration_time(self):
        return self.harvested_at + timedelta(hours=self.viability_hours)

    @property
    def hours_remaining(self):
        diff = self.expiration_time - timezone.now()
        hours = diff.total_seconds() / 3600
        return max(0, round(hours, 1))

    @property
    def is_viable(self):
        return timezone.now() <= self.expiration_time and self.status == 'AVAILABLE'

    def __str__(self):
        return f"{self.get_organ_type_display()} [{self.organ_id}] - {self.blood_group} ({self.get_status_display()})"


class OrganRequest(models.Model):
    request_code = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organ_requests')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='patient_requests')
    organ = models.CharField(max_length=30, choices=ORGAN_CHOICES)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    medical_history = models.TextField(help_text="Detailed diagnosis, clinical justification, previous surgeries")
    medical_report = models.FileField(upload_to='medical_reports/', blank=True, null=True)
    
    # Workflow State
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='SUBMITTED')
    priority_level = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    
    # Doctor Verification
    doctor_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_verifications')
    doctor_verified_at = models.DateTimeField(null=True, blank=True)
    doctor_notes = models.TextField(blank=True)
    
    # Government Authorization
    govt_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='govt_approvals')
    govt_approved_at = models.DateTimeField(null=True, blank=True)
    govt_notes = models.TextField(blank=True)
    govt_approval_number = models.CharField(max_length=100, blank=True, help_text="Official Government Legal Certification ID")
    
    # Allocation
    allocated_organ = models.ForeignKey(AvailableOrgan, on_delete=models.SET_NULL, null=True, blank=True, related_name='allocated_requests')
    allocated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def waiting_days(self):
        diff = timezone.now() - self.created_at
        return round(diff.total_seconds() / 86400, 1)

    @property
    def priority_score(self):
        mapping = {
            'EMERGENCY': 1000,
            'HIGH': 500,
            'NORMAL': 100,
        }
        return mapping.get(self.priority_level, 100)

    @property
    def patient_name(self):
        if self.patient:
            return self.patient.get_full_name() or self.patient.username
        return "Unknown Recipient"

    @property
    def doctor_name(self):
        if self.doctor_verified_by:
            return self.doctor_verified_by.get_full_name() or self.doctor_verified_by.username
        return "Medical Panel"

    @property
    def govt_official_name(self):
        if self.govt_approved_by:
            return self.govt_approved_by.get_full_name() or self.govt_approved_by.username
        return "State Authority"

    def __str__(self):
        return f"{self.request_code} - {self.patient_name} ({self.organ} / {self.blood_group})"


class MortuaryRecord(models.Model):
    case_number = models.CharField(max_length=50, unique=True)
    deceased_name = models.CharField(max_length=150)
    deceased_id_number = models.CharField(max_length=100, blank=True, help_text="Hospital Registration / Govt ID")
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    time_of_death = models.DateTimeField()
    cause_of_death = models.TextField()
    mortuary_room_location = models.CharField(max_length=100, help_text="E.g., Storage Bay 3, Cold Vault 4")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='mortuary_records')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='mortuary_entries')
    
    # Potential Donor Trigger
    is_potential_donor = models.BooleanField(default=False)
    donor_flag_reason = models.TextField(blank=True, help_text="E.g., Brain death criteria fulfilled, organs preserved")
    donor_status_verified = models.BooleanField(default=False, help_text="Family consent / NOTTO donor card check")
    organs_harvestable = models.CharField(max_length=255, blank=True, help_text="Comma-separated organs, e.g. Kidney, Liver, Cornea")
    
    # Alerts
    alert_sent_to_hospital = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(null=True, blank=True)
    linked_donor_record = models.ForeignKey(DonorRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='mortuary_sources')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Case {self.case_number}: {self.deceased_name} ({self.mortuary_room_location})"


class AuditLog(models.Model):
    request = models.ForeignKey(OrganRequest, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    organ = models.ForeignKey(AvailableOrgan, on_delete=models.SET_NULL, null=True, blank=True)
    mortuary_record = models.ForeignKey(MortuaryRecord, on_delete=models.SET_NULL, null=True, blank=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    actor_role = models.CharField(max_length=50)
    action = models.CharField(max_length=80)
    from_state = models.CharField(max_length=60, blank=True)
    to_state = models.CharField(max_length=60, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    @property
    def actor_name(self):
        if self.actor:
            return self.actor.get_full_name() or self.actor.username
        return "System Engine"

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action} by {self.actor or 'System'}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, default='INFO', choices=[
        ('INFO', 'Information'),
        ('SUCCESS', 'Success / Approval'),
        ('WARNING', 'Alert / Action Needed'),
        ('EMERGENCY', 'Critical Urgent Notification'),
    ])
    related_request = models.ForeignKey(OrganRequest, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title}"
