---
title: Memory系统详细设计
version: 1.0.0
date: 2026-04-19
---

# 3️⃣ Memory系统详细设计

## 📖 章节概览

本章详细设计Arduino Tools的Memory系统，包括存储结构、继承机制、访问控制和性能考虑。

---

## 3.1 Memory系统概览

### 3.1.1 核心特性

```
分层存储
  ├─ Global (全局) - Master专用
  ├─ Project (项目级) - Spawn + Task共享
  └─ Task (任务级) - Task临时

继承链
  └─ Task继承 ← Project + Global

访问控制
  ├─ 读权限: 可继承下级可读上级
  └─ 写权限: 只能写自己的级别

持久化
  ├─ Global & Project: 文件系统 (永久)
  └─ Task: 内存 + 临时文件 (任务后清理)
```

### 3.1.2 Memory vs Context

| 属性 | Memory | Context |
|------|--------|---------|
| 定义 | 持久化的知识库 | 临时的执行环境 |
| 存储 | 文件系统 | 内存 |
| 生命周期 | 长期 | 任务期 |
| 典型内容 | 需求、决策、代码 | 当前变量、状态 |

---

## 3.2 存储结构设计

### 3.2.1 全局Memory (Global)

```
memory/global/
├── README.md                    # Memory系统说明
├── context.md                   # 全局背景信息
├── requirements.md              # 所有项目的需求汇总
├── completed_tasks.md           # 完成任务的索引
├── statistics.md                # 全局统计数据
├── patterns/                    # 设计模式库
│   ├── architecture.md
│   ├── communication.md
│   └── error_handling.md
├── skills_inventory.md          # Skills清单和文档
├── agent_registry.md            # 当前活跃Agent列表
└── changelog.md                 # 系统变更日志
```

**主要内容示例**:

```markdown
# memory/global/context.md

## Arduino Tools 项目背景

- **项目名称**: Arduino Tools
- **目标**: 提供虚拟Arduino模拟和编程工具
- **架构**: 三层Agent框架 (Master/Spawn/Task)
- **用户群体**: Arduino爱好者、学生、开发者

## 核心技术栈

- Frontend: React (Tauri)
- Backend: Node.js
- Simulation: Virtual Machine
- Communication: IPC + Message Queue

## 关键决策

1. 采用消息驱动的异步通信
2. 文件驱动的Memory持久化
3. Worker进程隔离

## 常见问题和解决方案

...
```

### 3.2.2 项目级Memory (Project)

```
memory/projects/{projectId}/
├── config.json                  # 项目配置
├── metadata.json                # 项目元数据
├── README.md                    # 项目说明
├── context.md                   # 项目专属背景
├── requirements.md              # 项目的需求
├── requirements_log.md          # 需求接收日志
├── tasks_breakdown.md           # 需求分解
├── task_allocation.md           # 任务分配记录
├── progress.md                  # 项目进度
├── decisions.md                 # 项目决策日志
├── architecture.md              # 项目架构设计
├── code_style.md                # 代码规范
├── error_log.md                 # 错误日志
├── performance_notes.md         # 性能笔记
├── completed_tasks/
│   ├── task-001/
│   │   ├── result.md            # 任务结果总结
│   │   ├── execution_log.md     # 执行日志
│   │   └── artifacts/           # 生成物
│   │       ├── generated_code.ts
│   │       └── ...
│   └── task-002/
│       └── ...
├── blocked_tasks.md             # 阻止列表
├── artifacts/                   # 所有生成物
│   ├── src/
│   ├── tests/
│   └── docs/
└── history/                     # 版本历史
    ├── 2026-04-19-initial.md
    └── ...
```

**项目配置示例**:

```json
// memory/projects/{projectId}/config.json
{
  "projectId": "project-001",
  "name": "Arduino Simulator - Core Features",
  "description": "实现基础的Arduino虚拟模拟功能",
  "createdAt": "2026-04-19T10:00:00Z",
  "owner": "user-123",
  "status": "active",
  "priority": "high",
  "estimatedDuration": "2 weeks",
  "technologies": ["Node.js", "React", "Tauri"],
  "team": ["master-agent", "spawn-agent-001"],
  "dependencies": [],
  "tags": ["simulation", "core", "hardware"]
}
```

