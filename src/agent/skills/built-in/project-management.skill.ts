import { Skill, SkillContext, ProjectConfig } from '../types';

export const projectManagementSkill: Skill = {
  name: 'project_management',
  description: 'Manage projects including create, read, update, delete operations',
  version: '1.0.0',
  scope: 'spawn',
  
  async execute(args: any, context: SkillContext): Promise<any> {
    const { action, projectId, config } = args;
    
    switch (action) {
      case 'create':
        return await createProject(config, context);
      case 'get':
        return await getProject(projectId, context);
      case 'update':
        return await updateProject(projectId, config, context);
      case 'delete':
        return await deleteProject(projectId, context);
      case 'list':
        return await listProjects(context);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  },

  validate(args: any): boolean {
    return args && typeof args.action === 'string';
  }
};

async function createProject(config: ProjectConfig, context: SkillContext): Promise<any> {
  const project = {
    ...config,
    id: generateId(),
    createdAt: new Date(),
    updatedAt: new Date()
  };

  // 存储到Memory
  const projects = (await context.memory.read('projects')) || [];
  projects.push(project);
  await context.memory.write('projects', projects);

  return project;
}

async function getProject(projectId: string, context: SkillContext): Promise<any> {
  const projects = (await context.memory.read('projects')) || [];
  return projects.find((p: any) => p.id === projectId);
}

async function updateProject(
  projectId: string,
  updates: Partial<ProjectConfig>,
  context: SkillContext
): Promise<any> {
  const projects = (await context.memory.read('projects')) || [];
  const index = projects.findIndex((p: any) => p.id === projectId);
  
  if (index === -1) {
    throw new Error(`Project ${projectId} not found`);
  }

  projects[index] = {
    ...projects[index],
    ...updates,
    updatedAt: new Date()
  };

  await context.memory.write('projects', projects);
  return projects[index];
}

async function deleteProject(projectId: string, context: SkillContext): Promise<boolean> {
  const projects = (await context.memory.read('projects')) || [];
  const filtered = projects.filter((p: any) => p.id !== projectId);
  
  if (filtered.length === projects.length) {
    return false;
  }

  await context.memory.write('projects', filtered);
  return true;
}

async function listProjects(context: SkillContext): Promise<any[]> {
  return (await context.memory.read('projects')) || [];
}

function generateId(): string {
  return `proj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
