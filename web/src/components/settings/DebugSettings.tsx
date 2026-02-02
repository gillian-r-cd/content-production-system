// web/src/components/settings/DebugSettings.tsx
// 调试日志面板
// 功能：查看每次AI调用的完整输入/输出

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Trash2, ChevronDown, ChevronRight, Clock, Cpu, Hash, AlertCircle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/api/client'

interface AICallLog {
  id: string
  project_id: string | null
  stage: string
  timestamp: string
  duration_ms: number
  system_prompt: string
  user_message: string
  full_prompt: string
  response: string
  model: string
  temperature: number
  tokens_input: number
  tokens_output: number
  success: boolean
  error: string | null
}

interface LogsSummary {
  total_calls: number
  successful_calls: number
  failed_calls: number
  total_tokens: number
  total_duration_ms: number
  avg_duration_ms: number
  stage_stats: Record<string, { count: number; tokens: number; duration_ms: number }>
}

const STAGE_LABELS: Record<string, string> = {
  intent: '意图分析',
  research: '消费者调研',
  core: '内涵生产',
  extension: '外延生产',
  simulator: '评估器',
  '': '未知',
}

export default function DebugSettings() {
  const queryClient = useQueryClient()
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [selectedSection, setSelectedSection] = useState<'system' | 'user' | 'response'>('response')

  // 获取日志列表
  const { data: logs = [], isLoading, refetch } = useQuery({
    queryKey: ['ai-logs'],
    queryFn: async () => {
      const { data } = await apiClient.get('/logs?limit=100')
      return data as AICallLog[]
    },
  })

  // 获取统计摘要
  const { data: summary } = useQuery({
    queryKey: ['ai-logs-summary'],
    queryFn: async () => {
      const { data } = await apiClient.get('/logs/summary')
      return data as LogsSummary
    },
  })

  // 清空日志
  const clearMutation = useMutation({
    mutationFn: async () => {
      await apiClient.delete('/logs')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-logs'] })
      queryClient.invalidateQueries({ queryKey: ['ai-logs-summary'] })
    },
  })

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const formatTimestamp = (ts: string) => {
    const date = new Date(ts)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold">调试日志</h3>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="px-3 py-1.5 text-sm border rounded-md hover:bg-accent flex items-center gap-1"
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            刷新
          </button>
          <button
            onClick={() => {
              if (confirm('确定要清空所有日志吗？')) {
                clearMutation.mutate()
              }
            }}
            className="px-3 py-1.5 text-sm border border-error text-error rounded-md hover:bg-error/10 flex items-center gap-1"
          >
            <Trash2 className="w-4 h-4" />
            清空
          </button>
        </div>
      </div>

      {/* 统计摘要 */}
      {summary && (
        <div className="p-4 bg-muted/30 border-b">
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{summary.total_calls}</p>
              <p className="text-xs text-muted-foreground">总调用次数</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-success">{summary.successful_calls}</p>
              <p className="text-xs text-muted-foreground">成功</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{summary.total_tokens.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">总Token</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{formatDuration(summary.avg_duration_ms)}</p>
              <p className="text-xs text-muted-foreground">平均耗时</p>
            </div>
          </div>
        </div>
      )}

      {/* 日志列表 */}
      <div className="flex-1 overflow-auto p-4 space-y-2">
        {logs.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Cpu className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>暂无AI调用记录</p>
            <p className="text-sm mt-1">开始一个工作流后，日志将显示在这里</p>
          </div>
        ) : (
          logs.map((log) => (
            <div 
              key={log.id} 
              className={cn(
                "border rounded-lg overflow-hidden",
                !log.success && "border-error/50 bg-error/5"
              )}
            >
              {/* 日志标题栏 */}
              <button
                onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                className="w-full flex items-center gap-3 p-3 hover:bg-accent/50 text-left"
              >
                {expandedId === log.id ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
                
                {/* 状态图标 */}
                {log.success ? (
                  <CheckCircle className="w-4 h-4 text-success" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-error" />
                )}
                
                {/* 阶段 */}
                <span className="font-medium min-w-[80px]">
                  {STAGE_LABELS[log.stage] || log.stage}
                </span>
                
                {/* 时间 */}
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTimestamp(log.timestamp)}
                </span>
                
                {/* 耗时 */}
                <span className="text-sm text-muted-foreground">
                  {formatDuration(log.duration_ms)}
                </span>
                
                {/* Token */}
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  {(log.tokens_input + log.tokens_output).toLocaleString()} tokens
                </span>
                
                {/* 模型 */}
                <span className="text-xs bg-muted px-2 py-0.5 rounded ml-auto">
                  {log.model}
                </span>
              </button>

              {/* 展开内容 */}
              {expandedId === log.id && (
                <div className="border-t">
                  {/* 标签页 */}
                  <div className="flex border-b">
                    <button
                      onClick={() => setSelectedSection('system')}
                      className={cn(
                        "px-4 py-2 text-sm",
                        selectedSection === 'system' 
                          ? "border-b-2 border-primary text-primary font-medium" 
                          : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      System Prompt
                    </button>
                    <button
                      onClick={() => setSelectedSection('user')}
                      className={cn(
                        "px-4 py-2 text-sm",
                        selectedSection === 'user' 
                          ? "border-b-2 border-primary text-primary font-medium" 
                          : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      User Message
                    </button>
                    <button
                      onClick={() => setSelectedSection('response')}
                      className={cn(
                        "px-4 py-2 text-sm",
                        selectedSection === 'response' 
                          ? "border-b-2 border-primary text-primary font-medium" 
                          : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      Response
                    </button>
                  </div>

                  {/* 内容区 */}
                  <div className="p-4 bg-muted/30 max-h-96 overflow-auto">
                    <pre className="text-sm whitespace-pre-wrap font-mono">
                      {selectedSection === 'system' && log.system_prompt}
                      {selectedSection === 'user' && log.user_message}
                      {selectedSection === 'response' && (log.error || log.response)}
                    </pre>
                  </div>

                  {/* 元信息 */}
                  <div className="p-3 bg-muted/20 border-t text-xs text-muted-foreground flex gap-4">
                    <span>输入: {log.tokens_input} tokens</span>
                    <span>输出: {log.tokens_output} tokens</span>
                    <span>温度: {log.temperature}</span>
                    {log.project_id && <span>项目: {log.project_id}</span>}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}



