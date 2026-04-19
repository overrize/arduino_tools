import { EventEmitter } from 'events';
import {
  AgentType,
  MessageType,
  Task,
  TaskResult,
  TaskProgress,
  TaskPriority,
} from '../../agent/types';
import { agentRuntime } from '../../agent/runtime/runtime';
import { memorySystem } from '../../agent/memory/memory';
import { skillRegistry } from '../../agent/skills/registry';
import { AgentCommunicationHub } from '../../agent/communication/agent-hub';

interface SpawnConfig {
  projectId: string;
  maxConcurrentTasks: number;
  autoRetryFailed: boolean;
}

interface TaskAllocation {
  taskId: string;
  agentId: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
}

export class SpawnAgent extends EventEmitter {
  private id: string;
  private projectId: string;
  private masterId: string;
  private taskQueue: Task[] = [];
  private activeTasks: Map<string, TaskAllocation> = new Map();
  private completedTasks: Map<string, TaskResult> = new Map();
  private running: boolean = false;
  private config: SpawnConfig;
  private communicationHub: AgentCommunicationHub;

  constructor(id: string, masterId: string, config: SpawnConfig) {
    super();
    this.id = id;
    this.projectId = config.projectId;
    this.masterId = masterId;
    this.config = {
      maxConcurrentTasks: 5,
      autoRetryFailed: true,
      ...config,
    };
    this.communicationHub = new AgentCommunicationHub(this.id, masterId);
  }

  private setupCommunicationHandlers(): void {
    this.communicationHub.on('message:sent', (data) => {
      this.emit('communication:sent', data);
    });

    this.communicationHub.onMessage(MessageType.CONTEXT_SHARE, async (payload) => {
      if (payload.project) {
        await memorySystem.write(this.id, 'project_context', payload.project);
      }
      this.emit('context:received', payload);
    });

    this.communicationHub.onMessage(MessageType.EVENT_BROADCAST, (payload) => {
      this.emit('broadcast:received', payload);
    });
  }

  async initialize(): Promise<void> {
    const memoryRef = {
      path: `./memory/${this.id}`,
      readOnly: false,
      inheritedFrom: this.masterId,
    };
    await memorySystem.initializeMemory(this.id, memoryRef);

    try {
      const parentContext = await this.communicationHub.requestParentContext();
      if (parentContext) {
        await memorySystem.write(this.id, 'parent_context', parentContext);
      }
    } catch (error) {
      console.warn(`Failed to get parent context: ${error}`);
    }

    this.running = true;
    this.startTaskProcessor();

    await this.communicationHub.sendToParent(MessageType.STATUS_UPDATE, {
      agentId: this.id,
      status: 'ready',
      projectId: this.projectId,
    });

    this.emit('initialized', { agentId: this.id, projectId: this.projectId });
  }

  async receiveRequirement(req: string): Promise<any> {
    await memorySystem.write(this.id, `requirement:${Date.now()}`, {
      text: req,
      timestamp: new Date(),
    });

    const tasks = await this.decomposeTasks(req);
    
    for (const task of tasks) {
      await this.enqueueTask(task);
    }

    this.emit('requirement:received', { requirement: req, tasks: tasks.length });
    return { tasksQueued: tasks.length };
  }

  async decomposeTasks(requirement: string): Promise<Task[]> {
    const tasks: Task[] = [];
    
    if (requirement.toLowerCase().includes('code') || requirement.toLowerCase().includes('implement')) {
      tasks.push(this.createTask('coding', 'Generate code implementation', 'high'));
      tasks.push(this.createTask('review', 'Review generated code', 'normal'));
    }
    
    if (requirement.toLowerCase().includes('fix') || requirement.toLowerCase().includes('debug')) {
      tasks.push(this.createTask('debugging', 'Diagnose and fix issue', 'high'));
    }
    
    if (requirement.toLowerCase().includes('test')) {
      tasks.push(this.createTask('testing', 'Generate and run tests', 'normal'));
    }
    
    if (tasks.length === 0) {
      tasks.push(this.createTask('generic', `Process: ${requirement}`, 'normal'));
    }

    return tasks;
  }

  async enqueueTask(task: Task): Promise<void> {
    this.taskQueue.push(task);
    this.taskQueue.sort((a, b) => this.priorityWeight(b.priority) - this.priorityWeight(a.priority));
    this.emit('task:enqueued', { taskId: task.id, type: task.type });
  }

