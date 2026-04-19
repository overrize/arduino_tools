import { EventEmitter } from 'events';
import {
  Task,
  TaskResult,
  TaskProgress,
  MessageType,
  SkillContext,
  MemoryRef,
} from '../../agent/types';
import { memorySystem } from '../../agent/memory/memory';
import { skillRegistry } from '../../agent/skills/registry';
import { agentRuntime } from '../../agent/runtime/runtime';

export interface TaskContext {
  taskId: string;
  projectId: string;
  parentAgentId: string;
  requirements: string;
  artifacts: Map<string, any>;
}

export abstract class TaskAgent extends EventEmitter {
  protected id: string;
  protected taskId: string;
  protected projectId: string;
  protected parentId: string;
  protected context: TaskContext;
  protected running: boolean = false;
  protected startTime: number = 0;

  constructor(
    id: string,
    taskId: string,
    projectId: string,
    parentId: string,
    requirements: string
  ) {
    super();
    this.id = id;
    this.taskId = taskId;
    this.projectId = projectId;
    this.parentId = parentId;
    this.context = {
      taskId,
      projectId,
      parentAgentId: parentId,
      requirements,
      artifacts: new Map(),
    };
  }

  async execute(): Promise<TaskResult> {
    this.running = true;
    this.startTime = Date.now();

    try {
      await this.initialize();
      await this.reportProgress(0, 'Task started');

      const result = await this.performTask();

      await this.reportProgress(100, 'Task completed');
      await this.cleanup();

      const taskResult: TaskResult = {
        taskId: this.taskId,
        status: 'success',
        output: result,
        duration: Date.now() - this.startTime,
      };

      await this.saveResult(taskResult);
      this.emit('task:completed', taskResult);

      return taskResult;
    } catch (error) {
      const failedResult: TaskResult = {
        taskId: this.taskId,
        status: 'failed',
        error: error instanceof Error ? error.message : String(error),
        duration: Date.now() - this.startTime,
      };

      await this.saveResult(failedResult);
      this.emit('task:failed', failedResult);

      return failedResult;
    } finally {
      this.running = false;
    }
  }

  async reportProgress(percent: number, message: string): Promise<void> {
    const progress: TaskProgress = {
      taskId: this.taskId,
      percent: Math.min(100, Math.max(0, percent)),
      message,
      timestamp: Date.now(),
    };

    await memorySystem.write(this.id, 'progress', progress);
    this.emit('progress', progress);
  }

  async cleanup(): Promise<void> {
    await memorySystem.cleanupMemory(this.id);
    this.emit('cleanup');
  }

  protected async initialize(): Promise<void> {
    const memoryRef: MemoryRef = {
      path: `./memory/${this.id}`,
      readOnly: false,
      inheritedFrom: this.parentId,
    };
    await memorySystem.initializeMemory(this.id, memoryRef);

    const parentContext = await memorySystem.read(this.parentId, 'context');
    if (parentContext) {
      await memorySystem.write(this.id, 'parent_context', parentContext);
    }

    this.emit('initialized');
  }

  protected async saveResult(result: TaskResult): Promise<void> {
    await memorySystem.write(this.id, 'result', result);
    await memorySystem.write(this.parentId, `task_result:${this.taskId}`, result);
  }

  protected async invokeSkill(name: string, args: any): Promise<any> {
    const context: SkillContext = {
      agentId: this.id,
      agentType: 'task',
      memory: { path: `./memory/${this.id}`, readOnly: false },
      parentId: this.parentId,
      invokeSkill: this.invokeSkill.bind(this),
      sendMessage: async (to: string, type: MessageType, payload: any) => {
        // Implement message sending
      },
    };

    return await skillRegistry.executeSkill(name, args, context);
  }

  abstract performTask(): Promise<any>;
}
