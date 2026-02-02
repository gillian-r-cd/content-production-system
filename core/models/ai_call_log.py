# core/models/ai_call_log.py
# AI调用日志模型
# 功能：记录每次AI调用的完整信息，用于调试和优化

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import Field

from .base import BaseModel


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


class AICallLogStore:
    """AI调用日志存储（内存 + 文件）"""
    
    _instance: Optional['AICallLogStore'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logs: List[AICallLog] = []
        return cls._instance
    
    def add(self, log: AICallLog) -> None:
        """添加日志"""
        self._logs.append(log)
        # 保持最近1000条
        if len(self._logs) > 1000:
            self._logs = self._logs[-1000:]
    
    def get_by_project(self, project_id: str) -> List[AICallLog]:
        """按项目ID获取日志"""
        return [log for log in self._logs if log.project_id == project_id]
    
    def get_recent(self, limit: int = 50) -> List[AICallLog]:
        """获取最近的日志"""
        return self._logs[-limit:][::-1]  # 倒序，最新的在前
    
    def get_all(self) -> List[AICallLog]:
        """获取所有日志"""
        return self._logs[::-1]
    
    def clear(self) -> None:
        """清空日志"""
        self._logs = []


# 全局单例
log_store = AICallLogStore()

