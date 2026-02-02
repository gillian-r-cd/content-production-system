// web/src/types/index.ts
// TypeScript类型定义
// 功能：与后端API一致的数据类型

// === Profile ===
export interface Profile {
  id: string
  name: string
  taboos: {
    forbidden_words: string[]
    forbidden_topics: string[]
  }
  example_texts: string[]
  custom_fields: Record<string, string>
}

export interface ProfileCreate {
  name: string
  taboos?: {
    forbidden_words?: string[]
    forbidden_topics?: string[]
  }
  example_texts?: string[]
  custom_fields?: Record<string, string>
}

// === Project ===
export interface Project {
  id: string
  name: string
  description: string
  creator_profile_id: string
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectListItem {
  id: string
  name: string
  status: string
  created_at: string
}

// === Workflow ===
export interface WorkflowStatus {
  workflow_id: string
  project_id: string
  current_stage: Stage
  waiting_for_input: boolean
  input_prompt: string | null
  clarification_progress: string | null // "2/3"
  ai_call_count: number
  stages: Record<string, StageStatus>
}

export type Stage = 
  | 'intent'
  | 'research' 
  | 'core_design'
  | 'core_production'
  | 'extension'
  | 'completed'

export type StageStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'iterating'

export interface WorkflowStartRequest {
  profile_id: string
  project_name: string
  raw_input: string
}

export interface WorkflowRespondRequest {
  answer: string
}

export interface WorkflowData {
  project: {
    id: string
    name: string
    status: string
  }
  intent: Intent | null
  consumer_research: ConsumerResearch | null
  content_core: ContentCore | null
  content_extension: ContentExtension | null
}

// === Intent ===
export interface Intent {
  id: string
  goal: string
  success_criteria: string[]
  constraints: {
    must_have: string[]
    must_avoid: string[]
  }
  raw_input: string
}

// === Consumer Research ===
export interface Persona {
  id: string
  name: string
  role: string
  background: string
  pain_points: string[]
  desires: string[]
  selected?: boolean
}

export interface ConsumerResearch {
  id: string
  summary: string
  key_pain_points: string[]
  key_desires: string[]
  personas: Persona[]
  // 兼容旧字段
  pain_points?: string[]
  needs?: string[]
  expectations?: string[]
  target_users?: string[]
}

// === Content Core ===
export interface ContentCore {
  id: string
  design_schemes: DesignScheme[]
  selected_scheme_index: number | null
  field_schema_id?: string  // 关联的字段模板ID
  
  // 新的层次结构：章节 -> 字段
  sections: ContentSection[]
  outline_confirmed: boolean
  
  // 向后兼容的扁平字段列表
  fields: ContentField[]
  
  status: string
  
  // 生产进度
  current_section_index?: number
  current_field_index?: number
}

export interface ContentSection {
  id: string
  name: string
  description: string
  order: number
  status: 'pending' | 'in_progress' | 'completed'
  fields: ContentField[]
}

export interface DesignScheme {
  name: string
  type?: string
  description: string
  approach: string
  target_scenario?: string
  key_features?: string[]
  recommended?: boolean
}

export interface ContentField {
  id: string
  name: string
  display_name?: string
  description?: string
  order?: number
  content: string
  status: 'pending' | 'generating' | 'completed' | 'error' | 'failed' | 'review'
  evaluation_score: number | null
  evaluation_feedback?: string
  
  // 依赖关系
  custom_depends_on?: string[]
  custom_dependency_type?: string
  
  // 链式追踪
  chain_id?: string
  is_chain_head?: boolean
  context_stale?: boolean
  
  // 生成前交互
  clarification_answer?: string
}

// 用于目录编辑的请求类型
export interface OutlineSection {
  id: string
  name: string
  description: string
  order: number
  fields: OutlineField[]
}

export interface OutlineField {
  id: string
  name: string
  display_name: string
  description: string
  order: number
}

// === Content Extension ===
export interface ContentExtension {
  id: string
  channels: ChannelContent[]
  status: string
}

export interface ChannelContent {
  channel_name: string
  content: string
  status: string
}

// === Chat ===
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  stage?: Stage
}

// === Settings ===
export interface SystemConfig {
  ai: {
    provider: string
    model: string
    temperature: {
      default: number
      creative: number
      precise: number
    }
  }
  orchestrator: {
    max_loops: number
    alternatives_count: number
  }
}

export interface PromptTemplate {
  name: string
  content: string
}

// === Field Schema ===
export interface FieldDefinition {
  name: string
  description: string
  field_type: string  // text, list, freeform
  required: boolean
  ai_hint: string
  order: number
  depends_on: string[]
  clarification_prompt?: string  // 生成前询问用户的问题
}



