from django import forms

from apps.blog.models import Post

from .models import Comment


class CommentForm(forms.ModelForm):
    post = forms.ModelChoiceField(queryset=Post.objects.filter(status="published"), widget=forms.HiddenInput)

    class Meta:
        model = Comment
        fields = ["guest_name", "guest_email", "body", "parent"]
