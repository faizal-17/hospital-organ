from django.contrib import admin
from .models import (
    Hospital, UserProfile, DonorRecord, AvailableOrgan,
    OrganRequest, MortuaryRecord, AuditLog, Notification
)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'state', 'contact_phone', 'is_transplant_center')
    search_fields = ('name', 'code', 'city')
    list_filter = ('is_transplant_center', 'state')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'blood_group', 'phone', 'hospital', 'national_id')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'national_id', 'phone')
    list_filter = ('role', 'blood_group', 'hospital')


@admin.register(DonorRecord)
class DonorRecordAdmin(admin.ModelAdmin):
    list_display = ('donor_code', 'donor_name', 'donor_type', 'blood_group', 'age', 'hospital', 'created_at')
    search_fields = ('donor_code', 'donor_name', 'cause_of_death')
    list_filter = ('donor_type', 'blood_group', 'hospital', 'family_consent_verified')


@admin.register(AvailableOrgan)
class AvailableOrganAdmin(admin.ModelAdmin):
    list_display = ('organ_id', 'organ_type', 'blood_group', 'condition_grade', 'status', 'hospital', 'harvested_at', 'viability_hours')
    search_fields = ('organ_id', 'donor__donor_code')
    list_filter = ('organ_type', 'blood_group', 'status', 'condition_grade')


@admin.register(OrganRequest)
class OrganRequestAdmin(admin.ModelAdmin):
    list_display = ('request_code', 'patient', 'organ', 'blood_group', 'priority_level', 'status', 'hospital', 'created_at')
    search_fields = ('request_code', 'patient__username', 'patient__first_name', 'patient__last_name', 'govt_approval_number')
    list_filter = ('status', 'priority_level', 'organ', 'blood_group', 'hospital')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MortuaryRecord)
class MortuaryRecordAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'deceased_name', 'blood_group', 'mortuary_room_location', 'is_potential_donor', 'donor_status_verified', 'alert_sent_to_hospital')
    search_fields = ('case_number', 'deceased_name', 'cause_of_death')
    list_filter = ('is_potential_donor', 'donor_status_verified', 'alert_sent_to_hospital', 'blood_group')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'actor', 'actor_role', 'from_state', 'to_state', 'request', 'organ')
    search_fields = ('action', 'actor__username', 'comments', 'from_state', 'to_state')
    list_filter = ('actor_role', 'action')
    readonly_fields = ('timestamp',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'category', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    list_filter = ('category', 'is_read')
