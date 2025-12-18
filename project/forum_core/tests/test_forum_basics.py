from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser, UserProfile
from forum_core.models import Thread, Comment

class ForumBasicsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='premium_user',
            email='premium@example.com',
            password='password123',
            user_type='PREMIUM'
        )
        # Ensure UserProfile exists and is configured
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.is_configured = True
        profile.is_premium = True
        profile.save()
        self.client.login(username='premium_user', password='password123')

    def test_create_thread(self):
        url = reverse('forum_core:create_thread')
        data = {
            'title': 'Test Thread',
            'content': 'This is a test thread content.'
        }
        response = self.client.post(url, data)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.first()
        self.assertEqual(thread.title, 'Test Thread')
        self.assertEqual(thread.created_by, self.user)
        self.assertRedirects(response, reverse('forum_core:thread', kwargs={'thread_id': thread.id}))

    def test_post_comment(self):
        thread = Thread.objects.create(
            title='Sample Thread',
            content='Sample content',
            created_by=self.user
        )
        url = reverse('forum_core:thread', kwargs={'thread_id': thread.id})
        data = {
            'content': 'This is a sample comment.'
        }
        response = self.client.post(url, data)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.content, 'This is a sample comment.')
        self.assertEqual(comment.thread, thread)
        self.assertEqual(comment.created_by, self.user)
        self.assertRedirects(response, url)
        
        # Verify participant was added
        self.assertTrue(self.user in thread.participants.all())
