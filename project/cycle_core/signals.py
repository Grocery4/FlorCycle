from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import CycleDetails, CycleStats

#TODO - test
@receiver(post_save, sender=CycleDetails)
def initCycleStatsOnCycleDetailsCreation(sender, instance, created, **kwargs):
	# Only act when a CycleDetails instance is created
	if not created:
		return

	user = getattr(instance, 'user', None)
	if user is None:
		# Nothing to do if CycleDetails isn't bound to a user. Should never happen
		return

	# Initialise defaults from CycleDetails but don't overwrite existing CycleStats
	defaults = {
		'avg_cycle_duration': float(getattr(instance, 'avg_cycle_duration', 28)),
		'avg_menstruation_duration': float(getattr(instance, 'avg_menstruation_duration', 5)),
	}

	CycleStats.objects.get_or_create(user=user, defaults=defaults)