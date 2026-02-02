// web/src/components/stages/ResearchStage.tsx
// 消费者调研阶段视图
// 功能：显示用户画像、痛点、期望，支持编辑，Persona选择加入Simulator

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, CheckCircle, AlertTriangle, Heart, Loader2, ArrowRight, Edit2, Save, X, UserCircle, Plus, CheckSquare, Square, Settings, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'
import { Persona } from '@/types'
import apiClient from '@/api/client'

interface Simulator {
  id: string
  name: string
  description: string
}

export default function ResearchStage() {
  const { workflowData, workflowId, status, respond, isLoading, updateResearch } = useWorkflowStore()
  const research = workflowData?.consumer_research
  
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    summary: '',
    pain_points: [] as string[],
    desires: [] as string[],
  })
  
  // Persona 选择状态
  const [selectedPersonas, setSelectedPersonas] = useState<Set<string>>(new Set())
  const [editingPersonaId, setEditingPersonaId] = useState<string | null>(null)
  const [personaEditData, setPersonaEditData] = useState<Persona | null>(null)
  
  // Persona 保存状态
  const [isSavingPersonas, setIsSavingPersonas] = useState(false)
  const [personasSaved, setPersonasSaved] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  
  // 从后端数据初始化已选择的 Personas
  useEffect(() => {
    if (research?.personas) {
      const initialSelected = new Set<string>()
      research.personas.forEach((p: Persona) => {
        if (p.selected) {
          initialSelected.add(p.id)
        }
      })
      setSelectedPersonas(initialSelected)
      setHasUnsavedChanges(false)
    }
  }, [research?.personas])
  
  // 获取 Simulator 列表
  const { data: simulators = [] } = useQuery({
    queryKey: ['simulators'],
    queryFn: async () => {
      const { data } = await apiClient.get('/simulators')
      return data as Simulator[]
    },
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

  // Persona 选择切换
  const togglePersonaSelection = (personaId: string) => {
    setSelectedPersonas(prev => {
      const newSet = new Set(prev)
      if (newSet.has(personaId)) {
        newSet.delete(personaId)
      } else {
        newSet.add(personaId)
      }
      return newSet
    })
    setHasUnsavedChanges(true)
    setPersonasSaved(false)
  }
  
  // 保存 Persona 选择到后端
  const savePersonasSelection = async () => {
    if (!workflowId) return
    
    setIsSavingPersonas(true)
    try {
      await apiClient.patch(`/workflow/${workflowId}/personas`, {
        selected_persona_ids: Array.from(selectedPersonas),
      })
      setPersonasSaved(true)
      setHasUnsavedChanges(false)
      // 3秒后隐藏保存成功提示
      setTimeout(() => setPersonasSaved(false), 3000)
    } catch (error) {
      console.error('保存 Personas 失败:', error)
    } finally {
      setIsSavingPersonas(false)
    }
  }
  
  // 开始编辑 Persona
  const startEditingPersona = (persona: Persona) => {
    setEditingPersonaId(persona.id)
    setPersonaEditData({ ...persona })
  }
  
  // 保存 Persona 编辑
  const savePersonaEdit = async () => {
    // TODO: 调用后端API保存 Persona 修改
    setEditingPersonaId(null)
    setPersonaEditData(null)
  }
  
  // 取消编辑 Persona
  const cancelPersonaEdit = () => {
    setEditingPersonaId(null)
    setPersonaEditData(null)
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
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <UserCircle className="w-4 h-4 text-primary" />
              <label className="text-sm font-medium">典型用户画像</label>
              <span className="text-xs text-muted-foreground">（可选择加入Simulator进行评估）</span>
            </div>
            <div className="flex items-center gap-2">
              {selectedPersonas.size > 0 && (
                <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                  已选择 {selectedPersonas.size} 个
                </span>
              )}
              {/* 保存状态提示 */}
              {personasSaved && (
                <span className="text-xs text-success flex items-center gap-1">
                  <Check className="w-3 h-3" />
                  已保存
                </span>
              )}
              {hasUnsavedChanges && !personasSaved && (
                <span className="text-xs text-warning">未保存</span>
              )}
              {/* 保存按钮 */}
              {selectedPersonas.size > 0 && (
                <button
                  onClick={savePersonasSelection}
                  disabled={isSavingPersonas || !hasUnsavedChanges}
                  className={cn(
                    "flex items-center gap-1 px-3 py-1 text-xs rounded-md transition-colors",
                    hasUnsavedChanges
                      ? "bg-primary text-primary-foreground hover:bg-primary/90"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {isSavingPersonas ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Save className="w-3 h-3" />
                  )}
                  保存选择
                </button>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {personas.map((persona: Persona) => {
              const isSelected = selectedPersonas.has(persona.id)
              const isEditingThis = editingPersonaId === persona.id
              
              if (isEditingThis && personaEditData) {
                // 编辑模式
                return (
                  <div key={persona.id} className="border border-primary rounded-lg p-4 bg-primary/5">
                    <div className="space-y-3">
                      <input
                        type="text"
                        value={personaEditData.name}
                        onChange={(e) => setPersonaEditData({ ...personaEditData, name: e.target.value })}
                        className="w-full px-2 py-1 border rounded text-sm font-medium"
                        placeholder="姓名"
                      />
                      <input
                        type="text"
                        value={personaEditData.role}
                        onChange={(e) => setPersonaEditData({ ...personaEditData, role: e.target.value })}
                        className="w-full px-2 py-1 border rounded text-xs"
                        placeholder="角色"
                      />
                      <textarea
                        value={personaEditData.background}
                        onChange={(e) => setPersonaEditData({ ...personaEditData, background: e.target.value })}
                        className="w-full px-2 py-1 border rounded text-sm resize-none"
                        rows={3}
                        placeholder="背景介绍"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={cancelPersonaEdit}
                          className="flex-1 px-2 py-1 text-xs border rounded hover:bg-accent"
                        >
                          取消
                        </button>
                        <button
                          onClick={savePersonaEdit}
                          className="flex-1 px-2 py-1 text-xs bg-primary text-primary-foreground rounded"
                        >
                          保存
                        </button>
                      </div>
                    </div>
                  </div>
                )
              }
              
              // 显示模式
              return (
                <div
                  key={persona.id}
                  className={cn(
                    "border rounded-lg p-4 transition-all relative group",
                    isSelected 
                      ? "border-primary bg-primary/5" 
                      : "hover:border-primary/50"
                  )}
                >
                  {/* 选择复选框 */}
                  <button
                    onClick={() => togglePersonaSelection(persona.id)}
                    className="absolute top-2 right-2 p-1 hover:bg-accent rounded"
                    title={isSelected ? "取消选择" : "选择加入Simulator"}
                  >
                    {isSelected ? (
                      <CheckSquare className="w-5 h-5 text-primary" />
                    ) : (
                      <Square className="w-5 h-5 text-muted-foreground" />
                    )}
                  </button>
                  
                  {/* 编辑按钮 */}
                  <button
                    onClick={() => startEditingPersona(persona)}
                    className="absolute top-2 right-10 p-1 hover:bg-accent rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    title="编辑"
                  >
                    <Edit2 className="w-4 h-4 text-muted-foreground" />
                  </button>
                  
                  <div className="flex items-center gap-2 mb-2 pr-16">
                    <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <UserCircle className="w-6 h-6 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium truncate">{persona.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{persona.role}</p>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2 line-clamp-3">{persona.background}</p>
                  {persona.pain_points?.length > 0 && (
                    <div className="text-xs">
                      <span className="text-warning font-medium">痛点：</span>
                      <span className="text-muted-foreground">{persona.pain_points.slice(0, 2).join('、')}</span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
          
          {/* Simulator 选择区域 */}
          {selectedPersonas.size > 0 && (
            <div className="mt-4 p-4 border rounded-lg bg-muted/30">
              <div className="flex items-center gap-2 mb-3">
                <Settings className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium">选择评估器进行评估</span>
              </div>
              {simulators.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {simulators.map((sim) => (
                    <button
                      key={sim.id}
                      className="px-3 py-1.5 text-sm border rounded-md hover:bg-primary hover:text-primary-foreground hover:border-primary transition-colors"
                      onClick={() => {
                        // TODO: 触发 Simulator 评估
                        alert(`将使用 "${sim.name}" 评估 ${selectedPersonas.size} 个 Persona`)
                      }}
                    >
                      {sim.name}
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  暂无评估器，请先在设置中创建评估器
                </p>
              )}
            </div>
          )}
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
