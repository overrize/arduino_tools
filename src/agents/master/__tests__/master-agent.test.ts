import { MasterAgent, Command } from '../master-agent';
import { ProjectManager } from '../managers/project-manager';

jest.mock('../../agent/runtime/runtime', () => ({
  agentRuntime: {
    initialize: jest.fn().mockResolvedValue(undefined),
    getStats: jest.fn().mockReturnValue({ totalAgents: 0 }),
    shutdown: jest.fn().mockResolvedValue(undefined),
    forkAgent: jest.fn().mockResolvedValue({ id: 'SPAWN-123', type: 'spawn' }),
    terminateAgent: jest.fn().mockResolvedValue(true),
    getAgent: jest.fn().mockReturnValue(null),
  },
}));

jest.mock('../../agent/memory/memory', () => ({
  memorySystem: {
    initializeMemory: jest.fn().mockResolvedValue(undefined),
    write: jest.fn().mockResolvedValue(undefined),
    delete: jest.fn().mockResolvedValue(undefined),
    cleanupMemory: jest.fn().mockResolvedValue(undefined),
  },
}));

describe('MasterAgent', () => {
  let master: MasterAgent;

  beforeEach(() => {
    master = new MasterAgent();
  });

  describe('initialization', () => {
    test('should initialize successfully', async () => {
      const initialized = jest.fn();
      master.on('initialized', initialized);
      
      await master.initialize();
      
      expect(initialized).toHaveBeenCalled();
      expect(master.isRunning()).toBe(true);
    });
  });

  describe('project management', () => {
    beforeEach(async () => {
      await master.initialize();
    });

    test('should create project', async () => {
      const project = await master.receiveCommand({
        type: 'create_project',
        payload: {
          name: 'Test Project',
          description: 'A test project',
          technologies: ['typescript'],
        },
        source: 'test',
      });

      expect(project).toBeDefined();
      expect(project.name).toBe('Test Project');
      expect(project.id).toMatch(/^proj_/);
    });

    test('should list projects', async () => {
      await master.receiveCommand({
        type: 'create_project',
        payload: { name: 'Project 1' },
        source: 'test',
      });

      const projects = await master.receiveCommand({
        type: 'list_projects',
        payload: {},
        source: 'test',
      });

      expect(Array.isArray(projects)).toBe(true);
      expect(projects.length).toBeGreaterThan(0);
    });

    test('should delete project', async () => {
      const project = await master.receiveCommand({
        type: 'create_project',
        payload: { name: 'To Delete' },
        source: 'test',
      });

      const result = await master.receiveCommand({
        type: 'delete_project',
        payload: { projectId: project.id },
        source: 'test',
      });

      expect(result.success).toBe(true);
    });
  });

  describe('spawn agent management', () => {
    beforeEach(async () => {
      await master.initialize();
    });

    test('should fork spawn agent', async () => {
      const project = await master.receiveCommand({
        type: 'create_project',
        payload: { name: 'Test Project' },
        source: 'test',
      });

      const spawn = await master.receiveCommand({
        type: 'fork_spawn',
        payload: { projectId: project.id, config: {} },
        source: 'test',
      });

      expect(spawn).toBeDefined();
      expect(spawn.id).toMatch(/^SPAWN-/);
    });

    test('should terminate agent', async () => {
      const result = await master.receiveCommand({
        type: 'terminate_agent',
        payload: { agentId: 'AGENT-123' },
        source: 'test',
      });

      expect(result.success).toBe(true);
    });
  });

  describe('natural language processing', () => {
    beforeEach(async () => {
      await master.initialize();
    });

    test('should handle create project command', async () => {
      const result = await master.handleUserInteraction('create project My New Project');
      
      expect(result).toBeDefined();
      expect(result.name).toBe('My New Project');
    });

    test('should handle list projects command', async () => {
      const result = await master.handleUserInteraction('list projects');
      
      expect(Array.isArray(result)).toBe(true);
    });
  });

  describe('shutdown', () => {
    test('should shutdown gracefully', async () => {
      await master.initialize();
      
      const shutdown = jest.fn();
      master.on('shutdown', shutdown);
      
      await master.shutdown();
      
      expect(shutdown).toHaveBeenCalled();
      expect(master.isRunning()).toBe(false);
    });
  });
});

describe('ProjectManager', () => {
  let master: MasterAgent;
  let pm: ProjectManager;

  beforeEach(async () => {
    master = new MasterAgent();
    await master.initialize();
    pm = new ProjectManager(master);
  });

  test('should create project', async () => {
    const project = await pm.createProject({
      name: 'PM Test Project',
      description: 'Test',
    });

    expect(project.name).toBe('PM Test Project');
  });

  test('should get project', async () => {
    const created = await pm.createProject({ name: 'Get Test' });
    const fetched = await pm.getProject(created.id);

    expect(fetched).toBeDefined();
    expect(fetched.name).toBe('Get Test');
  });

  test('should update project', async () => {
    const created = await pm.createProject({ name: 'Update Test' });
    const updated = await pm.updateProject(created.id, { name: 'Updated Name' });

    expect(updated.name).toBe('Updated Name');
  });

  test('should throw on update non-existent', async () => {
    await expect(pm.updateProject('non-existent', { name: 'New' })).rejects.toThrow();
  });
});
