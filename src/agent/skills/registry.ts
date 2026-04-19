import { Skill, SkillRegistration, SkillContext, SkillRef } from '../types';
import { resolve, join } from 'path';
import { promises as fs } from 'fs';

export class SkillRegistry {
  private skills: Map<string, SkillRegistration> = new Map();
  private agentSkills: Map<string, Set<string>> = new Map();
  private skillDirectories: string[] = [];

  /**
   * 注册Skill目录
   */
  registerSkillDirectory(directory: string): void {
    const absolutePath = resolve(directory);
    if (!this.skillDirectories.includes(absolutePath)) {
      this.skillDirectories.push(absolutePath);
    }
  }

  /**
   * 注册单个Skill
   */
  registerSkill(skill: Skill, source: string = 'inline', config?: Record<string, any>): void {
    const registration: SkillRegistration = {
      skill,
      loadedAt: new Date(),
      source,
      config
    };

    this.skills.set(skill.name, registration);
    console.log(`Skill registered: ${skill.name} (version: ${skill.version})`);
  }

  /**
   * 从目录加载所有Skills
   */
  async loadSkillsFromDirectory(directory?: string): Promise<number> {
    const dirs = directory ? [directory] : this.skillDirectories;
    let loadedCount = 0;

    for (const dir of dirs) {
      try {
        const files = await fs.readdir(dir);
        
        for (const file of files) {
          if (file.endsWith('.skill.ts') || file.endsWith('.skill.js')) {
            try {
              const skillPath = join(dir, file);
              await this.loadSkillFromFile(skillPath);
              loadedCount++;
            } catch (error) {
              console.error(`Failed to load skill from ${file}:`, error);
            }
          }
        }
      } catch (error) {
        console.error(`Failed to read skill directory ${dir}:`, error);
      }
    }

    return loadedCount;
  }

  /**
   * 从文件加载Skill
   */
  async loadSkillFromFile(filePath: string): Promise<void> {
    try {
      // 清除require缓存以支持热更新
      delete require.cache[require.resolve(filePath)];
      
      const module = require(filePath);
      const skillExport = module.default || module.skill || module;
      
      if (this.isValidSkill(skillExport)) {
        this.registerSkill(skillExport, filePath);
      } else {
        throw new Error(`Invalid skill export in ${filePath}`);
      }
    } catch (error) {
      throw new Error(`Failed to load skill from ${filePath}: ${error}`);
    }
  }

  /**
   * 为Agent分配Skills
   */
  assignSkillsToAgent(agentId: string, skillNames: string[]): void {
    const agentSkillSet = new Set<string>();

    for (const name of skillNames) {
      if (this.skills.has(name)) {
        agentSkillSet.add(name);
      } else {
        console.warn(`Skill ${name} not found, cannot assign to agent ${agentId}`);
      }
    }

    this.agentSkills.set(agentId, agentSkillSet);
  }

  /**
   * 获取Agent的所有Skills
   */
  getAgentSkills(agentId: string): Skill[] {
    const skillNames = this.agentSkills.get(agentId);
    if (!skillNames) return [];

    return Array.from(skillNames)
      .map(name => this.skills.get(name)?.skill)
      .filter((skill): skill is Skill => skill !== undefined);
  }

  /**
   * 获取Skill
   */
  getSkill(name: string): Skill | undefined {
    return this.skills.get(name)?.skill;
  }

  /**
   * 检查Agent是否有某个Skill
   */
  hasSkill(agentId: string, skillName: string): boolean {
    return this.agentSkills.get(agentId)?.has(skillName) || false;
  }

  /**
   * 执行Skill
   */
  async executeSkill(
    skillName: string,
    args: any,
    context: SkillContext
  ): Promise<any> {
    const registration = this.skills.get(skillName);
    if (!registration) {
      throw new Error(`Skill ${skillName} not found`);
    }

    const skill = registration.skill;

    // 验证参数
    if (skill.validate) {
      const isValid = await skill.validate(args);
      if (!isValid) {
        throw new Error(`Invalid arguments for skill ${skillName}`);
      }
    }

    // 检查权限
    if (skill.permissions && skill.permissions.length > 0) {
      // 权限检查逻辑可以在这里实现
      console.log(`Checking permissions for skill ${skillName}: ${skill.permissions.join(', ')}`);
    }

    // 执行Skill
    try {
      const result = await skill.execute(args, context);
      return result;
    } catch (error) {
      console.error(`Skill ${skillName} execution failed:`, error);
      throw error;
    }
  }

  /**
   * 卸载Skill
   */
  unregisterSkill(name: string): boolean {
    // 从所有Agent中移除
    for (const [agentId, skillSet] of this.agentSkills) {
      skillSet.delete(name);
    }

    return this.skills.delete(name);
  }

  /**
   * 更新Skill
   */
  async reloadSkill(name: string): Promise<void> {
    const registration = this.skills.get(name);
    if (!registration) {
      throw new Error(`Skill ${name} not found`);
    }

    if (registration.source && registration.source !== 'inline') {
      await this.loadSkillFromFile(registration.source);
    } else {
      throw new Error(`Cannot reload inline skill ${name}`);
    }
  }

  /**
   * 获取所有注册的Skills
   */
  getAllSkills(): Skill[] {
    return Array.from(this.skills.values()).map(reg => reg.skill);
  }

  /**
   * 获取Skill统计信息
   */
  getStats(): { total: number; assigned: number } {
    let totalAssigned = 0;
    for (const skillSet of this.agentSkills.values()) {
      totalAssigned += skillSet.size;
    }

    return {
      total: this.skills.size,
      assigned: totalAssigned
    };
  }

  /**
   * 清理Agent的Skills
   */
  cleanupAgentSkills(agentId: string): void {
    this.agentSkills.delete(agentId);
  }

  // ============ 私有方法 ============

  private isValidSkill(obj: any): obj is Skill {
    return (
      obj &&
      typeof obj.name === 'string' &&
      typeof obj.description === 'string' &&
      typeof obj.version === 'string' &&
      typeof obj.execute === 'function'
    );
  }
}

export const skillRegistry = new SkillRegistry();
