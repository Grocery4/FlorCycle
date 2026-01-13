from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from cycle_core.models import CycleWindow

from django.utils.translation import gettext as _rt

# Create your models here.
class Symptom(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Name"))
    category = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Category"))

    class Meta:
        verbose_name = _("Symptom")
        verbose_name_plural = _("Symptoms")

    def __str__(self):
        return _rt(self.name)

class Mood(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Name"))
    category = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Category"))

    class Meta:
        verbose_name = _("Mood")
        verbose_name_plural = _("Moods")

    def __str__(self):
        return _rt(self.name)

class Medication(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Medication")
        verbose_name_plural = _("Medications")

    def __str__(self):
        return _rt(self.name)


class DailyLog(models.Model):
    OVULATION_TEST_CHOICES = [('POSITIVE', _('Positive')), ('NEGATIVE', _('Negative'))]
    FLOW_CHOICES = [(0, _('Spotting')), (1, _('Light')), (2, _('Medium')), (3, _('Heavy'))]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))
    date = models.DateField(verbose_name=_("Date"))

    # if the linked CycleWindow is deleted: it still exists as a standalone log for a given day
    # if a CycleWindow is created in its proximity, it will be linked to it.
    cycle_window = models.ForeignKey(
        CycleWindow,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Cycle Window")
    )

    # optional metadata for each day
    note = models.TextField(max_length=500, blank=True, null=True, verbose_name=_("Note"))
    flow = models.IntegerField(choices=FLOW_CHOICES, blank=True, null=True, verbose_name=_("Flow"))
    weight = models.FloatField(blank=True, null=True, verbose_name=_("Weight"))
    temperature = models.FloatField(blank=True, null=True, validators=[
            MinValueValidator(30.0),
            MaxValueValidator(50.0),
        ], verbose_name=_("Temperature"))
    ovulation_test = models.CharField(choices=OVULATION_TEST_CHOICES, blank=True, null=True, verbose_name=_("Ovulation Test"))

    symptoms_field = models.ManyToManyField('Symptom', through='SymptomLog', verbose_name=_("Symptoms"))
    moods_field = models.ManyToManyField('Mood', through='MoodLog', verbose_name=_("Moods"))
    medications_field = models.ManyToManyField('Medication', through='MedicationLog', verbose_name=_("Medications"))


    class Meta:
        unique_together = ('user', 'date')  # one log per day
        ordering = ['-date']
        verbose_name = _("Daily Log")
        verbose_name_plural = _("Daily Logs")

    def __str__(self):
        return f"{self.user} - {self.date}"

    def is_empty(self):
        # Check basic fields
        if self.note or self.flow is not None or self.weight or self.temperature or self.ovulation_test:
            return False
        
        # Check many-to-many fields
        if self.symptoms_field.exists() or self.moods_field.exists() or self.medications_field.exists():
            return False
            
        # Check related IntercourseLog
        il = getattr(self, 'intercourse', None)
        if il:
            if il.protected is not None or il.orgasm is not None or il.quantity is not None:
                return False
                
        return True

class SymptomLog(models.Model):
    log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='symptoms', verbose_name=_("Log"))
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE, verbose_name=_("Symptom"))

    class Meta:
        unique_together = ('log', 'symptom')
        verbose_name = _("Symptom Log")
        verbose_name_plural = _("Symptom Logs")

class MoodLog(models.Model):
    log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='moods', verbose_name=_("Log"))
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE, verbose_name=_("Mood"))

    class Meta:
        unique_together = ('log', 'mood')
        verbose_name = _("Mood Log")
        verbose_name_plural = _("Mood Logs")


class IntercourseLog(models.Model):
    log = models.OneToOneField(DailyLog, on_delete=models.CASCADE, related_name='intercourse', verbose_name=_("Log"))
    protected = models.BooleanField(blank=True, null=True, verbose_name=_("Protected"))
    orgasm = models.BooleanField(blank=True, null=True, verbose_name=_("Orgasm"))
    quantity = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("Quantity"))

    class Meta:
        verbose_name = _("Intercourse Log")
        verbose_name_plural = _("Intercourse Logs")

class MedicationLog(models.Model):
    log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='medication', verbose_name=_("Log"))
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, verbose_name=_("Medication"))

    class Meta:
        unique_together = ('log', 'medication')
        verbose_name = _("Medication Log")
        verbose_name_plural = _("Medication Logs")