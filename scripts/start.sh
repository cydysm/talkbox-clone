#!/bin/sh
set -eu

python manage.py migrate --noinput
python scripts/check_plugin_dependencies.py
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application --config docker/gunicorn.py
