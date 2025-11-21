from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

from cycle_core.models import CycleWindow

# Create your models here.
class Symptom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Mood(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Medication(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class DailyLog(models.Model):
    OVULATION_TEST_CHOICES = [('POSITIVE', 'Positive'), ('NEGATIVE', 'Negative')]
    FLOW_CHOICES = [(0, 'Spotting'), (1, 'Light'), (2, 'Medium'), (3, 'Heavy')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    # if the linked CycleWindow is deleted: it still exists as a standalone log for a given day
    # if a CycleWindow is created in its proximity, it will be linked to it.
    cycle_window = models.ForeignKey(
        CycleWindow,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # optional metadata for each day
    note = models.TextField(max_length=500, blank=True, null=True)
    flow = models.IntegerField(choices=FLOW_CHOICES, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    temperature = models.FloatField(blank=True, null=True, validators=[
            MinValueValidator(30.0),
            MaxValueValidator(50.0),
        ])
    # TODO - calculate ovulation date average and ovulation window average through ovulation_test=POSITIVE query \
    # MAYBE IN ANALYTICS APP, not MVP
    ovulation_test = models.CharField(choices=OVULATION_TEST_CHOICES, blank=True, null=True)

    symptoms_field = models.ManyToManyField('Symptom', through='SymptomLog')
    moods_field = models.ManyToManyField('Mood', through='MoodLog')
    medications_field = models.ManyToManyField('Medication', through='MedicationLog')


    class Meta:
        unique_together = ('user', 'date')  # one log per day
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} - {self.date}"

class SymptomLog(models.Model):
    log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='symptoms')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('log', 'symptom')

class MoodLog(models.Model):
    log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='moods')
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('log', 'mood')


class IntercourseLog(models.Model):
    log = models.OneToOneField(DailyLog, on_delete=models.CASCADE, related_name='intercourse')
    protected = models.BooleanField(blank=True, null=True)
    orgasm = models.BooleanField(blank=True, null=True)
    quantity = models.PositiveSmallIntegerField(blank=True, null=True)

class MedicationLog(models.Model):
    log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='medication')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('log', 'medication')