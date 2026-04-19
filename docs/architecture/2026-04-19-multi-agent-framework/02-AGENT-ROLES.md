---
title: Agent角色和职责定义
version: 1.0.0
date: 2026-04-19
---

# 2️⃣ Agent角色和职责定义

## 📖 章节概览

本章定义系统中三层Agent的具体角色、职责、生命周期、以及它们之间的关系。

---

## 2.1 L1: Master Agent (全局协调层)

### 2.1.1 基本信息

| 属性 | 值 |
|------|-----|
| **层级** | L1 (顶层) |
| **数量** | 1个 (单例) |
| **生命周期** | 进程级 (应用启动到关闭) |
| **作用域** | 全局 |
| **启动时机** | 应用启动 |
| **终止时机** | 应用关闭 |
| **Memory类型** | 全局共享库 |
| **Skills类型** | 全局基础Skills |

### 2.1.2 核心职责

#### ✅ 用户交互处理
```typescript
// 1. 接收用户命令
master.on('userCommand', async (cmd) => {
  // 2. 解析并验证
  const request = parseCommand(cmd)

  // 3. 路由到对应处理器
  const result = await router.handle(request)

  // 4. 格式化响应给UI
  return formatResponse(result)
})
```

**具体操作**:
- 接收来自UI的命令
- 验证用户权限
- 解析并标准化请求
- 调度给对应Handler
- 返回结果给UI

#### ✅ 项目生命周期管理
```typescript
// 创建项目
async createProject(projectConfig) {
  // 1. 验证配置
  validate(projectConfig)

  // 2. 创建项目记录
  const project = await projectManager.create(projectConfig)

  // 3. Fork Spawn Agent
  const spawnAgent = await forkSpawnAgent(project.id)

  // 4. 保存映射关系
  projectSpawnMapping.set(project.id, spawnAgent.id)

  // 5. 返回项目信息
  return project
}

// 删除项目
async deleteProject(projectId) {
  // 1. 关闭对应的Spawn Agent
  const spawnId = projectSpawnMapping.get(projectId)
  await terminateAgent(spawnId)

  // 2. 清理项目Memory
  await memorySystem.clearMemory(`projects/${projectId}`)

  // 3. 删除项目记录
  await projectManager.delete(projectId)
}
```

**具体操作**:
- 创建新项目并Fork Spawn Agent
- 删除项目并清理相关Spawn Agent
- 列出所有项目和状态
- 查询项目详情
- 更新项目配置

#### ✅ 需求记录和展示
```typescript
// 记录用户需求
async recordRequirement(projectId, requirement) {
  // 1. 添加到全局需求列表
  await globalMemory.append('requirements.md', {
    id: generateId(),
    projectId,
    content: requirement,
    timestamp: Date.now(),
    status: 'pending'
  })

  // 2. 转发给对应的Spawn Agent
  const spawnId = projectSpawnMapping.get(projectId)
  await messageBus.send({
    from: 'master',
    to: spawnId,
    type: MessageType.NEW_REQUIREMENT,
    payload: requirement
  })
}

// 展示需求
async listRequirements(projectId) {
  if (projectId) {
    // 查看特定项目的需求
    return await projectMemory.read(`projects/${projectId}/requirements.md`)
  } else {
    // 查看所有需求
    return await globalMemory.read('requirements.md')
  }
}
```

**具体操作**:
- 记录新的用户需求
- 跟踪需求状态 (pending/in-progress/completed)
- 展示需求历史
- 需求的优先级管理

