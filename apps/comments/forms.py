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

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get("parent")
        post = cleaned_data.get("post")
        if parent and post:
            if parent.post_id != post.pk:
                self.add_error("parent", "回复目标不属于这篇文章。")
            elif not parent.is_approved:
                self.add_error("parent", "回复目标尚未通过审核。")
        return cleaned_data
