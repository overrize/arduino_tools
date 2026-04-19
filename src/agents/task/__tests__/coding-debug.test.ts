import { CodingAgent } from '../coding-agent/coding-agent';

jest.mock('../../../agent/memory/memory', () => ({
  memorySystem: {
    initializeMemory: jest.fn().mockResolvedValue(undefined),
    write: jest.fn().mockResolvedValue(undefined),
    read: jest.fn().mockResolvedValue(undefined),
    cleanupMemory: jest.fn().mockResolvedValue(undefined),
  },
}));

describe('CodingAgent', () => {
  let agent: CodingAgent;
  const agentId = 'CODING-TEST-123';
  const taskId = 'task_coding_456';
  const projectId = 'proj_test_789';
  const parentId = 'SPAWN-TEST';

  beforeEach(() => {
    agent = new CodingAgent(agentId, taskId, projectId, parentId, 'Generate TypeScript code');
  });

  describe('code generation', () => {
    test('should generate code', async () => {
      const result = await agent.performTask();

      expect(result).toBeDefined();
      expect(result.code).toBeDefined();
      expect(result.language).toBe('typescript');
      expect(result.fileName).toBeDefined();
    });

    test('should detect language from requirements', async () => {
      const pythonAgent = new CodingAgent(agentId, taskId, projectId, parentId, 'Generate Python code');
      const result = await pythonAgent.performTask();

      expect(result.language).toBe('python');
    });

    test('should generate TypeScript by default', async () => {
      const result = await agent.performTask();

      expect(result.language).toBe('typescript');
    });

    test('should generate code with tests', async () => {
      const result = await agent.performTask();

      expect(result.tests).toBeDefined();
      expect(result.tests.length).toBeGreaterThan(0);
    });

    test('should perform code review', async () => {
      const result = await agent.performTask();

      expect(result.review).toBeDefined();
      expect(result.review.passed).toBeDefined();
      expect(result.review.issues).toBeDefined();
    });
  });

  describe('language detection', () => {
    test.each([
      ['Generate Python code', 'python'],
      ['Create a Rust implementation', 'rust'],
      ['Write Go code', 'go'],
      ['JavaScript function needed', 'javascript'],
      ['C++ algorithm', 'cpp'],
      ['TypeScript component', 'typescript'],
    ])('should detect %s as %s', async (req, expectedLang) => {
      const langAgent = new CodingAgent(agentId, taskId, projectId, parentId, req);
      const result = await langAgent.performTask();

      expect(result.language).toBe(expectedLang);
    });
  });

  describe('progress', () => {
    test('should report progress during execution', async () => {
      const progressEvents: any[] = [];
      agent.on('progress', (p) => progressEvents.push(p));

      await agent.execute();

      expect(progressEvents.length).toBeGreaterThan(0);
      expect(progressEvents.some(p => p.percent === 10)).toBe(true);
      expect(progressEvents.some(p => p.percent === 100)).toBe(true);
    });
  });
});

describe('DebugAgent', () => {
  const DebugAgent = require('../debug-agent/debug-agent').DebugAgent;
  
  jest.mock('../../../agent/memory/memory', () => ({
    memorySystem: {
      initializeMemory: jest.fn().mockResolvedValue(undefined),
      write: jest.fn().mockResolvedValue(undefined),
      read: jest.fn().mockResolvedValue(undefined),
      cleanupMemory: jest.fn().mockResolvedValue(undefined),
    },
  }));

  let agent: any;
  const agentId = 'DEBUG-TEST-123';
  const taskId = 'task_debug_456';
  const projectId = 'proj_test_789';
  const parentId = 'SPAWN-TEST';

  beforeEach(() => {
    agent = new DebugAgent(agentId, taskId, projectId, parentId, 'Fix null pointer error');
  });

  describe('debugging', () => {
    test('should diagnose issue', async () => {
      const result = await agent.performTask();

      expect(result.diagnosis).toBeDefined();
      expect(result.diagnosis.rootCause).toBeDefined();
      expect(result.diagnosis.confidence).toBeGreaterThan(0);
    });

    test('should generate fix', async () => {
      const result = await agent.performTask();

      expect(result.fix).toBeDefined();
      expect(result.fix.description).toBeDefined();
      expect(result.fix.codeChanges).toBeDefined();
    });

    test('should verify fix', async () => {
      const result = await agent.performTask();

      expect(result.verified).toBe(true);
    });

    test('should handle null errors', async () => {
      const nullAgent = new DebugAgent(agentId, taskId, projectId, parentId, 'null reference error');
      const result = await nullAgent.performTask();

      expect(result.diagnosis.rootCause).toContain('null');
    });

    test('should handle async errors', async () => {
      const asyncAgent = new DebugAgent(agentId, taskId, projectId, parentId, 'async operation failed');
      const result = await asyncAgent.performTask();

      expect(result.diagnosis.rootCause).toContain('async');
    });
  });
});
