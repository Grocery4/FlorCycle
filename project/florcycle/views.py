from django.shortcuts import redirect
from django.db.utils import OperationalError

def root_redirect(request):
    """
    Redirects users based on their authentication status and user type.
    """
    if not request.user.is_authenticated:
        return redirect('guest_mode:show_form')
        
    if request.user.is_banned:
        from django.contrib.auth import logout
        logout(request)
        return redirect('users:banned')

    if request.user.user_type in ['STANDARD', 'PREMIUM']:
        return redirect('dashboard:homepage')
    elif request.user.user_type == 'PARTNER':
        # Check if linked
        try:
            if hasattr(request.user, 'partnerprofile') and request.user.partnerprofile.linked_user:
                 return redirect('dashboard:homepage_readonly')
        except OperationalError:
            # Handle case where DB might be in weird state or migration
            pass
        return redirect('dashboard:partner_setup_page')
    elif request.user.user_type in ['DOCTOR', 'MODERATOR']:
        return redirect('forum_core:home')
        
    # Fallback
    return redirect('dashboard:homepage')
