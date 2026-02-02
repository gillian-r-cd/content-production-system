// web/src/components/layout/MainLayout.tsx
// 三栏主布局
// 功能：左侧进度栏 + 中间编辑区 + 右侧对话区

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Settings, Menu, ChevronLeft, ChevronRight, FolderOpen, Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { profilesApi } from '@/api'
import apiClient from '@/api/client'
import { useWorkflowStore } from '@/stores/workflowStore'
import { useUIStore } from '@/stores/uiStore'
import ProgressPanel from './ProgressPanel'
import EditorPanel from './EditorPanel'
import ChatPanel from './ChatPanel'
import SettingsDialog from '../settings/SettingsDialog'
import type { Profile } from '@/types'

interface ProjectListItem {
  id: string
  name: string
  status: string
  created_at: string
}

export default function MainLayout() {
  const queryClient = useQueryClient()
  const { leftPanelCollapsed, rightPanelCollapsed, toggleLeftPanel, toggleRightPanel, settingsOpen, setSettingsOpen } = useUIStore()
  const { currentProfile, setProfile, status, currentProject, workflowData, loadProject, reset } = useWorkflowStore()
  const [showProfileSelect, setShowProfileSelect] = useState(false)
  const [showProjectMenu, setShowProjectMenu] = useState(false)

  // 获取Profile列表
  const { data: profilesData, isLoading: profilesLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  })
  const profiles = Array.isArray(profilesData) ? profilesData : []

  // 获取项目列表
  const { data: projectsData, refetch: refetchProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const { data } = await apiClient.get('/projects')
      return data as ProjectListItem[]
    },
  })
  const projects = Array.isArray(projectsData) ? projectsData : []

  const handleSelectProfile = (profile: Profile) => {
    setProfile(profile)
    setShowProfileSelect(false)
  }

  const handleSwitchProject = async (projectId: string) => {
    setShowProjectMenu(false)
    await loadProject(projectId)
  }

  const handleNewProject = () => {
    setShowProjectMenu(false)
    reset() // 重置工作流状态，回到欢迎界面
  }

  const handleDeleteProject = async (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`确定要删除项目 ${projectId} 吗？此操作不可恢复。`)) {
      return
    }
    try {
      await apiClient.delete(`/projects/${projectId}`)
      await refetchProjects()
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      // 如果删除的是当前项目，重置状态
      if (currentProject?.id === projectId) {
        reset()
      }
    } catch (error) {
      console.error('删除项目失败:', error)
      alert('删除项目失败')
    }
  }

  const statusLabels: Record<string, string> = {
    draft: '草稿',
    intent: '意图分析',
    research: '消费者调研',
    core_design: '内涵设计',
    core_production: '内涵生产',
    extension: '外延生产',
    completed: '已完成',
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* 顶部导航栏 */}
      <header className="h-14 border-b flex items-center justify-between px-4 bg-white">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleLeftPanel}
            className="p-2 hover:bg-gray-100 rounded-md lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>
          
          {/* 项目选择器 */}
          <div className="relative">
            <button
              onClick={() => setShowProjectMenu(!showProjectMenu)}
              className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 rounded-md transition-colors"
            >
              <FolderOpen className="w-4 h-4 text-muted-foreground" />
              <span className="font-semibold">
                {currentProject ? currentProject.name : '选择项目'}
              </span>
              <ChevronRight className={cn(
                "w-4 h-4 text-muted-foreground transition-transform",
                showProjectMenu && "rotate-90"
              )} />
            </button>
            
            {/* 项目下拉菜单 */}
            {showProjectMenu && (
              <>
                <div 
                  className="fixed inset-0 z-40"
                  onClick={() => setShowProjectMenu(false)}
                />
                <div className="absolute top-full left-0 mt-1 w-80 bg-white border rounded-lg shadow-lg z-50 py-2 max-h-96 overflow-auto">
                  {/* 新建项目按钮 */}
                  <button
                    onClick={handleNewProject}
                    className="w-full flex items-center gap-2 px-4 py-2 hover:bg-gray-50 text-left text-primary"
                  >
                    <Plus className="w-4 h-4" />
                    <span>新建项目</span>
                  </button>
                  
                  {projects.length > 0 && <div className="border-t my-2" />}
                  
                  {/* 项目列表 */}
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      onClick={() => handleSwitchProject(project.id)}
                      className={cn(
                        "w-full flex items-center justify-between px-4 py-2 hover:bg-gray-50 cursor-pointer group",
                        currentProject?.id === project.id && "bg-primary/5"
                      )}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{project.name}</div>
                        <div className="text-xs text-muted-foreground flex items-center gap-2">
                          <span>{project.id}</span>
                          <span className="px-1.5 py-0.5 bg-muted rounded">
                            {statusLabels[project.status] || project.status}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => handleDeleteProject(project.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded text-red-500 transition-opacity"
                        title="删除项目"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  
                  {projects.length === 0 && (
                    <div className="px-4 py-3 text-sm text-muted-foreground text-center">
                      暂无项目
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
          
          {/* 意图摘要 */}
          {workflowData?.intent?.goal && (
            <span className="text-sm text-muted-foreground max-w-md truncate hidden lg:block" title={workflowData.intent.goal}>
              | {workflowData.intent.goal}
            </span>
          )}
          
          {currentProfile && (
            <span className="text-xs bg-muted px-2 py-1 rounded hidden md:inline">
              {currentProfile.name}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {currentProfile && (
            <button
              onClick={() => setShowProfileSelect(true)}
              className="text-sm text-primary hover:underline"
            >
              切换创作者
            </button>
          )}
          <button 
            onClick={() => setSettingsOpen(true)}
            className="p-2 hover:bg-gray-100 rounded-md"
            title="设置"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Profile选择界面 */}
      {showProfileSelect && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-semibold mb-4">选择创作者特质</h2>
            {profilesLoading ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">加载中...</p>
              </div>
            ) : profiles.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">还没有创作者特质</p>
                <p className="text-sm text-muted-foreground">
                  请先在设置中创建
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {profiles.map((profile) => (
                  <button
                    key={profile.id}
                    onClick={() => handleSelectProfile(profile)}
                    className="w-full text-left p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="font-medium">{profile.name}</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {profile.example_texts && profile.example_texts.length > 0 
                        ? profile.example_texts[0].slice(0, 50) + '...'
                        : '无范例文本'}
                    </div>
                  </button>
                ))}
              </div>
            )}
            {currentProfile && (
              <button
                onClick={() => setShowProfileSelect(false)}
                className="mt-4 w-full py-2 text-muted-foreground hover:text-foreground"
              >
                取消
              </button>
            )}
          </div>
        </div>
      )}

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧进度栏 */}
        <aside
          className={cn(
            "border-r bg-background-secondary transition-all duration-300",
            leftPanelCollapsed ? "w-0 overflow-hidden" : "w-[200px]"
          )}
        >
          <ProgressPanel />
        </aside>

        {/* 左侧折叠按钮 */}
        <button
          onClick={toggleLeftPanel}
          className="hidden lg:flex items-center justify-center w-4 hover:bg-gray-100 border-r"
        >
          {leftPanelCollapsed ? (
            <ChevronRight className="w-3 h-3 text-muted-foreground" />
          ) : (
            <ChevronLeft className="w-3 h-3 text-muted-foreground" />
          )}
        </button>

        {/* 中间编辑区 */}
        <main className="flex-1 overflow-hidden">
          <EditorPanel />
        </main>

        {/* 右侧折叠按钮 */}
        <button
          onClick={toggleRightPanel}
          className="hidden lg:flex items-center justify-center w-4 hover:bg-gray-100 border-l"
        >
          {rightPanelCollapsed ? (
            <ChevronLeft className="w-3 h-3 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-3 h-3 text-muted-foreground" />
          )}
        </button>

        {/* 右侧对话区 */}
        <aside
          className={cn(
            "border-l bg-background transition-all duration-300",
            rightPanelCollapsed ? "w-0 overflow-hidden" : "w-[350px]"
          )}
        >
          <ChatPanel />
        </aside>
      </div>

      {/* 状态栏 */}
      <footer className="h-8 border-t flex items-center justify-between px-4 text-sm text-muted-foreground bg-background-secondary">
        <div className="flex items-center gap-4">
          <span>阶段: {status?.current_stage || '未开始'}</span>
          {status?.clarification_progress && (
            <span>追问进度: {status.clarification_progress}</span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span>AI调用: {status?.ai_call_count || 0}次</span>
        </div>
      </footer>

      {/* 设置弹窗 */}
      <SettingsDialog 
        open={settingsOpen} 
        onClose={() => setSettingsOpen(false)} 
      />
    </div>
  )
}
