from django.test import TestCase
from django.contrib.auth import get_user_model
from forum_core.models import Thread, Comment
from notifications.models import Notification
from notifications.services import check_dangerous_symptoms

User = get_user_model()

class NotificationTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='user_a', email='a@test.com', password='password')
        self.user_b = User.objects.create_user(username='user_b', email='b@test.com', password='password')

    def test_dangerous_symptom_notification(self):
        symptoms = ["Severe Pain", "Fainting", "Fever"]
        check_dangerous_symptoms(self.user_a, symptoms, flow_level=3)
        
        notification = Notification.objects.filter(user=self.user_a, notification_type='MEDICAL').first()
        self.assertIsNotNone(notification)
        self.assertIn("critical symptoms", notification.message)
        self.assertIn("Severe Pain", notification.message)

    def test_forum_reply_notification(self):
        thread = Thread.objects.create(title="Test Thread", content="Body", created_by=self.user_a)
        
        # User B replies
        Comment.objects.create(thread=thread, created_by=self.user_b, content="I agree")
        
        # User A should get a notification
        notification = Notification.objects.filter(user=self.user_a, notification_type='FORUM').first()
        self.assertIsNotNone(notification)
        self.assertIn("user_b replied to your thread", notification.message)
