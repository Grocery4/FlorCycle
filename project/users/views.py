from django.shortcuts import render, redirect


from .forms import UserSignupForm, DoctorSignupForm, PartnerSignupForm


# Create your views here.

def standard_form(request):
    ctx = {}
    ctx['form'] = UserSignupForm()
    if request.method == 'POST':
        form = UserSignupForm(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return redirect('login')
    return render(request, 'registration/signup.html', ctx)

def doctor_form(request):
    ctx = {}
    ctx['form'] = DoctorSignupForm()
    if request.method == 'POST':
        form = DoctorSignupForm(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return redirect('login')
    
    return render(request, 'registration/signup.html', ctx)

def partner_form(request):
    ctx = {}
    ctx['form'] = PartnerSignupForm()
    if request.method == 'POST':
        form = PartnerSignupForm(request.POST)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return redirect('login')
         
    return render(request, 'registration/signup.html', ctx)
