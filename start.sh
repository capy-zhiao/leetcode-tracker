#!/usr/bin/env bash
# 一键启动刷题追踪器(前端 + 后端)。
# 用法:  ./start.sh          启动并打开浏览器
#        Ctrl+C              停止两个服务
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
API_PORT=8000
WEB_PORT=5173
LOG_DIR="$ROOT/.logs"
mkdir -p "$LOG_DIR"

green() { printf "\033[32m%s\033[0m\n" "$1"; }
yellow(){ printf "\033[33m%s\033[0m\n" "$1"; }
red()   { printf "\033[31m%s\033[0m\n" "$1"; }

port_busy() { lsof -ti :"$1" >/dev/null 2>&1; }

cleanup() {
  echo
  yellow "正在停止服务…"
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null
  [[ -n "${WEB_PID:-}" ]] && kill "$WEB_PID" 2>/dev/null
  wait 2>/dev/null
  green "已停止。下次再跑 ./start.sh 就行 👋"
}
trap cleanup EXIT INT TERM

echo "🧠 刷题追踪器"
echo "─────────────────────────────"

# ---------- 依赖检查(第一次跑或换了电脑时自动装) ----------
if [[ ! -x "$BACKEND/.venv/bin/uvicorn" ]]; then
  yellow "首次运行:正在创建 Python 虚拟环境并安装依赖…"
  python3 -m venv "$BACKEND/.venv" || { red "创建 venv 失败,检查 python3"; exit 1; }
  "$BACKEND/.venv/bin/pip" install -q --upgrade pip
  "$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt" || { red "装依赖失败"; exit 1; }
fi

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  yellow "首次运行:正在安装前端依赖(可能要一两分钟)…"
  (cd "$FRONTEND" && npm install --silent) || { red "npm install 失败"; exit 1; }
fi

if [[ ! -f "$BACKEND/tracker.db" ]]; then
  yellow "数据库不存在,正在导入 250 道题…"
  (cd "$BACKEND" && ./.venv/bin/python seed_db.py)
fi

# ---------- 启动后端 ----------
if port_busy "$API_PORT"; then
  if curl -fsS "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
    green "✅ 后端已在运行($API_PORT)"
  else
    red "❌ 端口 $API_PORT 被别的程序占用了,先关掉它再试"
    red "   查看占用:lsof -i :$API_PORT"
    exit 1
  fi
else
  (cd "$BACKEND" && ./.venv/bin/uvicorn app.main:app --port "$API_PORT" --reload) \
    > "$LOG_DIR/backend.log" 2>&1 &
  API_PID=$!
  printf "启动后端"
  for _ in {1..30}; do
    curl -fsS "http://localhost:$API_PORT/health" >/dev/null 2>&1 && break
    printf "."; sleep 0.5
  done
  echo
  if curl -fsS "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
    green "✅ 后端就绪  http://localhost:$API_PORT/docs"
  else
    red "❌ 后端起不来,看日志:$LOG_DIR/backend.log"; tail -20 "$LOG_DIR/backend.log"; exit 1
  fi
fi

# ---------- 启动前端 ----------
if port_busy "$WEB_PORT"; then
  green "✅ 前端已在运行($WEB_PORT)"
else
  (cd "$FRONTEND" && npm run dev) > "$LOG_DIR/frontend.log" 2>&1 &
  WEB_PID=$!
  printf "启动前端"
  for _ in {1..40}; do
    curl -fsS -o /dev/null "http://localhost:$WEB_PORT/" 2>/dev/null && break
    printf "."; sleep 0.5
  done
  echo
  if curl -fsS -o /dev/null "http://localhost:$WEB_PORT/" 2>/dev/null; then
    green "✅ 前端就绪  http://localhost:$WEB_PORT"
  else
    red "❌ 前端起不来,看日志:$LOG_DIR/frontend.log"; tail -20 "$LOG_DIR/frontend.log"; exit 1
  fi
fi

# ---------- 打开浏览器 + 今日任务预览 ----------
echo "─────────────────────────────"
curl -fsS "http://localhost:$API_PORT/review/today" 2>/dev/null | python3 -c "
import json, sys
try:
    q = json.load(sys.stdin)
except Exception:
    sys.exit()
print(f\"📅 {q['date']}   今日到期 {q['total_due']} 道\" + (f\"(顺延 {q['deferred']} 道)\" if q['deferred'] else ''))
for name, key in [('🔁 复习', 'reviews'), ('🆕 新题', 'new_problems'), ('🔧 模板', 'templates')]:
    items = q[key]
    if items:
        print(f'  {name}: ' + ' · '.join(f\"{i['problem']['number']} {i['problem']['title']}\" for i in items))
" 2>/dev/null

sleep 1
command -v open >/dev/null && open "http://localhost:$WEB_PORT"

echo "─────────────────────────────"
green "🚀 开刷!  http://localhost:$WEB_PORT"
echo "   (这个终端窗口别关,按 Ctrl+C 停止服务)"
echo

wait
