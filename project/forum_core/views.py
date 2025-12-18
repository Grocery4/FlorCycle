from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg, Q
from dashboard.services import user_type_required
from users.models import CustomUser, DoctorProfile
from .models import Thread, Comment, DoctorRating
from .forms import ThreadForm, EditThreadForm, CommentForm, DoctorRatingForm

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
    from django.db import models
    doctors = DoctorProfile.objects.filter(is_verified=True).annotate(
        avg_rating=Avg('ratings__rating'),
        rating_count=models.Count('ratings')
    ).order_by('-avg_rating')
    
    return render(request, 'forum_core/doctor_ranking.html', {'doctors': doctors})


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


@user_type_required(['PREMIUM', 'DOCTOR', 'MODERATOR'], denied_redirect_url='dashboard:settings_page')
def user_profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    
    # Calculate comment count
    comment_count = Comment.objects.filter(created_by=profile_user).count()
    
    # Get participated threads (threads created by user OR where they commented)
    participated_threads = Thread.objects.filter(
        Q(created_by=profile_user) | Q(comments__created_by=profile_user)
    ).distinct().order_by('-created_at')

    # Doctor specific logic
    avg_rating = None
    ratings = []
    rating_form = None
    if profile_user.user_type == 'DOCTOR':
        doctor_profile = getattr(profile_user, 'doctorprofile', None)
        if doctor_profile:
            avg_rating = DoctorRating.objects.filter(doctor=doctor_profile).aggregate(Avg('rating'))['rating__avg']
            ratings = DoctorRating.objects.filter(doctor=doctor_profile).order_by('-created_at')

            # Rating logic: only other users can rate
            if request.user != profile_user:
                if request.method == 'POST' and 'submit_rating' in request.POST:
                    rating_form = DoctorRatingForm(request.POST)
                    if rating_form.is_valid():
                        r = rating_form.save(commit=False)
                        r.author = request.user
                        r.doctor = doctor_profile
                        r.save()
                        return redirect('forum_core:user_profile', username=username)
                else:
                    rating_form = DoctorRatingForm()

    return render(request, 'forum_core/profile.html', {
        'profile_user': profile_user,
        'comment_count': comment_count,
        'threads': participated_threads,
        'avg_rating': avg_rating,
        'ratings': ratings,
        'rating_form': rating_form
    })