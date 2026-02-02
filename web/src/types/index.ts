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
export interface ConsumerResearch {
  id: string
  summary: string
  key_pain_points: string[]
  key_desires: string[]
}

// === Content Core ===
export interface ContentCore {
  id: string
  design_schemes: DesignScheme[]
  selected_scheme_index: number | null
  fields: ContentField[]
  status: string
}

export interface DesignScheme {
  name: string
  description: string
  approach: string
}

export interface ContentField {
  name: string
  content: string
  status: string
  evaluation_score: number | null
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



