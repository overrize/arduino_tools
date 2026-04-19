---
title: 快速参考卡
version: 1.0.0
date: 2026-04-19
---

# ⚡ 快速参考卡

打印此页保存在办公桌上！

---

## 三层Agent一览

| Agent | 数量 | 生命周期 | 职责 | Memory | Skills |
|-------|------|--------|------|--------|--------|
| **Master** | 1 | 全局 | 协调、交互、项目管理 | global/* | global/* |
| **Spawn** | 1..N | 项目级 | 进度跟进、任务分配 | projects/* | 继承 |
| **Task** | 可变 | 任务级 | 代码/调试等工作 | tasks/* | 继承 |

---

## Message类型速查

```
FROM Master        TO Spawn
├─ NEW_REQUIREMENT
├─ CONFIG_UPDATE
└─ ...

FROM Spawn         TO Master
├─ PROGRESS_REPORT
├─ TASK_COMPLETE
├─ ERROR
└─ ...

FROM Task          TO Spawn
├─ PROGRESS_UPDATE
├─ MILESTONE_REACHED
├─ ERROR
└─ COMPLETION
```

---

## Memory路径速查

```
全局:     memory/global/context.md
项目:     memory/projects/{projectId}/config.json
任务:     memory/tasks/{taskId}/metadata.json

权限:     只能写自己的级别
继承:     Task → Project + Global (只读)
```

---

## Agent职责矩阵

| 职责 | Master | Spawn | Task |
|------|--------|-------|------|
| 用户交互 | ✅ | ❌ | ❌ |
| 项目管理 | ✅ | ❌ | ❌ |
| 任务分配 | ❌ | ✅ | ❌ |
| 进度跟进 | ❌ | ✅ | ❌ |
| 代码生成 | ❌ | ❌ | ✅ |
| 调试修复 | ❌ | ❌ | ✅ |

---

## API速查

```typescript
// Agent Runtime
agentRuntime.forkAgent(config)
agentRuntime.spawnAgent(type, projectId)
agentRuntime.terminateAgent(agentId)
agentRuntime.getAgentStatus(agentId)

// Memory
memory.read(path)
memory.write(path, content)
memory.append(path, entry)
memory.setupInheritance(childId, parentId)

// Skills Registry
skillsRegistry.register(skill, scope)
skillsRegistry.loadSkills(agentId)
skillsRegistry.executeSkill(agentId, name, args)

// Message Bus
messageBus.send({ from, to, type, payload })
messageBus.subscribe(agentId, handler)

// Project Manager
projectManager.createProject(config)
projectManager.getProject(projectId)
projectManager.listProjects()
projectManager.deleteProject(projectId)
```

---

## 权限速查表

| 操作 | Global | Project | Task |
|------|--------|---------|------|
| Master Read | ✅ | ✅ | ❌ |
| Master Write | ✅ | ❌ | ❌ |
| Spawn Read | ✅ | ✅ | ✅ |
| Spawn Write | ❌ | ✅ | ❌ |
| Task Read | ✅ | ✅ | ✅ |
| Task Write | ❌ | ❌ | ✅ |

---

## 实现路线图

```
Week 1-2:  □ Agent Runtime  □ 通信系统  □ Memory
Week 3-4:  □ Master Agent   □ 项目管理
Week 5-7:  □ Spawn Agent    □ 任务管理
Week 8-10: □ Task Agent     □ 集成测试
Week 11-12: □ 优化上线
```

---

## 关键参数

| 参数 | 值 |
|------|-----|
| 消息延迟目标 | < 100ms |
| Memory读写 | < 100ms |
| Agent启动时间 | < 200ms |
| 支持Spawn数量 | 20+ 并发 |
| 支持Task数量 | 100+ 并发 |
| 消息吞吐量 | 1000+ msg/sec |

---

## 常见命令

```bash
# 查看所有Agent
agentRuntime.listActiveAgents()

# 获取项目进度
memory.read('projects/{projectId}/progress.md')

# 监听消息
messageBus.subscribe(agentId, (msg) => {})

# 查询Memory
memory.search('pattern')

# 执行Skill
skillsRegistry.executeSkill('agent-id', 'skillName', args)
```

---

## 错误代码速查

| 代码 | 含义 | 解决 |
|------|------|------|
| E001 | Agent启动失败 | 检查Worker进程 |
| E002 | Memory权限不足 | 检查权限配置 |
| E003 | 消息路由失败 | 确认目标Agent活跃 |
| E004 | Skill加载失败 | 检查Skill注册 |
| E005 | 项目不存在 | 确认projectId |

---

## 调试技巧

```javascript
// 打印Agent状态
console.log(agentRuntime.getAgentStatus(agentId))

// 查看Memory内容
const content = await memory.read('path')
console.log(JSON.stringify(content, null, 2))

// 监听所有消息
messageBus.subscribe('*', (msg) => console.log(msg))

// 查看继承链
console.log(await memory.getInheritedMemory(agentId))

// 获取Memory统计
console.log(await memory.getStatistics())
```

---

## 文件位置速查

```
源代码:
  src/agent/runtime/
  src/agent/communication/
  src/agent/memory/
  src/agent/skills/
  src/agents/master/
  src/agents/spawn/
  src/agents/task/

文档:
  docs/architecture/2026-04-19-multi-agent-framework/

测试:
  tests/unit/
  tests/integration/
  tests/e2e/
```

---

## Agent生命周期

```
IDLE
  ↓ fork/spawn
INITIALIZING
  ↓
RUNNING
  ├─ WORKING
  ├─ WAITING
  └─ BLOCKED
  ↓ error
ERRORED
  ↓ recover
RUNNING
  ↓ complete
COMPLETING
  ↓
TERMINATED
```

---

## 相关文档链接

| 文档 | 用途 | 位置 |
|------|------|------|
| OVERVIEW | 架构总体 | 01-OVERVIEW.md |
| AGENT-ROLES | 职责详解 | 02-AGENT-ROLES.md |
| MEMORY-SYSTEM | Memory详设 | 03-MEMORY-SYSTEM.md |
| IMPLEMENTATION | 代码示例 | 07-IMPLEMENTATION-GUIDE.md |
| API-DESIGN | 接口定义 | 09-API-DESIGN.md |
| PHASE-BREAKDOWN | 项目规划 | 10-PHASE-BREAKDOWN.md |

---

**打印后贴在办公桌上！** 📌

---

最后更新: 2026-04-19
