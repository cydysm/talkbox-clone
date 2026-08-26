from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.blog.feeds import PostAtomFeed, PostRSSFeed
from apps.blog.sitemaps import PostSitemap
from config.health import healthz
from config.rate_limit import RateLimitedLoginView

ADMIN_URL = "control-panel/"

sitemaps = {"posts": PostSitemap}

admin_urlpatterns = [
    path("", RateLimitedLoginView.as_view(), name="login"),
    path("", admin.site.urls),
]

urlpatterns = [
    path("", include("apps.blog.urls")),
    path("comments/", include("apps.comments.urls")),
    path("media-api/", include("apps.mediafiles.urls")),
    path(f"{ADMIN_URL}login/", RateLimitedLoginView.as_view()),
    path(ADMIN_URL, admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("rss.xml", PostRSSFeed(), name="rss"),
    path("atom.xml", PostAtomFeed(), name="atom"),
    path("healthz/", healthz, name="healthz"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "config.urls.custom_404"


def custom_404(request, exception=None):
    from django.views.defaults import page_not_found

    return page_not_found(request, exception, template_name="404.html")
