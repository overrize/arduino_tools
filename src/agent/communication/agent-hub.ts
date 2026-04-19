import { EventEmitter } from 'events';
import { MessageType, MessagePriority, AgentEvent } from '../../agent/types';
import { messageBus } from '../../agent/communication/message-bus';

interface AgentMessage {
  from: string;
  to: string;
  type: MessageType;
  payload: any;
  timestamp: number;
}

export class AgentCommunicationHub extends EventEmitter {
  private agentId: string;
  private parentId?: string;
  private children: Set<string> = new Set();
  private messageHandlers: Map<MessageType, Function> = new Map();

  constructor(agentId: string, parentId?: string) {
    super();
    this.agentId = agentId;
    this.parentId = parentId;
    this.setupDefaultHandlers();
  }

  registerChild(childId: string): void {
    this.children.add(childId);
    this.emit('child:registered', childId);
  }

  unregisterChild(childId: string): void {
    this.children.delete(childId);
    this.emit('child:unregistered', childId);
  }

  async sendToParent(type: MessageType, payload: any): Promise<void> {
    if (!this.parentId) {
      throw new Error('No parent agent registered');
    }
    await this.send(this.parentId, type, payload);
  }

  async sendToChild(childId: string, type: MessageType, payload: any): Promise<void> {
    if (!this.children.has(childId)) {
      throw new Error(`Child agent ${childId} not registered`);
    }
    await this.send(childId, type, payload);
  }

  async sendToAllChildren(type: MessageType, payload: any): Promise<void> {
    const promises = Array.from(this.children).map(childId => 
      this.send(childId, type, payload).catch(err => {
        console.error(`Failed to send to child ${childId}:`, err);
      })
    );
    await Promise.all(promises);
  }

  async broadcast(type: MessageType, payload: any): Promise<void> {
    await messageBus.send({
      from: this.agentId,
      to: '*',
      type,
      payload,
      priority: 'normal' as MessagePriority,
    });
  }

  async requestParentContext(): Promise<any> {
    if (!this.parentId) return null;
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Context request timeout'));
      }, 5000);

      this.once('context:received', (context) => {
        clearTimeout(timeout);
        resolve(context);
      });

      this.sendToParent(MessageType.CONTEXT_REQUEST, {
        requester: this.agentId,
      }).catch(reject);
    });
  }

  async reportProgress(taskId: string, percent: number, message: string): Promise<void> {
    const progress = {
      taskId,
      agentId: this.agentId,
      percent,
      message,
      timestamp: Date.now(),
    };

    if (this.parentId) {
      await this.sendToParent(MessageType.TASK_PROGRESS, progress);
    }

    this.emit('progress:reported', progress);
  }

  async reportResult(taskId: string, result: any): Promise<void> {
    const taskResult = {
      taskId,
      agentId: this.agentId,
      result,
      timestamp: Date.now(),
    };

    if (this.parentId) {
      await this.sendToParent(MessageType.TASK_RESULT, taskResult);
    }

    this.emit('result:reported', taskResult);
  }

  async reportError(error: Error, context?: any): Promise<void> {
    const errorInfo = {
      agentId: this.agentId,
      error: error.message,
      stack: error.stack,
      context,
      timestamp: Date.now(),
    };

    if (this.parentId) {
      await this.sendToParent(MessageType.ERROR, errorInfo);
    }

    this.emit('error:reported', errorInfo);
  }

  onMessage(type: MessageType, handler: (payload: any, from: string) => void): () => void {
    const wrappedHandler = (event: AgentEvent) => {
      if (event.type === type) {
        handler(event.payload, event.source);
      }
    };

    messageBus.subscribe(this.agentId, type, wrappedHandler);
    
    return () => {
      messageBus.unsubscribe?.(this.agentId, type, wrappedHandler);
    };
  }

  onChildMessage(childId: string, handler: (message: any) => void): void {
    const unsubscribe = this.onMessage(MessageType.STATUS_UPDATE, (payload, from) => {
      if (from === childId) {
        handler(payload);
      }
    });

    this.once('child:unregistered', (id) => {
      if (id === childId) {
        unsubscribe();
      }
    });
  }

  getChildren(): string[] {
    return Array.from(this.children);
  }

  getParent(): string | undefined {
    return this.parentId;
  }

  private async send(to: string, type: MessageType, payload: any): Promise<void> {
    await messageBus.send({
      from: this.agentId,
      to,
      type,
      payload,
      priority: 'normal' as MessagePriority,
    });

    this.emit('message:sent', { to, type, payload });
  }

  private setupDefaultHandlers(): void {
    this.onMessage(MessageType.CONTEXT_REQUEST, async (payload, from) => {
      if (this.children.has(from)) {
        const context = await this.gatherContext();
        await this.sendToChild(from, MessageType.CONTEXT_RESPONSE, context);
      }
    });

    this.onMessage(MessageType.CONTEXT_RESPONSE, (payload) => {
      this.emit('context:received', payload);
    });

    this.onMessage(MessageType.TASK_PROGRESS, (payload, from) => {
      if (this.children.has(from) || from === this.parentId) {
        this.emit('task:progress', { ...payload, from });
      }
    });

    this.onMessage(MessageType.TASK_RESULT, (payload, from) => {
      if (this.children.has(from)) {
        this.emit('task:completed', { ...payload, from });
        this.unregisterChild(from);
      }
    });

    this.onMessage(MessageType.ERROR, (payload, from) => {
      this.emit('agent:error', { ...payload, from });
    });

    this.onMessage(MessageType.HEARTBEAT, (payload, from) => {
      if (this.children.has(from)) {
        this.emit('child:heartbeat', { agentId: from, timestamp: payload.timestamp });
      }
    });
  }

  private async gatherContext(): Promise<any> {
    return {
      agentId: this.agentId,
      children: Array.from(this.children),
      timestamp: Date.now(),
    };
  }
}
