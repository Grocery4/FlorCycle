from functools import wraps
from django.shortcuts import redirect

from cycle_core.models import CycleWindow
from cycle_core.services import PredictionBuilder
from calendar_core.services import render_multiple_calendars, CalendarType
from datetime import timedelta, datetime
from dateutil import relativedelta


def user_type_required(allowed_types, redirect_url='login'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(redirect_url)
            if request.user.user_type not in allowed_types:
                return redirect('guest_mode:show_form')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def configured_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect('login')

        profile = getattr(user, 'userprofile', None)
        if not profile or not profile.is_configured:
            return redirect('dashboard:setup_page')

        return view_func(request, *args, **kwargs)

    return _wrapped_view

def fetch_closest_prediction(user):
    prediction = CycleWindow.objects.filter(user=user, is_prediction=True).order_by('menstruation_start').first()
    return prediction

def render_selectable_calendars(user, date):
    date_start = date.replace(day=1)
    one_month_ago = date_start - relativedelta.relativedelta(months=1)
    two_months_ago = date_start - relativedelta.relativedelta(months=2)
    one_month_fwd = date_start + relativedelta.relativedelta(months=1)


    rendered_months = [
        (two_months_ago.year, two_months_ago.month),
        (one_month_ago.year, one_month_ago.month),
        (date_start.year, date_start.month),
        (one_month_fwd.year, one_month_fwd.month)
    ]

    start_date = two_months_ago
    end_date = (one_month_fwd + relativedelta.relativedelta(months=1)) - timedelta(days=1)

    cw_in_rendered_months = CycleWindow.objects.filter(user=user, is_prediction=False, menstruation_start__lte=end_date, menstruation_end__gte=start_date)
    
    menstruation_dates = []
    
    for cw in cw_in_rendered_months:
        menstruation_dates.extend(cw.getMenstruationDatesAsList())

    return {
        'calendars': render_multiple_calendars(months=rendered_months, menstruation_dates=menstruation_dates, calendar_type=CalendarType.SELECTABLE),
        'selected_dates': menstruation_dates
    }

def group_consecutive_days(selected_dates):
    if not selected_dates:
        return []
    
    selected_dates = [datetime.strptime(date, '%Y-%m-%d').date() for date in selected_dates]
    sorted_dates = sorted(selected_dates)
    
    periods = []
    current_period = [sorted_dates[0]]
    
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i-1] + timedelta(days=1):
            current_period.append(sorted_dates[i])
        else:
            periods.append(current_period)
            current_period = [sorted_dates[i]]
        
    periods.append(current_period)
    return periods

def generate_date_intervals(consecutive_days):
    period_ranges = []
    for window in consecutive_days:
        period_ranges.append((window[0], window[-1]))
    
    return period_ranges

def check_existing_windows(user, period_ranges):
    existing_windows = []
    new_ranges = []
    
    for start_date, end_date in period_ranges:
        existing = CycleWindow.objects.filter(
            user=user,
            is_prediction=False,
            menstruation_start__lte=end_date,
            menstruation_end__gte=start_date
        ).exists()
        
        if existing:
            existing_windows.append((start_date, end_date))
        else:
            new_ranges.append((start_date, end_date))
    
    return {
        'existing': existing_windows,
        'new': new_ranges
    }

#TODO - accomodate for both cyclestats and cycledetails
def create_cycle_window(user, start_date, end_date):
    ovulation_start, ovulation_end = PredictionBuilder.predictOvulation(start_date)

    return CycleWindow.objects.create(
        user=user,
        menstruation_start=start_date,
        menstruation_end=end_date,
        min_ovulation_window=ovulation_start,
        max_ovulation_window=ovulation_end,
        is_prediction=False
    )