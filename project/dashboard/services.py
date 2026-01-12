from functools import wraps
from django.shortcuts import redirect
from django.db import transaction


from cycle_core.models import CycleWindow, CycleStats, CycleDetails, MIN_LOG_FOR_STATS

from cycle_core.services import PredictionBuilder, updateCycleStats
from calendar_core.services import render_multiple_calendars, CalendarType
from datetime import timedelta, datetime, date
from dateutil import relativedelta


from django.contrib.auth.views import redirect_to_login

def user_type_required(allowed_types, redirect_url='login', denied_redirect_url='guest_mode:show_form'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url=redirect_url)
            if request.user.user_type not in allowed_types:
                return redirect(denied_redirect_url)
            
            if request.user.is_banned:
                from django.contrib.auth import logout
                logout(request)
                return redirect('users:banned')
            
            # Additional check for Doctors - they must be verified
            if request.user.user_type == 'DOCTOR':
                doctor_profile = getattr(request.user, 'doctorprofile', None)
                if not doctor_profile or not doctor_profile.is_verified:
                    return redirect('users:verification_pending')

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
            # Partners, Doctors and Moderators don't need to be configured
            if user.user_type in ['PARTNER', 'DOCTOR', 'MODERATOR']:
                return view_func(request, *args, **kwargs)
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
        two_months_ago,
        one_month_ago,
        date_start,
        one_month_fwd
    ]

    rendered_month_start = two_months_ago
    rendered_month_end = (one_month_fwd + relativedelta.relativedelta(months=1)) - timedelta(days=1)

    rendered_menstruation_windows = get_visible_windows(user, rendered_month_start, rendered_month_end)

    return {
        'calendars': render_multiple_calendars(months=rendered_months, menstruation_dates=rendered_menstruation_windows, calendar_type=CalendarType.SELECTABLE),
        'selected_dates': rendered_menstruation_windows,
        'rendered_month_start': rendered_month_start,
        'rendered_month_end': rendered_month_end
    }

def get_visible_windows(user, visible_start, visible_end):
    visible_cw = CycleWindow.objects.filter(
        user=user,
        is_prediction=False,
        menstruation_start__lte=visible_end,
        menstruation_end__gte=visible_start
    )

    visible_menstruation_windows = []

    for cw in visible_cw:
        visible_menstruation_windows.extend(cw.getMenstruationDatesAsList())

    return visible_menstruation_windows

def parse_list_of_dates(dates):
    return sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in dates])

def group_consecutive_days(selected_dates):
    if not selected_dates:
        return []
    
    consecutive_date_ranges = []
    current_window = [selected_dates[0]]
    
    for i in range(1, len(selected_dates)):
        if selected_dates[i] == selected_dates[i-1] + timedelta(days=1):
            current_window.append(selected_dates[i])
        else:
            consecutive_date_ranges.append(current_window)
            current_window = [selected_dates[i]]
        
    consecutive_date_ranges.append(current_window)
    return consecutive_date_ranges

def generate_date_intervals(consecutive_days):
    period_ranges = []
    for window in consecutive_days:
        period_ranges.append((window[0], window[-1]))
    
    return period_ranges

def create_cycle_window(user, start_date, end_date):
    ovulation_start, ovulation_end = PredictionBuilder.predictOvulation(start_date)

    return CycleWindow(
        user=user,
        menstruation_start=start_date,
        menstruation_end=end_date,
        min_ovulation_window=ovulation_start,
        max_ovulation_window=ovulation_end,
        is_prediction=False
    )

def _normalize_ranges(ranges):
    """
    Merge overlapping or adjacent date ranges and return a sorted list.
    """
    if not ranges:
        return []

    ranges = sorted(ranges, key=lambda x: x[0])
    merged = []
    cur_start, cur_end = ranges[0]

    for s, e in ranges[1:]:
        if cur_end + timedelta(days=1) >= s:
            cur_end = max(cur_end, e)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e

    merged.append((cur_start, cur_end))
    return merged


def _validate_ranges(ranges):
    for s, e in ranges:
        if s > e:
            raise ValueError("Invalid range: {} > {}".format(s, e))


@transaction.atomic
def apply_period_windows(user, selected_ranges, visible_start, visible_end, month_offset=1):
    _validate_ranges(selected_ranges)
    selected_norm = _normalize_ranges(selected_ranges)

    # Extend the search range by month_offset on both sides to catch adjacent periods
    search_start = visible_start - relativedelta.relativedelta(months=month_offset)
    search_end = visible_end + relativedelta.relativedelta(months=month_offset)

    # Load all existing windows that overlap the extended search range
    existing_windows = list(
        CycleWindow.objects.filter(
            user=user,
            is_prediction=False,
            menstruation_start__lte=search_end,
            menstruation_end__gte=search_start
        )
    )

    preserved_fragments = []
    existing_ids_to_delete = []

    for w in existing_windows:
        w_start = w.menstruation_start
        w_end = w.menstruation_end

        # Preserve entire windows that are completely outside the visible range
        # but within the offset range (i.e., in adjacent months)
        if (w_end < visible_start or w_start > visible_end):
            # Window is entirely in the offset months - preserve it completely
            preserved_fragments.append((w_start, w_end))
        else:
            # Window overlaps with visible range - preserve only the parts outside visible range
            # Left fragment before visible_start
            if w_start < visible_start:
                left_end = min(w_end, visible_start - timedelta(days=1))
                if left_end >= w_start:
                    preserved_fragments.append((w_start, left_end))

            # Right fragment after visible_end
            if w_end > visible_end:
                right_start = max(w_start, visible_end + timedelta(days=1))
                if right_start <= w_end:
                    preserved_fragments.append((right_start, w_end))

        existing_ids_to_delete.append(w.id)

    preserved_fragments = _normalize_ranges(preserved_fragments)

    # Final set of ranges to create
    create_ranges = _normalize_ranges(selected_norm + preserved_fragments)

    deleted_count = 0
    created_objs = []

    if existing_ids_to_delete:
        deleted_count = CycleWindow.objects.filter(id__in=existing_ids_to_delete).delete()[0]

    objs_to_create = []
    for s, e in create_ranges:
        objs_to_create.append(create_cycle_window(user, s, e))

    if objs_to_create:
        created_objs = CycleWindow.objects.bulk_create(objs_to_create)

    # Manually update CycleStats since bulk_create doesn't trigger post_save signals
    try:
        stats = CycleStats.objects.get(user=user)
        stats.log_count = CycleWindow.objects.filter(user=user, is_prediction=False).count()
        stats.save()
        # Update avg durations if we have enough logs
        updateCycleStats(stats)
    except CycleStats.DoesNotExist:
        pass

    return {
        "deleted_count": deleted_count,
        "created_count": len(created_objs),
        "created_ranges": [(obj.menstruation_start, obj.menstruation_end) for obj in created_objs],
        "preserved_fragments": preserved_fragments,
        "selected_ranges_normalized": selected_norm,
    }


