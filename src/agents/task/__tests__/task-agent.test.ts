import { TaskAgent } from '../task-agent';
import { TaskResult } from '../../../agent/types';

jest.mock('../../../agent/memory/memory', () => ({
  memorySystem: {
    initializeMemory: jest.fn().mockResolvedValue(undefined),
    write: jest.fn().mockResolvedValue(undefined),
    read: jest.fn().mockResolvedValue(undefined),
    cleanupMemory: jest.fn().mockResolvedValue(undefined),
  },
}));

class TestTaskAgent extends TaskAgent {
  performTaskCalls: number = 0;

  async performTask(): Promise<any> {
    this.performTaskCalls++;
    await this.reportProgress(50, 'Halfway');
    return { result: 'success' };
  }
}

describe('TaskAgent', () => {
  let agent: TestTaskAgent;
  const agentId = 'TASK-TEST-123';
  const taskId = 'task_test_456';
  const projectId = 'proj_test_789';
  const parentId = 'SPAWN-TEST';

  beforeEach(() => {
    agent = new TestTaskAgent(agentId, taskId, projectId, parentId, 'Test requirements');
  });

  describe('execution', () => {
    test('should execute task successfully', async () => {
      const result = await agent.execute();

      expect(result.status).toBe('success');
      expect(result.taskId).toBe(taskId);
      expect(result.output).toEqual({ result: 'success' });
      expect(agent.performTaskCalls).toBe(1);
    });

    test('should report progress', async () => {
      const progressEvents: any[] = [];
      agent.on('progress', (p) => progressEvents.push(p));

      await agent.execute();

      expect(progressEvents.length).toBeGreaterThan(0);
      expect(progressEvents.some(p => p.percent === 50)).toBe(true);
    });

    test('should emit completed event', async () => {
      const completed = jest.fn();
      agent.on('task:completed', completed);

      await agent.execute();

      expect(completed).toHaveBeenCalledWith(expect.objectContaining({
        taskId,
        status: 'success',
      }));
    });

    test('should handle errors', async () => {
      class ErrorAgent extends TaskAgent {
        async performTask(): Promise<any> {
          throw new Error('Task failed');
        }
      }

      const errorAgent = new ErrorAgent(agentId, taskId, projectId, parentId, 'test');
      const result = await errorAgent.execute();

      expect(result.status).toBe('failed');
      expect(result.error).toBe('Task failed');
    });

    test('should emit failed event on error', async () => {
      class ErrorAgent extends TaskAgent {
        async performTask(): Promise<any> {
          throw new Error('Task failed');
        }
      }

      const errorAgent = new ErrorAgent(agentId, taskId, projectId, parentId, 'test');
      const failed = jest.fn();
      errorAgent.on('task:failed', failed);

      await errorAgent.execute();

      expect(failed).toHaveBeenCalled();
    });
  });

  describe('cleanup', () => {
    test('should cleanup after execution', async () => {
      const cleanup = jest.fn();
      agent.on('cleanup', cleanup);

      await agent.execute();

      expect(cleanup).toHaveBeenCalled();
    });

    test('should cleanup on manual call', async () => {
      await agent.cleanup();

      expect(agent.listenerCount('cleanup')).toBe(0); // No listeners after cleanup
    });
  });

  describe('context', () => {
    test('should store artifacts', async () => {
      class ArtifactAgent extends TaskAgent {
        async performTask(): Promise<any> {
          this.context.artifacts.set('test', 'value');
          return { ok: true };
        }
      }

      const artAgent = new ArtifactAgent(agentId, taskId, projectId, parentId, 'test');
      await artAgent.execute();

      expect(artAgent.context.artifacts.get('test')).toBe('value');
    });
  });
});
