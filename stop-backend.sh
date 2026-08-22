#!/bin/bash
# 停止本地后端和 Cloudflare Tunnel

DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$DIR/backend.pid" ]; then
  kill $(cat "$DIR/backend.pid") 2>/dev/null || true
  rm -f "$DIR/backend.pid"
fi
if [ -f "$DIR/tunnel.pid" ]; then
  kill $(cat "$DIR/tunnel.pid") 2>/dev/null || true
  rm -f "$DIR/tunnel.pid"
fi

pkill -f "node server.js" 2>/dev/null || true
pkill -f "cloudflared tunnel --url" 2>/dev/null || true

echo "后端和 Tunnel 已停止"
