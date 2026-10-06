"""
Automated Organ Allocation Service Engine
Implements multi-parameter weighted scoring algorithm:
1. Medical Priority (Emergency: 1000, High: 500, Normal: 100)
2. Blood Group Compatibility (Strict Match required)
3. Government Approval Status (Must be 'GOVT_APPROVED')
4. Waiting Time (FIFO tie-breaker based on days accrued in waiting pool)
"""

from django.utils import timezone
from .models import OrganRequest, AvailableOrgan, AuditLog, Notification


PRIORITY_WEIGHTS = {
    'EMERGENCY': 1000,
    'HIGH': 500,
    'NORMAL': 100,
}


def calculate_allocation_score(request, organ):
    """
    Calculates detailed allocation score for a candidate organ request
    against a specific available organ.
    
    Score Formula:
    Total Score = Priority Score + Waiting Time Points
    Waiting Time Points = 5 points per 24 hours (1 day) of verified wait time
    """
    priority_score = PRIORITY_WEIGHTS.get(request.priority_level, 100)
    
    # Calculate waiting time in days
    waiting_seconds = (timezone.now() - request.created_at).total_seconds()
    waiting_days = max(0.0, waiting_seconds / 86400.0)
    
    # 5 points per day waiting bonus
    waiting_score = round(waiting_days * 5.0, 2)
    
    total_score = priority_score + waiting_score
    
    return {
        'priority_level': request.priority_level,
        'priority_score': priority_score,
        'waiting_days': round(waiting_days, 2),
        'waiting_score': waiting_score,
        'total_score': round(total_score, 2),
    }


def find_eligible_candidates(organ):
    """
    Queries and ranks all eligible patients waiting for this specific organ.
    Strict Criteria:
    - Same organ type (e.g. KIDNEY, HEART)
    - Strict blood group match (request.blood_group == organ.blood_group)
    - Government Status == GOVT_APPROVED
    - Currently not allocated to another organ
    """
    # Active candidates requiring this organ
    candidates_qs = OrganRequest.objects.filter(
        organ=organ.organ_type,
        blood_group=organ.blood_group,
        status='GOVT_APPROVED',
        allocated_organ__isnull=True
    ).select_related('patient', 'patient__profile', 'hospital')
    
    ranked_list = []
    
    for candidate in candidates_qs:
        score_details = calculate_allocation_score(candidate, organ)
        ranked_list.append({
            'request': candidate,
            'patient_name': candidate.patient.get_full_name() or candidate.patient.username,
            'hospital_name': candidate.hospital.name,
            'blood_group': candidate.blood_group,
            'organ': candidate.organ,
            'priority_level': candidate.priority_level,
            'priority_score': score_details['priority_score'],
            'waiting_days': score_details['waiting_days'],
            'waiting_score': score_details['waiting_score'],
            'total_score': score_details['total_score'],
            'created_at': candidate.created_at,
        })
    
    # Sorting:
    # 1. Total score descending
    # 2. Created_at ascending (FIFO tie-breaker)
    ranked_list.sort(
        key=lambda item: (-item['total_score'], item['created_at'])
    )
    
    # Assign ranks
    for index, item in enumerate(ranked_list, start=1):
        item['rank'] = index
        
    return ranked_list


def execute_organ_allocation(organ, target_request, actor=None, comments=""):
    """
    Executes and binds an organ to a matched patient request:
    - Validates state
    - Updates request status to 'ALLOCATED'
    - Updates organ status to 'ALLOCATED'
    - Writes legal AuditLog entry
    - Sends automated simulated notifications to Patient, Hospital, and Transplant Teams
    """
    if organ.status != 'AVAILABLE':
        raise ValueError(f"Organ {organ.organ_id} is not currently available (status: {organ.status})")
    
    if target_request.status != 'GOVT_APPROVED':
        raise ValueError(f"Request {target_request.request_code} is not Government Approved")
        
    if target_request.blood_group != organ.blood_group or target_request.organ != organ.organ_type:
        raise ValueError("Incompatible blood group or organ type mismatch")

    from_state_req = target_request.status
    from_state_org = organ.status
    
    # Transition states
    now = timezone.now()
    target_request.status = 'ALLOCATED'
    target_request.allocated_organ = organ
    target_request.allocated_at = now
    target_request.save()
    
    organ.status = 'ALLOCATED'
    organ.allocated_request = target_request
    organ.save()
    
    # Calculate final allocation score
    score_info = calculate_allocation_score(target_request, organ)
    
    audit_notes = (
        f"Automated Allocation Match Executed. Organ {organ.organ_id} ({organ.organ_type}, {organ.blood_group}) "
        f"allocated to Request {target_request.request_code} (Patient: {target_request.patient.username}). "
        f"Score: {score_info['total_score']} [Priority: {score_info['priority_score']}, "
        f"Wait: {score_info['waiting_days']} days]. {comments}"
    )
    
    # Log state transition in AuditLog
    AuditLog.objects.create(
        request=target_request,
        organ=organ,
        actor=actor,
        actor_role=getattr(getattr(actor, 'profile', None), 'role', 'SYSTEM'),
        action='MATCH_ALLOCATED',
        from_state=from_state_req,
        to_state='ALLOCATED',
        comments=audit_notes
    )
    
    # Simulated Notification to Patient
    Notification.objects.create(
        recipient=target_request.patient,
        title="CRITICAL ALERT: Organ Match Found & Allocated!",
        message=(
            f"Dear {target_request.patient.get_full_name() or target_request.patient.username}, "
            f"a compatible {organ.get_organ_type_display()} ({organ.blood_group}) has been officially allocated "
            f"to your request ({target_request.request_code}) from {organ.hospital.name}. "
            f"Please report immediately to {target_request.hospital.name} transplant unit."
        ),
        category='EMERGENCY',
        related_request=target_request
    )
    
    # Notification to Hospital Team / Staff
    hospital_staff = target_request.hospital.staff_members.all()
    for staff in hospital_staff:
        Notification.objects.create(
            recipient=staff.user,
            title="NEW TRANSPLANT ALLOCATION ASSIGNED",
            message=(
                f"Organ {organ.organ_id} ({organ.organ_type}) matched to patient "
                f"{target_request.patient.get_full_name() or target_request.patient.username} "
                f"({target_request.request_code}). Prepare operating theater and organ transfer."
            ),
            category='EMERGENCY',
            related_request=target_request
        )
        
    return {
        'status': 'success',
        'request': target_request,
        'organ': organ,
        'score_info': score_info,
        'message': f"Organ {organ.organ_id} successfully allocated to {target_request.request_code}"
    }
