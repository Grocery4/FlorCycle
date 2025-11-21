from django.shortcuts import render, redirect
from django.views import generic

from datetime import date

from .services import user_type_required, configured_required, fetch_closest_prediction
from cycle_core.models import CycleDetails, CycleStats, CycleWindow
from cycle_core.forms import CycleDetailsForm
from log_core.services import get_day_log
from log_core.models import DailyLog, IntercourseLog
from log_core.forms import DailyLogForm, IntercourseLogForm

# Create your views here.
@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def homepage(request):
    ctx = {}
    ctx['next_prediction'] = fetch_closest_prediction(request.user)

    return render(request, 'dashboard/dashboard.html', ctx)
    
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
    try:
        cs = user.cyclestats
    except CycleStats.DoesNotExist:
        cs = None

    if cs:
        ctx['avg_cycle_duration'] = cs.avg_cycle_duration
        ctx['log_count'] = cs.log_count
        ctx['avg_menstruation_duration'] = cs.avg_menstruation_duration

    show_history_view = request.GET.get('view') == 'history'
    
    periods_history = CycleWindow.objects.filter(user=user, is_prediction=False)
    predictions_log = CycleWindow.objects.filter(user=user, is_prediction=True)

    ctx['objects'] = periods_history if show_history_view else predictions_log
    ctx['active_view'] = 'history' if show_history_view else 'predictions'

    return render(request, 'dashboard/logs/logs.html', ctx)

@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def add_log(request):
    ctx = {}

    #TODO - period start can be inserted only if selected_date <= today, else show period end button only
    # TODO - add Period Start/End logic
    # TODO - if DailyLog in range of a real Period window: sync DailyLog to closest real Period

    current_day_log = get_day_log(request.user, date.today())
    
    if current_day_log:
        ctx['dl_form'] = DailyLogForm(instance=current_day_log)
        ctx['il_form'] = IntercourseLogForm(instance=getattr(current_day_log, 'intercourse', None))
    else:
        ctx['dl_form'] = DailyLogForm()
        ctx['il_form'] = IntercourseLogForm()



    if request.method == 'POST':

        dl_form = DailyLogForm(request.POST)
        il_form = IntercourseLogForm(request.POST)
        
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


    return render(request, 'dashboard/add_log/add_log.html', ctx)