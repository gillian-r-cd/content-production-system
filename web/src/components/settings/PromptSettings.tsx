// web/src/components/settings/PromptSettings.tsx
// 系统提示词管理
// 功能：查看和编辑各阶段的Prompt模板

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Save, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/api/client'

interface PromptTemplate {
  name: string
  content: string
}

const PROMPT_CATEGORIES = [
  { id: 'intent_analyzer', label: '意图分析' },
  { id: 'consumer_researcher', label: '消费者调研' },
  { id: 'content_core_producer', label: '内涵生产' },
  { id: 'content_extension_producer', label: '外延生产' },
  { id: 'simulator', label: '评估器' },
]

const AVAILABLE_VARIABLES = [
  '{creator_profile}',
  '{consumer_research}',
  '{intent}',
  '{field_name}',
  '{field_description}',
  '{field_ai_hint}',
  '{previous_fields}',
  '{iteration_feedback}',
  '{content}',
]

export default function PromptSettings() {
  const queryClient = useQueryClient()
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [isDirty, setIsDirty] = useState(false)

  // 获取所有Prompt
  const { data: prompts = [], isLoading } = useQuery({
    queryKey: ['prompts'],
    queryFn: async () => {
      const { data } = await apiClient.get('/settings/prompts')
      return data as PromptTemplate[]
    },
  })

  // 保存Prompt
  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPrompt) return
      await apiClient.put(`/settings/prompts/${selectedPrompt}`, {
        name: selectedPrompt,
        content: editContent,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      setIsDirty(false)
    },
  })

  const handleSelectPrompt = (name: string) => {
    if (isDirty && !confirm('有未保存的更改，确定要切换吗？')) {
      return
    }
    setSelectedPrompt(name)
    const prompt = prompts.find(p => p.name === name)
    setEditContent(prompt?.content || '')
    setIsDirty(false)
  }

  const handleContentChange = (value: string) => {
    setEditContent(value)
    setIsDirty(true)
  }

  const selectedPromptData = prompts.find(p => p.name === selectedPrompt)

  return (
    <div className="h-full flex">
      {/* 左侧分类 */}
      <div className="w-48 border-r p-4">
        <h3 className="font-semibold mb-4">提示词分类</h3>
        
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-1">
            {prompts.map((prompt) => {
              const category = PROMPT_CATEGORIES.find(c => c.id === prompt.name)
              return (
                <button
                  key={prompt.name}
                  onClick={() => handleSelectPrompt(prompt.name)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-md text-sm",
                    selectedPrompt === prompt.name
                      ? "bg-primary/10 text-primary"
                      : "hover:bg-accent"
                  )}
                >
                  {category?.label || prompt.name}
                </button>
              )
            })}
          </div>
        )}
      </div>
      
      {/* 右侧编辑区 */}
      <div className="flex-1 p-6 flex flex-col">
        {selectedPrompt ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {PROMPT_CATEGORIES.find(c => c.id === selectedPrompt)?.label || selectedPrompt}
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditContent(selectedPromptData?.content || '')
                    setIsDirty(false)
                  }}
                  className="px-3 py-2 text-sm border rounded-md hover:bg-accent flex items-center gap-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  重置
                </button>
                <button
                  onClick={() => saveMutation.mutate()}
                  disabled={saveMutation.isPending || !isDirty}
                  className="px-3 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  {saveMutation.isPending ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
            
            {/* 编辑器 */}
            <div className="flex-1 flex flex-col">
              <textarea
                value={editContent}
                onChange={(e) => handleContentChange(e.target.value)}
                className="flex-1 w-full p-4 border rounded-md font-mono text-sm resize-none"
                placeholder="输入提示词模板..."
              />
              
              {/* 可用变量 */}
              <div className="mt-4">
                <p className="text-sm font-medium text-muted-foreground mb-2">可用变量：</p>
                <div className="flex flex-wrap gap-2">
                  {AVAILABLE_VARIABLES.map((v) => (
                    <button
                      key={v}
                      onClick={() => {
                        // 在光标位置插入变量
                        setEditContent(editContent + v)
                        setIsDirty(true)
                      }}
                      className="px-2 py-1 text-xs bg-muted rounded hover:bg-accent font-mono"
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p>选择一个提示词模板进行编辑</p>
          </div>
        )}
      </div>
    </div>
  )
}



