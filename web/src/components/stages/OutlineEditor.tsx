// web/src/components/stages/OutlineEditor.tsx
// 目录编辑组件
// 功能：编辑内涵生产的章节和字段结构，支持拖拽排序、增删改
// 主要组件：OutlineEditor, SortableSection, SortableField
// 使用 @dnd-kit 实现拖拽排序
// 
// 修改记录 2026-02-02:
// - 移除了 outlineConfirmed 对编辑功能的限制，目录确认后仍可编辑
// - 删除章节/字段改为直接调用后端API，支持删除已完成内容
// - 删除操作会确认提示，避免误删已生成内容

import { useState, useEffect } from 'react'
import { 
  Plus, Trash2, Edit3, Save, ChevronDown, ChevronRight,
  GripVertical, Check, AlertCircle, RefreshCw, RotateCcw, Loader2, AlertTriangle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ContentSection, ContentField, FieldDefinition } from '@/types'
import apiClient from '@/api/client'

// dnd-kit imports
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  UniqueIdentifier,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'


// ============ 可排序字段组件 ============

interface SortableFieldProps {
  field: ContentField
  sectionId: string
  sectionIndex: number
  fieldIndex: number
  isEditing: boolean
  outlineConfirmed: boolean
  workflowId: string
  onEdit: () => void
  onUpdate: (updates: Partial<ContentField>) => void
  onRemove: () => void
  onEditEnd: () => void
  onRegenerate: (fieldId: string) => Promise<void>
}

function SortableField({
  field,
  sectionId: _sectionId,
  sectionIndex,
  fieldIndex,
  isEditing,
  outlineConfirmed,
  workflowId: _workflowId,
  onEdit,
  onUpdate,
  onRemove,
  onEditEnd,
  onRegenerate,
}: SortableFieldProps) {
  // 保留 _sectionId 和 _workflowId 供将来使用
  void _sectionId
  void _workflowId
  const [isRegenerating, setIsRegenerating] = useState(false)
  
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: field.id,
    // 始终允许拖拽排序
    disabled: false,
  })
  
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }
  
  const handleRegenerate = async () => {
    setIsRegenerating(true)
    try {
      await onRegenerate(field.id)
    } finally {
      setIsRegenerating(false)
    }
  }
  
  // 检查是否有上下文过期标记
  const isStale = field.context_stale === true
  
  return (
    <div 
      ref={setNodeRef}
      style={style}
      className={cn(
        "flex items-center gap-2 p-2 border rounded bg-muted/10 hover:bg-muted/20",
        isDragging && "ring-2 ring-primary shadow-lg",
        isStale && "border-amber-400 bg-amber-50",
        field.status === 'generating' && "border-blue-400 bg-blue-50"
      )}
    >
      {/* 始终显示拖拽手柄 */}
      <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing">
        <GripVertical className="w-3 h-3 text-muted-foreground" />
      </div>
      <span className="text-xs text-muted-foreground w-6">
        {sectionIndex + 1}.{fieldIndex + 1}
      </span>
      
      {isEditing ? (
        <input
          type="text"
          value={field.display_name || field.name}
          onChange={(e) => onUpdate({ 
            display_name: e.target.value,
            name: e.target.value.toLowerCase().replace(/\s+/g, '_')
          })}
          onBlur={onEditEnd}
          onKeyDown={(e) => e.key === 'Enter' && onEditEnd()}
          className="flex-1 px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          autoFocus
        />
      ) : (
        <span className="flex-1 text-sm">{field.display_name || field.name}</span>
      )}
      
      {/* 状态指示器 */}
      {field.status === 'completed' && !isStale && (
        <Check className="w-4 h-4 text-green-500" />
      )}
      {field.status === 'generating' && (
        <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      )}
      {isStale && (
        <span title="上下文已过期，建议重新生成">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
        </span>
      )}
      
      {/* 操作按钮 - 始终显示 */}
      <div className="flex items-center gap-1">
        {/* 重新生成按钮（对已完成或过期的字段显示） */}
        {(field.status === 'completed' || isStale) && (
          <button
            onClick={handleRegenerate}
            disabled={isRegenerating}
            className="p-1 hover:bg-primary/10 rounded text-primary"
            title="重新生成此字段"
          >
            {isRegenerating ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RotateCcw className="w-3 h-3" />
            )}
          </button>
        )}
        
        {/* 编辑和删除按钮 - 始终显示 */}
        <button
          onClick={onEdit}
          className="p-1 hover:bg-muted rounded"
          title="编辑字段"
        >
          <Edit3 className="w-3 h-3 text-muted-foreground" />
        </button>
        <button
          onClick={onRemove}
          className="p-1 hover:bg-destructive/10 rounded"
          title="删除字段"
        >
          <Trash2 className="w-3 h-3 text-destructive" />
        </button>
      </div>
    </div>
  )
}


