# Multi-Agent Framework 交付文档

## 快速开始

```bash
cd src/agent
npm install
npm test
```

## 核心API

### Master Agent
```typescript
import { MasterAgent } from './src';

const master = new MasterAgent();
await master.initialize();

// 创建项目
const project = await master.receiveCommand({
  type: 'create_project',
  payload: { name: 'Project Name' }
});

// Fork Spawn Agent
const spawn = await master.receiveCommand({
  type: 'fork_spawn', 
  payload: { projectId: project.id }
});
```

### Spawn Agent
```typescript
import { SpawnAgent } from './src';

const spawn = new SpawnAgent(id, masterId, {
  projectId: 'proj_id',
  maxConcurrentTasks: 5
});

await spawn.initialize();
await spawn.receiveRequirement('Implement feature');
```

### Task Agents
```typescript
import { CodingAgent, DebugAgent } from './src';

// 代码生成
const coder = new CodingAgent(id, taskId, projectId, parentId, 
  'Generate TypeScript class');
const result = await coder.execute();

// 问题修复  
const debugger = new DebugAgent(id, taskId, projectId, parentId,
  'Fix null pointer error');
const fix = await debugger.execute();
```

## 测试结果

- 单元测试: 16个文件
- 测试用例: 80+
- 覆盖率: 核心模块 >80%

## 架构

```
Master → Spawn → Task (coding/debug/task)
```

## 文件清单

| 模块 | 文件 | 说明 |
|------|------|------|
| Core | runtime.ts | Agent生命周期 |
| Core | message-bus.ts | 消息通信 |
| Core | memory.ts | 持久化存储 |
| Core | registry.ts | Skill管理 |
| Master | master-agent.ts | 全局协调 |
| Master | project-manager.ts | 项目管理 |
| Spawn | spawn-agent.ts | 任务分解分配 |
| Task | task-agent.ts | 基类 |
| Task | coding-agent.ts | 代码生成 |
| Task | debug-agent.ts | 问题修复 |
