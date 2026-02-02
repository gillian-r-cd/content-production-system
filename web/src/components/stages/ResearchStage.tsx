// web/src/components/stages/ResearchStage.tsx
// 消费者调研阶段视图
// 功能：显示用户画像、痛点、期望，支持编辑，用户确认后进入下一阶段

import { useState } from 'react'
import { Users, CheckCircle, AlertTriangle, Heart, Loader2, ArrowRight, Edit2, Save, X, UserCircle, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'

interface Persona {
  id: string
  name: string
  role: string
  background: string
  pain_points: string[]
  desires: string[]
  selected?: boolean
}

export default function ResearchStage() {
  const { workflowData, status, respond, isLoading, updateResearch } = useWorkflowStore()
  const research = workflowData?.consumer_research
  
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    summary: '',
    pain_points: [] as string[],
    desires: [] as string[],
  })

  // 初始化编辑数据
  const startEditing = () => {
    setEditData({
      summary: research?.summary || '',
      pain_points: research?.key_pain_points || research?.pain_points || [],
      desires: research?.key_desires || research?.needs || research?.expectations || [],
    })
    setIsEditing(true)
  }

  const saveEdit = async () => {
    if (updateResearch) {
      await updateResearch({
        summary: editData.summary,
        key_pain_points: editData.pain_points,
        key_desires: editData.desires,
      })
    }
    setIsEditing(false)
  }

  const cancelEdit = () => {
    setIsEditing(false)
  }

  // 确认调研结果，进入下一阶段
  const handleConfirm = async () => {
    await respond('确认')
  }

  // 添加痛点/期望
  const addItem = (type: 'pain_points' | 'desires') => {
    setEditData(prev => ({
      ...prev,
      [type]: [...prev[type], ''],
    }))
  }

  // 更新痛点/期望
  const updateItem = (type: 'pain_points' | 'desires', index: number, value: string) => {
    setEditData(prev => ({
      ...prev,
      [type]: prev[type].map((item, i) => i === index ? value : item),
    }))
  }

  // 删除痛点/期望
  const removeItem = (type: 'pain_points' | 'desires', index: number) => {
    setEditData(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index),
    }))
  }

  // 检查是否在研究阶段（无论是否等待输入都显示确认按钮）
  const isResearchStage = status?.current_stage === 'research'
  const hasResearchData = !!research

  if (!research) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mb-4" />
        <h2 className="text-lg font-semibold mb-2">消费者调研</h2>
        <p className="text-muted-foreground">正在分析目标用户画像...</p>
        <p className="text-sm text-muted-foreground mt-2">AI正在根据意图分析结果生成用户画像</p>
      </div>
    )
  }

  const painPoints = research.key_pain_points || research.pain_points || []
  const desires = research.key_desires || research.needs || research.expectations || []
  const targetUsers = research.target_users || []
  const personas = research.personas || []

  return (
    <div className="h-full flex flex-col p-6 overflow-auto">
      {/* 标题区 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Users className="w-6 h-6 text-primary" />
          <h1 className="text-xl font-bold">消费者调研</h1>
        </div>
        <div className="flex items-center gap-2">
          {!isEditing ? (
            <button
              onClick={startEditing}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
            >
              <Edit2 className="w-4 h-4" />
              编辑
            </button>
          ) : (
            <>
              <button
                onClick={cancelEdit}
                className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-md hover:bg-accent"
              >
                <X className="w-4 h-4" />
                取消
              </button>
              <button
                onClick={saveEdit}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                <Save className="w-4 h-4" />
                保存
              </button>
            </>
          )}
        </div>
      </div>

      {/* 用户画像摘要 */}
      <div className="mb-6">
        <label className="text-sm font-medium text-muted-foreground mb-2 block">
          目标用户画像
        </label>
        {isEditing ? (
          <textarea
            value={editData.summary}
            onChange={(e) => setEditData(prev => ({ ...prev, summary: e.target.value }))}
            className="w-full bg-muted/50 border rounded-lg p-4 text-foreground resize-none"
            rows={3}
            placeholder="描述目标用户的特征..."
          />
        ) : (
          <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
            <p className="text-foreground">{research.summary || '暂无摘要'}</p>
          </div>
        )}
      </div>

      {/* 痛点和期望 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
        {/* 核心痛点 */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" />
              <label className="text-sm font-medium">核心痛点</label>
            </div>
            {isEditing && (
              <button
                onClick={() => addItem('pain_points')}
                className="flex items-center gap-1 text-xs text-primary hover:underline"
              >
                <Plus className="w-3 h-3" />
                添加
              </button>
            )}
          </div>
          <div className="space-y-2">
            {isEditing ? (
              editData.pain_points.map((point, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={point}
                    onChange={(e) => updateItem('pain_points', index, e.target.value)}
                    className="flex-1 bg-warning/10 border border-warning/20 rounded-lg px-3 py-2 text-sm"
                    placeholder="输入痛点..."
                  />
                  <button
                    onClick={() => removeItem('pain_points', index)}
                    className="p-2 text-muted-foreground hover:text-destructive"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              painPoints.length > 0 ? (
                painPoints.map((point: string, index: number) => (
                  <div 
                    key={index}
                    className="bg-warning/10 border border-warning/20 rounded-lg p-3"
                  >
                    <p className="text-sm">{point}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">暂无痛点数据</p>
              )
            )}
          </div>
        </div>

        {/* 核心期望 */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Heart className="w-4 h-4 text-success" />
              <label className="text-sm font-medium">核心期望</label>
            </div>
            {isEditing && (
              <button
                onClick={() => addItem('desires')}
                className="flex items-center gap-1 text-xs text-primary hover:underline"
              >
                <Plus className="w-3 h-3" />
                添加
              </button>
            )}
          </div>
          <div className="space-y-2">
            {isEditing ? (
              editData.desires.map((desire, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={desire}
                    onChange={(e) => updateItem('desires', index, e.target.value)}
                    className="flex-1 bg-success/10 border border-success/20 rounded-lg px-3 py-2 text-sm"
                    placeholder="输入期望..."
                  />
                  <button
                    onClick={() => removeItem('desires', index)}
                    className="p-2 text-muted-foreground hover:text-destructive"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              desires.length > 0 ? (
                desires.map((desire: string, index: number) => (
                  <div 
                    key={index}
                    className="bg-success/10 border border-success/20 rounded-lg p-3"
                  >
                    <p className="text-sm">{desire}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">暂无期望数据</p>
              )
            )}
          </div>
        </div>
      </div>

      {/* 典型用户画像(Personas) - 如果有的话 */}
      {personas.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-3">
            <UserCircle className="w-4 h-4 text-primary" />
            <label className="text-sm font-medium">典型用户画像</label>
            <span className="text-xs text-muted-foreground">（可选择加入Simulator进行评估）</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {personas.map((persona: Persona) => (
              <div
                key={persona.id}
                className={cn(
                  "border rounded-lg p-4 cursor-pointer transition-all",
                  persona.selected 
                    ? "border-primary bg-primary/5" 
                    : "hover:border-primary/50"
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                    <UserCircle className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{persona.name}</p>
                    <p className="text-xs text-muted-foreground">{persona.role}</p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-2">{persona.background}</p>
                {persona.pain_points?.length > 0 && (
                  <div className="text-xs">
                    <span className="text-warning">痛点：</span>
                    {persona.pain_points.slice(0, 2).join('、')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 目标用户群体标签 */}
      {targetUsers.length > 0 && (
        <div className="mt-6">
          <label className="text-sm font-medium mb-2 block">目标用户群体</label>
          <div className="flex flex-wrap gap-2">
            {targetUsers.map((user: string, index: number) => (
              <span 
                key={index}
                className="px-3 py-1 bg-muted rounded-full text-sm"
              >
                {user}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 确认按钮 - 只要在research阶段且有数据就显示 */}
      {isResearchStage && hasResearchData && !isEditing && (
        <div className="mt-6 pt-4 border-t">
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="w-full py-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                处理中...
              </>
            ) : (
              <>
                确认调研结果，进入内涵设计
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      )}

      {/* 非research阶段显示已确认状态 */}
      {!isResearchStage && hasResearchData && (
        <div className="mt-6 pt-4 border-t">
          <div className="flex items-center gap-2 text-success">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">调研结果已确认</span>
          </div>
        </div>
      )}
    </div>
  )
}
