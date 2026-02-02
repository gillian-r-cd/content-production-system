// web/src/components/settings/SettingsNav.tsx
// 设置左侧导航
// 功能：导航项列表、当前选中高亮

import { 
  Settings, 
  User, 
  FileText, 
  MessageSquare, 
  Gauge, 
  Share2, 
  Database,
  Bug
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SettingsTab } from './SettingsDialog'

interface NavItem {
  id: SettingsTab
  label: string
  icon: React.ComponentType<{ className?: string }>
}

const NAV_ITEMS: NavItem[] = [
  { id: 'project', label: '项目设置', icon: Settings },
  { id: 'profiles', label: '创作者特质', icon: User },
  { id: 'schemas', label: '字段模板', icon: FileText },
  { id: 'prompts', label: '系统提示词', icon: MessageSquare },
  { id: 'simulators', label: '评估器', icon: Gauge },
  { id: 'channels', label: '渠道管理', icon: Share2 },
  { id: 'data', label: '数据管理', icon: Database },
  { id: 'debug', label: '调试日志', icon: Bug },
]

interface SettingsNavProps {
  activeTab: SettingsTab
  onTabChange: (tab: SettingsTab) => void
}

export default function SettingsNav({ activeTab, onTabChange }: SettingsNavProps) {
  return (
    <nav className="p-4 space-y-1">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon
        const isActive = activeTab === item.id
        
        return (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md text-left transition-colors",
              isActive 
                ? "bg-primary text-primary-foreground" 
                : "hover:bg-accent text-foreground"
            )}
          >
            <Icon className="w-4 h-4" />
            <span className="text-sm">{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}

