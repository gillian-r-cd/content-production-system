// web/src/components/layout/ProgressPanel.tsx
// 左侧进度栏
// 功能：显示阶段列表、状态图标、点击切换

import { Circle, CheckCircle, AlertCircle, RotateCw, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'
import { useUIStore } from '@/stores/uiStore'
import type { StageStatus } from '@/types'

interface StageItem {
  id: string
  name: string
  label: string
}

const STAGES: StageItem[] = [
  { id: 'intent', name: 'intent', label: '意图分析' },
  { id: 'research', name: 'research', label: '消费者调研' },
  { id: 'core_design', name: 'core_design', label: '内涵设计' },
  { id: 'core_production', name: 'core_production', label: '内涵生产' },
  { id: 'extension', name: 'extension', label: '外延生产' },
]

function getStatusIcon(status: StageStatus | undefined) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-success" />
    case 'in_progress':
      return <ArrowRight className="w-4 h-4 text-primary" />
    case 'blocked':
      return <AlertCircle className="w-4 h-4 text-error" />
    case 'iterating':
      return <RotateCw className="w-4 h-4 text-warning animate-spin" />
    default:
      return <Circle className="w-4 h-4 text-muted-foreground" />
  }
}

export default function ProgressPanel() {
  const { status } = useWorkflowStore()
  const { selectedStage, setSelectedStage } = useUIStore()

  const stages = status?.stages || {}
  const currentStage = status?.current_stage

  return (
    <div className="h-full flex flex-col p-4">
      <h2 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">
        项目进度
      </h2>
      
      <nav className="space-y-1">
        {STAGES.map((stage) => {
          const stageStatus = stages[stage.name] as StageStatus | undefined
          const isCurrent = currentStage === stage.name
          const isSelected = selectedStage === stage.name
          
          return (
            <button
              key={stage.id}
              onClick={() => setSelectedStage(stage.name)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-md text-left transition-colors",
                // 选中状态优先显示（用户点击的项目）
                isSelected && "bg-primary/10 text-primary font-medium",
                // 非选中状态的 hover 效果
                !isSelected && "hover:bg-accent"
              )}
            >
              <span className="flex-shrink-0">
                {getStatusIcon(stageStatus)}
              </span>
              <span className={cn(
                "text-sm flex-1",
                stageStatus === 'completed' && !isSelected && "text-success"
              )}>
                {stage.label}
              </span>
              {/* 当前阶段指示器（箭头） */}
              {isCurrent && (
                <ArrowRight className="w-3 h-3 text-primary flex-shrink-0" />
              )}
            </button>
          )
        })}
      </nav>

      {/* 分隔线 */}
      <div className="border-t my-4" />

      {/* 项目信息 */}
      {status && (
        <div className="text-xs text-muted-foreground space-y-1">
          <div>项目ID: {status.project_id}</div>
          <div>状态: {status.current_stage}</div>
        </div>
      )}
    </div>
  )
}