#### ✅ Spawn Agent 的 Fork 和管理
```typescript
// Fork Spawn Agent
async forkSpawnAgent(projectId, projectConfig) {
  // 1. 准备Agent配置
  const agentConfig = {
    type: 'spawn',
    parent: 'master',
    projectId,
    name: `spawn-${projectId}`,
    memory: `memory/projects/${projectId}`,
    inherits: ['global/*']
  }

  // 2. 通过Runtime fork
  const spawnInstance = await agentRuntime.forkAgent(agentConfig)

  // 3. 初始化项目级Memory
  await memorySystem.setupProjectMemory(projectId, projectConfig)

  // 4. 建立消息通道
  await messageBus.subscribe(spawnInstance.id, handleSpawnMessage)

  // 5. 通知Spawn Agent已启动
  await messageBus.send({
    from: 'master',
    to: spawnInstance.id,
    type: MessageType.AGENT_STARTED,
    payload: { projectId, config: projectConfig }
  })

  return spawnInstance
}

// 监听所有Spawn Agent的消息
function handleSpawnMessage(message) {
  switch(message.type) {
    case MessageType.PROGRESS_UPDATE:
      // 更新UI上的进度
      uiBus.emit('progress', message.payload)
      break
    case MessageType.TASK_COMPLETE:
      // 任务完成通知
      recordTaskCompletion(message)
      break
    case MessageType.ERROR:
      // 错误处理
      handleError(message)
      break
  }
}
```

**具体操作**:
- 为每个新项目Fork一个Spawn Agent
- 维护Project<->SpawnAgent的映射
- 监听所有Spawn Agent的状态更新
- 处理Spawn Agent的故障和恢复

#### ✅ 全局Memory与Skills管理
```typescript
// 全局Memory维护
async maintainGlobalMemory() {
  // 定期更新全局统计
  const stats = {
    totalProjects: await projectManager.count(),
    activeSpawnAgents: agentRuntime.listActiveAgents()
      .filter(a => a.type === 'spawn').length,
    completedTasks: await globalMemory.read('completed_tasks.md'),
    timestamp: Date.now()
  }

  await globalMemory.write('stats.md', stats)
}

// 全局Skills管理
async manageGlobalSkills() {
  // 注册核心Skills供所有Agent使用
  skillsRegistry.register(new ProjectManagementSkill(), 'global')
  skillsRegistry.register(new CommunicationSkill(), 'global')
  skillsRegistry.register(new ContextSharingSkill(), 'global')

  // 定期检查Skills版本
  // 更新Skills如需
}
```

**具体操作**:
- 管理全局Memory库
- 注册和维护全局Skills
- 更新全局统计和日志
- 确保Memory一致性

### 2.1.3 不做什么 ❌

Master Agent **不负责**:
- ❌ 编码或调试 (由Task Agent做)
- ❌ 代码的生成和修改 (由CodingAgent做)
- ❌ 具体项目的进度跟进细节 (由Spawn Agent做)
- ❌ 问题诊断和修复 (由DebugAgent做)
- ❌ 存储临时任务数据 (由Task Agent的临时Memory做)

### 2.1.4 工作流程图

```
User
  │
  ├─ 创建项目
  │   └─→ 验证 → ProjectManager → Fork Spawn → 初始化Memory → 返回确认
  │
  ├─ 删除项目
  │   └─→ 验证 → Terminate Spawn → 清理Memory → 删除记录 → 返回确认
  │
  ├─ 列出项目
  │   └─→ ProjectManager → 返回项目列表
  │
  ├─ 提交需求
  │   └─→ 验证 → 记录到全局 → 转发给Spawn → 返回确认
  │
  └─ 查看进度
      └─→ 汇聚所有Spawn的消息 → 聚合展示 → 返回状态

Master 监听消息
  │
  ├─ 来自Spawn的进度更新 → 转发给UI
  ├─ 来自Spawn的错误 → 处理并通知用户
  └─ 来自UI的新命令 → 路由处理
```

---

## 2.2 L2: Spawn Agent (项目协调层)

### 2.2.1 基本信息

| 属性 | 值 |
|------|-----|
| **层级** | L2 (中间层) |
| **数量** | 1..N 个 (每个项目一个) |
| **生命周期** | 项目级 (项目创建到删除) |
| **作用域** | 项目级 |
| **启动时机** | 项目被创建 (由Master fork) |
| **终止时机** | 项目被删除 (由Master terminate) |
| **Memory类型** | 项目级 + 继承全局 |
| **Skills类型** | 项目级 + 继承全局 |

### 2.2.2 核心职责

