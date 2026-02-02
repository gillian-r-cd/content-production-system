import { ArrowRight, RefreshCw } from 'lucide-react'
import type { Stage } from '../App'
import './Editor.css'

interface EditorProps {
  stage: Stage
  content: any
  onContentChange: (content: any) => void
  onNext: () => void
}

export function Editor({ stage, content, onContentChange, onNext }: EditorProps) {
  const renderStageContent = () => {
    switch (stage) {
      case 'profile':
        return <ProfileEditor content={content} onChange={onContentChange} />
      case 'intent':
        return <IntentEditor content={content} onChange={onContentChange} />
      case 'research':
        return <ResearchEditor content={content} onChange={onContentChange} />
      case 'core':
        return <CoreEditor content={content} onChange={onContentChange} />
      case 'extension':
        return <ExtensionEditor content={content} onChange={onContentChange} />
      case 'report':
        return <ReportEditor content={content} />
      default:
        return <div className="empty-state">选择一个阶段开始</div>
    }
  }

  const stageNames: Record<Stage, string> = {
    profile: '创作者特质',
    intent: '意图分析',
    research: '消费者调研',
    core: '内涵生产',
    extension: '外延生产',
    report: '评估报告',
  }

  return (
    <main className="editor">
      <div className="editor-header">
        <h2>{stageNames[stage]}</h2>
        <div className="editor-actions">
          <button className="btn-secondary" title="重新生成">
            <RefreshCw size={16} />
            <span>重新生成</span>
          </button>
        </div>
      </div>
      
      <div className="editor-content">
        {renderStageContent()}
      </div>
      
      <div className="editor-footer">
        <button className="btn-primary" onClick={onNext}>
          <span>确认并继续</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </main>
  )
}

// ===== 各阶段编辑器 =====

function ProfileEditor({ content, onChange }: { content: any; onChange: (c: any) => void }) {
  return (
    <div className="stage-editor">
      <div className="info-card">
        <p>创作者特质已加载。你可以在设置中修改。</p>
      </div>
    </div>
  )
}

function IntentEditor({ content, onChange }: { content: any; onChange: (c: any) => void }) {
  return (
    <div className="stage-editor">
      <div className="form-group">
        <label>核心目标</label>
        <textarea
          className="input-textarea"
          placeholder="这个内容要达成什么效果？"
          value={content?.goal || ''}
          onChange={e => onChange({ ...content, goal: e.target.value })}
          rows={3}
        />
      </div>
      
      <div className="form-group">
        <label>成功标准</label>
        <textarea
          className="input-textarea"
          placeholder="怎么判断内容成功了？（可衡量的指标）"
          value={content?.success_criteria || ''}
          onChange={e => onChange({ ...content, success_criteria: e.target.value })}
          rows={3}
        />
      </div>
      
      <div className="form-row">
        <div className="form-group">
          <label>必须包含</label>
          <textarea
            className="input-textarea"
            placeholder="内容中必须出现的元素"
            value={content?.must_have || ''}
            onChange={e => onChange({ ...content, must_have: e.target.value })}
            rows={3}
          />
        </div>
        <div className="form-group">
          <label>必须避免</label>
          <textarea
            className="input-textarea"
            placeholder="内容中必须规避的元素"
            value={content?.must_avoid || ''}
            onChange={e => onChange({ ...content, must_avoid: e.target.value })}
            rows={3}
          />
        </div>
      </div>
    </div>
  )
}

function ResearchEditor({ content, onChange }: { content: any; onChange: (c: any) => void }) {
  return (
    <div className="stage-editor">
      <div className="mode-tabs">
        <button className="mode-tab active">AI生成</button>
        <button className="mode-tab">直接粘贴</button>
        <button className="mode-tab">混合模式</button>
      </div>
      
      <div className="form-group">
        <label>用户画像</label>
        <textarea
          className="input-textarea"
          placeholder="目标用户是谁？"
          value={content?.persona || ''}
          onChange={e => onChange({ ...content, persona: e.target.value })}
          rows={4}
        />
      </div>
      
      <div className="form-group">
        <label>核心痛点</label>
        <textarea
          className="input-textarea"
          placeholder="用户面临什么问题？"
          value={content?.pain_points || ''}
          onChange={e => onChange({ ...content, pain_points: e.target.value })}
          rows={4}
        />
      </div>
      
      <div className="form-group">
        <label>核心期望</label>
        <textarea
          className="input-textarea"
          placeholder="用户想要达成什么？"
          value={content?.desires || ''}
          onChange={e => onChange({ ...content, desires: e.target.value })}
          rows={4}
        />
      </div>
    </div>
  )
}

