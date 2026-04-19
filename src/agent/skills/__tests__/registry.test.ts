import { SkillRegistry } from '../registry';
import { Skill, SkillContext } from '../../types';

describe('SkillRegistry', () => {
  let registry: SkillRegistry;
  
  beforeEach(() => {
    registry = new SkillRegistry();
  });

  const mockSkill: Skill = {
    name: 'test_skill',
    description: 'A test skill',
    version: '1.0.0',
    scope: 'global',
    execute: jest.fn().mockResolvedValue({ success: true }),
    validate: jest.fn().mockReturnValue(true),
  };

  describe('registerSkill', () => {
    test('should register a skill', () => {
      registry.registerSkill(mockSkill);
      
      const skill = registry.getSkill('test_skill');
      expect(skill).toBeDefined();
      expect(skill?.name).toBe('test_skill');
    });

    test('should override existing skill', () => {
      registry.registerSkill(mockSkill);
      
      const updatedSkill = { ...mockSkill, version: '2.0.0' };
      registry.registerSkill(updatedSkill);
      
      const skill = registry.getSkill('test_skill');
      expect(skill?.version).toBe('2.0.0');
    });
  });

  describe('registerSkillDirectory', () => {
    test('should register skill directory', () => {
      registry.registerSkillDirectory('/path/to/skills');
      
      // Should not throw
      expect(() => registry.registerSkillDirectory('/path/to/skills')).not.toThrow();
    });

    test('should avoid duplicate directories', () => {
      registry.registerSkillDirectory('/path/to/skills');
      registry.registerSkillDirectory('/path/to/skills');
      
      // Should only register once
      expect(() => registry.loadSkillsFromDirectory()).not.toThrow();
    });
  });

  describe('assignSkillsToAgent', () => {
    beforeEach(() => {
      registry.registerSkill(mockSkill);
    });

    test('should assign skills to agent', () => {
      registry.assignSkillsToAgent('agent-1', ['test_skill']);
      
      const skills = registry.getAgentSkills('agent-1');
      expect(skills).toHaveLength(1);
      expect(skills[0].name).toBe('test_skill');
    });

    test('should warn for non-existent skill', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      registry.assignSkillsToAgent('agent-1', ['non-existent']);
      
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('getSkill', () => {
    test('should return skill by name', () => {
      registry.registerSkill(mockSkill);
      
      const skill = registry.getSkill('test_skill');
      expect(skill).toEqual(mockSkill);
    });

    test('should return undefined for non-existent skill', () => {
      const skill = registry.getSkill('non-existent');
      expect(skill).toBeUndefined();
    });
  });

  describe('hasSkill', () => {
    beforeEach(() => {
      registry.registerSkill(mockSkill);
      registry.assignSkillsToAgent('agent-1', ['test_skill']);
    });

    test('should return true if agent has skill', () => {
      expect(registry.hasSkill('agent-1', 'test_skill')).toBe(true);
    });

    test('should return false if agent does not have skill', () => {
      expect(registry.hasSkill('agent-1', 'non-existent')).toBe(false);
    });

    test('should return false for non-existent agent', () => {
      expect(registry.hasSkill('non-existent', 'test_skill')).toBe(false);
    });
  });

  describe('executeSkill', () => {
    beforeEach(() => {
      registry.registerSkill(mockSkill);
    });

    test('should execute skill successfully', async () => {
      const mockContext: SkillContext = {
        agentId: 'agent-1',
        agentType: 'master',
        memory: { path: '/test', readOnly: false },
        invokeSkill: jest.fn(),
        sendMessage: jest.fn(),
      };
      
      const result = await registry.executeSkill('test_skill', { arg: 'value' }, mockContext);
      
      expect(result).toEqual({ success: true });
      expect(mockSkill.execute).toHaveBeenCalledWith({ arg: 'value' }, mockContext);
    });

    test('should throw for non-existent skill', async () => {
      const mockContext: SkillContext = {
        agentId: 'agent-1',
        agentType: 'master',
        memory: { path: '/test', readOnly: false },
        invokeSkill: jest.fn(),
        sendMessage: jest.fn(),
      };
      
      await expect(registry.executeSkill('non-existent', {}, mockContext)).rejects.toThrow('Skill non-existent not found');
    });

    test('should validate arguments before execution', async () => {
      const invalidSkill: Skill = {
        name: 'invalid_skill',
        description: 'Invalid skill',
        version: '1.0.0',
        scope: 'global',
        execute: jest.fn(),
        validate: jest.fn().mockReturnValue(false),
      };
      
      registry.registerSkill(invalidSkill);
      
      const mockContext: SkillContext = {
        agentId: 'agent-1',
        agentType: 'master',
        memory: { path: '/test', readOnly: false },
        invokeSkill: jest.fn(),
        sendMessage: jest.fn(),
      };
      
      await expect(registry.executeSkill('invalid_skill', {}, mockContext)).rejects.toThrow('Invalid arguments');
    });

    test('should check permissions if specified', async () => {
      const privilegedSkill: Skill = {
        name: 'privileged_skill',
        description: 'Privileged skill',
        version: '1.0.0',
        scope: 'global',
        permissions: ['admin'],
        execute: jest.fn().mockResolvedValue({}),
      };
      
      registry.registerSkill(privilegedSkill);
      
      const mockContext: SkillContext = {
        agentId: 'agent-1',
        agentType: 'master',
        memory: { path: '/test', readOnly: false },
        invokeSkill: jest.fn(),
        sendMessage: jest.fn(),
      };
      
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      await registry.executeSkill('privileged_skill', {}, mockContext);
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Checking permissions'));
      consoleSpy.mockRestore();
    });
  });

  describe('unregisterSkill', () => {
    beforeEach(() => {
      registry.registerSkill(mockSkill);
      registry.assignSkillsToAgent('agent-1', ['test_skill']);
    });

    test('should unregister skill', () => {
      const result = registry.unregisterSkill('test_skill');
      
      expect(result).toBe(true);
      expect(registry.getSkill('test_skill')).toBeUndefined();
    });

    test('should remove skill from all agents', () => {
      registry.unregisterSkill('test_skill');
      
      expect(registry.hasSkill('agent-1', 'test_skill')).toBe(false);
    });

    test('should return false for non-existent skill', () => {
      const result = registry.unregisterSkill('non-existent');
      
      expect(result).toBe(false);
    });
  });

  describe('getAllSkills', () => {
    test('should return all registered skills', () => {
      registry.registerSkill(mockSkill);
      
      const skill2: Skill = {
        name: 'skill2',
        description: 'Another skill',
        version: '1.0.0',
        scope: 'spawn',
        execute: jest.fn(),
      };
      registry.registerSkill(skill2);
      
      const skills = registry.getAllSkills();
      
      expect(skills).toHaveLength(2);
    });

    test('should return empty array when no skills', () => {
      const skills = registry.getAllSkills();
      
      expect(skills).toEqual([]);
    });
  });

  describe('getStats', () => {
    test('should return skill statistics', () => {
      registry.registerSkill(mockSkill);
      registry.registerSkill({ ...mockSkill, name: 'skill2' });
      registry.assignSkillsToAgent('agent-1', ['test_skill']);
      registry.assignSkillsToAgent('agent-2', ['test_skill', 'skill2']);
      
      const stats = registry.getStats();
      
      expect(stats.total).toBe(2);
      expect(stats.assigned).toBe(3);
    });
  });

  describe('cleanupAgentSkills', () => {
    beforeEach(() => {
      registry.registerSkill(mockSkill);
      registry.assignSkillsToAgent('agent-1', ['test_skill']);
    });

    test('should cleanup agent skills', () => {
      registry.cleanupAgentSkills('agent-1');
      
      expect(registry.hasSkill('agent-1', 'test_skill')).toBe(false);
    });

    test('should not throw for non-existent agent', () => {
      expect(() => registry.cleanupAgentSkills('non-existent')).not.toThrow();
    });
  });
});
