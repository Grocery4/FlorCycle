import secrets
import os
import uuid

def doctorCvUploadPath(instance, filename):
    # Get file extension
    ext = filename.split('.')[-1]
    # Build unique filename: doctor_<user_id>_<uuid>.<ext>
    filename = f"doctor_{instance.user.id}_{uuid.uuid4().hex}.{ext}"
    # Save inside MEDIA_ROOT/doctors/cv/
    return os.path.join("doctors", "cv", filename)

def activatePremiumSubscription(user):
    from .models import UserProfile
    
    premium = UserProfile.objects.get(user=user)
    premium.is_premium = True
    premium.subscription_status = "ACTIVE"
    premium.payment_info = {
        "provider": "mockpay",
        "subscription_id": f"sub_{user.id}",
        "amount": "9.99",
        "currency": "EUR"
    }

    premium.save()

def userProfilePicturePath(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"user_{instance.user.id}_{uuid.uuid4().hex}.{ext}"
    return os.path.join('profile_pictures', f'user_{instance.user.id}', filename)

def generate_partner_code() -> str:
    return secrets.token_urlsafe(6)

def link_partner():
    pass

def unlink_partner():
    pass