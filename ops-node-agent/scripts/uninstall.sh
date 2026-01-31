#!/usr/bin/env bash
# ops-clawdbot-agent 卸载脚本
# 用法：sudo ./scripts/uninstall.sh

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/ops-clawdbot}"
SERVICE_NAME="ops-clawdbot-agent"
SERVICE_USER="${SERVICE_USER:-opsnode}"

log() { echo "[uninstall] $*"; }

if [[ $EUID -ne 0 ]]; then
  log "请使用 root 或 sudo 运行"
  exit 1
fi

echo ""
echo "即将卸载 $SERVICE_NAME，包括："
echo "  - 停止并禁用服务"
echo "  - 移除 systemd 单元"
echo "  - 删除安装目录 $INSTALL_DIR"
echo ""
read -rp "输入 YES 确认执行卸载: " confirm
if [[ "${confirm:-}" != "YES" ]]; then
  log "已取消（需输入 YES）"
  exit 0
fi

log "停止并禁用服务..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true

log "移除 systemd 单元..."
rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload

log "移除安装目录 $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"

read -rp "是否删除用户 $SERVICE_USER？(y/N): " del_user
if [[ "${del_user:-n}" == "y" || "${del_user:-n}" == "Y" ]]; then
  if id "$SERVICE_USER" &>/dev/null; then
    userdel "$SERVICE_USER" 2>/dev/null || true
    log "已删除用户 $SERVICE_USER"
  fi
else
  log "保留用户 $SERVICE_USER"
fi

echo ""
echo "=== 卸载完成 ==="
echo "  - 服务已停止并禁用"
echo "  - systemd 单元已移除"
echo "  - 安装目录已删除"
echo "  提示: 服务日志仍保留在 systemd journal，可手动执行 journalctl --vacuum-time=7d 清理旧日志"
echo ""
