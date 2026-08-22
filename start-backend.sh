#!/bin/bash
# 启动本地后端 + Cloudflare Tunnel，把后端暴露到公网
# 用法：./start-backend.sh [API_KEY]

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
API_KEY="${1:-dwxh_backend_key_2026}"
BACKEND_PORT="${BACKEND_PORT:-3000}"

# 确保工具在 PATH
export PATH="$DIR/.tools/node/bin:$DIR/.tools/vercel/bin:$PATH"
if ! command -v node >/dev/null 2>&1; then
  echo "[错误] 找不到 node，请确认 .tools/node 已存在或已安装 Node.js"
  exit 1
fi
if ! command -v cloudflared >/dev/null 2>&1; then
  CLOUDFLARED_BIN="$DIR/.tools/node/bin/cloudflared"
  if [ -x "$CLOUDFLARED_BIN" ]; then
    export PATH="$DIR/.tools/node/bin:$PATH"
  else
    echo "[错误] 找不到 cloudflared，请先安装："
    echo "  mkdir -p $DIR/.tools/node/bin"
    echo "  curl -Lo /tmp/cloudflared-darwin-arm64.tgz https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
    echo "  tar -xzf /tmp/cloudflared-darwin-arm64.tgz -C /tmp && cp /tmp/cloudflared $CLOUDFLARED_BIN && chmod +x $CLOUDFLARED_BIN"
    exit 1
  fi
fi

# 清理旧进程
pkill -f "node server.js" 2>/dev/null || true
sleep 1

echo "[1/4] 启动后端（端口 $BACKEND_PORT）..."
API_KEY="$API_KEY" node "$DIR/server.js" > "$DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$DIR/backend.pid"
sleep 3

# 检查后端是否启动
if ! curl -s "http://localhost:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
  echo "[错误] 后端启动失败，请查看 backend.log"
  exit 1
fi
echo "[2/4] 后端已启动，PID: $BACKEND_PID"

echo "[3/4] 启动 Cloudflare Tunnel..."
cloudflared tunnel --url "http://localhost:$BACKEND_PORT" > "$DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!
echo $TUNNEL_PID > "$DIR/tunnel.pid"

# 等待并提取公网 URL
for i in {1..30}; do
  TUNNEL_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$DIR/tunnel.log" | head -n 1)
  if [ -n "$TUNNEL_URL" ]; then
    break
  fi
  sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
  echo "[错误] 获取 Tunnel URL 失败，请查看 tunnel.log"
  exit 1
fi

echo "[4/4] 公网访问地址：$TUNNEL_URL"
echo ""
echo "========================================"
echo "后端已可通过公网访问："
echo "  $TUNNEL_URL"
echo ""
echo "API Key: $API_KEY"
echo ""
echo "请把这个地址填到："
echo "  1. 网页「备份/设置」→「后端同步设置」→「后端地址」"
echo "  2. crawler/config.json 的 backend.url"
echo "========================================"

# 可选：自动更新 crawler/config.json
read -p "是否自动更新 crawler/config.json 的 backend.url？ (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  python3 - <<PY
import json
with open('$DIR/crawler/config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
cfg['backend'] = cfg.get('backend', {})
cfg['backend']['url'] = '$TUNNEL_URL'
cfg['backend']['api_key'] = '$API_KEY'
cfg['backend']['auto_sync'] = True
with open('$DIR/crawler/config.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
print('已更新 crawler/config.json')
PY
fi

echo ""
echo "保持此终端运行。按 Ctrl+C 停止后端和 Tunnel。"
wait $BACKEND_PID
