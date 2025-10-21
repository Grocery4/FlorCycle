from django import forms
from .models import CycleDetails

class CycleDetailsForm(forms.ModelForm):
    class Meta:
        model = CycleDetails
        fields = ['base_menstruation_date', 'avg_cycle_duration', 'avg_menstruation_duration']
        widgets = {
            "base_menstruation_date": forms.DateInput(attrs={"type": "date"})
        }