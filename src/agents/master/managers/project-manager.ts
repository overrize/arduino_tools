import { MasterAgent } from './master-agent';

export class ProjectManager {
  private master: MasterAgent;

  constructor(master: MasterAgent) {
    this.master = master;
  }

  async createProject(config: {
    name: string;
    description?: string;
    technologies?: string[];
    priority?: 'high' | 'medium' | 'low';
    estimatedDuration?: string;
  }): Promise<any> {
    return await this.master.receiveCommand({
      type: 'create_project',
      payload: config,
      source: 'ProjectManager',
    });
  }

  async deleteProject(projectId: string): Promise<any> {
    return await this.master.receiveCommand({
      type: 'delete_project',
      payload: { projectId },
      source: 'ProjectManager',
    });
  }

  async getProject(projectId: string): Promise<any> {
    return await this.master.receiveCommand({
      type: 'get_project',
      payload: { projectId },
      source: 'ProjectManager',
    });
  }

  async listProjects(): Promise<any[]> {
    return await this.master.receiveCommand({
      type: 'list_projects',
      payload: {},
      source: 'ProjectManager',
    });
  }

  async updateProject(
    projectId: string,
    updates: Partial<{
      name: string;
      description: string;
      technologies: string[];
      priority: 'high' | 'medium' | 'low';
      estimatedDuration: string;
    }>
  ): Promise<any> {
    const project = await this.getProject(projectId);
    if (!project) {
      throw new Error(`Project ${projectId} not found`);
    }

    const updated = {
      ...project,
      ...updates,
      updatedAt: new Date(),
    };

    await this.master.receiveCommand({
      type: 'create_project',
      payload: updated,
      source: 'ProjectManager',
    });

    return updated;
  }
}
