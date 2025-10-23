from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from cycle_core.models import CycleDetails
from cycle_core.forms import CycleDetailsForm
from .services import user_type_required, configured_required

# Create your views here.
@user_type_required(['STANDARD', 'PREMIUM'])
@configured_required
def homepage(request):
    return render(request, 'dashboard/dashboard.html')
    
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
    if request.method == 'GET':
        ctx['cycle_details_form'] = CycleDetailsForm(user=request.user, instance=request.user.cycledetails)
    
    if request.method == 'POST':
        try:
            instance = request.user.cycledetails
        except CycleDetails.DoesNotExist:
            instance = None

        cycle_details_form = CycleDetailsForm(request.POST, instance=instance, user=request.user)
        if cycle_details_form.is_valid():
            cycle_details_form.save()
        
    ctx['cycle_details_form'] = CycleDetailsForm(user=request.user, instance=request.user.cycledetails)
    
    
    return render(request, 'dashboard/settings.html', ctx)

