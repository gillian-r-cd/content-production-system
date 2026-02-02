// web/src/stores/workflowStore.ts
// 工作流状态管理
// 功能：管理当前工作流的状态、数据、对话历史

import { create } from 'zustand'
import type { 
  WorkflowStatus, 
  WorkflowData, 
  ChatMessage, 
  Stage,
  Profile,
  Project,
  Intent
} from '@/types'
import { workflowApi } from '@/api'
import apiClient from '@/api/client'

interface WorkflowState {
  // 当前Profile
  currentProfile: Profile | null
  
  // 当前项目
  currentProject: Project | null
  
  // 工作流状态
  workflowId: string | null
  status: WorkflowStatus | null
  workflowData: WorkflowData | null
  
  // 对话历史
  messages: ChatMessage[]
  
  // 加载状态
  isLoading: boolean
  error: string | null
  
  // Actions - 基础
  setProfile: (profile: Profile) => void
  reset: () => void
  
  // Actions - 项目生命周期
  startNewProject: (projectName: string) => Promise<void>
  startWorkflow: (profileId: string, projectName: string, rawInput: string) => Promise<void>
  loadProject: (projectId: string) => Promise<void>
  respond: (answer: string) => Promise<void>
  refreshData: () => Promise<void>
  
  // Actions - 意图阶段
  updateIntent: (intent: Partial<Intent>) => void
  confirmIntent: () => Promise<void>
  
  // Actions - 消费者调研阶段
  updateResearch: (research: { summary?: string; key_pain_points?: string[]; key_desires?: string[] }) => Promise<void>
  
  // Actions - 方案选择
  selectScheme: (index: number, schemaId?: string) => Promise<void>
  updateScheme: (index: number, scheme: any) => Promise<void>
  
  // Actions - 对话
  addMessage: (role: 'user' | 'assistant' | 'system', content: string, stage?: Stage) => void
  retryFromMessage: (messageId: string, newContent: string) => Promise<void>
  
  // Actions - Agent对话（支持@引用）
  agentChat: (message: string) => Promise<void>
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  currentProfile: null,
  currentProject: null,
  workflowId: null,
  status: null,
  workflowData: null,
  messages: [],
  isLoading: false,
  error: null,

  setProfile: (profile) => {
    set({ currentProfile: profile })
  },

  reset: () => {
    set({
      currentProject: null,
      workflowId: null,
      status: null,
      workflowData: null,
      messages: [],
      isLoading: false,
      error: null,
    })
  },

