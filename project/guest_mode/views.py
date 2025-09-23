from django.shortcuts import render

from cycle_core.forms import CycleDetailsForm
from cycle_core.services import PredictionBuilder

# Create your views here.
def show_form(request):
    ctx = {}
    ctx['form'] = CycleDetailsForm()

    if request.method == 'POST':
        form = CycleDetailsForm(request.POST)
        if form.is_valid():
            
            cd = form.save(commit=False)

            ctx['last_menstruation_date'] = cd.last_menstruation_date
            ctx['avg_cycle_duration'] = cd.avg_cycle_duration
            ctx['avg_menstruation_duration'] = cd.avg_menstruation_duration

            ctx['predictions'] = PredictionBuilder.generateMultiplePredictions(cd, 3)

            return render(request, 'show_form.html', ctx)

    return render(request, 'show_form.html', ctx)