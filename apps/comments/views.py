from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CommentForm


@require_POST
def create_comment(request):
    form = CommentForm(request.POST)
    next_url = request.POST.get("next", "/")
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = form.cleaned_data["post"]
        comment.ip_address = request.META.get("REMOTE_ADDR")
        if request.user.is_authenticated:
            comment.user = request.user
            comment.is_approved = True
        comment.save()
        messages.success(request, "评论已提交。" if comment.is_approved else "评论已提交，等待审核。")
    else:
        messages.error(request, "评论提交失败，请检查表单。")
    return HttpResponseRedirect(next_url)
