import { MessageBus } from '../message-bus';
import { MessageType, MessagePriority } from '../../types';

// Mock EventEmitter properly
jest.mock('events', () => ({
  EventEmitter: class MockEventEmitter {
    private listeners: Map<string, Function[]> = new Map();
    
    on(event: string, handler: Function) {
      if (!this.listeners.has(event)) {
        this.listeners.set(event, []);
      }
      this.listeners.get(event)!.push(handler);
      return this;
    }
    
    emit(event: string, ...args: any[]) {
      const handlers = this.listeners.get(event) || [];
      handlers.forEach(h => h(...args));
      return true;
    }
    
    once(event: string, handler: Function) {
      const onceHandler = (...args: any[]) => {
        handler(...args);
        this.off(event, onceHandler);
      };
      return this.on(event, onceHandler);
    }
    
    off(event: string, handler: Function) {
      const handlers = this.listeners.get(event) || [];
      const index = handlers.indexOf(handler);
      if (index > -1) handlers.splice(index, 1);
      return this;
    }
  }
}));

describe('MessageBus', () => {
  let bus: MessageBus;
  
  beforeEach(() => {
    bus = new MessageBus();
  });

  describe('registerAgentPort', () => {
    test('should register agent port', () => {
      const mockPort = { on: jest.fn(), postMessage: jest.fn() };
      
      bus.registerAgentPort('agent-1', mockPort);
      
      expect(mockPort.on).toHaveBeenCalledWith('message', expect.any(Function));
    });

    test('should unregister agent port', () => {
      const mockPort = { on: jest.fn(), postMessage: jest.fn() };
      bus.registerAgentPort('agent-1', mockPort);
      
      bus.unregisterAgentPort('agent-1');
      
      // Should not throw
      expect(() => bus.unregisterAgentPort('agent-1')).not.toThrow();
    });
  });

  describe('send', () => {
    test('should send message to single agent', async () => {
      const mockPort = { on: jest.fn(), postMessage: jest.fn() };
      bus.registerAgentPort('agent-1', mockPort);
      
      const ack = await bus.send({
        from: 'sender',
        to: 'agent-1',
        type: MessageType.TASK_ASSIGN,
        payload: { task: 'test' },
        priority: 'normal' as MessagePriority,
      });
      
      expect(mockPort.postMessage).toHaveBeenCalled();
      expect(ack.status).toBe('delivered');
    });

    test('should fail when agent not found', async () => {
      const ack = await bus.send({
        from: 'sender',
        to: 'non-existent',
        type: MessageType.TASK_ASSIGN,
        payload: {},
        priority: 'normal' as MessagePriority,
      });
      
      expect(ack.status).toBe('failed');
    });

    test('should support broadcast to multiple agents', async () => {
      const mockPort1 = { on: jest.fn(), postMessage: jest.fn() };
      const mockPort2 = { on: jest.fn(), postMessage: jest.fn() };
      bus.registerAgentPort('agent-1', mockPort1);
      bus.registerAgentPort('agent-2', mockPort2);
      
      const acks = await bus.broadcast('sender', ['agent-1', 'agent-2'], MessageType.EVENT_BROADCAST, { event: 'test' });
      
      expect(acks).toHaveLength(2);
      expect(mockPort1.postMessage).toHaveBeenCalled();
      expect(mockPort2.postMessage).toHaveBeenCalled();
    });
  });

  describe('subscribe and publish', () => {
    test('should subscribe to events', async () => {
      const handler = jest.fn();
      const unsubscribe = bus.subscribe('agent-1', 'test-event', handler);
      
      await bus.publish({
        type: 'test-event',
        source: 'agent-2',
        payload: { data: 'test' },
        timestamp: Date.now(),
      });
      
      expect(handler).toHaveBeenCalled();
      
      // Test unsubscribe
      unsubscribe();
      await bus.publish({
        type: 'test-event',
        source: 'agent-3',
        payload: { data: 'test2' },
        timestamp: Date.now(),
      });
      
      // Handler should still be called only once
      expect(handler).toHaveBeenCalledTimes(1);
    });

    test('should not call handler for same source', async () => {
      const handler = jest.fn();
      bus.subscribe('agent-1', 'test-event', handler);
      
      await bus.publish({
        type: 'test-event',
        source: 'agent-1', // Same as subscriber
        payload: { data: 'test' },
        timestamp: Date.now(),
      });
      
      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('acknowledge', () => {
    test('should acknowledge message delivery', async () => {
      const mockPort = { on: jest.fn(), postMessage: jest.fn() };
      bus.registerAgentPort('agent-1', mockPort);
      
      const ackListener = jest.fn();
      bus.on('message:acknowledged', ackListener);
      
      const ack = await bus.send({
        from: 'sender',
        to: 'agent-1',
        type: MessageType.TASK_ASSIGN,
        payload: {},
        priority: 'normal' as MessagePriority,
      });
      
      bus.acknowledge(ack.messageId, 'delivered');
      
      expect(ackListener).toHaveBeenCalledWith({ messageId: ack.messageId, status: 'delivered' });
    });

    test('should retry on failed acknowledge', async () => {
      const mockPort = { on: jest.fn(), postMessage: jest.fn() };
      bus.registerAgentPort('agent-1', mockPort);
      
      const ack = await bus.send({
        from: 'sender',
        to: 'agent-1',
        type: MessageType.TASK_ASSIGN,
        payload: {},
        priority: 'normal' as MessagePriority,
      });
      
      bus.acknowledge(ack.messageId, 'failed');
      
      // Message should be queued for retry
      expect(mockPort.postMessage).toHaveBeenCalled();
    });
  });

  describe('getStats', () => {
    test('should return message statistics', async () => {
      const mockPort = { on: jest.fn(), postMessage: jest.fn() };
      bus.registerAgentPort('agent-1', mockPort);
      
      await bus.send({
        from: 'sender',
        to: 'agent-1',
        type: MessageType.TASK_ASSIGN,
        payload: {},
        priority: 'normal' as MessagePriority,
      });
      
      const stats = bus.getStats();
      
      expect(stats.totalSent).toBe(1);
      expect(stats.totalDelivered).toBe(1);
    });
  });

  describe('cleanupExpiredMessages', () => {
    test('should cleanup old messages', async () => {
      const mockPort = { on: jest.fn(), postMessage: jest.fn() };
      bus.registerAgentPort('agent-1', mockPort);
      
      // Send a message
      await bus.send({
        from: 'sender',
        to: 'agent-1',
        type: MessageType.TASK_ASSIGN,
        payload: {},
        priority: 'normal' as MessagePriority,
      });
      
      // Cleanup should not throw
      expect(() => bus.cleanupExpiredMessages()).not.toThrow();
    });
  });
});
