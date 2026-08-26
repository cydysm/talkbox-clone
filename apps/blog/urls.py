from django.urls import path, re_path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list_or_legacy_redirect, name="post-list"),
    path("category/<slug:slug>/", views.category_detail, name="category-detail"),
    path("tag/<int:tag_id>/", views.tag_detail, name="tag-detail"),
    path("search/", views.search_posts, name="search"),
    path("theme/", views.switch_theme, name="theme-switch"),
    path("post/<slug:slug>/", views.post_detail, name="post-detail"),
    path("post/<int:legacy_id>", views.legacy_post_redirect),
    path("post/<str:legacy_alias>", views.legacy_alias_redirect),
    path("post-<int:legacy_id>.html", views.legacy_post_redirect),
    path("<int:legacy_id>.html", views.legacy_post_redirect),
]


# Generic importers can preserve arbitrary source URLs. This fallback runs only
# after every concrete blog route has failed to match.
urlpatterns.append(re_path(
    r"^(?!category/|tag/|search/|rss\.xml$|atom\.xml$|sitemap\.xml$|healthz/|comments/|media-api/|admin/|control-panel/|static/|media/).+$",
    views.legacy_path_redirect,
))
