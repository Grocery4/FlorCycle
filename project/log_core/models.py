from django.db import models
from django.conf import settings

from cycle_core.models import CycleWindow

# Create your models here.
class DailyLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    OVULATION_TEST_CHOICES = [('POSITIVE', 'Positive'), ('NEGATIVE', 'Negative')]

    # optional metadata for each day
    note = models.TextField(max_length=500, blank=True)

    # TODO - check whether to use separate subclass or choices
    # mood = 
    # symptoms = 
    # intercourse = 
    # medication = 

    weight = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    ovulation_test = models.CharField(choices=OVULATION_TEST_CHOICES, blank=True)

    cycle_window = models.ForeignKey(
        CycleWindow,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = ('user', 'date')  # one log per day

    def __str__(self):
        return f"{self.user} - {self.date}"