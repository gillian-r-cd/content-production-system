# core/models/consumer_research.py
# 功能：消费者调研结果模型
# 主要类：ConsumerResearch
# 核心设计：支持三种输入方式（AI生成、用户粘贴、混合）

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import BaseModel


class StructuredResearch(BaseModel):
    """
    结构化调研数据
    
    建议结构，用户可以只填部分，也可以完全不填。
    """
    id: str = Field(default="structured", description="固定ID")
    
    persona: Optional[str] = Field(default=None, description="用户画像描述（自由格式）")
    pain_points: Optional[str] = Field(default=None, description="痛点（自由格式）")
    goals: Optional[str] = Field(default=None, description="目标/期望（自由格式）")
    context: Optional[str] = Field(default=None, description="使用场景/上下文（自由格式）")


class ConsumerResearch(BaseModel):
    """
    消费者调研结果
    
    设计原则：支持三种输入方式，用户选择最适合的。
    
    方式1：直接粘贴（raw_text）
        - 用户已有调研报告、用户访谈、竞品分析
        - 直接粘贴，系统原样传给AI
        - 最快，适合有积累的用户
    
    方式2：AI辅助生成（structured）
        - 用户描述目标用户是谁
        - AI生成结构化画像
        - 用户确认或修改
    
    方式3：混合模式
        - 粘贴部分已有资料
        - AI补充缺失的部分
    """
    
    # 关联项目
    project_id: str = Field(..., description="所属项目ID")
    
    # ===== 来源标记 =====
    source: Literal["ai_generated", "user_pasted", "hybrid"] = Field(
        default="ai_generated",
        description="数据来源"
    )
    
    # ===== 方式1：自由文本（用户直接粘贴）=====
    raw_text: Optional[str] = Field(
        default=None, 
        description="用户直接粘贴的调研资料"
    )
    
    # ===== 方式2：结构化字段 =====
    structured: StructuredResearch = Field(
        default_factory=lambda: StructuredResearch(id="structured"),
        description="结构化调研数据"
    )
    
    # ===== 方式3：自定义字段 =====
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="用户自定义的调研字段"
    )
    
    # ===== 摘要（用于Golden Context）=====
    summary: Optional[str] = Field(
        default=None,
        description="一句话用户画像摘要"
    )
    key_pain_points: List[str] = Field(
        default_factory=list,
        description="核心痛点列表"
    )
    key_desires: List[str] = Field(
        default_factory=list,
        description="核心期望列表"
    )
    
    # ===== 典型用户画像(Personas) =====
    personas: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="典型用户角色列表，每个包含id/name/role/background/pain_points/desires"
    )
    
    def format_for_prompt(self) -> str:
        """
        格式化为可注入prompt的文本
        
        处理逻辑：
        - 如果有raw_text，直接使用
        - 如果有structured，格式化后使用
        - 如果有personas，格式化后使用
        - 合并使用所有可用信息
        """
        parts = []
        
        # 摘要
        if self.summary:
            parts.append(f"【目标用户画像】{self.summary}")
        
        # 粘贴的原始资料
        if self.raw_text:
            parts.append("\n【用户提供的调研资料】")
            parts.append(self.raw_text)
        
        # 典型用户画像(Personas)
        if self.personas:
            parts.append("\n【典型用户角色】")
            for p in self.personas:
                parts.append(f"\n▸ {p.get('name', '未命名')}（{p.get('role', '用户')}）")
                if p.get('background'):
                    parts.append(f"  背景：{p.get('background')}")
                if p.get('pain_points'):
                    pain_points = p.get('pain_points', [])
                    if isinstance(pain_points, list):
                        parts.append(f"  痛点：{'; '.join(pain_points[:3])}")
                if p.get('desires'):
                    desires = p.get('desires', [])
                    if isinstance(desires, list):
                        parts.append(f"  期望：{'; '.join(desires[:3])}")
        
        # 核心痛点和期望
        if self.key_pain_points:
            parts.append(f"\n【核心痛点】{', '.join(self.key_pain_points)}")
        if self.key_desires:
            parts.append(f"\n【核心期望】{', '.join(self.key_desires)}")
        
        # 结构化数据（如果有额外的）
        structured_parts = []
        if self.structured.persona and not self.summary:
            structured_parts.append(f"用户画像：{self.structured.persona}")
        if self.structured.pain_points:
            structured_parts.append(f"痛点：{self.structured.pain_points}")
        if self.structured.goals:
            structured_parts.append(f"目标/期望：{self.structured.goals}")
        if self.structured.context:
            structured_parts.append(f"使用场景：{self.structured.context}")
        
        if structured_parts:
            parts.append("\n【补充结构化分析】")
            parts.extend(structured_parts)
        
        # 自定义字段
        if self.custom_fields:
            parts.append("\n【补充信息】")
            for key, value in self.custom_fields.items():
                parts.append(f"{key}：{value}")
        
        return "\n".join(parts) if parts else "暂无调研数据"
    
    def get_golden_context_part(self) -> Dict[str, Any]:
        """
        获取用于Golden Context的部分
        """
        return {
            "persona_summary": self.summary or self.structured.persona or "未定义",
            "key_pain_points": self.key_pain_points,
            "key_desires": self.key_desires,
        }