**项目进度示例**:

```markdown
# memory/projects/{projectId}/progress.md

## 项目进度概览

- **创建时间**: 2026-04-19
- **最后更新**: 2026-04-19 15:30 UTC
- **完成度**: 25% (5/20 tasks)

## 当前状态

- **总任务数**: 20
- **已完成**: 5
- **进行中**: 3
- **待处理**: 12
- **阻止**: 0

## 时间线

| 阶段 | 开始时间 | 预期完成 | 实际完成 | 状态 |
|------|---------|---------|---------|------|
| 需求分析 | 2026-04-19 | 2026-04-20 | - | 进行中 |
| 架构设计 | 2026-04-20 | 2026-04-22 | - | 等待 |
| 核心开发 | 2026-04-23 | 2026-05-03 | - | 等待 |
| 测试 | 2026-05-04 | 2026-05-10 | - | 等待 |

## 最近完成的任务

- task-001: 项目初始化
- task-002: 需求整理
- ...

## 当前焦点

正在分解用户需求为具体任务...
```

### 3.2.3 任务级Memory (Task)

```
memory/tasks/{taskId}/
├── metadata.json                # 任务元数据
├── task_context.json            # 任务执行上下文
├── execution_log.md             # 执行日志 (实时更新)
├── progress.md                  # 进度状态
├── errors.md                    # 错误记录
├── decisions.md                 # 任务中的决策
├── completion.md                # 完成报告
├── artifacts/
│   ├── generated_code.ts
│   ├── test_cases.ts
│   └── ...
└── temp_files/                  # 临时文件 (任务后删除)
    └── ...
```

**任务元数据示例**:

```json
// memory/tasks/{taskId}/metadata.json
{
  "taskId": "task-001",
  "projectId": "project-001",
  "type": "coding",
  "agentType": "CodingAgent",
  "requirement": "实现Arduino LED控制模块",
  "createdAt": "2026-04-19T10:05:00Z",
  "startedAt": "2026-04-19T10:06:00Z",
  "completedAt": null,
  "estimatedDuration": "2 hours",
  "actualDuration": null,
  "status": "in_progress",
  "priority": "high",
  "parentSpawnAgent": "spawn-agent-001",
  "parentMasterAgent": "master-agent"
}
```

---

## 3.3 继承和访问控制

### 3.3.1 继承链

```
Global Memory
  └─ 由Master维护
  └─ 所有Agent都可读
  └─ 不可继承下级写入

Project Memory
  └─ 由Spawn维护
  ├─ 继承Global (只读)
  └─ Task可读(只读)
  └─ Task不可写

Task Memory
  └─ 由Task维护
  ├─ 继承Project (只读)
  ├─ 继承Global (只读)
  └─ 只有自己能写
```

### 3.3.2 权限矩阵

| Action | Global | Project | Task | 说明 |
|--------|--------|---------|------|------|
| **Master** | R/W | R | - | 只读Project以了解状态 |
| **Spawn** | R | R/W | R | 读Task的日志但不修改 |
| **Task** | R | R | R/W | 只写自己的Memory |

### 3.3.3 访问API实现

```typescript
interface Memory {
  // 基础读写
  read(path: string): Promise<any>
  write(path: string, content: any): Promise<void>
  append(path: string, entry: any): Promise<void>
  delete(path: string): Promise<void>

  // 继承管理
  setupInheritance(childAgent: string, parentAgent: string): void
  getInheritedValue(key: string): Promise<any>

  // 权限检查
  canRead(agentId: string, path: string): boolean
  canWrite(agentId: string, path: string): boolean

  // 查询
  search(pattern: string): Promise<string[]>
  listDirectory(path: string): Promise<string[]>
}

// 使用示例
class TaskAgent extends Agent {
  async useContext() {
    // 读全局Memory
    const globalContext = await this.memory.read('global/context.md')

    // 读项目Memory
    const projectConfig = await this.memory.read(
      `projects/${this.projectId}/config.json`
    )

    // 写任务Memory
    await this.memory.write(
      `tasks/${this.taskId}/execution_log.md`,
      'Task started at ' + new Date()
    )

    // 追加到日志
    await this.memory.append(
      `tasks/${this.taskId}/errors.md`,
      { error: 'Some error', timestamp: Date.now() }
    )
  }
}
```

