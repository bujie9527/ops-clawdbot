#!/usr/bin/env bash
# 烟雾测试：调用 Console 的 register 与 heartbeat，验证配置与连通性
# 仅用 curl，不依赖 jq，兼容 Ubuntu 默认环境

set -e

ENV_FILE="${ENV_FILE:-/opt/ops-clawdbot/.env}"

_parse_env() {
  local key="$1"
  (grep -E "^${key}=" "$ENV_FILE" 2>/dev/null || true) | cut -d= -f2- | sed "s/^['\"]//;s/['\"]$//"
}

_fail() {
  echo "[FAIL] $*"
  exit 1
}

_suggest() {
  local code="$1"
  case "$code" in
    000) echo "建议: 无法连接 Console，请检查 CONSOLE_BASE_URL、网络、防火墙，确认 Console 已启动" ;;
    401) echo "建议: Token 无效或未配置，请检查 NODE_TOKEN 与 Console 的 NODE_TOKEN_PROJECT_A 是否一致" ;;
    403) echo "建议: project_key 不匹配或权限不足" ;;
    404) echo "建议: 节点未注册（register 后再 heartbeat）或 node_id 错误" ;;
    500) echo "建议: 服务器内部错误，请查看 Console 日志" ;;
    *)   echo "建议: 请检查请求参数与 Console 配置" ;;
  esac
}

# 检查 .env
if [[ ! -f "$ENV_FILE" ]]; then
  _fail "配置文件不存在: $ENV_FILE"
fi

CONSOLE_BASE_URL=$(_parse_env CONSOLE_BASE_URL)
NODE_ID=$(_parse_env NODE_ID)
PROJECT_KEY=$(_parse_env PROJECT_KEY)
NODE_TOKEN=$(_parse_env NODE_TOKEN)
NODE_NAME=$(_parse_env NODE_NAME)
[[ -z "$NODE_NAME" ]] && NODE_NAME="$NODE_ID"

for v in CONSOLE_BASE_URL NODE_ID PROJECT_KEY NODE_TOKEN; do
  eval "val=\$$v"
  if [[ -z "$val" ]]; then
    _fail "缺少配置: $v"
  fi
done

# 去除 URL 末尾斜杠
CONSOLE_BASE_URL="${CONSOLE_BASE_URL%/}"

echo "=== Smoke Test: Register & Heartbeat ==="
echo "Console: $CONSOLE_BASE_URL | Node: $NODE_ID"
echo ""

# 1) Register
REG_URL="${CONSOLE_BASE_URL}/api/nodes/register"
REG_BODY="{\"node_id\":\"${NODE_ID}\",\"project_key\":\"${PROJECT_KEY}\",\"name\":\"${NODE_NAME}\",\"tags\":[],\"version\":\"0.1.0\"}"

resp=$(curl -s -w "\n%{http_code}" -X POST "$REG_URL" \
  -H "Authorization: Bearer ${NODE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$REG_BODY")

reg_body=$(echo "$resp" | head -n -1)
reg_status=$(echo "$resp" | tail -n 1)

echo "1) POST /api/nodes/register"
echo "   HTTP $reg_status"
echo "   Response: $reg_body"
if [[ "$reg_status" != "200" ]]; then
  _suggest "$reg_status"
  exit 1
fi
echo ""

# 2) Heartbeat
HB_URL="${CONSOLE_BASE_URL}/api/nodes/${NODE_ID}/heartbeat"
HB_BODY='{"status":"online"}'

resp=$(curl -s -w "\n%{http_code}" -X POST "$HB_URL" \
  -H "Authorization: Bearer ${NODE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$HB_BODY")

hb_body=$(echo "$resp" | head -n -1)
hb_status=$(echo "$resp" | tail -n 1)

echo "2) POST /api/nodes/${NODE_ID}/heartbeat"
echo "   HTTP $hb_status"
echo "   Response: $hb_body"
if [[ "$hb_status" != "200" ]]; then
  _suggest "$hb_status"
  exit 1
fi
echo ""

echo "[OK] Smoke test passed."
