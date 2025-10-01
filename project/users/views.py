from django.shortcuts import render

from .forms import DoctorSignupForm

# Create your views here.
#TODO - create real view
#TODO - validate only pdf files
#TODO - TEST license_no / username / email uniqueness
# TODO - display error
def doctor_form(request):
    ctx = {}
    ctx['form'] = DoctorSignupForm()

    if request.method == 'POST':
        form = DoctorSignupForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

    return render(request, 'test.html', ctx)