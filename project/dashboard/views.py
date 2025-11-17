from django.shortcuts import render, redirect
from django.views import generic

from cycle_core.models import CycleDetails, CycleStats, CycleWindow
from cycle_core.forms import CycleDetailsForm
from .services import user_type_required, configured_required, fetch_closest_prediction


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
        ctx['avg_menstruation_duration'] = cs.avg_menstruation_duration

    show_history_view = request.GET.get('view') == 'history'
    
    periods_history = CycleWindow.objects.filter(user=user, is_prediction=False)
    predictions_log = CycleWindow.objects.filter(user=user, is_prediction=True)

    ctx['objects'] = periods_history if show_history_view else predictions_log
    ctx['active_view'] = 'history' if show_history_view else 'predictions'

    return render(request, 'dashboard/logs/logs.html', ctx)