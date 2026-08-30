from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.comments.models import Comment

from ..admin import PostAdmin, ThemeSettingAdmin
from ..models import Post, ThemeSetting


class AdminPolishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "test-password"
        )
        cls.rf = RequestFactory()

    # ---- 主题设置去自由化 ----

    def test_theme_settings_cannot_be_added_or_edited_in_admin(self):
        request = self.rf.get("/")
        request.user = self.superuser
        model_admin = ThemeSettingAdmin(ThemeSetting, site)
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))

    def test_set_active_action_activates_single_theme(self):
        ThemeSetting.objects.create(name="cactus_dark")
        light = ThemeSetting.objects.create(name="cactus_light")
        changelist = reverse("admin:blog_themesetting_changelist")
        self.client.force_login(self.superuser)
        response = self.client.post(
            changelist,
            {
                "action": "set_active_theme",
                "_selected_action": [str(light.pk)],
                "select_across": "0",
                "index": "0",
            },
            follow=True,
        )
        self.assertContains(response, "已启用主题")
        self.assertTrue(ThemeSetting.objects.get(name="cactus_light").is_active)
        self.assertFalse(ThemeSetting.objects.get(name="cactus_dark").is_active)

    def test_unknown_theme_name_rejected(self):
        setting = ThemeSetting(name="not_a_theme")
        with self.assertRaises(ValidationError):
            setting.full_clean()
        ThemeSetting(name="cactus_dark").full_clean()

    # ---- 文章编辑页 ----

    def test_new_post_defaults_author_to_current_user(self):
        request = self.rf.get("/")
        request.user = self.superuser
        model_admin = PostAdmin(Post, site)
        initial = model_admin.get_changeform_initial_data(request)
        self.assertEqual(initial["author"], self.superuser)

    def test_post_add_form_groups_publish_fields_first(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:blog_post_add"))
        content = response.content.decode()
        # 字段分组顺序：基本信息 → 内容 → 发布（status 在 content_markdown 之后、元数据之前）
        self.assertLess(
            content.index('name="content_markdown"'), content.index('name="status"')
        )
        self.assertLess(
            content.index('name="status"'), content.index('name="legacy_url"')
        )

    # ---- 评论 ----

    def test_comment_str_is_chinese(self):
        post = Post.objects.create(
            title="测试文章",
            slug="str-post",
            author=self.superuser,
            content_markdown="正文",
        )
        comment = Comment.objects.create(
            post=post, guest_name="老访客", guest_email="a@example.com", body="好文"
        )
        self.assertEqual(str(comment), "老访客 评论了《测试文章》")

    def test_comment_list_shows_body_excerpt(self):
        post = Post.objects.create(
            title="列表文章",
            slug="list-post",
            author=self.superuser,
            content_markdown="正文",
        )
        Comment.objects.create(
            post=post,
            guest_name="老访客",
            guest_email="a@example.com",
            body="这条评论的正文应该出现在列表里" * 3,
        )
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:comments_comment_changelist"))
        self.assertContains(response, "这条评论的正文应该出现在列表里")
