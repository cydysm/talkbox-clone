from django.test import TestCase, override_settings
from django.urls import resolve, reverse


class RootRoutingTests(TestCase):
    def test_query_route_takes_priority(self):
        resolver_match = resolve("/")
        self.assertEqual(resolver_match.func.__name__, "legacy_query_redirect")

    def test_named_home_url_is_registered(self):
        self.assertEqual(reverse("blog:post-list"), "/")
