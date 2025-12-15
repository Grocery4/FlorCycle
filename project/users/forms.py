from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.validators import FileExtensionValidator
from .models import CustomUser, UserProfile, ModeratorProfile, DoctorProfile, PartnerProfile

class UserSignupForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False)
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'email']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'STANDARD'
        if commit:
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            if self.cleaned_data.get('profile_picture'):
                profile.profile_picture = self.cleaned_data['profile_picture']
            profile.save()

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
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'PARTNER'
        if commit:
            user.save()
            PartnerProfile.objects.create(user=user)
        return user

class PremiumDataForm(UserCreationForm):
    pass
    #TODO - maybe PaymentDataForm is a better name
    #TODO - would it be better to create a separate object with 1:1 rel
    #TODO - with UserProfile?