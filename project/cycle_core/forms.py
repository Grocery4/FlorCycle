from django import forms
from .models import CycleDetails

class CycleDetailsForm(forms.ModelForm):
    class Meta:
        model = CycleDetails
        fields = '__all__'