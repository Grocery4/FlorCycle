from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'forum_core/forum_home.html')

def thread(request, thread_id):
    return render(request, 'forum_core/thread.html')

def doctor_ranking(request):
    return render(request, 'forum_core/doctor_ranking.html')