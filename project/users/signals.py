from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ModeratorProfile, DoctorProfile, PartnerProfile, PremiumProfile

#FIXME - does not work
@receiver(post_delete, sender=ModeratorProfile)
@receiver(post_delete, sender=DoctorProfile)
@receiver(post_delete, sender=PartnerProfile)
@receiver(post_delete, sender=PremiumProfile)
def downgrade_user_type_on_profile_delete(sender, instance, **kwargs):
    user = instance.user
    if user:
        user.user_type = 'STANDARD'  # or whatever your default value is
        user.save(update_fields=['user_type'])
