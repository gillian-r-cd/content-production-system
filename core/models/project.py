# core/models/project.py
# 功能：项目模型，作为整个内容生产的容器
# 主要类：Project
# 核心设计：关联所有阶段的数据，管理项目状态

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import BaseModel


class Project(BaseModel):
    """
    项目容器
    
    项目是整个内容生产的顶层容器，关联：
    - CreatorProfile（创作者特质）
    - FieldSchema（内容品类定义）
    - Intent（意图分析结果）
    - ConsumerResearch（消费者调研）
    - ContentCore（内涵生产）
    - ContentExtension（外延生产）
    - Reports（报告）
    """
    
    # ===== 基本信息 =====
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(default=None, description="项目描述")
    
    # ===== 深度模式 =====
    depth: Literal["light", "standard", "deep"] = Field(
        default="standard",
        description="模块深度：light=快速, standard=标准, deep=深度"
    )
    
    # ===== 关联配置 =====
    creator_profile_id: str = Field(..., description="关联的CreatorProfile ID")
    field_schema_id: Optional[str] = Field(
        default=None, 
        description="关联的FieldSchema ID（用户自定义品类）"
    )
    
    # ===== 阶段数据引用 =====
    # 这些ID指向存储在项目目录下的具体数据文件
    intent_id: Optional[str] = Field(default=None, description="意图分析结果ID")
    consumer_research_id: Optional[str] = Field(default=None, description="消费者调研结果ID")
    content_core_id: Optional[str] = Field(default=None, description="内涵生产结果ID")
    content_extension_id: Optional[str] = Field(default=None, description="外延生产结果ID")
    
    # ===== 项目状态 =====
    status: Literal["draft", "intent", "research", "core_design", "core_production", "extension", "completed", "archived"] = Field(
        default="draft",
        description="项目当前阶段"
    )
    
    # ===== 报告 =====
    process_report_id: Optional[str] = Field(default=None, description="流程报告ID")
    quality_report_id: Optional[str] = Field(default=None, description="质量报告ID")
    
    # ===== 配置覆盖（可选）=====
    # 允许项目级别覆盖全局配置
    config_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="项目级配置覆盖"
    )
    
    # ===== 对话历史 =====
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="与AI的对话历史"
    )
    
    def add_message(self, role: str, content: str, stage: Optional[str] = None) -> None:
        """添加对话消息"""
        from datetime import datetime
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if stage:
            msg["stage"] = stage
        self.conversation_history.append(msg)
    
    def get_stage_display_name(self) -> str:
        """获取当前阶段的显示名称"""
        stage_names = {
            "draft": "草稿",
            "intent": "意图分析",
            "research": "消费者调研",
            "core_design": "内涵设计",
            "core_production": "内涵生产",
            "extension": "外延生产",
            "completed": "已完成",
            "archived": "已归档",
        }
        return stage_names.get(self.status, self.status)
    
    def get_next_stage(self) -> Optional[str]:
        """获取下一个阶段"""
        stage_order = [
            "draft", "intent", "research", 
            "core_design", "core_production", 
            "extension", "completed"
        ]
        try:
            current_index = stage_order.index(self.status)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass
        return None
    
    def advance_stage(self) -> bool:
        """
        推进到下一阶段
        
        Returns:
            bool: 是否成功推进
        """
        next_stage = self.get_next_stage()
        if next_stage:
            self.status = next_stage
            return True
        return False
    
    def get_storage_path(self, base_path: str) -> str:
        """
        获取项目数据存储路径
        
        Args:
            base_path: 存储根路径
            
        Returns:
            str: 项目目录路径
        """
        from pathlib import Path
        return str(Path(base_path) / "projects" / self.id)


