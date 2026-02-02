// web/src/components/settings/DataSettings.tsx
// 数据管理
// 功能：导出/导入项目数据、清理数据

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Upload, Trash2, FileText, Loader2 } from 'lucide-react'
import apiClient from '@/api/client'

interface StorageStats {
  projects_count: number
  profiles_count: number
  total_files: number
}

export default function DataSettings() {
  const [isExporting, setIsExporting] = useState(false)
  const [exportMessage, setExportMessage] = useState('')

  // 获取存储统计（模拟）
  const { data: stats, isLoading } = useQuery({
    queryKey: ['storage-stats'],
    queryFn: async () => {
      // 从API获取项目和Profile数量
      const [projects, profiles] = await Promise.all([
        apiClient.get('/projects'),
        apiClient.get('/profiles'),
      ])
      return {
        projects_count: Array.isArray(projects.data) ? projects.data.length : 0,
        profiles_count: Array.isArray(profiles.data) ? profiles.data.length : 0,
        total_files: 0,
      } as StorageStats
    },
  })

  const handleExportProjects = async () => {
    setIsExporting(true)
    setExportMessage('')
    
    try {
      // 获取所有项目数据
      const { data: projects } = await apiClient.get('/projects')
      const { data: profiles } = await apiClient.get('/profiles')
      
      const exportData = {
        version: '1.0',
        exported_at: new Date().toISOString(),
        projects: projects,
        profiles: profiles,
      }
      
      // 创建下载
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `content_production_export_${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      setExportMessage('导出成功！')
    } catch (error) {
      setExportMessage('导出失败：' + (error as Error).message)
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      
      // TODO: 实现导入逻辑
      alert('导入功能开发中...\n\n数据预览：\n' + 
        `- 项目数: ${data.projects?.length || 0}\n` +
        `- Profile数: ${data.profiles?.length || 0}`)
      
    } catch (error) {
      alert('导入失败：文件格式错误')
    }
    
    // 清除input
    event.target.value = ''
  }

  return (
    <div className="p-6 space-y-8">
      <h3 className="text-lg font-semibold">数据管理</h3>
      
      {/* 存储统计 */}
      <div className="bg-muted/50 rounded-lg p-6">
        <h4 className="font-medium mb-4">存储统计</h4>
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
        ) : (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <p className="text-2xl font-bold">{stats?.projects_count || 0}</p>
              <p className="text-sm text-muted-foreground">项目</p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <p className="text-2xl font-bold">{stats?.profiles_count || 0}</p>
              <p className="text-sm text-muted-foreground">创作者特质</p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <p className="text-2xl font-bold">本地</p>
              <p className="text-sm text-muted-foreground">存储位置</p>
            </div>
          </div>
        )}
      </div>
      
      {/* 导出 */}
      <div className="border rounded-lg p-6">
        <div className="flex items-start gap-4">
          <Download className="w-6 h-6 text-primary" />
          <div className="flex-1">
            <h4 className="font-medium">导出数据</h4>
            <p className="text-sm text-muted-foreground mt-1">
              导出所有项目和创作者特质数据为JSON文件
            </p>
            <button
              onClick={handleExportProjects}
              disabled={isExporting}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
            >
              {isExporting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              导出全部数据
            </button>
            {exportMessage && (
              <p className="mt-2 text-sm text-success">{exportMessage}</p>
            )}
          </div>
        </div>
      </div>
      
      {/* 导入 */}
      <div className="border rounded-lg p-6">
        <div className="flex items-start gap-4">
          <Upload className="w-6 h-6 text-primary" />
          <div className="flex-1">
            <h4 className="font-medium">导入数据</h4>
            <p className="text-sm text-muted-foreground mt-1">
              从JSON文件导入项目和创作者特质数据
            </p>
            <label className="mt-4 inline-flex px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 cursor-pointer items-center gap-2">
              <Upload className="w-4 h-4" />
              选择文件导入
              <input
                type="file"
                accept=".json"
                onChange={handleImport}
                className="hidden"
              />
            </label>
          </div>
        </div>
      </div>
      
      {/* 清理数据 */}
      <div className="border border-error/20 rounded-lg p-6 bg-error/5">
        <div className="flex items-start gap-4">
          <Trash2 className="w-6 h-6 text-error" />
          <div className="flex-1">
            <h4 className="font-medium text-error">危险区域</h4>
            <p className="text-sm text-muted-foreground mt-1">
              清空所有数据，此操作不可恢复
            </p>
            <button
              onClick={() => {
                if (confirm('确定要清空所有数据吗？此操作不可恢复！')) {
                  alert('清空功能需要后端支持，暂未实现')
                }
              }}
              className="mt-4 px-4 py-2 border border-error text-error rounded-md hover:bg-error/10 flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              清空所有数据
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}



