from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser, DoctorProfile
from django.core.files.uploadedfile import SimpleUploadedFile

class ModeratorVerificationTestCase(TestCase):
    def setUp(self):
        self.moderator = CustomUser.objects.create_user(username="mod", password="password123", user_type='MODERATOR', email="mod@example.com")
        self.doctor_user = CustomUser.objects.create_user(username="doc", password="password123", user_type='DOCTOR', email="doc@example.com")
        dummy_cv = SimpleUploadedFile("cv.pdf", b"fake file content", content_type="application/pdf")
        self.doctor_profile = DoctorProfile.objects.create(user=self.doctor_user, license_number="DOC123", cv=dummy_cv)
        self.premium_user = CustomUser.objects.create_user(username="premium", password="password123", user_type='PREMIUM', email="premium@example.com")
        
    def test_moderator_can_verify_doctor(self):
        self.client.login(username="mod", password="password123")
        url = reverse('forum_core:toggle_doctor_verification', kwargs={'user_id': self.doctor_user.id})
        
        # Verify
        response = self.client.post(url)
        self.assertRedirects(response, reverse('forum_core:moderator_dashboard'))
        self.doctor_profile.refresh_from_db()
        self.assertTrue(self.doctor_profile.is_verified)
        
        # Check dashboard content
        response = self.client.get(reverse('forum_core:moderator_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "License:")
        self.assertContains(response, "DOC123")
        self.assertContains(response, self.doctor_profile.cv.url)
        
        # Unverify
        response = self.client.post(url)
        self.assertRedirects(response, reverse('forum_core:moderator_dashboard'))
        self.doctor_profile.refresh_from_db()
        self.assertFalse(self.doctor_profile.is_verified)

    def test_non_moderator_cannot_verify_doctor(self):
        self.client.login(username="premium", password="password123")
        url = reverse('forum_core:toggle_doctor_verification', kwargs={'user_id': self.doctor_user.id})
        
        response = self.client.post(url)
        # Should redirect to settings page or similar based on user_type_required decorator
        self.assertEqual(response.status_code, 302)
        self.doctor_profile.refresh_from_db()
        self.assertFalse(self.doctor_profile.is_verified)

    def test_dashboard_handles_missing_cv(self):
        # Create a doctor without a CV file (manually)
        no_cv_user = CustomUser.objects.create_user(username="nocv", password="password123", user_type='DOCTOR', email="nocv@example.com")
        DoctorProfile.objects.create(user=no_cv_user, license_number="NOCV123") # cv is blank=True in model? No, let's check.
        
        self.client.login(username="mod", password="password123")
        response = self.client.get(reverse('forum_core:moderator_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No CV uploaded")
