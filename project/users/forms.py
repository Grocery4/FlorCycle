from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.validators import FileExtensionValidator
from .models import CustomUser, StandardProfile, ModeratorProfile, DoctorProfile, PartnerProfile, PremiumProfile

class UserSignupForm(UserCreationForm):
    profile_picture = forms.ImageField()
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'STANDARD'
        if commit:
            user.save()
            StandardProfile.objects.create(
                user=user,
                profile_picture=self.cleaned_data["profile_picture"],
            )
        return user

class ModeratorSignupForm(UserCreationForm):
    pass

class DoctorSignupForm(UserCreationForm):
    cv = forms.FileField(validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])], required=True)
    license_number = forms.CharField(max_length=100)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'email']

    def clean_license_number(self):
        license_number = self.cleaned_data.get("license_number")
        if DoctorProfile.objects.filter(license_number=license_number).exists():
            raise forms.ValidationError("This license number is already registered.")
        return license_number


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