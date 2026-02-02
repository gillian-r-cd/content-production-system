// web/src/components/settings/ProfileSettings.tsx
// 创作者特质管理
// 功能：Profile列表、新建、编辑、删除

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, ChevronRight, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { profilesApi } from '@/api'
import type { Profile, ProfileCreate } from '@/types'

export default function ProfileSettings() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  
  // 获取列表
  const { data: profilesData, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: profilesApi.list,
  })
  const profiles = Array.isArray(profilesData) ? profilesData : []
  
  // 删除
  const deleteMutation = useMutation({
    mutationFn: profilesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      setSelectedId(null)
    },
  })

  const selectedProfile = profiles.find(p => p.id === selectedId)

  const handleDelete = (id: string) => {
    if (confirm('确定要删除这个创作者特质吗？')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="h-full flex">
      {/* 左侧列表 */}
      <div className="w-64 border-r p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">创作者特质</h3>
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
        ) : profiles.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            还没有创作者特质
          </p>
        ) : (
          <div className="space-y-1">
            {profiles.map((profile) => (
              <button
                key={profile.id}
                onClick={() => {
                  setSelectedId(profile.id)
                  setIsCreating(false)
                }}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 rounded-md text-left",
                  selectedId === profile.id 
                    ? "bg-primary/10 text-primary" 
                    : "hover:bg-accent"
                )}
              >
                <span className="text-sm truncate">{profile.name}</span>
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* 右侧编辑区 */}
      <div className="flex-1 p-6 overflow-auto">
        {isCreating ? (
          <ProfileEditor
            key="new-profile"
            onSave={() => {
              setIsCreating(false)
              queryClient.invalidateQueries({ queryKey: ['profiles'] })
            }}
            onCancel={() => setIsCreating(false)}
          />
        ) : selectedProfile ? (
          <ProfileEditor
            key={selectedProfile.id}
            profile={selectedProfile}
            onSave={() => {
              queryClient.invalidateQueries({ queryKey: ['profiles'] })
            }}
            onDelete={() => handleDelete(selectedProfile.id)}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p>选择一个创作者特质或点击 + 新建</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Profile编辑器
interface ProfileEditorProps {
  profile?: Profile
  onSave: () => void
  onCancel?: () => void
  onDelete?: () => void
}

function ProfileEditor({ profile, onSave, onCancel, onDelete }: ProfileEditorProps) {
  const queryClient = useQueryClient()
  const isNew = !profile
  
  const [name, setName] = useState(profile?.name || '')
  const [forbiddenWords, setForbiddenWords] = useState<string[]>(
    profile?.taboos?.forbidden_words || []
  )
  const [forbiddenTopics, setForbiddenTopics] = useState<string[]>(
    profile?.taboos?.forbidden_topics || []
  )
  const [exampleTexts, setExampleTexts] = useState<string[]>(
    profile?.example_texts || []
  )
  const [customFields, setCustomFields] = useState<Record<string, string>>(
    profile?.custom_fields || {}
  )
  
  const [newWord, setNewWord] = useState('')
  const [newTopic, setNewTopic] = useState('')
  const [newExample, setNewExample] = useState('')
  const [newFieldKey, setNewFieldKey] = useState('')
  const [newFieldValue, setNewFieldValue] = useState('')

  // 创建/更新
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data: ProfileCreate = {
        name,
        taboos: {
          forbidden_words: forbiddenWords,
          forbidden_topics: forbiddenTopics,
        },
        example_texts: exampleTexts,
        custom_fields: customFields,
      }
      if (isNew) {
        return profilesApi.create(data)
      } else {
        return profilesApi.update(profile!.id, data)
      }
    },
    onSuccess: () => {
      onSave()
    },
  })

  const handleAddWord = () => {
    if (newWord.trim()) {
      setForbiddenWords([...forbiddenWords, newWord.trim()])
      setNewWord('')
    }
  }

  const handleAddTopic = () => {
    if (newTopic.trim()) {
      setForbiddenTopics([...forbiddenTopics, newTopic.trim()])
      setNewTopic('')
    }
  }

  const handleAddExample = () => {
    if (newExample.trim()) {
      setExampleTexts([...exampleTexts, newExample.trim()])
      setNewExample('')
    }
  }

  const handleAddField = () => {
    if (newFieldKey.trim() && newFieldValue.trim()) {
      setCustomFields({ ...customFields, [newFieldKey.trim()]: newFieldValue.trim() })
      setNewFieldKey('')
      setNewFieldValue('')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {isNew ? '新建创作者特质' : `编辑: ${profile?.name}`}
        </h3>
        <div className="flex gap-2">
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm border rounded-md hover:bg-accent"
            >
              取消
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="px-4 py-2 text-sm text-error border border-error rounded-md hover:bg-error/10"
            >
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

      {/* 名称 */}
      <div>
        <label className="block text-sm font-medium mb-2">名称</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 border rounded-md"
          placeholder="例如：老王的风格"
        />
      </div>

      {/* 禁忌词汇 */}
      <div>
        <label className="block text-sm font-medium mb-2">禁忌词汇</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {forbiddenWords.map((word, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-1 bg-error/10 text-error text-sm rounded"
            >
              {word}
              <button
                onClick={() => setForbiddenWords(forbiddenWords.filter((_, j) => j !== i))}
                className="hover:text-error/70"
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddWord()}
            className="flex-1 px-3 py-2 border rounded-md text-sm"
            placeholder="输入禁忌词，回车添加"
          />
          <button
            onClick={handleAddWord}
            className="px-3 py-2 text-sm border rounded-md hover:bg-accent"
          >
            添加
          </button>
        </div>
      </div>

      {/* 禁碰话题 */}
      <div>
        <label className="block text-sm font-medium mb-2">禁碰话题</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {forbiddenTopics.map((topic, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-1 bg-warning/10 text-warning text-sm rounded"
            >
              {topic}
              <button
                onClick={() => setForbiddenTopics(forbiddenTopics.filter((_, j) => j !== i))}
                className="hover:text-warning/70"
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddTopic()}
            className="flex-1 px-3 py-2 border rounded-md text-sm"
            placeholder="输入话题，回车添加"
          />
          <button
            onClick={handleAddTopic}
            className="px-3 py-2 text-sm border rounded-md hover:bg-accent"
          >
            添加
          </button>
        </div>
      </div>

      {/* 范例文本 */}
      <div>
        <label className="block text-sm font-medium mb-2">范例文本（用于风格模仿）</label>
        <div className="space-y-2 mb-2">
          {exampleTexts.map((text, i) => (
            <div key={i} className="flex items-start gap-2 p-3 bg-muted rounded-md">
              <p className="flex-1 text-sm whitespace-pre-wrap">{text}</p>
              <button
                onClick={() => setExampleTexts(exampleTexts.filter((_, j) => j !== i))}
                className="text-muted-foreground hover:text-error"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        <textarea
          value={newExample}
          onChange={(e) => setNewExample(e.target.value)}
          className="w-full px-3 py-2 border rounded-md text-sm"
          rows={3}
          placeholder="粘贴一段你的风格范例..."
        />
        <button
          onClick={handleAddExample}
          disabled={!newExample.trim()}
          className="mt-2 px-3 py-2 text-sm border rounded-md hover:bg-accent disabled:opacity-50"
        >
          添加范例
        </button>
      </div>

      {/* 自定义字段 */}
      <div>
        <label className="block text-sm font-medium mb-2">自定义字段</label>
        <div className="space-y-2 mb-2">
          {Object.entries(customFields).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2 p-2 bg-muted rounded-md">
              <span className="font-medium text-sm">{key}:</span>
              <span className="flex-1 text-sm">{value}</span>
              <button
                onClick={() => {
                  const newFields = { ...customFields }
                  delete newFields[key]
                  setCustomFields(newFields)
                }}
                className="text-muted-foreground hover:text-error"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newFieldKey}
            onChange={(e) => setNewFieldKey(e.target.value)}
            className="w-32 px-3 py-2 border rounded-md text-sm"
            placeholder="字段名"
          />
          <input
            type="text"
            value={newFieldValue}
            onChange={(e) => setNewFieldValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddField()}
            className="flex-1 px-3 py-2 border rounded-md text-sm"
            placeholder="字段值"
          />
          <button
            onClick={handleAddField}
            disabled={!newFieldKey.trim() || !newFieldValue.trim()}
            className="px-3 py-2 text-sm border rounded-md hover:bg-accent disabled:opacity-50"
          >
            添加
          </button>
        </div>
      </div>
    </div>
  )
}

