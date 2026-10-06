from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from organ_app.models import (
    Hospital, UserProfile, DonorRecord, AvailableOrgan,
    OrganRequest, MortuaryRecord, AuditLog, Notification
)
from organ_app.matching_service import (
    calculate_allocation_score, find_eligible_candidates,
    execute_organ_allocation
)
from organ_app.certificate_service import generate_approval_certificate_pdf


class OrganAllocationSystemTests(TestCase):
    def setUp(self):
        # 1. Hospital
        self.hospital = Hospital.objects.create(
            name="City Hope Hospital",
            code="HOSP-TEST",
            license_number="LIC-1234",
            address="123 Health St",
            city="Metropolis",
            state="Central",
            contact_phone="1234567890",
            contact_email="hospital@test.com"
        )

        # 2. Users
        self.patient_user = User.objects.create_user(
            username="patient_test",
            password="pass1234",
            first_name="Alice",
            last_name="Smith"
        )
        self.patient_profile = UserProfile.objects.create(
            user=self.patient_user,
            role="PATIENT",
            blood_group="O+",
            national_id="NAT-1111",
            phone="9998887776"
        )

        self.doctor_user = User.objects.create_user(
            username="doctor_test",
            password="pass1234",
            first_name="Dr. Gregory",
            last_name="House"
        )
        self.doctor_profile = UserProfile.objects.create(
            user=self.doctor_user,
            role="DOCTOR",
            hospital=self.hospital,
            license_or_emp_id="DOC-999"
        )

        self.govt_user = User.objects.create_user(
            username="govt_test",
            password="pass1234",
            first_name="Govt Official",
            last_name="Admin"
        )
        self.govt_profile = UserProfile.objects.create(
            user=self.govt_user,
            role="GOVT"
        )

        # 3. Donor & Organ
        self.donor = DonorRecord.objects.create(
            donor_code="DNR-TEST-01",
            donor_name="Deceased Test Donor",
            blood_group="O+",
            age=35,
            gender="MALE",
            hospital=self.hospital
        )

        self.organ = AvailableOrgan.objects.create(
            organ_id="ORG-TEST-KID",
            donor=self.donor,
            hospital=self.hospital,
            organ_type="KIDNEY",
            blood_group="O+",
            viability_hours=24,
            status="AVAILABLE"
        )

        # 4. Patient Organ Requests
        self.req_emergency = OrganRequest.objects.create(
            request_code="REQ-EMERGENCY",
            patient=self.patient_user,
            hospital=self.hospital,
            organ="KIDNEY",
            blood_group="O+",
            medical_history="Severe Renal Failure",
            status="GOVT_APPROVED",
            priority_level="EMERGENCY",
            govt_approval_number="GOV-AUTH-TEST-001"
        )

        # Create a second patient with NORMAL priority to verify algorithm ranking
        self.patient2 = User.objects.create_user(
            username="patient_normal",
            password="pass1234",
            first_name="Bob",
            last_name="Jones"
        )
        UserProfile.objects.create(
            user=self.patient2,
            role="PATIENT",
            blood_group="O+"
        )
        self.req_normal = OrganRequest.objects.create(
            request_code="REQ-NORMAL",
            patient=self.patient2,
            hospital=self.hospital,
            organ="KIDNEY",
            blood_group="O+",
            medical_history="Kidney condition stage 4",
            status="GOVT_APPROVED",
            priority_level="NORMAL",
            govt_approval_number="GOV-AUTH-TEST-002"
        )

    def test_allocation_scoring_and_ranking(self):
        """Test that the matching engine ranks Emergency above Normal."""
        candidates = find_eligible_candidates(self.organ)
        self.assertEqual(len(candidates), 2)
        # Rank 1 must be emergency
        self.assertEqual(candidates[0]['request'].request_code, "REQ-EMERGENCY")
        self.assertEqual(candidates[0]['rank'], 1)
        self.assertGreater(candidates[0]['total_score'], candidates[1]['total_score'])
        self.assertEqual(candidates[0]['priority_score'], 1000)
        self.assertEqual(candidates[1]['priority_score'], 100)

    def test_strict_blood_group_filter(self):
        """Candidates with different blood groups must be excluded."""
        diff_blood_req = OrganRequest.objects.create(
            request_code="REQ-AB-BLOOD",
            patient=self.patient2,
            hospital=self.hospital,
            organ="KIDNEY",
            blood_group="AB+",
            medical_history="AB blood test",
            status="GOVT_APPROVED",
            priority_level="EMERGENCY"
        )
        candidates = find_eligible_candidates(self.organ)
        req_codes = [c['request'].request_code for c in candidates]
        self.assertNotIn("REQ-AB-BLOOD", req_codes)

    def test_government_approval_filter(self):
        """Requests without Government Approval (e.g. SUBMITTED or DOCTOR_VERIFIED) must not be ranked."""
        unapproved_req = OrganRequest.objects.create(
            request_code="REQ-NOT-GOVT",
            patient=self.patient2,
            hospital=self.hospital,
            organ="KIDNEY",
            blood_group="O+",
            medical_history="Unapproved test",
            status="DOCTOR_VERIFIED",
            priority_level="EMERGENCY"
        )
        candidates = find_eligible_candidates(self.organ)
        req_codes = [c['request'].request_code for c in candidates]
        self.assertNotIn("REQ-NOT-GOVT", req_codes)

    def test_execute_allocation(self):
        """Test binding organ to request updates state and creates audit log."""
        result = execute_organ_allocation(
            organ=self.organ,
            target_request=self.req_emergency,
            actor=self.doctor_user,
            comments="Test allocation execution"
        )
        self.assertEqual(result['status'], 'success')

        # Reload from db
        self.req_emergency.refresh_from_db()
        self.organ.refresh_from_db()

        self.assertEqual(self.req_emergency.status, 'ALLOCATED')
        self.assertEqual(self.organ.status, 'ALLOCATED')
        self.assertEqual(self.req_emergency.allocated_organ, self.organ)

        # Verify Audit Log
        audit = AuditLog.objects.filter(request=self.req_emergency, action='MATCH_ALLOCATED').first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.to_state, 'ALLOCATED')

        # Verify In-App Notification
        notif = Notification.objects.filter(recipient=self.patient_user, category='EMERGENCY').first()
        self.assertIsNotNone(notif)
        self.assertIn("Organ Match Found", notif.title)

    def test_pdf_certificate_generation(self):
        """Test ReportLab PDF certificate generation produces valid PDF bytes."""
        pdf_buffer = generate_approval_certificate_pdf(self.req_emergency)
        pdf_bytes = pdf_buffer.getvalue()
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_http_views(self):
        """Test core views return HTTP 200."""
        client = Client()

        # Landing page
        response = client.get('/')
        self.assertEqual(response.status_code, 200)

        # Login page
        response = client.get('/login/')
        self.assertEqual(response.status_code, 200)

        # Patient authenticated dashboard
        client.force_login(self.patient_user)
        response = client.get('/patient/dashboard/')
        self.assertEqual(response.status_code, 200)

        # Request detail view
        response = client.get(f'/request/{self.req_emergency.id}/')
        self.assertEqual(response.status_code, 200)

        # Doctor authenticated dashboard
        client.force_login(self.doctor_user)
        response = client.get('/doctor/dashboard/')
        self.assertEqual(response.status_code, 200)

        # Matching engine view
        response = client.get(f'/hospital/matching/{self.organ.id}/')
        self.assertEqual(response.status_code, 200)

        # Audit logs view
        response = client.get('/audit/logs/')
        self.assertEqual(response.status_code, 200)
