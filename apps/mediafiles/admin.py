from django.contrib import admin

from .models import UploadedImage


@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "uploaded_by", "post", "width", "height", "file_size", "created_at"]
    list_filter = ["uploaded_by", "post", "created_at"]
    search_fields = ["original_filename", "image", "post__title"]
    readonly_fields = ["thumbnail", "width", "height", "file_size", "created_at"]
    autocomplete_fields = ["post", "uploaded_by"]