  startNewProject: async (projectName) => {
    const { currentProfile } = get()
    if (!currentProfile) {
      set({ error: '请先选择创作者特质' })
      return
    }
    
    set({ isLoading: true, error: null })
    
    try {
      // 创建项目
      const { data: project } = await apiClient.post('/projects', {
        name: projectName,
        creator_profile_id: currentProfile.id,
      })
      
      set({
        currentProject: project,
        workflowId: project.id,
        status: {
          workflow_id: project.id,
          project_id: project.id,
          current_stage: 'intent',
          waiting_for_input: true,
          input_prompt: '请描述你想要生产的内容',
          clarification_progress: null,
          ai_call_count: 0,
          stages: {
            intent: 'in_progress',
            research: 'pending',
            core_design: 'pending',
            core_production: 'pending',
            extension: 'pending',
          },
        },
        isLoading: false,
      })
      
      // 添加欢迎消息
      get().addMessage('assistant', '项目创建成功！请描述你想要生产的内容，我会帮你进行意图分析。', 'intent')
      
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || error.message 
      })
    }
  },

  startWorkflow: async (profileId, projectName, rawInput) => {
    set({ isLoading: true, error: null })
    
    try {
      // 添加用户消息
      get().addMessage('user', rawInput, 'intent')
      
      const result = await workflowApi.start({
        profile_id: profileId,
        project_name: projectName,
        raw_input: rawInput,
      })
      
      set({
        workflowId: result.workflow_id,
        currentProject: result.project,
        status: result.status,
        isLoading: false,
      })
      
      // 如果需要追问，添加AI消息
      if (result.status.waiting_for_input && result.status.input_prompt) {
        get().addMessage('assistant', result.status.input_prompt, 'intent')
      }
      
      // 获取数据
      await get().refreshData()
      
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || error.message 
      })
    }
  },

  loadProject: async (projectId) => {
    set({ isLoading: true, error: null, messages: [] })
    
    try {
      // 调用后端加载项目
      const { data } = await apiClient.post(`/workflow/load/${projectId}`)
      
      // 恢复对话历史
      const restoredMessages: ChatMessage[] = []
      if (data.conversation_history && Array.isArray(data.conversation_history)) {
        data.conversation_history.forEach((msg: any, index: number) => {
          restoredMessages.push({
            id: `restored_${index}_${Date.now()}`,
            role: msg.role as 'user' | 'assistant' | 'system',
            content: msg.content,
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
            stage: undefined, // 历史消息不关联阶段
          })
        })
      }
      
      // 自动加载关联的创作者特质
      const profile = data.profile ? {
        id: data.profile.id,
        name: data.profile.name,
      } as Profile : null
      
      set({
        workflowId: data.workflow_id,
        currentProject: data.project,
        currentProfile: profile,  // 自动设置关联的profile
        status: data.status,
        workflowData: data.data,
        messages: restoredMessages,
        isLoading: false,
      })
      
      // 如果需要输入且没有历史消息中的相同提示，显示当前提示
      if (data.status.waiting_for_input && data.status.input_prompt) {
        const lastMsg = restoredMessages[restoredMessages.length - 1]
        if (!lastMsg || lastMsg.content !== data.status.input_prompt) {
          get().addMessage('assistant', data.status.input_prompt, data.status.current_stage)
        }
      }
      
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || error.message 
      })
    }
  },

  respond: async (answer) => {
    const { workflowId, status, currentProfile, currentProject } = get()
    
    // 如果还没有workflowId但有项目，说明是第一次输入
    if (!workflowId && currentProject && currentProfile) {
      return get().startWorkflow(currentProfile.id, currentProject.name, answer)
    }
    
    if (!workflowId) return
    
    set({ isLoading: true, error: null })
    
    try {
      // 添加用户消息
      get().addMessage('user', answer, status?.current_stage)
      
      const newStatus = await workflowApi.respond(workflowId, { answer })
      
      set({
        status: newStatus,
        isLoading: false,
      })
      
      // 如果需要继续追问
      if (newStatus.waiting_for_input && newStatus.input_prompt) {
        get().addMessage('assistant', newStatus.input_prompt, newStatus.current_stage)
      } else if (newStatus.current_stage !== status?.current_stage) {
        // 阶段变化，添加系统消息
        const stageNames: Record<string, string> = {
          intent: '意图分析',
          research: '消费者调研',
          core_design: '内涵设计',
          core_production: '内涵生产',
          extension: '外延生产',
        }
        get().addMessage('system', `已进入：${stageNames[newStatus.current_stage] || newStatus.current_stage}`, newStatus.current_stage)
      }
      
      // 刷新数据
      await get().refreshData()
      
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || error.message 
      })
      get().addMessage('system', `错误: ${error.response?.data?.detail || error.message}`)
    }
  },

  refreshData: async () => {
    const { workflowId } = get()
    if (!workflowId) return
    
    try {
      const data = await workflowApi.getData(workflowId)
      set({ workflowData: data })
    } catch (error) {
      console.error('Failed to refresh data:', error)
    }
  },

  updateIntent: (intentUpdate) => {
    set((state) => ({
      workflowData: state.workflowData ? {
        ...state.workflowData,
        intent: state.workflowData.intent ? {
          ...state.workflowData.intent,
          ...intentUpdate,
        } : null,
      } : null,
    }))
  },

  confirmIntent: async () => {
    const { workflowId } = get()
    if (!workflowId) return
    
    // 使用respond端点发送确认
    // 后端会通过input_callback="confirm_intent"识别这是确认操作
    get().addMessage('user', '确认意图', 'intent')
    
    set({ isLoading: true })
    
    try {
      const newStatus = await workflowApi.respond(workflowId, { answer: '确认' })
      
      set({
        status: newStatus,
        isLoading: false,
      })
      
      get().addMessage('system', '意图分析完成，正在进行消费者调研...', 'research')
      
      // 刷新数据
      await get().refreshData()
      
      // 如果需要输入（调研完成后会需要确认）
      if (newStatus.waiting_for_input && newStatus.input_prompt) {
        get().addMessage('assistant', newStatus.input_prompt, newStatus.current_stage)
      }
      
    } catch (error: any) {
      set({ isLoading: false })
      console.error('确认意图失败:', error)
    }
  },

  updateResearch: async (research) => {
    const { workflowId } = get()
    if (!workflowId) return
    
    // 本地更新
    set((state) => ({
      workflowData: state.workflowData ? {
        ...state.workflowData,
        consumer_research: state.workflowData.consumer_research ? {
          ...state.workflowData.consumer_research,
          summary: research.summary ?? state.workflowData.consumer_research.summary,
          key_pain_points: research.key_pain_points ?? state.workflowData.consumer_research.key_pain_points,
          key_desires: research.key_desires ?? state.workflowData.consumer_research.key_desires,
        } : null,
      } : null,
    }))
    
    // 尝试同步到后端（如果有对应API）
    try {
      await apiClient.patch(`/workflow/${workflowId}/research`, research)
    } catch (error) {
      // 忽略API错误，本地已更新
      console.log('Research update API not available, using local update only')
    }
  },

  selectScheme: async (index, schemaId) => {
    const { workflowId } = get()
    if (!workflowId) return
    
    set({ isLoading: true })
    
    try {
      // 选择方案并进入内容生产，同时可指定字段模板
      await apiClient.post(`/workflow/${workflowId}/select-scheme`, {
        scheme_index: index,
        schema_id: schemaId,  // 传递选中的字段模板ID
      })
      
      // 更新状态
      set((state) => ({
        workflowData: state.workflowData ? {
          ...state.workflowData,
          content_core: state.workflowData.content_core ? {
            ...state.workflowData.content_core,
            selected_scheme_index: index,
          } : null,
        } : null,
        status: state.status ? {
          ...state.status,
          current_stage: 'core_production',
          stages: {
            ...state.status.stages,
            core_design: 'completed',
            core_production: 'in_progress',
          },
        } : null,
        isLoading: false,
      }))
      
      get().addMessage('system', '方案已选择，开始内容生产...', 'core_production')
      
    } catch (error: any) {
      set({ isLoading: false })
      // 模拟阶段切换
      set((state) => ({
        workflowData: state.workflowData ? {
          ...state.workflowData,
          content_core: state.workflowData.content_core ? {
            ...state.workflowData.content_core,
            selected_scheme_index: index,
          } : null,
        } : null,
        status: state.status ? {
          ...state.status,
          current_stage: 'core_production',
          stages: {
            ...state.status.stages,
            core_design: 'completed',
            core_production: 'in_progress',
          },
        } : null,
      }))
    }
  },

  updateScheme: async (index, scheme) => {
    const { workflowId } = get()
    if (!workflowId) return

    // 本地更新
    set((state) => ({
      workflowData: state.workflowData ? {
        ...state.workflowData,
        content_core: state.workflowData.content_core ? {
          ...state.workflowData.content_core,
          design_schemes: state.workflowData.content_core.design_schemes?.map((s, i) => 
            i === index ? scheme : s
          ) || [],
        } : null,
      } : null,
    }))

    // 同步到后端
    try {
      await apiClient.patch(`/workflow/${workflowId}/update-field`, {
        stage: 'content_core',
        field: 'design_schemes',
        index,
        value: scheme,
      })
    } catch (error) {
      console.log('Scheme update API not available, using local update only')
    }
  },

  addMessage: (role, content, stage) => {
    const message: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role,
      content,
      timestamp: new Date(),
      stage,
    }
    set((state) => ({
      messages: [...state.messages, message],
    }))
  },

  retryFromMessage: async (messageId, newContent) => {
    const { messages, respond } = get()
    
    // 找到该消息的索引
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex === -1) return
    
    // 删除该消息及其之后的所有消息
    const newMessages = messages.slice(0, messageIndex)
    set({ messages: newMessages })
    
    // 重新发送
    await respond(newContent)
  },

  agentChat: async (message) => {
    const { workflowId, status, workflowData, currentProfile, currentProject } = get()
    
    // 如果没有workflowId但有项目，先启动工作流
    if (!workflowId && currentProject && currentProfile) {
      return get().startWorkflow(currentProfile.id, currentProject.name, message)
    }
    
    if (!workflowId) {
      get().addMessage('system', '请先创建或选择一个项目')
      return
    }
    
    set({ isLoading: true, error: null })
    
    // 添加用户消息
    get().addMessage('user', message, status?.current_stage)
    
    try {
      // 解析@引用
      const mentionPattern = /@(意图分析|消费者调研|内涵设计|内涵生产|外延生产)/g
      const mentions = message.match(mentionPattern) || []
      
      // 构建上下文引用
      const contexts: { type: string; content: string }[] = []
      
      for (const mention of mentions) {
        const type = mention.replace('@', '')
        let content = ''
        
        switch (type) {
          case '意图分析':
            if (workflowData?.intent) {
              content = JSON.stringify(workflowData.intent, null, 2)
            }
            break
          case '消费者调研':
            if (workflowData?.consumer_research) {
              content = JSON.stringify(workflowData.consumer_research, null, 2)
            }
            break
          case '内涵设计':
          case '内涵生产':
            if (workflowData?.content_core) {
              content = JSON.stringify(workflowData.content_core, null, 2)
            }
            break
          case '外延生产':
            if (workflowData?.content_extension) {
              content = JSON.stringify(workflowData.content_extension, null, 2)
            }
            break
        }
        
        if (content) {
          contexts.push({ type, content })
        }
      }
      
      // 调用后端Agent API
      const { data } = await apiClient.post(`/workflow/${workflowId}/agent-chat`, {
        message,
        contexts,
      })
      
      set({ isLoading: false })
      
      // 添加AI回复
      if (data.response) {
        get().addMessage('assistant', data.response, status?.current_stage)
      }
      
      // 如果有数据更新，刷新数据
      if (data.updated) {
        await get().refreshData()
        get().addMessage('system', '已根据你的要求更新内容', status?.current_stage)
      }
      
    } catch (error: any) {
      set({ isLoading: false })
      
      const errorMessage = error.response?.data?.detail || error.message
      
      // 如果API不存在或需要降级
      if (error.response?.status === 404) {
        // 降级处理：尝试使用respond
        try {
          // 移除已添加的用户消息，因为respond会重新添加
          set(state => ({ 
            messages: state.messages.slice(0, -1),
            isLoading: true 
          }))
          await get().respond(message)
        } catch (respondError: any) {
          set({ isLoading: false })
          get().addMessage('assistant', `抱歉，我现在无法回应。${respondError.response?.data?.detail || ''}`, status?.current_stage)
        }
      } else {
        get().addMessage('assistant', `抱歉，遇到了一些问题: ${errorMessage}`, status?.current_stage)
      }
    }
  },
}))
