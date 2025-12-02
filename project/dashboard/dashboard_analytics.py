from django.db.models import Count, Sum

from datetime import datetime, date
from dateutil import relativedelta

from log_core.models import IntercourseLog

def get_intercourse_activity_metrics(user, end_date=date.today(), month_range=1):
    start_date = end_date - relativedelta.relativedelta(months=month_range)

    print(IntercourseLog.objects.filter(log__user=user, log__date__range=[start_date,end_date]))

    intercourse_count = IntercourseLog.objects.filter(
        log__user=user,
        log__date__range=[start_date,end_date]
    ).aggregate(total_sum=Sum('quantity'))['total_sum'] or 0


    total_with_quantity = IntercourseLog.objects.filter(
        log__user=user,
        log__date__range=[start_date, end_date],
        quantity__isnull=False
    ).count()

    orgasm_count = IntercourseLog.objects.filter(
        log__user=user,
        log__date__range=[start_date, end_date],
        orgasm=True
    ).count()

    orgasm_percentage = (orgasm_count/total_with_quantity) * 100 if total_with_quantity > 0 else None

    protected_count = IntercourseLog.objects.filter(
        log__user=user,
        log__date__range=[start_date, end_date],
        protected=True
    ).count()

    unprotected_count = IntercourseLog.objects.filter(
        log__user=user,
        log__date__range=[start_date, end_date],
        protected=False
    ).count()

    return {
        'intercourse_count': intercourse_count,
        'orgasm_percentage': orgasm_percentage,
        'protected_count': protected_count,
        'unprotected_count': unprotected_count
    }

def get_intercourse_frequency_metrics(user, end_date=date.today(), month_range=1):
    start_date = end_date - relativedelta.relativedelta(months=month_range)

    total_days = (end_date - start_date).days

    days_with_intercourse = IntercourseLog.objects.filter(
        log__user=user,
        log__date__range=[start_date, end_date],
    ).values('log__date').distinct().count()

    days_with_orgasm = IntercourseLog.objects.filter(
        log__user=user,
        log__date__range=[start_date, end_date]
    ).values('log__date').distinct().count()

    frequency_intercourse = total_days / days_with_intercourse if days_with_intercourse > 0 else None
    frequency_orgasm = total_days / days_with_orgasm if days_with_orgasm > 0 else None

    return {
        'frequency_intercourse': round(frequency_intercourse, 1) if frequency_intercourse else None,
        'frequency_orgasm': round(frequency_orgasm, 1) if frequency_orgasm else None
    }