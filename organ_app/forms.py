from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    UserProfile, OrganRequest, AvailableOrgan, DonorRecord,
    MortuaryRecord, Hospital, ORGAN_CHOICES, BLOOD_GROUP_CHOICES,
    PRIORITY_CHOICES
)


class PatientRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Choose password'}), required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}), required=True)
    
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555-0199'}))
    national_id = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Aadhar / SSN'}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential address'}))
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary Emergency Contact'}))
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Contact Phone'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class PatientProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['phone', 'blood_group', 'national_id', 'date_of_birth', 'address', 'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class OrganRequestForm(forms.ModelForm):
    class Meta:
        model = OrganRequest
        fields = ['hospital', 'organ', 'blood_group', 'medical_history', 'medical_report']
        widgets = {
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'organ': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide clinical history, current diagnosis, dialysis/cardiac history, previous operations, allergies, and specialist consultation notes.'
            }),
            'medical_report': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DoctorVerificationForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[('APPROVE', 'Verify & Approve for Government Review'), ('REJECT', 'Reject Medical Request')],
        widget=forms.Select(attrs={'class': 'form-select font-monospace'})
    )
    priority_level = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select font-monospace'})
    )
    doctor_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Clinical justification for assigned priority, diagnostic lab checks verified, crossmatch readiness notes...'
        }),
        required=True
    )


class GovtAuthorizationForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[('APPROVE', 'Grant Official Government Legal Approval'), ('REJECT', 'Deny Legal Authorization')],
        widget=forms.Select(attrs={'class': 'form-select font-monospace'})
    )
    govt_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Statutory committee findings, ethical clearance record, legal compliance notes, registry filing ID...'
        }),
        required=True
    )
    compliance_identity_checked = forms.BooleanField(
        required=True,
        label="Verified recipient statutory identity & citizen residency criteria"
    )
    compliance_no_commercial_deal = forms.BooleanField(
        required=True,
        label="Certified adherence to Transplantation of Human Organs Act & anti-commercialization bylaws"
    )


class DonorRecordForm(forms.ModelForm):
    class Meta:
        model = DonorRecord
        fields = ['donor_name', 'donor_type', 'blood_group', 'age', 'gender', 'hospital', 'cause_of_death', 'time_of_death', 'family_consent_verified', 'legal_clearance', 'medical_notes']
        widgets = {
            'donor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name or Anonymous ID'}),
            'donor_type': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'cause_of_death': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., Severe Traumatic Brain Injury'}),
            'time_of_death': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'family_consent_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'legal_clearance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Serology, HLA typing, viral screen...'}),
        }


class AvailableOrganForm(forms.ModelForm):
    class Meta:
        model = AvailableOrgan
        fields = ['donor', 'hospital', 'organ_type', 'blood_group', 'harvested_at', 'viability_hours', 'condition_grade', 'storage_location']
        widgets = {
            'donor': forms.Select(attrs={'class': 'form-select'}),
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'organ_type': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'harvested_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'viability_hours': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hours (e.g. 6 for Heart, 24 for Kidney)'}),
            'condition_grade': forms.Select(attrs={'class': 'form-select'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cold Perfusion Bay / Container Box ID'}),
        }


class MortuaryRecordForm(forms.ModelForm):
    class Meta:
        model = MortuaryRecord
        fields = [
            'deceased_name', 'deceased_id_number', 'age', 'gender', 'blood_group',
            'time_of_death', 'cause_of_death', 'mortuary_room_location', 'hospital',
            'is_potential_donor', 'donor_flag_reason', 'donor_status_verified',
            'organs_harvestable', 'alert_sent_to_hospital'
        ]
        widgets = {
            'deceased_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'deceased_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital MRN / Gov ID'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'time_of_death': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'cause_of_death': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary cause of death'}),
            'mortuary_room_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., Storage Bay 3, Cold Unit 5'}),
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'is_potential_donor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'donor_flag_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Clinical justification for donor viability'}),
            'donor_status_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'organs_harvestable': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g. Kidney, Liver, Cornea'}),
            'alert_sent_to_hospital': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
