from django.db.models.signals import post_save
from django.utils.translation import gettext as _
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
                title=_("New reply on your thread"),
                message=_("{username} replied to your thread: '{title}'").format(username=author.username, title=thread.title),
                notification_type='FORUM',
                link=f"/forums/thread/{thread.id}/"
            )
        
        # Notify other participants
        participants = thread.participants.exclude(id__in=[author.id, thread.created_by.id])
        for participant in participants:
            create_notification(
                user=participant,
                title=_("New reply in joined thread"),
                message=_("{username} replied to a thread you joined: '{title}'").format(username=author.username, title=thread.title),
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
                title=_("New Comment Report"),
                message=_("A comment has been reported for {reason}. Review needed.").format(reason=instance.get_reason_display()),
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
                title=_("New Thread Report"),
                message=_("A thread has been reported for {reason}. Review needed.").format(reason=instance.get_reason_display()),
                notification_type='FORUM',
                link="/forums/moderator/dashboard/"
            )
