// web/src/api/profiles.ts
// Profile API调用
// 功能：创作者特质CRUD

import apiClient from './client'
import type { Profile, ProfileCreate } from '@/types'

export const profilesApi = {
  list: async (): Promise<Profile[]> => {
    const { data } = await apiClient.get('/profiles')
    // 后端可能返回 { profiles: [...] } 或直接返回数组
    return Array.isArray(data) ? data : (data.profiles || data || [])
  },

  get: async (id: string): Promise<Profile> => {
    const { data } = await apiClient.get(`/profiles/${id}`)
    return data
  },

  create: async (profile: ProfileCreate): Promise<Profile> => {
    const { data } = await apiClient.post('/profiles', profile)
    return data
  },

  update: async (id: string, profile: ProfileCreate): Promise<Profile> => {
    const { data } = await apiClient.put(`/profiles/${id}`, profile)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/profiles/${id}`)
  },
}

