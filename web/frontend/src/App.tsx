import { useState, useEffect } from 'react'
import { Sidebar } from './components/Sidebar'
import { Editor } from './components/Editor'
import { Chat } from './components/Chat'
import { Header } from './components/Header'
import { Settings } from './components/Settings'
import './App.css'

// 阶段定义
export type Stage = 'profile' | 'intent' | 'research' | 'core' | 'extension' | 'report'

export interface StageInfo {
  id: Stage
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'blocked'
}

export interface Project {
  id: string
  name: string
  status: string
  current_stage: string
}

export interface Profile {
  id: string
  name: string
}

function App() {
  const [currentStage, setCurrentStage] = useState<Stage>('intent')
  const [showSettings, setShowSettings] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  
  // 各阶段状态
  const [stages, setStages] = useState<StageInfo[]>([
    { id: 'profile', name: '创作者特质', status: 'completed' },
    { id: 'intent', name: '意图分析', status: 'in_progress' },
    { id: 'research', name: '消费者调研', status: 'pending' },
    { id: 'core', name: '内涵生产', status: 'pending' },
    { id: 'extension', name: '外延生产', status: 'pending' },
    { id: 'report', name: '评估报告', status: 'pending' },
  ])

  // 编辑区内容
  const [editorContent, setEditorContent] = useState<Record<string, any>>({})
  
  // 对话历史
  const [chatHistory, setChatHistory] = useState<Array<{role: string, content: string}>>([
    { role: 'assistant', content: '你好！请描述你想要生产的内容。包括目标、受众、用途等信息，我会帮你分析意图。' }
  ])

  // 加载数据
  useEffect(() => {
    fetchProfiles()
    fetchProjects()
  }, [])

  const fetchProfiles = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/profiles')
      const data = await res.json()
      setProfiles(data.profiles || [])
      if (data.profiles?.length > 0) {
        setCurrentProfile(data.profiles[0])
      }
    } catch (e) {
      console.error('Failed to fetch profiles:', e)
    }
  }

  const fetchProjects = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/projects')
      const data = await res.json()
      setProjects(data.projects || [])
    } catch (e) {
      console.error('Failed to fetch projects:', e)
    }
  }

  // 发送消息
  const handleSendMessage = async (message: string) => {
    // 添加用户消息
    setChatHistory(prev => [...prev, { role: 'user', content: message }])
    
    // 模拟AI响应（后续接入真实API）
    setTimeout(() => {
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: '收到！让我分析一下你的需求...\n\n正在处理中...' 
      }])
    }, 500)
  }

  // 更新阶段状态
  const updateStageStatus = (stageId: Stage, status: StageInfo['status']) => {
    setStages(prev => prev.map(s => 
      s.id === stageId ? { ...s, status } : s
    ))
  }

  // 进入下一阶段
  const goToNextStage = () => {
    const currentIndex = stages.findIndex(s => s.id === currentStage)
    if (currentIndex < stages.length - 1) {
      updateStageStatus(currentStage, 'completed')
      const nextStage = stages[currentIndex + 1].id
      setCurrentStage(nextStage)
      updateStageStatus(nextStage, 'in_progress')
    }
  }

  if (showSettings) {
    return <Settings onClose={() => setShowSettings(false)} />
  }

  return (
    <div className="app">
      <Header 
        projectName={currentProject?.name || '新项目'}
        profileName={currentProfile?.name || '未选择'}
        onSettingsClick={() => setShowSettings(true)}
        profiles={profiles}
        onProfileChange={(id) => {
          const profile = profiles.find(p => p.id === id)
          if (profile) setCurrentProfile(profile)
        }}
      />
      
      <div className="main-container">
        <Sidebar 
          stages={stages}
          currentStage={currentStage}
          onStageClick={setCurrentStage}
        />
        
        <Editor 
          stage={currentStage}
          content={editorContent[currentStage]}
          onContentChange={(content) => {
            setEditorContent(prev => ({ ...prev, [currentStage]: content }))
          }}
          onNext={goToNextStage}
        />
        
        <Chat 
          messages={chatHistory}
          onSendMessage={handleSendMessage}
          currentStage={currentStage}
        />
      </div>
      
      <footer className="status-bar">
        <span>当前阶段: {stages.find(s => s.id === currentStage)?.name}</span>
        <span>Simulator: 自动</span>
        <span>保存: ✓</span>
      </footer>
    </div>
  )
}

export default App
