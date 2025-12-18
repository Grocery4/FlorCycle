from django.shortcuts import render, redirect, get_object_or_404
from dashboard.services import user_type_required
from .models import Thread, Comment
from .forms import ThreadForm, EditThreadForm, CommentForm

# Create your views here.
@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
def home(request):
    threads = Thread.objects.all().order_by('-created_at')
    return render(request, 'forum_core/forum_home.html', {'threads': threads})

@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
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

@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
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

@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
def doctor_ranking(request):
    return render(request, 'forum_core/doctor_ranking.html')


@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
def edit_thread(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    if request.user != thread.created_by and request.user.user_type != 'MODERATOR':
        return redirect('forum_core:thread', thread_id=thread.id)

    if request.method == 'POST':
        form = EditThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            return redirect('forum_core:thread', thread_id=thread.id)
    else:
        form = EditThreadForm(instance=thread)
    return render(request, 'forum_core/edit_thread.html', {'form': form, 'thread': thread})


@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
def delete_thread(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    if request.user != thread.created_by and request.user.user_type != 'MODERATOR':
        return redirect('forum_core:thread', thread_id=thread.id)

    if request.method == 'POST':
        thread.delete()
        return redirect('forum_core:home')
    return render(request, 'forum_core/delete_confirm.html', {'obj': thread, 'type': 'thread'})


@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.created_by and request.user.user_type != 'MODERATOR':
        return redirect('forum_core:thread', thread_id=comment.thread.id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('forum_core:thread', thread_id=comment.thread.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'forum_core/edit_comment.html', {'form': form, 'comment': comment})


@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    thread_id = comment.thread.id
    if request.user != comment.created_by and request.user.user_type != 'MODERATOR':
        return redirect('forum_core:thread', thread_id=thread_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('forum_core:thread', thread_id=thread_id)
    return render(request, 'forum_core/delete_confirm.html', {'obj': comment, 'type': 'comment'})