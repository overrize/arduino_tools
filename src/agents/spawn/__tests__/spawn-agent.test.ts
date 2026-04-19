import { SpawnAgent } from '../spawn-agent';
import { Task, TaskPriority } from '../../../agent/types';

jest.mock('../../../agent/runtime/runtime', () => ({
  agentRuntime: {
    forkAgent: jest.fn().mockResolvedValue({
      id: 'TASK-123',
      type: 'coding',
    }),
    terminateAgent: jest.fn().mockResolvedValue(undefined),
  },
}));

jest.mock('../../../agent/memory/memory', () => ({
  memorySystem: {
    initializeMemory: jest.fn().mockResolvedValue(undefined),
    write: jest.fn().mockResolvedValue(undefined),
    read: jest.fn().mockResolvedValue(undefined),
    cleanupMemory: jest.fn().mockResolvedValue(undefined),
  },
}));

jest.mock('../../../agent/skills/registry', () => ({
  skillRegistry: {
    assignSkillsToAgent: jest.fn().mockResolvedValue(undefined),
  },
}));

describe('SpawnAgent', () => {
  let spawn: SpawnAgent;
  const spawnId = 'SPAWN-TEST-123';
  const masterId = 'MASTER-TEST-456';
  const projectId = 'proj_test_789';

  beforeEach(() => {
    spawn = new SpawnAgent(spawnId, masterId, {
      projectId,
      maxConcurrentTasks: 3,
      autoRetryFailed: true,
    });
  });

  describe('initialization', () => {
    test('should initialize', async () => {
      const initialized = jest.fn();
      spawn.on('initialized', initialized);

      await spawn.initialize();

      expect(initialized).toHaveBeenCalled();
    });
  });

  describe('requirement handling', () => {
    beforeEach(async () => {
      await spawn.initialize();
    });

    test('should receive and decompose requirement', async () => {
      const result = await spawn.receiveRequirement('Implement a user authentication system with code');

      expect(result.tasksQueued).toBeGreaterThan(0);
      expect(spawn.getQueueSize()).toBeGreaterThan(0);
    });

    test('should create coding tasks for code requirements', async () => {
      await spawn.receiveRequirement('Generate code for API endpoint');

      expect(spawn.getQueueSize()).toBeGreaterThan(0);
    });

    test('should create debug tasks for fix requirements', async () => {
      await spawn.receiveRequirement('Fix the null pointer error');

      expect(spawn.getQueueSize()).toBeGreaterThan(0);
    });
  });

  describe('task queue', () => {
    beforeEach(async () => {
      await spawn.initialize();
    });

    test('should enqueue task', async () => {
      const task: Task = {
        id: 'task_1',
        type: 'coding',
        description: 'Test task',
        priority: 'high',
        payload: {},
      };

      await spawn.enqueueTask(task);

      expect(spawn.getQueueSize()).toBe(1);
    });

    test('should sort by priority', async () => {
      const lowTask: Task = {
        id: 'low',
        type: 'generic',
        description: 'Low',
        priority: 'low',
        payload: {},
      };
      const highTask: Task = {
        id: 'high',
        type: 'generic',
        description: 'High',
        priority: 'high',
        payload: {},
      };

      await spawn.enqueueTask(lowTask);
      await spawn.enqueueTask(highTask);

      expect(spawn.getQueueSize()).toBe(2);
    });
  });

  describe('task allocation', () => {
    beforeEach(async () => {
      await spawn.initialize();
    });

    test('should allocate tasks', async () => {
      await spawn.receiveRequirement('Implement feature with code');

      const allocations = await spawn.planAndAllocate();

      expect(Array.isArray(allocations)).toBe(true);
    });

    test('should track active tasks', async () => {
      expect(spawn.getActiveTaskCount()).toBe(0);
    });
  });

  describe('progress reporting', () => {
    beforeEach(async () => {
      await spawn.initialize();
    });

    test('should report progress', async () => {
      const progress = jest.fn();
      spawn.on('task:progress', progress);

      await spawn.reportProgress('task_1', 50, 'Halfway done');

      expect(progress).toHaveBeenCalledWith(expect.objectContaining({
        taskId: 'task_1',
        percent: 50,
      }));
    });
  });

  describe('task results', () => {
    beforeEach(async () => {
      await spawn.initialize();
      await spawn.receiveRequirement('Test code');
    });

    test('should handle successful task', async () => {
      const completed = jest.fn();
      spawn.on('task:completed', completed);

      await spawn.handleTaskResult('task_1', {
        taskId: 'task_1',
        status: 'success',
        duration: 1000,
      });

      expect(completed).toHaveBeenCalled();
    });

    test('should handle failed task with retry', async () => {
      const retry = jest.fn();
      spawn.on('task:retry', retry);

      await spawn.handleTaskResult('task_1', {
        taskId: 'task_1',
        status: 'failed',
        error: 'Test error',
        duration: 500,
      });

      expect(retry).toHaveBeenCalled();
    });
  });

  describe('shutdown', () => {
    beforeEach(async () => {
      await spawn.initialize();
    });

    test('should shutdown gracefully', async () => {
      const shutdown = jest.fn();
      spawn.on('shutdown', shutdown);

      await spawn.shutdown();

      expect(shutdown).toHaveBeenCalled();
    });
  });
});
