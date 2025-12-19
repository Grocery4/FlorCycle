from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser, UserProfile

class ForumAccessControlTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.standard_user = CustomUser.objects.create_user(
            username='standard',
            email='standard@example.com',
            password='password123',
            user_type='STANDARD'
        )
        # Ensure UserProfile exists and is configured
        profile, created = UserProfile.objects.get_or_create(user=self.standard_user)
        profile.is_configured = True
        profile.save()

        self.premium_user = CustomUser.objects.create_user(
            username='premium',
            email='premium@example.com',
            password='password123',
            user_type='PREMIUM'
        )
        # Ensure UserProfile exists and is configured for premium user too
        profile_p, created_p = UserProfile.objects.get_or_create(user=self.premium_user)
        profile_p.is_configured = True
        profile_p.is_premium = True
        profile_p.save()

        self.forum_home_url = reverse('forum_core:home')

    def test_unauthenticated_user_redirects_to_login(self):
        response = self.client.get(self.forum_home_url)
        login_url = reverse('users:login')
        self.assertRedirects(response, f"{login_url}?next={self.forum_home_url}")

    def test_standard_user_redirects_to_settings(self):
        self.client.login(username='standard', password='password123')
        response = self.client.get(self.forum_home_url)
        # We use fetch_redirect_response=False because /dashboard/settings/ might itself redirect
        # if other conditions (like having cycle data) are not met, but we only care about 
        # the forum's redirection logic here.
        self.assertRedirects(response, reverse('dashboard:settings_page'), fetch_redirect_response=False)

    def test_premium_user_can_access_forum(self):
        self.client.login(username='premium', password='password123')
        response = self.client.get(self.forum_home_url)
        self.assertEqual(response.status_code, 200)
