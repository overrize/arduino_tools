# 架构设计

## 系统架构

```
┌─────────────────────────────────────┐
│           Master Agent               │
│  - 全局协调                          │
│  - 项目管理                          │
│  - 子 Agent 管理                     │
│  - AgentCommunicationHub            │
└──────────────┬──────────────────────┘
               │ fork
       ┌───────┼───────┐
       ▼       ▼       ▼
   Spawn1   Spawn2   Spawn3
   (项目级，持久化)
       │
       │ fork
       ▼
   Task Agents (coding/debug/task)
   (临时，任务完成后销毁)
```

## 通信机制

### AgentCommunicationHub

所有 Agent 通过 `AgentCommunicationHub` 进行通信：

```
Master (Hub)
  │
  ├─► sendToAllChildren() ──► Spawn1, Spawn2, Spawn3
  │
  ├─◄ reportProgress() ◄──── Spawn1
  │
  └─◄ reportResult() ◄────── Spawn1
       │
       ├─► sendToParent() ──► Master
       │
       ├─► registerChild() ─► Task1, Task2
       │
       └─◄ reportProgress() ◄─ Task1
```

### 消息类型

- **下行**: Master → Spawn → Task
  - `CONTEXT_SHARE` - 共享上下文
  - `TASK_ASSIGN` - 分配任务
  - `EVENT_BROADCAST` - 广播事件

- **上行**: Task → Spawn → Master
  - `TASK_PROGRESS` - 进度报告
  - `TASK_RESULT` - 结果汇报
  - `ERROR` - 错误报告
  - `CONTEXT_REQUEST` - 请求上下文

## 数据流

### 项目创建流程

```
1. User ──create_project──► Master
2. Master ──fork_spawn──► AgentRuntime
3. AgentRuntime ──fork──► SpawnAgent
4. SpawnAgent ──registerChild──► Master.CommunicationHub
5. SpawnAgent ──CONTEXT_SHARE──► Memory
```

### 任务执行流程

```
1. User ──requirement──► SpawnAgent
2. SpawnAgent ──decompose──► Tasks
3. SpawnAgent ──fork──► TaskAgent
4. TaskAgent ──reportProgress──► SpawnAgent ──► Master
5. TaskAgent ──reportResult──► SpawnAgent ──► Master
6. SpawnAgent ──unregisterChild──► TaskAgent
```

## 内存模型

### 继承链

```
Master Memory
    │ inheritedFrom
Spawn Memory
    │ inheritedFrom
Task Memory
```

每个 Agent 的 Memory 可以选择性地继承父级 Memory。

### 上下文传递

1. **Fork 时**: Master 通过 `sendToChild(CONTEXT_SHARE)` 发送项目上下文
2. **运行时**: Task 通过 `requestParentContext()` 请求父级上下文
3. **持久化**: 所有上下文写入 MemorySystem

## 组件职责

### AgentRuntime
- Agent 生命周期管理
- Worker 进程管理
- 心跳检测

### MessageBus
- 消息路由
- 消息确认
- 重试机制

### MemorySystem
- 数据持久化
- 继承链管理
- 权限控制

### AgentCommunicationHub
- 父子通信
- 广播消息
- 进度/结果报告

### SkillRegistry
- Skill 注册
- 动态加载
- 权限检查

## 安全设计

### 权限控制

- Agent 只能访问自己的 Memory
- 子 Agent 可以读取父级 Memory（只读）
- 写操作需要显式权限

### 消息验证

- 消息来源验证
- 消息类型检查
- 超时处理

## 扩展性

### 添加新的 Agent 类型

1. 继承 `TaskAgent`
2. 实现 `performTask()` 方法
3. 集成 `AgentCommunicationHub`

### 添加新的通信模式

1. 在 `MessageType` 中添加新类型
2. 在 `AgentCommunicationHub` 中添加处理方法
3. 在 `setupDefaultHandlers()` 中注册

## 性能考虑

### 消息批处理
- 进度报告合并
- 结果批量发送

### 内存优化
- 任务完成后清理 Memory
- 上下文懒加载

### 并发控制
- 最大并发任务数限制
- 消息队列优先级
