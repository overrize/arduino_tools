import { Skill, SkillContext, ContextChain } from '../types';

export const contextSharingSkill: Skill = {
  name: 'context_sharing',
  description: 'Share and inherit context between parent and child agents',
  version: '1.0.0',
  scope: 'global',
  
  async execute(args: any, context: SkillContext): Promise<any> {
    const { action, keys, contextData } = args;
    
    switch (action) {
      case 'get_context':
        return await getContext(keys, context);
      case 'share_context':
        return await shareContext(contextData, context);
      case 'inherit':
        return await inheritFromParent(keys, context);
      case 'get_chain':
        return await getContextChain(context);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  },

  validate(args: any): boolean {
    return args && typeof args.action === 'string';
  }
};

async function getContext(keys: string[], context: SkillContext): Promise<Record<string, any>> {
  const result: Record<string, any> = {};
  
  for (const key of keys) {
    const value = await context.memory.read(key);
    if (value !== undefined) {
      result[key] = value;
    }
  }
  
  return result;
}

async function shareContext(contextData: Record<string, any>, context: SkillContext): Promise<any> {
  const shared: string[] = [];
  
  for (const [key, value] of Object.entries(contextData)) {
    await context.memory.write(key, value, ['shared']);
    shared.push(key);
  }
  
  return { shared, count: shared.length };
}

async function inheritFromParent(keys: string[], context: SkillContext): Promise<Record<string, any>> {
  if (!context.parentId) {
    return {};
  }

  const result: Record<string, any> = {};
  
  // 请求父Agent的上下文
  await context.sendMessage(context.parentId, 'context_request', {
    keys,
    requester: context.agentId
  });
  
  // 实际实现需要等待响应并返回数据
  // 这里简化处理
  return result;
}

async function getContextChain(context: SkillContext): Promise<ContextChain> {
  // 构建上下文链
  const chain: ContextChain = {
    agentId: context.agentId,
    localContext: {},
    inheritedKeys: []
  };

  // 获取本地上下文
  // 实际实现需要根据具体存储机制获取
  
  if (context.parentId) {
    chain.parentChain = {
      agentId: context.parentId,
      localContext: {},
      inheritedKeys: []
    };
  }

  return chain;
}
