import { useState, useRef, useEffect } from 'react'
import { Send, Maximize2, Trash2 } from 'lucide-react'
import type { Stage } from '../App'
import './Chat.css'

interface Message {
  role: string
  content: string
}

interface ChatProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  currentStage: Stage
}

export function Chat({ messages, onSendMessage, currentStage }: ChatProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // 上下文引用提示
  const contextHints: Record<Stage, string[]> = {
    profile: [],
    intent: ['@创作者特质'],
    research: ['@意图分析', '@创作者特质'],
    core: ['@意图分析', '@消费者调研', '@创作者特质'],
    extension: ['@内涵.课程目标', '@内涵.课程大纲', '@消费者调研'],
    report: ['@内涵', '@外延'],
  }

  return (
    <aside className="chat">
      <div className="chat-header">
        <h2>对话</h2>
        <div className="chat-actions">
          <button className="icon-btn-small" title="清空对话">
            <Trash2 size={16} />
          </button>
          <button className="icon-btn-small" title="全屏">
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? '🤖' : '👤'}
            </div>
            <div className="message-content">
              <div className="message-role">
                {msg.role === 'assistant' ? 'AI' : '你'}
              </div>
              <div className="message-text">{msg.content}</div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {contextHints[currentStage]?.length > 0 && (
        <div className="context-hints">
          <span className="hint-label">可引用：</span>
          {contextHints[currentStage].map((hint, i) => (
            <button 
              key={i} 
              className="hint-tag"
              onClick={() => setInput(prev => prev + ' ' + hint)}
            >
              {hint}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-area">
        <textarea
          className="chat-input"
          placeholder="输入消息... (用@引用上下文)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
        />
        <button 
          className="send-btn" 
          onClick={handleSend}
          disabled={!input.trim()}
        >
          <Send size={18} />
        </button>
      </div>
    </aside>
  )
}

