from django import forms
from .models import CycleDetails

class CycleDetailsForm(forms.ModelForm):
    class Meta:
        model = CycleDetails
        fields = ['base_menstruation_date', 'avg_cycle_duration', 'avg_menstruation_duration']
        widgets = {
            "base_menstruation_date": forms.DateInput(attrs={"type": "date"}, format='%Y-%m-%d')
        }
    def __init__(self, *args, user=None, mode="setup", **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if mode == "settings":
            self.fields.pop('base_menstruation_date')
    
    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user:
            obj.user = self.user
        
        if commit:
            obj.save()
        return obj