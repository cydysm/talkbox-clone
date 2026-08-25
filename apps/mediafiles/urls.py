from django.urls import path

from . import views

app_name = "mediafiles"

urlpatterns = [
    path("upload/", views.upload_images, name="upload"),
]
