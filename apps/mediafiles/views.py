from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.conf import settings
from PIL import Image, UnidentifiedImageError

from apps.blog.models import Post

from .models import UploadedImage


@staff_member_required
@require_POST
def upload_images(request):
    post_id = request.POST.get("post")
    post = get_object_or_404(Post, pk=post_id) if post_id else None
    uploads = []
    errors = []
    files = request.FILES.getlist("images")
    max_files = settings.UPLOAD_MAX_IMAGES

    if not files:
        return JsonResponse({"errors": ["请选择要上传的图片。"]}, status=400)
    if len(files) > max_files:
        return JsonResponse(
            {"errors": [f"每次最多上传 {max_files} 张图片。"]},
            status=400,
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
                if not image_format in settings.ALLOWED_IMAGE_FORMATS:
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
        except (OSError, UnidentifiedImageError):
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
