# core/models/content_core.py
# 功能：内涵生产模型，管理核心内容的完整生产
# 主要类：ContentField, ContentCore
# 核心理念：内涵=核心内容的完整生产（如：整套课程素材）

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import BaseModel


class ContentField(BaseModel):
    """
    单个内容字段的生产结果
    
    对应FieldSchema中定义的每个字段。
    """
    id: str = Field(default="", description="字段ID")
    
    # 字段信息（来自FieldSchema）
    name: str = Field(..., description="字段名")
    
    # 生产状态
    status: Literal["pending", "generating", "review", "completed", "failed"] = Field(
        default="pending",
        description="字段状态"
    )
    
    # 生产结果
    content: Optional[str] = Field(default=None, description="生成的内容")
    alternatives: List[str] = Field(
        default_factory=list, 
        description="备选方案（如果生成了多个）"
    )
    
    # 评估结果
    evaluation_score: Optional[float] = Field(default=None, description="评估分数")
    evaluation_feedback: Optional[str] = Field(default=None, description="评估反馈")
    
    # 迭代历史
    iteration_count: int = Field(default=0, description="迭代次数")
    iteration_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="迭代历史"
    )
    
    def add_iteration(self, content: str, feedback: str, score: float) -> None:
        """记录一次迭代"""
        self.iteration_history.append({
            "iteration": self.iteration_count,
            "content": content,
            "feedback": feedback,
            "score": score,
        })
        self.iteration_count += 1


class ContentCore(BaseModel):
    """
    内涵生产结果
    
    设计原则：
    - 内涵=核心内容的完整生产
    - 按照用户定义的FieldSchema逐字段生产
    - 每个字段可以独立迭代优化
    
    工作流程：
    1. 先生成多个整体方案供选择
    2. 选择一个方案后，逐字段详细生产
    3. 每个字段可以独立评估和迭代
    4. 全部字段完成后，整体评估
    """
    
    # 关联信息
    project_id: str = Field(..., description="所属项目ID")
    field_schema_id: str = Field(..., description="使用的FieldSchema ID")
    
    # ===== 阶段1：方案选择 =====
    design_schemes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="生成的设计方案列表（供用户选择）"
    )
    selected_scheme_index: Optional[int] = Field(
        default=None,
        description="用户选择的方案索引"
    )
    
    # ===== 阶段2：逐字段生产 =====
    fields: List[ContentField] = Field(
        default_factory=list,
        description="各字段的生产结果"
    )
    
    # ===== 整体状态 =====
    status: Literal["scheme_generation", "scheme_selection", "field_production", "evaluation", "completed"] = Field(
        default="scheme_generation",
        description="当前阶段"
    )
    
    # ===== 整体评估 =====
    overall_score: Optional[float] = Field(default=None, description="整体评估分数")
    overall_feedback: Optional[str] = Field(default=None, description="整体评估反馈")
    
    def get_field(self, field_name: str) -> Optional[ContentField]:
        """获取指定字段"""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def get_completed_fields(self) -> List[ContentField]:
        """获取已完成的字段"""
        return [f for f in self.fields if f.status == "completed"]
    
    def get_pending_fields(self) -> List[ContentField]:
        """获取待处理的字段"""
        return [f for f in self.fields if f.status == "pending"]
    
    def is_all_fields_completed(self) -> bool:
        """检查是否所有字段都已完成"""
        return all(f.status == "completed" for f in self.fields)
    
    def format_for_prompt(self) -> str:
        """
        格式化为可注入prompt的文本
        返回已完成字段的内容
        """
        lines = ["【已完成的内容】"]
        
        for field in self.get_completed_fields():
            lines.append(f"\n## {field.name}")
            lines.append(field.content or "")
        
        return "\n".join(lines)
    
    def get_content_dict(self) -> Dict[str, str]:
        """
        获取所有字段内容的字典形式
        """
        return {
            field.name: field.content or ""
            for field in self.fields
            if field.content
        }



