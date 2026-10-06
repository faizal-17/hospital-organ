"""
Seed Data Script for Hospital Organ Request and Government Approval Management System
Populates:
- Hospitals
- Users across 5 Roles (Patient, Doctor, Government Official, Hospital Host, Mortuary Staff, Admin)
- Organ Requests across multiple workflow states (Submitted, Doctor Verified, Govt Approved, Allocated)
- Mortuary Deceased Records & Organ Donation Triggers
- Enrolled Donor Records
- Available Organs in Inventory ready for the Automated Matching Engine
- Notifications & Statutory Audit Logs
"""

import os
import sys
import django
from datetime import timedelta

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'organ_system.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from organ_app.models import (
    Hospital, UserProfile, DonorRecord, AvailableOrgan,
    OrganRequest, MortuaryRecord, AuditLog, Notification
)


def seed_all():
    print("==================================================")
    print("Seeding OrganSync Prototype Database...")
    print("==================================================")

    # 1. Hospitals
    hospitals_data = [
        {
            'name': 'City Hope Multispeciality & Transplant Center',
            'code': 'HOSP-001',
            'license_number': 'LIC-MED-2024-9081',
            'address': '104 Healthcare Boulevard, Medical District',
            'city': 'Metro City',
            'state': 'Capital State',
            'contact_phone': '+1 555-0100',
            'contact_email': 'transplants@cityhope.org',
            'is_transplant_center': True,
        },
        {
            'name': 'St. Jude National Organ Institute',
            'code': 'HOSP-002',
            'license_number': 'LIC-MED-2023-4512',
            'address': '78 University Medical Way',
            'city': 'North Port',
            'state': 'Capital State',
            'contact_phone': '+1 555-0200',
            'contact_email': 'info@stjude-organ.org',
            'is_transplant_center': True,
        },
        {
            'name': 'Apex Memorial Healthcare',
            'code': 'HOSP-003',
            'license_number': 'LIC-MED-2025-1102',
            'address': '22 South Ridge Road',
            'city': 'Apex City',
            'state': 'Capital State',
            'contact_phone': '+1 555-0300',
            'contact_email': 'contact@apexhealth.org',
            'is_transplant_center': True,
        }
    ]

    hospitals = {}
    for h_data in hospitals_data:
        hosp, created = Hospital.objects.update_or_create(
            code=h_data['code'],
            defaults=h_data
        )
        hospitals[h_data['code']] = hosp
        print(f"[{'CREATED' if created else 'UPDATED'}] Hospital: {hosp.name}")

    # 2. Users & Profiles
    users_data = [
        # Admin
        {
            'username': 'admin',
            'first_name': 'System',
            'last_name': 'Administrator',
            'email': 'admin@organsync.gov',
            'is_staff': True,
            'is_superuser': True,
            'role': 'ADMIN',
            'phone': '+1 555-9999',
            'national_id': 'GOV-ADM-001'
        },
        # Patients
        {
            'username': 'patient1',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@patient.org',
            'role': 'PATIENT',
            'blood_group': 'O+',
            'phone': '+1 555-1001',
            'national_id': 'NAT-8921-4321',
            'address': '12 Oak Ridge Lane, Metro City',
            'emergency_contact_name': 'Mary Doe (Spouse)',
            'emergency_contact_phone': '+1 555-1002'
        },
        {
            'username': 'patient2',
            'first_name': 'Sarah',
            'last_name': 'Connor',
            'email': 'sarah.connor@patient.org',
            'role': 'PATIENT',
            'blood_group': 'A+',
            'phone': '+1 555-2001',
            'national_id': 'NAT-5612-8812',
            'address': '45 Highland Terrace',
            'emergency_contact_name': 'John Connor (Son)',
            'emergency_contact_phone': '+1 555-2002'
        },
        {
            'username': 'patient3',
            'first_name': 'David',
            'last_name': 'Miller',
            'email': 'david.miller@patient.org',
            'role': 'PATIENT',
            'blood_group': 'B+',
            'phone': '+1 555-3001',
            'national_id': 'NAT-1092-3482',
            'address': '98 Sunset Blvd',
            'emergency_contact_name': 'Alice Miller (Wife)',
            'emergency_contact_phone': '+1 555-3002'
        },
        {
            'username': 'patient4',
            'first_name': 'Emily',
            'last_name': 'Watson',
            'email': 'emily.watson@patient.org',
            'role': 'PATIENT',
            'blood_group': 'O+',
            'phone': '+1 555-4001',
            'national_id': 'NAT-4421-9921',
            'address': '72 Pinecrest Avenue',
            'emergency_contact_name': 'Thomas Watson (Brother)',
            'emergency_contact_phone': '+1 555-4002'
        },
        {
            'username': 'patient5',
            'first_name': 'Marcus',
            'last_name': 'Vance',
            'email': 'marcus.vance@patient.org',
            'role': 'PATIENT',
            'blood_group': 'AB+',
            'phone': '+1 555-5001',
            'national_id': 'NAT-3321-7711',
            'address': '15 Riverbank Road',
            'emergency_contact_name': 'Claire Vance',
            'emergency_contact_phone': '+1 555-5002'
        },
        # Doctors
        {
            'username': 'doctor1',
            'first_name': 'Dr. Evelyn',
            'last_name': 'Reed, MD',
            'email': 'dr.reed@cityhope.org',
            'role': 'DOCTOR',
            'hospital': hospitals['HOSP-001'],
            'license_or_emp_id': 'SURG-LIC-88214',
            'phone': '+1 555-0105'
        },
        {
            'username': 'doctor2',
            'first_name': 'Dr. Alistair',
            'last_name': 'Chen, MD',
            'email': 'dr.chen@stjude.org',
            'role': 'DOCTOR',
            'hospital': hospitals['HOSP-002'],
            'license_or_emp_id': 'HEP-LIC-44102',
            'phone': '+1 555-0205'
        },
        # Government Officials
        {
            'username': 'govt1',
            'first_name': 'Hon. Arthur',
            'last_name': 'Vance',
            'email': 'arthur.vance@health.gov',
            'role': 'GOVT',
            'license_or_emp_id': 'GOV-COMM-AUTH-09',
            'phone': '+1 555-8001'
        },
        # Hospital Host Coordinators
        {
            'username': 'hospital1',
            'first_name': 'Elena',
            'last_name': 'Rostova',
            'email': 'coordinator@cityhope.org',
            'role': 'HOSPITAL',
            'hospital': hospitals['HOSP-001'],
            'license_or_emp_id': 'TX-COORD-109',
            'phone': '+1 555-0108'
        },
        # Mortuary Staff
        {
            'username': 'mortuary1',
            'first_name': 'Robert',
            'last_name': 'Hayes',
            'email': 'mortuary@cityhope.org',
            'role': 'MORTUARY',
            'hospital': hospitals['HOSP-001'],
            'license_or_emp_id': 'MORT-OFFICER-44',
            'phone': '+1 555-0109'
        }
    ]

    users = {}
    for u_data in users_data:
        role = u_data.pop('role')
        blood_group = u_data.pop('blood_group', '')
        hospital = u_data.pop('hospital', None)
        phone = u_data.pop('phone', '')
        national_id = u_data.pop('national_id', '')
        license_or_emp_id = u_data.pop('license_or_emp_id', '')
        address = u_data.pop('address', '')
        emergency_contact_name = u_data.pop('emergency_contact_name', '')
        emergency_contact_phone = u_data.pop('emergency_contact_phone', '')

        user, created = User.objects.update_or_create(
            username=u_data['username'],
            defaults=u_data
        )
        user.set_password('pass1234')
        user.save()
        users[user.username] = user

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'role': role,
                'blood_group': blood_group,
                'hospital': hospital,
                'phone': phone,
                'national_id': national_id,
                'license_or_emp_id': license_or_emp_id,
                'address': address,
                'emergency_contact_name': emergency_contact_name,
                'emergency_contact_phone': emergency_contact_phone,
            }
        )
        print(f"[{'CREATED' if created else 'UPDATED'}] User ({role}): {user.username} [Pass: pass1234]")

    now = timezone.now()

    # 3. Mortuary Records
    mort_cases = [
        {
            'case_number': 'MORT-2026-001',
            'deceased_name': 'James Sullivan',
            'deceased_id_number': 'MRN-781204',
            'age': 42,
            'gender': 'MALE',
            'blood_group': 'O+',
            'time_of_death': now - timedelta(hours=4),
            'cause_of_death': 'Severe Subarachnoid Hemorrhage following brain aneurysm rupture',
            'mortuary_room_location': 'Cold Unit Vault 3, Bay A',
            'hospital': hospitals['HOSP-001'],
            'recorded_by': users['mortuary1'],
            'is_potential_donor': True,
            'donor_flag_reason': 'Brain stem reflex cessation confirmed by two independent neurological reviews. Hemodynamics stabilized under ventilatory support prior to transfer.',
            'donor_status_verified': True,
            'organs_harvestable': 'Kidney, Liver, Cornea',
            'alert_sent_to_hospital': True,
            'alert_sent_at': now - timedelta(hours=3),
        },
        {
            'case_number': 'MORT-2026-002',
            'deceased_name': 'Walter Henderson',
            'deceased_id_number': 'MRN-441920',
            'age': 68,
            'gender': 'MALE',
            'blood_group': 'B+',
            'time_of_death': now - timedelta(hours=14),
            'cause_of_death': 'Cardiopulmonary arrest secondary to multi-organ failure',
            'mortuary_room_location': 'Cold Storage Unit 1, Rack C',
            'hospital': hospitals['HOSP-001'],
            'recorded_by': users['mortuary1'],
            'is_potential_donor': False,
            'donor_flag_reason': '',
            'donor_status_verified': False,
            'organs_harvestable': '',
            'alert_sent_to_hospital': False,
        }
    ]

    for m_data in mort_cases:
        m_rec, created = MortuaryRecord.objects.update_or_create(
            case_number=m_data['case_number'],
            defaults=m_data
        )
        print(f"[{'CREATED' if created else 'UPDATED'}] Mortuary Record: {m_rec.case_number}")

    # 4. Donor Records
    donor_cases = [
        {
            'donor_code': 'DNR-2026-001',
            'donor_name': 'Deceased James Sullivan',
            'donor_type': 'DECEASED',
            'blood_group': 'O+',
            'age': 42,
            'gender': 'MALE',
            'hospital': hospitals['HOSP-001'],
            'cause_of_death': 'Subarachnoid Hemorrhage',
            'time_of_death': now - timedelta(hours=4),
            'family_consent_verified': True,
            'legal_clearance': True,
            'medical_notes': 'HIV/HBV/HCV negative. Normal renal function. Serum creatinine 0.9 mg/dL. HLA-typing logged.',
        },
        {
            'donor_code': 'DNR-2026-002',
            'donor_name': 'Deceased Clara Oswald',
            'donor_type': 'DECEASED',
            'blood_group': 'A+',
            'age': 29,
            'gender': 'FEMALE',
            'hospital': hospitals['HOSP-002'],
            'cause_of_death': 'Traumatic Brain Injury (Road Accident)',
            'time_of_death': now - timedelta(hours=6),
            'family_consent_verified': True,
            'legal_clearance': True,
            'medical_notes': 'Optimal liver liver enzymes (AST: 24, ALT: 28). Normal bilirubin. Ultrasound normal parenchymal echo.',
        }
    ]

    donors = {}
    for d_data in donor_cases:
        d_rec, created = DonorRecord.objects.update_or_create(
            donor_code=d_data['donor_code'],
            defaults=d_data
        )
        donors[d_data['donor_code']] = d_rec
        print(f"[{'CREATED' if created else 'UPDATED'}] Donor Record: {d_rec.donor_code}")

    # 5. Available Organs in Inventory
    organs_data = [
        {
            'organ_id': 'ORG-KID-O-001',
            'donor': donors['DNR-2026-001'],
            'hospital': hospitals['HOSP-001'],
            'organ_type': 'KIDNEY',
            'blood_group': 'O+',
            'harvested_at': now - timedelta(hours=2),
            'viability_hours': 24,
            'condition_grade': 'EXCELLENT',
            'status': 'AVAILABLE',
            'storage_location': 'Machine Perfusion Bay 1 (City Hope)',
        },
        {
            'organ_id': 'ORG-LIV-A-002',
            'donor': donors['DNR-2026-002'],
            'hospital': hospitals['HOSP-002'],
            'organ_type': 'LIVER',
            'blood_group': 'A+',
            'harvested_at': now - timedelta(hours=3),
            'viability_hours': 12,
            'condition_grade': 'EXCELLENT',
            'status': 'AVAILABLE',
            'storage_location': 'Cold Static Preservation Unit 2 (St. Jude)',
        }
    ]

    for o_data in organs_data:
        organ, created = AvailableOrgan.objects.update_or_create(
            organ_id=o_data['organ_id'],
            defaults=o_data
        )
        print(f"[{'CREATED' if created else 'UPDATED'}] Available Organ: {organ.organ_id} ({organ.organ_type}, {organ.blood_group})")

    # 6. Organ Requests across Lifecycle States
    requests_data = [
        # Patient 1: O+ Kidney - Emergency priority, Govt Approved (Ready to match ORG-KID-O-001!)
        {
            'request_code': 'REQ-202601-KID01',
            'patient': users['patient1'],
            'hospital': hospitals['HOSP-001'],
            'organ': 'KIDNEY',
            'blood_group': 'O+',
            'medical_history': 'End-Stage Renal Disease (ESRD) secondary to bilateral focal segmental glomerulosclerosis. Dependent on hemodialysis 3x weekly since 18 months. Recurrent access thrombosis, refractory fluid overload.',
            'status': 'GOVT_APPROVED',
            'priority_level': 'EMERGENCY',
            'doctor_verified_by': users['doctor1'],
            'doctor_verified_at': now - timedelta(days=12),
            'doctor_notes': 'Critical priority confirmed. Patient experiencing vascular access exhaustion and recurrent pulmonary edema on dialysis. Immediate transplantation strongly indicated.',
            'govt_approved_by': users['govt1'],
            'govt_approved_at': now - timedelta(days=10),
            'govt_approval_number': 'GOV-AUTH-2026-78129',
            'govt_notes': 'Statutory verification completed. Form 10 and Form 16 examined. Ethical and anti-commercial clearances granted under Sec 9 Organ Transplant Act.',
            'created_at': now - timedelta(days=15),
        },
        # Patient 4: O+ Kidney - Normal priority, Govt Approved (Shows FIFO & Priority separation in algorithm!)
        {
            'request_code': 'REQ-202601-KID04',
            'patient': users['patient4'],
            'hospital': hospitals['HOSP-001'],
            'organ': 'KIDNEY',
            'blood_group': 'O+',
            'medical_history': 'Stage 5 Chronic Kidney Disease due to hypertensive nephrosclerosis. Peritoneal dialysis maintained with stable biochemistry.',
            'status': 'GOVT_APPROVED',
            'priority_level': 'NORMAL',
            'doctor_verified_by': users['doctor1'],
            'doctor_verified_at': now - timedelta(days=25),
            'doctor_notes': 'Stable on PD. Listed for deceased donor kidney transplant. Crossmatch panel reactive antibodies 0%.',
            'govt_approved_by': users['govt1'],
            'govt_approved_at': now - timedelta(days=22),
            'govt_approval_number': 'GOV-AUTH-2026-61023',
            'govt_notes': 'Central waiting registry approved. Statutory citizen verification clear.',
            'created_at': now - timedelta(days=30),
        },
        # Patient 2: A+ Liver - High priority, Govt Approved (Ready to match ORG-LIV-A-002!)
        {
            'request_code': 'REQ-202601-LIV02',
            'patient': users['patient2'],
            'hospital': hospitals['HOSP-002'],
            'organ': 'LIVER',
            'blood_group': 'A+',
            'medical_history': 'Decompensated Cirrhosis (MELD-Na score 29) secondary to primary sclerosing cholangitis. Refractory ascites, recurrent hepatic encephalopathy episodes.',
            'status': 'GOVT_APPROVED',
            'priority_level': 'HIGH',
            'doctor_verified_by': users['doctor2'],
            'doctor_verified_at': now - timedelta(days=8),
            'doctor_notes': 'High priority listing indicated. MELD score validated. Cardiovascular stress test cleared for major hepatic transplantation.',
            'govt_approved_by': users['govt1'],
            'govt_approved_at': now - timedelta(days=6),
            'govt_approval_number': 'GOV-AUTH-2026-90411',
            'govt_notes': 'Statutory authorization granted. Official compliance verified.',
            'created_at': now - timedelta(days=9),
        },
        # Patient 3: B+ Heart - Normal priority, Doctor Verified (Pending Government Official review!)
        {
            'request_code': 'REQ-202601-HRT03',
            'patient': users['patient3'],
            'hospital': hospitals['HOSP-001'],
            'organ': 'HEART',
            'blood_group': 'B+',
            'medical_history': 'Ischemic Dilated Cardiomyopathy with left ventricular ejection fraction 18%. NYHA functional class IV despite optimal guideline medical therapy.',
            'status': 'DOCTOR_VERIFIED',
            'priority_level': 'NORMAL',
            'doctor_verified_by': users['doctor1'],
            'doctor_verified_at': now - timedelta(days=2),
            'doctor_notes': 'Advanced heart failure confirmed. Right heart catheterization shows normal pulmonary vascular resistance. Approved for heart transplant registry.',
            'created_at': now - timedelta(days=4),
        },
        # Patient 5: AB+ Cornea / Organ - Submitted status (Awaiting Medical Doctor Review!)
        {
            'request_code': 'REQ-202601-LIV05',
            'patient': users['patient5'],
            'hospital': hospitals['HOSP-001'],
            'organ': 'LIVER',
            'blood_group': 'AB+',
            'medical_history': 'Early liver failure under diagnostic assessment. Referral from regional clinic for specialized tertiary evaluation.',
            'status': 'SUBMITTED',
            'priority_level': 'NORMAL',
            'created_at': now - timedelta(hours=12),
        }
    ]

    for req_d in requests_data:
        created_at = req_d.pop('created_at')
        req_obj, created = OrganRequest.objects.update_or_create(
            request_code=req_d['request_code'],
            defaults=req_d
        )
        # Update timestamp to simulate wait time accurately
        OrganRequest.objects.filter(id=req_obj.id).update(created_at=created_at)
        print(f"[{'CREATED' if created else 'UPDATED'}] Organ Request: {req_obj.request_code} [{req_obj.status}]")

    # 7. Seed Audit Logs
    audit_samples = [
        {
            'actor': users['patient1'],
            'actor_role': 'PATIENT',
            'action': 'REQUEST_SUBMITTED',
            'from_state': '',
            'to_state': 'SUBMITTED',
            'comments': 'Patient John Doe submitted initial organ request for Kidney (O+)',
        },
        {
            'actor': users['doctor1'],
            'actor_role': 'DOCTOR',
            'action': 'DOCTOR_VERIFIED',
            'from_state': 'SUBMITTED',
            'to_state': 'DOCTOR_VERIFIED',
            'comments': 'Dr. Evelyn Reed verified clinical necessity. Assigned Priority: EMERGENCY.',
        },
        {
            'actor': users['govt1'],
            'actor_role': 'GOVT',
            'action': 'GOVT_APPROVED',
            'from_state': 'DOCTOR_VERIFIED',
            'to_state': 'GOVT_APPROVED',
            'comments': 'Government Official Arthur Vance issued Statutory Approval Certificate #GOV-AUTH-2026-78129.',
        },
        {
            'actor': users['mortuary1'],
            'actor_role': 'MORTUARY',
            'action': 'MORTUARY_DONOR_ALERT',
            'from_state': 'RECORDED',
            'to_state': 'DONOR_TRIGGERED',
            'comments': 'Mortuary Unit triggered cadaveric donor alert for deceased James Sullivan (O+).',
        },
        {
            'actor': users['hospital1'],
            'actor_role': 'HOSPITAL',
            'action': 'ORGAN_HARVESTED',
            'from_state': '',
            'to_state': 'AVAILABLE',
            'comments': 'Procured Kidney (ORG-KID-O-001) added to central cold preservation inventory.',
        }
    ]

    for a_data in audit_samples:
        AuditLog.objects.create(**a_data)

    # 8. Seed Sample Notifications
    Notification.objects.create(
        recipient=users['patient1'],
        title="GOVERNMENT APPROVAL GRANTED",
        message="Statutory Authorization Certificate #GOV-AUTH-2026-78129 issued! You are in the active matching pool.",
        category='SUCCESS'
    )
    Notification.objects.create(
        recipient=users['doctor1'],
        title="NEW PATIENT DOSSIER AWAITING REVIEW",
        message="Patient Marcus Vance (REQ-202601-LIV05) submitted an organ request awaiting your clinical verification.",
        category='INFO'
    )
    Notification.objects.create(
        recipient=users['hospital1'],
        title="URGENT: CADAVERIC ORGAN DONOR ALERT FROM MORTUARY",
        message="Mortuary Staff alerted verified deceased donor (James Sullivan, O+) in Cold Unit Vault 3. Harvestable: Kidney, Liver, Cornea.",
        category='EMERGENCY'
    )

    print("==================================================")
    print("Database seeding completed successfully!")
    print("Test Personas Ready:")
    print("  - Patient:   Username 'patient1'  / Password 'pass1234'")
    print("  - Doctor:    Username 'doctor1'   / Password 'pass1234'")
    print("  - Govt:      Username 'govt1'     / Password 'pass1234'")
    print("  - Hospital:  Username 'hospital1' / Password 'pass1234'")
    print("  - Mortuary:  Username 'mortuary1' / Password 'pass1234'")
    print("  - Admin:     Username 'admin'     / Password 'pass1234'")
    print("==================================================")


if __name__ == '__main__':
    seed_all()
