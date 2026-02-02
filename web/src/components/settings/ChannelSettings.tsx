// web/src/components/settings/ChannelSettings.tsx
// 渠道管理
// 功能：Channel配置的CRUD

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, ChevronRight, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/api/client'

interface FormatConstraints {
  title_max_length: number | null
  body_min_length: number | null
  body_max_length: number | null
  special_requirements: string
}

interface Channel {
  id: string
  name: string
  description: string
  format_constraints: FormatConstraints
  prompt_template: string
  created_at: string
  updated_at: string
}

export default function ChannelSettings() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  
  // 获取列表
  const { data: channels = [], isLoading } = useQuery({
    queryKey: ['channels'],
    queryFn: async () => {
      const { data } = await apiClient.get('/channels')
      return data as Channel[]
    },
  })
  
  // 删除
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/channels/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      setSelectedId(null)
    },
  })

  const selectedChannel = channels.find(c => c.id === selectedId)

  const handleDelete = (id: string) => {
    if (confirm('确定要删除这个渠道吗？')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="h-full flex">
      {/* 左侧列表 */}
      <div className="w-64 border-r p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">渠道管理</h3>
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
        ) : channels.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            还没有渠道配置
          </p>
        ) : (
          <div className="space-y-1">
            {channels.map((channel) => (
              <button
                key={channel.id}
                onClick={() => {
                  setSelectedId(channel.id)
                  setIsCreating(false)
                }}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 rounded-md text-left",
                  selectedId === channel.id 
                    ? "bg-primary/10 text-primary" 
                    : "hover:bg-accent"
                )}
              >
                <span className="text-sm truncate">{channel.name}</span>
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* 右侧编辑区 */}
      <div className="flex-1 p-6 overflow-auto">
        {isCreating ? (
          <ChannelEditor
            key="new-channel"
            onSave={() => {
              setIsCreating(false)
              queryClient.invalidateQueries({ queryKey: ['channels'] })
            }}
            onCancel={() => setIsCreating(false)}
          />
        ) : selectedChannel ? (
          <ChannelEditor
            key={selectedChannel.id}
            channel={selectedChannel}
            onSave={() => {
              queryClient.invalidateQueries({ queryKey: ['channels'] })
            }}
            onDelete={() => handleDelete(selectedChannel.id)}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p>选择一个渠道或点击 + 新建</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Channel编辑器
interface ChannelEditorProps {
  channel?: Channel
  onSave: () => void
  onCancel?: () => void
  onDelete?: () => void
}

function ChannelEditor({ channel, onSave, onCancel, onDelete }: ChannelEditorProps) {
  const isNew = !channel
  
  const [name, setName] = useState(channel?.name || '')
  const [description, setDescription] = useState(channel?.description || '')
  const [promptTemplate, setPromptTemplate] = useState(channel?.prompt_template || DEFAULT_PROMPT)
  const [titleMaxLength, setTitleMaxLength] = useState<number | ''>(channel?.format_constraints?.title_max_length || '')
  const [bodyMinLength, setBodyMinLength] = useState<number | ''>(channel?.format_constraints?.body_min_length || '')
  const [bodyMaxLength, setBodyMaxLength] = useState<number | ''>(channel?.format_constraints?.body_max_length || '')
  const [specialRequirements, setSpecialRequirements] = useState(channel?.format_constraints?.special_requirements || '')

  // 保存
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data = {
        name,
        description,
        prompt_template: promptTemplate,
        format_constraints: {
          title_max_length: titleMaxLength || null,
          body_min_length: bodyMinLength || null,
          body_max_length: bodyMaxLength || null,
          special_requirements: specialRequirements,
        },
      }
      if (isNew) {
        return apiClient.post('/channels', data)
      } else {
        return apiClient.put(`/channels/${channel!.id}`, data)
      }
    },
    onSuccess: () => {
      onSave()
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {isNew ? '新建渠道' : `编辑: ${channel?.name}`}
        </h3>
        <div className="flex gap-2">
          {onCancel && (
            <button onClick={onCancel} className="px-4 py-2 text-sm border rounded-md hover:bg-accent">
              取消
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
          <label className="block text-sm font-medium mb-2">渠道名称</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="例如：小红书"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">描述</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="生成适合小红书平台的短图文内容"
          />
        </div>
      </div>

      {/* 格式约束 */}
      <div className="border rounded-md p-4">
        <h4 className="font-medium mb-4">格式约束</h4>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">标题字数上限</label>
            <input
              type="number"
              value={titleMaxLength}
              onChange={(e) => setTitleMaxLength(e.target.value ? parseInt(e.target.value) : '')}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="例如: 20"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">正文最少字数</label>
            <input
              type="number"
              value={bodyMinLength}
              onChange={(e) => setBodyMinLength(e.target.value ? parseInt(e.target.value) : '')}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="例如: 500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">正文最多字数</label>
            <input
              type="number"
              value={bodyMaxLength}
              onChange={(e) => setBodyMaxLength(e.target.value ? parseInt(e.target.value) : '')}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="例如: 1000"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium mb-2">其他要求</label>
          <input
            type="text"
            value={specialRequirements}
            onChange={(e) => setSpecialRequirements(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="例如：标题用emoji开头，结尾必须有互动引导"
          />
        </div>
      </div>

      {/* 生成提示词 */}
      <div>
        <label className="block text-sm font-medium mb-2">生成提示词</label>
        <textarea
          value={promptTemplate}
          onChange={(e) => setPromptTemplate(e.target.value)}
          className="w-full px-3 py-2 border rounded-md font-mono text-sm"
          rows={8}
          placeholder="输入生成该渠道内容时使用的提示词..."
        />
        <p className="text-xs text-muted-foreground mt-1">
          可用变量: {'{content_core_summary}'}, {'{value_points}'}, {'{format_constraints}'}
        </p>
      </div>
    </div>
  )
}

const DEFAULT_PROMPT = `基于以下核心内容，生成适合该渠道的宣传文案：

【核心内容摘要】
{content_core_summary}

【核心价值点】
{value_points}

【格式要求】
{format_constraints}

请生成符合以上要求的内容。`



