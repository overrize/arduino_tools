import { MemorySystem } from '../memory';
import { MemoryRef, PermissionLevel } from '../../types';
import { promises as fs } from 'fs';
import { resolve } from 'path';
import { tmpdir } from 'os';

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

describe('MemorySystem', () => {
  let memory: MemorySystem;
  const testAgentId = 'test-agent';
  const testPath = resolve(tmpdir(), 'test-memory');
  
  beforeEach(() => {
    memory = new MemorySystem();
    jest.clearAllMocks();
  });

  describe('initializeMemory', () => {
    test('should initialize memory for agent', async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      
      await memory.initializeMemory(testAgentId, memoryRef);
      
      expect(fs.mkdir).toHaveBeenCalledWith(testPath, { recursive: true });
    });

    test('should initialize with parent memory', async () => {
      const parentRef: MemoryRef = {
        path: resolve(tmpdir(), 'parent-memory'),
        readOnly: false,
      };
      await memory.initializeMemory('parent-agent', parentRef);
      
      const childRef: MemoryRef = {
        path: testPath,
        readOnly: false,
        inheritedFrom: 'parent-agent',
      };
      
      await memory.initializeMemory(testAgentId, childRef);
      
      expect(fs.mkdir).toHaveBeenCalledWith(testPath, { recursive: true });
    });
  });

  describe('write and read', () => {
    beforeEach(async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      await memory.initializeMemory(testAgentId, memoryRef);
    });

    test('should write and read value', async () => {
      await memory.write(testAgentId, 'key1', 'value1');
      const value = await memory.read(testAgentId, 'key1');
      
      expect(value).toBe('value1');
    });

    test('should update existing value', async () => {
      await memory.write(testAgentId, 'key1', 'value1');
      await memory.write(testAgentId, 'key1', 'value2');
      const value = await memory.read(testAgentId, 'key1');
      
      expect(value).toBe('value2');
    });

    test('should return undefined for non-existent key', async () => {
      const value = await memory.read(testAgentId, 'non-existent');
      
      expect(value).toBeUndefined();
    });

    test('should throw when memory not initialized', async () => {
      await expect(memory.read('non-initialized', 'key')).rejects.toThrow('Memory not initialized');
    });

    test('should throw when writing to read-only memory', async () => {
      const readOnlyRef: MemoryRef = {
        path: resolve(tmpdir(), 'readonly-memory'),
        readOnly: true,
      };
      await memory.initializeMemory('readonly-agent', readOnlyRef);
      
      await expect(memory.write('readonly-agent', 'key', 'value')).rejects.toThrow('read-only');
    });

    test('should support tags', async () => {
      await memory.write(testAgentId, 'key1', 'value1', ['tag1', 'tag2']);
      
      const result = await memory.queryByTag(testAgentId, 'tag1');
      expect(result.get('key1')).toBe('value1');
    });
  });

  describe('readMany', () => {
    beforeEach(async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      await memory.initializeMemory(testAgentId, memoryRef);
      await memory.write(testAgentId, 'key1', 'value1');
      await memory.write(testAgentId, 'key2', 'value2');
    });

    test('should read multiple keys', async () => {
      const result = await memory.readMany(testAgentId, ['key1', 'key2', 'key3']);
      
      expect(result.get('key1')).toBe('value1');
      expect(result.get('key2')).toBe('value2');
      expect(result.has('key3')).toBe(false);
    });
  });

  describe('queryByTag', () => {
    beforeEach(async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      await memory.initializeMemory(testAgentId, memoryRef);
      await memory.write(testAgentId, 'key1', 'value1', ['tag1']);
      await memory.write(testAgentId, 'key2', 'value2', ['tag1', 'tag2']);
      await memory.write(testAgentId, 'key3', 'value3', ['tag2']);
    });

    test('should query by single tag', async () => {
      const result = await memory.queryByTag(testAgentId, 'tag1');
      
      expect(result.size).toBe(2);
      expect(result.get('key1')).toBe('value1');
      expect(result.get('key2')).toBe('value2');
    });
  });

  describe('delete', () => {
    beforeEach(async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      await memory.initializeMemory(testAgentId, memoryRef);
      await memory.write(testAgentId, 'key1', 'value1');
    });

    test('should delete existing key', async () => {
      const result = await memory.delete(testAgentId, 'key1');
      
      expect(result).toBe(true);
      const value = await memory.read(testAgentId, 'key1');
      expect(value).toBeUndefined();
    });

    test('should return false for non-existent key', async () => {
      const result = await memory.delete(testAgentId, 'non-existent');
      
      expect(result).toBe(false);
    });

    test('should throw when deleting from read-only memory', async () => {
      const readOnlyRef: MemoryRef = {
        path: resolve(tmpdir(), 'readonly-memory'),
        readOnly: true,
      };
      await memory.initializeMemory('readonly-agent', readOnlyRef);
      
      await expect(memory.delete('readonly-agent', 'key')).rejects.toThrow('read-only');
    });
  });

  describe('getKeys', () => {
    beforeEach(async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      await memory.initializeMemory(testAgentId, memoryRef);
      await memory.write(testAgentId, 'key1', 'value1');
      await memory.write(testAgentId, 'key2', 'value2');
    });

    test('should return all keys', async () => {
      const keys = await memory.getKeys(testAgentId);
      
      expect(keys).toContain('key1');
      expect(keys).toContain('key2');
    });
  });

  describe('permissions', () => {
    test('should set and check permissions', () => {
      memory.setPermission(testAgentId, 'resource1', 'read' as PermissionLevel);
      memory.setPermission(testAgentId, 'resource2', 'write' as PermissionLevel);
      
      const check1 = memory.checkPermission(testAgentId, 'resource1', 'read' as PermissionLevel);
      expect(check1.granted).toBe(true);
      
      const check2 = memory.checkPermission(testAgentId, 'resource2', 'admin' as PermissionLevel);
      expect(check2.granted).toBe(false);
    });

    test('should deny permission for unknown agent', () => {
      const check = memory.checkPermission('unknown', 'resource', 'read' as PermissionLevel);
      expect(check.granted).toBe(false);
    });

    test('should support wildcard permissions', () => {
      memory.setPermission(testAgentId, '*', 'write' as PermissionLevel);
      
      const check = memory.checkPermission(testAgentId, 'any-resource', 'read' as PermissionLevel);
      expect(check.granted).toBe(true);
    });
  });

  describe('buildContextChain', () => {
    beforeEach(async () => {
      const parentRef: MemoryRef = {
        path: resolve(tmpdir(), 'parent-memory'),
        readOnly: false,
      };
      await memory.initializeMemory('parent-agent', parentRef);
      await memory.write('parent-agent', 'shared-key', 'shared-value');
      
      const childRef: MemoryRef = {
        path: testPath,
        readOnly: false,
        inheritedFrom: 'parent-agent',
      };
      await memory.initializeMemory(testAgentId, childRef);
      await memory.write(testAgentId, 'local-key', 'local-value');
    });

    test('should build context chain', async () => {
      const chain = memory.buildContextChain(testAgentId);
      
      expect(chain.agentId).toBe(testAgentId);
      expect(chain.localContext['local-key']).toBe('local-value');
      expect(chain.localContext['shared-key']).toBe('shared-value');
      expect(chain.inheritedKeys).toContain('shared-key');
    });
  });

  describe('cleanupMemory', () => {
    test('should cleanup memory', async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      await memory.initializeMemory(testAgentId, memoryRef);
      
      await memory.cleanupMemory(testAgentId);
      
      await expect(memory.read(testAgentId, 'key')).rejects.toThrow();
    });

    test('should delete files when specified', async () => {
      const memoryRef: MemoryRef = {
        path: testPath,
        readOnly: false,
      };
      await memory.initializeMemory(testAgentId, memoryRef);
      
      await memory.cleanupMemory(testAgentId, true);
      
      expect(fs.rmdir).toHaveBeenCalledWith(testPath, { recursive: true });
    });
  });
});