#### ✅ 项目上下文维护
```typescript
class SpawnAgent extends Agent {
  projectId: string
  projectMemory: ProjectMemory

  async initialize() {
    // 1. 加载项目配置
    this.projectMemory = await memorySystem
      .setupInheritance(this.id, 'master')
      .then(mem => mem.loadProject(this.projectId))

    // 2. 恢复项目历史
    this.history = await this.projectMemory.read('project_history.md')

    // 3. 恢复进度状态
    this.currentTasks = await this.projectMemory.read('current_tasks.md')

    // 4. 准备就绪
    this.status = 'ready'
  }

  async maintainContext() {
    // 定期更新项目上下文
    setInterval(async () => {
      await this.projectMemory.write('last_updated.md', {
        timestamp: Date.now(),
        activeTasks: this.activeTasks.length,
        completedTasks: this.completedTasks.length,
        status: this.status
      })
    }, 60000) // 每分钟更新一次
  }
}
```

**具体操作**:
- 加载和维护项目配置
- 保存项目历史和变更记录
- 维护项目的当前状态
- 恢复长中断后的项目状态

#### ✅ 用户需求接收和理解
```typescript
class SpawnAgent extends Agent {
  async receiveRequirement(requirement: string) {
    // 1. 记录需求到项目Memory
    await this.projectMemory.append('requirements_log.md', {
      id: generateId(),
      content: requirement,
      receivedAt: Date.now(),
      status: 'pending'
    })

    // 2. 分析需求的复杂度
    const complexity = await this.analyzeComplexity(requirement)

    // 3. 分解为子任务
    const subtasks = await this.decomposeTasks(requirement, complexity)

    // 4. 保存任务分解结果
    await this.projectMemory.write('tasks_breakdown.md', {
      requirementId: requirement.id,
      subtasks: subtasks,
      estimatedDuration: complexity.duration,
      breakdown_time: Date.now()
    })

    // 5. 返回确认给Master
    return {
      status: 'received',
      taskCount: subtasks.length,
      estimatedDuration: complexity.duration
    }
  }

  async analyzeComplexity(requirement: string): Promise<Complexity> {
    // 使用LLM分析需求复杂度
    // 返回预估时间、需要的Skills、可能的问题
  }

  async decomposeTasks(requirement: string, complexity: Complexity) {
    // 将大需求分解为小任务
    // 返回有序的子任务列表
  }
}
```

**具体操作**:
- 接收来自Master的用户需求
- 理解需求的背景和上下文
- 记录需求到项目Memory
- 对需求进行反馈和澄清

#### ✅ 工作分配和任务管理
```typescript
class SpawnAgent extends Agent {
  taskQueue: TaskQueue = new TaskQueue()

  async planAndAllocate() {
    // 1. 优先级排序
    const prioritizedTasks = this.taskQueue.sort()

    // 2. 为每个任务选择合适的Agent类型
    for (const task of prioritizedTasks) {
      const agentType = this.selectAgentType(task)
      // CodingAgent for coding tasks
      // DebugAgent for debugging tasks
      // TestAgent for testing tasks

      // 3. Fork Task Agent
      const taskAgent = await this.forkTaskAgent(agentType, task)

      // 4. 记录分配信息
      await this.projectMemory.append('task_allocation.md', {
        taskId: task.id,
        agentType: agentType,
        agentId: taskAgent.id,
        allocatedAt: Date.now(),
        estimatedDuration: task.duration
      })
    }
  }

  selectAgentType(task: Task): AgentType {
    if (task.type === 'coding') return 'CodingAgent'
    if (task.type === 'debugging') return 'DebugAgent'
    if (task.type === 'testing') return 'TestAgent'
    return 'TaskAgent'
  }

  async forkTaskAgent(agentType: AgentType, task: Task) {
    const config = {
      type: agentType,
      parent: this.id,
      taskId: task.id,
      projectId: this.projectId,
      memory: `memory/tasks/${task.id}`,
      context: {
        projectContext: await this.projectMemory.getContext(),
        taskContext: task,
        requirements: await this.projectMemory.read('requirements.md')
      }
    }

    return await agentRuntime.spawnAgent(config)
  }
}
```

