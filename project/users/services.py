import os
import uuid

def doctorCvUploadPath(instance, filename):
    # Get file extension
    ext = filename.split('.')[-1]
    # Build unique filename: doctor_<user_id>_<uuid>.<ext>
    filename = f"doctor_{instance.user.id}_{uuid.uuid4().hex}.{ext}"
    # Save inside MEDIA_ROOT/doctors/cv/
    return os.path.join("doctors", "cv", filename)

#TODO - implement function
def activatePremiumSubscription(user):
    pass