# core/models/content_extension.py
# 功能：外延生产模型，管理营销触达内容的生产
# 主要类：ChannelContent, ContentExtension
# 核心理念：外延=营销触达内容，可以在任何时候开始（只要价值点清晰）

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import BaseModel


class ChannelContent(BaseModel):
    """
    单个渠道的内容
    
    每个渠道（如：介绍页、小红书、邮件）有独立的内容和状态。
    """
    id: str = Field(default="", description="渠道内容ID")
    
    # 渠道信息
    channel_name: str = Field(..., description="渠道名称")
    channel_description: Optional[str] = Field(default=None, description="渠道说明")
    
    # 渠道特定的字段schema（可选）
    field_schema_id: Optional[str] = Field(
        default=None, 
        description="该渠道使用的FieldSchema ID（如果有特定结构）"
    )
    
    # 生产状态
    status: Literal["pending", "generating", "review", "completed", "failed"] = Field(
        default="pending",
        description="状态"
    )
    
    # 生产结果
    content: Optional[str] = Field(default=None, description="生成的内容")
    content_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="结构化的内容字段（如果有FieldSchema）"
    )
    
    # 评估结果
    evaluation_score: Optional[float] = Field(default=None, description="评估分数")
    evaluation_feedback: Optional[str] = Field(default=None, description="评估反馈")
    
    # 迭代
    iteration_count: int = Field(default=0, description="迭代次数")


class ContentExtension(BaseModel):
    """
    外延生产结果
    
    设计原则：
    - 外延=营销触达内容（介绍页、推广文案、社媒内容等）
    - 可以在任何时候开始，只要价值点清晰
    - 基于内涵（ContentCore）的核心价值点来生产
    
    工作流程：
    1. 用户选择要生产哪些渠道的内容
    2. 系统基于内涵的核心价值点，为每个渠道生成内容
    3. Simulator评估每个渠道的内容
    4. 迭代优化直到满足标准
    """
    
    # 关联信息
    project_id: str = Field(..., description="所属项目ID")
    content_core_id: Optional[str] = Field(
        default=None, 
        description="关联的内涵ID（如果有）"
    )
    
    # ===== 核心价值点（可独立于ContentCore存在）=====
    # 如果ContentCore还没完成，用户可以先定义价值点
    value_points: List[str] = Field(
        default_factory=list,
        description="核心价值点列表"
    )
    
    # ===== 渠道内容 =====
    channels: List[ChannelContent] = Field(
        default_factory=list,
        description="各渠道的内容"
    )
    
    # ===== 整体状态 =====
    status: Literal["pending", "in_progress", "completed"] = Field(
        default="pending",
        description="整体状态"
    )
    
    def add_channel(self, channel_name: str, description: str = None) -> ChannelContent:
        """添加渠道"""
        channel = ChannelContent(
            id=f"channel_{len(self.channels) + 1}",
            channel_name=channel_name,
            channel_description=description
        )
        self.channels.append(channel)
        return channel
    
    def get_channel(self, channel_name: str) -> Optional[ChannelContent]:
        """获取指定渠道"""
        for channel in self.channels:
            if channel.channel_name == channel_name:
                return channel
        return None
    
    def get_completed_channels(self) -> List[ChannelContent]:
        """获取已完成的渠道"""
        return [c for c in self.channels if c.status == "completed"]
    
    def is_all_channels_completed(self) -> bool:
        """检查是否所有渠道都已完成"""
        return all(c.status == "completed" for c in self.channels)
    
    def format_for_prompt(self) -> str:
        """
        格式化为可注入prompt的文本
        """
        lines = ["【外延内容概览】"]
        
        if self.value_points:
            lines.append("\n核心价值点：")
            for vp in self.value_points:
                lines.append(f"- {vp}")
        
        completed = self.get_completed_channels()
        if completed:
            lines.append("\n已完成的渠道：")
            for channel in completed:
                lines.append(f"\n## {channel.channel_name}")
                lines.append(channel.content or "")
        
        return "\n".join(lines)



