from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser, ModeratorProfile, DoctorProfile, PartnerProfile, PremiumProfile

class ModeratorSignupForm(UserCreationForm):
    pass

class DoctorSignupForm(UserCreationForm):
    cv = forms.FileField(required=True)
    license_number = forms.CharField(max_length=100)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'DOCTOR'
        if commit:
            user.save()
            DoctorProfile.objects.create(
                user=user,
                cv=self.cleaned_data["cv"],
                license_number=self.cleaned_data["license_number"],
            )
        return user


class PartnerSignupForm(UserCreationForm):
    pass

class PremiumSignupForm(UserCreationForm):
    pass