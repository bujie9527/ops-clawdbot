#!/usr/bin/env bash
# ops-clawdbot-agent 一键安装脚本（幂等）
# 用法：
#   交互式：sudo ./scripts/install.sh
#   非交互：CONSOLE_BASE_URL=... NODE_ID=... NODE_TOKEN=... sudo -E ./scripts/install.sh
# 环境变量：GIT_REPO BRANCH INSTALL_DIR SERVICE_USER CONSOLE_BASE_URL NODE_ID PROJECT_KEY NODE_TOKEN HEARTBEAT_INTERVAL_SEC

set -euo pipefail

# --- 可配置变量（环境变量覆盖）---
GIT_REPO="${GIT_REPO:-https://github.com/bujie9527/ops-clawdbot.git}"
BRANCH="${BRANCH:-master}"
INSTALL_DIR="${INSTALL_DIR:-/opt/ops-clawdbot}"
SERVICE_USER="${SERVICE_USER:-opsnode}"
SERVICE_NAME="ops-clawdbot-agent"
GIT_SUBPATH="${GIT_SUBPATH:-ops-node-agent}"

CONFIG_FILE="${INSTALL_DIR}/.env"
REQUIRED_ENV_KEYS="CONSOLE_BASE_URL NODE_ID PROJECT_KEY NODE_TOKEN HEARTBEAT_INTERVAL_SEC"
HEARTBEAT_INTERVAL_SEC="${HEARTBEAT_INTERVAL_SEC:-10}"

log() { echo "[install] $*"; }

