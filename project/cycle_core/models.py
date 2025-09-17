from django.db import models
from datetime import datetime

# Create your models here.
class CycleDetails(models.Model):

    CYCLE_DURATION_CHOICES = [(i, f'{i} DAYS') for i in range(22, 45)]
    MENSTRUATION_DURATION_CHOICES = [(i, f'{i} DAY') if i == 1 else (i, f'{i} DAYS') for i in range(1, 11)]

    last_menstruation_date = models.DateField(
        default=datetime.today()
    )

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