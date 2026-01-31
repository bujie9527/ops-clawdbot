# ops-node-agent 安装脚本自查报告

> 自查日期：根据生产环境标准执行

## 1) 幂等性检查 ✅

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 重复执行拉取最新代码 | ✅ | `clone_or_update` 每次 clone 到临时目录，rsync 到 `INSTALL_DIR`，会更新代码 |
| 跳过已存在的 .venv | ✅ | `setup_venv` 检查 `.venv/bin/pip` 存在则跳过创建；若残缺则删除重建 |
| 保留已存在的 .env | ✅ | `clone_or_update` 在 rsync 前备份 `.env`，sync 后恢复；`write_env` 的 `set_env` 只更新 5 个 key，不覆盖整文件 |
| Token 不写入日志 | ✅ | `write_env` 使用 `mask_token` 脱敏输出；`read -rsp` 输入 token 不回显 |

## 2) 依赖检查 ✅

| 检查项 | 结果 | 说明 |
|--------|------|------|
| git, python3, systemctl | ✅ | 启动时检查，缺失则报错 |
| python3-venv | ✅ | `import venv` 检查；Debian/Ubuntu 下 apt 安装 `python3.X-venv` |
| python3-pip, git | ✅ | 依赖缺失时自动 `apt-get install` |

## 3) 日志输出检查 ✅

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 仅输出必要信息 | ✅ | 使用 `log` 统一前缀，无冗余输出 |
| Token 脱敏 | ✅ | `mask_token` 仅显示前后 4 位，中间 `****` |

## 4) 配置文件覆盖检查 ✅

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 保留已存在配置 | ✅ | `set_env` 用 `grep -v "^KEY="` 移除旧行后追加，保留其他 key 和注释 |
| 不覆盖用户自定义 | ✅ | 环境变量优先，无则从 `get_env` 读文件，仅更新 5 个必需 key |
| 必需字段完整 | ✅ | 交互模式会提示缺失项；非交互需通过环境变量传入 |

## 5) 服务启动检查 ✅

| 检查项 | 结果 | 说明 |
|--------|------|------|
| systemctl start | ✅ | `install_service` 后 `start_service` 执行 `systemctl restart` |
| 非 root 运行 | ✅ | systemd 模板 `User=__SERVICE_USER__`（opsnode） |
| systemctl status | ✅ | `print_status` 输出 `systemctl status` |
| journalctl 查看日志 | ✅ | `print_status` 输出 `journalctl -u ops-clawdbot-agent -n 50` |

## 6) 卸载支持检查 ✅

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 删除 /opt/ops-clawdbot | ✅ | `rm -rf "$INSTALL_DIR"` |
| stop + disable | ✅ | `systemctl stop` 与 `systemctl disable` |
| 删除 systemd 单元 | ✅ | `rm -f /etc/systemd/system/ops-clawdbot-agent.service` |
| 可选删除 opsnode 用户 | ✅ | 交互提示 `是否删除用户` |
| 日志清理说明 | ✅ | 完成提示中说明 journal 保留，可手动 `journalctl --vacuum-time=7d` |

## 7) 自检命令支持 ✅

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 服务存在与运行 | ✅ | `doctor.sh` 检查 systemd 单元及 `is-active` |
| .env 存在且配置正确 | ✅ | 检查 5 个必需 key |
| Console HTTP 连通性 | ✅ | `curl -I $CONSOLE_BASE_URL/health` |
| 虚拟环境 | ✅ | 检查 `.venv/bin/python` 存在 |
| 入口文件 | ✅ | 检查 `agent/runtime.py` |

## 语法检查

```bash
bash -n scripts/install.sh   # 无输出即通过
bash -n scripts/uninstall.sh
bash -n scripts/doctor.sh
```

## 已知限制

1. **非 Debian/Ubuntu**：依赖自动安装仅支持 apt，其他发行版需手动安装 python3-venv、git
2. **非交互模式**：管道执行时无法 `read`，需通过环境变量传入全部配置
3. **.env 格式**：`set_env` 假设 `KEY=value` 格式，不支持 `KEY = value` 等变体
