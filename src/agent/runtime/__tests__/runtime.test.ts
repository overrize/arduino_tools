import { AgentRuntime } from '../runtime';
import { AgentType, AgentStatus, RuntimeConfig } from '../../types';

// Mock Worker
jest.mock('worker_threads', () => ({
  Worker: jest.fn().mockImplementation(() => ({
    postMessage: jest.fn(),
    terminate: jest.fn().mockResolvedValue(undefined),
    on: jest.fn(),
  })),
  workerData: {},
}));

describe('AgentRuntime', () => {
  let runtime: AgentRuntime;
  
  beforeEach(() => {
    const config: Partial<RuntimeConfig> = {
      maxAgents: 10,
      heartbeatInterval: 1000,
    };
    runtime = new AgentRuntime(config);
  });
  
  afterEach(async () => {
    await runtime.shutdown();
  });

  describe('initialization', () => {
    test('should initialize successfully', async () => {
      const initialized = jest.fn();
      runtime.on('initialized', initialized);
      
      await runtime.initialize();
      
      expect(initialized).toHaveBeenCalled();
    });
  });

  describe('forkAgent', () => {
    test('should fork a master agent', async () => {
      const agent = await runtime.forkAgent('master');
      
      expect(agent).toBeDefined();
      expect(agent.id).toMatch(/^MAST-/);
      expect(agent.type).toBe('master');
      expect(agent.status).toBe('idle');
    });

    test('should fork a spawn agent with parent', async () => {
      const parent = await runtime.forkAgent('master');
      const child = await runtime.forkAgent('spawn', parent.id);
      
      expect(child.parentId).toBe(parent.id);
      expect(child.type).toBe('spawn');
    });

    test('should throw error when max agents reached', async () => {
      const smallRuntime = new AgentRuntime({ maxAgents: 1 });
      
      await smallRuntime.forkAgent('master');
      
      await expect(smallRuntime.forkAgent('spawn')).rejects.toThrow('Maximum agent limit');
      
      await smallRuntime.shutdown();
    });

    test('should throw error when parent not found', async () => {
      await expect(runtime.forkAgent('spawn', 'non-existent')).rejects.toThrow('Parent agent non-existent not found');
    });
  });

  describe('terminateAgent', () => {
    test('should terminate an agent', async () => {
      const agent = await runtime.forkAgent('master');
      
      const result = await runtime.terminateAgent(agent.id);
      
      expect(result).toBe(true);
      expect(runtime.hasAgent(agent.id)).toBe(false);
    });

    test('should return false for non-existent agent', async () => {
      const result = await runtime.terminateAgent('non-existent');
      
      expect(result).toBe(false);
    });

    test('should force terminate when specified', async () => {
      const agent = await runtime.forkAgent('master');
      
      const result = await runtime.terminateAgent(agent.id, true);
      
      expect(result).toBe(true);
    });
  });

  describe('getAgent queries', () => {
    beforeEach(async () => {
      await runtime.forkAgent('master');
      await runtime.forkAgent('master');
      await runtime.forkAgent('spawn');
    });

    test('should get agent by id', async () => {
      const agents = runtime.getAllAgents();
      const first = agents[0];
      
      const found = runtime.getAgent(first.id);
      
      expect(found).toEqual(first);
    });

    test('should get all agents', () => {
      const agents = runtime.getAllAgents();
      
      expect(agents).toHaveLength(3);
    });

    test('should get agents by type', () => {
      const masters = runtime.getAgentsByType('master');
      const spawns = runtime.getAgentsByType('spawn');
      
      expect(masters).toHaveLength(2);
      expect(spawns).toHaveLength(1);
    });
  });

  describe('getChildAgents', () => {
    test('should get child agents', async () => {
      const parent = await runtime.forkAgent('master');
      await runtime.forkAgent('spawn', parent.id);
      await runtime.forkAgent('spawn', parent.id);
      
      const children = runtime.getChildAgents(parent.id);
      
      expect(children).toHaveLength(2);
      expect(children.every(c => c.parentId === parent.id)).toBe(true);
    });
  });

  describe('updateAgentStatus', () => {
    test('should update agent status', async () => {
      const agent = await runtime.forkAgent('master');
      
      const result = runtime.updateAgentStatus(agent.id, 'running');
      
      expect(result).toBe(true);
      expect(runtime.getAgent(agent.id)?.status).toBe('running');
    });

    test('should return false for non-existent agent', () => {
      const result = runtime.updateAgentStatus('non-existent', 'running');
      
      expect(result).toBe(false);
    });

    test('should emit status changed event', async () => {
      const agent = await runtime.forkAgent('master');
      const handler = jest.fn();
      runtime.on('agent:status:changed', handler);
      
      runtime.updateAgentStatus(agent.id, 'running');
      
      expect(handler).toHaveBeenCalledWith({ agentId: agent.id, status: 'running' });
    });
  });

  describe('getStats', () => {
    test('should return runtime stats', async () => {
      await runtime.forkAgent('master');
      await runtime.forkAgent('spawn');
      
      const stats = runtime.getStats();
      
      expect(stats.totalAgents).toBe(2);
      expect(stats.activeAgents).toBe(2);
      expect(stats.uptime).toBeGreaterThan(0);
    });
  });

  describe('shutdown', () => {
    test('should terminate all agents on shutdown', async () => {
      await runtime.forkAgent('master');
      await runtime.forkAgent('spawn');
      
      await runtime.shutdown();
      
      expect(runtime.getAllAgents()).toHaveLength(0);
    });

    test('should emit shutdown event', async () => {
      const handler = jest.fn();
      runtime.on('shutdown', handler);
      
      await runtime.shutdown();
      
      expect(handler).toHaveBeenCalled();
    });
  });

  describe('hasAgent', () => {
    test('should return true for existing agent', async () => {
      const agent = await runtime.forkAgent('master');
      
      expect(runtime.hasAgent(agent.id)).toBe(true);
    });

    test('should return false for non-existent agent', () => {
      expect(runtime.hasAgent('non-existent')).toBe(false);
    });
  });
});
