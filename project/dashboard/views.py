from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _


from datetime import datetime, date, timedelta
from dateutil import relativedelta
import json

from .services import user_type_required, configured_required, fetch_closest_prediction, render_selectable_calendars, group_consecutive_days, generate_date_intervals, parse_list_of_dates, apply_period_windows, calculate_timeline_data
from .dashboard_analytics import get_intercourse_activity_metrics, get_intercourse_frequency_metrics
from cycle_core.models import CycleDetails, CycleStats, CycleWindow, MIN_LOG_FOR_STATS
from cycle_core.forms import CycleDetailsForm
from log_core.services import get_day_log
from log_core.models import DailyLog, IntercourseLog
from log_core.forms import DailyLogForm, IntercourseLogForm
from calendar_core.services import render_multiple_calendars, CalendarType

from users.models import PartnerProfile
from users.models import PartnerProfile, UserProfile
from users.services import link_partner, unlink_partner, activatePremiumSubscription, deactivatePremiumSubscription
from users.forms import UserUpdateForm, ProfileUpdateForm, PremiumUpgradeForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from notifications.services import check_dangerous_symptoms, check_upcoming_predictions


# Create your views here.

def _get_dashboard_user(request):
    if request.user.user_type == 'PARTNER':
        try:
            return request.user.partnerprofile.linked_user
        except:
            return None
    return request.user

@login_required(login_url='login')
def redirect_handler(request):
    if request.user.is_banned:
        from django.contrib.auth import logout
        logout(request)
        return redirect('users:banned')
        
    if request.user.user_type == 'STANDARD' or request.user.user_type == 'PREMIUM':
        return redirect('dashboard:homepage')
    elif request.user.user_type == 'PARTNER':
        if hasattr(request.user, 'partnerprofile') and request.user.partnerprofile.linked_user:
             return redirect('dashboard:homepage_readonly')
        return redirect('dashboard:partner_setup_page')
    elif request.user.user_type in ['DOCTOR', 'MODERATOR']:
        return redirect('forum_core:home')

@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
def calendar_view(request):
    ctx = {}
    
    user = _get_dashboard_user(request)
    if not user:
        return redirect('dashboard:partner_setup_page')

    ctx['is_partner'] = request.user.user_type == 'PARTNER'
    
    # request GET parameter to render a specific date
    date_param = request.GET.get('date')
    if date_param:
        try:
            reference_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            reference_date = date.today()
    else:
        reference_date = date.today()

    start_date = reference_date.replace(day=1) - relativedelta.relativedelta(months=1)
    
    # compute which months to render
    months_to_render = [
        start_date,
        start_date + relativedelta.relativedelta(months=1),
        start_date + relativedelta.relativedelta(months=2),
    ]
    
    visible_start = months_to_render[0]
    visible_end = (months_to_render[-1] + relativedelta.relativedelta(months=1)) - timedelta(days=1)
    
    # get CycleWindows in month range
    cycle_windows = CycleWindow.objects.filter(
        user=user,
        menstruation_start__lte=visible_end,
        max_ovulation_window__gte=visible_start 
    )
    
    menstruation_dates = set()
    ovulation_dates = set()
    
    for cw in cycle_windows:
        try:
            menstruation_dates.update(cw.getMenstruationDatesAsList())
            ovulation_dates.update(cw.getOvulationDatesAsList())
        except ValueError:
            continue

    # get DailyLogs in month range
    logs = DailyLog.objects.filter(
        user=user,
        date__gte=visible_start,
        date__lte=visible_end
    )
    
    log_dates = {log.date.strftime('%Y-%m-%d') for log in logs}

    # render calendars
    calendars = render_multiple_calendars(
        months=months_to_render,
        menstruation_dates=list(menstruation_dates),
        ovulation_dates=list(ovulation_dates),
        log_dates=list(log_dates),
        calendar_type=CalendarType.STANDARD
    )
    
    ctx['calendars'] = calendars

    # compute navigation dates    
    prev_date = reference_date - relativedelta.relativedelta(months=1)
    next_date = reference_date + relativedelta.relativedelta(months=1)
    
    ctx['prev_date'] = prev_date.strftime('%Y-%m-%d')
    ctx['next_date'] = next_date.strftime('%Y-%m-%d')

    return render(request, 'dashboard/calendar_view.html', ctx)


