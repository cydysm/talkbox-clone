from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.blog.models import Post
from apps.mediafiles.models import UploadedImage

from .models import Comment


class AdminOperationsTests(TestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "admin-password"
        )
        self.client.force_login(self.superuser)
        author = get_user_model().objects.create_user("author", password="author-password")
        self.post = Post.objects.create(
            title="Admin Post",
            slug="admin-post",
            author=author,
            content_markdown="Body",
            status="draft",
        )

    def test_comment_bulk_approval(self):
        comments = [
            Comment.objects.create(
                post=self.post,
                guest_name=f"Guest {number}",
                guest_email=f"guest-{number}@example.com",
                body="Comment",
            )
            for number in range(3)
        ]
        change_url = reverse("admin:comments_comment_changelist")
        response = self.client.post(
            change_url,
            {"action": "approve_comments", "_selected_action": [item.pk for item in comments]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(is_approved=True).count(), 3)

    def test_uploaded_image_is_listed_in_admin(self):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        buffer = BytesIO()
        Image.new("RGB", (10, 10), "blue").save(buffer, format="PNG")
        upload = SimpleUploadedFile("admin.png", buffer.getvalue(), content_type="image/png")
        UploadedImage.objects.create(
            post=self.post,
            uploaded_by=self.superuser,
            image=upload,
            original_filename="admin.png",
            file_size=upload.size,
        )
        response = self.client.get(reverse("admin:mediafiles_uploadedimage_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin.png")

    def test_draft_hidden_from_guest_and_previewable_by_staff(self):
        self.client.logout()
        guest_response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(guest_response.status_code, 404)

        staff = get_user_model().objects.create_user("staff", password="staff-password")
        staff.is_staff = True
        staff.save(update_fields=["is_staff"])
        self.client.force_login(staff)
        preview_response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(preview_response.status_code, 200)
