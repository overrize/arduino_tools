import { MasterAgent } from '../../src/agents/master/master-agent';
import { ProjectManager } from '../../src/agents/master/managers/project-manager';
import { SpawnAgent } from '../../src/agents/spawn/spawn-agent';
import { CodingAgent } from '../../src/agents/task/coding-agent/coding-agent';
import { DebugAgent } from '../../src/agents/task/debug-agent/debug-agent';
import { agentRuntime } from '../../src/agent/runtime/runtime';
import { memorySystem } from '../../src/agent/memory/memory';
import { skillRegistry } from '../../src/agent/skills/registry';

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

describe('Complete Multi-Agent System', () => {
  beforeEach(async () => {
    await agentRuntime.initialize();
  });

  afterEach(async () => {
    await agentRuntime.shutdown();
  });

  describe('Master → Spawn → Task flow', () => {
    test('should create project and spawn agent', async () => {
      const master = new MasterAgent();
      await master.initialize();

      const project = await master.receiveCommand({
        type: 'create_project',
        payload: { name: 'Test Project', description: 'E2E Test' },
        source: 'user',
      });

      expect(project).toBeDefined();
      expect(project.id).toMatch(/^proj_/);

      const spawn = await master.receiveCommand({
        type: 'fork_spawn',
        payload: { projectId: project.id, config: {} },
        source: 'user',
      });

      expect(spawn).toBeDefined();
      expect(spawn.id).toMatch(/^SPAWN-/);

      await master.shutdown();
    });

    test('should handle requirements through full chain', async () => {
      const master = new MasterAgent();
      await master.initialize();

      const project = await master.receiveCommand({
        type: 'create_project',
        payload: { name: 'Code Generation Project' },
        source: 'user',
      });

      const spawnData = await master.receiveCommand({
        type: 'fork_spawn',
        payload: { projectId: project.id, config: { maxConcurrentTasks: 5 } },
        source: 'user',
      });

      const spawn = new SpawnAgent(spawnData.id, master.getId(), {
        projectId: project.id,
        maxConcurrentTasks: 5,
        autoRetryFailed: true,
      });
      await spawn.initialize();

      const result = await spawn.receiveRequirement('Implement a TypeScript class for user authentication');

      expect(result.tasksQueued).toBeGreaterThan(0);

      await spawn.shutdown();
      await master.shutdown();
    });
  });

  describe('Coding Agent', () => {
    test('should generate code end-to-end', async () => {
      const codingAgent = new CodingAgent(
        'CODING-E2E',
        'task_coding_e2e',
        'proj_e2e',
        'SPAWN-E2E',
        'Create a function to calculate fibonacci numbers'
      );

      const result = await codingAgent.execute();

      expect(result.status).toBe('success');
      expect(result.output).toBeDefined();
      expect(result.output.code).toBeDefined();
      expect(result.output.language).toBe('typescript');
    });
  });

  describe('Debug Agent', () => {
    test('should debug and fix issues end-to-end', async () => {
      const debugAgent = new DebugAgent(
        'DEBUG-E2E',
        'task_debug_e2e',
        'proj_e2e',
        'SPAWN-E2E',
        'Fix the null pointer exception in user data processing'
      );

      const result = await debugAgent.execute();

      expect(result.status).toBe('success');
      expect(result.output).toBeDefined();
      expect(result.output.diagnosis).toBeDefined();
      expect(result.output.fix).toBeDefined();
      expect(result.output.verified).toBe(true);
    });
  });

  describe('Project Manager', () => {
    test('should manage projects through Master', async () => {
      const master = new MasterAgent();
      await master.initialize();

      const pm = new ProjectManager(master);

      const project1 = await pm.createProject({
        name: 'Project 1',
        description: 'First project',
        technologies: ['typescript', 'node'],
      });

      const project2 = await pm.createProject({
        name: 'Project 2',
        description: 'Second project',
        priority: 'high',
      });

      const projects = await pm.listProjects();
      expect(projects).toHaveLength(2);

      const fetched = await pm.getProject(project1.id);
      expect(fetched.name).toBe('Project 1');

      await pm.updateProject(project1.id, { name: 'Updated Project 1' });
      const updated = await pm.getProject(project1.id);
      expect(updated.name).toBe('Updated Project 1');

      await pm.deleteProject(project2.id);
      const remaining = await pm.listProjects();
      expect(remaining).toHaveLength(1);

      await master.shutdown();
    });
  });

  describe('Complex scenario', () => {
    test('should handle multiple projects and tasks', async () => {
      const master = new MasterAgent();
      await master.initialize();

      const projects = [];
      for (let i = 0; i < 3; i++) {
        const project = await master.receiveCommand({
          type: 'create_project',
          payload: { name: `Project ${i}`, priority: i === 0 ? 'high' : 'medium' },
          source: 'test',
        });
        projects.push(project);
      }

      for (const project of projects) {
        await master.receiveCommand({
          type: 'fork_spawn',
          payload: { projectId: project.id },
          source: 'test',
        });
      }

      const stats = master.getStats();
      expect(stats.master.projects).toBe(3);

      await master.shutdown();
    });
  });
});