---

## 3.4 Memory操作规范

### 3.4.1 文件格式

**Markdown文档** (用于人类可读内容):
```markdown
# 标题

## 部分1

内容...

### 子部分1.1

- 列表项1
- 列表项2

| 列 | 列 |
|----|-----|
| 值 | 值  |
```

**JSON配置** (用于结构化数据):
```json
{
  "key": "value",
  "nested": {
    "item": "value"
  }
}
```

**日志追加** (用于序列化事件):
```json
[
  { "timestamp": 1234567890, "event": "started", "details": {} },
  { "timestamp": 1234567891, "event": "progress", "details": { "percent": 50 } }
]
```

### 3.4.2 版本控制

Memory系统集成Git版本控制:

```typescript
class Memory {
  async write(path: string, content: any) {
    // 1. 写入文件
    fs.writeFileSync(path, serialize(content))

    // 2. Git commit
    const message = `Update ${path}`
    exec(`git add "${path}"`)
    exec(`git commit -m "${message}"`)
  }

  async getHistory(path: string): Promise<Commit[]> {
    // 获取文件变更历史
    return exec(`git log --oneline "${path}"`)
  }

  async revert(path: string, commitHash: string) {
    // 恢复到特定版本
    exec(`git checkout ${commitHash} "${path}"`)
  }
}
```

### 3.4.3 清理策略

```typescript
class Memory {
  async cleanup() {
    // 定期清理过期的临时Memory

    // 1. 清理完成超过30天的任务Memory
    const completedTasks = await this.listDirectory('tasks/')
    for (const taskId of completedTasks) {
      const completion = await this.read(`tasks/${taskId}/completion.md`)
      if (Date.now() - completion.completedAt > 30 * 24 * 60 * 60 * 1000) {
        await this.delete(`tasks/${taskId}`)
      }
    }

    // 2. 归档完成的项目
    const completedProjects = await this.getCompletedProjects()
    for (const projectId of completedProjects) {
      await this.archiveProject(projectId)
    }

    // 3. 压缩日志文件
    await this.compressLogs()
  }
}
```

---

## 3.5 搜索和查询

### 3.5.1 查询语言

```typescript
interface MemoryQuery {
  // 按路径搜索
  path?: string                // glob模式

  // 按内容搜索
  content?: string             // 正则表达式
  tags?: string[]             // 标签过滤

  // 按时间搜索
  after?: Date
  before?: Date

  // 结果限制
  limit?: number
  offset?: number
}

// 使用示例
const results = await memory.query({
  path: 'projects/*/completed_tasks/*',
  tags: ['bug-fix'],
  after: new Date('2026-04-01'),
  limit: 10
})
```

### 3.5.2 索引和缓存

```typescript
class Memory {
  private searchIndex: Map<string, SearchEntry[]> = new Map()

  async buildIndex() {
    // 构建全文搜索索引
    const documents = this.getAllDocuments()
    for (const doc of documents) {
      const tokens = tokenize(doc.content)
      for (const token of tokens) {
        if (!this.searchIndex.has(token)) {
          this.searchIndex.set(token, [])
        }
        this.searchIndex.get(token)!.push({
          path: doc.path,
          line: doc.lineNumber
        })
      }
    }
  }

  search(query: string): SearchResult[] {
    // 使用索引快速搜索
    const tokens = tokenize(query)
    const results = this.searchIndex.get(tokens[0]) || []
    return results.filter(r => matchesQuery(r, tokens))
  }
}
```

---

## 3.6 性能考虑

### 3.6.1 大文件处理

```typescript
class Memory {
  // 流式读取大文件
  async *readStream(path: string) {
    const stream = fs.createReadStream(path)
    for await (const chunk of stream) {
      yield chunk
    }
  }

  // 流式写入大文件
  async writeStream(path: string, readableStream: Stream) {
    return new Promise((resolve, reject) => {
      readableStream.pipe(fs.createWriteStream(path))
        .on('finish', resolve)
        .on('error', reject)
    })
  }
}
```

