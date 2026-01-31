# ops-node-agent

Linux Node Agent：连接云端 Web Console（FastAPI），作为执行节点存在。

## 职责

- 启动时向 Console 注册节点
- 定期发送心跳
- 轮询拉取任务
- 执行任务（当前仅 PING）
- 回传执行结果

## 技术栈

- Python 3.11+
- requests + 标准库
- 无 FastAPI/Flask

---

## 一键安装 / 卸载 / 自检

安装目录固定为 `/opt/ops-clawdbot`，配置文件为 `/opt/ops-clawdbot/.env`，systemd 服务名为 `ops-clawdbot-agent.service`，运行用户为 `opsnode`（非 root）。仅出站访问 Web Console，无入站端口。主入口：`agent/runtime.py`（install.sh 会校验该文件存在）。支持 Ubuntu 22/24。

**systemd 模板说明**：`systemd/ops-clawdbot-agent.service` 为模板文件，内含占位符 `__INSTALL_DIR__`、`__SERVICE_USER__`、`__ENV_FILE__`、`__EXEC_START__`。install.sh 在安装时会用 sed 替换为实际路径与命令，请勿直接使用该文件启动服务。

### 前置条件

- Linux（支持 systemd）：Ubuntu 20.04+、CentOS 7+、Debian 10+ 等
- git、python3、systemctl（Ubuntu/Debian 下缺 python3-venv 时脚本会尝试 `apt install python3-venv python3-pip`）
- 能访问 Clawdbot Console 的 API 地址

### 一键安装（幂等，可重复执行）

**交互式**（未传环境变量时按提示输入）：

```bash
# 从仓库拉取并执行（需 root/sudo，默认 GIT_REPO 为用户给定 repo）
curl -sSL https://raw.githubusercontent.com/bujie9527/ops-clawdbot/master/ops-node-agent/scripts/install.sh | sudo bash
```

或已克隆后：

```bash
cd /path/to/ops-clawdbot/ops-node-agent
sudo ./scripts/install.sh
```

**非交互式**（通过环境变量传入，适合 CI/自动化）：

```bash
export CONSOLE_BASE_URL=https://console.example.com
export NODE_ID=node-1
export PROJECT_KEY=project_a
export NODE_TOKEN=your_token_from_console
export HEARTBEAT_INTERVAL_SEC=10
sudo -E ./scripts/install.sh
```

**指定仓库与目录**（可覆盖默认值）：

```bash
GIT_REPO=https://github.com/your/ops-clawdbot.git \
BRANCH=master \
INSTALL_DIR=/opt/ops-clawdbot \
SERVICE_USER=opsnode \
sudo ./scripts/install.sh
```

注：ops-clawdbot 主仓默认分支为 `master`，可设置 `BRANCH=master`。

安装完成后会输出：服务状态、最近日志、下一步操作提示。

### 烟雾测试

```bash
sudo bash /opt/ops-clawdbot/scripts/smoke_test.sh
# 或（若在 repo 内）
sudo bash scripts/smoke_test.sh
```

从 `/opt/ops-clawdbot/.env` 读取配置，调用 Console 的 `/api/nodes/register` 与 `/api/nodes/{id}/heartbeat`，输出返回 JSON。失败时输出 HTTP 状态码与建议。不依赖 jq，仅用 curl。

### 自检

```bash
/opt/ops-clawdbot/scripts/doctor.sh
# 或（若在 repo 内）
./scripts/doctor.sh
```

自检会检查：安装目录、配置文件、必需配置项（CONSOLE_BASE_URL、NODE_ID、PROJECT_KEY、NODE_TOKEN、HEARTBEAT_INTERVAL_SEC）、虚拟环境、入口脚本、运行用户、systemd 服务状态，以及（若有 curl）Console 可达性。Token 在输出中脱敏。

### 卸载

```bash
sudo /opt/ops-clawdbot/scripts/uninstall.sh
```

会停止并禁用服务、移除 systemd 单元、删除安装目录 `/opt/ops-clawdbot`。

### 验证服务

```bash
sudo systemctl status ops-clawdbot-agent
sudo journalctl -u ops-clawdbot-agent -f
```

在 Clawdbot Console Web 面板的节点列表中查看新节点是否在线。

---

## 配对方法（与 Clawdbot Console）

节点通过 `NODE_TOKEN` 与 Console 的 `NODE_TOKEN_PROJECT_A` 配对，二者**必须完全一致**。

| 节点 `.env` 变量 | Console `.env` 变量 | 说明 |
|------------------|---------------------|------|
| `CONSOLE_BASE_URL` | - | Console 公网/内网 API 地址，如 `https://console.example.com` |
| `NODE_TOKEN` | `NODE_TOKEN_PROJECT_A` | 必须一致，否则 401 |
| `PROJECT_KEY` | `PROJECT_KEY_DEFAULT` | 当前 MVP 固定为 `project_a` |
| `NODE_ID` | - | 节点唯一 ID，如 `node-1` |
| `NODE_NAME` | - | 展示名称，如 `Node A` |

获取 Token：在 Console 服务器查看 `apps/cloud_console/.env` 中的 `NODE_TOKEN_PROJECT_A`，复制到节点 `.env` 的 `NODE_TOKEN`。

---

## Linux 手动安装

### 1. 克隆项目

```bash
git clone https://github.com/bujie9527/ops-clawdbot.git
cd ops-clawdbot/ops-node-agent
```

### 2. 虚拟环境与依赖

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. 配置

```bash
cp .env.example .env
# 编辑 .env，配置 CONSOLE_BASE_URL、NODE_TOKEN 等（见上方配对方法）
```

### 4. systemd 启动

```bash
sudo mkdir -p /opt/ops-node-agent
sudo cp -r . /opt/ops-node-agent/
sudo useradd -r -s /bin/false ops-agent
sudo chown -R ops-agent:ops-agent /opt/ops-node-agent
sudo cp systemd/ops-node-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ops-node-agent
sudo systemctl start ops-node-agent
```

### 5. 日志

```bash
journalctl -u ops-node-agent -f
```

## 本地运行

```bash
cp .env.example .env
# 编辑 .env
pip install -r requirements.txt
python agent/runtime.py
```

## 目录结构

```
ops-node-agent/
  agent/
    config.py
    http_client.py
    registrar.py
    task_puller.py
    task_executor.py
    reporter.py
    runtime.py
  scripts/
    install.sh        # 一键安装（幂等）
    uninstall.sh      # 卸载
    doctor.sh         # 自检
    smoke_test.sh     # 烟雾测试（register + heartbeat）
  systemd/
    ops-node-agent.service      # 旧 unit（/opt/ops-node-agent）
    ops-clawdbot-agent.service  # 模板（占位符由 install.sh 注入）
  requirements.txt
  .env.example
  README.md
```
