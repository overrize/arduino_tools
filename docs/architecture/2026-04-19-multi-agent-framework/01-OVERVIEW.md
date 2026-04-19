---
title: 系统架构总体设计
version: 1.0.0
date: 2026-04-19
---

# 1️⃣ Arduino Tools 多Agent框架 - 架构总体设计

## 📖 章节概览

本章介绍多Agent框架的系统架构、核心设计原则和各组件关系。

---

## 1.1 系统架构图

### 整体架构

```
┌───────────────────────────────────────────────────────────────┐
│                        User Interface (Tauri)                 │
│                      (Arduino Desktop/Web)                    │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ 命令/事件
                ▼
┌───────────────────────────────────────────────────────────────┐
│                    Master Agent (L1)                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • 用户交互处理                                           │ │
│  │ • 项目生命周期管理                                       │ │
│  │ • 需求记录和展示                                        │ │
│  │ • Fork Spawn Agent                                      │ │
│  │ • 全局Memory与Skills管理                                │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Memory: global/                    Skills: global/*          │
└───────────────┬─────────────────────────────────────────────┘
                │
        ┌───────┼────────┬──────────┐
        │       │        │          │
        ▼       ▼        ▼          ▼
      ┌──┐   ┌──┐   ┌──┐        ┌──┐
      │SP│   │SP│   │SP│  ...   │SP│
      │ 1│   │ 2│   │ 3│        │ N│
      └┬─┘   └┬─┘   └┬─┘        └┬─┘
        │      │      │           │
    Project Project Project   Project
      A      B       C           N
        │      │      │           │ Spawn Agent (L2)
        │      │      │           │ 持久化，项目级上下文
        │      │      │           │
        ├─ fork ┤      │           ├─────── fork ────────┤
        │       │      │           │
        ▼       ▼      ▼           ▼
      ┌──┐   ┌──┐   ┌──┐        ┌──┐
      │CA│   │DA│   │TA│  ...   │TA│
      │  │   │  │   │  │        │  │
      └──┘   └──┘   └──┘        └──┘

      CA: CodingAgent (临时, L3)
      DA: DebugAgent  (临时, L3)
      TA: TaskAgent   (临时, L3)
```

### 三层隔离模型

```
┌─────────────────────────────────────┐
│ L1: Master Agent                    │
│ ├─ 长期运行 (进程级)                │
│ ├─ 全局作用域                       │
│ ├─ 多个Spawn Agent的管理者          │
│ └─ 用户交互入口                     │
└─────────────────────────────────────┘
           ▲
           │ 通过消息队列
           ▼
┌─────────────────────────────────────┐
│ L2: Spawn Agent (1..N)              │
│ ├─ 项目级长期运行                   │
│ ├─ 继承Master的Memory & Skills      │
│ ├─ 项目专属上下文                   │
│ ├─ Fork工作Agent的管理者            │
│ └─ 项目进度和反馈                   │
└─────────────────────────────────────┘
           ▲
           │ 通过消息队列
           ▼
┌─────────────────────────────────────┐
│ L3: Task Agent (CodingAgent等)      │
│ ├─ 短期运行 (任务级)                │
│ ├─ 任务完成后自动终止               │
│ ├─ 独立的临时Memory                │
│ ├─ 继承Spawn Agent的Skills          │
│ └─ 具体工作执行                     │
└─────────────────────────────────────┘
```

---

## 1.2 核心设计原则

### 原则1: 职责分离
- **Master**: 不做具体工作，只协调和交互
- **Spawn**: 不做编码/调试，只跟进和反馈
- **Task**: 只做具体任务，完成后立即清理

### 原则2: 上下文继承
```
Master Memory + Skills
    ├─ 被所有Spawn Agent继承
    │   └─ Spawn可扩展项目级Memory/Skills
    │       └─ 被Spawn fork的Task Agent继承
```

### 原则3: 持久化分层
```
生命周期          存储位置              清理时机
├─ L1 (全局)  →  memory/global/     → 项目关闭时
├─ L2 (项目)  →  memory/projects/X/ → 项目删除时
└─ L3 (任务)  →  memory/tasks/Y/    → 任务完成时
```

### 原则4: 通信异步化
- Agent间全部通过消息队列通信
- 支持并行执行多个Spawn Agent
- 避免阻塞式调用

### 原则5: 可观测性
- 所有Agent操作都有日志
- 完整的审计追踪
- 状态变化事件记录

---

## 1.3 核心组件

### 1.3.1 Agent Runtime (Agent运行时)

