from django.shortcuts import render

from .forms import DoctorSignupForm


# Create your views here.
def doctor_form(request):
    ctx = {}
    ctx['form'] = DoctorSignupForm()
    if request.method == 'POST':
        form = DoctorSignupForm(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            form.save()
    
    return render(request, 'test.html', ctx)