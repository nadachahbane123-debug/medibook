from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from .models import User


class PatientRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Adresse email')
    first_name = forms.CharField(max_length=50, required=True, label='Prénom')
    last_name = forms.CharField(max_length=50, required=True, label='Nom')
    phone = forms.CharField(max_length=20, required=False, label='Téléphone')
    date_of_birth = forms.DateField(
        required=False,
        label='Date de naissance',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label='Nom d\'utilisateur ou Email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'avatar']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
