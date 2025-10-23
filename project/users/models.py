from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import AbstractUser

import os
import uuid

def doctorCvUploadPath(instance, filename):
    # Get file extension
    ext = filename.split('.')[-1]
    # Build unique filename: doctor_<user_id>_<uuid>.<ext>
    filename = f"doctor_{instance.user.id}_{uuid.uuid4().hex}.{ext}"
    # Save inside MEDIA_ROOT/doctors/cv/
    return os.path.join("doctors", "cv", filename)

def activatePremiumSubscription(user):
    premium, created = PremiumProfile.objects.get_or_create(user=user)
    premium.subscription_status = "active"
    premium.payment_info = {
        "provider": "mockpay",
        "subscription_id": f"sub_{user.id}",
        "amount": "9.99",
        "currency": "EUR"
    }
    premium.save()

def userProfilePicturePath(instance, filename):
    # upload to MEDIA_ROOT/profile_pictures/user_<id>/<filename>
    return os.path.join('profile_pictures', f'user_{instance.user.id}', filename)

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
class StandardProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_configured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to=userProfilePicturePath, blank=True)

    def save(self, *args, **kwargs):
        cycledetails = getattr(self.user, 'cycledetails', None)
        
        if cycledetails and not self.is_configured:
            cd = self.user.cycledetails
            cd.delete()

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
    partner_code = models.CharField(max_length=20, unique=True)
    linked_user = models.ForeignKey(CustomUser, related_name="partners", on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.user.user_type = 'PARTNER'
        self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)



class PremiumProfile(models.Model):
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

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment_info = models.JSONField(default=dict)
    subscription_plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='MONTHLY'
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    auto_renew = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.user.user_type = 'PREMIUM'
        self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)