import { EventEmitter } from 'events';
import { AgentType, MessageType, ProjectConfig, RuntimeStats } from '../../agent/types';
import { agentRuntime } from '../../agent/runtime/runtime';
import { messageBus } from '../../agent/communication/message-bus';
import { memorySystem } from '../../agent/memory/memory';
import { skillRegistry } from '../../agent/skills/registry';
import { AgentCommunicationHub } from '../../agent/communication/agent-hub';

export interface Command {
  type: string;
  payload: any;
  source: string;
}

export interface Request {
  id: string;
  type: string;
  payload: any;
  respond: (response: any) => void;
}

interface AgentState {
  agents: Map<string, any>;
  projects: Map<string, any>;
  stats: RuntimeStats;
}

export class MasterAgent extends EventEmitter {
  private id: string;
  private state: AgentState;
  private commandHandlers: Map<string, Function>;
  private running: boolean = false;
  private communicationHub: AgentCommunicationHub;

  constructor() {
    super();
    this.id = 'MASTER-' + Date.now();
    this.state = {
      agents: new Map(),
      projects: new Map(),
      stats: agentRuntime.getStats(),
    };
    this.commandHandlers = new Map();
    this.communicationHub = new AgentCommunicationHub(this.id);
    this.setupCommandHandlers();
    this.setupCommunicationHandlers();
  }

  async initialize(): Promise<void> {
    await agentRuntime.initialize();
    
    const memoryRef = {
      path: `./memory/${this.id}`,
      readOnly: false,
    };
    await memorySystem.initializeMemory(this.id, memoryRef);

    this.running = true;
    this.emit('initialized', { agentId: this.id });
  }

  async receiveCommand(cmd: Command): Promise<any> {
    const handler = this.commandHandlers.get(cmd.type);
    if (!handler) {
      throw new Error(`Unknown command type: ${cmd.type}`);
    }
    return await handler(cmd.payload, cmd.source);
  }

  async handleUserInteraction(input: any): Promise<any> {
    if (typeof input === 'string') {
      return await this.processNaturalLanguage(input);
    }
    return await this.receiveCommand(input as Command);
  }

  async routeRequest(request: Request): Promise<void> {
    const { type, payload, respond } = request;
    
    try {
      let result;
      switch (type) {
        case 'agent_status':
          result = this.getAgentStatus(payload.agentId);
          break;
        case 'project_list':
          result = this.listProjects();
          break;
        case 'stats':
          result = this.getStats();
          break;
        default:
          result = { error: `Unknown request type: ${type}` };
      }
      respond(result);
    } catch (error) {
      respond({ error: error instanceof Error ? error.message : String(error) });
    }
  }

  getId(): string {
    return this.id;
  }

  isRunning(): boolean {
    return this.running;
  }

  getCommunicationHub(): AgentCommunicationHub {
    return this.communicationHub;
  }

  async shutdown(): Promise<void> {
    this.running = false;
    
    for (const [agentId] of this.state.agents) {
      await this.terminateSpawnAgent(agentId);
    }
    await agentRuntime.shutdown();
    this.emit('shutdown');
  }

  private setupCommandHandlers(): void {
    this.commandHandlers.set('create_project', this.handleCreateProject.bind(this));
    this.commandHandlers.set('delete_project', this.handleDeleteProject.bind(this));
    this.commandHandlers.set('get_project', this.handleGetProject.bind(this));
    this.commandHandlers.set('list_projects', this.handleListProjects.bind(this));
    this.commandHandlers.set('fork_spawn', this.handleForkSpawn.bind(this));
    this.commandHandlers.set('terminate_agent', this.handleTerminateAgent.bind(this));
    this.commandHandlers.set('get_stats', this.handleGetStats.bind(this));
    this.commandHandlers.set('broadcast', this.handleBroadcast.bind(this));
  }

  private setupCommunicationHandlers(): void {
    this.communicationHub.on('task:progress', (data) => {
      this.emit('spawn:progress', data);
    });

    this.communicationHub.on('task:completed', (data) => {
      this.state.agents.delete(data.from);
      this.emit('spawn:completed', data);
    });

    this.communicationHub.on('agent:error', (data) => {
      this.emit('spawn:error', data);
    });

    this.communicationHub.on('child:heartbeat', (data) => {
      const agent = this.state.agents.get(data.agentId);
      if (agent) {
        agent.lastHeartbeat = data.timestamp;
      }
    });
  }

