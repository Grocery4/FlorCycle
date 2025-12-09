from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser

from .services import doctorCvUploadPath, activatePremiumSubscription, userProfilePicturePath, generate_partner_code

#TODO - implement pfps, cycledata into standarduser,
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('STANDARD', 'Standard'),
        ('MODERATOR', 'Moderator'),
        ('DOCTOR', 'Doctor'),
        ('PARTNER', 'Partner'),
        ('PREMIUM', 'Premium'),
    ]
    
    first_name = None
    last_name = None

    email = models.EmailField(blank=False, null=False, unique=True)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='STANDARD'
    )

#TODO - test this mf class
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_configured = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to=userProfilePicturePath, default='profile_pictures/default/default_profile.jpg', blank=True)

    is_premium = models.BooleanField(default=False)
    
    #Premium fields
    PLAN_CHOICES = [
        ('TRIAL', 'trial'),
        ('MONTHLY', 'monthly'),
        ('YEARLY', 'yearly')
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELED', 'Canceled')
    ]

    payment_info = models.JSONField(
        blank=True, 
        null=True, 
        default=None
    )
    subscription_plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        blank=True,
        null=True,
        default=None
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        default=None,
    )
    start_date = models.DateField(
        blank=True, 
        null=True,
        default=None
    )
    end_date = models.DateField(
        blank=True,
        null=True, 
        default=None
    )
    auto_renew = models.BooleanField(
        blank=True,
        null=True,
        default=None
    )
    
    #TODO - test method
    def clean(self):
        if not self.is_premium:
            if self.subscription_plan or self.subscription_status or self.auto_renew:
                raise ValidationError(("Premium subscription fields can only be set if user is premium."))
            
            if self.payment_info:
                raise ValidationError(("Payment info should be empty for non-premium users."))
    #TODO - test method for premium fields
    def save(self, *args, **kwargs):
        if not self.is_premium:
            self.subscription_plan = None
            self.subscription_status = None
            self.auto_renew = None
            self.payment_info = None

        self.full_clean()

        cycledetails = getattr(self.user, 'cycledetails', None)
        if not self.is_configured and cycledetails:
            cd = self.user.cycledetails
            cd.delete()

        elif self.is_configured and not cycledetails:
            self.is_configured = False

        self.user.user_type = 'PREMIUM' if self.is_premium else 'STANDARD'
        self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)

class ModeratorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_suspend_users = models.BooleanField()
    can_edit_posts = models.BooleanField()
    is_verified = models.BooleanField(default=False)

    
    def save(self, *args, **kwargs):
        if self.user:
            if self.is_verified == True:
                self.user.is_staff = True
            else:
                self.user.is_staff = False
            self.user.user_type = 'MODERATOR'
            self.user.save(update_fields=['user_type', 'is_staff'])
        super().save(*args, **kwargs)


# FileExtensionValidator only checks for .pdf extension, therefore there's no way to check for fake .pdf files
class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cv = models.FileField(validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])], upload_to=doctorCvUploadPath)
    license_number = models.CharField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)
    #TODO - move rating to forum app
    # rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

    def save(self, *args, **kwargs):
        self.user.user_type = 'DOCTOR'
        self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)



class PartnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    partner_code = models.CharField(max_length=10, unique=True)
    linked_user = models.ForeignKey(CustomUser, related_name="partners", on_delete=models.CASCADE, null=True)

    def save(self, *args, **kwargs):
        self.user.user_type = 'PARTNER'
        self.user.save(update_fields=['user_type'])
        if not self.partner_code:
            self.partner_code = generate_partner_code()
            while PartnerProfile.objects.filter(partner_code=self.partner_code).exists():
                self.partner_code = generate_partner_code()
        super().save(*args, **kwargs)