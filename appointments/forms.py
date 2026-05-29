from django import forms
from .models import Appointment, Review, Consultation


class AppointmentForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Décrivez votre motif de consultation...'}),
        label='Motif de consultation'
    )
    slot_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Votre commentaire...'}),
        }
        labels = {
            'rating': 'Note',
            'comment': 'Commentaire (optionnel)',
        }


class CancellationForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Raison de l\'annulation',
        required=True
    )


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['diagnosis', 'treatment', 'prescription', 'follow_up_date']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'prescription': forms.Textarea(attrs={'rows': 3}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'diagnosis': 'Diagnostic',
            'treatment': 'Traitement',
            'prescription': 'Ordonnance',
            'follow_up_date': 'Date de suivi',
        }
