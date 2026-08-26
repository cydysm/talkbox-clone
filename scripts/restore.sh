#!/usr/bin/env bash
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose}"
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"

if [[ $# -lt 1 ]]; then
    echo "用法: ./scripts/restore.sh <备份文件前缀>"
    echo ""
    echo "示例: 如果备份文件是 talkbox_20260826_030000.sql.gz 和 media_20260826_030000.tar.gz"
    echo "则运行: ./scripts/restore.sh 20260826_030000"
    echo ""
    echo "可用备份："
    ls "$BACKUP_DIR"/talkbox_*.sql.gz 2>/dev/null | sed 's/.*talkbox_/  /;s/\.sql\.gz//' || echo "  (无)"
    exit 1
fi

STAMP="$1"
SQL_FILE="$BACKUP_DIR/talkbox_${STAMP}.sql.gz"
MEDIA_FILE="$BACKUP_DIR/media_${STAMP}.tar.gz"

[[ -f "$SQL_FILE" ]] || { echo "错误: 找不到 $SQL_FILE"; exit 1; }

echo "⚠️  此操作会覆盖当前数据库和媒体文件！"
read -r -p "确认恢复到时间点 $STAMP ? (输入 yes 继续): " confirm
[[ "$confirm" == "yes" ]] || { echo "已取消。"; exit 0; }

echo "[1/4] 停止 Web 服务..."
$COMPOSE stop web

echo "[2/4] 恢复 PostgreSQL 数据库..."
$COMPOSE exec -T db psql -U "${POSTGRES_USER:-talkbox}" -d "${POSTGRES_DB:-talkbox}" <<'EOSQL'
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO talkbox;
GRANT ALL ON SCHEMA public TO public;
EOSQL
gunzip -c "$SQL_FILE" | $COMPOSE exec -T db psql -U "${POSTGRES_USER:-talkbox}" -d "${POSTGRES_DB:-talkbox}"

echo "[3/4] 恢复媒体文件..."
if [[ -f "$MEDIA_FILE" ]]; then
    docker compose cp "$MEDIA_FILE" web:/tmp/media_restore.tar.gz 2>/dev/null \
        || tar -xzf "$MEDIA_FILE" -C /tmp/
    $COMPOSE exec -T web sh -c 'rm -rf /app/media/* && tar -xzf /tmp/media_restore.tar.gz -C / && rm /tmp/media_restore.tar.gz' 2>/dev/null \
        || true
else
    echo "  未找到媒体备份，跳过（$MEDIA_FILE）"
fi

echo "[4/4] 重启 Web 服务..."
$COMPOSE start web

# 等待健康检查通过
sleep 5
for i in $(seq 1 12); do
    if curl -fsS "http://127.0.0.1:${HTTP_PORT:-8000}/healthz/" 2>/dev/null | grep -q '"status":"ok"'; then
        echo ""
        echo "✅ 恢复完成，服务健康！"
        exit 0
    fi
    sleep 5
done

echo ""
echo "❌ 服务未在 60 秒内恢复健康，请检查日志: $COMPOSE logs -f web"
exit 1
