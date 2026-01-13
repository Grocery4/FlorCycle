from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('MEDICAL', _('Medical Advice')),
        ('CYCLE', _('Cycle Reminder')),
        ('FORUM', _('Forum Interaction')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name=_("User"))
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    message = models.TextField(verbose_name=_("Message"))
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name=_("Notification type"))
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
