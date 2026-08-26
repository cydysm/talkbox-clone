from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from ..models import Post


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class MarkdownAdminEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "test-password"
        )
        cls.post = Post.objects.create(
            title="编辑器文章",
            slug="editor-post",
            author=cls.superuser,
            content_markdown="正文",
            status="published",
        )

    def test_change_form_includes_lightweight_editor_assets(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            f"/control-panel/blog/post/{self.post.pk}/change/"
        )
        self.assertContains(response, "talkbox-editor-template")
        self.assertContains(response, "/static/admin/markdown_editor.js")

    def test_upload_endpoint_inserts_images_from_admin(self):
        self.client.force_login(self.superuser)
        buffer = BytesIO()
        Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")
        upload = SimpleUploadedFile("editor.png", buffer.getvalue(), content_type="image/png")
        response = self.client.post(reverse("mediafiles:upload"), {
            "post": self.post.pk,
            "images": upload,
        })
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(self.post.images.count(), 1)
