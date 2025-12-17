from django.test import TestCase

import os

from users.models import CustomUser, UserProfile, PartnerProfile, doctorCvUploadPath, activatePremiumSubscription
from users.services import link_partner, unlink_partner


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

    def test_generate_partner_code(self):
        main_user = CustomUser.objects.create_user(username='main', password='pass123', email='main@example.com')

        partner_user = CustomUser.objects.create_user(username='partner', password='pass123', email='partner@example.com', user_type='PARTNER')
        partner_profile = PartnerProfile.objects.create(user=partner_user, linked_user=main_user)
        
        self.assertIsNotNone(partner_profile.partner_code)

    def test_link_unlink(self):
        main_user1 = CustomUser.objects.create_user(username='main_user1', password='pass123', email='main1@example.com')
        main_user2 = CustomUser.objects.create_user(username='main_user2', password='pass123', email='main2@example.com')
        
        partner_user = CustomUser.objects.create_user(username='partner_user', password='pass123', email='partner@example.com', user_type='PARTNER')
        partner_profile = PartnerProfile.objects.create(user=partner_user, linked_user=main_user1)
        
        partner_code = partner_profile.partner_code
        
        # link_partner with invalid code should return None
        invalid_result = link_partner(main_user2, 'invalid_code')
        self.assertIsNone(invalid_result)
        
        # link_partner to different user should return None (already linked)
        re_link_result = link_partner(main_user2, partner_code)
        self.assertIsNone(re_link_result)
        
        # Verify the link wasn't changed
        partner_profile.refresh_from_db()
        self.assertEqual(partner_profile.linked_user, main_user1)
        
        # unlink_partner should set linked_user to None
        unlink_result = unlink_partner(partner_user)
        self.assertTrue(unlink_result)
        
        partner_profile.refresh_from_db()
        self.assertIsNone(partner_profile.linked_user)
        
        # after unlinking, should be able to link to a different user
        new_link_result = link_partner(main_user2, partner_code)
        self.assertIsNotNone(new_link_result)
        self.assertEqual(new_link_result.linked_user, main_user2)
        
        # unlink_partner with non-existent partner should return None
        non_partner_user = CustomUser.objects.create_user(username='non_partner', password='pass123', email='non@example.com')
        unlink_invalid = unlink_partner(non_partner_user)
        self.assertIsNone(unlink_invalid)