from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser
from forum_core.models import Thread

class ForumSearchTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="testuser", password="StrongP@ssw0rd123!", email="test@example.com", user_type='PREMIUM')
        # Ensure profile has is_premium=True so user_type doesn't revert to STANDARD
        profile = self.user.userprofile
        profile.is_premium = True
        profile.save()
        
        login_success = self.client.login(username="testuser", password="StrongP@ssw0rd123!")
        self.assertTrue(login_success, "Login failed")
        
        Thread.objects.create(title="How to use the app", created_by=self.user)
        Thread.objects.create(title="Tips for better tracking", created_by=self.user)
        Thread.objects.create(title="General discussion", created_by=self.user)

    def test_search_results(self):
        url = reverse('forum_core:home')
        
        # Search for "app"
        response = self.client.get(url, {'q': 'app'})
        if response.status_code == 302:
             print(f"DEBUG: Redirected to {response.url}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How to use the app")
        self.assertNotContains(response, "Tips for better tracking")
        self.assertNotContains(response, "General discussion")

        # Search for "Tips"
        response = self.client.get(url, {'q': 'Tips'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tips for better tracking")
        self.assertNotContains(response, "How to use the app")

        # Empty result
        response = self.client.get(url, {'q': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No threads found")
