from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

import markdown
from django.core.cache import cache
from django.core.paginator import InvalidPage, Paginator
from django.db import models
from django.db.models import F

from .models import Category, Post
from apps.plugins.registry import registry


def render_paginated(request, queryset, template="blog/post_list.html", extra_context=None):
    paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
    page_number = request.GET.get("page", "1")
    try:
        page = paginator.page(page_number)
    except (InvalidPage, ValueError):
        page = paginator.page(1)
    context = {"page_obj": page, "posts": page.object_list, **(extra_context or {})}
    return render(request, template, context)


def post_list_or_legacy_redirect(request):
    legacy_post_id = request.GET.get("post", "")
    if legacy_post_id:
        return legacy_query_redirect(request)
    posts = (
        Post.objects.filter(status="published")
        .select_related("author", "category")
        .only("id", "title", "slug", "excerpt", "views", "published_at", "created_at", "updated_at", "author__username", "category__name")
    )
    return render_paginated(request, posts)


def published_posts():
    return (
        Post.objects.filter(status="published")
        .select_related("author", "category")
        .prefetch_related("tags")
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = published_posts().filter(category=category)
    return render_paginated(
        request,
        posts,
        extra_context={"page_title": f"分类：{category.name}"},
    )


def tag_detail(request, tag_id):
    posts = published_posts().filter(tags__id=tag_id)
    tag_name = posts.first().tags.all()[0].name if posts else ""
    return render_paginated(
        request,
        posts,
        extra_context={"page_title": f"标签：{tag_name}" if tag_name else "标签"},
    )


def search_posts(request):
    query = request.GET.get("q", "").strip()
    posts = published_posts()
    if query:
        posts = posts.filter(
            models.Q(title__icontains=query)
            | models.Q(excerpt__icontains=query)
            | models.Q(content_markdown__icontains=query)
            | models.Q(tags__name__icontains=query)
        ).distinct()
    return render_paginated(
        request,
        posts,
        template="blog/search.html",
        extra_context={"query": query},
    )


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("author", "category"), slug=slug)
    if request.method == "GET":
        Post.objects.filter(pk=post.pk).update(views=F("views") + 1)
    cache_key = f"blog:html:{post.pk}:{post.updated_at.timestamp():.0f}"
    rendered_content = cache.get(cache_key)
    if rendered_content is None:
        rendered_content = markdown.markdown(post.content_markdown, extensions=["extra", "codehilite"])
        rendered_content = registry.apply_hook("transform_html", rendered_content)
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
