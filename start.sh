#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/backend"
echo ">>> 初始化数据..."
python3 scripts/load_data.py
echo ">>> 启动服务..."
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
