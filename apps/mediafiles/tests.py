from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import UploadedImage


def image_file(name="test.png", fmt="PNG", size=(10, 8), color="red"):
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format=fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


@override_settings(
    UPLOAD_MAX_BYTES=1024 * 1024,
    UPLOAD_MAX_IMAGES=3,
    IMAGE_MAX_DIMENSION=100,
)
class UploadSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("uploader", password="test-password")
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)
        self.url = reverse("mediafiles:upload")

    def test_valid_image_is_uploaded(self):
        response = self.client.post(self.url, {"images": image_file()})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["images"]), 1)
        self.assertIn("thumbnail", data["images"][0])
        self.assertEqual(UploadedImage.objects.count(), 1)

    @override_settings(ALLOWED_IMAGE_FORMATS=["PNG"])
    def test_non_image_is_rejected(self):
        fake = SimpleUploadedFile("fake.png", b"not-an-image", content_type="image/png")
        response = self.client.post(self.url, {"images": fake})
        self.assertEqual(response.status_code, 400)
        self.assertIn("不是有效的图片文件", response.json()["errors"][0])
        self.assertFalse(UploadedImage.objects.exists())

    def test_oversized_dimensions_are_rejected(self):
        response = self.client.post(self.url, {"images": image_file(size=(101, 50))})
        self.assertEqual(response.status_code, 400)
        self.assertIn("尺寸不能超过 100px", response.json()["errors"][0])
        self.assertFalse(UploadedImage.objects.exists())

    def test_batch_limit_is_enforced(self):
        files = [image_file(f"image-{number}.png") for number in range(4)]
        response = self.client.post(self.url, {"images": files})
        self.assertEqual(response.status_code, 400)
        self.assertIn("每次最多上传 3 张图片", response.json()["errors"][0])
        self.assertFalse(UploadedImage.objects.exists())
