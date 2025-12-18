from django import forms
from .models import Thread, Comment

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
