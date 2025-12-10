from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from datetime import datetime, date
from dateutil import relativedelta
import json

from .services import user_type_required, configured_required, fetch_closest_prediction, render_selectable_calendars, group_consecutive_days, generate_date_intervals, parse_list_of_dates, apply_period_windows, calculate_timeline_data
from .dashboard_analytics import get_intercourse_activity_metrics, get_intercourse_frequency_metrics
from cycle_core.models import CycleDetails, CycleStats, CycleWindow, MIN_LOG_FOR_STATS
from cycle_core.forms import CycleDetailsForm
from log_core.services import get_day_log
from log_core.models import DailyLog, IntercourseLog
from log_core.forms import DailyLogForm, IntercourseLogForm

# Create your views here.
@login_required(login_url='login')
def redirect_handler(request):
    if request.user.user_type == 'STANDARD' or request.user.user_type == 'PREMIUM':
        return redirect('dashboard:homepage')
    elif request.user.user_type == 'PARTNER':
        return redirect('dashboard:partner_setup')

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def homepage(request):
    ctx = {}
    ctx['next_prediction'] = fetch_closest_prediction(request.user)
    ctx['timeline_data'] = calculate_timeline_data(request.user)

    return render(request, 'dashboard/dashboard.html', ctx)

@user_type_required(['PARTNER'])
def partner_setup(request):
    ctx = {}
    try:
        partner_profile = request.user.partnerprofile
        ctx['user'] = request.user
        ctx['partner_profile'] = partner_profile
        ctx['linked_user'] = partner_profile.linked_user
    except:
        ctx['error'] = 'Partner profile not found'
    
    return render(request, 'dashboard/partner/partner_setup.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM'])