**具体操作**:
- 对任务进行优先级排序
- 为任务分配合适的Agent类型
- Fork短期的Task Agent
- 跟踪任务分配和进度

#### ✅ 任务进度跟进
```typescript
class SpawnAgent extends Agent {
  async trackTaskProgress(taskAgent: AgentInstance) {
    // 订阅Task Agent的进度消息
    await messageBus.subscribe(taskAgent.id, (message) => {
      switch(message.type) {
        case MessageType.PROGRESS_UPDATE:
          this.handleProgressUpdate(taskAgent.id, message.payload)
          break
        case MessageType.MILESTONE_REACHED:
          this.handleMilestone(taskAgent.id, message.payload)
          break
        case MessageType.BLOCKED:
          this.handleBlocked(taskAgent.id, message.payload)
          break
        case MessageType.ERROR:
          this.handleTaskError(taskAgent.id, message.payload)
          break
      }
    })
  }

  async handleProgressUpdate(taskAgentId: string, progress: Progress) {
    // 1. 更新项目进度
    await this.projectMemory.append('progress_log.md', {
      taskAgentId,
      progress,
      timestamp: Date.now()
    })

    // 2. 转发给Master (可选，影响UI)
    await messageBus.send({
      from: this.id,
      to: 'master',
      type: MessageType.PROGRESS_UPDATE,
      payload: {
        projectId: this.projectId,
        progress: progress
      }
    })

    // 3. 如果有障碍，采取行动
    if (progress.blockedBy) {
      await this.resolveBlockage(progress.blockedBy, taskAgentId)
    }
  }

  async handleTaskError(taskAgentId: string, error: Error) {
    // 1. 记录错误
    await this.projectMemory.append('error_log.md', {
      taskAgentId,
      error: error.message,
      stack: error.stack,
      timestamp: Date.now()
    })

    // 2. 分析是否可以恢复
    const canRecover = await this.analyzeRecoverability(error)

    // 3. 决定是否重试或升级
    if (canRecover) {
      await this.retryTask(taskAgentId)
    } else {
      await this.escalateError(error, taskAgentId)
    }
  }
}
```

**具体操作**:
- 监听Task Agent的进度消息
- 实时更新项目进度
- 处理任务中的错误和障碍
- 必要时重试或升级问题

#### ✅ 任务完成和清理
```typescript
class SpawnAgent extends Agent {
  async onTaskComplete(taskAgentId: string, result: TaskResult) {
    // 1. 收集任务结果
    const taskId = result.taskId
    const summary = {
      taskId,
      agentId: taskAgentId,
      status: 'completed',
      result: result,
      completedAt: Date.now(),
      duration: result.duration
    }

    // 2. 保存结果到项目Memory
    await this.projectMemory.write(
      `completed_tasks/${taskId}/result.md`,
      summary
    )

    // 3. 合并生成的代码等工件
    if (result.artifacts) {
      for (const [path, content] of Object.entries(result.artifacts)) {
        await this.projectMemory.write(`artifacts/${path}`, content)
      }
    }

    // 4. 关闭Task Agent
    await agentRuntime.terminateAgent(taskAgentId)

    // 5. 清理临时Memory
    await memorySystem.clearMemory(`memory/tasks/${taskId}`)

    // 6. 从队列中移除
    this.taskQueue.remove(taskId)

    // 7. 更新项目状态
    await this.updateProjectStatus()

    // 8. 如果所有任务完成，通知Master
    if (this.taskQueue.isEmpty()) {
      await messageBus.send({
        from: this.id,
        to: 'master',
        type: MessageType.ALL_TASKS_COMPLETE,
        payload: { projectId: this.projectId }
      })
    }
  }
}
```

**具体操作**:
- 收集Task Agent的执行结果
- 保存完成的任务到项目Memory
- 合并生成的代码工件
- 清理Task Agent的临时资源
- 更新项目整体状态