**职责**:
- Agent生命周期管理
- Worker进程池管理
- IPC通信桥接

**核心类**:
```typescript
class AgentRuntime {
  // Agent生命周期
  forkAgent(config: AgentConfig): AgentInstance
  spawnAgent(type: AgentType, projectId: string): AgentInstance
  terminateAgent(agentId: string): Promise<void>

  // 消息通信
  sendMessage(fromId: string, toId: string, message: Message): void
  subscribe(agentId: string, handler: MessageHandler): void

  // 状态查询
  getAgentStatus(agentId: string): AgentStatus
  listActiveAgents(): AgentInstance[]
}
```

### 1.3.2 Memory System (内存管理系统)

**职责**:
- Memory的CRUD操作
- 继承链管理
- 持久化存储

**核心接口**:
```typescript
interface MemorySystem {
  // 读写操作
  read(path: string): Promise<MemoryContent>
  write(path: string, content: any): Promise<void>
  append(path: string, entry: any): Promise<void>

  // 继承管理
  getInheritedMemory(agentId: string): Promise<MemoryContent>
  setupInheritance(childId: string, parentId: string): void

  // 清理
  clearMemory(path: string): Promise<void>
}
```

### 1.3.3 Skills Registry (技能注册系统)

**职责**:
- Skills的注册和加载
- 权限控制
- 动态注入

**核心接口**:
```typescript
interface SkillsRegistry {
  // 注册Skills
  register(skill: Skill, scope: 'global' | 'spawn' | 'task'): void

  // 加载Skills
  loadSkills(agentId: string): Promise<SkillSet>
  getAvailableSkills(agentId: string): Skill[]

  // 执行Skills
  executeSkill(agentId: string, skillName: string, args: any): Promise<any>
}
```

### 1.3.4 Communication Bus (通信总线)

**职责**:
- Agent间消息路由
- 事件分发
- 可靠性保证

**消息类型**:
```typescript
interface Message {
  id: string                    // 消息ID
  from: string                  // 发送者Agent ID
  to: string | string[]         // 接收者Agent ID(s)
  type: MessageType             // 消息类型
  payload: any                  // 消息内容
  timestamp: number             // 时间戳
  priority: 'high' | 'normal'   // 优先级
}

enum MessageType {
  FORK_REQUEST = 'fork_request'
  FORK_RESPONSE = 'fork_response'
  TASK_START = 'task_start'
  TASK_COMPLETE = 'task_complete'
  PROGRESS_UPDATE = 'progress_update'
  CONTEXT_SHARE = 'context_share'
  STATUS_QUERY = 'status_query'
}
```

### 1.3.5 Project Manager (项目管理器)

**职责**:
- 项目的创建、删除、列表
- 项目<->Spawn Agent映射
- 项目状态管理

**核心API**:
```typescript
interface ProjectManager {
  // 项目CRUD
  createProject(config: ProjectConfig): Promise<Project>
  getProject(projectId: string): Promise<Project>
  listProjects(): Promise<Project[]>
  deleteProject(projectId: string): Promise<void>

  // 状态管理
  updateProjectStatus(projectId: string, status: ProjectStatus): void
  getProjectSpawnAgent(projectId: string): AgentInstance
}
```

---

## 1.4 数据流

### 流程1: 创建项目并Fork Spawn Agent

```
用户命令
  │
  ▼
┌─────────────────────┐
│ Master Agent        │
│ (接收创建请求)      │
└────────┬────────────┘
         │
         ├─ 1. ProjectManager.createProject()
         │
         └─ 2. AgentRuntime.forkAgent(SpawnAgent)
                │
                ├─ 创建Worker进程
                ├─ 初始化项目级Memory
                ├─ 注册到SkillsRegistry
                └─ 建立消息通道
         │
         ▼
      Spawn Agent Ready
      返回确认给用户
```

### 流程2: Spawn Agent Fork Task Agent执行工作

```
Spawn Agent
  │ (收到任务)
  │
  ├─ 1. 准备上下文 (加载Memory)
  │
  ├─ 2. AgentRuntime.spawnAgent(CodingAgent)
  │     │
  │     ├─ 创建Worker进程
  │     ├─ 传递上下文
  │     └─ 启动任务
  │
  ├─ 3. 监听进度消息 (PROGRESS_UPDATE)
  │
  ├─ 4. 任务完成后
  │     │
  │     ├─ 收集结果
  │     ├─ 保存任务日志到项目Memory
  │     └─ AgentRuntime.terminateAgent(CodingAgent)
  │
  └─ 5. 返回反馈给Master
```

