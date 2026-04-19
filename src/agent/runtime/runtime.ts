/**
 * AgentRuntime - Agent运行时系统
 * 管理Agent的生命周期、Worker进程和状态
 */

import { EventEmitter } from 'events';
import { Worker } from 'worker_threads';
import { randomUUID } from 'crypto';
import { resolve } from 'path';
import {
  AgentInstance,
  AgentType,
  AgentStatus,
  AgentConfig,
  MemoryRef,
  SkillRef,
  RuntimeConfig,
  RuntimeStats,
  MessageType
} from '../types';

// 默认运行时配置
const DEFAULT_RUNTIME_CONFIG: RuntimeConfig = {
  maxAgents: 100,
  maxTasksPerAgent: 10,
  messageTimeout: 30000,
  heartbeatInterval: 5000,
  autoRestart: true,
  logLevel: 'info'
};

export class AgentRuntime extends EventEmitter {
  private agents: Map<string, AgentInstance> = new Map();
  private config: RuntimeConfig;
  private workerScriptPath: string;
  private stats: RuntimeStats;
  private startTime: number;
  private heartbeatTimers: Map<string, NodeJS.Timeout> = new Map();

  constructor(config: Partial<RuntimeConfig> = {}, workerScriptPath?: string) {
    super();
    this.config = { ...DEFAULT_RUNTIME_CONFIG, ...config };
    this.workerScriptPath = workerScriptPath || resolve(__dirname, 'worker.js');
    this.startTime = Date.now();
    this.stats = {
      totalAgents: 0,
      activeAgents: 0,
      terminatedAgents: 0,
      totalMessages: 0,
      pendingMessages: 0,
      avgMessageLatency: 0,
      uptime: 0
    };
  }

  /**
   * 初始化运行时
   */
  async initialize(): Promise<void> {
    this.log('info', 'AgentRuntime initializing...');
    
    // 启动统计更新定时器
    setInterval(() => this.updateStats(), 5000);
    
    this.log('info', 'AgentRuntime initialized successfully');
    this.emit('initialized');
  }

  /**
   * Fork一个新的Agent
   */
  async forkAgent(
    type: AgentType,
    parentId?: string,
    config: AgentConfig = {},
    memory?: MemoryRef,
    skills: SkillRef[] = []
  ): Promise<AgentInstance> {
    // 检查Agent数量限制
    if (this.agents.size >= this.config.maxAgents) {
      throw new Error(`Maximum agent limit (${this.config.maxAgents}) reached`);
    }

    // 验证父Agent存在（如果指定）
    if (parentId && !this.agents.has(parentId)) {
      throw new Error(`Parent agent ${parentId} not found`);
    }

    const agentId = this.generateAgentId(type);
    
    try {
      // 创建Worker进程
      const worker = new Worker(this.workerScriptPath, {
        workerData: {
          agentId,
          type,
          parentId,
          config,
          memory,
          skills
        }
      });

      // 创建Agent实例
      const agent: AgentInstance = {
        id: agentId,
        type,
        parentId,
        status: 'idle',
        createdAt: new Date(),
        updatedAt: new Date(),
        memory: memory || { path: `./memory/${agentId}`, readOnly: false },
        skills,
        worker,
        config,
        metadata: {}
      };

      // 设置Worker事件处理
      this.setupWorkerHandlers(agent);

      // 存储Agent
      this.agents.set(agentId, agent);
      this.stats.totalAgents++;
      this.stats.activeAgents++;

      // 启动心跳检测
      this.startHeartbeat(agentId);

      this.log('info', `Agent ${agentId} of type ${type} forked successfully`);
      this.emit('agent:forked', agent);

      return agent;
    } catch (error) {
      this.log('error', `Failed to fork agent: ${error}`);
      throw error;
    }
  }

  /**
   * 终止一个Agent
   */
  async terminateAgent(agentId: string, force: boolean = false): Promise<boolean> {
    const agent = this.agents.get(agentId);
    if (!agent) {
      this.log('warn', `Agent ${agentId} not found for termination`);
      return false;
    }

    try {
      // 停止心跳检测
      this.stopHeartbeat(agentId);

      // 更新状态
      agent.status = 'terminated';
      agent.updatedAt = new Date();

      // 终止Worker
      if (agent.worker) {
        if (force) {
          await agent.worker.terminate();
        } else {
          // 发送终止消息，等待优雅关闭
          agent.worker.postMessage({
            type: MessageType.TERMINATE_REQUEST,
            payload: { agentId }
          });
          
          // 等待一段时间让Agent清理
          await this.waitForTermination(agentId, 5000);
        }
      }

      // 从Map中移除
      this.agents.delete(agentId);
      this.stats.activeAgents--;
      this.stats.terminatedAgents++;

      this.log('info', `Agent ${agentId} terminated successfully`);
      this.emit('agent:terminated', agentId);

      return true;
    } catch (error) {
      this.log('error', `Error terminating agent ${agentId}: ${error}`);
      
      // 强制清理
      this.agents.delete(agentId);
      this.stats.activeAgents--;
      
      return false;
    }
  }

  /**
   * 获取Agent实例
   */
  getAgent(agentId: string): AgentInstance | undefined {
    return this.agents.get(agentId);
  }

  /**
   * 获取所有Agent
   */
  getAllAgents(): AgentInstance[] {
    return Array.from(this.agents.values());
  }

  /**
   * 获取特定类型的Agent
   */
  getAgentsByType(type: AgentType): AgentInstance[] {
    return this.getAllAgents().filter(agent => agent.type === type);
  }

