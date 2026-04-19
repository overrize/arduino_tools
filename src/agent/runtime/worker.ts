/**
 * Worker进程脚本
 * 每个Agent运行在独立的Worker线程中
 */

import { parentPort, workerData } from 'worker_threads';
import { MessageType, AgentStatus } from '../types';

const { agentId, type, parentId, config, memory, skills } = workerData;

// Agent状态
let status: AgentStatus = 'idle';
let lastHeartbeat = Date.now();

// 消息处理器映射
const messageHandlers: Map<MessageType, Function> = new Map();

// 初始化
async function initialize() {
  setupMessageHandlers();
  
  // 通知父进程已就绪
  sendMessage({
    type: MessageType.STATUS_UPDATE,
    payload: { status: 'idle', agentId }
  });
  
  console.log(`[Worker ${agentId}] Agent of type ${type} initialized`);
}

// 设置消息处理器
function setupMessageHandlers() {
  messageHandlers.set(MessageType.TERMINATE_REQUEST, handleTerminate);
  messageHandlers.set(MessageType.HEARTBEAT, handleHeartbeat);
  messageHandlers.set(MessageType.TASK_ASSIGN, handleTaskAssign);
  messageHandlers.set(MessageType.CONTEXT_SHARE, handleContextShare);
}

// 处理终止请求
async function handleTerminate(payload: any) {
  console.log(`[Worker ${agentId}] Received terminate request`);
  
  // 执行清理
  await cleanup();
  
  // 更新状态
  status = 'terminated';
  
  // 发送响应
  sendMessage({
    type: MessageType.TERMINATE_RESPONSE,
    payload: { agentId, status: 'success' }
  });
  
  // 退出进程
  process.exit(0);
}

// 处理心跳
function handleHeartbeat(payload: any) {
  lastHeartbeat = Date.now();
  
  sendMessage({
    type: MessageType.HEARTBEAT_ACK,
    payload: { agentId, timestamp: lastHeartbeat }
  });
}

// 处理任务分配
async function handleTaskAssign(payload: any) {
  const { taskId, task } = payload;
  
  console.log(`[Worker ${agentId}] Received task ${taskId}`);
  
  try {
    status = 'running';
    updateStatus();
    
    // 发送进度更新
    sendProgress(taskId, 0, 'Task started');
    
    // 模拟任务执行
    await executeTask(taskId, task);
    
    // 发送完成消息
    sendMessage({
      type: MessageType.TASK_RESULT,
      payload: {
        taskId,
        status: 'success',
        output: { result: `Task ${taskId} completed` },
        duration: Date.now() - lastHeartbeat
      }
    });
    
  } catch (error) {
    sendMessage({
      type: MessageType.TASK_RESULT,
      payload: {
        taskId,
        status: 'failed',
        error: error instanceof Error ? error.message : String(error),
        duration: Date.now() - lastHeartbeat
      }
    });
  } finally {
    status = 'idle';
    updateStatus();
  }
}

// 执行任务
async function executeTask(taskId: string, task: any) {
  // 这里会根据任务类型执行不同的逻辑
  // 实际实现中会有具体的任务处理逻辑
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  sendProgress(taskId, 50, 'Task in progress');
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  sendProgress(taskId, 100, 'Task completed');
}

// 处理上下文共享
function handleContextShare(payload: any) {
  const { context } = payload;
  console.log(`[Worker ${agentId}] Received context update`);
  // 存储或更新上下文
}

// 发送消息到父进程
function sendMessage(message: any) {
  if (parentPort) {
    parentPort.postMessage({
      ...message,
      from: agentId,
      timestamp: Date.now()
    });
  }
}

// 发送进度更新
function sendProgress(taskId: string, percent: number, message: string) {
  sendMessage({
    type: MessageType.TASK_PROGRESS,
    payload: { taskId, percent, message, timestamp: Date.now() }
  });
}

// 更新状态
function updateStatus() {
  sendMessage({
    type: MessageType.STATUS_UPDATE,
    payload: { status, agentId }
  });
}

// 清理
async function cleanup() {
  console.log(`[Worker ${agentId}] Cleaning up...`);
  // 执行必要的清理操作
}

// 主消息循环
if (parentPort) {
  parentPort.on('message', async (message) => {
    const { type, payload } = message;
    const handler = messageHandlers.get(type);
    
    if (handler) {
      try {
        await handler(payload);
      } catch (error) {
        sendMessage({
          type: MessageType.ERROR,
          payload: {
            error: error instanceof Error ? error.message : String(error),
            type,
            agentId
          }
        });
      }
    } else {
      console.log(`[Worker ${agentId}] Unknown message type: ${type}`);
    }
  });
}

// 启动
initialize();
