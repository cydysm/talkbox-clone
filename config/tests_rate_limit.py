from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings


@override_settings(CACHES={
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "rate-limit-test",
    }
})
class LoginRateLimitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "correct-password"
        )

    def setUp(self):
        cache.clear()

    def test_failed_login_is_counted(self):
        for _ in range(4):
            self._post_login("wrong-password")
        response = self._post_login("wrong-password")
        self.assertEqual(response.status_code, 200)

    def test_blocked_after_limit(self):
        for _ in range(5):
            self._post_login("wrong-password")
        response = self._post_login("wrong-password")
        self.assertEqual(response.status_code, 403)

    def test_successful_login_clears_counter(self):
        for _ in range(3):
            self._post_login("wrong-password")
        response = self._post_login("correct-password")
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(cache.get("login-fail:127.0.0.1"))

    def _post_login(self, password):
        return self.client.post("/control-panel/login/", {
            "username": "admin",
            "password": password,
            "next": "/control-panel/",
        })
