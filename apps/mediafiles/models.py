from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image


class UploadedImage(models.Model):
    post = models.ForeignKey(
        "blog.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_images",
    )
    image = models.ImageField(upload_to="images/%Y/%m/")
    thumbnail = models.ImageField(upload_to="thumbnails/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    file_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.thumbnail:
            self.create_thumbnail()

    def create_thumbnail(self, size=(480, 480)):
        with Image.open(self.image.path) as source:
            self.width, self.height = source.size
            source.thumbnail(size, Image.Resampling.LANCZOS)
            buffer = BytesIO()
            source_format = source.format or "JPEG"
            source.save(buffer, format=source_format)
            filename = self.image.name.rsplit("/", 1)[-1]
            self.thumbnail.save(f"thumb-{filename}", ContentFile(buffer.getvalue()), save=False)
        super().save(update_fields=["thumbnail", "width", "height"])