@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def homepage(request):
    ctx = {}
    ctx['next_prediction'] = fetch_closest_prediction(request.user)
    ctx['timeline_data'] = calculate_timeline_data(request.user)

    # Check for upcoming period/ovulation notifications
    check_upcoming_predictions(request.user)

    return render(request, 'dashboard/dashboard.html', ctx)

@user_type_required(['PARTNER'])
def partner_setup(request):
    from users.services import unlink_partner
    
    ctx = {}
    try:
        partner_profile = request.user.partnerprofile
        ctx['user'] = request.user
        ctx['partner_profile'] = partner_profile
        ctx['linked_user'] = partner_profile.linked_user
        
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'unlink':
                result = unlink_partner(request.user)
                if result:
                    ctx['unlink_success'] = _('Successfully unlinked from partner.')
                    ctx['linked_user'] = None
                    partner_profile.refresh_from_db()
                else:
                    ctx['unlink_error'] = _('Error unlinking from partner.')
        
    except:
        ctx['error'] = _('Partner profile not found')
    
    return render(request, 'dashboard/partner/partner_setup.html', ctx)

@user_type_required(['PARTNER'])
def homepage_readonly(request):
    ctx = {}
    try:
        partner_profile = request.user.partnerprofile
        linked_user = partner_profile.linked_user
        
        if not linked_user:
            ctx['error'] = _('No linked profile. Please link to a main user in partner setup.')
            return render(request, 'dashboard/dashboard_readonly.html', ctx)
        
        ctx['next_prediction'] = fetch_closest_prediction(linked_user)
        ctx['timeline_data'] = calculate_timeline_data(linked_user)
        
    except:
        ctx['error'] = 'Partner profile not found'
        return render(request, 'dashboard/dashboard_readonly.html', ctx)
    
    return render(request, 'dashboard/dashboard_readonly.html', ctx)

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

