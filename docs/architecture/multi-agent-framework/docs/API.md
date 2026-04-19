# API 文档

## 核心类

### AgentCommunicationHub

Agent fork 后的消息交互中心。

#### 构造函数

```typescript
constructor(agentId: string, parentId?: string)
```

- `agentId`: 当前 Agent ID
- `parentId`: 父 Agent ID（可选）

#### 方法

##### registerChild(childId: string): void
注册子 Agent。

```typescript
hub.registerChild('SPAWN-123');
```

##### unregisterChild(childId: string): void
注销子 Agent。

```typescript
hub.unregisterChild('SPAWN-123');
```

##### sendToParent(type: MessageType, payload: any): Promise<void>
向父 Agent 发送消息。

```typescript
await hub.sendToParent(MessageType.TASK_PROGRESS, {
  taskId: 'task-1',
  percent: 50,
  message: 'Halfway done'
});
```

##### sendToChild(childId: string, type: MessageType, payload: any): Promise<void>
向指定子 Agent 发送消息。

```typescript
await hub.sendToChild('SPAWN-123', MessageType.TASK_ASSIGN, {
  taskId: 'task-1',
  task: { /* task data */ }
});
```

##### sendToAllChildren(type: MessageType, payload: any): Promise<void>
向所有子 Agent 广播消息。

```typescript
await hub.sendToAllChildren(MessageType.EVENT_BROADCAST, {
  event: 'shutdown',
  message: 'System going down'
});
```

##### reportProgress(taskId: string, percent: number, message: string): Promise<void>
向父 Agent 报告任务进度。

```typescript
await hub.reportProgress('task-1', 75, 'Almost complete');
```

##### reportResult(taskId: string, result: any): Promise<void>
向父 Agent 报告任务结果。

```typescript
await hub.reportResult('task-1', {
  output: 'Generated code',
  files: ['src/index.ts']
});
```

##### reportError(error: Error, context?: any): Promise<void>
向父 Agent 报告错误。

```typescript
try {
  // do something
} catch (error) {
  await hub.reportError(error, { taskId: 'task-1' });
}
```

##### requestParentContext(): Promise<any>
请求父 Agent 的上下文。

```typescript
const context = await hub.requestParentContext();
// Returns: { agentId, children, timestamp }
```

##### onMessage(type: MessageType, handler: Function): () => void
监听指定类型的消息。

```typescript
const unsubscribe = hub.onMessage(MessageType.TASK_ASSIGN, (payload, from) => {
  console.log(`Received task from ${from}:`, payload);
});

// Later: unsubscribe()
```

#### 事件

- `child:registered` - 子 Agent 注册时触发
- `child:unregistered` - 子 Agent 注销时触发
- `message:sent` - 消息发送时触发
- `task:progress` - 收到进度更新时触发
- `task:completed` - 任务完成时触发
- `agent:error` - 收到错误报告时触发
- `context:received` - 收到上下文时触发

---

### MasterAgent

全局协调 Agent。

#### 方法

##### initialize(): Promise<void>
初始化 Master Agent。

```typescript
const master = new MasterAgent();
await master.initialize();
```

##### receiveCommand(cmd: Command): Promise<any>
接收并执行命令。

```typescript
const result = await master.receiveCommand({
  type: 'create_project',
  payload: { name: 'My Project' },
  source: 'user'
});
```

支持命令：
- `create_project` - 创建项目
- `delete_project` - 删除项目
- `get_project` - 获取项目
- `list_projects` - 列出项目
- `fork_spawn` - Fork Spawn Agent
- `terminate_agent` - 终止 Agent
- `broadcast` - 广播消息
- `get_stats` - 获取统计信息

##### getCommunicationHub(): AgentCommunicationHub
获取通信中心实例。

```typescript
const hub = master.getCommunicationHub();
await hub.sendToAllChildren(MessageType.EVENT_BROADCAST, { message: 'Hello' });
```

##### shutdown(): Promise<void>
关闭 Master Agent。

```typescript
await master.shutdown();
```

---

### SpawnAgent

任务分解和分配 Agent。

#### 构造函数

```typescript
constructor(
  id: string,
  masterId: string,
  config: {
    projectId: string;
    maxConcurrentTasks: number;
    autoRetryFailed: boolean;
  }
)
```

#### 方法

##### initialize(): Promise<void>
初始化 Spawn Agent。

##### receiveRequirement(req: string): Promise<any>
接收需求并分解为任务。

```typescript
const result = await spawn.receiveRequirement('Implement user authentication');
// Returns: { tasksQueued: 3 }
```

##### getCommunicationHub(): AgentCommunicationHub
获取通信中心实例。

```typescript
const hub = spawn.getCommunicationHub();
await hub.reportProgress('task-1', 50, 'Halfway');
```

---

### TaskAgent

任务执行 Agent 基类。

#### 子类

- `CodingAgent` - 代码生成
- `DebugAgent` - 问题修复

#### 方法

##### execute(): Promise<TaskResult>
执行任务。

```typescript
const result = await agent.execute();
// Returns: { taskId, status, output, duration }
```

##### getCommunicationHub(): AgentCommunicationHub
获取通信中心实例。

```typescript
const hub = agent.getCommunicationHub();
await hub.reportProgress(taskId, percent, message);
```

---

## 类型定义

### MessageType

```typescript
enum MessageType {
  FORK_REQUEST = 'fork_request',
  FORK_RESPONSE = 'fork_response',
  TERMINATE_REQUEST = 'terminate_request',
  TASK_ASSIGN = 'task_assign',
  TASK_RESULT = 'task_result',
  TASK_PROGRESS = 'task_progress',
  TASK_CANCEL = 'task_cancel',
  CONTEXT_SHARE = 'context_share',
  CONTEXT_REQUEST = 'context_request',
  CONTEXT_RESPONSE = 'context_response',
  EVENT_BROADCAST = 'event_broadcast',
  HEARTBEAT = 'heartbeat',
  ERROR = 'error',
}
```

### TaskResult

```typescript
interface TaskResult {
  taskId: string;
  status: 'success' | 'failed' | 'cancelled';
  output?: any;
  error?: string;
  duration: number;
}
```
