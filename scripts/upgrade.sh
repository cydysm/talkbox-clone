#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE="${COMPOSE:-docker compose}"
HEALTH_TIMEOUT="${UPGRADE_HEALTH_TIMEOUT:-120}"
DRY_RUN="${UPGRADE_DRY_RUN:-0}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
LOCK="/tmp/talkbox-upgrade.lock"
LOG_DIR="${UPGRADE_LOG_DIR:-./logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/upgrade_${STAMP}.log"
PREVIOUS_IMAGE=""

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

cleanup() {
  rm -f "$LOCK"
}
trap cleanup EXIT
trap 'rollback; exit 1' INT TERM ERR

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || { log "缺少命令：$1"; exit 2; }
}

current_web_image() {
  $COMPOSE ps -q web >/dev/null 2>&1 || return 0
  docker inspect "$($COMPOSE ps -q web)" --format '{{ index .Config.Labels "com.docker.compose.image" }}' 2>/dev/null || true
}

health_ok() {
  local deadline=$((SECONDS + HEALTH_TIMEOUT))
  while (( SECONDS < deadline )); do
    if curl -fsS "http://127.0.0.1:${HTTP_PORT:-8000}/healthz/" | grep -q '"status":"ok"'; then
      return 0
    fi
    sleep 5
  done
  return 1
}

rollback() {
  if [[ -n "$PREVIOUS_IMAGE" ]]; then
    log "升级失败，尝试回滚到上一版本：$PREVIOUS_IMAGE。"
    $COMPOSE stop web || true
    $COMPOSE up -d --no-deps --force-recreate web || true
    if health_ok; then
      log "回滚完成，服务健康。"
    else
      log "回滚后健康检查仍失败，请立即检查数据库和日志。"
    fi
  else
    log "没有可识别的上一镜像，请检查 Compose 状态和日志。"
  fi
  log "日志：$LOG_FILE"
}

main() {
  if [[ "$DRY_RUN" == "1" ]]; then
    bash -n "$0"
    log "Shell 语法检查通过（dry-run）。"
    return 0
  fi

  require_command docker
  require_command curl
  require_command git
  [[ -f ".env" ]] || { log "缺少 .env 配置文件"; exit 2; }

  mkdir -p /tmp
  if ! mkdir "$LOCK" 2>/dev/null; then
    log "已有升级流程在运行：$LOCK"
    exit 3
  fi

  log "开始 Talkbox 自动升级（保留当前镜像用于失败回滚）。"
  PREVIOUS_IMAGE="$(current_web_image)"

  log "拉取基础镜像与最新代码。"
  $COMPOSE pull db redis
  git pull --ff-only --autostash

  log "执行数据库备份。"
  BACKUP_DIR="${BACKUP_DIR:-/app/backups}" "$PWD/scripts/backup.sh"

  log "构建新 Web 镜像。"
  $COMPOSE build web

  log "启动新版本并等待健康检查。"
  $COMPOSE up -d --no-deps --force-recreate web
  if health_ok; then
    find "${BACKUP_DIR:-/app/backups}" -name "*.gz" -mtime "+$BACKUP_RETENTION_DAYS" -delete 2>/dev/null || true
    docker image prune -f >/dev/null
    log "升级完成，服务健康。"
    return 0
  fi

  log "新版本健康检查超时。"
  rollback
  return 1
}

main "$@"
