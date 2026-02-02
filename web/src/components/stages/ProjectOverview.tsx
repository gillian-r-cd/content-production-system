// web/src/components/stages/ProjectOverview.tsx
// 项目概览 - 显示项目的完整进度和数据
// 功能：加载既往项目后显示所有阶段的数据

import { useWorkflowStore } from '@/stores/workflowStore'
import { useUIStore } from '@/stores/uiStore'
import { 
  Target, 
  Users, 
  FileText, 
  Share2, 
  CheckCircle, 
  ChevronRight,
  Clock
} from 'lucide-react'

export default function ProjectOverview() {
  const { workflowData, status, currentProject } = useWorkflowStore()
  const { setSelectedStage } = useUIStore()
  
  const statusLabels: Record<string, string> = {
    draft: '草稿',
    intent: '意图分析中',
    research: '消费者调研中',
    core_design: '内涵设计中',
    core_production: '内涵生产中',
    extension: '外延生产中',
    completed: '已完成',
  }
  
  const handleViewStage = (stage: string) => {
    setSelectedStage(stage as any)
  }
  
  return (
    <div className="p-6 space-y-6">
      {/* 项目头部 */}
      <div className="border-b pb-6">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-2xl font-bold">{currentProject?.name || '项目'}</h1>
          <span className={`px-3 py-1 rounded-full text-sm ${
            status?.current_stage === 'completed' 
              ? 'bg-green-100 text-green-700' 
              : 'bg-blue-100 text-blue-700'
          }`}>
            {statusLabels[status?.current_stage || 'draft'] || status?.current_stage}
          </span>
        </div>
        <p className="text-muted-foreground text-sm">
          项目ID: {currentProject?.id}
        </p>
      </div>
      
      {/* 阶段卡片 */}
      <div className="grid gap-4">
        {/* 意图分析 */}
        <StageCard
          icon={<Target className="w-5 h-5" />}
          title="意图分析"
          status={workflowData?.intent ? 'completed' : 'pending'}
          onClick={() => handleViewStage('intent')}
        >
          {workflowData?.intent && (
            <div className="mt-3 space-y-2">
              <p className="text-sm font-medium">目标：</p>
              <p className="text-sm text-muted-foreground line-clamp-3">
                {workflowData.intent.goal}
              </p>
              {workflowData.intent.success_criteria && (
                <p className="text-xs text-muted-foreground">
                  {workflowData.intent.success_criteria.length} 个成功标准
                </p>
              )}
            </div>
          )}
        </StageCard>
        
        {/* 消费者调研 */}
        <StageCard
          icon={<Users className="w-5 h-5" />}
          title="消费者调研"
          status={workflowData?.consumer_research ? 'completed' : 'pending'}
          onClick={() => handleViewStage('research')}
        >
          {workflowData?.consumer_research && (
            <div className="mt-3">
              <p className="text-sm text-muted-foreground">
                调研数据已完成
              </p>
            </div>
          )}
        </StageCard>
        
        {/* 内涵设计/生产 */}
        <StageCard
          icon={<FileText className="w-5 h-5" />}
          title="内涵生产"
          status={workflowData?.content_core?.status === 'completed' ? 'completed' : 'pending'}
          onClick={() => handleViewStage('core_design')}
        >
          {workflowData?.content_core && (
            <div className="mt-3 space-y-2">
              {workflowData.content_core.design_schemes && (
                <p className="text-sm text-muted-foreground">
                  {workflowData.content_core.design_schemes.length} 个方案
                  {workflowData.content_core.selected_scheme_index !== null && 
                    ` (已选择方案 ${workflowData.content_core.selected_scheme_index + 1})`
                  }
                </p>
              )}
              {workflowData.content_core.fields && (
                <p className="text-sm text-muted-foreground">
                  {Object.keys(workflowData.content_core.fields).length} 个内容字段
                </p>
              )}
            </div>
          )}
        </StageCard>
        
        {/* 外延生产 */}
        <StageCard
          icon={<Share2 className="w-5 h-5" />}
          title="外延生产"
          status={workflowData?.content_extension?.status === 'completed' ? 'completed' : 'pending'}
          onClick={() => handleViewStage('extension')}
        >
          {workflowData?.content_extension && (
            <div className="mt-3">
              {workflowData.content_extension.channels && (
                <p className="text-sm text-muted-foreground">
                  {Object.keys(workflowData.content_extension.channels).length} 个渠道内容
                </p>
              )}
            </div>
          )}
        </StageCard>
      </div>
      
      {/* 快捷操作 */}
      {status?.current_stage !== 'completed' && status?.waiting_for_input && (
        <div className="mt-6 p-4 bg-primary/5 border border-primary/20 rounded-lg">
          <p className="text-sm font-medium mb-2">继续工作</p>
          <p className="text-sm text-muted-foreground">
            {status.input_prompt || '在右侧对话框继续交互'}
          </p>
        </div>
      )}
    </div>
  )
}

// 阶段卡片组件
interface StageCardProps {
  icon: React.ReactNode
  title: string
  status: 'completed' | 'in_progress' | 'pending'
  onClick: () => void
  children?: React.ReactNode
}

function StageCard({ icon, title, status, onClick, children }: StageCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 border rounded-lg hover:border-primary/50 hover:bg-accent/50 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            status === 'completed' 
              ? 'bg-green-100 text-green-600' 
              : status === 'in_progress'
              ? 'bg-blue-100 text-blue-600'
              : 'bg-muted text-muted-foreground'
          }`}>
            {status === 'completed' ? <CheckCircle className="w-5 h-5" /> : icon}
          </div>
          <div>
            <h3 className="font-medium">{title}</h3>
            <span className={`text-xs ${
              status === 'completed' 
                ? 'text-green-600' 
                : status === 'in_progress'
                ? 'text-blue-600'
                : 'text-muted-foreground'
            }`}>
              {status === 'completed' ? '已完成' : status === 'in_progress' ? '进行中' : '待开始'}
            </span>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-muted-foreground" />
      </div>
      {children}
    </button>
  )
}