### 3.6.2 缓存策略

```typescript
class Memory {
  private cache: Map<string, { data: any, timestamp: number }> = new Map()
  private cacheTTL = 5 * 60 * 1000 // 5分钟

  async read(path: string): Promise<any> {
    // 检查缓存
    const cached = this.cache.get(path)
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return cached.data
    }

    // 从文件系统读取
    const data = fs.readFileSync(path, 'utf-8')
    this.cache.set(path, { data, timestamp: Date.now() })
    return data
  }

  async write(path: string, content: any) {
    // 直接写入，清除缓存
    fs.writeFileSync(path, serialize(content))
    this.cache.delete(path)
  }

  clearCache() {
    this.cache.clear()
  }
}
```

### 3.6.3 监视和增量更新

```typescript
class Memory {
  async watchProject(projectId: string, callback: (event: MemoryEvent) => void) {
    // 监视项目Memory的变化
    const watchPath = `memory/projects/${projectId}`

    fs.watch(watchPath, { recursive: true }, (eventType, filename) => {
      callback({
        type: eventType as 'rename' | 'change',
        projectId,
        path: filename,
        timestamp: Date.now()
      })
    })
  }
}

// 使用
memory.watchProject('project-001', (event) => {
  if (event.type === 'change' && event.path === 'progress.md') {
    // 有新的进度更新
    messageBus.emit('progress-updated', event)
  }
})
```

---

## 3.7 备份和恢复

### 3.7.1 备份策略

```typescript
class Memory {
  async backup() {
    // 每日自动备份
    const timestamp = new Date().toISOString().split('T')[0]
    const backupDir = `memory/backups/${timestamp}`

    // 1. 复制整个memory目录
    exec(`cp -r memory/ "${backupDir}"`)

    // 2. 压缩
    exec(`tar -czf "${backupDir}.tar.gz" "${backupDir}"`)

    // 3. 上传到远程 (可选)
    // await uploadToRemote(backupDir)

    // 4. 保留最近7个备份
    this.pruneOldBackups(7)
  }

  async restore(backupDate: string) {
    const backupDir = `memory/backups/${backupDate}`
    exec(`rm -rf memory/`)
    exec(`cp -r "${backupDir}" memory/`)
  }
}
```

---

## 3.8 监控和调试

### 3.8.1 Memory统计

```typescript
class Memory {
  async getStatistics() {
    return {
      global: {
        files: await this.countFiles('memory/global'),
        totalSize: await this.getTotalSize('memory/global')
      },
      projects: {
        count: await this.countDirectories('memory/projects'),
        totalSize: await this.getTotalSize('memory/projects')
      },
      tasks: {
        active: await this.countDirectories('memory/tasks'),
        totalSize: await this.getTotalSize('memory/tasks')
      },
      cache: {
        size: this.cache.size,
        hitRate: this.calculateCacheHitRate()
      }
    }
  }

  async printDiagnostics() {
    const stats = await this.getStatistics()
    console.log('Memory系统诊断:')
    console.log(JSON.stringify(stats, null, 2))
  }
}
```

---

## 🔗 相关文档

- [OVERVIEW.md](./01-OVERVIEW.md) - 架构总体
- [AGENT-ROLES.md](./02-AGENT-ROLES.md) - Agent职责
- [DATA-STRUCTURES.md](./08-DATA-STRUCTURES.md) - 数据结构
- [IMPLEMENTATION-GUIDE.md](./07-IMPLEMENTATION-GUIDE.md) - 实现代码

---

## 📝 总结表

| 特性 | Global | Project | Task |
|------|--------|---------|------|
| 创建者 | Master | Spawn | Task |
| 读权限 | 所有Agent | Master/Spawn/Task | Spawn/Task |
| 写权限 | Master | Spawn | Task |
| 持久化 | 永久 | 永久 | 临时 |
| 继承 | 被继承 | 从Global | 从Project+Global |
| 清理 | 不清理 | 项目删除时 | 任务完成后 |
