from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile, ModeratorProfile, DoctorProfile, PartnerProfile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'STANDARD' or instance.user_type == 'PREMIUM':
            UserProfile.objects.get_or_create(user=instance)
        elif instance.user_type == 'MODERATOR':
            ModeratorProfile.objects.get_or_create(user=instance)
        elif instance.user_type == 'DOCTOR':
            DoctorProfile.objects.get_or_create(user=instance)
        elif instance.user_type == 'PARTNER':
            PartnerProfile.objects.get_or_create(user=instance)