from django.apps import AppConfig
from taggit.apps import TaggitAppConfig


class BlogConfig(AppConfig):
    # apps.py 存在多个 AppConfig 时需显式指定默认配置
    default = True
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"
    verbose_name = "博客"


class TaggitChineseConfig(TaggitAppConfig):
    # 让后台 app 列表里的 taggit 显示中文而非「标签项」
    name = "taggit"
    verbose_name = "标签"
