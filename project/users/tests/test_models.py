from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from users.models import CustomUser, ModeratorProfile, DoctorProfile, PartnerProfile, PremiumProfile


class UserProfilesTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="testuser", password="pass123", email="setupemail@example.com")
        self.user1 = CustomUser.objects.create_user(username="testuser1", password="pass123", email="setupemail1@example.com")

    def test_moderator_profile_sets_flag_and_fields(self):
        moderator_profile = ModeratorProfile.objects.create(
            user=self.user,
            can_suspend_users = True,
            can_edit_posts = True
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, 'MODERATOR')
        self.assertTrue(moderator_profile.can_suspend_users)
        self.assertTrue(moderator_profile.can_edit_posts)

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

    # inputting a .pdf file does not raise ValidationError, regardless of content_type
    def test_cv_file_type(self):
        #wrong format
        fake_cv = SimpleUploadedFile("fake_cv.zip", b"fake file", content_type="application/zip")
        doctor_profile, created = DoctorProfile.objects.get_or_create(
            user=self.user,
            cv=fake_cv,
            license_number="ABC123"
        )
        with self.assertRaises(ValidationError):
            doctor_profile.full_clean()
            doctor_profile.save()
        
        #pdf file, wrong extension
        real_cv = SimpleUploadedFile("real_cv.zip", b"fake file", content_type="application/pdf")
        doctor_profile1, created = DoctorProfile.objects.get_or_create(
            user=self.user1,
            cv=real_cv,
            license_number="123ABC"
        )
        with self.assertRaises(ValidationError):
            doctor_profile1.full_clean()
            doctor_profile1.save()



    def test_license_number_uniqueness(self):
        dummy_cv = SimpleUploadedFile("cv.pdf", b"fake file", content_type="application/pdf")
        DoctorProfile.objects.create(
            user=self.user,
            cv=dummy_cv,
            license_number="UNIQUE123"
        )

        another_user = CustomUser.objects.create_user(username="doctor2", password="pass123", email="licenseuniqueness@example.com")
        with self.assertRaises(IntegrityError):
            DoctorProfile.objects.create(
                user=another_user,
                cv=dummy_cv,
                license_number="UNIQUE123"
            )

    def test_username_uniqueness(self):
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(username="testuser", password="newpass123")

    def test_email_uniqueness(self):
        user1 = CustomUser.objects.create_user(username="user1", password="pass123", email="unique@example.com")
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(username="user2", password="pass123", email="unique@example.com")

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

