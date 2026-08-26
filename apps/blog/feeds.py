from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from .models import Post


class BasePostFeed(Feed):
    title = settings.SITE_NAME
    description = settings.SITE_DESCRIPTION
    link = "/"

    def items(self):
        return Post.objects.filter(status="published").order_by(
            "-published_at", "-created_at"
        )[: settings.FEED_LIMIT]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or item.content_markdown[:300]

    def item_pubdate(self, item):
        return item.published_at or item.created_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_link(self, item):
        return item.get_absolute_url()


class PostRSSFeed(BasePostFeed):
    pass


class PostAtomFeed(BasePostFeed):
    feed_type = Atom1Feed
    subtitle = BasePostFeed.description
