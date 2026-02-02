// web/src/components/stages/CoreProductionStage.tsx
// 内涵生产阶段
// 功能：
// 1. 目录编辑：随时可编辑章节和字段结构（点击设置按钮进入编辑模式）
// 2. 生产进度：动态显示各字段的生成状态
// 3. 内容编辑：查看和编辑已生成的内容
//
// 修改记录 2026-02-02:
// - 移除 outlineConfirmed 对目录编辑器显示的限制，目录确认后仍可编辑

import { useState, useEffect, useCallback, useRef } from 'react'
import { 
  FileText, Check, Loader2, Edit3, Save, X, 
  RefreshCw, ChevronDown, ChevronRight, AlertCircle,
  Settings, AlertTriangle, Play, Pause, RotateCcw
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'
import apiClient from '@/api/client'
import OutlineEditor from './OutlineEditor'
import type { ContentSection, ContentField, FieldDefinition } from '@/types'

interface FieldSchemaInfo {
  id: string
  name: string
  description: string
  field_count: number
}

export default function CoreProductionStage() {
  const { workflowData, workflowId, status, refreshData, isLoading } = useWorkflowStore()
  const [selectedSection, setSelectedSection] = useState<string | null>(null)
  const [selectedField, setSelectedField] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  
  // 使用 ref 避免闭包陷阱
  const isPausedRef = useRef(false)
  const isGeneratingRef = useRef(false)
  
  // 生成前提问（clarification）
  const [clarificationQuestion, setClarificationQuestion] = useState<string | null>(null)
  const [clarificationFieldId, setClarificationFieldId] = useState<string | null>(null)  // 使用 ID 精确查找
  const [clarificationFieldName, setClarificationFieldName] = useState<string | null>(null)
  const [clarificationAnswer, setClarificationAnswer] = useState('')
  const [isSubmittingClarification, setIsSubmittingClarification] = useState(false)
  
  // 目录结构
  const [sections, setSections] = useState<ContentSection[]>([])
  const [outlineConfirmed, setOutlineConfirmed] = useState(false)
  const [showOutlineEditor, setShowOutlineEditor] = useState(true)
  
  // 字段模板更换
  const [fieldSchemas, setFieldSchemas] = useState<FieldSchemaInfo[]>([])
  const [showChangeSchemaDialog, setShowChangeSchemaDialog] = useState(false)
  const [newSchemaId, setNewSchemaId] = useState<string | null>(null)
  const [isChangingSchema, setIsChangingSchema] = useState(false)
  
  // 当前模板的字段定义列表（用于添加字段时选择）
  const [templateFields, setTemplateFields] = useState<FieldDefinition[]>([])

  const contentCore = workflowData?.content_core
  const currentSchemaId = contentCore?.field_schema_id
  const selectedSchemeIndex = contentCore?.selected_scheme_index
  const selectedScheme = contentCore?.design_schemes?.[selectedSchemeIndex ?? 0]

  // 加载目录结构
  useEffect(() => {
    const loadOutline = async () => {
      if (!workflowId) return
      
      try {
        const { data } = await apiClient.get(`/workflow/${workflowId}/outline`)
        setSections(data.sections || [])
        setOutlineConfirmed(data.outline_confirmed || false)
        
        // 如果已确认目录，隐藏编辑器
        if (data.outline_confirmed) {
          setShowOutlineEditor(false)
        }
      } catch (error) {
        console.warn('Failed to load outline:', error)
        // 使用 content_core 中的数据作为后备
        if (contentCore?.sections) {
          setSections(contentCore.sections)
          setOutlineConfirmed(contentCore.outline_confirmed || false)
        }
      }
    }
    
    loadOutline()
  }, [workflowId, contentCore?.outline_confirmed])

  // 加载可用的字段模板
  useEffect(() => {
    const fetchSchemas = async () => {
      try {
        const { data } = await apiClient.get('/schemas')
        const schemas = data.map((s: any) => ({
          id: s.id,
          name: s.name,
          description: s.description || '',
          field_count: s.fields?.length || 0,
        }))
        setFieldSchemas(schemas)
      } catch (error) {
        console.warn('Failed to load field schemas:', error)
      }
    }
    fetchSchemas()
  }, [])

  // 获取当前关联模板的字段定义（用于添加字段时选择）
  useEffect(() => {
    const fetchTemplateFields = async () => {
      if (!currentSchemaId) {
        setTemplateFields([])
        return
      }
      try {
        const { data } = await apiClient.get(`/schemas/${currentSchemaId}`)
        const fields = (data.fields || []).map((f: any) => ({
          name: f.name,
          description: f.description || '',
          field_type: f.field_type || 'text',
          required: f.required ?? true,
          ai_hint: f.ai_hint || '',
          order: f.order || 0,
          depends_on: f.depends_on || [],
        }))
        setTemplateFields(fields)
      } catch (error) {
        console.warn('Failed to load template fields:', error)
        setTemplateFields([])
      }
    }
    fetchTemplateFields()
  }, [currentSchemaId])

  // 计算进度
  const getProgress = () => {
    let completed = 0
    let total = 0
    
    for (const section of sections) {
      for (const field of section.fields) {
        total++
        if (field.status === 'completed') {
          completed++
        }
      }
    }
    
    return { completed, total, percentage: total > 0 ? (completed / total) * 100 : 0 }
  }

  const progress = getProgress()

  // 获取当前选中的字段
  const getCurrentField = (): ContentField | null => {
    if (!selectedSection || !selectedField) return null
    
    const section = sections.find(s => s.id === selectedSection)
    if (!section) return null
    
    return section.fields.find(f => f.id === selectedField) || null
  }

  const currentField = getCurrentField()

  // 自动选择第一个字段
  useEffect(() => {
    if (sections.length > 0 && !selectedSection) {
      const firstSection = sections[0]
      setSelectedSection(firstSection.id)
      if (firstSection.fields.length > 0) {
        setSelectedField(firstSection.fields[0].id)
      }
    }
  }, [sections])

  // 开始/继续生成（使用 ref 避免闭包陷阱）
  const handleStartGeneration = useCallback(async () => {
    // 使用 ref 检查状态，避免闭包问题
    if (!workflowId || isGeneratingRef.current) return
    
    setIsGenerating(true)
    isGeneratingRef.current = true
    setIsPaused(false)
    isPausedRef.current = false
    // 清除之前的澄清问题
    setClarificationQuestion(null)
    setClarificationFieldId(null)
    setClarificationFieldName(null)
    setClarificationAnswer('')
    
    const generateNextField = async () => {
      // 每次生成前检查是否已暂停
      if (isPausedRef.current) {
        console.log('生成已暂停（开始前检查）')
        setIsGenerating(false)
        isGeneratingRef.current = false
        return
      }
      
      // 乐观更新：在调用 API 之前，先将下一个待生成的字段标记为 generating
      setSections(prevSections => {
        const updated = [...prevSections]
        for (const section of updated) {
          for (const field of section.fields) {
            if (field.status === 'pending') {
              field.status = 'generating'
              // 选中当前正在生成的字段
              setSelectedSection(section.id)
              setSelectedField(field.id)
              return updated
            }
          }
        }
        return prevSections
      })
      
      try {
        const { data } = await apiClient.post(`/workflow/${workflowId}/generate-fields`)
        
        // API 返回后立即检查是否已暂停
        if (isPausedRef.current) {
          console.log('生成已暂停（API返回后检查）')
          setIsGenerating(false)
          isGeneratingRef.current = false
          // 仍然更新数据，显示已生成的内容
          await refreshData()
          const outlineRes = await apiClient.get(`/workflow/${workflowId}/outline`)
          setSections(outlineRes.data.sections || [])
          return
        }
        
        if (data.success) {
          // 检查是否需要用户回答问题
          if (data.waiting_for_clarification && data.clarification) {
            setClarificationQuestion(data.clarification.question)
            setClarificationFieldId(data.clarification.field_id)  // 使用 ID 精确查找
            setClarificationFieldName(data.clarification.field_name)
            // 暂停生成，等待用户回答
            setIsGenerating(false)
            isGeneratingRef.current = false
            return
          }
          
          await refreshData()
          
          // 重新加载目录结构以更新状态
          const outlineRes = await apiClient.get(`/workflow/${workflowId}/outline`)
          setSections(outlineRes.data.sections || [])
          
          // 如果还有待生成的字段且未暂停，继续生成
          if (data.remaining_count > 0 && !isPausedRef.current) {
            // 延迟后继续生成下一个
            setTimeout(generateNextField, 500)
            return
          }
        }
      } catch (error: any) {
        console.error('生成失败:', error)
        const errorMessage = error.response?.data?.detail || error.message
        if (errorMessage.includes('请先确认目录结构')) {
          setShowOutlineEditor(true)
        } else {
          alert(`生成失败: ${errorMessage}`)
        }
        
        // 生成失败时，重新加载目录以恢复正确状态
        try {
          const outlineRes = await apiClient.get(`/workflow/${workflowId}/outline`)
          setSections(outlineRes.data.sections || [])
        } catch (e) {
          console.error('加载目录失败:', e)
        }
      }
      
      // 生成完成或出错，重置状态
      setIsGenerating(false)
      isGeneratingRef.current = false
    }
    
    // 开始生成
    generateNextField()
  }, [workflowId, refreshData])
  
  // 提交澄清回答
  const handleSubmitClarification = useCallback(async () => {
    if (!workflowId || !clarificationAnswer.trim()) return
    
    setIsSubmittingClarification(true)
    try {
      await apiClient.post(`/workflow/${workflowId}/fields/clarify`, {
        answer: clarificationAnswer.trim(),
        field_id: clarificationFieldId,      // 使用 ID 精确查找
        field_name: clarificationFieldName   // 向后兼容
      })
      
      // 清除澄清问题
      setClarificationQuestion(null)
      setClarificationFieldId(null)
      setClarificationFieldName(null)
      setClarificationAnswer('')
      
      // 继续生成
      await handleStartGeneration()
    } catch (error: any) {
      console.error('提交澄清回答失败:', error)
      alert(`提交失败: ${error.response?.data?.detail || error.message}`)
    }
    setIsSubmittingClarification(false)
  }, [workflowId, clarificationAnswer, clarificationFieldId, clarificationFieldName, handleStartGeneration])

  // 暂停生成
  const handlePauseGeneration = () => {
    setIsPaused(true)
    isPausedRef.current = true
    // 注意：不立即设置 isGenerating = false
    // 等待当前正在进行的生成完成后，generateNextField 会自动停止
  }

  // 重新生成单个字段
  const handleRegenerate = async (fieldId: string) => {
    if (!workflowId) return
    
    setIsRegenerating(true)
    try {
      // 正确的 API 路径
      const { data } = await apiClient.post(`/workflow/${workflowId}/fields/${fieldId}/regenerate`)
      
      if (data.success) {
        await refreshData()
        
        // 重新加载目录
        const outlineRes = await apiClient.get(`/workflow/${workflowId}/outline`)
        setSections(outlineRes.data.sections || [])
      }
    } catch (error: any) {
      console.error('重新生成失败:', error)
      alert(`重新生成失败: ${error.response?.data?.detail || error.message}`)
    }
    setIsRegenerating(false)
  }

  // 保存编辑
  const handleSaveEdit = async () => {
    if (!workflowId || !selectedSection || !selectedField) return
    
    try {
      // 更新字段内容
      const updatedSections = sections.map(s => {
        if (s.id === selectedSection) {
          return {
            ...s,
            fields: s.fields.map(f => 
              f.id === selectedField 
                ? { ...f, content: editContent, status: 'completed' as const }
                : f
            )
          }
        }
        return s
      })
      
      await apiClient.patch(`/workflow/${workflowId}/update-field`, {
        stage: 'content_core',
        field: 'sections',
        value: updatedSections,
      })
      
      setSections(updatedSections)
      setIsEditing(false)
      await refreshData()
    } catch (error) {
      console.error('保存失败:', error)
    }
  }

  const startEditing = () => {
    if (currentField) {
      setEditContent(currentField.content || '')
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

  // 当前使用的模板名称
  const currentSchemaName = currentSchemaId 
    ? fieldSchemas.find(s => s.id === currentSchemaId)?.name || currentSchemaId 
    : '默认模板'

  // 如果显示目录编辑器（无论目录是否已确认，都可以编辑）
  if (showOutlineEditor) {
    return (
      <div className="h-full flex">
        {/* 左侧：目录编辑器 */}
        <div className="w-80 border-r">
          <OutlineEditor
            workflowId={workflowId || ''}
            sections={sections}
            outlineConfirmed={outlineConfirmed}
            templateFields={templateFields}
            onSave={async () => {
              const { data } = await apiClient.get(`/workflow/${workflowId}/outline`)
              setSections(data.sections || [])
            }}
            onConfirm={async () => {
              const { data } = await apiClient.get(`/workflow/${workflowId}/outline`)
              setSections(data.sections || [])
              setOutlineConfirmed(true)
              setShowOutlineEditor(false)
              await refreshData()
            }}
          />
        </div>
        
        {/* 右侧：方案预览或返回按钮 */}
        <div className="flex-1 p-6 overflow-auto">
          {outlineConfirmed ? (
            // 已确认：显示返回生产的按钮
            <div className="max-w-2xl mx-auto">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-medium text-blue-800 flex items-center gap-2">
                  <Check className="w-5 h-5" />
                  目录结构编辑模式
                </h3>
                <p className="text-sm text-blue-700 mt-2">
                  你可以在左侧编辑目录结构：添加、删除、重命名章节和字段。
                  修改会自动保存。
                </p>
                <button
                  onClick={() => setShowOutlineEditor(false)}
                  className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
                >
                  返回内容生产
                </button>
              </div>
            </div>
          ) : (
            // 未确认：显示方案预览和提示
            selectedScheme && (
              <div className="max-w-2xl mx-auto">
                <h2 className="text-xl font-bold mb-4">当前设计方案</h2>
                <div className="p-4 bg-muted/30 rounded-lg space-y-4">
                  <div>
                    <h3 className="font-medium">{selectedScheme.name || '未命名方案'}</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedScheme.type || '标准型'}
                    </p>
                  </div>
                  
                  {selectedScheme.description && (
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">描述</p>
                      <p className="text-sm mt-1">{selectedScheme.description}</p>
                    </div>
                  )}
                  
                  {selectedScheme.approach && (
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">整体思路</p>
                      <p className="text-sm mt-1 whitespace-pre-wrap">{selectedScheme.approach}</p>
                    </div>
                  )}
                </div>
                
                <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <h3 className="font-medium text-amber-800 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    请先确认目录结构
                  </h3>
                  <p className="text-sm text-amber-700 mt-2">
                    在左侧编辑你的内容目录结构（章节和字段），确认后才能开始生产内容。
                  </p>
                </div>
              </div>
            )
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex">
      {/* 左侧：章节和字段列表 */}
      <div className="w-72 border-r bg-muted/20 flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              内涵生产
            </h2>
            <button
              onClick={() => setShowOutlineEditor(true)}
              className="p-1.5 hover:bg-muted rounded"
              title="编辑目录结构"
            >
              <Settings className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            进度: {progress.completed}/{progress.total} 字段
          </p>
          {/* 进度条 */}
          <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className={cn(
                "h-full transition-all duration-500",
                isGenerating ? "bg-blue-500 animate-pulse" : "bg-primary"
              )}
              style={{ width: `${progress.percentage}%` }}
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

        {/* 章节和字段树 */}
        <div className="flex-1 overflow-auto">
          {sections.map((section) => (
            <div key={section.id}>
              {/* 章节标题 */}
              <div className="px-4 py-2 bg-muted/40 border-b sticky top-0">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {section.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {section.fields.filter(f => f.status === 'completed').length}/{section.fields.length}
                </p>
              </div>
              
              {/* 字段列表 */}
              {section.fields.map((field) => (
                <button
                  key={field.id}
                  onClick={() => {
                    setSelectedSection(section.id)
                    setSelectedField(field.id)
                  }}
                  className={cn(
                    "w-full text-left px-4 py-3 border-b transition-colors flex items-center gap-3",
                    selectedSection === section.id && selectedField === field.id
                      ? "bg-primary/10 border-l-4 border-l-primary" 
                      : "hover:bg-muted/50"
                  )}
                >
                  {getStatusIcon(field.status)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">
                      {field.display_name || field.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {getStatusText(field.status)}
                    </p>
                  </div>
                  {selectedSection === section.id && selectedField === field.id && (
                    <ChevronRight className="w-4 h-4 text-primary flex-shrink-0" />
                  )}
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="p-4 border-t bg-background space-y-2">
          {progress.completed < progress.total && (
            <>
              {isGenerating ? (
                <button
                  onClick={handlePauseGeneration}
                  className="w-full px-4 py-3 bg-amber-500 text-white rounded-lg font-medium text-sm hover:bg-amber-600 flex items-center justify-center gap-2"
                >
                  <Pause className="w-4 h-4" />
                  暂停生成
                </button>
              ) : (
                <button
                  onClick={handleStartGeneration}
                  disabled={isLoading}
                  className="w-full px-4 py-3 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  {progress.completed > 0 ? '继续生成' : '开始生成内容'}
                </button>
              )}
            </>
          )}
          
          {progress.completed === progress.total && progress.total > 0 && (
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
                <h2 className="text-xl font-bold">
                  {currentField.display_name || currentField.name}
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  状态: {getStatusText(currentField.status)}
                  {currentField.evaluation_score && (
                    <span className="ml-2">• 评分: {currentField.evaluation_score}/10</span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {currentField.status === 'completed' && !isEditing && (
                  <>
                    <button
                      onClick={() => handleRegenerate(currentField.id)}
                      disabled={isRegenerating}
                      className="px-3 py-1.5 text-sm border rounded hover:bg-muted flex items-center gap-1"
                    >
                      <RotateCcw className={cn("w-4 h-4", isRegenerating && "animate-spin")} />
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
                    onClick={() => handleRegenerate(currentField.id)}
                    className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
                  >
                    重试
                  </button>
                </div>
              )}
            </div>
            
            {/* 评估反馈 */}
            {currentField.evaluation_feedback && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-800">AI评估反馈</p>
                <p className="text-sm text-blue-700 mt-1">{currentField.evaluation_feedback}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            请从左侧选择一个字段
          </div>
        )}
      </div>
      
      {/* 澄清问题对话框 */}
      {clarificationQuestion && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-primary" />
              生成前提问
            </h3>
            <p className="text-sm text-muted-foreground mb-1">
              字段: {clarificationFieldName}
            </p>
            <div className="p-4 bg-muted/50 rounded-lg mb-4">
              <p className="text-sm whitespace-pre-wrap">{clarificationQuestion}</p>
            </div>
            <textarea
              value={clarificationAnswer}
              onChange={(e) => setClarificationAnswer(e.target.value)}
              placeholder="请输入您的回答..."
              className="w-full p-3 border rounded-lg text-sm resize-none h-32 mb-4"
              disabled={isSubmittingClarification}
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setClarificationQuestion(null)
                  setClarificationFieldId(null)
                  setClarificationFieldName(null)
                  setClarificationAnswer('')
                  setIsGenerating(false)
                  isGeneratingRef.current = false
                }}
                className="px-4 py-2 text-sm border rounded-lg hover:bg-muted"
                disabled={isSubmittingClarification}
              >
                跳过此字段
              </button>
              <button
                onClick={handleSubmitClarification}
                disabled={!clarificationAnswer.trim() || isSubmittingClarification}
                className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
              >
                {isSubmittingClarification ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    提交中...
                  </>
                ) : (
                  '提交并继续生成'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
