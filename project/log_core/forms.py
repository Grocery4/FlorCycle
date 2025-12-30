from django import forms
from .models import DailyLog, SymptomLog, MoodLog, IntercourseLog, MedicationLog, Symptom, Mood, Medication
from django.utils.translation import gettext_lazy as _

class DailyLogForm(forms.ModelForm):
    symptoms = forms.ModelMultipleChoiceField(
        queryset=Symptom.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Symptoms")
    )
    moods = forms.ModelMultipleChoiceField(
        queryset=Mood.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Moods")
    )
    medications = forms.ModelMultipleChoiceField(
        queryset=Medication.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Medications")
    )

    class Meta:
        model = DailyLog
        fields = ['date', 'note', 'flow', 'weight', 'temperature', 'ovulation_test',
                  'symptoms', 'moods', 'medications']
        widgets = {
            'date' : forms.DateInput(attrs={"type": "date"}, format='%Y-%m-%d')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
         # Add CSS classes for error styling
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-field'})
        
        # If this is an existing instance, populate the custom fields
        if self.instance and self.instance.pk:
            self.fields['symptoms'].initial = self.instance.symptoms_field.all()
            self.fields['moods'].initial = self.instance.moods_field.all()
            self.fields['medications'].initial = self.instance.medications_field.all()

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if not date:
            raise forms.ValidationError("Date is required.")
        return date

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight <= 0:
            raise forms.ValidationError("Weight must be a positive number.")
        return weight

    def clean_temperature(self):
        temperature = self.cleaned_data.get('temperature')
        if temperature is not None and (temperature < 30 or temperature > 50):
            raise forms.ValidationError("Temperature must be between 30°C and 50°C.")
        return temperature

class IntercourseLogForm(forms.ModelForm):
    class Meta:
        model = IntercourseLog
        fields = ['protected', 'orgasm', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for error styling
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-field'})

    def clean(self):
        cleaned_data = super().clean()
        protected = cleaned_data.get('protected')
        orgasm = cleaned_data.get('orgasm')
        quantity = cleaned_data.get('quantity')
        
        # Auto-set quantity to 1 if either protected or orgasm is set (not blank/empty)
        if (protected is not None and protected != '') or (orgasm is not None and orgasm != ''):
            if quantity is None or quantity == 0:
                cleaned_data['quantity'] = 1
        
        return cleaned_data
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity