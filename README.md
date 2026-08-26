# Talkbox Clone

一个基于 Python 3、Django、PostgreSQL、Redis、Docker、Gunicorn 和 Gevent 的轻量博客系统。当前版本提供可运行的 MVP 骨架，后续可继续扩展其他博客导入、插件系统和更多主题。

## 功能

- Django Admin 管理文章与分类
- Markdown 文章渲染和 Redis 渲染缓存
- 多标签（django-taggit）
- 树形评论模型和评论审核状态
- 评论与回复邮件提醒
- 图片上传与缩略图生成
- 后台轻量 Markdown 工具栏，支持多图上传并一键批量插入 Markdown
- 图片上传安全校验：真实格式、大小、数量和尺寸限制
- 轻量插件机制与 Markdown/HTML 内容钩子
- 后台评论审核、媒体库管理和文章批量发布/草稿操作
- 作者与后台用户可预览草稿，访客不可访问
- 评论蜜罐防护和 IP 提交间隔限制
- `/healthz/` 应用、数据库和缓存健康检查
- Cactus Dark 主题模板
- 分类页、标签页和站内搜索
- 文章列表统一分页，每页数量可配置
- RSS 与 Atom 订阅源
- 后台多模板切换，当前支持 Cactus Dark 和 Cactus Light
- Emlog JSON/SQLite 导入：文章、分类、标签和评论树
- 其他博客 `talkbox-generic` v1 JSON 导入：文章、分类、标签和评论树
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
UPLOAD_TOTAL_LIMIT_GB=20
IMAGE_MAX_DIMENSION=8000
THUMBNAIL_SIZE=240,240
```

当前支持 JPEG、PNG、WebP 和 GIF。

缩略图自动输出为 WebP，默认 240×240。媒体总容量默认上限 20GB，超限时返回 HTTP 507。

### 备份与恢复

```bash
# 手动执行
./scripts/backup.sh

# cron 定时（每天凌晨3点）
0 3 * * * /app/scripts/backup.sh >> /app/logs/backup.log 2>&1
```

备份文件保留最近 7 天，可通过 `BACKUP_RETENTION_DAYS` 调整。

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

### 订阅源

- `/rss.xml`：RSS 2.0
- `/atom.xml`：Atom 1.0

订阅源只输出已发布文章，默认最多 20 篇；可通过 `.env` 的 `FEED_LIMIT` 调整。

### 评论防刷

评论表单包含对普通用户隐藏的蜜罐字段。同一 IP 默认每 `COMMENT_INTERVAL_SECONDS=30` 秒只能提交一次，可在 `.env` 调整。

### 健康检查

Docker 与负载均衡可探测 `GET /healthz/`。该接口会检查数据库连接和缓存读写，任一失败返回 HTTP 503。

默认读取 `.env`；本地设置使用 `config.settings.local`。PostgreSQL 和 Redis 可通过 Docker 单独运行。

## Docker 部署

```bash
cp .env.example .env
chmod +x scripts/start.sh
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

生产环境必须修改 `SECRET_KEY`、`POSTGRES_PASSWORD`，并配置真实的 `ALLOWED_HOSTS`。启动时会强制校验密钥强度和主机白名单，拒绝默认密钥、弱密钥、空主机列表和通配符配置。对外启用 HTTPS 时设置 `SECURE_SSL_REDIRECT=true`。

### 低配服务器调优（1C2G / 1M 带宽）

默认配置已针对小服务器优化：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `GUNICORN_WORKERS` | 2 | gevent 协程模型，2 进程足够 |
| `GUNICORN_WORKER_CONNECTIONS` | 200 | 每进程并发连接数 |
| `GUNICORN_MAX_REQUESTS` | 2000 | 自动重启 worker 防内存泄漏 |
| `GUNICORN_ACCESS_LOG` | 空=关闭 | 关闭 access log 减少磁盘 I/O |
| `CONN_MAX_AGE` | 60 | 数据库持久连接，减少握手开销 |
| `POSTS_PER_PAGE` | 10 | 列表分页大小 |
| `FEED_LIMIT` | 20 | RSS/Atom 输出条目数 |

## 当前范围

已实现博客核心链路。其他博客导入和插件依赖隔离仍属于后续阶段。
