from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    is_moderator = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    is_partner = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)



class ModeratorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.user.is_moderator = True
        self.user.save(update_fields=["is_moderator"])
        super().save(*args, **kwargs)



class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cv = ...
    license_number = ... #string
    is_verified = ... #bool
    rating = ...#choice 1/5

    def save(self, *args, **kwargs):
        self.user.is_doctor = True
        self.user.save(update_fields=["is_doctor"])
        super().save(*args, **kwargs)



class PartnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    partner_code = ... #str, has to be randgen
    linked_user = ... #1:1 with user

    def save(self, *args, **kwargs):
        self.user.is_partner = True
        self.user.save(update_fields=["is_partner"])
        super().save(*args, **kwargs)



class PremiumProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment_info = ... #no idea
    subscription_plan = ...#custom
    subscription_status = ...#custom
    start_date = ... #date
    end_date = ... #date
    auto_renew = ... #bool

    def save(self, *args, **kwargs):
        self.user.is_premium = True
        self.user.save(update_fields=["is_premium"])
        super().save(*args, **kwargs)