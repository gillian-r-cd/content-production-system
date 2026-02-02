// web/src/components/layout/ChatPanel.tsx
// 右侧对话区 - 全局Agent入口
// 功能：AI对话、@引用机制、再来一回、内容修改同步

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Send, Loader2, RotateCcw, Pencil, X, AtSign, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflowStore'
import type { ChatMessage, Stage } from '@/types'

// 可引用的上下文定义
interface MentionOption {
  id: string
  label: string
  category: 'stage' | 'field'
  icon?: string
  available: boolean
  description?: string
}

interface MessageBubbleProps {
  message: ChatMessage
  isLast: boolean
  onRetry?: (newContent: string) => void
}

function MessageBubble({ message, isLast, onRetry }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(message.content)
  const [copied, setCopied] = useState(false)
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('复制失败:', err)
    }
  }
  
  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    )
  }

  const handleRetry = () => {
    if (onRetry && editContent.trim()) {
      onRetry(editContent.trim())
      setIsEditing(false)
    }
  }
  
  return (
    <div className={cn(
      "flex mb-4 group",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className="flex flex-col max-w-[85%]">
        {isEditing ? (
          // 编辑模式
          <div className="space-y-2">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm resize-none"
              rows={3}
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setEditContent(message.content)
                  setIsEditing(false)
                }}
                className="px-2 py-1 text-xs border rounded hover:bg-accent flex items-center gap-1"
              >
                <X className="w-3 h-3" /> 取消
              </button>
              <button
                onClick={handleRetry}
                className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" /> 重新发送
              </button>
            </div>
          </div>
        ) : (
          // 显示模式
          <div className={cn(
            "rounded-lg px-4 py-2",
            isUser 
              ? "bg-primary text-primary-foreground" 
              : "bg-muted text-foreground"
          )}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            <span className="text-xs opacity-70 mt-1 block">
              {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        )}
        
        {/* 消息操作按钮 */}
        {!isEditing && (
          <div className={cn(
            "flex gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity",
            isUser ? "justify-end" : "justify-start"
          )}>
            {/* 复制按钮 - 所有消息都有 */}
            <button
              onClick={handleCopy}
              className="p-1 text-xs text-muted-foreground hover:text-foreground rounded flex items-center gap-1"
              title="复制内容"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-green-500" />
                  <span className="text-green-500">已复制</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>复制</span>
                </>
              )}
            </button>
            
            {/* 用户消息额外的编辑和重试按钮 */}
            {isUser && onRetry && (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-1 text-xs text-muted-foreground hover:text-foreground rounded flex items-center gap-1"
                  title="编辑并重发"
                >
                  <Pencil className="w-3 h-3" />
                  <span>编辑</span>
                </button>
                <button
                  onClick={() => onRetry(message.content)}
                  className="p-1 text-xs text-muted-foreground hover:text-foreground rounded flex items-center gap-1"
                  title="重新发送"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>重试</span>
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// @引用下拉菜单
function MentionDropdown({ 
  options, 
  onSelect, 
  searchText,
  position 
}: { 
  options: MentionOption[]
  onSelect: (option: MentionOption) => void
  searchText: string
  position: { top: number; left: number }
}) {
  const filteredOptions = options.filter(opt => 
    opt.available && opt.label.toLowerCase().includes(searchText.toLowerCase())
  )

  if (filteredOptions.length === 0) return null

  return (
    <div 
      className="absolute z-50 bg-background border rounded-lg shadow-lg py-1 min-w-[200px] max-h-[200px] overflow-auto"
      style={{ bottom: '100%', left: 0, marginBottom: '4px' }}
    >
      <div className="px-2 py-1 text-xs text-muted-foreground border-b">
        可引用的上下文
      </div>
      {filteredOptions.map(option => (
        <button
          key={option.id}
          onClick={() => onSelect(option)}
          className="w-full px-3 py-2 text-left text-sm hover:bg-accent flex items-center gap-2"
        >
          <AtSign className="w-4 h-4 text-primary" />
          <div>
            <div className="font-medium">{option.label}</div>
            {option.description && (
              <div className="text-xs text-muted-foreground">{option.description}</div>
            )}
          </div>
        </button>
      ))}
    </div>
  )
}

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const [showMentions, setShowMentions] = useState(false)
  const [mentionSearch, setMentionSearch] = useState('')
  const [cursorPosition, setCursorPosition] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  const { 
    messages, 
    status, 
    isLoading, 
    respond, 
    startWorkflow, 
    currentProfile,
    retryFromMessage,
    workflowData,
    agentChat,
  } = useWorkflowStore()
  
  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 构建可引用的上下文选项
  const mentionOptions: MentionOption[] = useMemo(() => {
    const options: MentionOption[] = [
      {
        id: 'intent',
        label: '意图分析',
        category: 'stage',
        available: !!workflowData?.intent,
        description: '项目目标和成功标准',
      },
      {
        id: 'research',
        label: '消费者调研',
        category: 'stage',
        available: !!workflowData?.consumer_research,
        description: '用户画像和痛点期望',
      },
      {
        id: 'core_design',
        label: '内涵设计',
        category: 'stage',
        available: !!workflowData?.content_core,
        description: '设计方案',
      },
    ]
    
    // 添加内涵生产已完成的字段
    if (workflowData?.content_core?.sections) {
      for (const section of workflowData.content_core.sections) {
        for (const field of section.fields) {
          if (field.status === 'completed' && field.content) {
            options.push({
              id: `field_${field.id}`,
              label: `${section.name}/${field.name}`,
              category: 'field',
              available: true,
              description: field.content.slice(0, 50) + (field.content.length > 50 ? '...' : ''),
            })
          }
        }
      }
    }
    
    return options
  }, [workflowData])

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    const cursor = e.target.selectionStart || 0
    setInput(value)
    setCursorPosition(cursor)

    // 检测@触发
    const textBeforeCursor = value.slice(0, cursor)
    const lastAtIndex = textBeforeCursor.lastIndexOf('@')
    
    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1)
      // 如果@后面没有空格，显示下拉菜单
      if (!textAfterAt.includes(' ')) {
        setShowMentions(true)
        setMentionSearch(textAfterAt)
        return
      }
    }
    
    setShowMentions(false)
    setMentionSearch('')
  }

  // 处理选择@引用
  const handleSelectMention = (option: MentionOption) => {
    const textBeforeCursor = input.slice(0, cursorPosition)
    const lastAtIndex = textBeforeCursor.lastIndexOf('@')
    const textBeforeAt = input.slice(0, lastAtIndex)
    const textAfterCursor = input.slice(cursorPosition)
    
    const newInput = `${textBeforeAt}@${option.label} ${textAfterCursor}`
    setInput(newInput)
    setShowMentions(false)
    setMentionSearch('')
    
    // 聚焦输入框
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus()
        const newCursor = textBeforeAt.length + option.label.length + 2
        inputRef.current.setSelectionRange(newCursor, newCursor)
      }
    }, 0)
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    
    const message = input.trim()
    setInput('')
    setShowMentions(false)
    
    // 如果还没开始工作流，开始新的
    if (!status) {
      if (currentProfile) {
        await startWorkflow(
          currentProfile.id,
          `项目_${new Date().toISOString().slice(0, 10)}`,
          message
        )
      }
      return
    }
    
    // 如果正在等待用户输入（追问阶段），使用普通respond
    if (status.waiting_for_input && !message.includes('@')) {
      await respond(message)
      return
    }
    
    // 其他所有情况都使用agentChat（随时可对话）
    if (agentChat) {
      await agentChat(message)
    } else {
      // 降级到respond
      await respond(message)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
    // ESC关闭下拉菜单
    if (e.key === 'Escape') {
      setShowMentions(false)
    }
  }

  // 处理重试
  const handleRetry = (messageId: string, newContent: string) => {
    if (retryFromMessage) {
      retryFromMessage(messageId, newContent)
    }
  }

  // 找到最后一条用户消息
  const lastUserMessageIndex = [...messages].reverse().findIndex(m => m.role === 'user')
  const lastUserMessageId = lastUserMessageIndex >= 0 
    ? messages[messages.length - 1 - lastUserMessageIndex].id 
    : null

  // 获取当前阶段提示
  const getStageTip = () => {
    if (!status) return '开始你的内容生产之旅'
    
    const stageTips: Record<string, string> = {
      intent: '意图分析阶段 - 可用@引用修改目标',
      research: '消费者调研阶段 - 可用@意图分析 引用意图',
      core_design: '内涵设计阶段 - 可用@引用调整方案',
      core_production: '内涵生产阶段',
      extension: '外延生产阶段',
    }
    return stageTips[status.current_stage] || ''
  }

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="p-4 border-b">
        <h2 className="font-semibold flex items-center gap-2">
          AI 对话
          {workflowData && (
            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
              可用@引用
            </span>
          )}
        </h2>
        {status?.clarification_progress && (
          <span className="text-xs text-muted-foreground">
            追问进度: {status.clarification_progress}
          </span>
        )}
        <p className="text-xs text-muted-foreground mt-1">{getStageTip()}</p>
      </div>
      
      {/* 消息列表 */}
      <div className="flex-1 overflow-auto p-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="mb-2">开始你的内容生产之旅</p>
              <p className="text-sm">描述你想要生产的内容...</p>
              <div className="mt-4 text-xs border rounded-lg p-3 text-left">
                <p className="font-medium mb-2">💡 使用@引用</p>
                <p>输入 @ 可以引用已有内容，例如：</p>
                <p className="text-primary mt-1">@意图分析 修改目标为...</p>
                <p className="text-primary">@消费者调研 调整用户画像...</p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble 
                key={message.id} 
                message={message}
                isLast={index === messages.length - 1}
                onRetry={
                  message.role === 'user' && message.id === lastUserMessageId && !isLoading
                    ? (newContent) => handleRetry(message.id, newContent)
                    : undefined
                }
              />
            ))}
            
            {/* 加载状态 */}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-muted rounded-lg px-4 py-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">AI思考中...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* 输入区 */}
      <div className="p-4 border-t relative">
        {/* @引用下拉菜单 */}
        {showMentions && (
          <MentionDropdown
            options={mentionOptions}
            onSelect={handleSelectMention}
            searchText={mentionSearch}
            position={{ top: 0, left: 0 }}
          />
        )}
        
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={
                !status 
                  ? "描述你想生产的内容..." 
                  : status.waiting_for_input 
                    ? "回复追问... (输入@引用上下文)" 
                    : "随时输入，AI助手在线... (输入@引用上下文)"
              }
              className="w-full resize-none rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              rows={2}
              disabled={isLoading || !currentProfile}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim() || !currentProfile}
            className={cn(
              "p-3 rounded-lg transition-colors",
              isLoading || !input.trim() || !currentProfile
                ? "bg-muted text-muted-foreground cursor-not-allowed"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        {!currentProfile && (
          <p className="text-xs text-muted-foreground mt-2">
            请先选择创作者特质
          </p>
        )}
      </div>
    </div>
  )
}
