// web/src/components/common/VersionManager.tsx
// 版本管理组件
// 功能：显示版本历史、创建版本、恢复版本

import { useState, useEffect } from 'react'
import { 
  History, Plus, RotateCcw, Trash2, ChevronDown, ChevronRight,
  Clock, Save, AlertTriangle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/api/client'

interface Version {
  id: string
  version_number: number
  description: string
  trigger_stage: string
  trigger_action: string
  created_at: string
  backed_up_stages: string[]
}

interface VersionManagerProps {
  projectId: string
  onRestore?: () => void
  className?: string
}

export default function VersionManager({ 
  projectId, 
  onRestore,
  className 
}: VersionManagerProps) {
  const [versions, setVersions] = useState<Version[]>([])
  const [isExpanded, setIsExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newDescription, setNewDescription] = useState('')
  
  const fetchVersions = async () => {
    try {
      const { data } = await apiClient.get(`/workflow/${projectId}/versions`)
      setVersions(data.versions || [])
    } catch (error) {
      console.error('获取版本列表失败:', error)
    }
  }
  
  useEffect(() => {
    if (projectId && isExpanded) {
      fetchVersions()
    }
  }, [projectId, isExpanded])
  
  const handleCreateVersion = async () => {
    setIsLoading(true)
    try {
      await apiClient.post(`/workflow/${projectId}/versions`, {
        description: newDescription || '手动创建的版本',
        trigger_stage: 'manual',
        trigger_action: 'manual',
      })
      setNewDescription('')
      setShowCreateDialog(false)
      await fetchVersions()
    } catch (error) {
      console.error('创建版本失败:', error)
    }
    setIsLoading(false)
  }
  
  const handleRestoreVersion = async (versionId: string) => {
    if (!confirm('确定要恢复到此版本吗？当前状态将被自动备份。')) {
      return
    }
    
    setIsLoading(true)
    try {
      await apiClient.post(`/workflow/${projectId}/versions/${versionId}/restore`)
      await fetchVersions()
      onRestore?.()
    } catch (error) {
      console.error('恢复版本失败:', error)
    }
    setIsLoading(false)
  }
  
  const handleDeleteVersion = async (versionId: string) => {
    if (!confirm('确定要删除此版本吗？')) {
      return
    }
    
    try {
      await apiClient.delete(`/workflow/${projectId}/versions/${versionId}`)
      await fetchVersions()
    } catch (error) {
      console.error('删除版本失败:', error)
    }
  }
  
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }
  
  const stageNames: Record<string, string> = {
    intent: '意图分析',
    research: '消费者调研',
    core_design: '内涵设计',
    core_production: '内涵生产',
    extension: '外延生产',
    manual: '手动',
    restore: '恢复',
  }
  
  return (
    <div className={cn("border rounded-lg bg-background", className)}>
      {/* 头部 */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-muted-foreground" />
          <span className="font-medium text-sm">版本历史</span>
          {versions.length > 0 && (
            <span className="text-xs bg-muted px-1.5 py-0.5 rounded">{versions.length}</span>
          )}
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
        )}
      </button>
      
      {/* 展开内容 */}
      {isExpanded && (
        <div className="border-t px-4 py-3 space-y-3">
          {/* 创建版本按钮 */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              修改上游内容前，建议先创建版本备份
            </p>
            <button
              onClick={() => setShowCreateDialog(true)}
              className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 flex items-center gap-1"
            >
              <Plus className="w-3 h-3" />
              创建版本
            </button>
          </div>
          
          {/* 创建对话框 */}
          {showCreateDialog && (
            <div className="p-3 bg-muted/30 rounded-lg space-y-2">
              <input
                type="text"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="版本描述（可选）"
                className="w-full p-2 text-sm border rounded bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowCreateDialog(false)}
                  className="px-3 py-1.5 text-xs bg-muted rounded hover:bg-muted/80"
                >
                  取消
                </button>
                <button
                  onClick={handleCreateVersion}
                  disabled={isLoading}
                  className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
                >
                  <Save className="w-3 h-3 inline-block mr-1" />
                  保存
                </button>
              </div>
            </div>
          )}
          
          {/* 版本列表 */}
          {versions.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              暂无版本记录
            </p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-auto">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className="p-3 bg-muted/30 rounded-lg group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          V{version.version_number}
                        </span>
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDate(version.created_at)}
                        </span>
                      </div>
                      {version.description && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {version.description}
                        </p>
                      )}
                      <div className="flex gap-1 mt-2 flex-wrap">
                        <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                          触发: {stageNames[version.trigger_stage] || version.trigger_stage}
                        </span>
                        {version.backed_up_stages.map((stage) => (
                          <span 
                            key={stage}
                            className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded"
                          >
                            {stageNames[stage] || stage}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {/* 操作按钮 */}
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleRestoreVersion(version.id)}
                        disabled={isLoading}
                        className="p-1.5 text-primary hover:bg-primary/10 rounded"
                        title="恢复此版本"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteVersion(version.id)}
                        className="p-1.5 text-destructive hover:bg-destructive/10 rounded"
                        title="删除此版本"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * 版本检查提示组件
 * 在修改上游内容前显示
 */
export function VersionWarning({
  projectId,
  stage,
  onConfirm,
  onCancel,
}: {
  projectId: string
  stage: string
  onConfirm: (createVersion: boolean, description: string) => void
  onCancel: () => void
}) {
  const [shouldCreate, setShouldCreate] = useState(false)
  const [downstreamStages, setDownstreamStages] = useState<string[]>([])
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    const checkVersion = async () => {
      try {
        const { data } = await apiClient.post(`/workflow/${projectId}/check-version-needed`, {
          stage,
        })
        setShouldCreate(data.should_create_version)
        setDownstreamStages(data.downstream_stages || [])
      } catch (error) {
        console.error('检查版本需求失败:', error)
      }
      setIsLoading(false)
    }
    
    checkVersion()
  }, [projectId, stage])
  
  const stageNames: Record<string, string> = {
    research: '消费者调研',
    core_design: '内涵设计',
    core_production: '内涵生产',
    extension: '外延生产',
  }
  
  if (isLoading) {
    return null
  }
  
  if (!shouldCreate) {
    // 不需要版本备份，直接继续
    onConfirm(false, '')
    return null
  }
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-lg max-w-md w-full mx-4 p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="w-6 h-6 text-amber-500" />
          <h3 className="font-semibold text-lg">修改将影响下游数据</h3>
        </div>
        
        <p className="text-muted-foreground mb-4">
          修改此阶段会导致以下下游数据可能需要重新生成：
        </p>
        
        <div className="flex gap-2 mb-4 flex-wrap">
          {downstreamStages.map((stage) => (
            <span 
              key={stage}
              className="px-2 py-1 bg-amber-100 text-amber-700 text-sm rounded"
            >
              {stageNames[stage] || stage}
            </span>
          ))}
        </div>
        
        <div className="mb-4">
          <label className="text-sm font-medium block mb-2">
            版本描述（可选）
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="描述此次修改的原因..."
            className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm bg-muted rounded hover:bg-muted/80"
          >
            取消修改
          </button>
          <button
            onClick={() => onConfirm(false, '')}
            className="px-4 py-2 text-sm border rounded hover:bg-muted/50"
          >
            不备份，直接修改
          </button>
          <button
            onClick={() => onConfirm(true, description)}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            创建备份后修改
          </button>
        </div>
      </div>
    </div>
  )
}


