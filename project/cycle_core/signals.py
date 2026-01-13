from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import CycleDetails, CycleWindow, CycleStats
from .services import generate_prediction_based_on_log_count, update_cycle_stats

@receiver(post_save, sender=CycleDetails)
def initCycleStatsOnCycleDetailsCreation(sender, instance, created, **kwargs):
	# Only act when a CycleDetails instance is created and is bound to a user
	user = getattr(instance, 'user', None)
	if not created or user is None:
		return

	# Initialise defaults from CycleDetails but don't overwrite existing CycleStats
	defaults = {
		'avg_cycle_duration': int(getattr(instance, 'avg_cycle_duration', 28)),
		'avg_menstruation_duration': int(getattr(instance, 'avg_menstruation_duration', 5)),
		'log_count' : int(CycleWindow.objects.filter(user=user, is_prediction=False).count())
	}

	CycleStats.objects.update_or_create(user=user, defaults=defaults)


# Clean up CycleStats (and predicted windows) when CycleDetails is deleted
@receiver(post_delete, sender=CycleDetails)
def teardownCycleStatsOnCycleDetailsDeletion(sender, instance, **kwargs):
    user = getattr(instance, 'user', None)
    if not user:
        return

    # remove stats so a fresh one can be created on next CycleDetails create
    CycleStats.objects.filter(user=user).delete()
    # remove any generated predictions for this user
    CycleWindow.objects.filter(user=user, is_prediction=True).delete()



@receiver(post_save, sender=CycleDetails)
@receiver(post_save, sender=CycleStats)
def generateOrUpdatePredictions(sender, instance, created, **kwargs):
	user = getattr(instance, 'user', None)

	if sender is CycleDetails and created:
		return

	if user:
		predictions = generate_prediction_based_on_log_count(user)
		CycleWindow.objects.filter(user=user, is_prediction=True).delete()
		CycleWindow.objects.bulk_create(predictions)

@receiver([post_save, post_delete], sender=CycleWindow)
def updateLogCount(sender, instance, **kwargs):
    if instance.is_prediction:
        return  # only count real logs

    stats = CycleStats.objects.filter(user=instance.user).first()
    if stats:
        stats.log_count = CycleWindow.objects.filter(user=instance.user, is_prediction=False).count()
        stats.save()

@receiver([post_save, post_delete], sender=CycleWindow)
def updateStatsOnLogChange(sender, instance, **kwargs):
	if instance.is_prediction:
		return
	if not instance.user:
		return
    
	try:
		stats = CycleStats.objects.get(user=instance.user)
	except CycleStats.DoesNotExist:
		return
	update_cycle_stats(stats)