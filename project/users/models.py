from django.db import models
from django.conf import settings
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

# Create your models here.

#TODO - remove unused fields, ie: first & last name
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('STANDARD', 'Standard'),
        ('MODERATOR', 'Moderator'),
        ('DOCTOR', 'Doctor'),
        ('PARTNER', 'Partner'),
        ('PREMIUM', 'Premium'),
    ]
    
    email = models.EmailField(blank=False, null=False, unique=True)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='STANDARD'
    )



class ModeratorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.user.user_type = 'MODERATOR'
        self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)



class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cv = models.FileField(upload_to=doctorCvUploadPath)
    license_number = models.CharField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

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