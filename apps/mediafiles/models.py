from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont


class UploadedImage(models.Model):
    post = models.ForeignKey(
        "blog.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
        verbose_name="所属文章",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_images",
        verbose_name="上传者",
    )
    image = models.ImageField("图片", upload_to="images/%Y/%m/")
    thumbnail = models.ImageField("缩略图", upload_to="thumbnails/%Y/%m/")
    original_filename = models.CharField("原始文件名", max_length=255)
    width = models.PositiveIntegerField("宽度", default=0)
    height = models.PositiveIntegerField("高度", default=0)
    file_size = models.PositiveIntegerField("文件大小", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "上传图片"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.thumbnail:
            self.create_thumbnail()

    def create_thumbnail(self, size=None):
        if size is None:
            size = getattr(settings, "THUMBNAIL_SIZE", (240, 240))
        with Image.open(self.image.path) as source:
            self.width, self.height = source.size
            watermarked = self.apply_watermark(source)
            watermarked.thumbnail(size, Image.Resampling.LANCZOS)
            buffer = BytesIO()
            output_format = "WEBP"
            filename_base = self.image.name.rsplit("/", 1)[-1].rsplit(".", 1)[0]

            if watermarked.mode == "RGBA" or "A" in watermarked.getbands():
                watermarked = watermarked.convert("RGB")
                watermarked = watermarked.convert("RGB")

            watermarked.save(buffer, format=output_format, quality=80)
            self.thumbnail.save(
                f"thumb-{filename_base}.webp",
                ContentFile(buffer.getvalue()),
                save=False,
            )
        super().save(update_fields=["thumbnail", "width", "height"])

    def apply_watermark(self, image):
        watermark_text = getattr(settings, "WATERMARK_TEXT", "")
        watermark_path = getattr(settings, "WATERMARK_IMAGE_PATH", "")
        if not watermark_text and not watermark_path:
            return image.copy()

        marked = image.convert("RGBA")
        if watermark_path:
            try:
                with Image.open(watermark_path).convert("RGBA") as mark:
                    scale = min(marked.width / (mark.width * 3), 1)
                    mark = mark.resize(
                        (max(1, int(mark.width * scale)), max(1, int(mark.height * scale))),
                        Image.Resampling.LANCZOS,
                    )
                    position = (marked.width - mark.width - 24, marked.height - mark.height - 24)
                    marked.alpha_composite(mark, position)
            except OSError:
                pass

        if watermark_text:
            overlay = Image.new("RGBA", marked.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            font_size = max(14, marked.width // 32)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()
            text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_size = (text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1])
            position = (max(16, marked.width - text_size[0] - 24), max(16, marked.height - text_size[1] - 24))
            draw.text(position, watermark_text, fill=(255, 255, 255, 180), font=font)
            marked.alpha_composite(overlay)
        return marked
