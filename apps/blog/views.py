import markdown
from django.core.cache import cache
from django.db.models import F
from django.shortcuts import get_object_or_404, render

from .models import Post


def post_list(request):
    posts = (
        Post.objects.filter(status="published")
        .select_related("author", "category")
        .only("id", "title", "slug", "excerpt", "views", "published_at", "created_at", "updated_at", "author__username", "category__name")
    )
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("author", "category"), slug=slug)
    if request.method == "GET":
        Post.objects.filter(pk=post.pk).update(views=F("views") + 1)
    cache_key = f"blog:html:{post.pk}:{post.updated_at.timestamp():.0f}"
    rendered_content = cache.get(cache_key)
    if rendered_content is None:
        rendered_content = markdown.markdown(post.content_markdown, extensions=["extra", "codehilite"])
        cache.set(cache_key, rendered_content, 3600)
    comments = post.comments.filter(is_approved=True).select_related("parent", "user")
    return render(
        request,
        "blog/post_detail.html",
        {"post": post, "content_html": rendered_content, "comments": comments},
    )
