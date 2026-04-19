import { promises as fs } from 'fs';
import { resolve, dirname, join } from 'path';
import { MemoryRef, MemoryEntry, PermissionLevel, PermissionCheck, ContextChain } from '../types';

interface MemoryStore {
  entries: Map<string, MemoryEntry>;
  path: string;
  readOnly: boolean;
  parent?: MemoryStore;
}

export class MemorySystem {
  private stores: Map<string, MemoryStore> = new Map();
  private permissions: Map<string, Map<string, PermissionLevel>> = new Map();

  /**
   * 初始化Agent的Memory
   */
  async initializeMemory(agentId: string, memoryRef: MemoryRef): Promise<void> {
    const store: MemoryStore = {
      entries: new Map(),
      path: memoryRef.path,
      readOnly: memoryRef.readOnly,
      parent: memoryRef.inheritedFrom ? this.stores.get(memoryRef.inheritedFrom) : undefined
    };

    this.stores.set(agentId, store);

    // 确保目录存在
    try {
      await fs.mkdir(memoryRef.path, { recursive: true });
    } catch (error) {
      // 目录可能已存在
    }

    // 加载已有数据
    await this.loadFromDisk(agentId);
  }

  /**
   * 写入数据
   */
  async write(agentId: string, key: string, value: any, tags?: string[]): Promise<boolean> {
    const store = this.stores.get(agentId);
    if (!store) {
      throw new Error(`Memory not initialized for agent ${agentId}`);
    }

    if (store.readOnly) {
      throw new Error(`Memory is read-only for agent ${agentId}`);
    }

    const entry: MemoryEntry = {
      key,
      value,
      createdAt: new Date(),
      updatedAt: new Date(),
      version: 1,
      tags
    };

    const existing = store.entries.get(key);
    if (existing) {
      entry.createdAt = existing.createdAt;
      entry.version = existing.version + 1;
    }

    store.entries.set(key, entry);
    
    // 异步持久化
    this.persistToDisk(agentId, key, entry).catch(console.error);

    return true;
  }

  /**
   * 读取数据
   */
  async read(agentId: string, key: string): Promise<any | undefined> {
    const store = this.stores.get(agentId);
    if (!store) {
      throw new Error(`Memory not initialized for agent ${agentId}`);
    }

    // 先查本地
    const localEntry = store.entries.get(key);
    if (localEntry) {
      return localEntry.value;
    }

    // 从父级继承
    if (store.parent) {
      const parentEntry = store.parent.entries.get(key);
      if (parentEntry) {
        return parentEntry.value;
      }
    }

    return undefined;
  }

  /**
   * 批量读取
   */
  async readMany(agentId: string, keys: string[]): Promise<Map<string, any>> {
    const results = new Map<string, any>();
    
    for (const key of keys) {
      const value = await this.read(agentId, key);
      if (value !== undefined) {
        results.set(key, value);
      }
    }

    return results;
  }

  /**
   * 按标签查询
   */
  async queryByTag(agentId: string, tag: string): Promise<Map<string, any>> {
    const store = this.stores.get(agentId);
    if (!store) {
      throw new Error(`Memory not initialized for agent ${agentId}`);
    }

    const results = new Map<string, any>();

    // 查询本地
    for (const [key, entry] of store.entries) {
      if (entry.tags?.includes(tag)) {
        results.set(key, entry.value);
      }
    }

    // 查询父级
    if (store.parent) {
      for (const [key, entry] of store.parent.entries) {
        if (entry.tags?.includes(tag) && !results.has(key)) {
          results.set(key, entry.value);
        }
      }
    }

    return results;
  }

  /**
   * 删除数据
   */
  async delete(agentId: string, key: string): Promise<boolean> {
    const store = this.stores.get(agentId);
    if (!store) {
      throw new Error(`Memory not initialized for agent ${agentId}`);
    }

    if (store.readOnly) {
      throw new Error(`Memory is read-only for agent ${agentId}`);
    }

    const existed = store.entries.delete(key);
    
    if (existed) {
      // 删除文件
      const filePath = join(store.path, `${key}.json`);
      try {
        await fs.unlink(filePath);
      } catch (error) {
        // 文件可能不存在
      }
    }

    return existed;
  }

