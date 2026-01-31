#!/usr/bin/env bash
# ops-clawdbot-agent 自检脚本
# 用法：./scripts/doctor.sh 或 sudo ./scripts/doctor.sh
# 只检查，不改动

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/ops-clawdbot}"
CONFIG_FILE="${INSTALL_DIR}/.env"
SERVICE_NAME="ops-clawdbot-agent"
ENTRY_FILE="${INSTALL_DIR}/agent/runtime.py"
REQUIRED_KEYS="CONSOLE_BASE_URL NODE_ID PROJECT_KEY NODE_TOKEN HEARTBEAT_INTERVAL_SEC"

ok()  { echo "  [OK]   $*"; }
fail() { echo "  [FAIL] $*"; }
warn() { echo "  [WARN] $*"; }

mask_token() {
  local val="$1"
  if [[ -z "${val:-}" ]]; then echo "(未设置)"; return; fi
  if [[ ${#val} -ge 8 ]]; then echo "${val:0:4}****${val: -4}"; else echo "****"; fi
}

get_env() {
  local k="$1"
  [[ -r "$CONFIG_FILE" ]] && grep -E "^${k}=" "$CONFIG_FILE" 2>/dev/null | cut -d= -f2- || true
}

echo "=== ops-clawdbot-agent 自检 ==="
echo ""

# 1) 检查 systemd 服务是否存在
if [[ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
  ok "systemd 服务存在"
  if command -v systemctl &>/dev/null; then
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
      ok "服务运行中"
    else
      fail "服务未运行"
    fi
  fi
else
  fail "systemd 服务不存在: /etc/systemd/system/${SERVICE_NAME}.service"
fi

# 2) 检查安装目录
if [[ -d "$INSTALL_DIR" ]]; then
  ok "安装目录存在: $INSTALL_DIR"
else
  fail "安装目录不存在: $INSTALL_DIR"
  echo ""
  echo "自检终止（安装目录缺失）"
  exit 1
fi

# 3) 检查 .env 存在且字段齐全
if [[ -f "$CONFIG_FILE" ]]; then
  ok "配置文件存在: $CONFIG_FILE"
  missing=""
  for k in $REQUIRED_KEYS; do
    val=$(get_env "$k")
    if [[ -z "$val" ]]; then
      missing="$missing $k"
    fi
  done
  if [[ -n "$missing" ]]; then
    fail "缺少配置项:$missing"
  else
    ok "必需字段齐全"
  fi
else
  fail "配置文件不存在: $CONFIG_FILE"
fi

# 4) 检查 Python 入口文件
if [[ -f "$ENTRY_FILE" ]]; then
  ok "入口文件存在: agent/runtime.py"
else
  fail "入口文件不存在: $ENTRY_FILE"
fi

# 5) 检查网络连通性
if [[ -r "$CONFIG_FILE" ]] && command -v curl &>/dev/null; then
  url=$(get_env "CONSOLE_BASE_URL")
  url="${url%%#*}"
  url="${url%% *}"
  url="${url%/}"
  if [[ -n "$url" ]]; then
    if curl -sSf -I -o /dev/null --connect-timeout 5 "$url/health" 2>/dev/null; then
      ok "Console 可达: ${url}/health"
    else
      fail "Console 不可达: ${url}"
      echo "    建议：检查 CONSOLE_BASE_URL、网络、防火墙、Console 服务是否启动"
    fi
  else
    warn "CONSOLE_BASE_URL 未设置，跳过网络检查"
  fi
else
  warn "无法检查网络（.env 不可读或未安装 curl）"
fi

# 6) 输出当前节点信息（token 脱敏）
echo ""
echo "--- 当前节点信息 ---"
if [[ -r "$CONFIG_FILE" ]]; then
  node_id=$(get_env "NODE_ID")
  project_key=$(get_env "PROJECT_KEY")
  node_token=$(get_env "NODE_TOKEN")
  echo "  NODE_ID:      ${node_id:-(未设置)}"
  echo "  PROJECT_KEY:  ${project_key:-(未设置)}"
  echo "  NODE_TOKEN:   $(mask_token "$node_token")"
else
  echo "  (配置文件不可读)"
fi

echo ""
echo "自检完成"
echo ""