def setup(request):
    profile = request.user.userprofile
    if profile.is_configured:
        return redirect('dashboard:homepage')

    ctx = {}
    ctx['form'] = CycleDetailsForm()

    if request.method == 'POST':
        form = CycleDetailsForm(request.POST, user=request.user)
        if form.is_valid():
            ctx['base_menstruation_date'] = form.cleaned_data['base_menstruation_date']
            ctx['avg_cycle_duration'] = form.cleaned_data['avg_cycle_duration']
            ctx['avg_menstruation_duration'] = form.cleaned_data['avg_menstruation_duration']
            
            profile = request.user.userprofile
        
            cycle = form.save(commit=False)
            cycle.user = request.user  # link to logged-in user
            cycle.save()
            profile.is_configured = True
            profile.save()
            return redirect('dashboard:homepage')


    return render(request, 'dashboard/setup.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def settings(request):
    ctx = {}

    if request.method == 'POST':
        # checks whether to render user values or default values in case cycledetails is instantiated.
        # it's a redundant check, since settings page cannot be accessed if there is no cycledetails object
        try:
            instance = request.user.cycledetails
        except CycleDetails.DoesNotExist:
            instance = None

        # retrieve form data
        cycle_details_form = CycleDetailsForm(request.POST, mode='settings', user=request.user, instance=instance)
        if cycle_details_form.is_valid():
            cycle_details_form.save()
    
    # display user's form data
    ctx['cycle_details_form'] = CycleDetailsForm(user=request.user, mode='settings', instance=request.user.cycledetails)
    
    
    return render(request, 'dashboard/settings.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def cycle_logs(request):
    ctx = {}

    user = request.user
    cs = getattr(user, 'cyclestats', None)
    
    if cs:
        ctx['log_count'] = cs.log_count
        
        if cs.log_count < MIN_LOG_FOR_STATS:
            cd = getattr(user, 'cycledetails', None)
            if cd:
                ctx['avg_cycle_duration'] = cd.avg_cycle_duration
                ctx['avg_menstruation_duration'] = cd.avg_menstruation_duration
                ctx['avg_ovulation_start_day'] = cd.AVG_MIN_OVULATION_DAY
                ctx['avg_ovulation_end_day'] = cd.AVG_MAX_OVULATION_DAY
        else:
            ctx['avg_cycle_duration'] = cs.avg_cycle_duration
            ctx['avg_menstruation_duration'] = cs.avg_menstruation_duration
            ctx['avg_ovulation_start_day'] = cs.avg_ovulation_start_day
            ctx['avg_ovulation_end_day'] = cs.avg_ovulation_end_day

    show_history_view = request.GET.get('view') == 'history'
    
    periods_history = CycleWindow.objects.filter(user=user, is_prediction=False).order_by('menstruation_start')
    predictions_log = CycleWindow.objects.filter(user=user, is_prediction=True).order_by('menstruation_start')

    ctx['objects'] = periods_history if show_history_view else predictions_log
    ctx['active_view'] = 'history' if show_history_view else 'predictions'

    return render(request, 'dashboard/logs/logs.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def add_period(request):
    ctx = {}
    
    if request.method == 'POST': 
        reference_month = datetime.strptime(request.POST.get('reference_month'), "%Y-%m-%d").date()
        calendar_data = render_selectable_calendars(request.user, reference_month)
        
        selected_days = parse_list_of_dates(request.POST.getlist('selected_days'))
        menstruation_windows_list = group_consecutive_days(selected_days)
        menstruation_ranges = generate_date_intervals(menstruation_windows_list)


        apply_period_windows(request.user, menstruation_ranges, calendar_data['rendered_month_start'], calendar_data['rendered_month_end'])
        # re-render changes
        calendar_data = render_selectable_calendars(request.user, reference_month)

    else:
        reference_month = date.today()
        calendar_data = render_selectable_calendars(request.user, reference_month)


    ctx['reference_month'] = reference_month
    ctx['calendars'] = calendar_data['calendars']
    ctx['selected_dates'] = calendar_data['selected_dates']
    ctx['rendered_month_start'] = calendar_data['rendered_month_start']
    ctx['rendered_month_end'] = calendar_data['rendered_month_end']

    return render(request, 'dashboard/log_period/log_period.html', ctx)


@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
@require_POST
def ajax_navigate_calendar(request):
    data = json.loads(request.body)

    reference_month = datetime.strptime(data.get('reference_month'), '%Y-%m-%d')
    button_type = data.get('button_type')

    if button_type == 'next_btn':
        new_reference_month = reference_month.replace(day=1) + relativedelta.relativedelta(months=1)
    elif button_type == 'prev_btn':
        new_reference_month = reference_month.replace(day=1) + relativedelta.relativedelta(months=-1)

    calendar_data = render_selectable_calendars(request.user, new_reference_month.date())

    response_data = {
        'reference_month': new_reference_month.strftime('%Y-%m-%d'),
        'calendars': calendar_data['calendars'],
        'selected_dates': calendar_data['selected_dates'],
        'rendered_month_start': calendar_data['rendered_month_start'].strftime('%Y-%m-%d'),
        'rendered_month_end': calendar_data['rendered_month_end'].strftime('%Y-%m-%d')
    }

    return JsonResponse(response_data)

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def add_log(request):
    ctx = {}

    if request.method == 'POST':
        # Get the date from POST data first
        selected_date = request.POST.get('date')
        
        # Try to get existing log for the selected date
        existing_log = None
        if selected_date:
            try:
                existing_log = DailyLog.objects.get(user=request.user, date=selected_date)
            except DailyLog.DoesNotExist:
                pass

        # Create forms with POST data and existing instances if they exist
        dl_form = DailyLogForm(request.POST, instance=existing_log)
        il_form = IntercourseLogForm(request.POST, instance=getattr(existing_log, 'intercourse', None) if existing_log else None)
        
        if all((dl_form.is_valid(), il_form.is_valid())):
            daily_log, created = DailyLog.objects.get_or_create(
                user=request.user,
                date=dl_form.cleaned_data['date'],
                defaults={}
            )

            for field, value in dl_form.cleaned_data.items():
                if field not in ['symptoms', 'moods', 'medications']:
                    setattr(daily_log, field, value)
            daily_log.user = request.user
            daily_log.save()

            if 'symptoms' in dl_form.cleaned_data:
                daily_log.symptoms_field.set(dl_form.cleaned_data['symptoms'])
            if 'moods' in dl_form.cleaned_data:
                daily_log.moods_field.set(dl_form.cleaned_data['moods'])
            if 'medications' in dl_form.cleaned_data:
                daily_log.medications_field.set(dl_form.cleaned_data['medications'])

            intercourse_log, _ = IntercourseLog.objects.get_or_create(log=daily_log)
            for field, value in il_form.cleaned_data.items():
                setattr(intercourse_log, field, value)
            intercourse_log.save()

            ctx['dl_form'] = DailyLogForm(instance=daily_log)
            ctx['il_form'] = IntercourseLogForm(instance=intercourse_log)
        else:
            # Form validation failed - keep the forms with errors and selected date
            ctx['dl_form'] = dl_form
            ctx['il_form'] = il_form
    else:
        # GET request - load forms for today's date
        current_day_log = get_day_log(request.user, date.today())
        
        if current_day_log:
            ctx['dl_form'] = DailyLogForm(instance=current_day_log)
            ctx['il_form'] = IntercourseLogForm(instance=getattr(current_day_log, 'intercourse', None))
        else:
            ctx['dl_form'] = DailyLogForm()
            ctx['il_form'] = IntercourseLogForm()
        
    return render(request, 'dashboard/add_log/add_log.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
@require_POST
def ajax_load_log(request):
    data = json.loads(request.body)
    date = data.get("date")
    if not date:
        print(date)

    try:
        log = DailyLog.objects.get(user=request.user, date=date)
        exists = True
    except DailyLog.DoesNotExist:
        log = None
        exists = False
    
    response_data = {"exists": exists}

    # Return data only if exists. Return empty form if it doesn't
    if log:
        il = IntercourseLog.objects.filter(log=log).first()

        response_data.update({
            # Daily log data
            "note": log.note,
            "flow": log.flow,
            "weight": log.weight,
            "temperature": log.temperature,
            "ovulation_test": log.ovulation_test,

            # M2M fields
            "symptoms": list(log.symptoms_field.values_list("id", flat=True)),
            "moods": list(log.moods_field.values_list("id", flat=True)),
            "medications": list(log.medications_field.values_list("id", flat=True)),

            # Intercourse
            "protected": il.protected if il else None,
            "orgasm": il.orgasm if il else None,
            "quantity": il.quantity if il else None,
        })

    else:
        response_data.update({
            "note": "",
            "flow": "",
            "weight": "",
            "temperature": "",
            "ovulation_test": "",

            "symptoms": [],
            "moods": [],
            "medications": [],

            "protected": "",
            "orgasm": "",
            "quantity": "",
        })

    return JsonResponse(response_data)

#TODO - might turn into a CBV
#TODO - add form to choose month_range
@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def stats(request):
    ctx = {}

    activity_metrics = get_intercourse_activity_metrics(user=request.user)
    frequency_metrics = get_intercourse_frequency_metrics(user=request.user)

    ctx['intercourse_count'] = activity_metrics['intercourse_count']
    ctx['orgasm_percentage'] = activity_metrics['orgasm_percentage']
    ctx['protected_count'] = activity_metrics['protected_count']
    ctx['unprotected_count'] = activity_metrics['unprotected_count']
    
    ctx['frequency_intercourse'] = frequency_metrics['frequency_intercourse']
    ctx['frequency_orgasm'] = frequency_metrics['frequency_orgasm']

    return render(request, 'dashboard/stats/stats.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
@require_POST
def ajax_load_stats(request):
    data = json.loads(request.body)
    month_range= int(data.get('month_range', 1))
    type=str(data.get('type'))

    response_data = {}
    if type == 'activity_dropdown':
        activity_metrics = get_intercourse_activity_metrics(user=request.user, month_range=month_range)
        response_data.update({
            'intercourse_count': activity_metrics['intercourse_count'],
            'orgasm_percentage': activity_metrics['orgasm_percentage'],
            'protected_count': activity_metrics['protected_count'],
            'unprotected_count': activity_metrics['unprotected_count']

        })

    elif type == 'frequency_dropdown':
        frequency_metrics = get_intercourse_frequency_metrics(user=request.user, month_range=month_range)
        response_data.update({
            'frequency_intercourse' : frequency_metrics['frequency_intercourse'],
            'frequency_orgasm' : frequency_metrics['frequency_orgasm']
        })

    return JsonResponse(response_data)