mask_token() {
  local val="$1"
  if [[ -z "${val:-}" ]]; then echo "(未设置)"; return; fi
  if [[ ${#val} -ge 8 ]]; then echo "${val:0:4}****${val: -4}"; else echo "****"; fi
}

# 1) 检查 root
check_root() {
  if [[ $EUID -ne 0 ]]; then
    log "请使用 sudo 运行此脚本"
    exit 1
  fi
}

# 2) 检查依赖，缺则 apt 安装
check_deps() {
  local need_install=""
  for cmd in git python3 systemctl; do
    if ! command -v "$cmd" &>/dev/null; then
      need_install="1"
      break
    fi
  done
  if ! python3 -c "import venv" 2>/dev/null; then
    need_install="1"
  fi

  if [[ -n "$need_install" ]] && [[ -f /etc/debian_version ]] && command -v apt-get &>/dev/null; then
    local py_ver
    py_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "3")
    local pkgs="python3-venv python3-pip git"
    if [[ "$py_ver" =~ ^3\.[0-9]+$ ]] && apt-cache show "python${py_ver}-venv" &>/dev/null; then
      pkgs="python${py_ver}-venv python3-pip git"
    fi
    log "安装依赖: $pkgs"
    apt-get update -qq && apt-get install -y -qq $pkgs
  fi

  for cmd in git python3 systemctl; do
    if ! command -v "$cmd" &>/dev/null; then
      log "缺少命令: $cmd，请先安装"
      exit 1
    fi
  done
  if ! python3 -c "import venv" 2>/dev/null; then
    log "缺少 python3-venv，请先安装: sudo apt install python3-venv python3-pip"
    exit 1
  fi
  log "依赖检查通过"
}

# 3) 创建/确认服务用户
ensure_user() {
  if id "$SERVICE_USER" &>/dev/null; then
    log "用户 $SERVICE_USER 已存在"
  else
    log "创建用户: $SERVICE_USER"
    useradd -r -s /usr/sbin/nologin "$SERVICE_USER"
  fi
}

# 4) 克隆或更新代码
clone_or_update() {
  local tmp_clone="/tmp/ops-clawdbot-install-$$"
  rm -rf "$tmp_clone"
  log "克隆仓库: $GIT_REPO (分支: $BRANCH)"
  git clone --depth 1 --branch "$BRANCH" "$GIT_REPO" "$tmp_clone"

  local src_dir="$tmp_clone"
  if [[ -n "${GIT_SUBPATH:-}" ]] && [[ -d "$tmp_clone/$GIT_SUBPATH" ]]; then
    log "使用子路径: $GIT_SUBPATH"
    src_dir="$tmp_clone/$GIT_SUBPATH"
  fi

  if [[ ! -f "$src_dir/requirements.txt" ]]; then
    log "错误: 未找到 requirements.txt"
    rm -rf "$tmp_clone"
    exit 1
  fi

  mkdir -p "$INSTALL_DIR"
  if [[ -f "$CONFIG_FILE" ]]; then
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak.$$"
  fi
  if command -v rsync &>/dev/null; then
    rsync -a --exclude='.venv' --exclude='.env' --exclude='.git' "$src_dir/" "$INSTALL_DIR/"
  else
    (cd "$src_dir" && tar cf - --exclude='.venv' --exclude='.env' --exclude='.git' .) | (cd "$INSTALL_DIR" && tar xf -)
  fi
  if [[ -f "${CONFIG_FILE}.bak.$$" ]]; then
    mv "${CONFIG_FILE}.bak.$$" "$CONFIG_FILE"
  fi
  rm -rf "$tmp_clone"
  log "代码已更新到 $INSTALL_DIR"
}

# 5) 创建 venv
# 6) pip install requirements.txt
# 校验主入口 agent/runtime.py 存在
setup_venv() {
  cd "$INSTALL_DIR"
  if [[ ! -f requirements.txt ]]; then
    log "错误: requirements.txt 不存在"
    exit 1
  fi
  if [[ ! -f agent/runtime.py ]]; then
    log "错误: 主入口 agent/runtime.py 不存在"
    exit 1
  fi
  if [[ ! -f .venv/bin/pip ]]; then
    [[ -d .venv ]] && rm -rf .venv
    log "创建虚拟环境"
    python3 -m venv .venv
  fi
  log "安装依赖"
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
}

# 7) 生成/更新 .env
write_env() {
  cd "$INSTALL_DIR"
  if [[ ! -f "$CONFIG_FILE" ]]; then
    [[ -f .env.example ]] && cp .env.example "$CONFIG_FILE" || touch "$CONFIG_FILE"
  fi

  # 从 .env 读取现有值
  get_env() {
    local k="$1"
    grep -E "^${k}=" "$CONFIG_FILE" 2>/dev/null | cut -d= -f2- || true
  }
  set_env() {
    local k="$1" v="$2"
    [[ -z "${v:-}" ]] && return
    grep -v "^${k}=" "$CONFIG_FILE" 2>/dev/null > "${CONFIG_FILE}.tmp" || true
    printf '%s=%s\n' "$k" "$v" >> "${CONFIG_FILE}.tmp"
    mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
  }

  local needs_input=false
  for k in CONSOLE_BASE_URL NODE_ID PROJECT_KEY NODE_TOKEN HEARTBEAT_INTERVAL_SEC; do
    local env_val="${!k:-}"
    local file_val=""
    [[ -r "$CONFIG_FILE" ]] && file_val=$(get_env "$k")
    local val="${env_val:-$file_val}"
    if [[ -z "$val" ]]; then
      needs_input=true
      break
    fi
  done

  if [[ "$needs_input" == true ]]; then
    log "交互式配置 .env"
    read -rp "CONSOLE_BASE_URL (Console API 地址): " CONSOLE_BASE_URL
    read -rp "NODE_ID (节点 ID): " NODE_ID
    read -rp "PROJECT_KEY [project_a]: " _pk && PROJECT_KEY="${_pk:-project_a}"
    read -rsp "NODE_TOKEN (与 Console 一致，输入不回显): " NODE_TOKEN && echo ""
    read -rp "HEARTBEAT_INTERVAL_SEC [10]: " _hi && HEARTBEAT_INTERVAL_SEC="${_hi:-10}"
  fi

  # 写入（环境变量优先）
  for k in CONSOLE_BASE_URL NODE_ID PROJECT_KEY NODE_TOKEN HEARTBEAT_INTERVAL_SEC; do
    local v="${!k:-}"
    if [[ -z "$v" ]] && [[ -r "$CONFIG_FILE" ]]; then
      v=$(get_env "$k")
    fi
    if [[ -n "$v" ]]; then
      set_env "$k" "$v"
    fi
  done

  # 确保 HEARTBEAT 有默认值
  if [[ -z "$(get_env HEARTBEAT_INTERVAL_SEC)" ]]; then
    set_env "HEARTBEAT_INTERVAL_SEC" "10"
  fi

  log "配置已写入 $CONFIG_FILE"
  log "NODE_TOKEN: $(mask_token "${NODE_TOKEN:-$(get_env NODE_TOKEN)}")"
}

# 8) 安装 systemd service（占位符由 install.sh 注入）
install_service() {
  local unit_file="/etc/systemd/system/${SERVICE_NAME}.service"
  local src_unit="$INSTALL_DIR/systemd/ops-clawdbot-agent.service"
  if [[ ! -f "$src_unit" ]]; then
    src_unit="$INSTALL_DIR/../systemd/ops-clawdbot-agent.service"
  fi
  if [[ ! -f "$src_unit" ]]; then
    log "错误: systemd 模板不存在: systemd/ops-clawdbot-agent.service"
    exit 1
  fi
  local exec_start="${INSTALL_DIR}/.venv/bin/python -m agent.runtime"
  sed -e "s|__INSTALL_DIR__|${INSTALL_DIR}|g" \
      -e "s|__SERVICE_USER__|${SERVICE_USER}|g" \
      -e "s|__ENV_FILE__|${CONFIG_FILE}|g" \
      -e "s|__EXEC_START__|${exec_start}|g" \
      "$src_unit" > "$unit_file"
  chown -R "${SERVICE_USER}:${SERVICE_USER}" "$INSTALL_DIR"
  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
  log "systemd 服务已安装"
}

# 9) 重启服务
start_service() {
  systemctl restart "$SERVICE_NAME"
  log "服务已启动"
}

# 10) 输出状态与日志
print_status() {
  echo ""
  echo "=== 安装完成 ==="
  echo ""
  echo "服务状态:"
  systemctl status "$SERVICE_NAME" --no-pager || true
  echo ""
  echo "最近日志:"
  journalctl -u "$SERVICE_NAME" -n 50 --no-pager 2>/dev/null || true
  echo ""
  echo "下一步:"
  echo "  - 查看日志: journalctl -u $SERVICE_NAME -f"
  echo "  - 自检: $INSTALL_DIR/scripts/doctor.sh"
  echo "  - 卸载: $INSTALL_DIR/scripts/uninstall.sh"
  echo ""
}

# --- main ---
main() {
  check_root
  log "开始安装 $SERVICE_NAME (INSTALL_DIR=$INSTALL_DIR)"
  check_deps
  ensure_user
  clone_or_update
  setup_venv
  write_env
  install_service
  start_service
  print_status
}

main "$@"
