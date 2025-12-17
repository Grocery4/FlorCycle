from django.db import models
from django.conf import settings
from users.models import DoctorProfile

# Create your models here.
class Comment(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()

class Thread(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_threads', blank=True)

    def __str__(self):
        return self.title

class ForumProfile(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    reputation = models.IntegerField(default=0)

class DoctorRating(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='ratings')
    
    rating = models.IntegerField()
    comment = models.TextField()