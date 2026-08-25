from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

import markdown
from django.core.cache import cache
from django.db.models import F

from .models import Post


def post_list_or_legacy_redirect(request):
    legacy_post_id = request.GET.get("post", "")
    if legacy_post_id:
        return legacy_query_redirect(request)
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


def legacy_post_redirect(request, legacy_id):
    legacy_paths = (
        f"/post-{legacy_id}.html",
        f"/{legacy_id}.html",
        f"/post/{legacy_id}",
        f"/{legacy_id}",
    )
    post = Post.objects.filter(status="published").filter(
        legacy_url__in=legacy_paths
    ).first()
    if post is None:
        posts = [item for item in Post.objects.filter(status="published") if item.legacy_id == legacy_id]
        post = posts[0] if posts else None
    if post is None:
        raise Http404("旧文章不存在")
    return redirect(post, permanent=True)


def legacy_query_redirect(request):
    raw_id = request.GET.get("post", "")
    if not raw_id.isdigit():
        raise Http404("旧文章不存在")
    return legacy_post_redirect(request, int(raw_id))


def legacy_alias_redirect(request, legacy_alias):
    post = Post.objects.filter(status="published", slug=legacy_alias).first()
    if post is None:
        raise Http404("旧文章不存在")
    return redirect(post, permanent=True)
