import { Skill, SkillContext, MessageType } from '../types';

export const communicationSkill: Skill = {
  name: 'communication',
  description: 'Send messages and communicate with other agents',
  version: '1.0.0',
  scope: 'global',
  
  async execute(args: any, context: SkillContext): Promise<any> {
    const { action, target, message, messageType } = args;
    
    switch (action) {
      case 'send':
        return await sendMessage(target, messageType || MessageType.SYSTEM_COMMAND, message, context);
      case 'broadcast':
        return await broadcastMessage(messageType || MessageType.EVENT_BROADCAST, message, context);
      case 'request_context':
        return await requestContext(target, context);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  },

  validate(args: any): boolean {
    return args && typeof args.action === 'string';
  }
};

async function sendMessage(
  target: string,
  type: MessageType,
  payload: any,
  context: SkillContext
): Promise<any> {
  await context.sendMessage(target, type, payload);
  return { sent: true, target, timestamp: Date.now() };
}

async function broadcastMessage(
  type: MessageType,
  payload: any,
  context: SkillContext
): Promise<any> {
  // 广播消息需要发送给所有相关Agent
  // 实际实现会根据架构决定如何广播
  return { broadcast: true, timestamp: Date.now() };
}

async function requestContext(target: string, context: SkillContext): Promise<any> {
  await context.sendMessage(target, MessageType.CONTEXT_REQUEST, {
    requester: context.agentId
  });
  
  // 这里应该等待响应，实际实现可能需要更复杂的异步处理
  return { requested: true, target };
}
