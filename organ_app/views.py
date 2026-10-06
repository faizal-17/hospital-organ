import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import Q

from .models import (
    UserProfile, Hospital, OrganRequest, AvailableOrgan,
    DonorRecord, MortuaryRecord, AuditLog, Notification,
    ORGAN_CHOICES, BLOOD_GROUP_CHOICES, PRIORITY_CHOICES
)
from .forms import (
    PatientRegistrationForm, PatientProfileForm, OrganRequestForm,
    DoctorVerificationForm, GovtAuthorizationForm, DonorRecordForm,
    AvailableOrganForm, MortuaryRecordForm
)
from .matching_service import find_eligible_candidates, execute_organ_allocation
from .certificate_service import generate_approval_certificate_pdf


# ==========================================
# AUTHENTICATION & DEMO SWITCHER VIEWS
# ==========================================

def landing_page(request):
    """
    Public Homepage with system overview, architecture highlights,
    live counter metrics, and rapid role demo switcher.
    """
    stats = {
        'total_requests': OrganRequest.objects.count(),
        'doctor_verified': OrganRequest.objects.filter(status='DOCTOR_VERIFIED').count(),
        'govt_approved': OrganRequest.objects.filter(status='GOVT_APPROVED').count(),
        'allocated': OrganRequest.objects.filter(status='ALLOCATED').count(),
        'available_organs': AvailableOrgan.objects.filter(status='AVAILABLE').count(),
        'registered_donors': DonorRecord.objects.count(),
    }
    return render(request, 'landing.html', {'stats': stats})


def patient_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create UserProfile for patient
            UserProfile.objects.create(
                user=user,
                role='PATIENT',
                phone=form.cleaned_data.get('phone', ''),
                national_id=form.cleaned_data.get('national_id', ''),
                blood_group=form.cleaned_data.get('blood_group', ''),
                date_of_birth=form.cleaned_data.get('date_of_birth'),
                address=form.cleaned_data.get('address', ''),
                emergency_contact_name=form.cleaned_data.get('emergency_contact_name', ''),
                emergency_contact_phone=form.cleaned_data.get('emergency_contact_phone', '')
            )
            
            # Send welcome notification
            Notification.objects.create(
                recipient=user,
                title="Account Registration Successful",
                message="Welcome to the Organ Request and Government Approval Management System. You can now submit your organ request for medical verification.",
                category='SUCCESS'
            )
            
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}! Your patient account has been created.")
            return redirect('patient_dashboard')
    else:
        form = PatientRegistrationForm()
        
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Signed in as {user.username}.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


def switch_demo_role(request, role):
    """
    Convenience view for evaluation: logs directly into pre-seeded users for each role.
    """
    user_mapping = {
        'PATIENT': 'patient1',
        'DOCTOR': 'doctor1',
        'GOVT': 'govt1',
        'HOSPITAL': 'hospital1',
        'MORTUARY': 'mortuary1',
        'ADMIN': 'admin'
    }
    target_username = user_mapping.get(role.upper())
    if target_username:
        try:
            user = User.objects.get(username=target_username)
            login(request, user)
            messages.success(request, f"Switched active session to {role.upper()} ({user.get_full_name() or user.username}).")
            return redirect('dashboard')
        except User.DoesNotExist:
            messages.warning(request, f"User for {role} not found. Please run seed script first.")
            return redirect('landing')
    return redirect('landing')


@login_required
def dashboard_router(request):
    """
    Routes logged-in users to their specialized dashboard according to their profile role.
    """
    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else ('ADMIN' if request.user.is_superuser else 'PATIENT')
    
    if role == 'PATIENT':
        return redirect('patient_dashboard')
    elif role == 'DOCTOR':
        return redirect('doctor_dashboard')
    elif role == 'GOVT':
        return redirect('govt_dashboard')
    elif role == 'HOSPITAL':
        return redirect('hospital_dashboard')
    elif role == 'MORTUARY':
        return redirect('mortuary_dashboard')
    elif role == 'ADMIN':
        return redirect('admin_overview')
    return redirect('patient_dashboard')


# ==========================================
# 1. PATIENT MODULE VIEWS
# ==========================================

