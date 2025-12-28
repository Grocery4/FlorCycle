from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.translation import gettext_lazy as _
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
            raise forms.ValidationError(_("This license number is already registered."))
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

class PremiumUpgradeForm(forms.ModelForm):
    card_number = forms.CharField(max_length=16, label=_("Card Number"), widget=forms.TextInput(attrs={'placeholder': '1234 5678 1234 5678'}))
    expiry_date = forms.CharField(max_length=5, label=_("Expiry Date"), widget=forms.TextInput(attrs={'placeholder': 'MM/YY'}))
    cvv = forms.CharField(max_length=3, label=_("CVV"), widget=forms.PasswordInput(attrs={'placeholder': '123'}))

    class Meta:
        model = UserProfile
        fields = ['subscription_plan']
        widgets = {
            'subscription_plan': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription_plan'].required = True
        self.fields['subscription_plan'].choices = [choice for choice in UserProfile.PLAN_CHOICES if choice[0] != 'TRIAL']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        
        if not profile_picture:
            return 'profile_pictures/default/default_profile.jpg'
        return profile_picture