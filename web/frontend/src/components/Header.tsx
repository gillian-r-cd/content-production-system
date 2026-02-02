import { Settings, HelpCircle } from 'lucide-react'
import './Header.css'

interface HeaderProps {
  projectName: string
  profileName: string
  onSettingsClick: () => void
  profiles: Array<{ id: string; name: string }>
  onProfileChange: (id: string) => void
}

export function Header({ 
  projectName, 
  profileName, 
  onSettingsClick,
  profiles,
  onProfileChange,
}: HeaderProps) {
  return (
    <header className="header">
      <div className="header-left">
        <h1 className="project-name">{projectName}</h1>
      </div>
      
      <div className="header-center">
        <select 
          className="profile-select"
          value={profiles.find(p => p.name === profileName)?.id || ''}
          onChange={(e) => onProfileChange(e.target.value)}
        >
          {profiles.length === 0 && (
            <option value="">未选择创作者</option>
          )}
          {profiles.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>
      
      <div className="header-right">
        <button className="icon-btn" onClick={onSettingsClick} title="设置">
          <Settings size={20} />
        </button>
        <button className="icon-btn" title="帮助">
          <HelpCircle size={20} />
        </button>
      </div>
    </header>
  )
}

