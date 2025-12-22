from django.db.models.signals import post_save
from django.dispatch import receiver
from forum_core.models import Comment
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