  /**
   * 获取所有键
   */
  async getKeys(agentId: string): Promise<string[]> {
    const store = this.stores.get(agentId);
    if (!store) {
      throw new Error(`Memory not initialized for agent ${agentId}`);
    }

    const keys = new Set(store.entries.keys());
    
    // 包含父级的键
    if (store.parent) {
      for (const key of store.parent.entries.keys()) {
        keys.add(key);
      }
    }

    return Array.from(keys);
  }

  /**
   * 设置权限
   */
  setPermission(agentId: string, resource: string, level: PermissionLevel): void {
    if (!this.permissions.has(agentId)) {
      this.permissions.set(agentId, new Map());
    }

    this.permissions.get(agentId)!.set(resource, level);
  }

  /**
   * 检查权限
   */
  checkPermission(agentId: string, resource: string, level: PermissionLevel): PermissionCheck {
    const agentPerms = this.permissions.get(agentId);
    if (!agentPerms) {
      return { agentId, resource, level, granted: false };
    }

    const grantedLevel = agentPerms.get(resource) || agentPerms.get('*');
    if (!grantedLevel) {
      return { agentId, resource, level, granted: false };
    }

    const levels = ['read', 'write', 'admin'];
    const requiredIndex = levels.indexOf(level);
    const grantedIndex = levels.indexOf(grantedLevel);

    return {
      agentId,
      resource,
      level,
      granted: grantedIndex >= requiredIndex
    };
  }

  /**
   * 构建上下文链
   */
  buildContextChain(agentId: string): ContextChain {
    const store = this.stores.get(agentId);
    if (!store) {
      throw new Error(`Memory not initialized for agent ${agentId}`);
    }

    const localContext: Record<string, any> = {};
    const inheritedKeys: string[] = [];

    // 收集本地上下文
    for (const [key, entry] of store.entries) {
      localContext[key] = entry.value;
    }

    // 收集继承的上下文
    if (store.parent) {
      for (const key of store.parent.entries.keys()) {
        if (!localContext[key]) {
          inheritedKeys.push(key);
          localContext[key] = store.parent.entries.get(key)!.value;
        }
      }
    }

    return {
      agentId,
      parentChain: store.parent ? this.buildContextChain(this.findAgentIdByStore(store.parent)) : undefined,
      localContext,
      inheritedKeys
    };
  }

  /**
   * 清理Agent的Memory
   */
  async cleanupMemory(agentId: string, deleteFiles: boolean = false): Promise<void> {
    const store = this.stores.get(agentId);
    if (!store) return;

    if (deleteFiles) {
      try {
        await fs.rmdir(store.path, { recursive: true });
      } catch (error) {
        console.error(`Failed to delete memory directory for ${agentId}:`, error);
      }
    }

    this.stores.delete(agentId);
    this.permissions.delete(agentId);
  }

  // ============ 私有方法 ============

  private async loadFromDisk(agentId: string): Promise<void> {
    const store = this.stores.get(agentId);
    if (!store) return;

    try {
      const files = await fs.readdir(store.path);
      
      for (const file of files) {
        if (file.endsWith('.json')) {
          try {
            const content = await fs.readFile(join(store.path, file), 'utf-8');
            const entry: MemoryEntry = JSON.parse(content);
            const key = file.replace('.json', '');
            store.entries.set(key, entry);
          } catch (error) {
            console.error(`Failed to load memory entry from ${file}:`, error);
          }
        }
      }
    } catch (error) {
      // 目录可能为空或不存在
    }
  }

  private async persistToDisk(agentId: string, key: string, entry: MemoryEntry): Promise<void> {
    const store = this.stores.get(agentId);
    if (!store || store.readOnly) return;

    const filePath = join(store.path, `${key}.json`);
    
    try {
      await fs.mkdir(dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, JSON.stringify(entry, null, 2), 'utf-8');
    } catch (error) {
      console.error(`Failed to persist memory entry ${key}:`, error);
    }
  }

  private findAgentIdByStore(targetStore: MemoryStore): string {
    for (const [agentId, store] of this.stores) {
      if (store === targetStore) {
        return agentId;
      }
    }
    return '';
  }
}

export const memorySystem = new MemorySystem();
