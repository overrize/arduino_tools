import { AgentRuntime } from '../src/agent/runtime/runtime';
import { MemorySystem } from '../src/agent/memory/memory';
import { SkillRegistry } from '../src/agent/skills/registry';
import { MessageBus } from '../src/agent/communication/message-bus';
import { Skill, SkillContext, MemoryRef, AgentType, MessageType } from '../src/agent/types';

// Mock Worker
jest.mock('worker_threads', () => ({
  Worker: jest.fn().mockImplementation(() => ({
    postMessage: jest.fn(),
    terminate: jest.fn().mockResolvedValue(undefined),
    on: jest.fn(),
  })),
  workerData: {},
}));

jest.mock('fs', () => ({
  promises: {
    mkdir: jest.fn().mockResolvedValue(undefined),
    writeFile: jest.fn().mockResolvedValue(undefined),
    readFile: jest.fn().mockResolvedValue('{}'),
    readdir: jest.fn().mockResolvedValue([]),
    unlink: jest.fn().mockResolvedValue(undefined),
    rmdir: jest.fn().mockResolvedValue(undefined),
  },
}));

describe('Integration Tests', () => {
  let runtime: AgentRuntime;
  let memory: MemorySystem;
  let registry: SkillRegistry;
  let messageBus: MessageBus;

  beforeEach(() => {
    runtime = new AgentRuntime({ maxAgents: 10 });
    memory = new MemorySystem();
    registry = new SkillRegistry();
    messageBus = new MessageBus();
  });

  afterEach(async () => {
    await runtime.shutdown();
  });

  describe('End-to-End Workflow', () => {
    test('should create agent and assign skills', async () => {
      // Register a skill
      const testSkill: Skill = {
        name: 'test_skill',
        description: 'Test skill',
        version: '1.0.0',
        scope: 'global',
        execute: jest.fn().mockResolvedValue({ result: 'success' }),
      };
      registry.registerSkill(testSkill);

      // Create agent
      const agent = await runtime.forkAgent('master' as AgentType);
      expect(agent).toBeDefined();

      // Assign skill to agent
      registry.assignSkillsToAgent(agent.id, ['test_skill']);
      expect(registry.hasSkill(agent.id, 'test_skill')).toBe(true);

      // Initialize memory for agent
      const memoryRef: MemoryRef = {
        path: `/tmp/test-memory-${agent.id}`,
        readOnly: false,
      };
      await memory.initializeMemory(agent.id, memoryRef);

      // Execute skill
      const mockContext: SkillContext = {
        agentId: agent.id,
        agentType: 'master',
        memory: memoryRef,
        invokeSkill: jest.fn(),
        sendMessage: jest.fn(),
      };

      const result = await registry.executeSkill('test_skill', { test: 'data' }, mockContext);
      expect(result).toEqual({ result: 'success' });
    });

    test('should support parent-child agent hierarchy', async () => {
      // Create parent agent
      const parent = await runtime.forkAgent('master' as AgentType);
      
      // Initialize parent memory
      const parentMemoryRef: MemoryRef = {
        path: `/tmp/parent-memory`,
        readOnly: false,
      };
      await memory.initializeMemory(parent.id, parentMemoryRef);
      await memory.write(parent.id, 'shared-config', { value: 'parent-config' });

      // Create child agent with inheritance
      const child = await runtime.forkAgent('spawn' as AgentType, parent.id);
      expect(child.parentId).toBe(parent.id);

      // Initialize child memory with inheritance
      const childMemoryRef: MemoryRef = {
        path: `/tmp/child-memory`,
        readOnly: false,
        inheritedFrom: parent.id,
      };
      await memory.initializeMemory(child.id, childMemoryRef);

      // Child should be able to read parent config through inheritance
      const contextChain = memory.buildContextChain(child.id);
      expect(contextChain.parentChain).toBeDefined();
      expect(contextChain.localContext['shared-config']).toBe('parent-config');
    });

    test('should route messages between agents', async () => {
      // Create two agents
      const agent1 = await runtime.forkAgent('master' as AgentType);
      const agent2 = await runtime.forkAgent('spawn' as AgentType, agent1.id);

      // Mock message ports
      const mockPort1 = {
        postMessage: jest.fn(),
        on: jest.fn(),
      };
      const mockPort2 = {
        postMessage: jest.fn(),
        on: jest.fn(),
      };

      messageBus.registerAgentPort(agent1.id, mockPort1);
      messageBus.registerAgentPort(agent2.id, mockPort2);

      // Send message from agent1 to agent2
      await messageBus.send({
        from: agent1.id,
        to: agent2.id,
        type: MessageType.TASK_ASSIGN,
        payload: { task: 'test-task' },
        priority: 'normal',
      });

      expect(mockPort2.postMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          from: agent1.id,
          to: agent2.id,
          type: MessageType.TASK_ASSIGN,
        })
      );
    });

    test('should handle skill with memory operations', async () => {
      // Create a skill that uses memory
      const memorySkill: Skill = {
        name: 'memory_skill',
        description: 'Skill that uses memory',
        version: '1.0.0',
        scope: 'spawn',
        execute: async (args: any, context: SkillContext) => {
          // This would normally use the memory system
          return { stored: args.data };
        },
      };
      registry.registerSkill(memorySkill);

      // Create agent
      const agent = await runtime.forkAgent('spawn' as AgentType);

      // Initialize memory
      const memoryRef: MemoryRef = {
        path: `/tmp/agent-memory-${agent.id}`,
        readOnly: false,
      };
      await memory.initializeMemory(agent.id, memoryRef);

      // Assign and execute skill
      registry.assignSkillsToAgent(agent.id, ['memory_skill']);

      const mockContext: SkillContext = {
        agentId: agent.id,
        agentType: 'spawn',
        memory: memoryRef,
        invokeSkill: jest.fn(),
        sendMessage: jest.fn(),
      };

      const result = await registry.executeSkill('memory_skill', { data: 'test-data' }, mockContext);
      expect(result).toEqual({ stored: 'test-data' });
    });

    test('should cleanup all resources on shutdown', async () => {
      // Create agents and resources
      const agent = await runtime.forkAgent('master' as AgentType);
      
      registry.registerSkill({
        name: 'cleanup_test',
        description: 'Test skill',
        version: '1.0.0',
        scope: 'global',
        execute: jest.fn(),
      });
      registry.assignSkillsToAgent(agent.id, ['cleanup_test']);

      const memoryRef: MemoryRef = {
        path: `/tmp/cleanup-test`,
        readOnly: false,
      };
      await memory.initializeMemory(agent.id, memoryRef);

      // Shutdown
      await runtime.shutdown();
      
      // Verify cleanup
      expect(runtime.hasAgent(agent.id)).toBe(false);
      expect(runtime.getAllAgents()).toHaveLength(0);
    });
  });

  describe('Complete Project Workflow', () => {
    test('should execute full project creation workflow', async () => {
      // 1. Create Master Agent
      const master = await runtime.forkAgent('master' as AgentType);
      expect(master.type).toBe('master');

      // 2. Initialize Master Memory
      const masterMemoryRef: MemoryRef = {
        path: `/tmp/master-memory`,
        readOnly: false,
      };
      await memory.initializeMemory(master.id, masterMemoryRef);

      // 3. Register Project Management Skill
      registry.registerSkill({
        name: 'project_management',
        description: 'Manage projects',
        version: '1.0.0',
        scope: 'spawn',
        execute: async (args: any, context: SkillContext) => {
          if (args.action === 'create') {
            const project = {
              id: `proj-${Date.now()}`,
              ...args.config,
              createdAt: new Date(),
            };
            return project;
          }
          return null;
        },
      });

      // 4. Create Spawn Agent
      const spawn = await runtime.forkAgent('spawn' as AgentType, master.id);
      expect(spawn.parentId).toBe(master.id);

      // 5. Initialize Spawn Memory with inheritance
      const spawnMemoryRef: MemoryRef = {
        path: `/tmp/spawn-memory`,
        readOnly: false,
        inheritedFrom: master.id,
      };
      await memory.initializeMemory(spawn.id, spawnMemoryRef);

      // 6. Assign skills to Spawn
      registry.assignSkillsToAgent(spawn.id, ['project_management']);

      // 7. Execute skill to create project
      const mockContext: SkillContext = {
        agentId: spawn.id,
        agentType: 'spawn',
        memory: spawnMemoryRef,
        parentId: master.id,
        invokeSkill: jest.fn(),
        sendMessage: jest.fn(),
      };

      const result = await registry.executeSkill(
        'project_management',
        {
          action: 'create',
          config: {
            name: 'Test Project',
            description: 'A test project',
            technologies: ['TypeScript', 'Node.js'],
            priority: 'high',
            estimatedDuration: '2 weeks',
          },
        },
        mockContext
      );

      expect(result).toMatchObject({
        name: 'Test Project',
        description: 'A test project',
        technologies: ['TypeScript', 'Node.js'],
      });
      expect(result.id).toBeDefined();
      expect(result.createdAt).toBeDefined();
    });
  });
});
