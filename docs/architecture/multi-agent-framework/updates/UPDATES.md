# 更新记录 (Updates)

## v1.0.0 (2026-04-19)

### 新增功能

#### Fork 后交互机制
- **AgentCommunicationHub**: 实现 Agent fork 后的完整消息交互
  - 父子 Agent 通信支持
  - 广播消息到所有子 Agent
  - 进度报告和结果汇报
  - 上下文请求和传递
  - 错误报告机制

#### Master Agent 增强
- 集成 AgentCommunicationHub
- 支持向所有子 Agent 广播消息
- 实时接收子 Agent 进度更新
- 接收任务完成通知
- 支持心跳检测

#### Spawn Agent 增强
- 集成 AgentCommunicationHub
- Fork Task Agent 后自动注册
- 向 Master 汇报任务进度
- 请求父级上下文
- 接收广播消息

#### Task Agent 增强
- 集成 AgentCommunicationHub
- 实时报告执行进度
- 任务完成后自动汇报结果
- 支持向父 Agent 发送消息

### 代码变更

#### 新增文件
- `src/agent/communication/agent-hub.ts` - 通信中心实现
- `src/agent/communication/__tests__/agent-hub.test.ts` - 通信中心测试

#### 修改文件
- `src/agents/master/master-agent.ts` - 集成通信中心
- `src/agents/spawn/spawn-agent.ts` - 集成通信中心
- `src/agents/task/task-agent.ts` - 集成通信中心
- `src/index.ts` - 导出通信中心

### API 变更

#### 新增 API
```typescript
// AgentCommunicationHub
registerChild(childId: string): void
unregisterChild(childId: string): void
sendToParent(type: MessageType, payload: any): Promise<void>
sendToChild(childId: string, type: MessageType, payload: any): Promise<void>
sendToAllChildren(type: MessageType, payload: any): Promise<void>
reportProgress(taskId: string, percent: number, message: string): Promise<void>
reportResult(taskId: string, result: any): Promise<void>
reportError(error: Error, context?: any): Promise<void>
requestParentContext(): Promise<any>
```

#### 修改 API
```typescript
// MasterAgent
getCommunicationHub(): AgentCommunicationHub

// SpawnAgent
getCommunicationHub(): AgentCommunicationHub

// TaskAgent
getCommunicationHub(): AgentCommunicationHub
```

### 测试

#### 新增测试
- AgentCommunicationHub 完整测试套件
  - 子 Agent 注册/注销测试
  - 消息发送测试（父/子/广播）
  - 进度报告测试
  - 错误报告测试
  - 上下文请求测试

### 文档

#### 新增文档
- `docs/architecture/multi-agent-framework/README.md` - 文档入口
- `docs/architecture/multi-agent-framework/docs/API.md` - API 文档
- `docs/architecture/multi-agent-framework/docs/ARCHITECTURE.md` - 架构文档
- `docs/architecture/multi-agent-framework/docs/USAGE.md` - 使用指南
- `docs/architecture/multi-agent-framework/updates/UPDATES.md` - 本文件
- `docs/architecture/multi-agent-framework/MAINTENANCE.md` - 维护指南

## 历史版本

### v0.9.0 (2026-04-19)
- Phase 4: Task Agent 实现
  - TaskAgent 基类
  - CodingAgent 代码生成
  - DebugAgent 问题修复

### v0.8.0 (2026-04-19)
- Phase 3: Spawn Agent 实现
  - 任务队列管理
  - 任务分配
  - 进度跟踪

### v0.5.0 (2026-04-19)
- Phase 2: Master Agent 实现
  - 项目 CRUD
  - Spawn Agent Fork

### v0.1.0 (2026-04-19)
- Phase 1: 基础框架
  - AgentRuntime
  - MessageBus
  - MemorySystem
  - SkillRegistry
