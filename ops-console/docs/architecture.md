# 架构说明

## 系统定位

Clawdbot Console 是「控制面（Control Plane）」：提供 Web 管理面板 + JSON API，用于跨云管理多个 Clawdbot 节点，并下发任务。

## 跨云 Pull 模式

### 为什么用 Pull 而不是 Push？

- **节点不开放入站端口**：节点部署在不同云（阿里云、腾讯云、AWS 等），通常处于私有网络或防火墙后，无法从公网直接访问节点的 IP/端口。
- **Pull 模式**：节点通过 `node-adapter` 主动向 Console 发起 HTTPS 请求，拉取待执行任务，执行后回传结果。全程由节点发起连接，无需暴露端口。
- **运维友好**：无需为每个节点配置公网 IP、安全组、端口转发；Console 只需一个公网入口，节点可在任意网络环境接入。

### 数据流

```
[Console] <-- HTTPS (节点拉取) -- [node-adapter] --> [Clawdbot 节点]
    |                                    |
    | 任务入队                             | 执行任务
    v                                    v
[MySQL] <-- 结果回执 (节点上报) ----------|
```

1. 管理员在 Console 创建任务，任务写入 `tasks` 表，状态为 `CREATED`/`QUEUED`。
2. 节点上的 `node-adapter` 定时调用 `POST /api/nodes/{id}/tasks/pull` 拉取任务。
3. 节点执行任务后，调用 `POST /api/tasks/{id}/result` 上报结果。
4. Console 更新任务状态和 `task_events`。

## 组件

| 组件 | 职责 |
|------|------|
| **cloud_console** | Web 面板 + JSON API，任务调度与管理 |
| **node_adapter** | 部署在节点，轮询拉取任务、执行、上报结果 |
| **MySQL** | 持久化 nodes / tasks / task_events |

## 安全（MVP）

- **节点接口**：Bearer Token（`Authorization: Bearer <NODE_TOKEN>`），Token 与 `project_key` 绑定。
- **管理端**：admin 用户名/密码 + session cookie（最简实现）。