#### ✅ 反馈和报告生成
```typescript
class SpawnAgent extends Agent {
  async generateProgressReport(): Promise<ProgressReport> {
    return {
      projectId: this.projectId,
      generatedAt: Date.now(),
      summary: {
        totalTasks: this.totalTaskCount,
        completedTasks: this.completedTaskCount,
        inProgressTasks: this.inProgressTaskCount,
        failedTasks: this.failedTaskCount,
        completionPercentage: this.calculateCompletion()
      },
      timeline: {
        started: this.projectStartTime,
        lastUpdated: this.lastUpdateTime,
        estimatedCompletion: this.estimateCompletionTime()
      },
      issues: {
        blockedTasks: await this.projectMemory.read('blocked_tasks.md'),
        errors: await this.projectMemory.read('error_log.md'),
        warnings: await this.projectMemory.read('warnings.md')
      },
      nextSteps: this.planNextSteps(),
      recommendations: await this.generateRecommendations()
    }
  }

  async sendFeedbackToMaster() {
    const report = await this.generateProgressReport()

    await messageBus.send({
      from: this.id,
      to: 'master',
      type: MessageType.PROGRESS_REPORT,
      payload: report
    })
  }
}
```

**具体操作**:
- 生成进度报告
- 汇总完成情况、问题和建议
- 定期发送反馈给Master和用户
- 识别风险和机遇

### 2.2.3 不做什么 ❌

Spawn Agent **不负责**:
- ❌ 实际编码工作 (由CodingAgent做)
- ❌ 调试和问题修复 (由DebugAgent做)
- ❌ 直接与用户交互 (由Master做)
- ❌ 跨项目协调 (由Master做)

### 2.2.4 工作流程图

```
Master → Fork Spawn Agent
  │
  ├─ 初始化 (加载Memory、配置)
  │
  ├─ 监听来自Master的需求
  │   └─→ 分解任务 → 加入队列 → 规划执行
  │
  ├─ 定期循环
  │   ├─ 检查队列中的任务
  │   ├─ 选择合适的Agent类型
  │   ├─ Fork Task Agent执行
  │   │
  │   └─ 监听Task Agent的进度
  │       ├─ 进度更新 → 记录并转发
  │       ├─ 任务完成 → 收集结果 → 清理 → 从队列移除
  │       └─ 任务错误 → 处理并记录
  │
  ├─ 定期反馈
  │   └─→ 生成报告 → 发送给Master
  │
  └─ 终止 (由Master删除项目触发)
      └─→ 关闭所有Task Agent → 清理资源 → 保存最终状态
```

---

## 2.3 L3: Task Agent (任务执行层)

### 2.3.1 基本信息

| 属性 | 值 |
|------|-----|
| **层级** | L3 (底层) |
| **数量** | 可变 (随需创建) |
| **子类型** | CodingAgent, DebugAgent, TestAgent等 |
| **生命周期** | 任务级 (任务开始到完成) |
| **作用域** | 单个任务 |
| **启动时机** | Spawn Agent fork (任务开始) |
| **终止时机** | 任务完成或失败 (由Spawn Agent terminate) |
| **Memory类型** | 临时任务级 + 继承项目级和全局 |
| **Skills类型** | 任务级 + 继承 |

### 2.3.2 通用职责

所有Task Agent共同的职责:

#### ✅ 执行分配的任务
```typescript
abstract class TaskAgent extends Agent {
  taskId: string
  projectId: string

  async execute(): Promise<TaskResult> {
    try {
      // 1. 验证输入
      await this.validateInput()

      // 2. 初始化工作环境
      await this.initializeWorkspace()

      // 3. 执行任务逻辑 (由子类实现)
      const result = await this.performTask()

      // 4. 验证输出
      await this.validateOutput(result)

      // 5. 返回结果
      return result
    } catch (error) {
      // 错误处理
      await this.handleTaskError(error)
      throw error
    }
  }

  abstract async performTask(): Promise<TaskResult>
}
```

