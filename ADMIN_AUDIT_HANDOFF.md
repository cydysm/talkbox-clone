# 交接文档：Django 后台（control-panel）易用性整改

> 交接时间：2026-08-30。本文档供新会话接手使用，包含审计结论、修复建议、环境要点和验证方法。
> 审计方式：通读 admin 代码 + 临时超管账号实际登录逐页检查（临时账号已删除）。

## 0. 环境与项目要点（务必先读）

- 项目根：`/Users/irrelephant/PrivateX/talkbox-clone`（Django 博客，git 仓库，分支 main）
- Python 解释器：`/opt/homebrew/Caskroom/miniconda/base/envs/talkbox-clone/bin/python`
- 测试：`.../python manage.py test`（当前 **80 个测试全部通过**，含 `test_navigation.py`、`test_pages.py`）
- 本地 dev server：`127.0.0.1:8321`，启动命令 `.../python manage.py runserver 127.0.0.1:8321 --noreload`
- 后台地址：`http://127.0.0.1:8321/control-panel/`（`ADMIN_URL` 在 `config/urls.py`）
- 语言：`LANGUAGE_CODE = "zh-hans"`（`config/settings/base.py:92`）

### ⚠️ 静态文件双坑（本会话踩过）

1. 改 `themes/*/static/` 或 `apps/*/static/` 后必须 `manage.py collectstatic`（whitenoise + `CompressedManifestStaticFilesStorage`，收集副本在 `staticfiles/`）。
2. whitenoise 在非 DEBUG 下把静态文件**缓存在 dev server 进程内存**：collectstatic 必须在 server 启动**之前**完成，或之后**重启 server**，否则浏览器拿到的还是旧内容。另外浏览器对非 hash 文件有 `max-age=60` 缓存，改完要等 1 分钟或强刷。
3. `STATICFILES_DIRS` 同时收集**两个主题**的 static 目录（`base.py:103` 附近），同名路径先找到 `cactus_dark` 的，注意静默覆盖问题（见审计发现 A3）。

### ⚠️ URL 边界坑

`apps/blog/urls.py` 末尾有一个 legacy 兜底 `re_path`（放行任意未匹配路径）。2026-08-30 新加的独立页面路由 `/<slug>/` 已带保留前缀负向断言（排除 category/tag/search/theme/post/comments/media-api/admin/control-panel/static/media/healthz）。**新增顶级路由时必须同步维护这份排除列表**（曾有测试抓到 `healthz/` 被抢配）。

## 1. 当前工作区状态（未提交）

本轮已完成但**未 commit** 的改动（主题 UI + 后台新功能），接手时可先整体 review 后提交：

- 主题 UI：cactus 主题深浅两套的 `main.css`、`base.html`、`post_detail.html`、`post_list.html`、`search.html`；新增 `post_navigation.html`、`share_links.html`、`page_detail.html`、`js/main.js`、`js/post.js`（文章页固定导航含上一篇/下一篇/回到顶部/分享面板，Markdown 原文切换按钮在文章 header 右侧）
- 后台新功能：`NavItem`（导航链接，后台可管理，上限 `NAV_MAX_ITEMS=8`，模型 `clean()` 校验）+ migration `0004_navitem`；`Page`（独立页面，`/<slug>/` 顶级路径，保留字校验）+ migration `0005_page`；对应 admin 注册、context processor（`NAV_ITEMS` 注入，空表兜底「首页」）、测试 `test_navigation.py`（6 个）、`test_pages.py`（6 个）
- 其他改动：`theme_preferences.py`（`get_nav_items()`）、`views.py`（`page_detail`、post_detail 的 prev/next）、`urls.py`、`config/settings/base.py`（`NAV_MAX_ITEMS`）、`seed_data.py`（此前会话遗留改动，接手时确认内容）
- 开发库中留有示例数据：1 篇「关于」独立页面（slug=about，占位内容）+ 1 条「关于」导航链接，可留可删

## 2. 审计发现与修复建议（按建议动手顺序）

### ① 补全模型中文 verbose_name（改动最小、观感提升最大）

现状证据：后台显示「Posts / Comments / Uploaded images / 标签项」模型名英文；列表页标题「选择 post 来修改」「增加 POST」、统计「4 comments」中英混排；评论列表「父评论」列显示英文 `Comment by 老访客 on 3`。

改法：
- `apps/blog/models.py`：`Post`、`Comment`（在 `apps/comments/models.py`）、`UploadedImage`（`apps/mediafiles/models.py`）的 Meta 加 `verbose_name`/`verbose_name_plural`（如 "文章"/"评论"/"上传图片"），字段 label 大多已中文化，缺的补上。
- taggit 的 app 名「标签项」：在 `INSTALLED_APPS` 用自定义 label 或加 `apps.py` verbose_name，或接受现状。
- `Comment.__str__`（apps/comments/models.py）改成中文，例如 `f"{self.guest_name} 评论了《{self.post.title}》"`。

### ② 仪表盘样式与信息架构

文件：`apps/blog/templates/admin/dashboard.html`（已读，结构是 `.talkbox-stats > .stat-card` 三张卡 + 最新待审核评论列表）。

- `.talkbox-stats`/`.stat-card` **没有任何 CSS**（全项目 grep 无定义），渲染为无样式文本。改法：新建 `apps/blog/templates/admin/base_site.html` 覆写，在里面加 `{% block extrahead %}<style>…卡片布局…</style>{% endblock %}`；或加 admin CSS 静态文件。
- 统计数字加链接：文章卡→`admin:blog_post_changelist`、待审核→`admin:comments_comment_changelist?is_approved__exact=0`。
- 隐藏「最近动作」块：覆写 `admin/index.html` 去掉 `{% block recent_actions %}`（dashboard.html 里 `{{ block.super }}` 会带出来，需要改为继承 `admin/base.html` 自行拼装，或在 base_site 用 CSS 隐藏 `#recent-actions-module`）。
- 「最新待审核评论」列表项建议直接链接到评论 change 页而非文章页，并显示评论正文截断。

