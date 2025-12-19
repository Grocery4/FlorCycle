from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser, DoctorProfile

class DoctorVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.unverified_doctor = CustomUser.objects.create_user(
            username='dr_unverified', email='dr1@example.com', password='password123', user_type='DOCTOR'
        )
        # Create profile but leave is_verified=False
        DoctorProfile.objects.create(user=self.unverified_doctor, license_number='DOC_UNV', is_verified=False)
        
        self.verified_doctor = CustomUser.objects.create_user(
            username='dr_verified', email='dr2@example.com', password='password123', user_type='DOCTOR'
        )
        DoctorProfile.objects.create(user=self.verified_doctor, license_number='DOC_VER', is_verified=True)

    def test_unverified_doctor_redirects_to_waiting_page(self):
        self.client.login(username='dr_unverified', password='password123')
        response = self.client.get(reverse('forum_core:home'))
        self.assertRedirects(response, reverse('users:verification_pending'))

    def test_verified_doctor_can_access_forum(self):
        self.client.login(username='dr_verified', password='password123')
        response = self.client.get(reverse('forum_core:home'))
        self.assertEqual(response.status_code, 200)
