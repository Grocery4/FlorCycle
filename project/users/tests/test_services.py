from django.test import TestCase

import os

from users.models import CustomUser, PremiumProfile, doctorCvUploadPath, activatePremiumSubscription


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
        # No profile exists initially
        self.assertFalse(PremiumProfile.objects.filter(user=self.user).exists())

        activatePremiumSubscription(self.user)
        premium = PremiumProfile.objects.get(user=self.user)

        self.assertEqual(premium.subscription_status.lower(), "active")
        self.assertEqual(premium.payment_info["provider"], "mockpay")
        self.assertEqual(premium.payment_info["subscription_id"], f"sub_{self.user.id}")
        self.assertEqual(premium.payment_info["amount"], "9.99")
        self.assertEqual(premium.payment_info["currency"], "USD")

    def test_activate_premium_subscription_updates_existing_profile(self):
        # Create a premium profile with different status
        premium = PremiumProfile.objects.create(
            user=self.user,
            subscription_status="EXPIRED",
            payment_info={}
        )

        activatePremiumSubscription(self.user)
        premium.refresh_from_db()

        self.assertEqual(premium.subscription_status.lower(), "active")
        self.assertEqual(premium.payment_info["provider"], "mockpay")
        self.assertIn("subscription_id", premium.payment_info)