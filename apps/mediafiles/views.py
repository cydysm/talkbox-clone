from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError

from apps.blog.models import Post

from .models import UploadedImage


def get_media_usage_bytes() -> int:
    media_root = Path(settings.MEDIA_ROOT)
    if not media_root.exists():
        return 0
    return sum(f.stat().st_size for f in media_root.rglob("*") if f.is_file())


@staff_member_required
@require_POST
def upload_images(request):
    post_id = request.POST.get("post")
    if post_id:
        if not post_id.isdigit():
            return JsonResponse({"errors": ["无效的文章 ID。"]}, status=400)
        post = get_object_or_404(Post, pk=post_id)
    else:
        post = None
    uploads = []
    errors = []
    files = request.FILES.getlist("images")
    max_files = settings.UPLOAD_MAX_IMAGES
    total_limit = settings.UPLOAD_TOTAL_LIMIT_GB * 1024 * 1024 * 1024
    current_usage = get_media_usage_bytes()

    if not files:
        return JsonResponse({"errors": ["请选择要上传的图片。"]}, status=400)
    if len(files) > max_files:
        return JsonResponse(
            {"errors": [f"每次最多上传 {max_files} 张图片。"]},
            status=400,
        )
    incoming_size = sum(f.size for f in files)
    if current_usage + incoming_size > total_limit:
        limit_gb = settings.UPLOAD_TOTAL_LIMIT_GB
        used_gb = round(current_usage / (1024 * 1024 * 1024), 2)
        return JsonResponse(
            {"errors": [f"媒体总容量已达上限（{used_gb}GB/{limit_gb}GB），无法继续上传。"]},
            status=507,
        )

    for uploaded_file in request.FILES.getlist("images"):
        filename = uploaded_file.name.rsplit("/", 1)[-1]
        if uploaded_file.size <= 0 or uploaded_file.size > settings.UPLOAD_MAX_BYTES:
            limit_mb = settings.UPLOAD_MAX_BYTES // (1024 * 1024)
            errors.append(f"{filename}：大小必须在 1 B 到 {limit_mb} MB 之间。")
            continue

        try:
            uploaded_file.seek(0)
            with Image.open(uploaded_file) as probe:
                image_format = (probe.format or "").upper()
                width, height = probe.size
                if image_format not in settings.ALLOWED_IMAGE_FORMATS:
                    raise UnidentifiedImageError
                if (
                    width < 1
                    or height < 1
                    or width > settings.IMAGE_MAX_DIMENSION
                    or height > settings.IMAGE_MAX_DIMENSION
                ):
                    errors.append(
                        f"{filename}：尺寸不能超过 {settings.IMAGE_MAX_DIMENSION}px。"
                    )
                    continue
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
            errors.append(f"{filename}：不是有效的图片文件。")
            continue
        finally:
            uploaded_file.seek(0)

        image = UploadedImage.objects.create(
            post=post,
            uploaded_by=request.user,
            image=uploaded_file,
            original_filename=filename,
            file_size=uploaded_file.size,
        )
        uploads.append({"url": image.image.url, "thumbnail": image.thumbnail.url})

    if not uploads:
        return JsonResponse({"errors": errors}, status=400)
    return JsonResponse({"images": uploads})
