from django.db import models

# Create your models here.
class CycleDetails(models.Model):

    CYCLE_DURATION_CHOICES = [(f'{i} DAYS', i) for i in range(22, 45)]
    MENSTRUATION_DURATION_CHOICES = [(f'{i} DAY', i) if i == 1 else (f'{i} DAYS', i) for i in range(1, 11)]

    last_menstruation_date = models.DateField()

    avg_cycle_duration = models.IntegerField(
        choices=CYCLE_DURATION_CHOICES,
        default=5,
        blank=False,
        null=False,
    )

    avg_menstruation_duration = models.IntegerField(
        choices=MENSTRUATION_DURATION_CHOICES,
        default=30,
        blank=False,
        null=False,
    )