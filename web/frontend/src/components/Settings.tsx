import { useState } from 'react'
import { X, User, FileText, MessageSquare, Gauge, Radio, Database } from 'lucide-react'
import './Settings.css'

interface SettingsProps {
  onClose: () => void
}

type SettingsTab = 'project' | 'profile' | 'schema' | 'prompts' | 'simulator' | 'channels' | 'data'

export function Settings({ onClose }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('project')

  const tabs: Array<{ id: SettingsTab; name: string; icon: React.ReactNode }> = [
    { id: 'project', name: '项目设置', icon: <FileText size={18} /> },
    { id: 'profile', name: '创作者特质', icon: <User size={18} /> },
    { id: 'schema', name: '字段模板', icon: <FileText size={18} /> },
    { id: 'prompts', name: '系统提示词', icon: <MessageSquare size={18} /> },
    { id: 'simulator', name: '评估器配置', icon: <Gauge size={18} /> },
    { id: 'channels', name: '渠道管理', icon: <Radio size={18} /> },
    { id: 'data', name: '数据管理', icon: <Database size={18} /> },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'project':
        return <ProjectSettings />
      case 'profile':
        return <ProfileSettings />
      case 'schema':
        return <SchemaSettings />
      case 'prompts':
        return <PromptSettings />
      case 'simulator':
        return <SimulatorSettings />
      case 'channels':
        return <ChannelSettings />
      case 'data':
        return <DataSettings />
      default:
        return null
    }
  }

  return (
    <div className="settings-overlay">
      <div className="settings-modal">
        <div className="settings-header">
          <h1>设置</h1>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="settings-body">
          <nav className="settings-nav">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon}
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>

          <main className="settings-content">
            {renderContent()}
          </main>
        </div>
      </div>
    </div>
  )
}

// ===== Settings Panels =====

function ProjectSettings() {
  return (
    <div className="settings-panel">
      <h2>项目设置</h2>
      
      <div className="form-group">
        <label>项目名称</label>
        <input type="text" className="input" defaultValue="团队管理课程" />
      </div>
      
      <div className="form-group">
        <label>项目描述</label>
        <textarea className="input-textarea" rows={3} defaultValue="面向新晋管理者的团队管理入门课程" />
      </div>
      
      <div className="form-group">
        <label>使用的字段模板</label>
        <select className="input">
          <option>课程模板 v2</option>
          <option>营销长文案模板</option>
          <option>产品说明书模板</option>
        </select>
      </div>
      
      <div className="form-group">
        <label>关联的创作者特质</label>
        <select className="input">
          <option>老王的风格</option>
          <option>正式商务风格</option>
          <option>轻松口语风格</option>
        </select>
      </div>
      
      <div className="form-actions">
        <button className="btn-primary">保存</button>
        <button className="btn-secondary">重置</button>
      </div>
    </div>
  )
}

function ProfileSettings() {
  return (
    <div className="settings-panel">
      <div className="panel-header">
        <h2>创作者特质</h2>
        <button className="btn-secondary">+ 新建特质</button>
      </div>
      
      <div className="item-list">
        <div className="list-item active">
          <span className="item-name">老王的风格（当前使用）</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text danger">删除</button>
          </div>
        </div>
        <div className="list-item">
          <span className="item-name">正式商务风格</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text danger">删除</button>
          </div>
        </div>
      </div>
      
      <hr className="divider" />
      
      <h3>编辑：老王的风格</h3>
      
      <div className="form-group">
        <label>禁忌词汇</label>
        <input type="text" className="input" defaultValue="躺赚, 割韭菜, 暴富" />
      </div>
      
      <div className="form-group">
        <label>禁碰话题</label>
        <input type="text" className="input" defaultValue="政治, 宗教" />
      </div>
      
      <div className="form-group">
        <label>范例文本</label>
        <textarea 
          className="input-textarea" 
          rows={5}
          defaultValue="说白了就是，很多人学东西学不会，不是因为笨，是因为他们总想一步到位。"
        />
      </div>
      
      <div className="form-group">
        <label>自定义字段</label>
        <div className="custom-fields">
          <div className="custom-field">
            <input type="text" className="input small" defaultValue="调性" />
            <input type="text" className="input" defaultValue="口语化、略带自嘲" />
          </div>
          <div className="custom-field">
            <input type="text" className="input small" defaultValue="写作节奏" />
            <input type="text" className="input" defaultValue="短句为主，每段不超过3行" />
          </div>
        </div>
        <button className="btn-text">+ 添加字段</button>
      </div>
      
      <div className="form-actions">
        <button className="btn-primary">保存</button>
      </div>
    </div>
  )
}

