// web/src/components/stages/CoreProductionStage.tsx
// 内涵生产阶段
// 功能：显示字段生产进度，支持编辑生成的内容

import { useState, useEffect } from 'react'
import { 
  FileText, Check, Loader2, Edit3, Save, X, 
  RefreshCw, ChevronDown, ChevronRight, AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'
import apiClient from '@/api/client'

interface ContentField {
  name: string
  display_name: string
  status: 'pending' | 'generating' | 'completed' | 'error'
  content: string
  iterations?: number
  last_updated?: string
}

export default function CoreProductionStage() {
  const { workflowData, workflowId, status, refreshData, isLoading } = useWorkflowStore()
  const [selectedField, setSelectedField] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [isRegenerating, setIsRegenerating] = useState(false)

  const contentCore = workflowData?.content_core
  const selectedSchemeIndex = contentCore?.selected_scheme_index
  const selectedScheme = contentCore?.design_schemes?.[selectedSchemeIndex ?? 0]
  
  // 解析字段列表
  const fields: ContentField[] = contentCore?.fields?.map((f: any) => ({
    name: f.name || f.id,
    display_name: f.display_name || f.name || f.id,
    status: f.status || 'pending',
    content: f.content || f.value || '',
    iterations: f.iterations || 0,
    last_updated: f.last_updated,
  })) || []

  // 如果没有字段定义，显示默认字段
  const defaultFields: ContentField[] = fields.length > 0 ? fields : [
    { name: 'title', display_name: '标题', status: 'pending', content: '' },
    { name: 'outline', display_name: '大纲', status: 'pending', content: '' },
    { name: 'content', display_name: '正文', status: 'pending', content: '' },
    { name: 'summary', display_name: '摘要', status: 'pending', content: '' },
  ]

  const currentField = selectedField 
    ? defaultFields.find(f => f.name === selectedField) 
    : defaultFields[0]

  useEffect(() => {
    if (!selectedField && defaultFields.length > 0) {
      setSelectedField(defaultFields[0].name)
    }
  }, [defaultFields.length])

  const completedCount = defaultFields.filter(f => f.status === 'completed').length
  const totalCount = defaultFields.length

  const handleStartGeneration = async () => {
    if (!workflowId) return
    
    try {
      // 触发继续生成
      await apiClient.post(`/workflow/${workflowId}/continue`)
      await refreshData()
    } catch (error: any) {
      console.error('触发生成失败:', error)
      // 如果是400错误（需要用户输入），可能是正常的
      if (error.response?.status !== 400) {
        alert(`触发生成失败: ${error.response?.data?.detail || error.message}`)
      }
    }
  }

  const handleRegenerate = async (fieldName: string) => {
    if (!workflowId) return
    
    setIsRegenerating(true)
    try {
      await apiClient.post(`/workflow/${workflowId}/regenerate-field`, {
        field_name: fieldName,
      })
      await refreshData()
    } catch (error: any) {
      console.error('重新生成失败:', error)
      // API可能不存在，忽略
    }
    setIsRegenerating(false)
  }

  const handleSaveEdit = async () => {
    if (!workflowId || !selectedField) return
    
    try {
      await apiClient.patch(`/workflow/${workflowId}/update-field`, {
        stage: 'content_core',
        field: 'fields',
        value: defaultFields.map(f => 
          f.name === selectedField 
            ? { ...f, content: editContent, status: 'completed' }
            : f
        ),
      })
      await refreshData()
      setIsEditing(false)
    } catch (error) {
      console.error('保存失败:', error)
    }
  }

  const startEditing = () => {
    if (currentField) {
      setEditContent(currentField.content)
      setIsEditing(true)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <Check className="w-4 h-4 text-green-500" />
      case 'generating':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <div className="w-4 h-4 rounded-full border-2 border-muted-foreground/30" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成'
      case 'generating': return '生成中'
      case 'error': return '生成失败'
      default: return '待生成'
    }
  }

  return (
    <div className="h-full flex">
      {/* 左侧：字段列表 */}
      <div className="w-64 border-r bg-muted/20 flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            内涵生产
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            进度: {completedCount}/{totalCount} 字段
          </p>
          {/* 进度条 */}
          <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all"
              style={{ width: `${(completedCount / totalCount) * 100}%` }}
            />
          </div>
        </div>

        {/* 选中的方案信息 */}
        {selectedScheme && (
          <div className="p-3 border-b bg-primary/5">
            <p className="text-xs text-muted-foreground">当前方案</p>
            <p className="text-sm font-medium truncate">
              {selectedScheme.name || `方案 ${(selectedSchemeIndex ?? 0) + 1}`}
            </p>
          </div>
        )}

        {/* 字段列表 */}
        <div className="flex-1 overflow-auto">
          {defaultFields.map((field) => (
            <button
              key={field.name}
              onClick={() => setSelectedField(field.name)}
              className={cn(
                "w-full text-left p-4 border-b transition-colors flex items-center gap-3",
                selectedField === field.name 
                  ? "bg-primary/10 border-l-4 border-l-primary" 
                  : "hover:bg-muted/50"
              )}
            >
              {getStatusIcon(field.status)}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{field.display_name}</p>
                <p className="text-xs text-muted-foreground">{getStatusText(field.status)}</p>
              </div>
              {selectedField === field.name && (
                <ChevronRight className="w-4 h-4 text-primary flex-shrink-0" />
              )}
            </button>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="p-4 border-t bg-background">
          {completedCount < totalCount && (
            <button
              onClick={handleStartGeneration}
              disabled={isLoading}
              className="w-full px-4 py-3 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> 生成中...</>
              ) : (
                <>开始生成内容</>
              )}
            </button>
          )}
          {completedCount === totalCount && totalCount > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-center">
              <Check className="w-5 h-5 text-green-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-green-700">内涵生产完成</p>
            </div>
          )}
        </div>
      </div>

      {/* 右侧：字段内容详情 */}
      <div className="flex-1 overflow-auto p-6">
        {currentField ? (
          <div className="max-w-3xl mx-auto">
            {/* 字段标题 */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold">{currentField.display_name}</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  状态: {getStatusText(currentField.status)}
                  {currentField.iterations && currentField.iterations > 0 && (
                    <span className="ml-2">• 迭代次数: {currentField.iterations}</span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {currentField.status === 'completed' && !isEditing && (
                  <>
                    <button
                      onClick={() => handleRegenerate(currentField.name)}
                      disabled={isRegenerating}
                      className="px-3 py-1.5 text-sm border rounded hover:bg-muted flex items-center gap-1"
                    >
                      <RefreshCw className={cn("w-4 h-4", isRegenerating && "animate-spin")} />
                      重新生成
                    </button>
                    <button
                      onClick={startEditing}
                      className="px-3 py-1.5 text-sm border rounded hover:bg-muted flex items-center gap-1"
                    >
                      <Edit3 className="w-4 h-4" />
                      编辑
                    </button>
                  </>
                )}
                {isEditing && (
                  <>
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1.5 text-sm border rounded hover:bg-muted flex items-center gap-1"
                    >
                      <X className="w-4 h-4" />
                      取消
                    </button>
                    <button
                      onClick={handleSaveEdit}
                      className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 flex items-center gap-1"
                    >
                      <Save className="w-4 h-4" />
                      保存
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* 字段内容 */}
            <div className="bg-muted/30 rounded-lg p-6 min-h-[400px]">
              {currentField.status === 'pending' && (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                  <FileText className="w-12 h-12 mb-4 opacity-50" />
                  <p>此字段尚未生成</p>
                  <p className="text-sm mt-1">点击左侧"开始生成内容"按钮开始</p>
                </div>
              )}
              
              {currentField.status === 'generating' && (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                  <Loader2 className="w-12 h-12 mb-4 animate-spin text-primary" />
                  <p>正在生成中...</p>
                  <p className="text-sm mt-1">AI正在为你创作内容</p>
                </div>
              )}
              
              {currentField.status === 'completed' && !isEditing && (
                <div className="prose prose-sm max-w-none">
                  <div className="whitespace-pre-wrap text-foreground">
                    {currentField.content || '（暂无内容）'}
                  </div>
                </div>
              )}
              
              {isEditing && (
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full h-[400px] p-4 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary bg-background"
                  placeholder="编辑内容..."
                />
              )}
              
              {currentField.status === 'error' && (
                <div className="h-full flex flex-col items-center justify-center text-destructive">
                  <AlertCircle className="w-12 h-12 mb-4" />
                  <p>生成失败</p>
                  <button
                    onClick={() => handleRegenerate(currentField.name)}
                    className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
                  >
                    重试
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            请从左侧选择一个字段
          </div>
        )}
      </div>
    </div>
  )
}


