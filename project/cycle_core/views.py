from django.shortcuts import render, HttpResponse

from .forms import CycleDetailsForm

# Create your views here.
def show_form(request):
    ctx = {}
    ctx['form'] = CycleDetailsForm()

    if request.method == 'GET':
        form = CycleDetailsForm(request.GET)
        if form.is_valid():
            ctx['last_menstruation_date'] = form.cleaned_data['last_menstruation_date']
            ctx['avg_cycle_duration'] = form.cleaned_data['avg_cycle_duration']
            ctx['avg_menstruation_duration'] = form.cleaned_data['avg_menstruation_duration']
            return render(request, 'cycle_details_test.html', ctx)
    
    return render(request, 'cycle_details_test.html', ctx)