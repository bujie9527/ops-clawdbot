#!/usr/bin/env bash
# ops-node-agent 一键安装脚本
# 用法：curl -sSL https://raw.githubusercontent.com/bujie9527/ops-clawdbot/master/ops-node-agent/install.sh | sudo bash
#   或：cd /path/to/ops-clawdbot/ops-node-agent && sudo ./install.sh

set -e

INSTALL_DIR="/opt/ops-node-agent"
REPO_URL="https://github.com/bujie9527/ops-clawdbot.git"
SYSTEMD_USER="ops-agent"

echo "=== ops-node-agent 一键安装 ==="

# 1. 检查 root 或 sudo
if [[ $EUID -ne 0 ]]; then
  echo "请使用 root 或 sudo 运行此脚本"
  exit 1
fi

# 2. 检查 Python 3.11+
if ! command -v python3 &>/dev/null; then
  echo "错误: 未找到 python3，请先安装 Python 3.11+"
  exit 1
fi
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
  echo "错误: 需要 Python 3.11 或更高版本，当前: $(python3 --version)"
  exit 1
fi

# 3. 检查 git
if ! command -v git &>/dev/null; then
  echo "错误: 未找到 git，请先安装 git"
  exit 1
fi

# 4. 确定源码目录
SOURCE_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" != "bash" ]]; then
  MAYBE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
  if [[ -f "${MAYBE}/agent/runtime.py" && -f "${MAYBE}/requirements.txt" ]]; then
    SOURCE_DIR="$MAYBE"
  fi
fi

if [[ -z "$SOURCE_DIR" ]]; then
  echo "正在从 GitHub 克隆仓库..."
  rm -rf /tmp/ops-clawdbot-install
  git clone --depth 1 "$REPO_URL" /tmp/ops-clawdbot-install
  if [[ ! -d /tmp/ops-clawdbot-install/ops-node-agent ]]; then
    echo "错误: 仓库中未找到 ops-node-agent 目录"
    exit 1
  fi
  SOURCE_DIR="/tmp/ops-clawdbot-install/ops-node-agent"
fi

# 5. 复制到安装目录
CURRENT_INSTALL=""
if [[ -d "$INSTALL_DIR" && -f "$INSTALL_DIR/agent/runtime.py" ]]; then
  RESOLVED_SRC="$(cd "$SOURCE_DIR" && pwd)"
  RESOLVED_INSTALL="$(cd "$INSTALL_DIR" 2>/dev/null && pwd)"
  if [[ "$RESOLVED_SRC" == "$RESOLVED_INSTALL" ]]; then
    CURRENT_INSTALL="yes"
  fi
fi

if [[ -z "$CURRENT_INSTALL" ]]; then
  echo "正在安装到 $INSTALL_DIR ..."
  mkdir -p "$INSTALL_DIR"
  if command -v rsync &>/dev/null; then
    rsync -a --exclude='.venv' --exclude='.git' "$SOURCE_DIR/" "$INSTALL_DIR/"
  else
    cp -r "$SOURCE_DIR"/* "$INSTALL_DIR/"
    [[ -f "$SOURCE_DIR/.env.example" ]] && cp "$SOURCE_DIR/.env.example" "$INSTALL_DIR/"
  fi
  [[ -d /tmp/ops-clawdbot-install ]] && rm -rf /tmp/ops-clawdbot-install
fi

cd "$INSTALL_DIR"

# 6. 虚拟环境与依赖
echo "正在创建虚拟环境并安装依赖..."
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

# 7. 配置文件
if [[ ! -f .env ]]; then
  echo ""
  echo "=== 配置配对（与 Clawdbot Console 连接）==="
  cp .env.example .env

  read -rp "Console API 地址 (如 https://console.example.com): " CONSOLE_URL
  CONSOLE_URL="${CONSOLE_URL:-http://127.0.0.1:8000}"
  read -rp "节点 ID (唯一，如 node-1): " NODE_ID
  NODE_ID="${NODE_ID:-node-1}"
  read -rp "节点 Token (与 Console 的 NODE_TOKEN_PROJECT_A 一致): " NODE_TOKEN
  NODE_TOKEN="${NODE_TOKEN:-changeme_node_token_project_a}"
  read -rp "节点名称 (可选，默认 Node): " NODE_NAME
  NODE_NAME="${NODE_NAME:-Node}"

  CONSOLE_URL="${CONSOLE_URL%/}"
  cat > .env << EOF
# ops-node-agent 配置 (install.sh 生成)
NODE_ID=$NODE_ID
PROJECT_KEY=project_a
NODE_NAME=$NODE_NAME
CONSOLE_BASE_URL=$CONSOLE_URL
NODE_TOKEN=$NODE_TOKEN
HEARTBEAT_INTERVAL_SEC=10
TASK_POLL_INTERVAL_SEC=5
EOF

  echo "已写入 .env"
else
  echo "已存在 .env，跳过配置"
fi

# 8. 创建运行用户
if ! id "$SYSTEMD_USER" &>/dev/null; then
  echo "正在创建系统用户 $SYSTEMD_USER ..."
  useradd -r -s /bin/false "$SYSTEMD_USER"
fi
chown -R "$SYSTEMD_USER:$SYSTEMD_USER" "$INSTALL_DIR"

# 9. systemd 服务
echo "正在安装 systemd 服务..."
cp systemd/ops-node-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ops-node-agent
systemctl restart ops-node-agent

echo ""
echo "=== 安装完成 ==="
echo "服务状态: sudo systemctl status ops-node-agent"
echo "查看日志: sudo journalctl -u ops-node-agent -f"
echo "请在 Clawdbot Console Web 面板查看节点是否在线"
