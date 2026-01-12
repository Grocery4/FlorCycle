from django.db.models import Sum

from datetime import date
from dateutil import relativedelta

from log_core.models import IntercourseLog
from cycle_core.models import CycleWindow
from collections import Counter

def get_cycle_length_distribution(user):
    """
    Calculates the distribution of cycle lengths for historical data.
    """
    windows = CycleWindow.objects.filter(
        user=user, 
        is_prediction=False
    ).order_by('menstruation_start')

    if windows.count() < 2:
        return {'labels': [], 'data': []}

    cycle_lengths = []
    
    # Calculate lengths between consecutive menstruation starts
    for i in range(len(windows) - 1):
        delta = (windows[i+1].menstruation_start - windows[i].menstruation_start).days
        # Filter out unrealistic values if necessary (e.g., < 15 or > 60)
        if 15 < delta < 60:
            cycle_lengths.append(delta)

    if not cycle_lengths:
        return {'labels': [], 'data': []}

    # Count frequencies
    counts = Counter(cycle_lengths)
    
    # Sort by length for the x-axis
    sorted_lengths = sorted(counts.keys())
    
    return {
        'labels': [str(l) for l in sorted_lengths],
        'data': [counts[l] for l in sorted_lengths]
    }

def get_intercourse_activity_metrics(user, end_date=date.today(), month_range=1):
    start_date = end_date - relativedelta.relativedelta(months=month_range)

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