from django.shortcuts import render, redirect

# Create your views here.
def homepage(request):
    ctx = {}
    if request.user.is_authenticated:
        return render(request, 'dashboard/dashboard.html', ctx)
    else:
        return redirect('guest_mode:show_form')