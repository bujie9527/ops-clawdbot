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

## Linux 安装

### 1. 克隆项目

```bash
sudo mkdir -p /opt/ops-node-agent
sudo chown $USER:$USER /opt/ops-node-agent
cd /opt/ops-node-agent
git clone <repo_url> .
```

### 2. 虚拟环境与依赖

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. 配置

```bash
cp .env.example .env
# 编辑 .env，配置 CONSOLE_BASE_URL、NODE_TOKEN 等
```

### 4. systemd 启动

```bash
# 创建运行用户（非 root）
sudo useradd -r -s /bin/false ops-agent
sudo chown -R ops-agent:ops-agent /opt/ops-node-agent

# 安装 service
sudo cp systemd/ops-node-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ops-node-agent
sudo systemctl start ops-node-agent
sudo systemctl status ops-node-agent
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
  systemd/
    ops-node-agent.service
  requirements.txt
  .env.example
  README.md
```
