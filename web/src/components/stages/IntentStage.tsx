// web/src/components/stages/IntentStage.tsx
// 意图分析阶段
// 功能：展示和编辑意图分析结果

import { useState, useEffect } from 'react'
import { Target, Plus, X, Pencil, Check, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'

export default function IntentStage() {
  const { workflowData, updateIntent, confirmIntent, isLoading, status } = useWorkflowStore()
  const intent = workflowData?.intent

  // 本地编辑状态
  const [editingField, setEditingField] = useState<string | null>(null)
  const [localGoal, setLocalGoal] = useState(intent?.goal || '')
  const [localCriteria, setLocalCriteria] = useState<string[]>(intent?.success_criteria || [])
  const [localMustHave, setLocalMustHave] = useState<string[]>(intent?.constraints?.must_have || [])
  const [localMustAvoid, setLocalMustAvoid] = useState<string[]>(intent?.constraints?.must_avoid || [])
  const [newItem, setNewItem] = useState('')

  // 同步远程数据到本地
  useEffect(() => {
    if (intent) {
      setLocalGoal(intent.goal || '')
      setLocalCriteria(intent.success_criteria || [])
      setLocalMustHave(intent.constraints?.must_have || [])
      setLocalMustAvoid(intent.constraints?.must_avoid || [])
    }
  }, [intent])

  // 如果还没有意图数据
  if (!intent) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <Target className="w-12 h-12 text-muted-foreground mb-4" />
        <h2 className="text-lg font-semibold mb-2">意图分析</h2>
        <p className="text-muted-foreground text-center max-w-md">
          {status?.waiting_for_input 
            ? '请在右侧对话框回答AI的问题，完成意图分析'
            : '正在等待AI分析你的内容需求...'}
        </p>
      </div>
    )
  }

  const handleSaveField = (field: string) => {
    updateIntent({
      goal: localGoal,
      success_criteria: localCriteria,
      constraints: {
        must_have: localMustHave,
        must_avoid: localMustAvoid,
      }
    })
    setEditingField(null)
  }

  const handleAddItem = (field: 'criteria' | 'mustHave' | 'mustAvoid') => {
    if (!newItem.trim()) return
    
    switch (field) {
      case 'criteria':
        setLocalCriteria([...localCriteria, newItem.trim()])
        break
      case 'mustHave':
        setLocalMustHave([...localMustHave, newItem.trim()])
        break
      case 'mustAvoid':
        setLocalMustAvoid([...localMustAvoid, newItem.trim()])
        break
    }
    setNewItem('')
  }

  const handleRemoveItem = (field: 'criteria' | 'mustHave' | 'mustAvoid', index: number) => {
    switch (field) {
      case 'criteria':
        setLocalCriteria(localCriteria.filter((_, i) => i !== index))
        break
      case 'mustHave':
        setLocalMustHave(localMustHave.filter((_, i) => i !== index))
        break
      case 'mustAvoid':
        setLocalMustAvoid(localMustAvoid.filter((_, i) => i !== index))
        break
    }
  }

  const handleConfirm = () => {
    // 先保存所有修改
    updateIntent({
      goal: localGoal,
      success_criteria: localCriteria,
      constraints: {
        must_have: localMustHave,
        must_avoid: localMustAvoid,
      }
    })
    // 确认并进入下一步
    confirmIntent()
  }

  return (
    <div className="h-full flex flex-col p-6 overflow-auto">
      {/* 标题区 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Target className="w-6 h-6 text-primary" />
            意图分析
          </h1>
          <p className="text-muted-foreground mt-1">
            AI已理解你的需求，请确认或修改以下内容
          </p>
        </div>
        <button className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
          <RotateCcw className="w-4 h-4" />
          重新分析
        </button>
      </div>

      {/* 目标 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="font-medium">目标</label>
          {editingField !== 'goal' && (
            <button 
              onClick={() => setEditingField('goal')}
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              <Pencil className="w-3 h-3" />
              编辑
            </button>
          )}
        </div>
        {editingField === 'goal' ? (
          <div className="space-y-2">
            <textarea
              value={localGoal}
              onChange={(e) => setLocalGoal(e.target.value)}
              className="w-full px-4 py-3 border rounded-lg resize-none"
              rows={3}
            />
            <div className="flex gap-2">
              <button
                onClick={() => handleSaveField('goal')}
                className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded"
              >
                保存
              </button>
              <button
                onClick={() => {
                  setLocalGoal(intent.goal || '')
                  setEditingField(null)
                }}
                className="px-3 py-1.5 text-sm border rounded"
              >
                取消
              </button>
            </div>
          </div>
        ) : (
          <div className="px-4 py-3 bg-muted/50 rounded-lg">
            {localGoal || '未设置'}
          </div>
        )}
      </div>

      {/* 成功标准 */}
      <div className="mb-6">
        <label className="font-medium block mb-2">成功标准</label>
        <div className="space-y-2">
          {localCriteria.map((item, index) => (
            <div key={index} className="flex items-center gap-2 px-4 py-2 bg-muted/50 rounded-lg group">
              <span className="text-primary">•</span>
              <span className="flex-1">{item}</span>
              <button
                onClick={() => handleRemoveItem('criteria', index)}
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-error transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
          <div className="flex gap-2">
            <input
              type="text"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddItem('criteria')}
              placeholder="添加成功标准..."
              className="flex-1 px-4 py-2 border rounded-lg text-sm"
            />
            <button
              onClick={() => handleAddItem('criteria')}
              className="px-3 py-2 border rounded-lg hover:bg-accent"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 约束条件 */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* 必须包含 */}
        <div>
          <label className="font-medium block mb-2 text-success">必须包含</label>
          <div className="space-y-2">
            {localMustHave.map((item, index) => (
              <div key={index} className="flex items-center gap-2 px-3 py-2 bg-success/10 rounded group text-sm">
                <span className="text-success">+</span>
                <span className="flex-1">{item}</span>
                <button
                  onClick={() => handleRemoveItem('mustHave', index)}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-error"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
            <input
              type="text"
              placeholder="添加..."
              className="w-full px-3 py-2 border rounded text-sm"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.currentTarget.value) {
                  setLocalMustHave([...localMustHave, e.currentTarget.value])
                  e.currentTarget.value = ''
                }
              }}
            />
          </div>
        </div>

        {/* 必须避免 */}
        <div>
          <label className="font-medium block mb-2 text-error">必须避免</label>
          <div className="space-y-2">
            {localMustAvoid.map((item, index) => (
              <div key={index} className="flex items-center gap-2 px-3 py-2 bg-error/10 rounded group text-sm">
                <span className="text-error">-</span>
                <span className="flex-1">{item}</span>
                <button
                  onClick={() => handleRemoveItem('mustAvoid', index)}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-error"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
            <input
              type="text"
              placeholder="添加..."
              className="w-full px-3 py-2 border rounded text-sm"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.currentTarget.value) {
                  setLocalMustAvoid([...localMustAvoid, e.currentTarget.value])
                  e.currentTarget.value = ''
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* 确认按钮 */}
      <div className="mt-auto pt-4 border-t">
        <button
          onClick={handleConfirm}
          disabled={isLoading || !localGoal}
          className="w-full py-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Check className="w-5 h-5" />
          确认意图，进入消费者调研
        </button>
      </div>
    </div>
  )
}
