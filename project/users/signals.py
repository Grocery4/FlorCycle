from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile

# This signal is implemented to allow the automatic creation of UserProfile from admin menu.
# The method receives a signal after saving the CustomUser, 
@receiver(post_save, sender=CustomUser)
def create_standard_profile(sender, instance, created, **kwargs):
    #TODO - include premium user type -- Should I? There is no way a user is created premium directly from admin menu
    if created and instance.user_type == 'STANDARD':
        UserProfile.objects.create(user=instance)