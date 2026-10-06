from django.urls import path
from . import views

urlpatterns = [
    # Public & Auth
    path('', views.landing_page, name='landing'),
    path('register/', views.patient_register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('demo-switch/<str:role>/', views.switch_demo_role, name='switch_demo_role'),
    path('dashboard/', views.dashboard_router, name='dashboard'),
    
    # 1. Patient Module
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/request/submit/', views.submit_organ_request, name='submit_organ_request'),
    path('patient/profile/', views.patient_profile_view, name='patient_profile'),
    path('request/<int:pk>/', views.request_detail_view, name='request_detail'),
    
    # 2. Doctor & Government Authorization Module
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/review/<int:pk>/', views.doctor_review_request, name='doctor_review'),
    path('govt/dashboard/', views.govt_dashboard, name='govt_dashboard'),
    path('govt/review/<int:pk>/', views.govt_review_request, name='govt_review'),
    path('certificate/<int:pk>/pdf/', views.download_certificate_pdf, name='download_certificate_pdf'),
    path('certificate/<int:pk>/view/', views.view_certificate_html, name='view_certificate_html'),
    
    # 3. Hospital (Host) Module & Matching Engine
    path('hospital/dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    path('hospital/donor/register/', views.register_donor_view, name='register_donor'),
    path('hospital/organ/register/', views.register_organ_view, name='register_organ'),
    path('hospital/matching/<int:organ_id>/', views.matching_engine_view, name='matching_engine_view'),
    path('hospital/match/<int:organ_id>/execute/<int:request_id>/', views.execute_match_view, name='execute_match'),
    
    # 4. Mortuary Module
    path('mortuary/dashboard/', views.mortuary_dashboard, name='mortuary_dashboard'),
    path('mortuary/create/', views.create_mortuary_record, name='create_mortuary_record'),
    path('mortuary/trigger/<int:pk>/', views.trigger_donation_from_mortuary, name='trigger_donation'),
    
    # 5. Audit Log & Admin Overview
    path('audit/logs/', views.audit_log_view, name='audit_logs'),
    path('admin-overview/', views.admin_overview, name='admin_overview'),
    
    # Notifications
    path('notification/read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notification/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
