# Talkbox Clone

一个基于 Python 3、Django、PostgreSQL、Redis、Docker、Gunicorn 和 Gevent 的轻量博客系统。当前版本提供可运行的 MVP 骨架，后续可继续扩展其他博客导入、插件系统和更多主题。

## 功能

- Django Admin 管理文章与分类
- Markdown 文章渲染和 Redis 渲染缓存
- 多标签（django-taggit）
- 树形评论模型和评论审核状态
- 评论与回复邮件提醒
- 图片上传与缩略图生成
- 图片上传安全校验：真实格式、大小、数量和尺寸限制
- 轻量插件机制与 Markdown/HTML 内容钩子
- Cactus Dark 主题模板
- 分类页、标签页和站内搜索
- 文章列表统一分页，每页数量可配置
- 后台多模板切换，当前支持 Cactus Dark 和 Cactus Light
- Emlog JSON/SQLite 导入：文章、分类、标签和评论树
- Emlog 旧链接 301 重定向
- 浏览量统计、站点地图和安全响应基线
- Docker Compose 一键启动 PostgreSQL、Redis 和 Web
- Miniconda 管理本地 Python 环境

## 本地环境

```bash
conda env create -f environment.yml
conda activate talkbox-clone
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 导入 Emlog 数据

支持官方表结构的 SQLite 文件，或包含 `posts`、`categories`、`tags`、`comments` 四个数组的 JSON：

```bash
python manage.py import_emlog /path/to/emlog.sqlite3 --author-id 1
python manage.py import_emlog /path/to/emlog-export.json --author-id 1
```

导入会保留浏览量、发布时间、标签和评论父子结构，并记录 `/post-{id}.html` 等旧地址。

### 邮件提醒

在 `.env` 中配置：

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=smtp-account@example.com
EMAIL_HOST_PASSWORD=smtp-password
DEFAULT_FROM_EMAIL=noreply@example.com
NOTIFY_EMAIL=owner@example.com
COMMENT_REPLY_NOTIFY=true
```

默认控制台后端会把邮件输出到日志，便于本地验证。`NOTIFY_EMAIL` 接收新评论提醒；留空时发送给文章作者。回复通知发给被回复的访客邮箱。

### 切换主题

进入 Django Admin 的 **Theme settings**，把目标主题设为启用；同一时间只会有一个主题生效。默认主题由 `.env` 中的 `THEME=cactus_dark` 控制。

### 图片上传限制

上传接口仅允许登录后台用户调用，并使用 Pillow 校验图片内容，而不是只信任扩展名或 MIME。默认限制可在 `.env` 调整：

```dotenv
UPLOAD_MAX_MB=10
UPLOAD_MAX_IMAGES=20
IMAGE_MAX_DIMENSION=8000
```

当前支持 JPEG、PNG、WebP 和 GIF。

### 插件机制

每个插件放在 `plugins/<plugin-name>/`，必须包含：

- `plugin.json`：声明 `name`、`version` 和 `description`
- 可选 `plugin.py`：定义 `transform_markdown` 或 `transform_html` 钩子

在 Django Admin 的 **Plugin settings** 中启用插件。仓库内置 `Markdown Footnote` 示例，会把文章 HTML 中的 `[FOOTNOTE]` 替换为页脚说明。

### 内容浏览

公开页面包括：

- `/category/<slug>/`：按分类筛选已发布文章
- `/tag/<id>/`：按标签筛选已发布文章
- `/search/?q=关键词`：搜索标题、摘要、正文和标签

草稿始终不会出现在这些页面中。

列表分页默认每页 10 篇，可在 `.env` 中使用 `POSTS_PER_PAGE` 调整。

默认读取 `.env`；本地设置使用 `config.settings.local`。PostgreSQL 和 Redis 可通过 Docker 单独运行。

## Docker 部署

```bash
cp .env.example .env
chmod +x scripts/start.sh
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

生产环境必须修改 `SECRET_KEY`、`POSTGRES_PASSWORD`，并配置真实的 `ALLOWED_HOSTS`。对外启用 HTTPS 时设置 `SECURE_SSL_REDIRECT=true`。

## 当前范围

已实现博客核心链路。其他博客导入和插件依赖隔离仍属于后续阶段。
