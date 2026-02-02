// web/src/components/settings/SchemaSettings.tsx
// 字段模板管理
// 功能：FieldSchema的CRUD + 字段编辑 + 依赖关系配置
// 主要组件：SchemaSettings, SchemaEditor, DependencySelector

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Copy, ChevronRight, ChevronUp, ChevronDown, Loader2, Link2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/api/client'

interface Field {
  name: string
  description: string
  field_type: string
  required: boolean
  ai_hint: string
  order: number
  depends_on: string[]
  clarification_prompt?: string  // 生成前提问
}

interface FieldSchema {
  id: string
  name: string
  description: string
  fields: Field[]
  created_at: string
  updated_at: string
}

export default function SchemaSettings() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  
  // 获取列表
  const { data: schemas = [], isLoading } = useQuery({
    queryKey: ['schemas'],
    queryFn: async () => {
      const { data } = await apiClient.get('/schemas')
      return data as FieldSchema[]
    },
  })
  
  // 删除
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/schemas/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schemas'] })
      setSelectedId(null)
    },
  })
  
  // 复制
  const copyMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/schemas/${id}/copy`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schemas'] })
    },
  })

  const selectedSchema = schemas.find(s => s.id === selectedId)

  const handleDelete = (id: string) => {
    if (confirm('确定要删除这个模板吗？')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="h-full flex">
      {/* 左侧列表 */}
      <div className="w-64 border-r p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">字段模板</h3>
          <button
            onClick={() => {
              setIsCreating(true)
              setSelectedId(null)
            }}
            className="p-1 hover:bg-accent rounded"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
        
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : schemas.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            还没有字段模板
          </p>
        ) : (
          <div className="space-y-1">
            {schemas.map((schema) => (
              <div key={schema.id} className="group">
                <button
                  onClick={() => {
                    setSelectedId(schema.id)
                    setIsCreating(false)
                  }}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 rounded-md text-left",
                    selectedId === schema.id 
                      ? "bg-primary/10 text-primary" 
                      : "hover:bg-accent"
                  )}
                >
                  <div>
                    <span className="text-sm truncate block">{schema.name}</span>
                    <span className="text-xs text-muted-foreground">{schema.fields.length}个字段</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* 右侧编辑区 */}
      <div className="flex-1 p-6 overflow-auto">
        {isCreating ? (
          <SchemaEditor
            key="new-schema"
            onSave={() => {
              setIsCreating(false)
              queryClient.invalidateQueries({ queryKey: ['schemas'] })
            }}
            onCancel={() => setIsCreating(false)}
          />
        ) : selectedSchema ? (
          <SchemaEditor
            key={selectedSchema.id}
            schema={selectedSchema}
            onSave={() => {
              queryClient.invalidateQueries({ queryKey: ['schemas'] })
            }}
            onDelete={() => handleDelete(selectedSchema.id)}
            onCopy={() => copyMutation.mutate(selectedSchema.id)}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p>选择一个模板或点击 + 新建</p>
          </div>
        )}
      </div>
    </div>
  )
}


// ============ 依赖选择器组件 ============

interface DependencySelectorProps {
  fieldIndex: number
  fieldName: string
  allFields: Field[]
  selectedDependencies: string[]
  onChange: (deps: string[]) => void
}

function DependencySelector({
  fieldIndex,
  fieldName,
  allFields,
  selectedDependencies,
  onChange,
}: DependencySelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  
  // 可选的依赖字段（当前字段之前的所有字段）
  const availableFields = allFields
    .slice(0, fieldIndex)
    .filter(f => f.name !== fieldName)
  
  if (availableFields.length === 0) {
    return (
      <div className="text-xs text-muted-foreground italic">
        无可依赖的字段（当前是第一个字段）
      </div>
    )
  }
  
  const toggleDependency = (depName: string) => {
    if (selectedDependencies.includes(depName)) {
      onChange(selectedDependencies.filter(d => d !== depName))
    } else {
      onChange([...selectedDependencies, depName])
    }
  }
  
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full px-2 py-1.5 border rounded text-sm text-left flex items-center justify-between",
          selectedDependencies.length > 0 ? "border-primary/50 bg-primary/5" : ""
        )}
      >
        <span className="flex items-center gap-1">
          <Link2 className="w-3 h-3" />
          {selectedDependencies.length > 0 ? (
            <span>依赖 {selectedDependencies.length} 个字段</span>
          ) : (
            <span className="text-muted-foreground">无依赖</span>
          )}
        </span>
        <ChevronDown className={cn("w-4 h-4 transition-transform", isOpen && "rotate-180")} />
      </button>
      
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-background border rounded-md shadow-lg z-10 max-h-40 overflow-auto">
          {availableFields.map((f, i) => (
            <button
              key={i}
              type="button"
              onClick={() => toggleDependency(f.name)}
              className={cn(
                "w-full px-3 py-2 text-left text-sm hover:bg-accent flex items-center gap-2",
                selectedDependencies.includes(f.name) && "bg-primary/10"
              )}
            >
              <input
                type="checkbox"
                checked={selectedDependencies.includes(f.name)}
                onChange={() => {}}
                className="pointer-events-none"
              />
              <span>{f.name}</span>
              {selectedDependencies.includes(f.name) && (
                <Link2 className="w-3 h-3 text-primary ml-auto" />
              )}
            </button>
          ))}
        </div>
      )}
      
      {/* 显示已选依赖标签 */}
      {selectedDependencies.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedDependencies.map(dep => (
            <span 
              key={dep}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary/10 text-primary text-xs rounded"
            >
              {dep}
              <button
                type="button"
                onClick={() => toggleDependency(dep)}
                className="hover:text-destructive"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}


// ============ Schema编辑器 ============

interface SchemaEditorProps {
  schema?: FieldSchema
  onSave: () => void
  onCancel?: () => void
  onDelete?: () => void
  onCopy?: () => void
}

function SchemaEditor({ schema, onSave, onCancel, onDelete, onCopy }: SchemaEditorProps) {
  const isNew = !schema
  
  const [name, setName] = useState(schema?.name || '')
  const [description, setDescription] = useState(schema?.description || '')
  const [fields, setFields] = useState<Field[]>(
    schema?.fields?.map((f, i) => ({
      ...f,
      order: f.order ?? i,
      depends_on: f.depends_on ?? [],
    })) || []
  )
  const [editingFieldIndex, setEditingFieldIndex] = useState<number | null>(null)

  // 保存
  const saveMutation = useMutation({
    mutationFn: async () => {
      // 确保字段有正确的order和depends_on
      const fieldsToSave = fields.map((f, i) => ({
        ...f,
        order: i,
        depends_on: f.depends_on || [],
      }))
      const data = { name, description, fields: fieldsToSave }
      if (isNew) {
        return apiClient.post('/schemas', data)
      } else {
        return apiClient.put(`/schemas/${schema!.id}`, data)
      }
    },
    onSuccess: () => {
      onSave()
    },
  })

  const handleAddField = () => {
    setFields([...fields, {
      name: `字段${fields.length + 1}`,
      description: '',
      field_type: 'text',
      required: true,
      ai_hint: '',
      order: fields.length,
      depends_on: [],
      clarification_prompt: '',
    }])
    setEditingFieldIndex(fields.length)
  }

  const handleUpdateField = (index: number, updates: Partial<Field>) => {
    const newFields = [...fields]
    newFields[index] = { ...newFields[index], ...updates }
    setFields(newFields)
  }

  const handleDeleteField = (index: number) => {
    const deletedFieldName = fields[index].name
    // 删除字段时，同时删除其他字段对它的依赖
    const newFields = fields
      .filter((_, i) => i !== index)
      .map(f => ({
        ...f,
        depends_on: f.depends_on.filter(d => d !== deletedFieldName)
      }))
    setFields(newFields)
    setEditingFieldIndex(null)
  }

  const handleMoveField = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1
    if (newIndex < 0 || newIndex >= fields.length) return
    
    const newFields = [...fields]
    ;[newFields[index], newFields[newIndex]] = [newFields[newIndex], newFields[index]]
    // 更新order
    newFields.forEach((f, i) => { f.order = i })
    setFields(newFields)
  }

  // 计算依赖关系统计
  const dependencyStats = fields.reduce((acc, f) => {
    acc.total += f.depends_on?.length || 0
    return acc
  }, { total: 0 })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">
            {isNew ? '新建字段模板' : `编辑: ${schema?.name}`}
          </h3>
          {dependencyStats.total > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              <Link2 className="w-3 h-3 inline-block mr-1" />
              已配置 {dependencyStats.total} 个依赖关系
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {onCancel && (
            <button onClick={onCancel} className="px-4 py-2 text-sm border rounded-md hover:bg-accent">
              取消
            </button>
          )}
          {onCopy && (
            <button onClick={onCopy} className="px-4 py-2 text-sm border rounded-md hover:bg-accent flex items-center gap-1">
              <Copy className="w-4 h-4" />
              复制
            </button>
          )}
          {onDelete && (
            <button onClick={onDelete} className="px-4 py-2 text-sm text-red-600 border border-red-300 rounded-md hover:bg-red-50">
              删除
            </button>
          )}
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || !name.trim()}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {saveMutation.isPending ? '保存中...' : '保存'}
          </button>
        </div>
      </div>

      {/* 基本信息 */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">模板名称</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="例如：课程模板"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">模板描述</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="例如：适用于线上课程的完整素材"
          />
        </div>
      </div>

      {/* 字段列表 */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium">字段列表（按生成顺序排列）</label>
          <button
            onClick={handleAddField}
            className="px-3 py-1 text-sm border rounded-md hover:bg-accent flex items-center gap-1"
          >
            <Plus className="w-4 h-4" />
            添加字段
          </button>
        </div>

        {fields.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center border rounded-md">
            还没有字段，点击上方按钮添加
          </p>
        ) : (
          <div className="space-y-2">
            {fields.map((field, index) => (
              <div key={index} className="border rounded-md">
                {/* 字段头部 */}
                <div 
                  className="flex items-center gap-2 p-3 cursor-pointer hover:bg-accent/50"
                  onClick={() => setEditingFieldIndex(editingFieldIndex === index ? null : index)}
                >
                  <span className="text-sm text-muted-foreground w-6">{index + 1}.</span>
                  <span className="font-medium flex-1">{field.name}</span>
                  
                  {/* 依赖指示器 */}
                  {field.depends_on?.length > 0 && (
                    <span className="flex items-center gap-1 text-xs text-primary bg-primary/10 px-2 py-0.5 rounded">
                      <Link2 className="w-3 h-3" />
                      {field.depends_on.length}
                    </span>
                  )}
                  
                  <span className="text-xs bg-muted px-2 py-0.5 rounded">{field.field_type}</span>
                  {field.required && <span className="text-xs text-red-500">必填</span>}
                  
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleMoveField(index, 'up') }}
                      disabled={index === 0}
                      className="p-1 hover:bg-accent rounded disabled:opacity-30"
                    >
                      <ChevronUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleMoveField(index, 'down') }}
                      disabled={index === fields.length - 1}
                      className="p-1 hover:bg-accent rounded disabled:opacity-30"
                    >
                      <ChevronDown className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteField(index) }}
                      className="p-1 hover:bg-red-100 text-red-500 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* 字段编辑区 */}
                {editingFieldIndex === index && (
                  <div className="border-t p-4 bg-muted/30 space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium mb-1">字段名称</label>
                        <input
                          type="text"
                          value={field.name}
                          onChange={(e) => handleUpdateField(index, { name: e.target.value })}
                          className="w-full px-2 py-1.5 border rounded text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium mb-1">字段类型</label>
                        <select
                          value={field.field_type}
                          onChange={(e) => handleUpdateField(index, { field_type: e.target.value })}
                          className="w-full px-2 py-1.5 border rounded text-sm"
                        >
                          <option value="text">文本</option>
                          <option value="list">列表</option>
                          <option value="structured">结构化</option>
                        </select>
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-xs font-medium mb-1">字段说明</label>
                      <input
                        type="text"
                        value={field.description}
                        onChange={(e) => handleUpdateField(index, { description: e.target.value })}
                        className="w-full px-2 py-1.5 border rounded text-sm"
                        placeholder="这个字段用于..."
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs font-medium mb-1">
                        AI生成提示词
                        <span className="text-muted-foreground font-normal ml-1">
                          （直接传递给大模型，指导内容生成）
                        </span>
                      </label>
                      <textarea
                        value={field.ai_hint}
                        onChange={(e) => handleUpdateField(index, { ai_hint: e.target.value })}
                        className="w-full px-2 py-1.5 border rounded text-sm min-h-[80px] resize-y"
                        placeholder="例如：请生成包含以下要素的内容：1. 具体场景描述 2. 角色对话..."
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        💡 这段文字会在生成该字段时，作为提示词的一部分传递给AI大模型
                      </p>
                    </div>
                    
                    {/* 依赖关系配置 */}
                    <div>
                      <label className="block text-xs font-medium mb-1 flex items-center gap-1">
                        <Link2 className="w-3 h-3" />
                        依赖字段（此字段生成时，会引用这些字段的内容）
                      </label>
                      <DependencySelector
                        fieldIndex={index}
                        fieldName={field.name}
                        allFields={fields}
                        selectedDependencies={field.depends_on || []}
                        onChange={(deps) => handleUpdateField(index, { depends_on: deps })}
                      />
                    </div>
                    
                    {/* 生成前提问配置 */}
                    <div>
                      <label className="block text-xs font-medium mb-1">
                        生成前提问
                        <span className="text-muted-foreground font-normal ml-1">
                          （可选，生成前弹出对话框让用户补充信息）
                        </span>
                      </label>
                      <textarea
                        value={field.clarification_prompt || ''}
                        onChange={(e) => handleUpdateField(index, { clarification_prompt: e.target.value })}
                        className="w-full px-2 py-1.5 border rounded text-sm min-h-[60px] resize-y"
                        placeholder="例如：请描述这个角色的核心性格特征..."
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        💬 如果填写，生成该字段前会先弹出对话框询问用户（只问1轮）
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2 pt-2 border-t">
                      <input
                        type="checkbox"
                        id={`required-${index}`}
                        checked={field.required}
                        onChange={(e) => handleUpdateField(index, { required: e.target.checked })}
                      />
                      <label htmlFor={`required-${index}`} className="text-sm">必填字段</label>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* 依赖关系可视化提示 */}
      {fields.some(f => f.depends_on?.length > 0) && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 mb-2 flex items-center gap-1">
            <Link2 className="w-4 h-4" />
            依赖关系说明
          </h4>
          <ul className="text-xs text-blue-700 space-y-1">
            {fields.map((f, i) => (
              f.depends_on?.length > 0 && (
                <li key={i}>
                  <span className="font-medium">{f.name}</span>
                  {' 依赖于：'}
                  {f.depends_on.join('、')}
                </li>
              )
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
