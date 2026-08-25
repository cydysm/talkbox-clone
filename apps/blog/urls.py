from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list_or_legacy_redirect, name="post-list"),
    path("post/<slug:slug>/", views.post_detail, name="post-detail"),
    path("post/<int:legacy_id>", views.legacy_post_redirect),
    path("post/<str:legacy_alias>", views.legacy_alias_redirect),
    path("post-<int:legacy_id>.html", views.legacy_post_redirect),
    path("<int:legacy_id>.html", views.legacy_post_redirect),
]
