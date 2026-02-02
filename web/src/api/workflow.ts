// web/src/api/workflow.ts
// Workflow API调用
// 功能：工作流管理（核心API）

import apiClient from './client'
import type { 
  WorkflowStatus, 
  WorkflowStartRequest, 
  WorkflowRespondRequest,
  WorkflowData 
} from '@/types'

export const workflowApi = {
  start: async (request: WorkflowStartRequest): Promise<{ workflow_id: string; project_id: string; project?: any; status: WorkflowStatus }> => {
    const { data } = await apiClient.post('/workflow/start', request)
    return data
  },

  respond: async (workflowId: string, request: WorkflowRespondRequest): Promise<WorkflowStatus> => {
    const { data } = await apiClient.post(`/workflow/${workflowId}/respond`, request)
    return data
  },

  getStatus: async (workflowId: string): Promise<WorkflowStatus> => {
    const { data } = await apiClient.get(`/workflow/${workflowId}/status`)
    return data
  },

  getData: async (workflowId: string): Promise<WorkflowData> => {
    const { data } = await apiClient.get(`/workflow/${workflowId}/data`)
    return data
  },

  continue: async (workflowId: string): Promise<WorkflowStatus> => {
    const { data } = await apiClient.post(`/workflow/${workflowId}/continue`)
    return data
  },
}


