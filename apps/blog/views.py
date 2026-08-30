import markdown
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import InvalidPage, Paginator
from django.db import models
from django.db.models import F
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.plugins.registry import registry

from .models import Category, MarkdownSourceSetting, Page, Post, ShareTarget
from .share_targets import prepare_share_targets
from .theme_preferences import THEME_COOKIE_NAME, THEME_PREFERENCES


def _page_window(page_obj, span=2):
    """带省略号的页码窗口：首末页始终显示，与当前页相距超过 span 页时以 "gap" 占位。"""
    total = page_obj.paginator.num_pages
    current = page_obj.number
    if total <= (span * 2 + 3):
        return list(range(1, total + 1))
    pages = {1, total, current}
    pages.update(range(max(1, current - span), min(total, current + span) + 1))
    ordered = sorted(pages)
    window = []
    for index, number in enumerate(ordered):
        if index and number - ordered[index - 1] > 1:
            window.append("gap")
        window.append(number)
    return window


def render_paginated(request, queryset, template="blog/post_list.html", extra_context=None):
    paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
    page_number = request.GET.get("page", "1")
    try:
        page = paginator.page(page_number)
    except (InvalidPage, ValueError):
        page = paginator.page(1)
    context = {
        "page_obj": page,
        "posts": page.object_list,
        "page_window": _page_window(page),
        **(extra_context or {}),
    }
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
    if not post.is_accessible_by(request.user):
        raise Http404("文章不存在")
    if request.method == "GET":
        Post.objects.filter(pk=post.pk).update(views=F("views") + 1)
    cache_key = f"blog:html:{post.pk}:{post.updated_at.timestamp():.0f}"
    rendered_content = cache.get(cache_key)
    if rendered_content is None:
        rendered_content = markdown.markdown(
            post.content_markdown,
            extensions=["extra", "codehilite"],
            output_format="html5",
        )
        rendered_content = registry.apply_hook("transform_html", rendered_content)
        cache.set(cache_key, rendered_content, 3600)
    comments = post.comments.filter(is_approved=True).select_related("parent", "user")
    view_mode = "markdown" if request.GET.get("view") == "markdown" else "rendered"
    if view_mode == "markdown" and not MarkdownSourceSetting.enabled():
        return redirect(post)
    prev_post = next_post = None
    if post.published_at:
        published = (
            Post.objects.filter(status="published", published_at__isnull=False)
            .only("title", "slug", "published_at")
        )
        prev_post = published.filter(published_at__lt=post.published_at).order_by("-published_at").first()
        next_post = published.filter(published_at__gt=post.published_at).order_by("published_at").first()
    share_rows = ShareTarget.objects.filter(is_visible=True).only("name")
    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "content_html": rendered_content,
            "comments": comments,
            "view_mode": view_mode,
            "prev_post": prev_post,
            "next_post": next_post,
            "share_targets": prepare_share_targets(request, post, share_rows),
        },
    )


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    if page.status != "published" and not request.user.is_staff:
        raise Http404("页面不存在")
    content_html = markdown.markdown(
        page.content_markdown,
        extensions=["extra", "codehilite"],
        output_format="html5",
    )
    return render(
        request,
        "blog/page_detail.html",
        {"page": page, "content_html": content_html},
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


def legacy_path_redirect(request):
    legacy_url = request.path_info
    post = Post.objects.filter(status="published", legacy_url=legacy_url).first()
    if post is None:
        raise Http404("旧文章不存在")
    return redirect(post, permanent=True)


def switch_theme(request):
    if request.method != "POST":
        return redirect("blog:post-list")

    theme = request.POST.get("theme")
    if theme not in THEME_PREFERENCES:
        return HttpResponseBadRequest("未知主题偏好")

    next_url = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = "/"

    response = redirect(next_url)
    response.set_cookie(
        THEME_COOKIE_NAME,
        theme,
        max_age=365 * 24 * 60 * 60,
        secure=request.is_secure(),
        httponly=True,
        samesite="Lax",
    )
    return response
