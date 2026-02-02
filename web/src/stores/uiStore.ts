// web/src/stores/uiStore.ts
// UI状态管理
// 功能：侧边栏折叠、当前视图、弹窗状态等

import { create } from 'zustand'

interface UIState {
  // 侧边栏
  leftPanelCollapsed: boolean
  rightPanelCollapsed: boolean
  
  // 设置弹窗
  settingsOpen: boolean
  
  // 当前选中的阶段（用于左侧高亮）
  selectedStage: string | null
  
  // Actions
  toggleLeftPanel: () => void
  toggleRightPanel: () => void
  setSettingsOpen: (open: boolean) => void
  setSelectedStage: (stage: string | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  leftPanelCollapsed: false,
  rightPanelCollapsed: false,
  settingsOpen: false,
  selectedStage: null,

  toggleLeftPanel: () => {
    set((state) => ({ leftPanelCollapsed: !state.leftPanelCollapsed }))
  },

  toggleRightPanel: () => {
    set((state) => ({ rightPanelCollapsed: !state.rightPanelCollapsed }))
  },

  setSettingsOpen: (open) => {
    set({ settingsOpen: open })
  },

  setSelectedStage: (stage) => {
    set({ selectedStage: stage })
  },
}))



