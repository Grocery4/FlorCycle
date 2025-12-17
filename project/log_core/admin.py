from django.contrib import admin

from .models import DailyLog, SymptomLog, MoodLog, IntercourseLog, MedicationLog

# Register your models here.
admin.site.register(DailyLog)
admin.site.register(SymptomLog)
admin.site.register(MoodLog)
admin.site.register(IntercourseLog)
admin.site.register(MedicationLog)