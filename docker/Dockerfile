FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements /tmp/requirements
RUN pip install --upgrade pip && pip install -r /tmp/requirements/base.txt

COPY . .

RUN addgroup --system talkbox && adduser --system --ingroup talkbox talkbox \
 && mkdir -p /app/media /app/staticfiles \
 && chown -R talkbox:talkbox /app/media /app/staticfiles
USER talkbox

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD curl -fsS http://127.0.0.1:8000/healthz/ || exit 1

ENTRYPOINT ["./scripts/start.sh"]
