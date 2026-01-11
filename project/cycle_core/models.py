from django.db import models
from django.utils.timezone import now
from django.conf import settings
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from datetime import timedelta

# Create your models here.

MIN_LOG_FOR_STATS = 6

class CycleDetails(models.Model):
    #TODO - test this mf
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    CYCLE_DURATION_CHOICES = [(i, format_lazy(_('{count} DAYS'), count=i)) for i in range(22, 45)]
    MENSTRUATION_DURATION_CHOICES = [(i, format_lazy(_('{count} DAY'), count=i)) if i == 1 else (i, format_lazy(_('{count} DAYS'), count=i)) for i in range(1, 11)]

    #Values based on reference website.
    AVG_MIN_OVULATION_DAY = 12
    AVG_MAX_OVULATION_DAY = 16


    base_menstruation_date = models.DateField(
        default=now,
        verbose_name=_("Base menstruation date")
    )

    avg_cycle_duration = models.IntegerField(
        choices=CYCLE_DURATION_CHOICES,
        default=28,
        verbose_name=_("Average cycle duration"),
        blank=False,
        null=False,
    )

    avg_menstruation_duration = models.IntegerField(
        choices=MENSTRUATION_DURATION_CHOICES,
        default=5,
        verbose_name=_("Average menstruation duration"),
        blank=False,
        null=False,
    )
    
    # CycleWindow.objects.get_or_create() should be used in view.
    # The model should NOT be the one to insert elements in database.
    # Used in services.PredictionBuilder.generateMultiplePrediction to generate
    # a uniformed list of CycleWindows starting from the initial CycleWindow.
    def asCycleWindow(self):
        cw = CycleWindow(
            menstruation_start=self.base_menstruation_date,
            menstruation_end=self.base_menstruation_date + timedelta(days=self.avg_menstruation_duration-1),
            min_ovulation_window=self.base_menstruation_date + timedelta(days=CycleDetails.AVG_MIN_OVULATION_DAY),
            max_ovulation_window=self.base_menstruation_date + timedelta(days=CycleDetails.AVG_MAX_OVULATION_DAY),
            is_prediction = False

        )
        
        return cw
    
    def __str__(self):
        return f'last menstruation: {self.base_menstruation_date}\n average cycle duration:{self.avg_cycle_duration}\n average menstruation duration:{self.avg_menstruation_duration}'



class CycleWindow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    menstruation_start = models.DateField(
        blank=False,
        default=now
    )

    menstruation_end = models.DateField(
        null=True,
        blank=True,
    )

    min_ovulation_window = models.DateField(
        blank=False,
    )

    max_ovulation_window = models.DateField(
        blank=False,
    )

    is_prediction = models.BooleanField(default=True)

    def getMenstruationDatesAsList(self):
        if self.menstruation_start is None or self.menstruation_end is None:
            raise ValueError('period_start and period_end must be set.')

        delta = self.getMenstruationDuration()
        return [(self.menstruation_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days)]


    def getOvulationDatesAsList(self):
        if self.min_ovulation_window is None or self.max_ovulation_window is None:
            raise ValueError('min_ovulation_window and max_ovulation_window must be set.')

        delta = self.getOvulationDuration()
        return [(self.min_ovulation_window + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days)]
    

    def getMenstruationDuration(self):
        if not self.menstruation_end:
            return timedelta(days=0)
        return (self.menstruation_end - self.menstruation_start) + timedelta(days=1)


    def getOvulationDuration(self):
        return (self.max_ovulation_window - self.min_ovulation_window) + timedelta(days=1)

    def getPhasesBreakdown(self):
        # calculate probable ovulation date (midpoint of ovulation window)
        ovulation_duration = self.getOvulationDuration()
        probable_ovulation_date = self.min_ovulation_window + (ovulation_duration / 2) - timedelta(days=0.5)
        
        return {
            'menstruation': {
                'start': self.menstruation_start,
                'end': self.menstruation_end,
                'duration': self.getMenstruationDuration().days
            },
            'ovulation': {
                'start': self.min_ovulation_window,
                'end': self.max_ovulation_window,
                'probable_date': probable_ovulation_date.date() if hasattr(probable_ovulation_date, 'date') else probable_ovulation_date,
                'duration': ovulation_duration.days
            }
        }

    def __str__(self):
        return (
            f"Menstruation: from {self.menstruation_start} to {self.menstruation_end}, "
            f"Ovulation: from {self.min_ovulation_window} to {self.max_ovulation_window}"
        )
    

    
# This class is used as a stats holder which will be dynamically updated by methods.
# It's different from CycleDetails, which is a class used to generate the initial setup form
# fillled by the user through UI.
class CycleStats(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avg_cycle_duration = models.IntegerField(default=28)
    avg_menstruation_duration = models.IntegerField(default=5)
    avg_ovulation_start_day = models.IntegerField(default=CycleDetails.AVG_MIN_OVULATION_DAY)
    avg_ovulation_end_day = models.IntegerField(default=CycleDetails.AVG_MAX_OVULATION_DAY)
    updated_at = models.DateTimeField(auto_now=True)

    log_count = models.PositiveIntegerField(default=0)