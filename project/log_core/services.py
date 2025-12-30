from .models import DailyLog

def get_day_log(user, target_date):
    return DailyLog.objects.filter(user=user, date=target_date).first()