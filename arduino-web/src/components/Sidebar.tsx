import React from 'react';
import { Plus, Settings, Trash2, Folder, Download } from 'lucide-react';
import { Project } from '../types';
import './Sidebar.css';

interface SidebarProps {
  projects: Project[];
  currentProject: Project | null;
  onSelectProject: (projectId: string) => void;
  onDeleteProject: (projectId: string) => void;
  onNewProject: () => void;
  onOpenSettings: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  projects,
  currentProject,
  onSelectProject,
  onDeleteProject,
  onNewProject,
  onOpenSettings,
}) => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1 className="app-title">
          <span className="app-icon">⚡</span>
          Arduino Web
        </h1>
        <div className="header-actions">
          <button className="icon-button" onClick={onNewProject} title="新建项目">
            <Plus size={20} />
          </button>
          <button className="icon-button" onClick={onOpenSettings} title="设置">
            <Settings size={20} />
          </button>
        </div>
      </div>

      <div className="sidebar-content">
        <div className="section-title">
          <Folder size={16} />
          <span>项目历史</span>
        </div>

        <div className="project-list">
          {projects.length === 0 ? (
            <div className="empty-state">
              <p>暂无项目</p>
              <p className="hint">点击 + 创建新项目</p>
            </div>
          ) : (
            projects.map((project) => (
              <div
                key={project.id}
                className={`project-item ${currentProject?.id === project.id ? 'active' : ''}`}
                onClick={() => onSelectProject(project.id)}
              >
                <div className="project-info">
                  <span className="project-name">{project.name}</span>
                  <span className="project-board">{project.board}</span>
                </div>
                <button
                  className="delete-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteProject(project.id);
                  }}
                  title="删除项目"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        <span className="version">Web v0.1.0</span>
      </div>
    </div>
  );
};

export default Sidebar;
