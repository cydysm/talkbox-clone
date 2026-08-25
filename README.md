# Talkbox Clone

一个基于 Python 3、Django、PostgreSQL、Redis、Docker、Gunicorn 和 Gevent 的轻量博客系统。当前版本提供可运行的 MVP 骨架，后续可继续扩展 Emlog 导入、插件系统和更多主题。

## 功能

- Django Admin 管理文章与分类
- Markdown 文章渲染和 Redis 渲染缓存
- 多标签（django-taggit）
- 树形评论模型和评论审核状态
- 图片上传与缩略图生成
- Cactus Dark 主题模板
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

已实现博客核心链路。Emlog 数据迁移、老链接兼容、邮件通知、水印、多模板切换、其他博客导入和完整插件机制仍属于后续阶段，需要按旧站数据结构逐步实现。
