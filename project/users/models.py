from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser

from django.utils.translation import gettext_lazy as _
from .services import doctorCvUploadPath, activatePremiumSubscription, userProfilePicturePath, generate_partner_code

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('STANDARD', _('Standard')),
        ('MODERATOR', _('Moderator')),
        ('DOCTOR', _('Doctor')),
        ('PARTNER', _('Partner')),
        ('PREMIUM', _('Premium')),
    ]
    
    first_name = None
    last_name = None

    email = models.EmailField(blank=False, null=False, unique=True)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='STANDARD'
    )
    is_banned = models.BooleanField(default=False)

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_configured = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to=userProfilePicturePath, default='profile_pictures/default/default_profile.jpg', blank=True)

    is_premium = models.BooleanField(default=False)
    
    #Premium fields
    PLAN_CHOICES = [
        ('TRIAL', _('trial')),
        ('MONTHLY', _('monthly')),
        ('YEARLY', _('yearly'))
    ]

    STATUS_CHOICES = [
        ('ACTIVE', _('Active')),
        ('EXPIRED', _('Expired')),
        ('CANCELED', _('Canceled'))
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
        default=None,
        verbose_name=_("Subscription plan")
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Subscription status")
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
    
    @property
    def has_active_premium(self):
        return self.is_premium and self.subscription_status == 'ACTIVE'
    
    def clean(self):
        super().clean()
    def save(self, *args, **kwargs):
        if not self.is_premium:
            # Preserve EXPIRED and CANCELED statuses for historical tracking
            # Only clear if status is ACTIVE or None
            if self.subscription_status not in ['EXPIRED', 'CANCELED']:
                self.subscription_status = None
            self.subscription_plan = None
            self.auto_renew = None
            self.payment_info = None

        self.full_clean()   

        cycledetails = getattr(self.user, 'cycledetails', None)
        if not self.is_configured and cycledetails:
            cd = self.user.cycledetails
            cd.delete()

        elif self.is_configured and not cycledetails:
            self.is_configured = False

        if self.user.user_type in ['STANDARD', 'PREMIUM']:
            new_user_type = 'PREMIUM' if self.is_premium else 'STANDARD'
            if self.user.user_type != new_user_type:
                self.user.user_type = new_user_type
                self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)

class ModeratorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_suspend_users = models.BooleanField(default=True)
    can_edit_posts = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.user:
            new_is_staff = bool(self.is_verified)
            changed = False
            if self.user.is_staff != new_is_staff:
                self.user.is_staff = new_is_staff
                changed = True
            if self.user.user_type != 'MODERATOR':
                self.user.user_type = 'MODERATOR'
                changed = True
            
            if changed:
                self.user.save(update_fields=['user_type', 'is_staff'])
        super().save(*args, **kwargs)


# FileExtensionValidator only checks for .pdf extension, therefore there's no way to check for fake .pdf files
class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cv = models.FileField(validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])], upload_to=doctorCvUploadPath)
    license_number = models.CharField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.user.user_type != 'DOCTOR':
            self.user.user_type = 'DOCTOR'
            self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)



class PartnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    partner_code = models.CharField(max_length=10, unique=True)
    linked_user = models.ForeignKey(CustomUser, related_name="partners", on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.user.user_type != 'PARTNER':
            self.user.user_type = 'PARTNER'
            self.user.save(update_fields=['user_type'])
        if not self.partner_code:
            self.partner_code = generate_partner_code()
            while PartnerProfile.objects.filter(partner_code=self.partner_code).exists():
                self.partner_code = generate_partner_code()
        super().save(*args, **kwargs)