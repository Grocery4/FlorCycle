from django import forms
from .models import Thread, Comment, DoctorRating

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Thread Title'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'What is on your mind?', 'rows': 5}),
        }

class EditThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'What is on your mind?', 'rows': 5}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Write a comment...', 'rows': 3}),
        }

class DoctorRatingForm(forms.ModelForm):
    class Meta:
        model = DoctorRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1, 6)], attrs={'class': 'form-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Share your experience...', 'rows': 3}),
        }