  /**
   * 获取子Agent
   */
  getChildAgents(parentId: string): AgentInstance[] {
    return this.getAllAgents().filter(agent => agent.parentId === parentId);
  }

  /**
   * 更新Agent状态
   */
  updateAgentStatus(agentId: string, status: AgentStatus): boolean {
    const agent = this.agents.get(agentId);
    if (!agent) return false;

    agent.status = status;
    agent.updatedAt = new Date();

    this.emit('agent:status:changed', { agentId, status });
    return true;
  }

  /**
   * 检查Agent是否存在
   */
  hasAgent(agentId: string): boolean {
    return this.agents.has(agentId);
  }

  /**
   * 获取运行时统计
   */
  getStats(): RuntimeStats {
    return {
      ...this.stats,
      uptime: Date.now() - this.startTime
    };
  }

  /**
   * 关闭运行时
   */
  async shutdown(): Promise<void> {
    this.log('info', 'AgentRuntime shutting down...');

    // 终止所有Agent
    const terminatePromises = this.getAllAgents().map(agent => 
      this.terminateAgent(agent.id, true)
    );
    
    await Promise.all(terminatePromises);

    this.agents.clear();
    this.heartbeatTimers.clear();

    this.log('info', 'AgentRuntime shut down successfully');
    this.emit('shutdown');
  }

  // ============ 私有方法 ============

  private generateAgentId(type: AgentType): string {
    const prefix = type.substring(0, 4).toUpperCase();
    const uuid = randomUUID().split('-')[0];
    return `${prefix}-${uuid}`;
  }

  private setupWorkerHandlers(agent: AgentInstance): void {
    if (!agent.worker) return;

    // 消息处理
    agent.worker.on('message', (message) => {
      this.emit('message:received', { agentId: agent.id, message });
      
      // 处理状态更新消息
      if (message.type === MessageType.STATUS_UPDATE) {
        this.updateAgentStatus(agent.id, message.payload.status);
      }
      
      // 处理错误消息
      if (message.type === MessageType.ERROR) {
        this.log('error', `Agent ${agent.id} error: ${message.payload.error}`);
        this.emit('agent:error', { agentId: agent.id, error: message.payload });
      }
    });

    // 错误处理
    agent.worker.on('error', (error) => {
      this.log('error', `Worker ${agent.id} error: ${error}`);
      
      if (agent.config?.autoRestart !== false && this.config.autoRestart) {
        this.restartAgent(agent);
      } else {
        this.updateAgentStatus(agent.id, 'error');
        this.emit('agent:error', { agentId: agent.id, error });
      }
    });

    // 退出处理
    agent.worker.on('exit', (code) => {
      if (code !== 0) {
        this.log('warn', `Worker ${agent.id} exited with code ${code}`);
        
        if (agent.status !== 'terminated' && agent.config?.autoRestart !== false) {
          this.restartAgent(agent);
        }
      }
    });
  }

  private async restartAgent(agent: AgentInstance): Promise<void> {
    this.log('info', `Restarting agent ${agent.id}...`);
    
    try {
      // 终止旧Worker
      if (agent.worker) {
        await agent.worker.terminate();
      }

      // 创建新Worker
      const newWorker = new Worker(this.workerScriptPath, {
        workerData: {
          agentId: agent.id,
          type: agent.type,
          parentId: agent.parentId,
          config: agent.config,
          memory: agent.memory,
          skills: agent.skills
        }
      });

      agent.worker = newWorker;
      agent.status = 'idle';
      agent.updatedAt = new Date();

      this.setupWorkerHandlers(agent);

      this.log('info', `Agent ${agent.id} restarted successfully`);
      this.emit('agent:restarted', agent);
    } catch (error) {
      this.log('error', `Failed to restart agent ${agent.id}: ${error}`);
      this.updateAgentStatus(agent.id, 'error');
    }
  }

  private startHeartbeat(agentId: string): void {
    if (this.heartbeatTimers.has(agentId)) return;

    const timer = setInterval(() => {
      const agent = this.agents.get(agentId);
      if (!agent || agent.status === 'terminated') {
        this.stopHeartbeat(agentId);
        return;
      }

      // 发送心跳消息
      if (agent.worker) {
        agent.worker.postMessage({
          type: MessageType.HEARTBEAT,
          payload: { timestamp: Date.now() }
        });
      }
    }, this.config.heartbeatInterval);

    this.heartbeatTimers.set(agentId, timer);
  }

  private stopHeartbeat(agentId: string): void {
    const timer = this.heartbeatTimers.get(agentId);
    if (timer) {
      clearInterval(timer);
      this.heartbeatTimers.delete(agentId);
    }
  }

  private async waitForTermination(agentId: string, timeout: number): Promise<void> {
    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (!this.agents.has(agentId)) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);

      setTimeout(() => {
        clearInterval(checkInterval);
        resolve();
      }, timeout);
    });
  }

  private updateStats(): void {
    this.stats.uptime = Date.now() - this.startTime;
  }

  private log(level: string, message: string): void {
    if (this.shouldLog(level)) {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] [AgentRuntime] [${level.toUpperCase()}] ${message}`);
    }
  }

  private shouldLog(level: string): boolean {
    const levels = ['debug', 'info', 'warn', 'error'];
    const configLevelIndex = levels.indexOf(this.config.logLevel);
    const messageLevelIndex = levels.indexOf(level);
    return messageLevelIndex >= configLevelIndex;
  }
}

// 导出单例
export const agentRuntime = new AgentRuntime();
