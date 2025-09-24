from django.db import models
from django.utils.timezone import now

from datetime import timedelta

# Create your models here.
class CycleDetails(models.Model):
    #TODO - add a user class to have one CycleDetails seed per user.    

    CYCLE_DURATION_CHOICES = [(i, f'{i} DAYS') for i in range(22, 45)]
    MENSTRUATION_DURATION_CHOICES = [(i, f'{i} DAY') if i == 1 else (i, f'{i} DAYS') for i in range(1, 11)]

    #Values based on reference website.
    AVG_MIN_OVULATION_DAY = 12
    AVG_MAX_OVULATION_DAY = 16


    last_menstruation_date = models.DateField(
        default=now
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
    
    # CycleWindow.objects.get_or_create() should be used in view.
    # The model should NOT be the one to insert elements in database.
    # Used in services.PredictionBuilder.generateMultiplePrediction to generate
    # a uniformed list of CycleWindows starting from the initial CycleWindow.
    def asCycleWindow(self):
        cw = CycleWindow(
            menstruation_start=self.last_menstruation_date,
            menstruation_end=self.last_menstruation_date + timedelta(days=self.avg_menstruation_duration-1),
            min_ovulation_window=self.last_menstruation_date + timedelta(days=CycleDetails.AVG_MIN_OVULATION_DAY),
            max_ovulation_window=self.last_menstruation_date + timedelta(days=CycleDetails.AVG_MAX_OVULATION_DAY)
        )
        
        return cw
    
    #TODO - implement methods
    # external function could pass last x=12 cycle/menstruation durations
    # and make an average of those durations
    # if total_entry_count % x == 0: take last x logs
    def updateAverageCycleDuration(self):
        pass

    def updateAverageMenstruationDuration(self):
        pass

    def __str__(self):
        return f'last menstruation: {self.last_menstruation_date}\n average cycle duration:{self.avg_cycle_duration}\n average menstruation duration:{self.avg_menstruation_duration}'



class CycleWindow(models.Model):

    menstruation_start = models.DateField(
        blank=False,
        default=now
    )

    menstruation_end = models.DateField(
        blank=False,
        default=now
    )

    min_ovulation_window = models.DateField(
        blank=False,
    )

    max_ovulation_window = models.DateField(
        blank=False,
    )

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
        return (self.menstruation_end - self.menstruation_start) + timedelta(days=1)


    def getOvulationDuration(self):
        return (self.max_ovulation_window - self.min_ovulation_window) + timedelta(days=1)


    def __str__(self):
        return (
            f"Menstruation: from {self.menstruation_start} to {self.menstruation_end}, "
            f"Ovulation: from {self.min_ovulation_window} to {self.max_ovulation_window}"
        )