from django.utils.translation import gettext as _
from .models import Notification

def create_notification(user, title, message, notification_type, link=None):
    # Utility function to create a new notification.
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )

def check_dangerous_symptoms(user, symptom_names, flow_level=None):
    # Checks for dangerous symptoms and triggers medical advice notification. 
    # Only sends notification if ALL dangerous symptoms are present together:
    # Severe Pain, Fainting, Fever, AND Heavy Bleeding.
    DANGEROUS_SYMPTOMS = ["Severe Pain", "Fainting", "Fever"]
    
    # Check if all dangerous symptoms are present
    has_all_symptoms = all(symptom in symptom_names for symptom in DANGEROUS_SYMPTOMS)
    
    # Check for Heavy Bleeding from flow field (3 = Heavy)
    has_heavy_bleeding = (flow_level == 3)
    
    # Only notify if ALL conditions are met
    if has_all_symptoms and has_heavy_bleeding:
        create_notification(
            user=user,
            title=_("URGENT: Medical Advice Needed"),
            message=_("You have logged all critical symptoms together: Severe Pain, Fainting, Fever, and Heavy Bleeding. Please contact a medical professional immediately."),
            notification_type='MEDICAL'
        )
        return True
    return False

def check_upcoming_predictions(user):
    # Checks if a period or ovulation starts tomorrow and notifies the user. Only creates notification if one doesn't already exist for that prediction.
    from datetime import date, timedelta
    from cycle_core.models import CycleWindow
    
    tomorrow = date.today() + timedelta(days=1)
    
    # Check for period
    upcoming_period = CycleWindow.objects.filter(
        user=user,
        is_prediction=True,
        menstruation_start=tomorrow
    ).first()
    
    if upcoming_period:
        # Check if notification already exists for this prediction
        existing_notification = Notification.objects.filter(
            user=user,
            notification_type='CYCLE',
            title=_("Cycle Reminder"),
            created_at__date=date.today()
        ).exists()
        
        if not existing_notification:
            create_notification(
                user=user,
                title=_("Cycle Reminder"),
                message=_("Your period is predicted to start tomorrow."),
                notification_type='CYCLE',
                link='/dashboard/calendar'
            )

    # Check for ovulation window start
    upcoming_ovulation = CycleWindow.objects.filter(
        user=user,
        is_prediction=True,
        min_ovulation_window=tomorrow
    ).first()
    
    if upcoming_ovulation:
        # Check if notification already exists for this prediction
        existing_notification = Notification.objects.filter(
            user=user,
            notification_type='CYCLE',
            message=_("Your ovulation window is predicted to start tomorrow."),
            created_at__date=date.today()
        ).exists()
        
        if not existing_notification:
            create_notification(
                user=user,
                title=_("Cycle Reminder"),
                message=_("Your ovulation window is predicted to start tomorrow."),
                notification_type='CYCLE',
                link='/dashboard/calendar'
            )
    
    # Check for probable ovulation day (midpoint of ovulation window)
    for cycle_window in CycleWindow.objects.filter(user=user, is_prediction=True):
        phases = cycle_window.getPhasesBreakdown()
        probable_ovulation_date = phases['ovulation']['probable_date']
        
        if probable_ovulation_date == tomorrow:
            # Check if notification already exists
            existing_notification = Notification.objects.filter(
                user=user,
                notification_type='CYCLE',
                title=_("Ovulation Day Reminder"),
                created_at__date=date.today()
            ).exists()
            
            if not existing_notification:
                create_notification(
                    user=user,
                    title=_("Ovulation Day Reminder"),
                    message=_("Your most likely ovulation day is tomorrow."),
                    notification_type='CYCLE',
                    link='/dashboard/calendar'
                )
            break  # Only notify once