function SchemaSettings() {
  return (
    <div className="settings-panel">
      <div className="panel-header">
        <h2>字段模板</h2>
        <button className="btn-secondary">+ 新建模板</button>
      </div>
      
      <div className="item-list">
        <div className="list-item active">
          <span className="item-name">课程模板 v2（当前使用）</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text">复制</button>
          </div>
        </div>
        <div className="list-item">
          <span className="item-name">营销长文案模板</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text">复制</button>
          </div>
        </div>
      </div>
      
      <hr className="divider" />
      
      <h3>编辑：课程模板 v2</h3>
      
      <div className="form-group">
        <label>模板描述</label>
        <input type="text" className="input" defaultValue="适用于线上课程的完整素材生产" />
      </div>
      
      <div className="form-group">
        <label>字段列表</label>
        <div className="field-editor">
          <div className="field-card">
            <div className="field-header">
              <span className="field-order">1.</span>
              <input type="text" className="input" defaultValue="课程目标" />
              <button className="btn-icon">↑</button>
              <button className="btn-icon">↓</button>
              <button className="btn-icon danger">×</button>
            </div>
            <div className="field-details">
              <input type="text" className="input small" placeholder="说明" defaultValue="学完后学员能做到什么" />
              <select className="input small">
                <option>text</option>
                <option>list</option>
                <option>object</option>
              </select>
              <label className="checkbox">
                <input type="checkbox" defaultChecked />
                <span>必填</span>
              </label>
            </div>
            <input type="text" className="input" placeholder="AI提示" defaultValue='用"能+动词+具体成果"格式' />
          </div>
          
          <button className="btn-secondary full-width">+ 添加字段</button>
        </div>
      </div>
      
      <div className="form-actions">
        <button className="btn-primary">保存</button>
        <button className="btn-secondary">预览</button>
      </div>
    </div>
  )
}

function PromptSettings() {
  return (
    <div className="settings-panel">
      <h2>系统提示词</h2>
      
      <div className="form-group">
        <label>提示词分类</label>
        <div className="tab-buttons">
          <button className="tab-btn active">意图分析</button>
          <button className="tab-btn">消费者调研</button>
          <button className="tab-btn">内涵生产</button>
          <button className="tab-btn">外延生产</button>
          <button className="tab-btn">评估器</button>
        </div>
      </div>
      
      <div className="form-group">
        <label>内涵生产 &gt; 内容生成提示词</label>
        <textarea 
          className="input-textarea code" 
          rows={15}
          defaultValue={`你正在为以下创作者生产内容：
{creator_profile}

目标用户：
{consumer_research}

当前要生产的字段：
名称：{field_name}
说明：{field_description}
提示：{field_ai_hint}

请生成该字段的内容。`}
        />
      </div>
      
      <div className="hint-box">
        <strong>可用变量：</strong>
        <span className="var-tag">{'{creator_profile}'}</span>
        <span className="var-tag">{'{consumer_research}'}</span>
        <span className="var-tag">{'{intent}'}</span>
        <span className="var-tag">{'{field_name}'}</span>
        <span className="var-tag">{'{field_description}'}</span>
      </div>
      
      <div className="form-actions">
        <button className="btn-primary">保存</button>
        <button className="btn-secondary">重置为默认</button>
        <button className="btn-secondary">测试运行</button>
      </div>
    </div>
  )
}