  async planAndAllocate(): Promise<TaskAllocation[]> {
    const allocations: TaskAllocation[] = [];
    
    for (const task of this.taskQueue) {
      if (this.activeTasks.size >= this.config.maxConcurrentTasks) {
        break;
      }

      const agentType = this.selectAgentType(task);
      const allocation = await this.forkTaskAgent(agentType, task);
      allocations.push(allocation);
    }

    return allocations;
  }

  async reportProgress(taskId: string, percent: number, message: string): Promise<void> {
    const allocation = this.activeTasks.get(taskId);
    if (allocation) {
      allocation.progress = percent;
    }

    await this.communicationHub.reportProgress(taskId, percent, message);

    const progress: TaskProgress = {
      taskId,
      percent,
      message,
      timestamp: Date.now(),
    };

    await memorySystem.write(this.id, `progress:${taskId}`, progress);
    this.emit('task:progress', progress);
  }

  async handleTaskResult(taskId: string, result: TaskResult): Promise<void> {
    this.activeTasks.delete(taskId);
    this.completedTasks.set(taskId, result);

    await this.communicationHub.reportResult(taskId, result);
    await memorySystem.write(this.id, `result:${taskId}`, result);

    if (result.status === 'failed' && this.config.autoRetryFailed) {
      const task = this.taskQueue.find(t => t.id === taskId);
      if (task && !task.metadata?.retryCount || task.metadata?.retryCount < 3) {
        task.metadata = { ...task.metadata, retryCount: (task.metadata?.retryCount || 0) + 1 };
        await this.enqueueTask(task);
        this.emit('task:retry', { taskId });
        return;
      }
    }

    this.emit('task:completed', { taskId, result });
  }

  getId(): string {
    return this.id;
  }

  getProjectId(): string {
    return this.projectId;
  }

  getQueueSize(): number {
    return this.taskQueue.length;
  }

  getActiveTaskCount(): number {
    return this.activeTasks.size;
  }

  getCompletedTaskCount(): number {
    return this.completedTasks.size;
  }

  async shutdown(): Promise<void> {
    this.running = false;

    for (const [taskId, allocation] of this.activeTasks) {
      this.communicationHub.unregisterChild(allocation.agentId);
      await agentRuntime.terminateAgent(allocation.agentId);
    }

    await this.communicationHub.sendToParent(MessageType.STATUS_UPDATE, {
      agentId: this.id,
      status: 'terminated',
      projectId: this.projectId,
    });

    await memorySystem.cleanupMemory(this.id);
    this.emit('shutdown');
  }

  private startTaskProcessor(): void {
    const process = async () => {
      if (!this.running) return;

      if (this.taskQueue.length > 0 && this.activeTasks.size < this.config.maxConcurrentTasks) {
        await this.planAndAllocate();
      }

      setTimeout(process, 100);
    };

    process();
  }

  private createTask(type: string, description: string, priority: TaskPriority): Task {
    return {
      id: `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      description,
      priority,
      payload: {},
    };
  }

  private priorityWeight(priority: TaskPriority): number {
    const weights = { high: 3, normal: 2, low: 1 };
    return weights[priority] || 0;
  }

  private selectAgentType(task: Task): AgentType {
    switch (task.type) {
      case 'coding':
      case 'code':
        return 'coding';
      case 'debugging':
      case 'debug':
      case 'fix':
        return 'debug';
      default:
        return 'task';
    }
  }

  private async forkTaskAgent(type: AgentType, task: Task): Promise<TaskAllocation> {
    const agent = await agentRuntime.forkAgent(type, this.id, { taskId: task.id });

    this.communicationHub.registerChild(agent.id);

    const allocation: TaskAllocation = {
      taskId: task.id,
      agentId: agent.id,
      type: task.type,
      status: 'running',
      progress: 0,
    };

    this.activeTasks.set(task.id, allocation);
    this.taskQueue = this.taskQueue.filter(t => t.id !== task.id);

    const memoryRef = {
      path: `./memory/${agent.id}`,
      readOnly: false,
      inheritedFrom: this.id,
    };
    await memorySystem.initializeMemory(agent.id, memoryRef);

    await skillRegistry.assignSkillsToAgent(agent.id, [task.type, 'communication']);

    await this.communicationHub.sendToChild(agent.id, MessageType.TASK_ASSIGN, {
      taskId: task.id,
      task: task,
      parentId: this.id,
    });

    this.emit('task:allocated', allocation);
    return allocation;
  }

  getCommunicationHub(): AgentCommunicationHub {
    return this.communicationHub;
  }
}