### 流程3: 上下文继承链

```
1. Master读取global Memory
   ↓
2. Spawn继承并加载
   ├─ global Memory (只读)
   └─ projects/projectA/ Memory (读写)
   ↓
3. Task继承并加载
   ├─ global Memory (只读)
   ├─ projects/projectA/ Memory (只读)
   └─ tasks/taskXYZ/ Memory (读写,临时)
```

---

## 1.5 关键特性

### 1.5.1 并行处理
- 多个Spawn Agent并行运行
- 每个Spawn可同时fork多个Task Agent
- 通过消息队列实现异步处理

### 1.5.2 上下文持久化
- 项目级Memory持久到文件系统
- 任务级Memory在内存+临时文件
- 支持任务恢复（通过Memory重建）

### 1.5.3 灵活扩展
```typescript
// 添加新的Skill很简单
skillsRegistry.register(new MySkill(), 'global')

// 添加新的Task Agent类型也很简单
class NewTaskAgent extends TaskAgent {
  async execute() { /* 自定义逻辑 */ }
}
```

### 1.5.4 安全隔离
- Worker进程完全隔离
- 没有共享内存风险
- Task Agent不能访问其他Project的Memory

---

## 1.6 与现有系统的集成

### 现有组件

```
arduino-desktop/     ← Tauri UI界面
  ├─ src-tauri/     ← Rust后端
  └─ src/           ← React前端

arduino-web/        ← Web UI

arduino-mcp-server/ ← MCP服务器

arduino-client/     ← CLI客户端
```

### 集成点

```
┌──────────────────┐
│  Tauri UI        │
│  Arduino Desktop │
└────────┬─────────┘
         │
         │ Tauri Command API
         │
         ▼
┌──────────────────────────────┐
│  Tauri Backend (Rust)        │
│ (提供命令接口)               │
└────────┬─────────────────────┘
         │
         │ Node.js IPC / Stdio
         │
         ▼
┌──────────────────────────────┐
│  Master Agent (Node.js)       │
│  + Agent Runtime              │
│  + Communication Bus          │
│  + Memory System              │
│  + Skills Registry            │
└──────────────────────────────┘
```

---

## 1.7 扩展性考虑

### 横向扩展
- 支持在不同机器上运行Agent
- 通过网络通信替代IPC
- 支持分布式部署

### 纵向扩展
- 支持更多层级的Agent
- 支持Agent嵌套fork
- 支持动态的Skills加载

### 新Agent类型
```typescript
// 容易添加新的Agent类型
class ReviewAgent extends TaskAgent {
  // 代码审查Agent
}

class TestAgent extends TaskAgent {
  // 测试Agent
}

class OptimizeAgent extends TaskAgent {
  // 优化Agent
}
```

---

## 1.8 非功能性需求

| 需求 | 目标 | 实现方式 |
|------|------|--------|
| 可靠性 | 99.9% 可用性 | 心跳检测、故障恢复 |
| 性能 | <100ms消息延迟 | 本地IPC、异步处理 |
| 可扩展性 | 支持50+个并行Spawn | 进程池、负载均衡 |
| 可维护性 | 清晰的代码结构 | 模块化、接口抽象 |
| 安全性 | 进程隔离 | Worker进程、权限控制 |

---

## 📊 架构对标

| 对标系统 | 相似点 | 差异点 |
|---------|------|------|
| Kubernetes | 多级orchestration | 单机、文件驱动 |
| 微服务 | 隔离、通信、扩展 | 同进程、轻量级 |
| Actor模型 | 消息驱动、并发 | 分层、持久化 |
| VSCode扩展 | 进程隔离、插件系统 | 不支持fork |

---

## 🔗 相关文档

- [AGENT-ROLES.md](./02-AGENT-ROLES.md) - 详细的角色定义
- [COMMUNICATION.md](./05-COMMUNICATION.md) - 通信机制详设
- [LIFECYCLE.md](./06-LIFECYCLE.md) - 生命周期管理
- [IMPLEMENTATION-GUIDE.md](./07-IMPLEMENTATION-GUIDE.md) - 实现代码示例

---

## 📝 下一步

1. 阅读 [AGENT-ROLES.md](./02-AGENT-ROLES.md) 了解各Agent的具体职责
2. 学习 [MEMORY-SYSTEM.md](./03-MEMORY-SYSTEM.md) 理解数据持久化
3. 参考 [IMPLEMENTATION-GUIDE.md](./07-IMPLEMENTATION-GUIDE.md) 开始编码
