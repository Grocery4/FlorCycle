from django.db.models.signals import post_save
from django.dispatch import receiver
from forum_core.models import Comment, CommentReport, ThreadReport
from .services import create_notification

@receiver(post_save, sender=Comment)
def notify_comment_reply(sender, instance, created, **kwargs):
    if created:
        thread = instance.thread
        author = instance.created_by
        
        # Notify the thread creator if they aren't the one who commented
        if thread.created_by != author:
            create_notification(
                user=thread.created_by,
                title="New reply on your thread",
                message=f"{author.username} replied to your thread: '{thread.title}'",
                notification_type='FORUM',
                link=f"/forums/thread/{thread.id}/"
            )
        
        # Notify other participants
        participants = thread.participants.exclude(id__in=[author.id, thread.created_by.id])
        for participant in participants:
            create_notification(
                user=participant,
                title="New reply in joined thread",
                message=f"{author.username} replied to a thread you joined: '{thread.title}'",
                notification_type='FORUM',
                link=f"/forums/thread/{thread.id}/"
            )

@receiver(post_save, sender=CommentReport)
def notify_moderators_comment_report(sender, instance, created, **kwargs):
    if created:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get all moderators
        moderators = User.objects.filter(user_type='MODERATOR')
        
        for moderator in moderators:
            create_notification(
                user=moderator,
                title="New Comment Report",
                message=f"A comment has been reported for {instance.get_reason_display()}. Review needed.",
                notification_type='FORUM',
                link="/forums/moderator/dashboard/"
            )

@receiver(post_save, sender=ThreadReport)
def notify_moderators_thread_report(sender, instance, created, **kwargs):
    if created:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get all moderators
        moderators = User.objects.filter(user_type='MODERATOR')
        
        for moderator in moderators:
            create_notification(
                user=moderator,
                title="New Thread Report",
                message=f"A thread has been reported for {instance.get_reason_display()}. Review needed.",
                notification_type='FORUM',
                link="/forums/moderator/dashboard/"
            )
