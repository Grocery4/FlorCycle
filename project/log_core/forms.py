from django import forms
from .models import DailyLog, SymptomLog, MoodLog, IntercourseLog, MedicationLog


class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['note', 'flow', 'weight', 'temperature', 'ovulation_test']

class SymptomLogForm(forms.ModelForm):
    class Meta:
        model = SymptomLog
        fields = ['symptom', 'intensity']
        widgets = {
            'symptom': forms.CheckboxSelectMultiple(),
            'class': 'hidden-checkbox'
        }

class MoodLogForm(forms.ModelForm):
    class Meta:
        model = MoodLog
        fields = ['mood']
        widgets = {
            'mood': forms.CheckboxSelectMultiple(),
            'class': 'hidden-checkbox'
        }


class IntercourseLogForm(forms.ModelForm):
    class Meta:
        model = IntercourseLog
        fields = ['protected', 'orgasm', 'quantity']

class MedicationLogForm(forms.ModelForm):
    class Meta:
        model = MedicationLog
        fields = ['medication']
        widgets = {
            'medication': forms.CheckboxSelectMultiple(),
            'class': 'hidden-checkbox'
        }