# 使用指南

## 快速开始

### 安装

```bash
cd src/agent
npm install
```

### 运行测试

```bash
npm test
```

## 基本用法

### 1. 创建 Master Agent

```typescript
import { MasterAgent } from './src';

const master = new MasterAgent();
await master.initialize();

console.log(`Master ID: ${master.getId()}`);
```

### 2. 创建项目

```typescript
const project = await master.receiveCommand({
  type: 'create_project',
  payload: {
    name: 'My Project',
    description: 'Project description',
    technologies: ['typescript', 'nodejs'],
    priority: 'high'
  },
  source: 'user'
});

console.log(`Project created: ${project.id}`);
```

### 3. Fork Spawn Agent

```typescript
const spawn = await master.receiveCommand({
  type: 'fork_spawn',
  payload: {
    projectId: project.id,
    config: {
      maxConcurrentTasks: 5
    }
  },
  source: 'user'
});

console.log(`Spawn Agent: ${spawn.id}`);
```

### 4. 使用 Spawn Agent

```typescript
import { SpawnAgent } from './src';

const spawnAgent = new SpawnAgent(spawn.id, master.getId(), {
  projectId: project.id,
  maxConcurrentTasks: 5,
  autoRetryFailed: true
});

await spawnAgent.initialize();

// 接收需求
const result = await spawnAgent.receiveRequirement(
  'Implement user authentication with TypeScript'
);

console.log(`Tasks queued: ${result.tasksQueued}`);
```

### 5. 监听进度

```typescript
// Master 监听 Spawn 进度
master.on('spawn:progress', (data) => {
  console.log(`Task ${data.taskId}: ${data.percent}% - ${data.message}`);
});

// Master 监听任务完成
master.on('spawn:completed', (data) => {
  console.log(`Task completed: ${data.taskId}`);
  console.log(`Result:`, data.result);
});
```

## 通信机制

### 广播消息

```typescript
// Master 向所有子 Agent 广播
await master.receiveCommand({
  type: 'broadcast',
  payload: {
    message: 'System maintenance in 5 minutes'
  },
  source: 'admin'
});

// 或使用自然语言
await master.handleUserInteraction('broadcast System going down for maintenance');
```

### 直接通信

```typescript
// 获取通信中心
const hub = master.getCommunicationHub();

// 向指定子 Agent 发送消息
await hub.sendToChild('SPAWN-123', MessageType.TASK_ASSIGN, {
  taskId: 'task-1',
  priority: 'high'
});

// 获取所有子 Agent
const children = hub.getChildren();
console.log(`Active children: ${children.length}`);
```

### 进度报告

```typescript
// 在 Task Agent 中报告进度
await this.communicationHub.reportProgress(
  this.taskId,
  50,
  'Halfway complete'
);

// 报告结果
await this.communicationHub.reportResult(this.taskId, {
  output: generatedCode,
  files: ['src/index.ts']
});
```

## 代码生成示例

```typescript
import { CodingAgent } from './src';

const codingAgent = new CodingAgent(
  'CODING-AGENT-1',
  'task-code-1',
  project.id,
  spawn.id,
  'Generate a TypeScript class for user authentication with JWT support'
);

const result = await codingAgent.execute();

console.log('Generated code:', result.output.code);
console.log('Language:', result.output.language);
console.log('Review:', result.output.review);
```

## 调试示例

```typescript
import { DebugAgent } from './src';

const debugAgent = new DebugAgent(
  'DEBUG-AGENT-1',
  'task-debug-1',
  project.id,
  spawn.id,
  'Fix null pointer exception in user data processing'
);

const result = await debugAgent.execute();

console.log('Root cause:', result.output.diagnosis.rootCause);
console.log('Fix:', result.output.fix.description);
console.log('Verified:', result.output.verified);
```

## 关闭系统

```typescript
// 关闭 Spawn Agent
await spawnAgent.shutdown();

// 关闭 Master Agent（会自动关闭所有子 Agent）
await master.shutdown();
```

## 最佳实践

### 1. 错误处理

```typescript
try {
  await spawnAgent.receiveRequirement(requirement);
} catch (error) {
  console.error('Failed to process requirement:', error);
  // 向 Master 报告错误
  await spawnAgent.getCommunicationHub().reportError(error);
}
```

### 2. 进度监控

```typescript
// 定期获取统计信息
setInterval(async () => {
  const stats = await master.receiveCommand({
    type: 'get_stats',
    payload: {},
    source: 'monitor'
  });
  
  console.log('Active agents:', stats.master.managedAgents);
  console.log('Projects:', stats.master.projects);
}, 5000);
```

### 3. 资源清理

```typescript
process.on('SIGINT', async () => {
  console.log('Shutting down...');
  await master.shutdown();
  process.exit(0);
});
```

## 故障排查

### Agent 无法 Fork

- 检查 AgentRuntime 是否已初始化
- 检查 maxAgents 限制
- 查看 AgentRuntime 统计信息

### 消息未送达

- 检查 Agent ID 是否正确
- 检查 Agent 是否已注册
- 查看 MessageBus 统计信息

### 任务卡住

- 检查任务队列大小
- 检查并发任务数限制
- 查看 Agent 状态

## 进阶用法

### 自定义 Task Agent

```typescript
import { TaskAgent, TaskResult } from './src';

class MyCustomAgent extends TaskAgent {
  async performTask(): Promise<any> {
    // 报告开始
    await this.reportProgress(0, 'Starting custom task');
    
    // 执行任务
    const result = await this.doCustomWork();
    
    // 报告进度
    await this.reportProgress(50, 'Halfway done');
    
    // 完成
    return result;
  }
  
  private async doCustomWork(): Promise<any> {
    // 实现自定义逻辑
    return { success: true };
  }
}
```