@login_required
def patient_dashboard(request):
    user = request.user
    requests = OrganRequest.objects.filter(patient=user).order_by('-created_at')
    active_request = requests.first()
    
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:10]
    
    return render(request, 'patient/dashboard.html', {
        'requests': requests,
        'active_request': active_request,
        'notifications': notifications,
    })


@login_required
def submit_organ_request(request):
    profile = getattr(request.user, 'profile', None)
    initial_data = {}
    if profile and profile.blood_group:
        initial_data['blood_group'] = profile.blood_group

    if request.method == 'POST':
        form = OrganRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req_obj = form.save(commit=False)
            req_obj.patient = request.user
            req_obj.request_code = f"REQ-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
            req_obj.status = 'SUBMITTED'
            req_obj.save()
            
            # Audit log
            AuditLog.objects.create(
                request=req_obj,
                actor=request.user,
                actor_role='PATIENT',
                action='REQUEST_SUBMITTED',
                from_state='',
                to_state='SUBMITTED',
                comments=f"Patient {request.user.username} submitted new request for {req_obj.organ} ({req_obj.blood_group})"
            )
            
            # In-app notification
            Notification.objects.create(
                recipient=request.user,
                title="Organ Request Submitted",
                message=f"Your request {req_obj.request_code} for {req_obj.get_organ_display()} has been submitted. It is now awaiting medical review by the attending physician.",
                category='INFO',
                related_request=req_obj
            )
            
            messages.success(request, f"Organ Request {req_obj.request_code} successfully submitted for doctor verification!")
            return redirect('patient_dashboard')
    else:
        form = OrganRequestForm(initial=initial_data)

    return render(request, 'patient/submit_request.html', {'form': form})