// ============ 可排序章节组件 ============

interface SortableSectionProps {
  section: ContentSection
  sectionIndex: number
  isExpanded: boolean
  isEditing: boolean
  editingFieldId: string | null
  outlineConfirmed: boolean
  workflowId: string
  templateFields: FieldDefinition[]  // 可选择的字段模板
  showFieldDropdown: boolean  // 是否显示字段选择下拉菜单
  usedFieldNames: Set<string>  // 当前章节已使用的字段名
  onToggle: () => void
  onEdit: () => void
  onEditEnd: () => void
  onUpdate: (updates: Partial<ContentSection>) => void
  onRemove: () => void
  onAddFields: (templateFields: FieldDefinition[]) => void  // 支持多选添加
  onAddCustomField: () => void  // 添加自定义空白字段
  onToggleFieldDropdown: () => void  // 切换字段选择下拉菜单
  onEditField: (fieldId: string) => void
  onEditFieldEnd: () => void
  onUpdateField: (fieldId: string, updates: Partial<ContentField>) => void
  onRemoveField: (fieldId: string) => void
  onFieldsReorder: (newFields: ContentField[]) => void
  onRegenerateField: (fieldId: string) => Promise<void>
  onRegenerateChain: (chainHeadId: string) => Promise<void>
}

function SortableSection({
  section,
  sectionIndex,
  isExpanded,
  isEditing,
  editingFieldId,
  outlineConfirmed,
  workflowId,
  templateFields,
  showFieldDropdown,
  usedFieldNames,
  onToggle,
  onEdit,
  onEditEnd,
  onUpdate,
  onRemove,
  onAddFields,
  onAddCustomField,
  onToggleFieldDropdown,
  onEditField,
  onEditFieldEnd,
  onUpdateField,
  onRemoveField,
  onFieldsReorder,
  onRegenerateField,
  onRegenerateChain,
}: SortableSectionProps) {
  // 多选状态
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set())
  const [isRegeneratingChain, setIsRegeneratingChain] = useState(false)
  
  // 检查章节中第一个字段是否可以作为链头
  const firstField = section.fields[0]
  const canRegenerateChain = outlineConfirmed && firstField && 
    (firstField.status === 'completed' || firstField.context_stale)
  
  const handleRegenerateChain = async () => {
    if (!firstField) return
    setIsRegeneratingChain(true)
    try {
      await onRegenerateChain(firstField.id)
    } finally {
      setIsRegeneratingChain(false)
    }
  }
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: section.id,
    // 始终允许拖拽排序
    disabled: false,
  })
  
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }
  
  // 字段排序的sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )
  
  const handleFieldDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    
    if (over && active.id !== over.id) {
      const oldIndex = section.fields.findIndex(f => f.id === active.id)
      const newIndex = section.fields.findIndex(f => f.id === over.id)
      
      if (oldIndex !== -1 && newIndex !== -1) {
        const newFields = arrayMove(section.fields, oldIndex, newIndex)
        // 更新 order 属性
        const reorderedFields = newFields.map((f, i) => ({ ...f, order: i }))
        onFieldsReorder(reorderedFields)
      }
    }
  }
  
  return (
    <div 
      ref={setNodeRef}
      style={style}
      className={cn(
        "border rounded-lg bg-background",
        isDragging && "ring-2 ring-primary shadow-lg"
      )}
    >
      {/* 章节头部 */}
      <div 
        className="flex items-center gap-2 p-3 bg-muted/30 cursor-pointer hover:bg-muted/50"
        onClick={onToggle}
      >
        {/* 始终显示拖拽手柄 */}
        <div 
          {...attributes} 
          {...listeners} 
          className="cursor-grab active:cursor-grabbing"
          onClick={(e) => e.stopPropagation()}
        >
          <GripVertical className="w-4 h-4 text-muted-foreground" />
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
        )}
        
        {isEditing ? (
          <input
            type="text"
            value={section.name}
            onChange={(e) => onUpdate({ name: e.target.value })}
            onBlur={onEditEnd}
            onKeyDown={(e) => e.key === 'Enter' && onEditEnd()}
            className="flex-1 px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="flex-1 font-medium">{section.name}</span>
        )}
        
        <span className="text-xs text-muted-foreground">
          {section.fields.length} 字段
        </span>
        
        {/* 重新生成链条按钮 */}
        {canRegenerateChain && (
          <button
            onClick={(e) => { e.stopPropagation(); handleRegenerateChain() }}
            disabled={isRegeneratingChain}
            className="p-1.5 hover:bg-primary/10 rounded text-primary flex items-center gap-1 text-xs"
            title="重新生成本章节所有字段"
          >
            {isRegeneratingChain ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                <span className="hidden sm:inline">重新生成</span>
              </>
            )}
          </button>
        )}
        
        {/* 编辑和删除按钮 - 始终显示 */}
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={onEdit}
            className="p-1 hover:bg-muted rounded"
            title="编辑章节名称"
          >
            <Edit3 className="w-4 h-4 text-muted-foreground" />
          </button>
          <button
            onClick={onRemove}
            className="p-1 hover:bg-destructive/10 rounded"
            title="删除章节"
          >
            <Trash2 className="w-4 h-4 text-destructive" />
          </button>
        </div>
      </div>

      {/* 章节内容 - 字段列表 */}
      {isExpanded && (
        <div className="p-3 space-y-2">
          {section.fields.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              暂无字段，点击下方按钮添加
            </p>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleFieldDragEnd}
            >
              <SortableContext
                items={section.fields.map(f => f.id)}
                strategy={verticalListSortingStrategy}
              >
                {section.fields.map((field, fieldIndex) => (
                  <SortableField
                    key={field.id}
                    field={field}
                    sectionId={section.id}
                    sectionIndex={sectionIndex}
                    fieldIndex={fieldIndex}
                    isEditing={editingFieldId === field.id}
                    outlineConfirmed={outlineConfirmed}
                    workflowId={workflowId}
                    onEdit={() => onEditField(field.id)}
                    onUpdate={(updates) => onUpdateField(field.id, updates)}
                    onRemove={() => onRemoveField(field.id)}
                    onEditEnd={onEditFieldEnd}
                    onRegenerate={onRegenerateField}
                  />
                ))}
              </SortableContext>
            </DndContext>
          )}
          
          {/* 始终显示添加字段按钮 */}
          <div className="relative">
            <button
              onClick={() => {
                setSelectedFields(new Set())
                onToggleFieldDropdown()
              }}
              className="w-full py-2 border-2 border-dashed rounded text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors flex items-center justify-center gap-1"
            >
              <Plus className="w-4 h-4" />
              添加字段
              {templateFields.length > 0 && <ChevronDown className="w-3 h-3 ml-1" />}
            </button>
            
            {/* 字段选择下拉菜单（支持多选） */}
            {showFieldDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-popover border rounded-md shadow-lg z-[100] max-h-80 overflow-auto">
                {templateFields.length > 0 ? (
                  <>
                    <div className="px-3 py-2 text-xs text-muted-foreground border-b bg-muted/50 flex items-center justify-between">
                      <span>从模板选择字段（可多选）</span>
                      {selectedFields.size > 0 && (
                        <span className="text-primary font-medium">已选 {selectedFields.size} 个</span>
                      )}
                    </div>
                    {templateFields.map((tf) => {
                      const isUsed = usedFieldNames.has(tf.name)
                      const isSelected = selectedFields.has(tf.name)
                      return (
                        <label
                          key={tf.name}
                          className={cn(
                            "w-full px-3 py-2 text-left text-sm flex items-center gap-2 cursor-pointer",
                            isUsed 
                              ? "text-muted-foreground bg-muted/30 cursor-not-allowed"
                              : "hover:bg-muted"
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            disabled={isUsed}
                            onChange={(e) => {
                              if (isUsed) return
                              const newSet = new Set(selectedFields)
                              if (e.target.checked) {
                                newSet.add(tf.name)
                              } else {
                                newSet.delete(tf.name)
                              }
                              setSelectedFields(newSet)
                            }}
                            className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium">{tf.name}</div>
                            {tf.description && (
                              <div className="text-xs text-muted-foreground truncate">
                                {tf.description}
                              </div>
                            )}
                          </div>
                          {isUsed && (
                            <span className="text-xs text-muted-foreground flex-shrink-0">已添加</span>
                          )}
                        </label>
                      )
                    })}
                    
                    {/* 操作按钮 */}
                    <div className="border-t p-2 flex gap-2">
                      {selectedFields.size > 0 && (
                        <button
                          onClick={() => {
                            const fieldsToAdd = templateFields.filter(tf => selectedFields.has(tf.name))
                            onAddFields(fieldsToAdd)
                            setSelectedFields(new Set())
                          }}
                          className="flex-1 px-3 py-1.5 bg-primary text-primary-foreground rounded text-sm font-medium hover:bg-primary/90"
                        >
                          添加选中的 {selectedFields.size} 个字段
                        </button>
                      )}
                      <button
                        onClick={() => {
                          onAddCustomField()
                          setSelectedFields(new Set())
                        }}
                        className={cn(
                          "px-3 py-1.5 text-sm hover:bg-muted rounded flex items-center gap-1",
                          selectedFields.size === 0 && "flex-1"
                        )}
                      >
                        <Plus className="w-3 h-3" />
                        自定义字段
                      </button>
                    </div>
                  </>
                ) : (
                  <button
                    onClick={onAddCustomField}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-muted"
                  >
                    <Plus className="w-3 h-3 inline mr-2" />
                    创建自定义字段
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


// ============ 主编辑器组件 ============

interface OutlineEditorProps {
  workflowId: string
  sections: ContentSection[]
  outlineConfirmed: boolean
  templateFields?: FieldDefinition[]  // 可选择的字段模板
  onSave: () => void
  onConfirm: () => void
}

export default function OutlineEditor({
  workflowId,
  sections: initialSections,
  outlineConfirmed,
  templateFields = [],
  onSave,
  onConfirm,
}: OutlineEditorProps) {
  const [sections, setSections] = useState<ContentSection[]>(initialSections)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [editingSection, setEditingSection] = useState<string | null>(null)
  const [editingField, setEditingField] = useState<string | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const [activeDragId, setActiveDragId] = useState<UniqueIdentifier | null>(null)
  const [showFieldDropdown, setShowFieldDropdown] = useState<string | null>(null) // 显示字段选择的章节ID

  // 章节排序的sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  useEffect(() => {
    setSections(initialSections)
    // 默认展开所有章节
    setExpandedSections(new Set(initialSections.map(s => s.id)))
  }, [initialSections])

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(sectionId)) {
        next.delete(sectionId)
      } else {
        next.add(sectionId)
      }
      return next
    })
  }

  const addSection = () => {
    const newSection: ContentSection = {
      id: `section_${Date.now()}`,
      name: '新章节',
      description: '',
      order: sections.length,
      status: 'pending',
      fields: [],
    }
    setSections([...sections, newSection])
    setExpandedSections(prev => new Set([...prev, newSection.id]))
    setEditingSection(newSection.id)
    setHasChanges(true)
  }

  const removeSection = async (sectionId: string) => {
    // 找到要删除的章节
    const section = sections.find(s => s.id === sectionId)
    const completedFields = section?.fields.filter(f => f.status === 'completed').length || 0
    
    // 如果有已完成字段，确认删除
    if (completedFields > 0) {
      if (!confirm(`该章节有 ${completedFields} 个已完成的字段，确定要删除吗？`)) {
        return
      }
    }
    
    try {
      // 调用后端API删除
      const response = await apiClient.delete(`/workflow/${workflowId}/sections/${sectionId}`)
      if (response.data.success) {
        // 本地状态更新
        setSections(sections.filter(s => s.id !== sectionId))
        // 刷新父组件
        onSave()
      }
    } catch (error: any) {
      console.error('删除章节失败:', error)
      alert(`删除失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  const updateSection = (sectionId: string, updates: Partial<ContentSection>) => {
    setSections(sections.map(s => 
      s.id === sectionId ? { ...s, ...updates } : s
    ))
    setHasChanges(true)
  }

  // 获取章节中已使用的字段名
  const getUsedFieldNames = (sectionId: string): Set<string> => {
    const usedNames = new Set<string>()
    for (const section of sections) {
      if (section.id === sectionId) {
        for (const field of section.fields) {
          usedNames.add(field.name)
        }
      }
    }
    return usedNames
  }

  // 批量添加字段（从模板选择）
  const addFields = (sectionId: string, templateFieldList: FieldDefinition[]) => {
    if (templateFieldList.length === 0) return
    
    setSections(sections.map(s => {
      if (s.id === sectionId) {
        const newFields = templateFieldList.map((tf, index) => ({
          id: `field_${Date.now()}_${index}`,
          name: tf.name,
          display_name: tf.name,
          description: tf.description || '',
          order: s.fields.length + index,
          content: '',
          status: 'pending' as const,
          evaluation_score: null,
          custom_depends_on: tf.depends_on || [],
        }))
        return { ...s, fields: [...s.fields, ...newFields] }
      }
      return s
    }))
    setShowFieldDropdown(null)
    setHasChanges(true)
  }

  // 添加自定义空白字段
  const addCustomField = (sectionId: string) => {
    const newField: ContentField = {
      id: `field_${Date.now()}`,
      name: '新字段',
      display_name: '新字段',
      description: '',
      order: 0,
      content: '',
      status: 'pending',
      evaluation_score: null,
    }
    
    setSections(sections.map(s => {
      if (s.id === sectionId) {
        newField.order = s.fields.length
        return { ...s, fields: [...s.fields, newField] }
      }
      return s
    }))
    setShowFieldDropdown(null)
    setEditingField(newField.id)
    setHasChanges(true)
  }

  const removeField = async (sectionId: string, fieldId: string) => {
    // 找到要删除的字段
    const section = sections.find(s => s.id === sectionId)
    const field = section?.fields.find(f => f.id === fieldId)
    
    // 如果字段已完成，确认删除
    if (field?.status === 'completed') {
      if (!confirm(`该字段已生成内容，确定要删除吗？`)) {
        return
      }
    }
    
    try {
      // 调用后端API删除
      const response = await apiClient.delete(`/workflow/${workflowId}/sections/${sectionId}/fields/${fieldId}`)
      if (response.data.success) {
        // 本地状态更新
        setSections(sections.map(s => {
          if (s.id === sectionId) {
            return { ...s, fields: s.fields.filter(f => f.id !== fieldId) }
          }
          return s
        }))
        // 刷新父组件
        onSave()
      }
    } catch (error: any) {
      console.error('删除字段失败:', error)
      alert(`删除失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  const updateField = (sectionId: string, fieldId: string, updates: Partial<ContentField>) => {
    setSections(sections.map(s => {
      if (s.id === sectionId) {
        return {
          ...s,
          fields: s.fields.map(f => f.id === fieldId ? { ...f, ...updates } : f)
        }
      }
      return s
    }))
    setHasChanges(true)
  }

  const reorderFieldsInSection = (sectionId: string, newFields: ContentField[]) => {
    setSections(sections.map(s => {
      if (s.id === sectionId) {
        return { ...s, fields: newFields }
      }
      return s
    }))
    setHasChanges(true)
  }

  // 章节拖拽处理
  const handleSectionDragStart = (event: DragStartEvent) => {
    setActiveDragId(event.active.id)
  }

  const handleSectionDragEnd = (event: DragEndEvent) => {
    setActiveDragId(null)
    const { active, over } = event
    
    if (over && active.id !== over.id) {
      const oldIndex = sections.findIndex(s => s.id === active.id)
      const newIndex = sections.findIndex(s => s.id === over.id)
      
      if (oldIndex !== -1 && newIndex !== -1) {
        const newSections = arrayMove(sections, oldIndex, newIndex)
        // 更新 order 属性
        const reorderedSections = newSections.map((s, i) => ({ ...s, order: i }))
        setSections(reorderedSections)
        setHasChanges(true)
      }
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await apiClient.patch(`/workflow/${workflowId}/outline`, {
        sections: sections.map((s, idx) => ({
          id: s.id,
          name: s.name,
          description: s.description,
          order: idx, // 使用当前索引作为order
          fields: s.fields.map((f, fIdx) => ({
            id: f.id,
            name: f.name,
            display_name: f.display_name || f.name,
            description: f.description || '',
            order: fIdx, // 使用当前索引作为order
          }))
        })),
        confirm: false,
      })
      setHasChanges(false)
      onSave()
    } catch (error: any) {
      console.error('保存失败:', error)
      alert(`保存失败: ${error.response?.data?.detail || error.message}`)
    }
    setIsSaving(false)
  }

  const handleConfirm = async () => {
    // 先保存
    if (hasChanges) {
      await handleSave()
    }
    
    setIsConfirming(true)
    try {
      // 调用确认目录结构 API
      await apiClient.post(`/workflow/${workflowId}/confirm-outline`)
      onConfirm()
    } catch (error: any) {
      console.error('确认失败:', error)
      alert(`确认失败: ${error.response?.data?.detail || error.message}`)
    }
    setIsConfirming(false)
  }

  // 重新生成单个字段
  const handleRegenerateField = async (fieldId: string) => {
    try {
      const response = await apiClient.post(`/workflow/${workflowId}/fields/${fieldId}/regenerate`)
      
      if (response.data.success) {
        // 刷新数据
        onSave()
        
        // 如果有下游字段被标记为过期，提示用户
        if (response.data.downstream_stale_count > 0) {
          alert(`字段已重新生成。${response.data.downstream_stale_count} 个后续字段已标记为过期，建议重新生成。`)
        }
      }
    } catch (error: any) {
      console.error('重新生成失败:', error)
      alert(`重新生成失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  // 重新生成链条（从指定字段开始的所有后续字段）
  const handleRegenerateChain = async (chainHeadId: string) => {
    if (!confirm('确定要重新生成此章节的所有字段吗？这可能需要一些时间。')) {
      return
    }
    
    try {
      const response = await apiClient.post(`/workflow/${workflowId}/chains/${chainHeadId}/regenerate`)
      
      if (response.data.success) {
        // 刷新数据
        onSave()
        alert(`已重新生成 ${response.data.regenerated_count}/${response.data.total_in_chain} 个字段。`)
      }
    } catch (error: any) {
      console.error('重新生成链条失败:', error)
      alert(`重新生成链条失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  const totalFields = sections.reduce((sum, s) => sum + s.fields.length, 0)
  
  // 获取当前拖拽的章节
  const activeDragSection = activeDragId 
    ? sections.find(s => s.id === activeDragId)
    : null

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="p-4 border-b bg-muted/20">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-lg">目录结构</h2>
            <p className="text-sm text-muted-foreground">
              {sections.length} 个章节，{totalFields} 个字段
            </p>
          </div>
          {outlineConfirmed ? (
            <div className="flex items-center gap-2 text-green-600">
              <Check className="w-5 h-5" />
              <span className="text-sm font-medium">已确认</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-amber-600">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">待确认</span>
            </div>
          )}
        </div>
      </div>

      {/* 章节列表 */}
      <div className="flex-1 overflow-auto p-4">
        {sections.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>暂无章节</p>
            <p className="text-sm mt-1">点击下方按钮添加第一个章节</p>
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleSectionDragStart}
            onDragEnd={handleSectionDragEnd}
          >
            <SortableContext
              items={sections.map(s => s.id)}
              strategy={verticalListSortingStrategy}
            >
              <div className="space-y-4">
                {sections.map((section, sectionIndex) => (
                  <SortableSection
                    key={section.id}
                    section={section}
                    sectionIndex={sectionIndex}
                    isExpanded={expandedSections.has(section.id)}
                    isEditing={editingSection === section.id}
                    editingFieldId={editingField}
                    outlineConfirmed={outlineConfirmed}
                    workflowId={workflowId}
                    templateFields={templateFields}
                    showFieldDropdown={showFieldDropdown === section.id}
                    usedFieldNames={getUsedFieldNames(section.id)}
                    onToggle={() => toggleSection(section.id)}
                    onEdit={() => setEditingSection(section.id)}
                    onEditEnd={() => setEditingSection(null)}
                    onUpdate={(updates) => updateSection(section.id, updates)}
                    onRemove={() => removeSection(section.id)}
                    onAddFields={(templateFieldList) => addFields(section.id, templateFieldList)}
                    onAddCustomField={() => addCustomField(section.id)}
                    onToggleFieldDropdown={() => setShowFieldDropdown(
                      showFieldDropdown === section.id ? null : section.id
                    )}
                    onEditField={(fieldId) => setEditingField(fieldId)}
                    onEditFieldEnd={() => setEditingField(null)}
                    onUpdateField={(fieldId, updates) => updateField(section.id, fieldId, updates)}
                    onRemoveField={(fieldId) => removeField(section.id, fieldId)}
                    onFieldsReorder={(newFields) => reorderFieldsInSection(section.id, newFields)}
                    onRegenerateField={handleRegenerateField}
                    onRegenerateChain={handleRegenerateChain}
                  />
                ))}
              </div>
            </SortableContext>
            
            {/* 拖拽overlay */}
            <DragOverlay>
              {activeDragSection ? (
                <div className="border rounded-lg bg-background shadow-xl opacity-90">
                  <div className="flex items-center gap-2 p-3 bg-muted/30">
                    <GripVertical className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium">{activeDragSection.name}</span>
                    <span className="text-xs text-muted-foreground ml-auto">
                      {activeDragSection.fields.length} 字段
                    </span>
                  </div>
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        )}

        {/* 始终显示添加章节按钮 */}
        <button
          onClick={addSection}
          className="w-full mt-4 py-3 border-2 border-dashed rounded-lg text-muted-foreground hover:border-primary hover:text-primary transition-colors flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          添加章节
        </button>
      </div>

      {/* 底部操作栏 */}
      <div className="p-4 border-t bg-background space-y-2">
        {/* 保存按钮：有改动时始终显示 */}
        {hasChanges && (
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            {isSaving ? '保存中...' : '保存目录结构'}
          </button>
        )}
        
        {/* 确认按钮：仅未确认时显示 */}
        {!outlineConfirmed && totalFields > 0 && !hasChanges && (
          <button
            onClick={handleConfirm}
            disabled={isConfirming || sections.length === 0 || totalFields === 0}
            className="w-full px-4 py-3 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Check className="w-4 h-4" />
            {isConfirming ? '确认中...' : '确认目录结构并开始生产'}
          </button>
        )}
        
        {/* 已确认且无改动时显示状态 */}
        {outlineConfirmed && !hasChanges && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-center">
            <Check className="w-5 h-5 text-green-600 mx-auto mb-1" />
            <p className="text-sm font-medium text-green-700">目录已确认</p>
            <p className="text-xs text-green-600">修改会自动保存</p>
          </div>
        )}
      </div>
    </div>
  )
}
