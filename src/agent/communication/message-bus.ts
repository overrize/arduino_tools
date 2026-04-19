import { EventEmitter } from 'events';
import { Message, MessageType, MessagePriority, MessageAck, AgentEvent, EventHandler } from '../types';
import { randomUUID } from 'crypto';

interface QueuedMessage {
  message: Message;
  retries: number;
  sentAt: number;
  ackTimeout?: NodeJS.Timeout;
}

interface Subscription {
  agentId: string;
  eventType: string;
  handler: EventHandler;
}

export class MessageBus extends EventEmitter {
  private messageQueue: Map<string, QueuedMessage> = new Map();
  private subscriptions: Map<string, Set<Subscription>> = new Map();
  private agentPorts: Map<string, any> = new Map();
  private stats = {
    totalSent: 0,
    totalDelivered: 0,
    totalFailed: 0,
    avgLatency: 0
  };
  
  private readonly MAX_RETRIES = 3;
  private readonly RETRY_DELAY = 1000;
  private readonly ACK_TIMEOUT = 30000;

  constructor() {
    super();
  }

  /**
   * 注册Agent的消息端口
   */
  registerAgentPort(agentId: string, port: any): void {
    this.agentPorts.set(agentId, port);
    
    port.on('message', (message: Message) => {
      this.handleIncomingMessage(message);
    });
  }

  /**
   * 注销Agent的消息端口
   */
  unregisterAgentPort(agentId: string): void {
    this.agentPorts.delete(agentId);
  }

  /**
   * 发送消息
   */
  async send(message: Omit<Message, 'id' | 'timestamp'>): Promise<MessageAck> {
    const fullMessage: Message = {
      ...message,
      id: randomUUID(),
      timestamp: Date.now()
    };

    const queued: QueuedMessage = {
      message: fullMessage,
      retries: 0,
      sentAt: Date.now()
    };

    this.messageQueue.set(fullMessage.id, queued);
    this.stats.totalSent++;

    const result = await this.routeMessage(fullMessage);
    
    if (result.status === 'delivered') {
      this.stats.totalDelivered++;
      this.updateLatency(Date.now() - queued.sentAt);
    } else {
      this.stats.totalFailed++;
    }

    return result;
  }

  /**
   * 广播消息给多个Agent
   */
  async broadcast(
    from: string,
    to: string[],
    type: MessageType,
    payload: any,
    priority: MessagePriority = 'normal'
  ): Promise<MessageAck[]> {
    const promises = to.map(agentId => 
      this.send({
        from,
        to: agentId,
        type,
        payload,
        priority,
        ttl: 60000
      })
    );

    return Promise.all(promises);
  }

  /**
   * 订阅事件
   */
  subscribe(agentId: string, eventType: string, handler: EventHandler): () => void {
    if (!this.subscriptions.has(eventType)) {
      this.subscriptions.set(eventType, new Set());
    }

    const subscription: Subscription = { agentId, eventType, handler };
    this.subscriptions.get(eventType)!.add(subscription);

    return () => {
      this.subscriptions.get(eventType)?.delete(subscription);
    };
  }

  /**
   * 发布事件
   */
  async publish(event: AgentEvent): Promise<void> {
    const subs = this.subscriptions.get(event.type);
    if (!subs) return;

    const promises: Promise<void>[] = [];
    
    for (const sub of subs) {
      if (sub.agentId !== event.source) {
        promises.push(
          Promise.resolve(sub.handler(event)).catch(err => {
            console.error(`Event handler error for ${event.type}:`, err);
          })
        );
      }
    }

    await Promise.all(promises);
    this.emit('event:published', event);
  }

  /**
   * 确认消息接收
   */
  acknowledge(messageId: string, status: 'delivered' | 'failed', error?: string): void {
    const queued = this.messageQueue.get(messageId);
    if (!queued) return;

    if (queued.ackTimeout) {
      clearTimeout(queued.ackTimeout);
    }

    if (status === 'failed' && queued.retries < this.MAX_RETRIES) {
      this.retryMessage(queued);
    } else {
      this.messageQueue.delete(messageId);
    }

    this.emit('message:acknowledged', { messageId, status, error });
  }

  /**
   * 获取消息统计
   */
  getStats() {
    return { ...this.stats };
  }

  /**
   * 清理过期的消息
   */
  cleanupExpiredMessages(): void {
    const now = Date.now();
    const TTL = 300000; // 5分钟

    for (const [id, queued] of this.messageQueue) {
      if (now - queued.sentAt > TTL) {
        if (queued.ackTimeout) {
          clearTimeout(queued.ackTimeout);
        }
        this.messageQueue.delete(id);
      }
    }
  }

  // ============ 私有方法 ============

  private async routeMessage(message: Message): Promise<MessageAck> {
    const targets = Array.isArray(message.to) ? message.to : [message.to];
    
    if (targets.includes('*')) {
      return this.routeToAll(message);
    }

    const results = await Promise.all(
      targets.map(target => this.routeToAgent(message, target))
    );

    const failed = results.filter(r => r.status === 'failed');
    if (failed.length === results.length) {
      return { messageId: message.id, status: 'failed', timestamp: Date.now(), error: 'All targets failed' };
    }

    return { messageId: message.id, status: 'delivered', timestamp: Date.now() };
  }

  private async routeToAgent(message: Message, agentId: string): Promise<MessageAck> {
    const port = this.agentPorts.get(agentId);
    
    if (!port) {
      return {
        messageId: message.id,
        status: 'failed',
        timestamp: Date.now(),
        error: `Agent ${agentId} not found`
      };
    }

    try {
      port.postMessage(message);
      
      this.setupAckTimeout(message.id);
      
      return { messageId: message.id, status: 'delivered', timestamp: Date.now() };
    } catch (error) {
      return {
        messageId: message.id,
        status: 'failed',
        timestamp: Date.now(),
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  private async routeToAll(message: Message): Promise<MessageAck> {
    const allAgents = Array.from(this.agentPorts.keys());
    const results = await Promise.all(
      allAgents.map(agentId => 
        agentId !== message.from ? this.routeToAgent(message, agentId) : null
      )
    );

    const validResults = results.filter(r => r !== null) as MessageAck[];
    const delivered = validResults.filter(r => r.status === 'delivered');

    return {
      messageId: message.id,
      status: delivered.length > 0 ? 'delivered' : 'failed',
      timestamp: Date.now()
    };
  }

  private setupAckTimeout(messageId: string): void {
    const queued = this.messageQueue.get(messageId);
    if (!queued) return;

    queued.ackTimeout = setTimeout(() => {
      if (queued.retries < this.MAX_RETRIES) {
        this.retryMessage(queued);
      } else {
        this.messageQueue.delete(messageId);
        this.emit('message:timeout', { messageId });
      }
    }, this.ACK_TIMEOUT);
  }

  private retryMessage(queued: QueuedMessage): void {
    queued.retries++;
    queued.sentAt = Date.now();
    
    setTimeout(() => {
      this.routeMessage(queued.message);
    }, this.RETRY_DELAY * queued.retries);
  }

  private handleIncomingMessage(message: Message): void {
    if (message.type === MessageType.HEARTBEAT_ACK) {
      return;
    }

    this.emit('message:received', message);
  }

  private updateLatency(latency: number): void {
    this.stats.avgLatency = (this.stats.avgLatency * 0.9) + (latency * 0.1);
  }
}

export const messageBus = new MessageBus();
