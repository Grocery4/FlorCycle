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

def link_partner(main_user, partner_code: str):
    from .models import PartnerProfile
    try:
        partner_profile = PartnerProfile.objects.get(partner_code=partner_code)

        if partner_profile.linked_user is not None:
            return None
        
        partner_profile.linked_user = main_user
        partner_profile.save()
        return partner_profile
    
    except PartnerProfile.DoesNotExist:
        return None

def unlink_partner(partner_user):
    from .models import PartnerProfile
    
    try:
        partner_profile = PartnerProfile.objects.get(user=partner_user)
        partner_profile.linked_user = None
        partner_profile.save()
        return True
    except PartnerProfile.DoesNotExist:
        return None