#### ✅ 进度报告
```typescript
class TaskAgent extends Agent {
  async reportProgress(percentage: number, message: string) {
    await messageBus.send({
      from: this.id,
      to: this.parentId, // Spawn Agent
      type: MessageType.PROGRESS_UPDATE,
      payload: {
        taskId: this.taskId,
        progress: percentage,
        message: message,
        timestamp: Date.now()
      }
    })
  }

  async reportMilestone(milestone: string, details: any) {
    await messageBus.send({
      from: this.id,
      to: this.parentId,
      type: MessageType.MILESTONE_REACHED,
      payload: {
        taskId: this.taskId,
        milestone: milestone,
        details: details,
        timestamp: Date.now()
      }
    })
  }
}
```

#### ✅ 上下文继承和使用
```typescript
class TaskAgent extends Agent {
  contextChain: ContextChain

  async setupContext() {
    // 1. 加载全局上下文 (只读)
    const globalContext = await memorySystem
      .read('memory/global/context.md')

    // 2. 加载项目上下文 (只读)
    const projectContext = await memorySystem
      .read(`memory/projects/${this.projectId}/context.md`)

    // 3. 初始化任务上下文 (读写)
    const taskContext = await memorySystem
      .write(`memory/tasks/${this.taskId}/context.md`, {
        taskId: this.taskId,
        projectId: this.projectId,
        startTime: Date.now(),
        executionLog: []
      })

    // 4. 组建上下文链
    this.contextChain = {
      global: globalContext,
      project: projectContext,
      task: taskContext,
      query: (key: string) => {
        // 优先查询任务级，然后项目级，最后全局
        return this.contextChain.task[key]
          || this.contextChain.project[key]
          || this.contextChain.global[key]
      }
    }
  }

  // 使用上下文
  async getProjectInfo(key: string) {
    return this.contextChain.query(key)
  }
}
```

#### ✅ 错误处理
```typescript
class TaskAgent extends Agent {
  async handleTaskError(error: Error) {
    // 1. 记录错误到临时Memory
    await this.taskMemory.append('errors.md', {
      error: error.message,
      stack: error.stack,
      timestamp: Date.now(),
      context: await this.getErrorContext()
    })

    // 2. 通知Spawn Agent
    await messageBus.send({
      from: this.id,
      to: this.parentId,
      type: MessageType.ERROR,
      payload: {
        taskId: this.taskId,
        error: error.message,
        recoverable: this.isRecoverable(error),
        context: await this.getErrorContext()
      }
    })

    // 3. 尝试恢复 (如果可能)
    if (this.isRecoverable(error)) {
      await this.attemptRecovery()
    }
  }

  private isRecoverable(error: Error): boolean {
    // 业务逻辑判断是否可恢复
  }

  private async attemptRecovery() {
    // 恢复逻辑
  }
}
```

#### ✅ 资源清理
```typescript
class TaskAgent extends Agent {
  async cleanup() {
    // 1. 关闭所有打开的文件和连接
    await this.closeAllResources()

    // 2. 清理临时文件
    await this.cleanupTempFiles()

    // 3. 记录任务完成状态到Memory
    await this.taskMemory.write('completion.md', {
      taskId: this.taskId,
      status: 'completed',
      completedAt: Date.now(),
      duration: this.getDuration(),
      statistics: this.getStatistics()
    })

    // 4. 通知父Agent (Spawn)
    // 由Spawn Agent的监听器处理自动cleanup
  }
}
```

### 2.3.3 特定Agent类型

#### CodingAgent (代码生成Agent)

**专责**:
- 代码生成
- 文件创建和修改
- 代码复查和优化

