from functools import wraps
from django.shortcuts import redirect

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