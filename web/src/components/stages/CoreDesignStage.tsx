// web/src/components/stages/CoreDesignStage.tsx
// 内涵设计阶段 - 方案选择与编辑
// 功能：左侧方案目录，右侧展开编辑，支持选择字段模板

import { useState, useEffect } from 'react'
import { 
  Check, ChevronRight, Lightbulb, Loader2, 
  Edit3, Save, X, Plus, Trash2, RotateCcw, AlertTriangle,
  FileText, ChevronDown
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'
import apiClient from '@/api/client'

interface FieldSchemaInfo {
  id: string
  name: string
  description: string
  field_count: number
}

interface DesignScheme {
  name: string
  type: string
  description: string
  approach: string
  target_scenario?: string
  key_features: string[]
  recommended?: boolean
  // 旧格式兼容
  scheme?: string
  index?: number
}

/**
 * 解析方案数据，兼容多种格式
 */
function parseScheme(raw: any, index: number): DesignScheme {
  if (!raw) {
    return {
      name: `方案 ${index + 1}`,
      type: '标准型',
      description: '待生成',
      approach: '',
      key_features: [],
    }
  }

  // 如果是旧格式 { scheme: "长文本...", index: 0 }
  if (raw.scheme && typeof raw.scheme === 'string') {
    const text = raw.scheme
    // 尝试提取名称
    const nameMatch = text.match(/方案[一二三][:：]?\s*[\*]*[「【]?([^」】\*\n]+)[」】]?[\*]*/)
    const name = nameMatch ? nameMatch[1].trim().slice(0, 30) : `方案 ${index + 1}`
    
    return {
      name,
      type: ['稳妥型', '创意型', '激进型'][index] || '标准型',
      description: text.slice(0, 150) + '...',
      approach: text,
      key_features: [],
    }
  }

  // 正常格式
  return {
    name: raw.name || `方案 ${index + 1}`,
    type: raw.type || '标准型',
    description: raw.description || raw.summary || '',
    approach: raw.approach || '',
    target_scenario: raw.target_scenario || '',
    key_features: raw.key_features || [],
    recommended: raw.recommended || false,
  }
}

/**
 * 可编辑文本字段
 */
function EditableText({ 
  value, 
  onChange, 
  label, 
  multiline = false,
  placeholder = '' 
}: { 
  value: string
  onChange: (v: string) => void
  label: string
  multiline?: boolean
  placeholder?: string
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [localValue, setLocalValue] = useState(value)
  
  useEffect(() => {
    setLocalValue(value)
  }, [value])
  
  const handleSave = () => {
    onChange(localValue)
    setIsEditing(false)
  }
  
  const handleCancel = () => {
    setLocalValue(value)
    setIsEditing(false)
  }
  
  if (isEditing) {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium text-muted-foreground">{label}</label>
        {multiline ? (
          <textarea
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            className="w-full min-h-[120px] p-3 border rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder={placeholder}
            autoFocus
          />
        ) : (
          <input
            type="text"
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            className="w-full p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder={placeholder}
            autoFocus
          />
        )}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="px-3 py-1 bg-primary text-primary-foreground text-sm rounded hover:bg-primary/90"
          >
            <Save className="w-4 h-4 inline-block mr-1" />
            保存
          </button>
          <button
            onClick={handleCancel}
            className="px-3 py-1 bg-muted text-muted-foreground text-sm rounded hover:bg-muted/80"
          >
            <X className="w-4 h-4 inline-block mr-1" />
            取消
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div className="group">
      <label className="text-sm font-medium text-muted-foreground">{label}</label>
      <div 
        className="mt-1 p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50 transition-colors relative"
        onClick={() => setIsEditing(true)}
      >
        <p className="text-sm whitespace-pre-wrap">{value || <span className="text-muted-foreground italic">{placeholder || '点击编辑...'}</span>}</p>
        <Edit3 className="w-4 h-4 absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-muted-foreground transition-opacity" />
      </div>
    </div>
  )
}

/**
 * 可编辑列表字段
 */
function EditableList({
  value,
  onChange,
  label,
  placeholder = '添加项目...'
}: {
  value: string[]
  onChange: (v: string[]) => void
  label: string
  placeholder?: string
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [newItem, setNewItem] = useState('')
  
  const handleAdd = () => {
    if (newItem.trim()) {
      onChange([...value, newItem.trim()])
      setNewItem('')
    }
  }
  
  const handleRemove = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }
  
  return (
    <div className="group">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-muted-foreground">{label}</label>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="text-xs text-primary hover:underline"
        >
          {isEditing ? '完成' : '编辑'}
        </button>
      </div>
      
      <div className="space-y-2">
        {value.length === 0 && !isEditing ? (
          <p className="text-sm text-muted-foreground italic p-2">暂无内容</p>
        ) : (
          value.map((item, index) => (
            <div key={index} className="flex items-center gap-2 p-2 bg-muted/30 rounded">
              <span className="text-primary">•</span>
              <span className="text-sm flex-1">{item}</span>
              {isEditing && (
                <button
                  onClick={() => handleRemove(index)}
                  className="text-destructive hover:text-destructive/80"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))
        )}
        
        {isEditing && (
          <div className="flex gap-2">
            <input
              type="text"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={handleAdd}
              disabled={!newItem.trim()}
              className="px-3 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function CoreDesignStage() {
  const { workflowData, selectScheme, isLoading, updateScheme, workflowId, refreshData } = useWorkflowStore()
  const [selectedIndex, setSelectedIndex] = useState<number>(
    workflowData?.content_core?.selected_scheme_index ?? 0
  )
  const [localSchemes, setLocalSchemes] = useState<DesignScheme[]>([])
  const [hasChanges, setHasChanges] = useState(false)
  const [showReselectDialog, setShowReselectDialog] = useState(false)
  const [reselectDescription, setReselectDescription] = useState('')
  
  // 字段模板选择
  const [fieldSchemas, setFieldSchemas] = useState<FieldSchemaInfo[]>([])
  const [selectedSchemaId, setSelectedSchemaId] = useState<string | null>(null)
  const [showSchemaDropdown, setShowSchemaDropdown] = useState(false)

  // 从workflowData获取方案，解析并兼容处理
  const rawSchemes = workflowData?.content_core?.design_schemes || []
  
  useEffect(() => {
    const parsed = rawSchemes.map((s: any, i: number) => parseScheme(s, i))
    setLocalSchemes(parsed)
    setHasChanges(false)
  }, [JSON.stringify(rawSchemes)])
  
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
        
        // 如果项目已有关联的schema，预选它
        const currentSchemaId = workflowData?.content_core?.field_schema_id
        if (currentSchemaId) {
          setSelectedSchemaId(currentSchemaId)
        }
      } catch (error) {
        console.warn('Failed to load field schemas:', error)
      }
    }
    fetchSchemas()
  }, [workflowData?.content_core?.field_schema_id])

  const currentScheme = localSchemes[selectedIndex]
  const alreadySelected = workflowData?.content_core?.selected_scheme_index !== undefined && 
                          workflowData?.content_core?.selected_scheme_index !== null
  const previouslySelectedIndex = workflowData?.content_core?.selected_scheme_index

  const handleSchemeChange = (field: keyof DesignScheme, value: any) => {
    const updated = [...localSchemes]
    updated[selectedIndex] = { ...updated[selectedIndex], [field]: value }
    setLocalSchemes(updated)
    setHasChanges(true)
  }

  const handleSaveChanges = async () => {
    if (updateScheme) {
      await updateScheme(selectedIndex, localSchemes[selectedIndex])
    }
    setHasChanges(false)
  }

  const handleConfirm = async () => {
    if (hasChanges) {
      await handleSaveChanges()
    }
    // 传递选中的字段模板ID
    await selectScheme(selectedIndex, selectedSchemaId || undefined)
  }

  // 重新选择方案（需要版本备份 + 回退）
  const handleReselect = async () => {
    if (!workflowId) return
    
    try {
      // 使用 force_rollback 参数，后端会自动备份并清除下游数据
      const { data } = await apiClient.post(`/workflow/${workflowId}/select-scheme`, {
        scheme_index: selectedIndex,
        schema_id: selectedSchemaId,  // 传递字段模板ID
        force_rollback: true,
      })
      
      if (data.success) {
        setShowReselectDialog(false)
        setReselectDescription('')
        
        // 刷新数据
        await refreshData()
      }
    } catch (error: any) {
      console.error('重新选择失败:', error)
      alert(`重新选择失败: ${error.response?.data?.detail || error.message}`)
    }
  }
  
  // 当前选中的字段模板信息
  const selectedSchema = fieldSchemas.find(s => s.id === selectedSchemaId)

  if (localSchemes.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mb-4" />
        <p className="text-muted-foreground">正在生成设计方案...</p>
        <p className="text-sm text-muted-foreground mt-2">AI正在分析你的需求，请稍候</p>
      </div>
    )
  }

  return (
    <div className="h-full flex">
      {/* 左侧：方案目录 */}
      <div className="w-64 border-r bg-muted/20 flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-primary" />
            设计方案
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            共 {localSchemes.length} 个方案
          </p>
        </div>
        
        <div className="flex-1 overflow-auto">
          {localSchemes.map((scheme, index) => (
            <button
              key={index}
              onClick={() => setSelectedIndex(index)}
              className={cn(
                "w-full text-left p-4 border-b transition-colors",
                selectedIndex === index 
                  ? "bg-primary/10 border-l-4 border-l-primary" 
                  : "hover:bg-muted/50"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-sm truncate flex-1">
                  {scheme.name}
                </span>
                {selectedIndex === index && (
                  <ChevronRight className="w-4 h-4 text-primary flex-shrink-0" />
                )}
              </div>
              <span className="text-xs text-muted-foreground mt-1 block">
                {scheme.type}
              </span>
              {scheme.recommended && (
                <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded mt-2 inline-block">
                  AI推荐
                </span>
              )}
            </button>
          ))}
        </div>
        
        {/* 字段模板选择 + 确认按钮 */}
        <div className="p-4 border-t bg-background space-y-3">
          {/* 字段模板选择器 */}
          {!alreadySelected && fieldSchemas.length > 0 && (
            <div className="relative">
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                选择字段模板
              </label>
              <button
                onClick={() => setShowSchemaDropdown(!showSchemaDropdown)}
                className="w-full p-2 border rounded-lg text-sm text-left bg-background hover:bg-muted/50 flex items-center justify-between"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  {selectedSchema ? (
                    <span className="truncate">{selectedSchema.name}</span>
                  ) : (
                    <span className="text-muted-foreground">使用默认模板</span>
                  )}
                </div>
                <ChevronDown className={cn("w-4 h-4 transition-transform", showSchemaDropdown && "rotate-180")} />
              </button>
              
              {showSchemaDropdown && (
                <div className="absolute left-0 right-0 mt-1 bg-background border rounded-lg shadow-lg z-10 max-h-48 overflow-auto">
                  <button
                    onClick={() => { setSelectedSchemaId(null); setShowSchemaDropdown(false); }}
                    className={cn(
                      "w-full p-2 text-left text-sm hover:bg-muted/50",
                      !selectedSchemaId && "bg-primary/10"
                    )}
                  >
                    <span className="font-medium">默认模板</span>
                    <p className="text-xs text-muted-foreground">标题、大纲、正文、摘要</p>
                  </button>
                  {fieldSchemas.map(schema => (
                    <button
                      key={schema.id}
                      onClick={() => { setSelectedSchemaId(schema.id); setShowSchemaDropdown(false); }}
                      className={cn(
                        "w-full p-2 text-left text-sm hover:bg-muted/50 border-t",
                        selectedSchemaId === schema.id && "bg-primary/10"
                      )}
                    >
                      <span className="font-medium">{schema.name}</span>
                      <p className="text-xs text-muted-foreground">
                        {schema.field_count} 个字段 {schema.description && `· ${schema.description.slice(0, 20)}...`}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {hasChanges && (
            <button
              onClick={handleSaveChanges}
              className="w-full px-4 py-2 bg-muted text-foreground rounded-lg text-sm hover:bg-muted/80"
            >
              <Save className="w-4 h-4 inline-block mr-2" />
              保存修改
            </button>
          )}
          
          {/* 未选择时显示确认按钮 */}
          {!alreadySelected && (
            <button
              onClick={handleConfirm}
              disabled={isLoading}
              className="w-full px-4 py-3 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 disabled:opacity-50"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 inline-block mr-2 animate-spin" />处理中...</>
              ) : (
                <>
                  确认选择「{currentScheme?.name}」
                  {selectedSchema && <span className="text-primary-foreground/80 text-xs ml-1">({selectedSchema.name})</span>}
                </>
              )}
            </button>
          )}
          
          {/* 已选择时显示状态+重新选择按钮 */}
          {alreadySelected && (
            <>
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
                <Check className="w-5 h-5 text-green-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-700">
                    已选择: {localSchemes[previouslySelectedIndex ?? 0]?.name}
                  </p>
                  <p className="text-xs text-green-600">方案已确认，正在进行内容生产</p>
                </div>
              </div>
              
              {/* 如果选择了不同的方案，显示重新选择按钮 */}
              {selectedIndex !== previouslySelectedIndex && (
                <button
                  onClick={() => setShowReselectDialog(true)}
                  disabled={isLoading}
                  className="w-full px-4 py-3 bg-amber-500 text-white rounded-lg font-medium text-sm hover:bg-amber-600 disabled:opacity-50"
                >
                  <RotateCcw className="w-4 h-4 inline-block mr-2" />
                  切换到「{currentScheme?.name}」（需要重新生成）
                </button>
              )}
            </>
          )}
        </div>
        
        {/* 重新选择确认对话框 */}
        {showReselectDialog && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-background rounded-lg shadow-lg max-w-md w-full mx-4 p-6">
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="w-6 h-6 text-amber-500" />
                <h3 className="font-semibold text-lg">确认切换方案</h3>
              </div>
              
              <p className="text-muted-foreground mb-4">
                切换设计方案将导致已生成的内容需要重新生成。系统会自动创建当前版本的备份。
              </p>
              
              <div className="mb-4">
                <label className="text-sm font-medium block mb-2">备份描述（可选）</label>
                <input
                  type="text"
                  value={reselectDescription}
                  onChange={(e) => setReselectDescription(e.target.value)}
                  placeholder="描述此次切换的原因..."
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowReselectDialog(false)}
                  className="px-4 py-2 text-sm bg-muted rounded hover:bg-muted/80"
                >
                  取消
                </button>
                <button
                  onClick={handleReselect}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm bg-amber-500 text-white rounded hover:bg-amber-600 disabled:opacity-50"
                >
                  {isLoading ? '处理中...' : '确认切换并备份'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 右侧：方案详情编辑区 */}
      <div className="flex-1 overflow-auto p-6">
        {currentScheme ? (
          <div className="max-w-3xl mx-auto space-y-6">
            {/* 方案标题 */}
            <div className="flex items-center gap-4 mb-6">
              <EditableText
                value={currentScheme.name}
                onChange={(v) => handleSchemeChange('name', v)}
                label="方案名称"
                placeholder="输入方案名称"
              />
              <div className="flex-shrink-0">
                <label className="text-sm font-medium text-muted-foreground block">类型</label>
                <select
                  value={currentScheme.type}
                  onChange={(e) => handleSchemeChange('type', e.target.value)}
                  className="mt-1 p-2 border rounded-lg text-sm bg-background"
                >
                  <option value="稳妥型">稳妥型</option>
                  <option value="创意型">创意型</option>
                  <option value="激进型">激进型</option>
                  <option value="标准型">标准型</option>
                </select>
              </div>
            </div>

            {/* 核心描述 */}
            <EditableText
              value={currentScheme.description}
              onChange={(v) => handleSchemeChange('description', v)}
              label="核心描述"
              multiline
              placeholder="描述这个方案的核心定位和特点..."
            />

            {/* 整体思路 */}
            <EditableText
              value={currentScheme.approach}
              onChange={(v) => handleSchemeChange('approach', v)}
              label="整体思路"
              multiline
              placeholder="详细描述方案的实现思路..."
            />

            {/* 适用场景 */}
            <EditableText
              value={currentScheme.target_scenario || ''}
              onChange={(v) => handleSchemeChange('target_scenario', v)}
              label="适用场景"
              multiline
              placeholder="描述这个方案最适合的使用场景..."
            />

            {/* 关键特点 */}
            <EditableList
              value={currentScheme.key_features || []}
              onChange={(v) => handleSchemeChange('key_features', v)}
              label="关键特点"
              placeholder="输入一个关键特点..."
            />

            {/* 状态提示 */}
            {hasChanges && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-700">
                  你已修改了方案内容，记得点击「保存修改」或在确认选择时自动保存。
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            请从左侧选择一个方案
          </div>
        )}
      </div>
    </div>
  )
}
