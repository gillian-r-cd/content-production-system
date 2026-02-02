// web/src/components/common/EditableField.tsx
// 通用可编辑字段组件
// 功能：支持文本、列表、对象等类型的编辑

import { useState, useEffect, useRef } from 'react'
import { Edit3, Save, X, Plus, Trash2, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EditableFieldProps {
  value: any
  onChange: (value: any) => void
  label: string
  type?: 'text' | 'textarea' | 'list' | 'tags' | 'number' | 'select'
  options?: { value: string; label: string }[] // for select type
  placeholder?: string
  className?: string
  readOnly?: boolean
  autoSave?: boolean // 自动保存
}

/**
 * 可编辑文本字段
 */
export function EditableText({
  value,
  onChange,
  label,
  multiline = false,
  placeholder = '',
  className,
  readOnly = false,
  autoSave = false,
}: {
  value: string
  onChange: (v: string) => void
  label: string
  multiline?: boolean
  placeholder?: string
  className?: string
  readOnly?: boolean
  autoSave?: boolean
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [localValue, setLocalValue] = useState(value)
  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement>(null)

  useEffect(() => {
    setLocalValue(value)
  }, [value])

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isEditing])

  const handleSave = () => {
    onChange(localValue)
    setIsEditing(false)
  }

  const handleCancel = () => {
    setLocalValue(value)
    setIsEditing(false)
  }

  const handleBlur = () => {
    if (autoSave && localValue !== value) {
      onChange(localValue)
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel()
    } else if (e.key === 'Enter' && !multiline) {
      handleSave()
    } else if (e.key === 'Enter' && e.metaKey && multiline) {
      handleSave()
    }
  }

  if (readOnly) {
    return (
      <div className={cn("space-y-1", className)}>
        <label className="text-sm font-medium text-muted-foreground">{label}</label>
        <div className="p-3 bg-muted/30 rounded-lg">
          <p className="text-sm whitespace-pre-wrap">{value || <span className="text-muted-foreground italic">暂无内容</span>}</p>
        </div>
      </div>
    )
  }

  if (isEditing) {
    return (
      <div className={cn("space-y-2", className)}>
        <label className="text-sm font-medium text-muted-foreground">{label}</label>
        {multiline ? (
          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={autoSave ? handleBlur : undefined}
            className="w-full min-h-[120px] p-3 border rounded-lg text-sm resize-y focus:outline-none focus:ring-2 focus:ring-primary bg-background"
            placeholder={placeholder}
          />
        ) : (
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type="text"
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={autoSave ? handleBlur : undefined}
            className="w-full p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-background"
            placeholder={placeholder}
          />
        )}
        {!autoSave && (
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="px-3 py-1.5 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 flex items-center gap-1"
            >
              <Save className="w-3.5 h-3.5" />
              保存
            </button>
            <button
              onClick={handleCancel}
              className="px-3 py-1.5 bg-muted text-muted-foreground text-sm rounded-lg hover:bg-muted/80 flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" />
              取消
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cn("group", className)}>
      <label className="text-sm font-medium text-muted-foreground">{label}</label>
      <div
        className="mt-1 p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50 transition-colors relative min-h-[44px]"
        onClick={() => setIsEditing(true)}
      >
        <p className="text-sm whitespace-pre-wrap pr-6">
          {value || <span className="text-muted-foreground italic">{placeholder || '点击编辑...'}</span>}
        </p>
        <Edit3 className="w-4 h-4 absolute top-3 right-3 opacity-0 group-hover:opacity-100 text-muted-foreground transition-opacity" />
      </div>
    </div>
  )
}

/**
 * 可编辑列表字段
 */
export function EditableList({
  value = [],
  onChange,
  label,
  placeholder = '添加项目...',
  className,
  readOnly = false,
}: {
  value: string[]
  onChange: (v: string[]) => void
  label: string
  placeholder?: string
  className?: string
  readOnly?: boolean
}) {
  const [isExpanded, setIsExpanded] = useState(true)
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

  const handleEdit = (index: number, newValue: string) => {
    const updated = [...value]
    updated[index] = newValue
    onChange(updated)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          {label}
          <span className="text-xs bg-muted px-1.5 py-0.5 rounded ml-1">{value.length}</span>
        </button>
        {!readOnly && (
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-xs text-primary hover:underline"
          >
            {isEditing ? '完成' : '编辑'}
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="space-y-1.5">
          {value.length === 0 && !isEditing ? (
            <p className="text-sm text-muted-foreground italic p-2 bg-muted/30 rounded">暂无内容</p>
          ) : (
            value.map((item, index) => (
              <div key={index} className="flex items-start gap-2 p-2 bg-muted/30 rounded group">
                <span className="text-primary mt-0.5">•</span>
                {isEditing ? (
                  <input
                    type="text"
                    value={item}
                    onChange={(e) => handleEdit(index, e.target.value)}
                    className="flex-1 p-1 border rounded text-sm bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                ) : (
                  <span className="text-sm flex-1">{item}</span>
                )}
                {isEditing && (
                  <button
                    onClick={() => handleRemove(index)}
                    className="text-destructive hover:text-destructive/80 p-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))
          )}

          {isEditing && (
            <div className="flex gap-2 mt-2">
              <input
                type="text"
                value={newItem}
                onChange={(e) => setNewItem(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-background"
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
      )}
    </div>
  )
}

/**
 * 可编辑标签字段（紧凑列表）
 */
export function EditableTags({
  value = [],
  onChange,
  label,
  placeholder = '添加标签...',
  className,
  readOnly = false,
}: {
  value: string[]
  onChange: (v: string[]) => void
  label: string
  placeholder?: string
  className?: string
  readOnly?: boolean
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [newTag, setNewTag] = useState('')

  const handleAdd = () => {
    if (newTag.trim() && !value.includes(newTag.trim())) {
      onChange([...value, newTag.trim()])
      setNewTag('')
    }
  }

  const handleRemove = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-muted-foreground">{label}</label>
        {!readOnly && (
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-xs text-primary hover:underline"
          >
            {isEditing ? '完成' : '编辑'}
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-2 p-2 bg-muted/30 rounded-lg min-h-[44px]">
        {value.map((tag, index) => (
          <span
            key={index}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary text-sm rounded",
              isEditing && "pr-1"
            )}
          >
            {tag}
            {isEditing && (
              <button
                onClick={() => handleRemove(index)}
                className="text-primary/70 hover:text-primary ml-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </span>
        ))}
        {value.length === 0 && !isEditing && (
          <span className="text-sm text-muted-foreground italic">暂无标签</span>
        )}
        {isEditing && (
          <input
            type="text"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="flex-1 min-w-[120px] p-1 text-sm bg-transparent focus:outline-none"
          />
        )}
      </div>
    </div>
  )
}

/**
 * 通用可编辑字段
 */
export default function EditableField({
  value,
  onChange,
  label,
  type = 'text',
  options,
  placeholder = '',
  className,
  readOnly = false,
  autoSave = false,
}: EditableFieldProps) {
  switch (type) {
    case 'textarea':
      return (
        <EditableText
          value={value || ''}
          onChange={onChange}
          label={label}
          multiline
          placeholder={placeholder}
          className={className}
          readOnly={readOnly}
          autoSave={autoSave}
        />
      )

    case 'list':
      return (
        <EditableList
          value={value || []}
          onChange={onChange}
          label={label}
          placeholder={placeholder}
          className={className}
          readOnly={readOnly}
        />
      )

    case 'tags':
      return (
        <EditableTags
          value={value || []}
          onChange={onChange}
          label={label}
          placeholder={placeholder}
          className={className}
          readOnly={readOnly}
        />
      )

    case 'select':
      return (
        <div className={cn("space-y-1", className)}>
          <label className="text-sm font-medium text-muted-foreground">{label}</label>
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={readOnly}
            className="w-full p-2 border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      )

    case 'number':
      return (
        <div className={cn("space-y-1", className)}>
          <label className="text-sm font-medium text-muted-foreground">{label}</label>
          <input
            type="number"
            value={value || ''}
            onChange={(e) => onChange(Number(e.target.value))}
            disabled={readOnly}
            placeholder={placeholder}
            className="w-full p-2 border rounded-lg text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      )

    default:
      return (
        <EditableText
          value={value || ''}
          onChange={onChange}
          label={label}
          placeholder={placeholder}
          className={className}
          readOnly={readOnly}
          autoSave={autoSave}
        />
      )
  }
}


