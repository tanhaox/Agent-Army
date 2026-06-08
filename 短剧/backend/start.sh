#!/bin/bash
# 后端启动脚本 - 执行数据库迁移后启动应用。

set -e

echo "=== 短剧AI 后端启动 ==="

echo "[1/2] 执行数据库迁移..."
alembic upgrade head 2>&1 || echo "  警告：迁移执行失败（可能已是最新或数据库未就绪）"

echo "[2/2] 启动 FastAPI 应用..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