```typescript
class CodingAgent extends TaskAgent {
  async performTask(): Promise<TaskResult> {
    const { codeRequirement, relatedFiles } = this.taskContext

    // 1. 分析需求
    const analysis = await this.analyzeRequirement(codeRequirement)

    // 2. 查看相关文件
    const context = await this.reviewRelatedFiles(relatedFiles)

    // 3. 生成代码
    this.reportProgress(25, '开始生成代码')
    const generatedCode = await this.generateCode(analysis, context)
    this.reportProgress(50, '代码生成完成')

    // 4. 代码审查
    this.reportProgress(75, '进行代码审查')
    const reviewed = await this.reviewCode(generatedCode)

    // 5. 提交生成物
    this.reportProgress(100, '任务完成')
    return {
      taskId: this.taskId,
      status: 'success',
      artifacts: {
        'generated_code.ts': reviewed,
        'code_explanation.md': analysis.explanation,
        'test_cases.ts': await this.generateTestCases(reviewed)
      },
      duration: this.getDuration()
    }
  }

  async generateCode(analysis: Analysis, context: Context): Promise<string> {
    // 使用LLM生成代码
  }

  async reviewCode(code: string): Promise<string> {
    // 审查并改进代码
  }
}
```

#### DebugAgent (调试Agent)

**专责**:
- 问题诊断
- Bug修复
- 测试验证

```typescript
class DebugAgent extends TaskAgent {
  async performTask(): Promise<TaskResult> {
    const { issue, affectedFiles } = this.taskContext

    // 1. 复现问题
    this.reportProgress(20, '正在复现问题')
    const reproduction = await this.reproduceIssue(issue)

    // 2. 诊断根因
    this.reportProgress(40, '进行根因分析')
    const diagnosis = await this.diagnoseRootCause(reproduction)

    // 3. 生成修复
    this.reportProgress(60, '生成修复方案')
    const fix = await this.generateFix(diagnosis)

    // 4. 验证修复
    this.reportProgress(80, '验证修复')
    const verified = await this.verifyFix(fix)

    // 5. 返回结果
    this.reportProgress(100, '调试完成')
    return {
      taskId: this.taskId,
      status: verified ? 'success' : 'failed',
      artifacts: {
        'diagnosis.md': diagnosis.report,
        'fix.patch': fix,
        'test_verification.md': verified.report
      },
      duration: this.getDuration()
    }
  }
}
```

### 2.3.4 生命周期

```
Fork (Spawn创建)
  │
  ├─ 初始化 (准备环境、加载上下文)
  │
  ├─ 执行 (performTask)
  │   ├─ 定期reportProgress
  │   ├─ 遇到问题时报告错误
  │   └─ 完成后返回结果
  │
  ├─ 清理 (关闭资源)
  │
  └─ Terminate (由Spawn删除)
      └─ 内存被自动清理
```

---

## 2.4 Agent间的关系矩阵

| 关系 | Master | Spawn | Task |
|------|--------|-------|------|
| **Master** | - | Fork (1:N) | - |
| **Spawn** | Parent | Sibling (N:N) | Fork (1:M) |
| **Task** | - | Parent | Sibling (M:M) |

---

## 2.5 通信模式

| From | To | Message Type | Content | Frequency |
|------|-----|--------------|---------|-----------|
| Spawn | Master | PROGRESS_REPORT | 进度/完成情况 | 每5分钟或事件驱动 |
| Task | Spawn | PROGRESS_UPDATE | 任务进度 | 每分钟或按需 |
| Task | Spawn | MILESTONE_REACHED | 里程碑事件 | 按需 |
| Task | Spawn | ERROR | 错误信息 | 即时 |
| Master | Spawn | NEW_REQUIREMENT | 新需求 | 按需 |
| Master | Spawn | CONFIG_UPDATE | 配置变更 | 按需 |

---

## 🔗 相关文档

- [OVERVIEW.md](./01-OVERVIEW.md) - 架构总体
- [LIFECYCLE.md](./06-LIFECYCLE.md) - 生命周期管理
- [COMMUNICATION.md](./05-COMMUNICATION.md) - 通信协议
- [IMPLEMENTATION-GUIDE.md](./07-IMPLEMENTATION-GUIDE.md) - 代码实现

---

## 📝 总结

| Agent | 创建者 | 职责 | 生命周期 |
|-------|--------|------|--------|
| Master | App启动 | 协调、交互、项目管理 | 全局 |
| Spawn | Master | 项目跟进、任务分配 | 项目级 |
| Task | Spawn | 具体工作执行 | 任务级 |