@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER', 'DOCTOR', 'MODERATOR'])
@configured_required
def settings(request):
    # Ensure UserProfile exists (for legacy users or those created before signal change)
    from users.models import UserProfile
    UserProfile.objects.get_or_create(user=request.user)
    
    ctx = {}
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if 'cycle_details' in request.POST:
            try:
                instance = request.user.cycledetails
            except CycleDetails.DoesNotExist:
                instance = None

            cycle_details_form = CycleDetailsForm(request.POST, mode='settings', user=request.user, instance=instance)
            if cycle_details_form.is_valid():
                cycle_details_form.save()
                messages.success(request, _('Cycle details updated successfully.'))
        
        elif action == 'update_user_info':
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, _('Email updated successfully.'))
            else:
                 messages.error(request, _('Error updating email.'))

        elif action == 'update_profile_pic':
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.userprofile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _('Profile picture updated successfully.'))
            else:
                messages.error(request, _('Error updating profile picture.'))

        elif action == 'change_password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, _('Your password was successfully updated!'))
            else:
                messages.error(request, _('Please correct the error below.'))
        
        elif action == 'link_partner':
            partner_code = request.POST.get('partner_code', '').strip()
            if partner_code:
                result = link_partner(request.user, partner_code)
                if result:
                    ctx['partner_link_success'] = _('Successfully linked to partner!')
                else:
                    ctx['partner_link_error'] = _('Invalid partner code or partner already linked to someone else.')
            else:
                ctx['partner_link_error'] = _('Please enter a partner code.')
        
        elif action == 'unlink_partner':
            try:
                partner_profiles = PartnerProfile.objects.filter(linked_user=request.user)
                for profile in partner_profiles:
                    unlink_partner(profile.user)
                ctx['partner_unlink_success'] = _('Successfully unlinked all partners.')
            except Exception as e:
                ctx['partner_unlink_error'] = _('Error unlinking partners: {error}').format(error=str(e))
        
        elif action == 'unlink_single_partner':
            try:
                partner_user_id = request.POST.get('partner_user_id')
                if partner_user_id:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    partner_user = User.objects.get(id=partner_user_id)
                    result = unlink_partner(partner_user)
                    if result:
                        ctx['partner_unlink_success'] = _('Successfully unlinked partner.')
                    else:
                        ctx['partner_unlink_error'] = _('Partner profile not found.')
            except Exception as e:
                ctx['partner_unlink_error'] = f'Error unlinking partner: {str(e)}'
        
        elif action == 'upgrade_premium':
            premium_form = PremiumUpgradeForm(request.POST, instance=request.user.userprofile)
            if premium_form.is_valid():
                plan = premium_form.cleaned_data['subscription_plan']
                activatePremiumSubscription(request.user, plan)
                messages.success(request, _('Welcome to Premium! You now have access to the forum.'))
                return redirect('dashboard:settings_page')
            else:
                messages.error(request, _('Error processing payment. Please check your card details.'))
        
        elif action == 'cancel_premium':
            deactivatePremiumSubscription(request.user)
            messages.info(request, _('Your premium subscription has been canceled.'))
            return redirect('dashboard:settings_page')
    
    # Initialize forms
    if 'cycle_details_form' not in ctx:
        try:
            instance = request.user.cycledetails
        except CycleDetails.DoesNotExist:
            instance = None
        ctx['cycle_details_form'] = CycleDetailsForm(user=request.user, mode='settings', instance=instance)
    if 'user_form' not in ctx:
        ctx['user_form'] = UserUpdateForm(instance=request.user)
    if 'profile_form' not in ctx:
        ctx['profile_form'] = ProfileUpdateForm(instance=request.user.userprofile)
    if 'password_form' not in ctx:
        ctx['password_form'] = PasswordChangeForm(request.user)
    if 'premium_form' not in ctx:
        ctx['premium_form'] = PremiumUpgradeForm(instance=request.user.userprofile)
    
    try:
        ctx['linked_partners'] = PartnerProfile.objects.filter(linked_user=request.user)
    except:
        ctx['linked_partners'] = []
    
    return render(request, 'dashboard/settings.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
def cycle_logs(request):
    ctx = {}

    user = _get_dashboard_user(request)
    if not user:
        return redirect('dashboard:partner_setup_page')

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


@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
@require_POST
def ajax_navigate_calendar(request):
    user = _get_dashboard_user(request)
    if not user:
        return JsonResponse({'error': 'No linked user'}, status=403)

    data = json.loads(request.body)

    reference_month = datetime.strptime(data.get('reference_month'), '%Y-%m-%d')
    button_type = data.get('button_type')

    if button_type == 'next_btn':
        new_reference_month = reference_month.replace(day=1) + relativedelta.relativedelta(months=1)
    elif button_type == 'prev_btn':
        new_reference_month = reference_month.replace(day=1) + relativedelta.relativedelta(months=-1)

    calendar_data = render_selectable_calendars(user, new_reference_month.date())

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
        selected_date = request.POST.get('date')
        
        existing_log = None
        if selected_date:
            try:
                existing_log = DailyLog.objects.get(user=request.user, date=selected_date)
            except DailyLog.DoesNotExist:
                pass

        # create forms with POST data and existing instances if they exist
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
                symptoms = dl_form.cleaned_data['symptoms']
                daily_log.symptoms_field.set(symptoms)
                # Check for dangerous symptoms and heavy bleeding
                symptom_names = [s.name for s in symptoms]
                flow_level = dl_form.cleaned_data.get('flow')
                check_dangerous_symptoms(request.user, symptom_names, flow_level)
            if 'moods' in dl_form.cleaned_data:
                daily_log.moods_field.set(dl_form.cleaned_data['moods'])
            if 'medications' in dl_form.cleaned_data:
                daily_log.medications_field.set(dl_form.cleaned_data['medications'])

            intercourse_log, _ = IntercourseLog.objects.get_or_create(log=daily_log)
            for field, value in il_form.cleaned_data.items():
                setattr(intercourse_log, field, value)
            intercourse_log.save()
            
            # Delete log if empty
            is_deleted = False
            if daily_log.is_empty():
                daily_log.delete()
                is_deleted = True
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if is_deleted:
                # If deleted, redirect to the same page but empty
                return redirect(f"{request.path}?date={daily_log.date.strftime('%Y-%m-%d')}")

            ctx['dl_form'] = DailyLogForm(instance=daily_log)
            ctx['il_form'] = IntercourseLogForm(instance=intercourse_log)
        else:
            # render forms with errors
            ctx['dl_form'] = dl_form
            ctx['il_form'] = il_form
    else:
        # load forms for a date
        date_param = request.GET.get('date')
        if date_param:
            try:
                selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                selected_date = date.today()
        else:
            selected_date = date.today()

        current_day_log = get_day_log(request.user, selected_date)
        
        if current_day_log:
            ctx['dl_form'] = DailyLogForm(instance=current_day_log)
            ctx['il_form'] = IntercourseLogForm(instance=getattr(current_day_log, 'intercourse', None))
        else:
            # pre-fill date field if selected date exists
            ctx['dl_form'] = DailyLogForm(initial={'date': selected_date})
            ctx['il_form'] = IntercourseLogForm()
        
    return render(request, 'dashboard/add_log/add_log.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
@require_POST
def ajax_load_log(request):
    
    user = _get_dashboard_user(request)
    if not user:
        return JsonResponse({'error': 'No linked user'}, status=403)

    data = json.loads(request.body)
    date = data.get("date")
    if not date:
        print(date)

    try:
        log = DailyLog.objects.get(user=user, date=date)
        exists = True
    except DailyLog.DoesNotExist:
        log = None
        exists = False
    
    response_data = {"exists": exists}
    
    # check for cycle status (Period/Ovulation) even if log doesn't exist
    cycle_windows = CycleWindow.objects.filter(
        user=user,
        menstruation_start__lte=date,
        max_ovulation_window__gte=date
    )
    
    is_period = False
    is_ovulation = False
    
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    
    # check if date is in a cycle window
    for cw in cycle_windows:
        if cw.menstruation_start <= date_obj <= cw.menstruation_end:
            is_period = True
        
        if cw.min_ovulation_window <= date_obj <= cw.max_ovulation_window:
            is_ovulation = True

    response_data['is_period'] = is_period
    response_data['is_ovulation'] = is_ovulation

    # return data only if exists. return empty form if it doesn't
    if log:
        il = IntercourseLog.objects.filter(log=log).first()
        from django.utils.translation import gettext as _rt

        response_data.update({
            "note": log.note,
            "flow": log.flow,
            "flow_display": _rt(log.get_flow_display()) if log.flow is not None else None,
            "weight": log.weight,
            "temperature": log.temperature,
            "ovulation_test": log.ovulation_test,

            "symptoms": [s.id for s in log.symptoms_field.all()],
            "symptoms_display": [str(s) for s in log.symptoms_field.all()],
            "moods": [m.id for m in log.moods_field.all()],
            "moods_display": [str(m) for m in log.moods_field.all()],
            "medications": [m.id for m in log.medications_field.all()],
            "medications_display": [str(med) for med in log.medications_field.all()],

            "protected": il.protected if il else None,
            "protected_display": _rt("Yes") if il and il.protected else (_rt("No") if il and il.protected is False else None),
            "orgasm": il.orgasm if il else None,
            "orgasm_display": _rt("Yes") if il and il.orgasm else (_rt("No") if il and il.orgasm is False else None),
            "quantity": il.quantity if il else None,
        })

    else:
        response_data.update({
            "note": "",
            "flow": "",
            "flow_display": "",
            "weight": "",
            "temperature": "",
            "ovulation_test": "",

            "symptoms": [],
            "symptoms_display": [],
            "moods": [],
            "moods_display": [],
            "medications": [],
            "medications_display": [],

            "protected": "",
            "protected_display": "",
            "orgasm": "",
            "orgasm_display": "",
            "quantity": "",
        })

    return JsonResponse(response_data)

#TODO - might turn into a CBV
#TODO - add form to choose month_range
@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
def stats(request):
    ctx = {}

    user = _get_dashboard_user(request)
    if not user:
        return redirect('dashboard:partner_setup_page')

    activity_metrics = get_intercourse_activity_metrics(user=user)
    frequency_metrics = get_intercourse_frequency_metrics(user=user)

    ctx['intercourse_count'] = activity_metrics['intercourse_count']
    ctx['orgasm_percentage'] = activity_metrics['orgasm_percentage']
    ctx['protected_count'] = activity_metrics['protected_count']
    ctx['unprotected_count'] = activity_metrics['unprotected_count']
    
    ctx['frequency_intercourse'] = frequency_metrics['frequency_intercourse']
    ctx['frequency_orgasm'] = frequency_metrics['frequency_orgasm']

    return render(request, 'dashboard/stats/stats.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
@require_POST
def ajax_load_stats(request):
    user = _get_dashboard_user(request)
    if not user:
         return JsonResponse({'error': 'No linked user'}, status=403)

    data = json.loads(request.body)
    month_range= int(data.get('month_range', 1))
    type=str(data.get('type'))

    response_data = {}
    if type == 'activity_dropdown':
        activity_metrics = get_intercourse_activity_metrics(user=user, month_range=month_range)
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


@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
def ajax_get_top_symptoms(request):
    user = _get_dashboard_user(request)
    if not user:
        return JsonResponse({'error': 'No linked user'}, status=403)

    from django.db.models import Count
    from log_core.models import SymptomLog
    # 1. Top 5 Symptoms
    # Group by symptom name and count.
    top_symptoms_qs = SymptomLog.objects.filter(log__user=user)\
        .values('symptom__name')\
        .annotate(count=Count('id'))\
        .order_by('-count')[:5]
        
    from django.utils.translation import gettext as _rt
    results = []
    
    for item in top_symptoms_qs:
        name = item['symptom__name']
        count = item['count']
        
        results.append({
            'name': _rt(name),
            'count': count
        })
        
    return JsonResponse({'top_symptoms': results})


@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
def ajax_get_available_items(request):
    from log_core.models import Symptom, Mood, Medication

    # Get only used items (optimisation) or all? 
    # Let's get all for now, or filter by what the user has actually used if preferred.
    # To keep it simple and discoverable, let's return all available types.
    # Or better: distinct existing logs to show what *can* be analyzed.
    
    from django.utils.translation import gettext as _rt
    
    symptoms = Symptom.objects.all()
    moods = Mood.objects.all()
    medications = Medication.objects.all()

    return JsonResponse({
        'symptoms': [{'id': s.name, 'name': _rt(s.name)} for s in symptoms],
        'moods': [{'id': m.name, 'name': _rt(m.name)} for m in moods],
        'medications': [{'id': med.name, 'name': _rt(med.name)} for med in medications]
    })

@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
@require_POST
def ajax_analyze_item(request):
    user = _get_dashboard_user(request)
    if not user:
        return JsonResponse({'error': 'No linked user'}, status=403)
        
    data = json.loads(request.body)
    item_type = data.get('item_type') # 'symptom', 'mood', 'medication'
    item_names = data.get('item_names', []) # List of names

    # Fallback for single item (backward compatibility if needed, but we'll update JS)
    if 'item_name' in data and not item_names:
        item_names = [data.get('item_name')]

    logs = DailyLog.objects.filter(user=user)
    
    if not item_names:
        return JsonResponse({'total': 0, 'occurrences': []})

    if item_type == 'symptom':
        logs = logs.filter(symptoms_field__name__in=item_names)
    elif item_type == 'mood':
        logs = logs.filter(moods_field__name__in=item_names)
    elif item_type == 'medication':
        logs = logs.filter(medications_field__name__in=item_names)
    else:
        return JsonResponse({'error': 'Invalid item type'}, status=400)
    
    # Distinct because one log might match multiple selected items
    logs = logs.distinct()
    
    total = logs.count()
    occurrences = [log.date.strftime('%Y-%m-%d') for log in logs.order_by('-date')]

    return JsonResponse({
        'total': total,
        'occurrences': occurrences
    })

@user_type_required(['STANDARD', 'PREMIUM', 'PARTNER'])
@configured_required
@require_POST
def ajax_search_logs(request):
    user = _get_dashboard_user(request)
    if not user:
        return JsonResponse({'error': 'No linked user'}, status=403)

    from django.db.models import Q
    data = json.loads(request.body)
    query = data.get('query')

    if not query:
        return JsonResponse({'results': []})

    logs = DailyLog.objects.filter(
        user=user, 
        note__icontains=query
    ).order_by('-date')

    results = []
    for log in logs:
        results.append({
            'date': log.date.strftime('%Y-%m-%d'),
            'note': log.note
        })

    return JsonResponse({'results': results})

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def backup_data(request):
    user = request.user
    data = {
        'cycle_details': {},
        'cycle_stats': {},
        'cycle_windows': [],
        'daily_logs': []
    }

    # CycleDetails
    cd = getattr(user, 'cycledetails', None)
    if cd:
        data['cycle_details'] = {
            'base_menstruation_date': cd.base_menstruation_date.strftime('%Y-%m-%d'),
            'avg_cycle_duration': cd.avg_cycle_duration,
            'avg_menstruation_duration': cd.avg_menstruation_duration
        }

    # CycleStats
    cs = getattr(user, 'cyclestats', None)
    if cs:
        data['cycle_stats'] = {
            'avg_cycle_duration': cs.avg_cycle_duration,
            'avg_menstruation_duration': cs.avg_menstruation_duration,
            'avg_ovulation_start_day': cs.avg_ovulation_start_day,
            'avg_ovulation_end_day': cs.avg_ovulation_end_day,
            'log_count': cs.log_count
        }

    # CycleWindows
    for cw in CycleWindow.objects.filter(user=user):
        data['cycle_windows'].append({
            'menstruation_start': cw.menstruation_start.strftime('%Y-%m-%d'),
            'menstruation_end': cw.menstruation_end.strftime('%Y-%m-%d') if cw.menstruation_end else None,
            'min_ovulation_window': cw.min_ovulation_window.strftime('%Y-%m-%d'),
            'max_ovulation_window': cw.max_ovulation_window.strftime('%Y-%m-%d'),
            'is_prediction': cw.is_prediction
        })

    # DailyLogs
    for log in DailyLog.objects.filter(user=user):
        log_data = {
            'date': log.date.strftime('%Y-%m-%d'),
            'note': log.note,
            'flow': log.flow,
            'weight': log.weight,
            'temperature': log.temperature,
            'ovulation_test': log.ovulation_test,
            'symptoms': [s.name for s in log.symptoms_field.all()],
            'moods': [m.name for m in log.moods_field.all()],
            'medications': [med.name for med in log.medications_field.all()],
        }
        
        il = getattr(log, 'intercourse', None)
        if il:
            log_data['intercourse'] = {
                'protected': il.protected,
                'orgasm': il.orgasm,
                'quantity': il.quantity
            }
        
        data['daily_logs'].append(log_data)

    response_content = json.dumps(data, indent=4)
    response = HttpResponse(response_content, content_type='application/json')
    filename = f"florcycle_backup_{user.username}_{date.today()}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
@require_POST
def restore_data(request):
    from django.db import transaction
    from log_core.models import Symptom, Mood, Medication
    
    backup_file = request.FILES.get('backup_file')
    if not backup_file:
        messages.error(request, _("No backup file provided."))
        return redirect('dashboard:settings_page')

    try:
        data = json.load(backup_file)
    except json.JSONDecodeError:
        messages.error(request, _("Invalid JSON file."))
        return redirect('dashboard:settings_page')

    try:
        with transaction.atomic():
            user = request.user
            
            # Delete existing data to prevent duplicates/conflicts (Cascade will handle logs-intercourse relationship)
            CycleWindow.objects.filter(user=user).delete()
            DailyLog.objects.filter(user=user).delete()

            # Restore CycleDetails
            if data.get('cycle_details'):
                cd_data = data['cycle_details']
                CycleDetails.objects.update_or_create(
                    user=user,
                    defaults={
                        'base_menstruation_date': datetime.strptime(cd_data['base_menstruation_date'], '%Y-%m-%d').date(),
                        'avg_cycle_duration': cd_data['avg_cycle_duration'],
                        'avg_menstruation_duration': cd_data['avg_menstruation_duration']
                    }
                )

            # Restore CycleStats
            if data.get('cycle_stats'):
                cs_data = data['cycle_stats']
                CycleStats.objects.update_or_create(
                    user=user,
                    defaults={
                        'avg_cycle_duration': cs_data['avg_cycle_duration'],
                        'avg_menstruation_duration': cs_data['avg_menstruation_duration'],
                        'avg_ovulation_start_day': cs_data['avg_ovulation_start_day'],
                        'avg_ovulation_end_day': cs_data['avg_ovulation_end_day'],
                        'log_count': cs_data['log_count']
                    }
                )

            # Restore CycleWindows
            for cw_data in data.get('cycle_windows', []):
                CycleWindow.objects.create(
                    user=user,
                    menstruation_start=datetime.strptime(cw_data['menstruation_start'], '%Y-%m-%d').date(),
                    menstruation_end=datetime.strptime(cw_data['menstruation_end'], '%Y-%m-%d').date() if cw_data['menstruation_end'] else None,
                    min_ovulation_window=datetime.strptime(cw_data['min_ovulation_window'], '%Y-%m-%d').date(),
                    max_ovulation_window=datetime.strptime(cw_data['max_ovulation_window'], '%Y-%m-%d').date(),
                    is_prediction=cw_data['is_prediction']
                )

            # Restore DailyLogs
            for log_data in data.get('daily_logs', []):
                daily_log = DailyLog.objects.create(
                    user=user,
                    date=datetime.strptime(log_data['date'], '%Y-%m-%d').date(),
                    note=log_data.get('note'),
                    flow=log_data.get('flow'),
                    weight=log_data.get('weight'),
                    temperature=log_data.get('temperature'),
                    ovulation_test=log_data.get('ovulation_test')
                )

                # Restore Symptoms
                for name in log_data.get('symptoms', []):
                    symptom = Symptom.objects.filter(name=name).first()
                    if symptom:
                        daily_log.symptoms_field.add(symptom)

                # Restore Moods
                for name in log_data.get('moods', []):
                    mood = Mood.objects.filter(name=name).first()
                    if mood:
                        daily_log.moods_field.add(mood)

                # Restore Medications
                for name in log_data.get('medications', []):
                    med = Medication.objects.filter(name=name).first()
                    if med:
                        daily_log.medications_field.add(med)

                # Restore IntercourseLog
                il_data = log_data.get('intercourse')
                if il_data:
                    IntercourseLog.objects.create(
                        log=daily_log,
                        protected=il_data.get('protected'),
                        orgasm=il_data.get('orgasm'),
                        quantity=il_data.get('quantity')
                    )

        messages.success(request, _("Data restored successfully."))
    except Exception as e:
        messages.error(request, _("Restore failed: {error}").format(error=str(e)))

    return redirect('dashboard:settings_page')

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
@require_POST
def reset_data(request):
    from django.db import transaction
    user = request.user
    
    try:
        with transaction.atomic():
            # Delete all cycle-related data
            CycleWindow.objects.filter(user=user).delete()
            DailyLog.objects.filter(user=user).delete()
            CycleDetails.objects.filter(user=user).delete()
            CycleStats.objects.filter(user=user).delete()
            
            # Reset configuration status
            profile = user.userprofile
            profile.is_configured = False
            profile.save()
            
        messages.success(request, _("All data has been reset. You can now start over."))
        return redirect('dashboard:setup_page')
    except Exception as e:
        messages.error(request, _("Reset failed: {error}").format(error=str(e)))
        return redirect('dashboard:settings_page')