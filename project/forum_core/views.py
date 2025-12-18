from django.shortcuts import render
from dashboard.services import user_type_required

# Create your views here.
@user_type_required(['PREMIUM'], denied_redirect_url='dashboard:settings_page')
def home(request):
    return render(request, 'forum_core/forum_home.html')

@user_type_required(['PREMIUM'], denied_redirect_url='dashboard:settings_page')
def thread(request, thread_id):
    return render(request, 'forum_core/thread.html')

@user_type_required(['PREMIUM'], denied_redirect_url='dashboard:settings_page')
def doctor_ranking(request):
    return render(request, 'forum_core/doctor_ranking.html')