def get_current_cycle(user):
    # returns the most recent non-prediction cycle.
    current_cycle = CycleWindow.objects.filter(
        user=user,
        is_prediction=False
    ).order_by('-menstruation_start').first()
    
    return current_cycle


def get_cycle_length(user):
    # returns the average cycle duration in days from either cyclestats or cycledetails based on log_count.
    try:
        stats = CycleStats.objects.get(user=user)
        if stats.log_count >= MIN_LOG_FOR_STATS:
            return stats.avg_cycle_duration
    except CycleStats.DoesNotExist:
        pass
    
    # Fallback to CycleDetails
    try:
        cycle_details = CycleDetails.objects.get(user=user)
        return cycle_details.avg_cycle_duration
    except CycleDetails.DoesNotExist:
        return 28  # Default fallback


def calculate_timeline_data(user):
    """
    Calculate timeline data for the current cycle.
    Returns a dict with phase boundaries and marker positions as percentages.
    """
    today = date.today()
    cycle = get_current_cycle(user)
    
    if not cycle:
        return {
            'has_cycle': False,
            'current_day': today,
        }
    
    cycle_length = get_cycle_length(user)
    cycle_start = cycle.menstruation_start
    cycle_end = cycle_start + timedelta(days=cycle_length - 1)
    
    # Get adaptive ovulation timing from CycleStats if available
    try:
        stats = CycleStats.objects.get(user=user)
        ovulation_start_day = stats.avg_ovulation_start_day
        ovulation_end_day = stats.avg_ovulation_end_day
    except CycleStats.DoesNotExist:
        # Fallback to defaults
        ovulation_start_day = CycleDetails.AVG_MIN_OVULATION_DAY
        ovulation_end_day = CycleDetails.AVG_MAX_OVULATION_DAY
    
    # Recalculate ovulation with adaptive timing
    ovulation_start, ovulation_end = PredictionBuilder.predictOvulation(
        cycle_start,
        ovulation_start_day=ovulation_start_day,
        ovulation_end_day=ovulation_end_day
    )
    
    # Calculate phase data
    phases = cycle.getPhasesBreakdown()
    
    # Calculate percentages relative to cycle length
    menstruation_duration = phases['menstruation']['duration']
    
    menstruation_start_day = (cycle.menstruation_start - cycle_start).days
    ovulation_start_day_offset = (ovulation_start - cycle_start).days
    ovulation_end_day_offset = (ovulation_end - cycle_start).days
    probable_ovulation = phases['ovulation']['probable_date']
    probable_ovulation_day = (probable_ovulation - cycle_start).days
    
    menstruation_start_percent = (menstruation_start_day / cycle_length) * 100
    menstruation_end_percent = ((menstruation_start_day + menstruation_duration - 1) / cycle_length) * 100
    ovulation_start_percent = (ovulation_start_day_offset / cycle_length) * 100
    ovulation_end_percent = ((ovulation_end_day_offset + 1) / cycle_length) * 100
    probable_ovulation_percent = (probable_ovulation_day / cycle_length) * 100
    
    # Check if today is within cycle
    is_today_in_cycle = cycle_start <= today <= cycle_end
    
    if is_today_in_cycle:
        current_day_offset = (today - cycle_start).days
        current_day_percent = (current_day_offset / cycle_length) * 100
    else:
        current_day_percent = None
    
    return {
        'has_cycle': True,
        'cycle_start': cycle_start,
        'cycle_end': cycle_end,
        'cycle_length': cycle_length,
        'menstruation': {
            'start_percent': menstruation_start_percent,
            'end_percent': menstruation_end_percent,
            'width_percent': menstruation_end_percent - menstruation_start_percent,
            'duration': menstruation_duration,
        },
        'ovulation': {
            'start_percent': ovulation_start_percent,
            'end_percent': ovulation_end_percent,
            'width_percent': ovulation_end_percent - ovulation_start_percent,
            'probable_percent': probable_ovulation_percent,
            'duration': (ovulation_end_day_offset - ovulation_start_day_offset) + 1,
        },
        'current_day_percent': current_day_percent,
        'current_day': today,
        'show_markers': is_today_in_cycle,
    }