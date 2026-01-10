from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile, ModeratorProfile, DoctorProfile, PartnerProfile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # UserProfile is created for ALL users to house generic data like profile_picture
        UserProfile.objects.get_or_create(user=instance)