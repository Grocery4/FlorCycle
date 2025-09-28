from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from users.models import CustomUser, ModeratorProfile, DoctorProfile, PartnerProfile, PremiumProfile


class UserProfilesTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="testuser", password="pass123")

    def test_moderator_profile_sets_flag(self):
        ModeratorProfile.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, 'MODERATOR')

    def test_doctor_profile_sets_flag_and_fields(self):
        dummy_cv = SimpleUploadedFile("cv.pdf", b"fake file", content_type="application/pdf")
        doctor_profile = DoctorProfile.objects.create(
            user=self.user,
            cv=dummy_cv,
            license_number="ABC123"
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, 'DOCTOR')
        self.assertEqual(doctor_profile.license_number, "ABC123")
        self.assertFalse(doctor_profile.is_verified)
        self.assertEqual(doctor_profile.rating, 0.0)

    def test_partner_profile_sets_flag_and_unique_code(self):
        linked_user = CustomUser.objects.create_user(username="linked", password="pass123")
        partner_profile = PartnerProfile.objects.create(
            user=self.user,
            partner_code="PARTNER001",
            linked_user=linked_user
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, 'PARTNER')
        self.assertEqual(partner_profile.partner_code, "PARTNER001")
        self.assertEqual(partner_profile.linked_user, linked_user)

        # unique partner_code constraint
        with self.assertRaises(IntegrityError):
            PartnerProfile.objects.create(
                user=linked_user,
                partner_code="PARTNER001",
                linked_user=self.user
            )

    def test_premium_profile_sets_flag_and_defaults(self):
        premium_profile = PremiumProfile.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, 'PREMIUM')
        self.assertEqual(premium_profile.subscription_plan, "MONTHLY")
        self.assertEqual(premium_profile.subscription_status, "ACTIVE")
        self.assertFalse(premium_profile.auto_renew)
        self.assertIsNotNone(premium_profile.start_date)

    def test_premium_profile_end_date_and_auto_renew(self):
        end_date = timezone.now().date() + timedelta(days=30)
        premium_profile = PremiumProfile.objects.create(
            user=self.user,
            subscription_plan="YEARLY",
            subscription_status="EXPIRED",
            end_date=end_date,
            auto_renew=True
        )
        self.assertEqual(premium_profile.subscription_plan, "YEARLY")
        self.assertEqual(premium_profile.subscription_status, "EXPIRED")
        self.assertTrue(premium_profile.auto_renew)
        self.assertEqual(premium_profile.end_date, end_date)