### ③ 文章编辑页 fieldsets 重排

文件：`apps/blog/admin.py` 的 `PostAdmin`。

- 现状：字段平铺，「状态」「发布时间」「Emlog 原链接」在长 Markdown 正文**之后**，发布一篇文章要滚到底。
- 建议 fieldsets：
  ```python
  fieldsets = [
      (None, {"fields": ["title", "slug", "excerpt"]}),
      ("内容", {"fields": ["content_markdown"]}),
      ("发布", {"fields": ["status", "published_at", "author", "category", "tags"]}),
      ("元数据", {"fields": ["legacy_url"], "classes": ["collapse"]}),
  ]
  ```
- 作者默认当前用户：`def get_changeform_initial_data(self, request): return {"author": request.user}`。
- 保留现有 actions（发布/转草稿）、markdown_editor Media、date_hierarchy。

### ④ 主题设置页去自由化

文件：`apps/blog/admin.py` 的 `ThemeSettingAdmin`；模型 `apps/blog/models.py` 的 `ThemeSetting`。

- 现状：可勾选多个主题同时「当前启用」（`default_theme()` 只取其一，静默不一致）；可「增加」任意不存在的主题名。
- 改法：`ThemeSettingAdmin.has_add_permission = lambda self, request: False`（主题是代码定义的，不该后台新增）；「当前启用」改单选语义——最简单是用 action（「设为当前主题」）替代 `list_editable` 的勾选框，或在 `save_model`/`clean` 里强制启用新的同时取消其他（`ThemeSetting.set_active` 已有此语义，`base.py` models 55 行附近）。
- 顺带：给 `name` 字段加 `clean()` 校验 `name in settings.AVAILABLE_THEMES`。

### ⑤ 评论审核效率

文件：`apps/comments/admin.py`。

- `list_display` 加 `body` 截断列：`["guest_name", "short_body", "post", "is_approved", "created_at"]`，`short_body` 用 `format_html` 或 admin display 描述 `body[:50]`。
- 默认只看待审核：重写 `get_queryset` 或 `changelist_view` 设默认过滤，或至少把「待审核」做成显眼入口（配合 ② 的仪表盘链接）。
- Select2 空选项英文 `- Select an option -`：autocomplete 控件 locale 问题，低优先级，可在 admin 基模板引入 select2 中文包或忽略。

### ⑥ 编辑器资源迁移（顺手项）

- `themes/cactus_dark/static/admin/markdown_editor.{css,js}` → `apps/blog/static/admin/`（新建 app static 目录即可被 `AppDirectoriesFinder` 找到）。迁移后 `collectstatic` + 重启 server，并跑 `manage.py findstatic admin/markdown_editor.css` 验证只剩新位置。
- 两主题 static 目录从此只放前端主题资源，消除同名静默覆盖隐患。
- 可选增强：编辑器加预览面板（当前是纯 textarea + 文字工具条，无预览/分屏/自动保存；图片上传依赖 `/media-api/upload/`，成功后光标处插入 markdown）。

### ⑦ 杂项

- `PageAdmin`（apps/blog/admin.py）加 `view_on_site = True`（Page 有 `get_absolute_url`），编辑页即可「在站点上查看」。
- 文章列表标签过滤器大小写重复（`django/Django`、`python/Python`）：清理 seed 数据的标签大小写（`apps/blog/seed_data.py`），过滤器本身可不管。
- 评论列表 IP 列是访客隐私，后台可见可接受，不需要改。

## 3. 每步完成后的验证清单

1. `.../python manage.py test` → 期望 `Ran 80+ tests ... OK`（新加测试另计）
2. `.../python manage.py collectstatic --noinput`（若改了 static）
3. 重启 8321 server（先于 collectstatic 完成后再启动，见第 0 节坑 2）
4. 浏览器逐页看：仪表盘（卡片有样式、数字可点）、文章新增页（状态在顶部、作者已预填、无中文混杂）、文章列表（无 "post" 英文）、评论列表（正文列、中文 str）、主题设置（无法新增、单选语义）、`/about/`（独立页面仍正常）
5. 后台登录用你自己的超管账号；需要临时账号时记得审计后删除（本会话的 `audit_temp` 已删）

## 4. 相关文件速查

| 文件 | 作用 |
|---|---|
| `apps/blog/admin.py` | blog 后台（Post/Category/NavItem/Page/ThemeSetting/PluginSetting + 仪表盘 hook） |
| `apps/comments/admin.py` | 评论后台 |
| `apps/mediafiles/admin.py` | 上传图片后台 |
| `apps/blog/models.py` | Post/Category/NavItem/Page/ThemeSetting/PluginSetting |
| `apps/blog/templates/admin/dashboard.html` | 自定义仪表盘（样式缺失待修） |
| `themes/cactus_dark/static/admin/markdown_editor.{js,css}` | Markdown 编辑器（待迁出主题目录） |
| `apps/blog/templates/admin/blog/post/change_form.html` | 编辑器注入模板（template#talkbox-editor-template） |
| `config/settings/base.py` | `NAV_MAX_ITEMS`、`AVAILABLE_THEMES`、`STATICFILES_DIRS`（双主题收集） |
| `apps/blog/urls.py` | 页面路由 + legacy 兜底（保留前缀排除列表在此维护） |
