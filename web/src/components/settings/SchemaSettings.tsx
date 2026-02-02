// web/src/components/settings/SchemaSettings.tsx
// 字段模板管理
// 功能：FieldSchema的CRUD + 字段编辑

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Copy, ChevronRight, ChevronUp, ChevronDown, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/api/client'

interface Field {
  name: string
  description: string
  field_type: string
  required: boolean
  ai_hint: string
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

// Schema编辑器
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
  const [fields, setFields] = useState<Field[]>(schema?.fields || [])
  const [editingFieldIndex, setEditingFieldIndex] = useState<number | null>(null)

  // 保存
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data = { name, description, fields }
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
    }])
    setEditingFieldIndex(fields.length)
  }

  const handleUpdateField = (index: number, updates: Partial<Field>) => {
    const newFields = [...fields]
    newFields[index] = { ...newFields[index], ...updates }
    setFields(newFields)
  }

  const handleDeleteField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index))
    setEditingFieldIndex(null)
  }

  const handleMoveField = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1
    if (newIndex < 0 || newIndex >= fields.length) return
    
    const newFields = [...fields]
    ;[newFields[index], newFields[newIndex]] = [newFields[newIndex], newFields[index]]
    setFields(newFields)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {isNew ? '新建字段模板' : `编辑: ${schema?.name}`}
        </h3>
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
            <button onClick={onDelete} className="px-4 py-2 text-sm text-error border border-error rounded-md hover:bg-error/10">
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
          <label className="text-sm font-medium">字段列表</label>
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
                  <span className="text-xs bg-muted px-2 py-0.5 rounded">{field.field_type}</span>
                  {field.required && <span className="text-xs text-error">必填</span>}
                  
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
                      className="p-1 hover:bg-error/10 text-error rounded"
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
                      <label className="block text-xs font-medium mb-1">AI提示</label>
                      <input
                        type="text"
                        value={field.ai_hint}
                        onChange={(e) => handleUpdateField(index, { ai_hint: e.target.value })}
                        className="w-full px-2 py-1.5 border rounded text-sm"
                        placeholder="生成时的特殊要求..."
                      />
                    </div>
                    <div className="flex items-center gap-2">
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
    </div>
  )
}



