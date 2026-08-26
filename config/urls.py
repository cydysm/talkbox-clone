from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.blog.sitemaps import PostSitemap
from apps.blog.feeds import PostAtomFeed, PostRSSFeed
from config.health import healthz
from apps.blog.views import legacy_query_redirect
from config.rate_limit import RateLimitedLoginView

sitemaps = {"posts": PostSitemap}

admin_urlpatterns = [
    path("login/", RateLimitedLoginView.as_view(), name="login"),
    path("", admin.site.urls),
]

urlpatterns = [
    path("", include("apps.blog.urls")),
    path("comments/", include("apps.comments.urls")),
    path("media-api/", include("apps.mediafiles.urls")),
    path("admin/", include(admin_urlpatterns)),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("rss.xml", PostRSSFeed(), name="rss"),
    path("atom.xml", PostAtomFeed(), name="atom"),
    path("healthz/", healthz, name="healthz"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
