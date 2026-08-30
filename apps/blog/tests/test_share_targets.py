from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from ..models import Post, ShareTarget
from ..share_targets import SHARE_TARGETS, prepare_share_targets


class ShareTargetTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user("writer", password="test-password")
        self.post = Post.objects.create(
            title="分享测试",
            slug="share-test",
            author=self.author,
            content_markdown="正文",
            status="published",
        )
        self.url = self.post.get_absolute_url()

    def test_default_set_when_table_empty(self):
        response = self.client.get(self.url)
        body = response.content.decode()
        for label in ("复制链接", "微信", "微博", "小红书", "Threads", "X（Twitter）"):
            self.assertIn(label, body)
        self.assertNotIn("LinkedIn", body)

    def test_copy_targets_carry_message(self):
        response = self.client.get(self.url)
        body = response.content.decode()
        self.assertIn("data-share-message", body)
        self.assertIn("粘贴到微信", body)

    def test_url_targets_are_encoded_absolute_links(self):
        targets = prepare_share_targets(self.request_with_post(), self.post, [])
        weibo = next(t for t in targets if t["name"] == "weibo")
        self.assertTrue(weibo["href"].startswith("https://service.weibo.com/share/share.php?url=http%3A%2F%2F"))
        self.assertIn("%E5%88%86%E4%BA%AB%E6%B5%8B%E8%AF%95", weibo["href"])

    def request_with_post(self):
        from django.test import RequestFactory

        request = RequestFactory().get(self.url)
        request.META["SERVER_NAME"] = "testserver"
        request.META["SERVER_PORT"] = "80"
        return request

    def test_admin_order_and_visibility(self):
        names = ["x", "copylink"]
        for index, name in enumerate(names):
            ShareTarget.objects.create(name=name, order=index, is_visible=index == 0)
        response = self.client.get(self.url)
        body = response.content.decode()
        self.assertIn("X（Twitter）", body)
        self.assertNotIn("复制链接", body)

    def test_unknown_name_rejected(self):
        target = ShareTarget(name="nonexistent")
        with self.assertRaises(ValidationError):
            target.full_clean()

    def test_registry_has_no_linkedin(self):
        self.assertNotIn("linkedin", SHARE_TARGETS)