@login_required
def patient_profile_view(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            req_user = request.user
            req_user.first_name = form.cleaned_data['first_name']
            req_user.last_name = form.cleaned_data['last_name']
            req_user.email = form.cleaned_data['email']
            req_user.save()
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('patient_profile')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = PatientProfileForm(instance=profile, initial=initial)
        
    return render(request, 'patient/profile.html', {'form': form, 'profile': profile})


@login_required
def request_detail_view(request, pk):
    req_obj = get_object_or_404(OrganRequest, pk=pk)
    
    # Permission check: patient or authorized roles
    profile = getattr(request.user, 'profile', None)
    user_role = profile.role if profile else ('ADMIN' if request.user.is_superuser else None)
    
    if user_role == 'PATIENT' and req_obj.patient != request.user:
        return HttpResponseForbidden("You are not authorized to view this request.")
        
    audit_trail = req_obj.audit_logs.all()
    
    return render(request, 'patient/request_detail.html', {
        'req': req_obj,
        'audit_trail': audit_trail,
        'user_role': user_role,
    })


# ==========================================
# 2. DOCTOR & GOVT AUTHORIZATION MODULE
# ==========================================

@login_required
def doctor_dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role not in ['DOCTOR', 'ADMIN'] and not request.user.is_superuser:
        messages.error(request, "Access restricted to medical doctors and administrators.")
        return redirect('dashboard')
        
    pending_requests = OrganRequest.objects.filter(status='SUBMITTED').order_by('created_at')
    reviewed_requests = OrganRequest.objects.filter(
        Q(doctor_verified_by=request.user) | ~Q(status='SUBMITTED')
    ).order_by('-updated_at')[:20]
    
    return render(request, 'doctor/dashboard.html', {
        'pending_requests': pending_requests,
        'reviewed_requests': reviewed_requests,
    })


@login_required
def doctor_review_request(request, pk):
    req_obj = get_object_or_404(OrganRequest, pk=pk)
    profile = getattr(request.user, 'profile', None)
    
    if profile and profile.role not in ['DOCTOR', 'ADMIN'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access restricted to medical doctors.")
        
    if request.method == 'POST':
        form = DoctorVerificationForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            priority = form.cleaned_data['priority_level']
            notes = form.cleaned_data['doctor_notes']
            
            from_state = req_obj.status
            if decision == 'APPROVE':
                req_obj.status = 'DOCTOR_VERIFIED'
                req_obj.priority_level = priority
                req_obj.doctor_verified_by = request.user
                req_obj.doctor_verified_at = timezone.now()
                req_obj.doctor_notes = notes
                req_obj.save()
                
                # Audit log
                AuditLog.objects.create(
                    request=req_obj,
                    actor=request.user,
                    actor_role='DOCTOR',
                    action='DOCTOR_VERIFIED',
                    from_state=from_state,
                    to_state='DOCTOR_VERIFIED',
                    comments=f"Doctor {request.user.get_full_name() or request.user.username} verified request. Priority: {priority}. Notes: {notes}"
                )
                
                # Notification to patient
                Notification.objects.create(
                    recipient=req_obj.patient,
                    title="Medical Review Verified",
                    message=f"Dr. {request.user.get_full_name() or request.user.username} has verified your organ request ({req_obj.request_code}) with Priority: {req_obj.get_priority_level_display()}. It has been forwarded to Government Officials for statutory authorization.",
                    category='SUCCESS',
                    related_request=req_obj
                )
                
                messages.success(request, f"Request {req_obj.request_code} verified and prioritized as {req_obj.get_priority_level_display()}!")
            else:
                req_obj.status = 'DOCTOR_REJECTED'
                req_obj.doctor_verified_by = request.user
                req_obj.doctor_verified_at = timezone.now()
                req_obj.doctor_notes = notes
                req_obj.save()
                
                AuditLog.objects.create(
                    request=req_obj,
                    actor=request.user,
                    actor_role='DOCTOR',
                    action='DOCTOR_REJECTED',
                    from_state=from_state,
                    to_state='DOCTOR_REJECTED',
                    comments=f"Medical verification rejected: {notes}"
                )
                
                Notification.objects.create(
                    recipient=req_obj.patient,
                    title="Medical Review Rejected",
                    message=f"Your organ request ({req_obj.request_code}) was rejected by the medical reviewer. Reason: {notes}",
                    category='WARNING',
                    related_request=req_obj
                )
                
                messages.warning(request, f"Request {req_obj.request_code} has been rejected.")
                
            return redirect('doctor_dashboard')
    else:
        form = DoctorVerificationForm(initial={'priority_level': req_obj.priority_level})
        
    return render(request, 'doctor/review_request.html', {
        'req': req_obj,
        'form': form
    })


@login_required
def govt_dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role not in ['GOVT', 'ADMIN'] and not request.user.is_superuser:
        messages.error(request, "Access restricted to Government Officials and Administrators.")
        return redirect('dashboard')
        
    awaiting_approval = OrganRequest.objects.filter(status='DOCTOR_VERIFIED').order_by('-priority_level', 'created_at')
    approved_pool = OrganRequest.objects.filter(status='GOVT_APPROVED').order_by('-priority_level', 'created_at')
    denied_requests = OrganRequest.objects.filter(status='GOVT_REJECTED').order_by('-updated_at')[:10]
    
    return render(request, 'govt/dashboard.html', {
        'awaiting_approval': awaiting_approval,
        'approved_pool': approved_pool,
        'denied_requests': denied_requests,
    })


@login_required
def govt_review_request(request, pk):
    req_obj = get_object_or_404(OrganRequest, pk=pk)
    profile = getattr(request.user, 'profile', None)
    
    if profile and profile.role not in ['GOVT', 'ADMIN'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access restricted to Government Authorization Officials.")
        
    if request.method == 'POST':
        form = GovtAuthorizationForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            notes = form.cleaned_data['govt_notes']
            from_state = req_obj.status
            
            if decision == 'APPROVE':
                cert_id = f"GOV-AUTH-{timezone.now().year}-{uuid.uuid4().hex[:6].upper()}"
                req_obj.status = 'GOVT_APPROVED'
                req_obj.govt_approved_by = request.user
                req_obj.govt_approved_at = timezone.now()
                req_obj.govt_notes = notes
                req_obj.govt_approval_number = cert_id
                req_obj.save()
                
                # Audit log
                AuditLog.objects.create(
                    request=req_obj,
                    actor=request.user,
                    actor_role='GOVT',
                    action='GOVT_APPROVED',
                    from_state=from_state,
                    to_state='GOVT_APPROVED',
                    comments=f"Government Authorization Granted. Cert: {cert_id}. Notes: {notes}"
                )
                
                # Notification
                Notification.objects.create(
                    recipient=req_obj.patient,
                    title="GOVERNMENT APPROVAL GRANTED",
                    message=(
                        f"Official statutory authorization granted for request {req_obj.request_code}! "
                        f"Authorization Certificate #{cert_id} is now issued. "
                        f"You are placed in the active organ allocation matching pool."
                    ),
                    category='SUCCESS',
                    related_request=req_obj
                )
                
                messages.success(request, f"Official Government Approval Certificate #{cert_id} granted for Request {req_obj.request_code}!")
            else:
                req_obj.status = 'GOVT_REJECTED'
                req_obj.govt_approved_by = request.user
                req_obj.govt_approved_at = timezone.now()
                req_obj.govt_notes = notes
                req_obj.save()
                
                AuditLog.objects.create(
                    request=req_obj,
                    actor=request.user,
                    actor_role='GOVT',
                    action='GOVT_REJECTED',
                    from_state=from_state,
                    to_state='GOVT_REJECTED',
                    comments=f"Government authorization denied: {notes}"
                )
                
                Notification.objects.create(
                    recipient=req_obj.patient,
                    title="Government Authorization Denied",
                    message=f"Government statutory authorization was denied for your request {req_obj.request_code}. Grounds: {notes}",
                    category='WARNING',
                    related_request=req_obj
                )
                
                messages.warning(request, f"Request {req_obj.request_code} was denied government clearance.")
                
            return redirect('govt_dashboard')
    else:
        form = GovtAuthorizationForm()
        
    return render(request, 'govt/review_request.html', {
        'req': req_obj,
        'form': form
    })


@login_required
def download_certificate_pdf(request, pk):
    req_obj = get_object_or_404(OrganRequest, pk=pk)
    
    if req_obj.status not in ['GOVT_APPROVED', 'ALLOCATED', 'TRANSPLANTED']:
        messages.error(request, "Approval Certificate is only available for Government Approved requests.")
        return redirect('request_detail', pk=pk)
        
    pdf_buffer = generate_approval_certificate_pdf(req_obj)
    filename = f"Govt_Approval_Certificate_{req_obj.govt_approval_number or req_obj.request_code}.pdf"
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def view_certificate_html(request, pk):
    req_obj = get_object_or_404(OrganRequest, pk=pk)
    
    if req_obj.status not in ['GOVT_APPROVED', 'ALLOCATED', 'TRANSPLANTED']:
        messages.error(request, "Approval Certificate is only available for Government Approved requests.")
        return redirect('request_detail', pk=pk)
        
    return render(request, 'govt/certificate_view.html', {'req': req_obj})


# ==========================================
# 3. HOSPITAL (HOST) MODULE & MATCHING ENGINE
# ==========================================

@login_required
def hospital_dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role not in ['HOSPITAL', 'ADMIN', 'DOCTOR'] and not request.user.is_superuser:
        messages.error(request, "Access restricted to Hospital Coordinators and Administrators.")
        return redirect('dashboard')
        
    hospital = profile.hospital if profile and profile.hospital else Hospital.objects.first()
    
    available_organs = AvailableOrgan.objects.filter(status='AVAILABLE').order_by('harvested_at')
    allocated_organs = AvailableOrgan.objects.filter(status__in=['ALLOCATED', 'IN_TRANSIT']).order_by('-created_at')[:10]
    donors = DonorRecord.objects.all().order_by('-created_at')[:10]
    
    return render(request, 'hospital/dashboard.html', {
        'hospital': hospital,
        'available_organs': available_organs,
        'allocated_organs': allocated_organs,
        'donors': donors,
    })


@login_required
def register_donor_view(request):
    profile = getattr(request.user, 'profile', None)
    initial_hospital = profile.hospital if profile and profile.hospital else Hospital.objects.first()
    
    if request.method == 'POST':
        form = DonorRecordForm(request.POST)
        if form.is_valid():
            donor = form.save(commit=False)
            donor.donor_code = f"DNR-{timezone.now().year}-{uuid.uuid4().hex[:6].upper()}"
            donor.save()
            
            AuditLog.objects.create(
                actor=request.user,
                actor_role='HOSPITAL',
                action='DONOR_REGISTERED',
                to_state='REGISTERED',
                comments=f"Donor record created: {donor.donor_code} ({donor.donor_name}, {donor.blood_group})"
            )
            
            messages.success(request, f"Donor {donor.donor_code} successfully registered!")
            return redirect('hospital_dashboard')
    else:
        form = DonorRecordForm(initial={'hospital': initial_hospital})
        
    return render(request, 'hospital/register_donor.html', {'form': form})


@login_required
def register_organ_view(request):
    profile = getattr(request.user, 'profile', None)
    initial_hospital = profile.hospital if profile and profile.hospital else Hospital.objects.first()

    if request.method == 'POST':
        form = AvailableOrganForm(request.POST)
        if form.is_valid():
            organ = form.save(commit=False)
            organ.organ_id = f"ORG-{organ.organ_type[:3]}-{uuid.uuid4().hex[:6].upper()}"
            organ.status = 'AVAILABLE'
            organ.save()
            
            AuditLog.objects.create(
                organ=organ,
                actor=request.user,
                actor_role='HOSPITAL',
                action='ORGAN_HARVESTED',
                from_state='',
                to_state='AVAILABLE',
                comments=f"Organ {organ.organ_id} ({organ.organ_type}, {organ.blood_group}) harvested & placed in inventory"
            )
            
            messages.success(request, f"Organ {organ.organ_id} registered and available for matching!")
            return redirect('matching_engine_view', organ_id=organ.id)
    else:
        form = AvailableOrganForm(initial={
            'hospital': initial_hospital,
            'harvested_at': timezone.now().strftime("%Y-%m-%dT%H:%M")
        })
        
    return render(request, 'hospital/register_organ.html', {'form': form})


@login_required
def matching_engine_view(request, organ_id):
    """
    Core matching engine interface:
    Evaluates waiting pool candidates and presents transparent algorithm scoring breakdown.
    """
    organ = get_object_or_404(AvailableOrgan, pk=organ_id)
    candidates = find_eligible_candidates(organ)
    
    return render(request, 'hospital/matching_engine.html', {
        'organ': organ,
        'candidates': candidates,
    })


@login_required
def execute_match_view(request, organ_id, request_id):
    """
    Triggers execution of automated allocation binding the selected candidate to the organ.
    """
    organ = get_object_or_404(AvailableOrgan, pk=organ_id)
    target_request = get_object_or_404(OrganRequest, pk=request_id)
    
    try:
        result = execute_organ_allocation(
            organ=organ,
            target_request=target_request,
            actor=request.user,
            comments="Allocation confirmed via Hospital Host Matching Engine."
        )
        messages.success(request, result['message'])
    except Exception as e:
        messages.error(request, f"Allocation Failed: {str(e)}")
        
    return redirect('hospital_dashboard')


# ==========================================
# 4. MORTUARY MODULE VIEWS
# ==========================================

@login_required
def mortuary_dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role not in ['MORTUARY', 'ADMIN'] and not request.user.is_superuser:
        messages.error(request, "Access restricted to Mortuary Staff and Administrators.")
        return redirect('dashboard')
        
    records = MortuaryRecord.objects.all().order_by('-created_at')[:30]
    potential_donors = MortuaryRecord.objects.filter(is_potential_donor=True).order_by('-created_at')
    
    return render(request, 'mortuary/dashboard.html', {
        'records': records,
        'potential_donors': potential_donors,
    })


@login_required
def create_mortuary_record(request):
    profile = getattr(request.user, 'profile', None)
    initial_hospital = profile.hospital if profile and profile.hospital else Hospital.objects.first()

    if request.method == 'POST':
        form = MortuaryRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.case_number = f"MORT-{timezone.now().year}-{uuid.uuid4().hex[:6].upper()}"
            rec.recorded_by = request.user
            rec.save()
            
            AuditLog.objects.create(
                mortuary_record=rec,
                actor=request.user,
                actor_role='MORTUARY',
                action='MORTUARY_CASE_LOGGED',
                to_state='RECORDED',
                comments=f"Deceased intake logged: {rec.case_number} ({rec.deceased_name}). Potential donor: {rec.is_potential_donor}"
            )
            
            # If flagged as potential donor right away, alert coordinators
            if rec.is_potential_donor and rec.alert_sent_to_hospital:
                _trigger_mortuary_donation_alert(rec, request.user)
                
            messages.success(request, f"Mortuary intake case {rec.case_number} recorded.")
            return redirect('mortuary_dashboard')
    else:
        form = MortuaryRecordForm(initial={
            'hospital': initial_hospital,
            'time_of_death': timezone.now().strftime("%Y-%m-%dT%H:%M")
        })
        
    return render(request, 'mortuary/create_record.html', {'form': form})


@login_required
def trigger_donation_from_mortuary(request, pk):
    rec = get_object_or_404(MortuaryRecord, pk=pk)
    
    if request.method == 'POST':
        rec.is_potential_donor = True
        rec.donor_status_verified = True
        rec.donor_flag_reason = request.POST.get('donor_flag_reason', rec.donor_flag_reason)
        rec.organs_harvestable = request.POST.get('organs_harvestable', rec.organs_harvestable)
        rec.alert_sent_to_hospital = True
        rec.alert_sent_at = timezone.now()
        rec.save()
        
        _trigger_mortuary_donation_alert(rec, request.user)
        messages.success(request, f"Potential donor alert dispatched to Hospital Transplant Team for Case {rec.case_number}!")
        return redirect('mortuary_dashboard')
        
    return render(request, 'mortuary/trigger_donation.html', {'rec': rec})


def _trigger_mortuary_donation_alert(rec, actor):
    """
    Helper to create DonorRecord from Mortuary case and dispatch urgent alerts.
    """
    # Create or link donor record
    donor, created = DonorRecord.objects.get_or_create(
        donor_code=f"DNR-CAD-{rec.case_number[-6:]}",
        defaults={
            'donor_name': f"Deceased {rec.deceased_name}",
            'donor_type': 'DECEASED',
            'blood_group': rec.blood_group,
            'age': rec.age,
            'gender': rec.gender,
            'hospital': rec.hospital,
            'cause_of_death': rec.cause_of_death,
            'time_of_death': rec.time_of_death,
            'family_consent_verified': rec.donor_status_verified,
            'legal_clearance': True,
            'medical_notes': f"Source: Mortuary Case {rec.case_number}. Organs harvestable: {rec.organs_harvestable}. Reason: {rec.donor_flag_reason}"
        }
    )
    rec.linked_donor_record = donor
    rec.alert_sent_to_hospital = True
    rec.alert_sent_at = timezone.now()
    rec.save()
    
    AuditLog.objects.create(
        mortuary_record=rec,
        actor=actor,
        actor_role='MORTUARY',
        action='MORTUARY_DONOR_ALERT',
        to_state='DONOR_TRIGGERED',
        comments=f"Urgent Organ Donation Alert sent to {rec.hospital.name}. Harvestable: {rec.organs_harvestable}"
    )
    
    # Alert Hospital staff
    hospital_staff = rec.hospital.staff_members.all()
    for staff in hospital_staff:
        Notification.objects.create(
            recipient=staff.user,
            title="URGENT: CADAVERIC ORGAN DONOR ALERT FROM MORTUARY",
            message=(
                f"Mortuary Staff alerted a verified deceased donor ({rec.deceased_name}, {rec.blood_group}, age {rec.age}) "
                f"at {rec.mortuary_room_location}. Viable organs: {rec.organs_harvestable or 'Kidney, Liver, Cornea'}. "
                f"Dispatch harvest team immediately."
            ),
            category='EMERGENCY'
        )


# ==========================================
# 5. AUDIT LOG & COMPLIANCE VIEWS
# ==========================================

@login_required
def audit_log_view(request):
    logs = AuditLog.objects.all().select_related('request', 'organ', 'mortuary_record', 'actor')[:100]
    return render(request, 'audit/log_viewer.html', {'logs': logs})


@login_required
def admin_overview(request):
    if not request.user.is_superuser and getattr(getattr(request.user, 'profile', None), 'role', '') != 'ADMIN':
        messages.warning(request, "Admin overview restricted to system administrators.")
        return redirect('dashboard')
        
    return render(request, 'admin_overview.html', {
        'total_users': User.objects.count(),
        'total_requests': OrganRequest.objects.count(),
        'total_organs': AvailableOrgan.objects.count(),
        'total_donors': DonorRecord.objects.count(),
        'total_mortuary': MortuaryRecord.objects.count(),
        'recent_logs': AuditLog.objects.all()[:15],
    })


# ==========================================
# 6. NOTIFICATION AJAX / ACTIONS
# ==========================================

@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.info(request, "All notifications marked as read.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
