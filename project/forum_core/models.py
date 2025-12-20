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
    content = models.TextField()
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_threads', blank=True)
    is_solved = models.BooleanField(default=False)
    solved_by_comment = models.ForeignKey('Comment', on_delete=models.SET_NULL, null=True, blank=True, related_name='solution_to_thread')

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

class CommentReport(models.Model):
    REPORT_REASON_CHOICES = [
        ('SPAM', 'Spam'),
        ('HARASSMENT', 'Harassment'),
        ('INAPPROPRIATE', 'Inappropriate Content'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_reports_made')
    reason = models.CharField(max_length=20, choices=REPORT_REASON_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Report on Comment {self.comment.id} by {self.reported_by.username}"

class ThreadReport(models.Model):
    REPORT_REASON_CHOICES = CommentReport.REPORT_REASON_CHOICES
    STATUS_CHOICES = CommentReport.STATUS_CHOICES

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='thread_reports_made')
    reason = models.CharField(max_length=20, choices=REPORT_REASON_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Report on Thread {self.thread.id} by {self.reported_by.username}"