/**
 * Agent类型定义
 * 定义多Agent框架中所有核心类型和接口
 */

// Agent类型枚举
export type AgentType = 'master' | 'spawn' | 'coding' | 'debug' | 'task';

// Agent状态枚举
export type AgentStatus = 'idle' | 'running' | 'blocked' | 'terminated' | 'error';

// Agent实例接口
export interface AgentInstance {
  id: string;
  type: AgentType;
  parentId?: string;
  status: AgentStatus;
  createdAt: Date;
  updatedAt: Date;
  memory: MemoryRef;
  skills: SkillRef[];
  worker?: Worker;
  config?: AgentConfig;
  metadata?: Record<string, any>;
}

// Agent配置接口
export interface AgentConfig {
  name?: string;
  description?: string;
  maxRetries?: number;
  timeout?: number;
  autoRestart?: boolean;
  inheritFromParent?: boolean;
  [key: string]: any;
}

// Memory引用接口
export interface MemoryRef {
  path: string;
  readOnly: boolean;
  inheritedFrom?: string;
}

// Skill引用接口
export interface SkillRef {
  name: string;
  version?: string;
  config?: Record<string, any>;
}

// 消息类型枚举
export enum MessageType {
  // Agent生命周期
  FORK_REQUEST = 'fork_request',
  FORK_RESPONSE = 'fork_response',
  TERMINATE_REQUEST = 'terminate_request',
  TERMINATE_RESPONSE = 'terminate_response',
  STATUS_UPDATE = 'status_update',
  
  // 任务相关
  TASK_ASSIGN = 'task_assign',
  TASK_RESULT = 'task_result',
  TASK_PROGRESS = 'task_progress',
  TASK_CANCEL = 'task_cancel',
  
  // 上下文共享
  CONTEXT_SHARE = 'context_share',
  CONTEXT_REQUEST = 'context_request',
  CONTEXT_RESPONSE = 'context_response',
  
  // 事件
  EVENT_BROADCAST = 'event_broadcast',
  EVENT_SUBSCRIBE = 'event_subscribe',
  EVENT_UNSUBSCRIBE = 'event_unsubscribe',
  
  // 心跳
  HEARTBEAT = 'heartbeat',
  HEARTBEAT_ACK = 'heartbeat_ack',
  
  // 错误
  ERROR = 'error',
  
  // 系统
  SYSTEM_COMMAND = 'system_command',
  SYSTEM_RESPONSE = 'system_response'
}

// 消息优先级
export type MessagePriority = 'high' | 'normal' | 'low';

// 消息接口
export interface Message {
  id: string;
  from: string;
  to: string | string[];
  type: MessageType;
  payload: any;
  timestamp: number;
  priority: MessagePriority;
  ttl?: number;
  replyTo?: string;
  correlationId?: string;
}

// 消息确认接口
export interface MessageAck {
  messageId: string;
  status: 'delivered' | 'failed' | 'timeout';
  timestamp: number;
  error?: string;
}

// 事件接口
export interface AgentEvent {
  type: string;
  source: string;
  payload: any;
  timestamp: number;
}

// 事件处理器类型
export type EventHandler = (event: AgentEvent) => void | Promise<void>;

// 任务接口
export interface Task {
  id: string;
  type: string;
  description: string;
  priority: MessagePriority;
  payload: any;
  dependencies?: string[];
  deadline?: number;
  metadata?: Record<string, any>;
}

// 任务结果接口
export interface TaskResult {
  taskId: string;
  status: 'success' | 'failed' | 'cancelled';
  output?: any;
  error?: string;
  duration: number;
  metadata?: Record<string, any>;
}

// 任务进度接口
export interface TaskProgress {
  taskId: string;
  percent: number;
  message: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

// Skill接口
export interface Skill {
  name: string;
  description: string;
  version: string;
  scope: 'global' | 'spawn' | 'task';
  permissions?: string[];
  execute: (args: any, context: SkillContext) => Promise<any>;
  validate?: (args: any) => boolean | Promise<boolean>;
}

// Skill上下文
export interface SkillContext {
  agentId: string;
  agentType: AgentType;
  memory: MemoryRef;
  parentId?: string;
  invokeSkill: (name: string, args: any) => Promise<any>;
  sendMessage: (to: string, type: MessageType, payload: any) => Promise<void>;
}

// Skill注册信息
export interface SkillRegistration {
  skill: Skill;
  loadedAt: Date;
  source: string;
  config?: Record<string, any>;
}

// 项目配置接口
export interface ProjectConfig {
  id: string;
  name: string;
  description: string;
  technologies: string[];
  priority: 'high' | 'medium' | 'low';
  estimatedDuration: string;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

// 上下文链接口
export interface ContextChain {
  agentId: string;
  parentChain?: ContextChain;
  localContext: Record<string, any>;
  inheritedKeys: string[];
}

// 内存条目接口
export interface MemoryEntry {
  key: string;
  value: any;
  createdAt: Date;
  updatedAt: Date;
  version: number;
  tags?: string[];
}

// 权限级别
export type PermissionLevel = 'read' | 'write' | 'admin';

// 权限检查接口
export interface PermissionCheck {
  agentId: string;
  resource: string;
  level: PermissionLevel;
  granted: boolean;
}

// Agent运行时配置
export interface RuntimeConfig {
  maxAgents: number;
  maxTasksPerAgent: number;
  messageTimeout: number;
  heartbeatInterval: number;
  autoRestart: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

// 运行时统计
export interface RuntimeStats {
  totalAgents: number;
  activeAgents: number;
  terminatedAgents: number;
  totalMessages: number;
  pendingMessages: number;
  avgMessageLatency: number;
  uptime: number;
}
