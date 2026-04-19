import { AgentCommunicationHub } from '../../agent/communication/agent-hub';
import { MessageType } from '../../agent/types';
import { EventEmitter } from 'events';

jest.mock('../../agent/communication/message-bus', () => ({
  messageBus: {
    send: jest.fn().mockResolvedValue({ messageId: 'test-msg', status: 'delivered' }),
    subscribe: jest.fn().mockReturnValue(() => {}),
  },
}));

describe('AgentCommunicationHub', () => {
  let hub: AgentCommunicationHub;
  const agentId = 'AGENT-TEST-123';
  const parentId = 'PARENT-TEST-456';

  beforeEach(() => {
    hub = new AgentCommunicationHub(agentId, parentId);
  });

  describe('child management', () => {
    test('should register child', () => {
      const handler = jest.fn();
      hub.on('child:registered', handler);

      hub.registerChild('CHILD-1');

      expect(handler).toHaveBeenCalledWith('CHILD-1');
      expect(hub.getChildren()).toContain('CHILD-1');
    });

    test('should unregister child', () => {
      hub.registerChild('CHILD-1');
      
      const handler = jest.fn();
      hub.on('child:unregistered', handler);

      hub.unregisterChild('CHILD-1');

      expect(handler).toHaveBeenCalledWith('CHILD-1');
      expect(hub.getChildren()).not.toContain('CHILD-1');
    });
  });

  describe('message sending', () => {
    test('should send to parent', async () => {
      const { messageBus } = require('../../agent/communication/message-bus');
      
      await hub.sendToParent(MessageType.TASK_PROGRESS, { percent: 50 });

      expect(messageBus.send).toHaveBeenCalledWith(
        expect.objectContaining({
          from: agentId,
          to: parentId,
          type: MessageType.TASK_PROGRESS,
        })
      );
    });

    test('should throw when sending to parent without parent', async () => {
      const orphanHub = new AgentCommunicationHub('ORPHAN');
      
      await expect(orphanHub.sendToParent(MessageType.TASK_PROGRESS, {}))
        .rejects.toThrow('No parent agent registered');
    });

    test('should send to child', async () => {
      hub.registerChild('CHILD-1');
      const { messageBus } = require('../../agent/communication/message-bus');
      
      await hub.sendToChild('CHILD-1', MessageType.TASK_ASSIGN, { task: 'test' });

      expect(messageBus.send).toHaveBeenCalledWith(
        expect.objectContaining({
          from: agentId,
          to: 'CHILD-1',
          type: MessageType.TASK_ASSIGN,
        })
      );
    });

    test('should throw when sending to unregistered child', async () => {
      await expect(hub.sendToChild('UNKNOWN', MessageType.TASK_ASSIGN, {}))
        .rejects.toThrow('Child agent UNKNOWN not registered');
    });

    test('should broadcast to all children', async () => {
      hub.registerChild('CHILD-1');
      hub.registerChild('CHILD-2');
      const { messageBus } = require('../../agent/communication/message-bus');
      
      await hub.sendToAllChildren(MessageType.EVENT_BROADCAST, { event: 'test' });

      expect(messageBus.send).toHaveBeenCalledTimes(2);
    });
  });

  describe('progress reporting', () => {
    test('should report progress to parent', async () => {
      const { messageBus } = require('../../agent/communication/message-bus');
      
      await hub.reportProgress('task-1', 50, 'Halfway done');

      expect(messageBus.send).toHaveBeenCalledWith(
        expect.objectContaining({
          type: MessageType.TASK_PROGRESS,
          payload: expect.objectContaining({
            taskId: 'task-1',
            percent: 50,
            message: 'Halfway done',
          }),
        })
      );
    });

    test('should emit progress event', async () => {
      const handler = jest.fn();
      hub.on('progress:reported', handler);

      await hub.reportProgress('task-1', 75, 'Almost done');

      expect(handler).toHaveBeenCalledWith(expect.objectContaining({
        taskId: 'task-1',
        percent: 75,
      }));
    });
  });

  describe('result reporting', () => {
    test('should report result to parent', async () => {
      const { messageBus } = require('../../agent/communication/message-bus');
      
      await hub.reportResult('task-1', { output: 'success' });

      expect(messageBus.send).toHaveBeenCalledWith(
        expect.objectContaining({
          type: MessageType.TASK_RESULT,
        })
      );
    });

    test('should emit result event', async () => {
      const handler = jest.fn();
      hub.on('result:reported', handler);

      await hub.reportResult('task-1', { data: 'test' });

      expect(handler).toHaveBeenCalled();
    });
  });

  describe('error reporting', () => {
    test('should report error to parent', async () => {
      const { messageBus } = require('../../agent/communication/message-bus');
      const error = new Error('Test error');
      
      await hub.reportError(error, { context: 'test' });

      expect(messageBus.send).toHaveBeenCalledWith(
        expect.objectContaining({
          type: MessageType.ERROR,
          payload: expect.objectContaining({
            error: 'Test error',
          }),
        })
      );
    });
  });

  describe('message handlers', () => {
    test('should handle context request from child', async () => {
      hub.registerChild('CHILD-1');
      const { messageBus } = require('../../agent/communication/message-bus');
      
      const unsubscribe = hub.onMessage(MessageType.CONTEXT_REQUEST, async (payload, from) => {
        if (from === 'CHILD-1') {
          await hub.sendToChild('CHILD-1', MessageType.CONTEXT_RESPONSE, { data: 'context' });
        }
      });

      expect(unsubscribe).toBeInstanceOf(Function);
    });

    test('should receive context from parent', () => {
      const handler = jest.fn();
      hub.on('context:received', handler);

      const { messageBus } = require('../../agent/communication/message-bus');
      const subscribeCallback = (messageBus.subscribe as jest.Mock).mock.calls[0][2];
      
      subscribeCallback({
        type: MessageType.CONTEXT_RESPONSE,
        source: parentId,
        payload: { data: 'parent-context' },
      });

      expect(handler).toHaveBeenCalledWith({ data: 'parent-context' });
    });
  });
});
