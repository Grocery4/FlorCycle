from django.shortcuts import render, redirect, get_object_or_404
from dashboard.services import user_type_required
from .models import Thread, Comment
from .forms import ThreadForm, CommentForm

# Create your views here.
@user_type_required(['PREMIUM'], denied_redirect_url='dashboard:settings_page')
def home(request):
    threads = Thread.objects.all().order_by('-created_at')
    return render(request, 'forum_core/forum_home.html', {'threads': threads})

@user_type_required(['PREMIUM'], denied_redirect_url='dashboard:settings_page')
def create_thread(request):
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.created_by = request.user
            thread.save()
            return redirect('forum_core:thread', thread_id=thread.id)
    else:
        form = ThreadForm()
    return render(request, 'forum_core/create_thread.html', {'form': form})

@user_type_required(['PREMIUM'], denied_redirect_url='dashboard:settings_page')
def thread(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    comments = thread.comments.all().order_by('created_at')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.created_by = request.user
            comment.thread = thread
            comment.save()
            # Optionally add user to participants
            thread.participants.add(request.user)
            return redirect('forum_core:thread', thread_id=thread.id)
    else:
        form = CommentForm()
        
    return render(request, 'forum_core/thread.html', {
        'thread': thread,
        'comments': comments,
        'form': form
    })

@user_type_required(['PREMIUM'], denied_redirect_url='dashboard:settings_page')
def doctor_ranking(request):
    return render(request, 'forum_core/doctor_ranking.html')