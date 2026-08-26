from django.test import TestCase


class NotFoundPageTests(TestCase):
    def test_custom_404_page_is_rendered(self):
        response = self.client.get("/nonexistent-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "404", status_code=404)
        self.assertContains(response, "页面不存在", status_code=404)
