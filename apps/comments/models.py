from django.conf import settings
from django.db import models


class Comment(models.Model):
    post = models.ForeignKey(
        "blog.Post",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="文章",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="父评论",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="comments",
        verbose_name="用户",
    )
    guest_name = models.CharField("昵称", max_length=80)
    guest_email = models.EmailField("邮箱")
    body = models.TextField("内容", max_length=5000)
    is_approved = models.BooleanField("已审核", default=False)
    ip_address = models.GenericIPAddressField("IP 地址", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comment by {self.guest_name} on {self.post_id}"
