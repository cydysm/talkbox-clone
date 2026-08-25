# Talkbox Clone

一个基于 Python 3、Django、PostgreSQL、Redis、Docker、Gunicorn 和 Gevent 的轻量博客系统。当前版本提供可运行的 MVP 骨架，后续可继续扩展其他博客导入、插件系统和更多主题。

## 功能

- Django Admin 管理文章与分类
- Markdown 文章渲染和 Redis 渲染缓存
- 多标签（django-taggit）
- 树形评论模型和评论审核状态
- 评论与回复邮件提醒
- 图片上传与缩略图生成
- Cactus Dark 主题模板
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

已实现博客核心链路。多模板切换、其他博客导入和完整插件机制仍属于后续阶段。
