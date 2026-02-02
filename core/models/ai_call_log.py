# core/models/ai_call_log.py
# AI调用日志模型
# 功能：记录每次AI调用的完整信息，用于调试和优化
# 支持：持久化到项目目录，每次打开项目都能加载历史日志

from __future__ import annotations

import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import BaseModel


# 存储根目录
STORAGE_ROOT = Path(__file__).parent.parent.parent / "storage" / "projects"


def generate_log_id() -> str:
    """生成日志ID"""
    return f"log_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"


class AICallLog(BaseModel):
    """AI调用日志"""
    
    # 覆盖父类的id字段，使用默认工厂
    id: str = Field(default_factory=generate_log_id, description="日志ID")
    
    project_id: Optional[str] = None
    stage: str = ""  # intent, research, core, extension, simulator
    
    # 时间信息
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: int = 0
    
    # 输入
    system_prompt: str = ""
    user_message: str = ""
    full_prompt: str = ""  # 渲染后的完整prompt（包含所有变量替换）
    
    # 输出
    response: str = ""
    response_structured: Optional[dict] = None  # 结构化响应（如果有）
    
    # 元信息
    model: str = ""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    tokens_input: int = 0
    tokens_output: int = 0
    
    # 状态
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于保存"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "stage": self.stage,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "system_prompt": self.system_prompt,
            "user_message": self.user_message,
            "full_prompt": self.full_prompt,
            "response": self.response,
            "model": self.model,
            "temperature": self.temperature,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "success": self.success,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AICallLog:
        """从字典创建"""
        # 处理 timestamp
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class AICallLogStore:
    """AI调用日志存储（内存 + 文件持久化）"""
    
    _instance: Optional['AICallLogStore'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logs: List[AICallLog] = []
            cls._instance._loaded_projects: set = set()  # 已加载日志的项目
        return cls._instance
    
    def _get_log_file(self, project_id: str) -> Path:
        """获取项目的日志文件路径"""
        return STORAGE_ROOT / project_id / "ai_logs.yaml"
    
    def _save_project_logs(self, project_id: str) -> None:
        """保存项目日志到文件"""
        if not project_id:
            return
        
        log_file = self._get_log_file(project_id)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 获取该项目的所有日志
        project_logs = [log for log in self._logs if log.project_id == project_id]
        
        # 保存为 YAML
        logs_data = [log.to_dict() for log in project_logs]
        with open(log_file, 'w', encoding='utf-8') as f:
            yaml.dump(logs_data, f, allow_unicode=True, default_flow_style=False)
    
    def load_project_logs(self, project_id: str) -> None:
        """加载项目的历史日志"""
        if not project_id or project_id in self._loaded_projects:
            return
        
        log_file = self._get_log_file(project_id)
        if not log_file.exists():
            self._loaded_projects.add(project_id)
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs_data = yaml.safe_load(f) or []
            
            # 加载日志（避免重复）
            existing_ids = {log.id for log in self._logs}
            for log_data in logs_data:
                if log_data.get("id") not in existing_ids:
                    log = AICallLog.from_dict(log_data)
                    self._logs.append(log)
            
            self._loaded_projects.add(project_id)
        except Exception as e:
            print(f"加载项目日志失败: {e}")
    
    def add(self, log: AICallLog) -> None:
        """添加日志（自动持久化）"""
        self._logs.append(log)
        
        # 保持最近1000条
        if len(self._logs) > 1000:
            self._logs = self._logs[-1000:]
        
        # 持久化到项目文件
        if log.project_id:
            self._save_project_logs(log.project_id)
    
    def get_by_project(self, project_id: str) -> List[AICallLog]:
        """按项目ID获取日志"""
        # 先加载项目历史日志
        self.load_project_logs(project_id)
        return [log for log in self._logs if log.project_id == project_id]
    
    def get_recent(self, limit: int = 50) -> List[AICallLog]:
        """获取最近的日志"""
        return self._logs[-limit:][::-1]  # 倒序，最新的在前
    
    def get_all(self) -> List[AICallLog]:
        """获取所有日志"""
        return self._logs[::-1]
    
    def clear(self) -> None:
        """清空内存中的日志（不删除文件）"""
        self._logs = []
        self._loaded_projects = set()


# 全局单例
log_store = AICallLogStore()

