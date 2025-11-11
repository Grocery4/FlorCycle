from functools import wraps
from django.shortcuts import redirect

from cycle_core.models import CycleWindow

def user_type_required(allowed_types, redirect_url='login'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(redirect_url)
            if request.user.user_type not in allowed_types:
                return redirect('guest_mode:show_form')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def configured_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect('login')

        profile = getattr(user, 'userprofile', None)
        if not profile or not profile.is_configured:
            return redirect('dashboard:setup_page')

        return view_func(request, *args, **kwargs)

    return _wrapped_view

#FIXME - dashboard.views.homepage
# should render next_prediction based on last CycleWindow, not setup CycleDetails.
def fetch_closest_prediction(user):
    prediction = CycleWindow.objects.filter(user=user, is_prediction=True).order_by('menstruation_start').first()
    return prediction