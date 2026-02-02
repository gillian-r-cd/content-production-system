import { CheckCircle, Circle, ArrowRight, AlertCircle, RotateCw } from 'lucide-react'
import type { Stage, StageInfo } from '../App'
import './Sidebar.css'

interface SidebarProps {
  stages: StageInfo[]
  currentStage: Stage
  onStageClick: (stage: Stage) => void
}

const statusIcons = {
  pending: <Circle size={16} />,
  in_progress: <ArrowRight size={16} />,
  completed: <CheckCircle size={16} />,
  blocked: <AlertCircle size={16} />,
  iterating: <RotateCw size={16} />,
}

export function Sidebar({ stages, currentStage, onStageClick }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>流程进度</h2>
      </div>
      
      <nav className="stage-list">
        {stages.map((stage, index) => (
          <button
            key={stage.id}
            className={`stage-item ${stage.status} ${stage.id === currentStage ? 'active' : ''}`}
            onClick={() => onStageClick(stage.id)}
            disabled={stage.status === 'pending' && index > 0}
          >
            <span className={`stage-icon status-${stage.status}`}>
              {statusIcons[stage.status]}
            </span>
            <span className="stage-name">{stage.name}</span>
          </button>
        ))}
      </nav>
      
      <div className="sidebar-footer">
        <div className="progress-info">
          <span className="progress-label">完成进度</span>
          <span className="progress-value">
            {stages.filter(s => s.status === 'completed').length}/{stages.length}
          </span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ 
              width: `${(stages.filter(s => s.status === 'completed').length / stages.length) * 100}%` 
            }}
          />
        </div>
      </div>
    </aside>
  )
}

