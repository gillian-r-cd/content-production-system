// web/src/components/settings/SettingsDialog.tsx
// 设置弹窗主容器
// 功能：全屏弹窗、左侧导航、右侧内容区

import { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useUIStore } from '@/stores/uiStore'
import { useWorkflowStore } from '@/stores/workflowStore'
import { profilesApi } from '@/api'
import apiClient from '@/api/client'
import SettingsNav from './SettingsNav'
import ProfileSettings from './ProfileSettings'
import PromptSettings from './PromptSettings'
import DataSettings from './DataSettings'
import DebugSettings from './DebugSettings'
import SchemaSettings from './SchemaSettings'
import SimulatorSettings from './SimulatorSettings'
import ChannelSettings from './ChannelSettings'

export type SettingsTab = 
  | 'project'
  | 'profiles'
  | 'schemas'
  | 'prompts'
  | 'simulators'
  | 'channels'
  | 'data'
  | 'debug'

interface SettingsDialogProps {
  open: boolean
  onClose: () => void
}

export default function SettingsDialog({ open, onClose }: SettingsDialogProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profiles')

  // ESC键关闭
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (open) {
      document.addEventListener('keydown', handleEsc)
      // 禁止背景滚动
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = 'auto'
    }
  }, [open, onClose])

  if (!open) return null

  const renderContent = () => {
    switch (activeTab) {
      case 'project':
        return <ProjectSettings />
      case 'profiles':
        return <ProfileSettings />
      case 'schemas':
        return <SchemaSettings />
      case 'prompts':
        return <PromptSettings />
      case 'simulators':
        return <SimulatorSettings />
      case 'channels':
        return <ChannelSettings />
      case 'data':
        return <DataSettings />
      case 'debug':
        return <DebugSettings />
      default:
        return <ProfileSettings />
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 背景遮罩 */}
      <div 
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />
      
      {/* 弹窗内容 */}
      <div className="relative w-full max-w-5xl h-[80vh] bg-white rounded-lg shadow-xl flex overflow-hidden">
        {/* 头部 */}
        <div className="absolute top-0 left-0 right-0 h-14 border-b flex items-center justify-between px-6 bg-white z-10">
          <h2 className="text-lg font-semibold">设置</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* 左侧导航 */}
        <div className="w-48 border-r bg-background-secondary pt-14">
          <SettingsNav 
            activeTab={activeTab} 
            onTabChange={setActiveTab} 
          />
        </div>
        
        {/* 右侧内容 */}
        <div className="flex-1 pt-14 overflow-auto">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}

// 项目设置组件
function ProjectSettings() {
  const { currentProject, currentProfile, setProfile } = useWorkflowStore()
  const queryClient = useQueryClient()
  
  const [name, setName] = useState(currentProject?.name || '')
  const [description, setDescription] = useState(currentProject?.description || '')
  const [isSaving, setIsSaving] = useState(false)
  
  // 获取Profile列表
  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  })
  const profiles = Array.isArray(profilesData) ? profilesData : []
  
  const handleSave = async () => {
    if (!currentProject) return
    setIsSaving(true)
    try {
      await apiClient.put(`/projects/${currentProject.id}`, {
        name,
        description,
      })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    } catch (error) {
      console.error('保存失败:', error)
    } finally {
      setIsSaving(false)
    }
  }

  if (!currentProject) {
    return (
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4">项目设置</h3>
        <p className="text-muted-foreground">请先开始一个项目</p>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">项目设置</h3>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {isSaving ? '保存中...' : '保存'}
        </button>
      </div>

      {/* 项目名称 */}
      <div>
        <label className="block text-sm font-medium mb-2">项目名称</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 border rounded-md"
        />
      </div>

      {/* 项目描述 */}
      <div>
        <label className="block text-sm font-medium mb-2">项目描述</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border rounded-md"
          rows={3}
        />
      </div>

      {/* 关联的创作者特质 */}
      <div>
        <label className="block text-sm font-medium mb-2">关联的创作者特质</label>
        <div className="p-3 bg-muted rounded-md">
          <p className="font-medium">{currentProfile?.name || '未选择'}</p>
          {currentProfile && (
            <p className="text-sm text-muted-foreground mt-1">
              禁忌词: {currentProfile.taboos?.forbidden_words?.length || 0}个 | 
              范例: {currentProfile.example_texts?.length || 0}个
            </p>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          如需更换，请关闭设置后点击顶部"切换创作者"
        </p>
      </div>

      {/* 项目信息 */}
      <div className="pt-4 border-t">
        <h4 className="text-sm font-medium mb-2">项目信息</h4>
        <div className="text-sm text-muted-foreground space-y-1">
          <p>项目ID: {currentProject.id}</p>
          <p>状态: {currentProject.status}</p>
          <p>创建时间: {new Date(currentProject.created_at).toLocaleString('zh-CN')}</p>
        </div>
      </div>
    </div>
  )
}

// SchemaSettings已从单独文件导入

// SimulatorSettings和ChannelSettings已从单独文件导入