function SimulatorSettings() {
  return (
    <div className="settings-panel">
      <div className="panel-header">
        <h2>评估器配置</h2>
        <button className="btn-secondary">+ 新建评估器</button>
      </div>
      
      <div className="item-list">
        <div className="list-item active">
          <span className="item-name">目标读者视角（当前使用）</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text danger">删除</button>
          </div>
        </div>
      </div>
      
      <hr className="divider" />
      
      <h3>编辑：目标读者视角</h3>
      
      <div className="form-group">
        <label>评估提示词</label>
        <textarea 
          className="input-textarea code" 
          rows={10}
          defaultValue={`你是我的目标读者：
{consumer_research}

读完以下内容后回答：
1. 读完后你想采取什么行动？
2. 哪里让你觉得"这不对"或"不适合我"？
3. 整体打分（1-10），一句话说为什么。

【内容】
{content}`}
        />
      </div>
      
      <div className="form-group">
        <label>自动迭代配置</label>
        <div className="config-row">
          <label className="checkbox">
            <input type="checkbox" defaultChecked />
            <span>启用自动迭代</span>
          </label>
        </div>
        <div className="config-row">
          <span>触发条件：评分低于</span>
          <input type="number" className="input tiny" defaultValue="6" />
          <span>分</span>
        </div>
        <div className="config-row">
          <span>停止条件：评分高于</span>
          <input type="number" className="input tiny" defaultValue="8" />
          <span>分 或 迭代次数达到</span>
          <input type="number" className="input tiny" defaultValue="3" />
          <span>次</span>
        </div>
      </div>
      
      <div className="form-actions">
        <button className="btn-primary">保存</button>
        <button className="btn-secondary">测试运行</button>
      </div>
    </div>
  )
}

function ChannelSettings() {
  return (
    <div className="settings-panel">
      <div className="panel-header">
        <h2>渠道管理</h2>
        <button className="btn-secondary">+ 新建渠道</button>
      </div>
      
      <div className="item-list">
        <div className="list-item">
          <span className="item-name">课程介绍页</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text danger">删除</button>
          </div>
        </div>
        <div className="list-item">
          <span className="item-name">小红书</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text danger">删除</button>
          </div>
        </div>
        <div className="list-item">
          <span className="item-name">邮件序列</span>
          <div className="item-actions">
            <button className="btn-text">编辑</button>
            <button className="btn-text danger">删除</button>
          </div>
        </div>
      </div>
      
      <hr className="divider" />
      
      <h3>编辑：小红书</h3>
      
      <div className="form-group">
        <label>渠道描述</label>
        <input type="text" className="input" defaultValue="生成适合小红书平台的短图文内容" />
      </div>
      
      <div className="form-group">
        <label>格式约束</label>
        <div className="constraints-list">
          <div className="constraint-item">
            <span>标题字数</span>
            <input type="text" className="input small" defaultValue="最多20字" />
          </div>
          <div className="constraint-item">
            <span>正文字数</span>
            <input type="text" className="input small" defaultValue="500-1000字" />
          </div>
          <div className="constraint-item">
            <span>标题格式</span>
            <input type="text" className="input small" defaultValue="emoji开头" />
          </div>
        </div>
      </div>
      
      <div className="form-actions">
        <button className="btn-primary">保存</button>
      </div>
    </div>
  )
}

function DataSettings() {
  return (
    <div className="settings-panel">
      <h2>数据管理</h2>
      
      <div className="data-section">
        <h3>项目数据</h3>
        <div className="data-info">
          <p>存储位置：本地数据库</p>
          <p>数据大小：12.3 MB</p>
          <p>最后保存：2026-02-01 14:32:15</p>
        </div>
        <div className="data-actions">
          <button className="btn-secondary">导出项目</button>
          <button className="btn-secondary">导入项目</button>
          <button className="btn-secondary danger">清空项目数据</button>
        </div>
      </div>
      
      <hr className="divider" />
      
      <div className="data-section">
        <h3>内容文件</h3>
        <div className="file-list">
          <div className="file-item">
            <span className="file-icon">📄</span>
            <span className="file-name">课程目标.md</span>
            <span className="file-size">12KB</span>
            <button className="btn-text">查看</button>
            <button className="btn-text">导出</button>
          </div>
          <div className="file-item">
            <span className="file-icon">📄</span>
            <span className="file-name">课程大纲.md</span>
            <span className="file-size">8KB</span>
            <button className="btn-text">查看</button>
            <button className="btn-text">导出</button>
          </div>
        </div>
        <button className="btn-secondary">导出全部为ZIP</button>
      </div>
      
      <hr className="divider" />
      
      <div className="data-section">
        <h3>对话历史</h3>
        <p>共 156 条对话记录</p>
        <div className="data-actions">
          <button className="btn-secondary">查看完整历史</button>
          <button className="btn-secondary">导出对话</button>
          <button className="btn-secondary danger">清空对话历史</button>
        </div>
      </div>
    </div>
  )
}