  private async handleCreateProject(payload: any, source: string): Promise<any> {
    const projectId = `proj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const project: ProjectConfig = {
      id: projectId,
      name: payload.name,
      description: payload.description || '',
      technologies: payload.technologies || [],
      priority: payload.priority || 'medium',
      estimatedDuration: payload.estimatedDuration || 'unknown',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    this.state.projects.set(projectId, project);
    await memorySystem.write(this.id, `project:${projectId}`, project);

    this.emit('project:created', { projectId, source });
    return project;
  }

  private async handleDeleteProject(payload: any, source: string): Promise<any> {
    const { projectId } = payload;
    const existed = this.state.projects.delete(projectId);
    
    if (existed) {
      await memorySystem.delete(this.id, `project:${projectId}`);
      this.emit('project:deleted', { projectId, source });
    }
    
    return { success: existed, projectId };
  }

  private async handleGetProject(payload: any, source: string): Promise<any> {
    return this.state.projects.get(payload.projectId) || null;
  }

  private async handleListProjects(payload: any, source: string): Promise<any> {
    return Array.from(this.state.projects.values());
  }

  private async handleForkSpawn(payload: any, source: string): Promise<any> {
    const { projectId, config } = payload;
    
    const spawnAgent = await agentRuntime.forkAgent(
      'spawn' as AgentType,
      this.id,
      { projectId, ...config }
    );

    this.communicationHub.registerChild(spawnAgent.id);

    const memoryRef = {
      path: `./memory/${spawnAgent.id}`,
      readOnly: false,
      inheritedFrom: this.id,
    };
    await memorySystem.initializeMemory(spawnAgent.id, memoryRef);

    this.state.agents.set(spawnAgent.id, {
      ...spawnAgent,
      projectId,
      createdBy: source,
      lastHeartbeat: Date.now(),
    });

    await this.communicationHub.sendToChild(spawnAgent.id, MessageType.CONTEXT_SHARE, {
      project: this.state.projects.get(projectId),
      masterId: this.id,
    });

    this.emit('spawn:forked', { agentId: spawnAgent.id, projectId });
    return spawnAgent;
  }

  private async handleTerminateAgent(payload: any, source: string): Promise<any> {
    const { agentId } = payload;
    return await this.terminateSpawnAgent(agentId);
  }

  private async terminateSpawnAgent(agentId: string): Promise<any> {
    const result = await agentRuntime.terminateAgent(agentId);
    
    if (result) {
      this.communicationHub.unregisterChild(agentId);
      this.state.agents.delete(agentId);
      await memorySystem.cleanupMemory(agentId);
      this.emit('agent:terminated', { agentId });
    }
    
    return { success: result, agentId };
  }

  private async handleBroadcast(payload: any, source: string): Promise<any> {
    const { message } = payload;
    await this.communicationHub.sendToAllChildren(MessageType.EVENT_BROADCAST, {
      from: 'master',
      message,
      timestamp: Date.now(),
    });
    return { broadcast: true, recipientCount: this.communicationHub.getChildren().length };
  }

  private async handleGetStats(payload: any, source: string): Promise<any> {
    return this.getStats();
  }

  private async processNaturalLanguage(input: string): Promise<any> {
    const lower = input.toLowerCase();

    if (lower.includes('create project') || lower.includes('new project')) {
      const name = input.replace(/.*project/i, '').trim() || 'New Project';
      return await this.handleCreateProject({ name }, 'natural_language');
    }

    if (lower.includes('list projects') || lower.includes('show projects')) {
      return await this.handleListProjects({}, 'natural_language');
    }

    if (lower.includes('broadcast') || lower.includes('notify all')) {
      const message = input.replace(/.*broadcast|.*notify all/i, '').trim();
      return await this.handleBroadcast({ message }, 'natural_language');
    }

    return { message: 'Command not recognized', input };
  }

  private getAgentStatus(agentId: string): any {
    return this.state.agents.get(agentId) || agentRuntime.getAgent(agentId);
  }

  private listProjects(): any[] {
    return Array.from(this.state.projects.values());
  }

  private getStats(): any {
    return {
      runtime: agentRuntime.getStats(),
      master: {
        managedAgents: this.state.agents.size,
        projects: this.state.projects.size,
        children: this.communicationHub.getChildren().length,
      },
    };
  }
}

export const masterAgent = new MasterAgent();
