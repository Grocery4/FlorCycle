from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator


from .forms import UserSignupForm, DoctorSignupForm, PartnerSignupForm


def redirect_if_authenticated(user):
    return not user.is_authenticated


@method_decorator(user_passes_test(redirect_if_authenticated, login_url='/dashboard/redirect'), name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

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
