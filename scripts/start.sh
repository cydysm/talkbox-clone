#!/bin/sh
set -eu

# 作为镜像 ENTRYPOINT 时支持一次性命令：`docker compose run web python manage.py ...`
# 直接 exec 参数而不做启动流程；仅当无参数时才走 migrate + gunicorn。
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

python manage.py migrate --noinput
python scripts/check_plugin_dependencies.py
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application --config docker/gunicorn.py
