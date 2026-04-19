# Multi-Agent Framework

Multi-Agent framework with Master → Spawn → Task hierarchy.

## Quick Start

```typescript
import { MasterAgent, SpawnAgent, CodingAgent } from './src';

// Initialize Master
const master = new MasterAgent();
await master.initialize();

// Create project
const project = await master.receiveCommand({
  type: 'create_project',
  payload: { name: 'My Project' },
  source: 'user'
});

// Fork Spawn Agent
const spawn = await master.receiveCommand({
  type: 'fork_spawn',
  payload: { projectId: project.id },
  source: 'user'
});

// Spawn handles requirements
const spawnAgent = new SpawnAgent(spawn.id, master.getId(), {
  projectId: project.id,
  maxConcurrentTasks: 5
});
await spawnAgent.initialize();

// Process requirement
await spawnAgent.receiveRequirement('Implement user authentication');
```

## Architecture

```
Master Agent
  ↓ fork
Spawn Agent (per project)
  ↓ fork
Task Agents (coding/debug/task)
```

## Components

### Phase 1 - Core
- `AgentRuntime`: Lifecycle management
- `MessageBus`: Inter-agent communication
- `MemorySystem`: Persistent storage with inheritance
- `SkillRegistry`: Dynamic skill loading

### Phase 2 - Master
- `MasterAgent`: Global coordination
- `ProjectManager`: Project CRUD

### Phase 3 - Spawn
- `SpawnAgent`: Task decomposition & allocation
- Task queue with priority
- Context sharing

### Phase 4 - Task
- `TaskAgent`: Base class
- `CodingAgent`: Code generation & review
- `DebugAgent`: Issue diagnosis & fix

## Test

```bash
cd src/agent
npm install
npm test
```

## File Structure

```
src/
├── agent/
│   ├── runtime/
│   ├── communication/
│   ├── memory/
│   ├── skills/
│   └── types/
├── agents/
│   ├── master/
│   ├── spawn/
│   └── task/
└── tests/e2e/
```
