from .models import Notification, OrganRequest, AvailableOrgan

def global_context(request):
    """
    Supplies global stats, user profile role, and notification alerts to all templates.
    """
    context = {
        'user_role': 'ANONYMOUS',
        'user_profile': None,
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'stats': {
            'total_requests': OrganRequest.objects.count(),
            'pending_doctor': OrganRequest.objects.filter(status='SUBMITTED').count(),
            'pending_govt': OrganRequest.objects.filter(status='DOCTOR_VERIFIED').count(),
            'govt_approved': OrganRequest.objects.filter(status='GOVT_APPROVED').count(),
            'allocated_matches': OrganRequest.objects.filter(status='ALLOCATED').count(),
            'available_organs': AvailableOrgan.objects.filter(status='AVAILABLE').count(),
        }
    }
    
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            context['user_role'] = profile.role
            context['user_profile'] = profile
        elif request.user.is_superuser:
            context['user_role'] = 'ADMIN'
            
        unread_notifs = Notification.objects.filter(recipient=request.user, is_read=False)
        context['unread_notifications_count'] = unread_notifs.count()
        context['recent_notifications'] = Notification.objects.filter(recipient=request.user)[:5]
        
    return context
