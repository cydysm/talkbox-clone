from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.blog.models import Post

from .models import UploadedImage


@staff_member_required
@require_POST
def upload_images(request):
    post_id = request.POST.get("post")
    post = get_object_or_404(Post, pk=post_id) if post_id else None
    uploads = []
    for uploaded_file in request.FILES.getlist("images"):
        image = UploadedImage.objects.create(
            post=post,
            uploaded_by=request.user,
            image=uploaded_file,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
        )
        uploads.append({"url": image.image.url, "thumbnail": image.thumbnail.url})
    return JsonResponse({"images": uploads})
