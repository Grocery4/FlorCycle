from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from cycle_core.models import CycleDetails
from cycle_core.forms import CycleDetailsForm
from .services import user_type_required

# FIXME - what if it's a PremiumProfile?


# Create your views here.
@user_type_required(['STANDARD', 'PREMIUM'])
def homepage(request):
    profile = request.user.standardprofile
    if profile.is_configured:
        return render(request, 'dashboard/dashboard.html')
    else:
        return redirect('dashboard:setup_page')
    
@user_type_required(['STANDARD', 'PREMIUM'])
def setup(request):
    profile = request.user.standardprofile
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
            
            # TODO fix this shi
            profile = request.user.standardprofile
        
            cycle = form.save(commit=False)
            cycle.user = request.user  # link to logged-in user
            cycle.save()
            profile.is_configured = True
            profile.save()
            return redirect('dashboard:homepage')


    return render(request, 'dashboard/setup.html', ctx)
