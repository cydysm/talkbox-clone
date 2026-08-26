from django import forms

from apps.blog.models import Post

from .models import Comment


class CommentForm(forms.ModelForm):
    post = forms.ModelChoiceField(queryset=Post.objects.filter(status="published"), widget=forms.HiddenInput)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Comment
        fields = ["guest_name", "guest_email", "body", "parent"]

    def clean_honeypot(self):
        value = self.cleaned_data.get("honeypot", "")
        if value:
            raise forms.ValidationError("评论提交被拒绝。")
        return value