function CoreEditor({ content, onChange }: { content: any; onChange: (c: any) => void }) {
  return (
    <div className="stage-editor">
      <div className="info-card">
        <h3>内涵生产</h3>
        <p>根据字段模板逐个生产完整内容。</p>
      </div>
      
      <div className="field-list">
        <div className="field-item completed">
          <span className="field-status">✓</span>
          <span className="field-name">课程目标</span>
          <span className="field-score">8/10</span>
        </div>
        <div className="field-item active">
          <span className="field-status">→</span>
          <span className="field-name">课程大纲</span>
          <span className="field-score">-</span>
        </div>
        <div className="field-item pending">
          <span className="field-status">○</span>
          <span className="field-name">第一节脚本</span>
          <span className="field-score">-</span>
        </div>
      </div>
      
      <div className="current-field">
        <h4>当前字段：课程大纲</h4>
        <textarea
          className="input-textarea large"
          placeholder="AI生成的内容将显示在这里..."
          value={content?.current_field || ''}
          onChange={e => onChange({ ...content, current_field: e.target.value })}
          rows={12}
        />
      </div>
    </div>
  )
}

function ExtensionEditor({ content, onChange }: { content: any; onChange: (c: any) => void }) {
  return (
    <div className="stage-editor">
      <div className="channel-tabs">
        <button className="channel-tab active">课程介绍页</button>
        <button className="channel-tab">小红书</button>
        <button className="channel-tab">+ 添加渠道</button>
      </div>
      
      <div className="form-group">
        <label>课程介绍页内容</label>
        <textarea
          className="input-textarea large"
          placeholder="基于内涵生成的营销内容..."
          value={content?.channel_content || ''}
          onChange={e => onChange({ ...content, channel_content: e.target.value })}
          rows={16}
        />
      </div>
      
      <div className="evaluation-card">
        <div className="eval-header">
          <span>Simulator 评估</span>
          <span className="eval-score">8/10 ✓</span>
        </div>
        <p className="eval-summary">开头有吸引力，痛点描述到位。CTA部分紧迫感可以加强。</p>
      </div>
    </div>
  )
}

function ReportEditor({ content }: { content: any }) {
  return (
    <div className="stage-editor">
      <div className="report-section">
        <h3>流程报告</h3>
        <div className="report-stats">
          <div className="stat-item">
            <span className="stat-value">6</span>
            <span className="stat-label">AI调用次数</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">2</span>
            <span className="stat-label">迭代次数</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">15分钟</span>
            <span className="stat-label">总耗时</span>
          </div>
        </div>
      </div>
      
      <div className="report-section">
        <h3>质量报告</h3>
        <div className="quality-bars">
          <div className="quality-item">
            <span className="quality-label">课程目标</span>
            <div className="quality-bar"><div className="quality-fill" style={{width: '80%'}}></div></div>
            <span className="quality-score">8/10</span>
          </div>
          <div className="quality-item">
            <span className="quality-label">课程大纲</span>
            <div className="quality-bar"><div className="quality-fill" style={{width: '90%'}}></div></div>
            <span className="quality-score">9/10</span>
          </div>
          <div className="quality-item">
            <span className="quality-label">介绍页</span>
            <div className="quality-bar"><div className="quality-fill" style={{width: '80%'}}></div></div>
            <span className="quality-score">8/10</span>
          </div>
        </div>
      </div>
      
      <div className="report-actions">
        <button className="btn-primary">导出全部内容</button>
        <button className="btn-secondary">查看详细报告</button>
      </div>
    </div>
  )
}

