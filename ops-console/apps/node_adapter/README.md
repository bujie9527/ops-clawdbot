# node_adapter

节点适配器：Clawdbot 节点主动向 Console 拉取任务并上报结果（Pull 模式）。

**本阶段不实现业务，仅保留骨架。** 后续实现：

- 定时轮询 Console `/api/nodes/{id}/tasks/pull`
- 执行任务并上报结果
- 心跳上报
