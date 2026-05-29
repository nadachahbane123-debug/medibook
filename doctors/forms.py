from django import forms
from .models import Doctor, Specialty


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = [
            'specialty', 'additional_specialties', 'license_number',
            'phone_professional', 'cabinet_address', 'bio',
            'years_experience', 'consultation_fee', 'photo', 'is_active'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'cabinet_address': forms.Textarea(attrs={'rows': 3}),
            'additional_specialties': forms.CheckboxSelectMultiple(),
        }
