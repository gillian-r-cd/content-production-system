// web/src/components/layout/EditorPanel.tsx
// 中间编辑区
// 功能：根据当前阶段显示不同的内容视图

import { useWorkflowStore } from '@/stores/workflowStore'
import { useUIStore } from '@/stores/uiStore'
import IntentStage from '../stages/IntentStage'
import ResearchStage from '../stages/ResearchStage'
import CoreDesignStage from '../stages/CoreDesignStage'
import CoreProductionStage from '../stages/CoreProductionStage'
import ProjectOverview from '../stages/ProjectOverview'
import WelcomeView from '../stages/WelcomeView'

export default function EditorPanel() {
  const { status, workflowData, currentProfile, currentProject } = useWorkflowStore()
  const { selectedStage, setSelectedStage } = useUIStore()
  
  // 如果没有开始工作流，显示欢迎界面
  if (!status && !currentProject) {
    return <WelcomeView />
  }
  
  // 如果有工作流数据但没有选择阶段，显示项目概览
  if (workflowData && !selectedStage) {
    return <ProjectOverview />
  }
  
  // 优先使用用户选择的阶段，否则使用当前阶段
  const displayStage = selectedStage || status?.current_stage || 'intent'
  
  // 根据阶段显示不同内容
  const renderStageContent = () => {
    switch (displayStage) {
      case 'intent':
        return <IntentStage />
      case 'research':
        return <ResearchStage />
      case 'core_design':
        return <CoreDesignStage />
      case 'core_production':
        return <CoreProductionStage />
      case 'extension':
        return (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">外延生产</h2>
            <p className="text-muted-foreground">外延生产阶段</p>
            {workflowData?.content_extension && (
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <pre className="text-sm whitespace-pre-wrap">
                  {JSON.stringify(workflowData.content_extension, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )
      case 'completed':
        return <ProjectOverview />
      default:
        return <WelcomeView />
    }
  }
  
  return (
    <div className="h-full overflow-auto">
      {renderStageContent()}
    </div>
  )
}
