// web/src/components/settings/SimulatorSettings.tsx
// 评估器配置管理
// 功能：Simulator的CRUD + 迭代条件配置

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, ChevronRight, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/api/client'

interface Simulator {
  id: string
  name: string
  description: string
  prompt_template: string
  auto_iterate: boolean
  trigger_score: number
  stop_score: number
  max_iterations: number
  created_at: string
  updated_at: string
}

export default function SimulatorSettings() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  
  // 获取列表
  const { data: simulators = [], isLoading } = useQuery({
    queryKey: ['simulators'],
    queryFn: async () => {
      const { data } = await apiClient.get('/simulators')
      return data as Simulator[]
    },
  })
  
  // 删除
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/simulators/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulators'] })
      setSelectedId(null)
    },
  })

  const selectedSimulator = simulators.find(s => s.id === selectedId)

  const handleDelete = (id: string) => {
    if (confirm('确定要删除这个评估器吗？')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="h-full flex">
      {/* 左侧列表 */}
      <div className="w-64 border-r p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">评估器配置</h3>
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
        ) : simulators.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            还没有评估器配置
          </p>
        ) : (
          <div className="space-y-1">
            {simulators.map((sim) => (
              <button
                key={sim.id}
                onClick={() => {
                  setSelectedId(sim.id)
                  setIsCreating(false)
                }}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 rounded-md text-left",
                  selectedId === sim.id 
                    ? "bg-primary/10 text-primary" 
                    : "hover:bg-accent"
                )}
              >
                <span className="text-sm truncate">{sim.name}</span>
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* 右侧编辑区 */}
      <div className="flex-1 p-6 overflow-auto">
        {isCreating ? (
          <SimulatorEditor
            key="new-simulator"
            onSave={() => {
              setIsCreating(false)
              queryClient.invalidateQueries({ queryKey: ['simulators'] })
            }}
            onCancel={() => setIsCreating(false)}
          />
        ) : selectedSimulator ? (
          <SimulatorEditor
            key={selectedSimulator.id}
            simulator={selectedSimulator}
            onSave={() => {
              queryClient.invalidateQueries({ queryKey: ['simulators'] })
            }}
            onDelete={() => handleDelete(selectedSimulator.id)}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p>选择一个评估器或点击 + 新建</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Simulator编辑器
interface SimulatorEditorProps {
  simulator?: Simulator
  onSave: () => void
  onCancel?: () => void
  onDelete?: () => void
}

function SimulatorEditor({ simulator, onSave, onCancel, onDelete }: SimulatorEditorProps) {
  const isNew = !simulator
  
  const [name, setName] = useState(simulator?.name || '')
  const [description, setDescription] = useState(simulator?.description || '')
  const [promptTemplate, setPromptTemplate] = useState(simulator?.prompt_template || DEFAULT_PROMPT)
  const [autoIterate, setAutoIterate] = useState(simulator?.auto_iterate ?? true)
  const [triggerScore, setTriggerScore] = useState(simulator?.trigger_score ?? 6)
  const [stopScore, setStopScore] = useState(simulator?.stop_score ?? 8)
  const [maxIterations, setMaxIterations] = useState(simulator?.max_iterations ?? 3)

  // 保存
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data = {
        name,
        description,
        prompt_template: promptTemplate,
        auto_iterate: autoIterate,
        trigger_score: triggerScore,
        stop_score: stopScore,
        max_iterations: maxIterations,
      }
      if (isNew) {
        return apiClient.post('/simulators', data)
      } else {
        return apiClient.put(`/simulators/${simulator!.id}`, data)
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
          {isNew ? '新建评估器' : `编辑: ${simulator?.name}`}
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
          <label className="block text-sm font-medium mb-2">评估器名称</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="例如：目标读者视角"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">描述</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="评估器的用途说明"
          />
        </div>
      </div>

      {/* 评估提示词 */}
      <div>
        <label className="block text-sm font-medium mb-2">评估提示词</label>
        <textarea
          value={promptTemplate}
          onChange={(e) => setPromptTemplate(e.target.value)}
          className="w-full px-3 py-2 border rounded-md font-mono text-sm"
          rows={10}
          placeholder="输入评估时使用的提示词..."
        />
        <p className="text-xs text-muted-foreground mt-1">
          可用变量: {'{consumer_research}'}, {'{content}'}, {'{creator_profile}'}
        </p>
      </div>

      {/* 自动迭代配置 */}
      <div className="border rounded-md p-4">
        <div className="flex items-center gap-2 mb-4">
          <input
            type="checkbox"
            id="auto-iterate"
            checked={autoIterate}
            onChange={(e) => setAutoIterate(e.target.checked)}
          />
          <label htmlFor="auto-iterate" className="font-medium">启用自动迭代</label>
        </div>

        {autoIterate && (
          <div className="grid grid-cols-3 gap-4 pl-6">
            <div>
              <label className="block text-sm font-medium mb-2">触发分数（低于此分触发）</label>
              <input
                type="number"
                value={triggerScore}
                onChange={(e) => setTriggerScore(parseFloat(e.target.value))}
                className="w-full px-3 py-2 border rounded-md"
                min={1}
                max={10}
                step={0.5}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">停止分数（高于此分停止）</label>
              <input
                type="number"
                value={stopScore}
                onChange={(e) => setStopScore(parseFloat(e.target.value))}
                className="w-full px-3 py-2 border rounded-md"
                min={1}
                max={10}
                step={0.5}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">最大迭代次数</label>
              <input
                type="number"
                value={maxIterations}
                onChange={(e) => setMaxIterations(parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded-md"
                min={1}
                max={10}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const DEFAULT_PROMPT = `你是我的目标读者：
{consumer_research}

读完以下内容后回答：
1. 读完后你想采取什么行动？
2. 哪里让你觉得"这不对"或"不适合我"？
3. 整体打分（1-10），一句话说为什么。

【内容】
{content}`



