# 维护指南

## 目录结构

```
src/
├── agent/                    # 核心基础设施
│   ├── communication/       # 通信层
│   │   ├── agent-hub.ts    # Agent 通信中心
│   │   ├── message-bus.ts  # 消息总线
│   │   └── __tests__/
│   ├── memory/             # 存储层
│   │   ├── memory.ts
│   │   └── __tests__/
│   ├── runtime/            # 运行时
│   │   ├── runtime.ts
│   │   ├── worker.ts
│   │   └── __tests__/
│   ├── skills/             # Skill 系统
│   │   ├── registry.ts
│   │   ├── built-in/
│   │   └── __tests__/
│   └── types/              # 类型定义
│       └── index.ts
├── agents/                  # Agent 实现
│   ├── master/             # Master Agent
│   │   ├── master-agent.ts
│   │   ├── managers/
│   │   └── __tests__/
│   ├── spawn/              # Spawn Agent
│   │   ├── spawn-agent.ts
│   │   └── __tests__/
│   └── task/               # Task Agent
│       ├── task-agent.ts
│       ├── coding-agent/
│       ├── debug-agent/
│       └── __tests__/
└── index.ts                # 统一导出

docs/
└── architecture/
    └── multi-agent-framework/
        ├── README.md
        ├── MAINTENANCE.md      # 本文件
        ├── docs/
        │   ├── API.md
        │   ├── ARCHITECTURE.md
        │   └── USAGE.md
        └── updates/
            └── UPDATES.md
```

## 开发规范

### 代码规范

- 使用 TypeScript 严格模式
- 所有公共 API 必须导出类型
- 所有方法必须有返回类型声明
- 使用 async/await 处理异步

### 测试规范

- 所有模块必须有单元测试
- 测试文件放在 `__tests__/` 目录
- 使用 Jest 测试框架
- 覆盖率要求：核心模块 >80%

### 文档规范

- 新增 API 必须更新 API.md
- 架构变更必须更新 ARCHITECTURE.md
- 每次提交必须更新 UPDATES.md

## 更新流程

### 1. 修改代码

```bash
# 编辑相关文件
vim src/agent/communication/agent-hub.ts
```

### 2. 更新测试

```bash
# 编辑或新增测试
vim src/agent/communication/__tests__/agent-hub.test.ts

# 运行测试
npm test
```

### 3. 更新文档

```bash
# 更新 API 文档
vim docs/architecture/multi-agent-framework/docs/API.md

# 更新更新记录
vim docs/architecture/multi-agent-framework/updates/UPDATES.md
```

### 4. 提交代码

```bash
# 查看变更
git status

# 添加文件
git add -A

# 提交
git commit -m "feat(communication): add new feature

- 描述变更 1
- 描述变更 2

更新文档: docs/API.md, docs/UPDATES.md"
```

## 版本管理

### 版本号规则

使用语义化版本控制 (SemVer):
- MAJOR: 不兼容的 API 修改
- MINOR: 向下兼容的功能新增
- PATCH: 向下兼容的问题修复

### 发布流程

1. 更新 UPDATES.md 中的版本信息
2. 创建 git tag
3. 推送代码和 tag

```bash
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags
```

## 常见问题

### 添加新的消息类型

1. 在 `src/agent/types/index.ts` 中添加：
```typescript
enum MessageType {
  // ... 现有类型
  NEW_MESSAGE_TYPE = 'new_message_type',
}
```

2. 在 `AgentCommunicationHub` 中处理：
```typescript
private setupDefaultHandlers(): void {
  // ... 现有处理器
  this.onMessage(MessageType.NEW_MESSAGE_TYPE, (payload, from) => {
    // 处理逻辑
  });
}
```

3. 更新 API.md 文档

### 添加新的 Agent 类型

1. 创建新的 Agent 文件：
```typescript
// src/agents/task/my-agent/my-agent.ts
import { TaskAgent } from '../task-agent';

export class MyAgent extends TaskAgent {
  async performTask(): Promise<any> {
    // 实现
  }
}
```

2. 在 `src/index.ts` 中导出
3. 创建测试文件
4. 更新 USAGE.md 文档

### 调试通信问题

1. 启用调试日志：
```typescript
const hub = new AgentCommunicationHub(agentId, parentId);
hub.on('message:sent', (data) => console.log('Sent:', data));
hub.on('message:received', (data) => console.log('Received:', data));
```

2. 检查 Agent 注册状态：
```typescript
console.log('Children:', hub.getChildren());
console.log('Parent:', hub.getParent());
```

3. 查看 MessageBus 统计：
```typescript
console.log('Message stats:', messageBus.getStats());
```

## 性能优化

### 监控指标

- 消息延迟
- Agent 启动时间
- 内存占用
- 并发任务数

### 优化建议

- 大批量消息使用批量发送
- 任务完成后及时清理 Memory
- 限制最大并发任务数
- 使用心跳检测死锁

## 安全维护

### 定期更新

- 更新依赖包
- 检查安全漏洞
- 更新文档

### 备份策略

- Memory 数据定期备份
- 配置文件版本控制
- 测试用例完整覆盖

## 联系方式

- 维护者: Sisyphus Agent
- 最后更新: 2026-04-19
