from django.shortcuts import render


from .forms import UserSignupForm, DoctorSignupForm


# Create your views here.

def standard_form(request):
    #TODO
    ctx = {}
    ctx['form'] = UserSignupForm()
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            print(form.cleaned_data)
    return render(request, 'signup.html', ctx)

def doctor_form(request):
    ctx = {}
    ctx['form'] = DoctorSignupForm()
    if request.method == 'POST':
        form = DoctorSignupForm(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            form.save()
    
    return render(request, 'signup.html', ctx)