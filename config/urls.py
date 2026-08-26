from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.blog.sitemaps import PostSitemap
from apps.blog.feeds import PostAtomFeed, PostRSSFeed
from apps.blog.views import legacy_query_redirect

sitemaps = {"posts": PostSitemap}

urlpatterns = [
    path("", include("apps.blog.urls")),
    path("comments/", include("apps.comments.urls")),
    path("media-api/", include("apps.mediafiles.urls")),
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("rss.xml", PostRSSFeed(), name="rss"),
    path("atom.xml", PostAtomFeed(), name="atom"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
