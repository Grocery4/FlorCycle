from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from users.forms import DoctorSignupForm, PartnerSignupForm
from users.models import CustomUser, DoctorProfile, PartnerProfile

class RegistrationFixTestCase(TestCase):
    def test_doctor_registration_no_crash(self):
        form_data = {
            'username': 'newdoctor',
            'email': 'newdoctor@example.com',
            'password1': 'StrongP@ssw0rd123!',
            'password2': 'StrongP@ssw0rd123!',
            'license_number': 'DOC123'
        }
        dummy_cv = SimpleUploadedFile("cv.pdf", b"fake file", content_type="application/pdf")
        form = DoctorSignupForm(data=form_data, files={'cv': dummy_cv})
        self.assertTrue(form.is_valid(), form.errors)
        
        # This is where it used to crash
        user = form.save()
        
        self.assertEqual(user.username, 'newdoctor')
        self.assertTrue(DoctorProfile.objects.filter(user=user).exists())
        self.assertEqual(DoctorProfile.objects.get(user=user).license_number, 'DOC123')

    def test_partner_registration_no_crash(self):
        form_data = {
            'username': 'newpartner',
            'email': 'newpartner@example.com',
            'password1': 'StrongP@ssw0rd123!',
            'password2': 'StrongP@ssw0rd123!'
        }
        form = PartnerSignupForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        
        # This is where it used to crash
        user = form.save()
        
        self.assertEqual(user.username, 'newpartner')
        self.assertTrue(PartnerProfile.objects.filter(user=user).exists())
