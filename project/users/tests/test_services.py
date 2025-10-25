from django.test import TestCase

import os

from users.models import CustomUser, UserProfile, doctorCvUploadPath, activatePremiumSubscription


class ServicesTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="docuser", password="pass123")

    def test_doctor_cv_upload_path_generates_unique_path(self):
        class DummyInstance:
            def __init__(self, user):
                self.user = user

        instance = DummyInstance(self.user)
        filename = "resume.pdf"
        path = doctorCvUploadPath(instance, filename)

        # Correct base path
        self.assertTrue(path.startswith(os.path.join("doctors", "cv")))
        # Has correct prefix and user ID
        self.assertIn(f"doctor_{self.user.id}_", path)
        # Ends with the same extension
        self.assertTrue(path.endswith(".pdf"))

        # Extract the generated filename and check UUID part
        generated_name = os.path.basename(path)
        uuid_part = generated_name.split("_")[-1].split(".")[0]
        self.assertEqual(len(uuid_part), 32)  # UUID4 hex string length

    def test_activate_premium_subscription_creates_new_profile(self):
        user_profile = UserProfile.objects.get(user=self.user)
        self.assertFalse(user_profile.is_premium)
        activatePremiumSubscription(self.user)
        user_profile.refresh_from_db()

        self.assertTrue(user_profile.is_premium)
        self.assertEqual(user_profile.user.user_type, 'PREMIUM')

        self.assertEqual(user_profile.subscription_status.lower(), "active")
        self.assertEqual(user_profile.payment_info["provider"], "mockpay")
        self.assertEqual(user_profile.payment_info["subscription_id"], f"sub_{self.user.id}")
        self.assertEqual(user_profile.payment_info["amount"], "9.99")
        self.assertEqual(user_profile.payment_info["currency"], "EUR")

    def test_activate_premium_subscription_updates_existing_profile(self):
        # Create a premium profile with different status
        premium = UserProfile.objects.get(user=self.user)
        premium.subscription_status="EXPIRED",
        premium.payment_info={}

        activatePremiumSubscription(self.user)
        premium.refresh_from_db()

        self.assertEqual(premium.subscription_status.lower(), "active")
        self.assertEqual(premium.payment_info["provider"], "mockpay")
        self.assertIn("subscription_id", premium.payment_info)