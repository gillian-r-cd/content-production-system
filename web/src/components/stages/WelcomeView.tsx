// web/src/components/stages/WelcomeView.tsx
// 欢迎页面 - 新建项目或加载既往项目
// 功能：引导用户开始新项目或继续既往项目

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Sparkles, ArrowRight, Plus, FolderOpen, Clock } from 'lucide-react'
import { profilesApi } from '@/api'
import apiClient from '@/api/client'
import { useWorkflowStore } from '@/stores/workflowStore'
import type { Profile } from '@/types'

interface ProjectListItem {
  id: string
  name: string
  status: string
  created_at: string
}

export default function WelcomeView() {
  const { currentProfile, setProfile, startWorkflow, loadProject, isLoading } = useWorkflowStore()
  const [projectName, setProjectName] = useState('')
  const [projectIntent, setProjectIntent] = useState('')
  const [step, setStep] = useState<'select-profile' | 'choose-action' | 'new-project' | 'load-project'>('select-profile')
  
  // 获取Profile列表
  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  })
  const profiles = Array.isArray(profilesData) ? profilesData : []

  // 获取既往项目列表
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const { data } = await apiClient.get('/projects')
      return data as ProjectListItem[]
    },
  })
  const projects = Array.isArray(projectsData) ? projectsData : []

  const handleSelectProfile = (profile: Profile) => {
    setProfile(profile)
    setStep('choose-action')
  }

  const handleStartNewProject = () => {
    if (!currentProfile || !projectIntent.trim()) return
    const name = projectName.trim() || `项目_${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
    startWorkflow(currentProfile.id, name, projectIntent.trim())
  }

  const handleLoadProject = async (projectId: string) => {
    await loadProject(projectId)
  }

  // Step 1: 选择Profile
  if (!currentProfile || step === 'select-profile') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="max-w-lg w-full text-center">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <Sparkles className="w-8 h-8 text-primary" />
          </div>
          
          <h1 className="text-2xl font-bold mb-2">内容生产系统</h1>
          <p className="text-muted-foreground mb-8">
            选择一个创作者特质开始
          </p>
          
          {profiles.length === 0 ? (
            <div className="bg-muted/50 rounded-lg p-6">
              <p className="text-muted-foreground mb-4">还没有创作者特质</p>
              <p className="text-sm text-muted-foreground">
                请点击右上角设置，在"创作者特质"中创建一个
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  onClick={() => handleSelectProfile(profile)}
                  className="w-full text-left p-4 border rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
                >
                  <div className="font-medium">{profile.name}</div>
                  {profile.example_texts && profile.example_texts.length > 0 && (
                    <div className="text-sm text-muted-foreground mt-1 truncate">
                      {profile.example_texts[0].slice(0, 60)}...
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Step 2: 选择操作（新建或加载）
  if (step === 'choose-action') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="max-w-xl w-full">
          <div className="text-center mb-8">
            <p className="text-muted-foreground mb-2">
              创作者: <span className="text-foreground font-medium">{currentProfile.name}</span>
              <button 
                onClick={() => setStep('select-profile')}
                className="ml-2 text-primary hover:underline text-sm"
              >
                更换
              </button>
            </p>
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            {/* 新建项目 */}
            <button
              onClick={() => setStep('new-project')}
              className="p-6 border-2 border-dashed rounded-xl hover:border-primary hover:bg-primary/5 transition-colors text-left"
            >
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                <Plus className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-lg mb-2">新建项目</h3>
              <p className="text-sm text-muted-foreground">
                开始一个全新的内容生产项目
              </p>
            </button>
            
            {/* 加载项目 */}
            <button
              onClick={() => setStep('load-project')}
              disabled={projects.length === 0}
              className="p-6 border-2 border-dashed rounded-xl hover:border-primary hover:bg-primary/5 transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center mb-4">
                <FolderOpen className="w-6 h-6 text-muted-foreground" />
              </div>
              <h3 className="font-semibold text-lg mb-2">继续项目</h3>
              <p className="text-sm text-muted-foreground">
                {projects.length > 0 
                  ? `加载既往项目 (${projects.length}个)`
                  : '暂无既往项目'}
              </p>
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Step 3a: 新建项目
  if (step === 'new-project') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="max-w-2xl w-full">
          <div className="mb-6">
            <button
              onClick={() => setStep('choose-action')}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← 返回
            </button>
          </div>
          
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold mb-2">新建项目</h1>
            <p className="text-muted-foreground">
              创作者: {currentProfile.name}
            </p>
          </div>
          
          {/* 项目名称 */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">项目名称</label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="例如：团队管理课程、产品介绍页"
              className="w-full px-4 py-3 border rounded-lg"
            />
          </div>
          
          {/* 项目意图 */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              你想生产什么内容？<span className="text-error">*</span>
            </label>
            <textarea
              value={projectIntent}
              onChange={(e) => setProjectIntent(e.target.value)}
              placeholder="描述你的内容生产目标..."
              className="w-full px-4 py-3 border rounded-lg resize-none"
              rows={5}
            />
            <p className="text-xs text-muted-foreground mt-2">
              AI将基于你的描述进行意图分析，可能会追问2-3个问题来明确需求
            </p>
          </div>
          
          <button
            onClick={handleStartNewProject}
            disabled={isLoading || !projectIntent.trim()}
            className="w-full py-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? '创建中...' : (
              <>开始意图分析 <ArrowRight className="w-5 h-5" /></>
            )}
          </button>
        </div>
      </div>
    )
  }

  // Step 3b: 加载既往项目
  if (step === 'load-project') {
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
      <div className="h-full flex flex-col p-8">
        <div className="max-w-3xl mx-auto w-full">
          <div className="mb-6">
            <button
              onClick={() => setStep('choose-action')}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← 返回
            </button>
          </div>
          
          <div className="mb-8">
            <h1 className="text-2xl font-bold mb-2">选择项目</h1>
            <p className="text-muted-foreground">
              点击项目卡片继续上次的进度
            </p>
          </div>
          
          <div className="space-y-3">
            {projects.map((project) => (
              <button
                key={project.id}
                onClick={() => handleLoadProject(project.id)}
                disabled={isLoading}
                className="w-full text-left p-4 border rounded-lg hover:border-primary hover:bg-primary/5 transition-colors disabled:opacity-50"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">{project.name}</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {project.id}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="inline-block px-2 py-1 text-xs bg-muted rounded">
                      {statusLabels[project.status] || project.status}
                    </span>
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {project.created_at ? new Date(project.created_at).toLocaleDateString('zh-CN') : ''}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return null
}
