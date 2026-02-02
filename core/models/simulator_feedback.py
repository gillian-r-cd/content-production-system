# core/models/simulator_feedback.py
# 功能：Simulator评估结果模型
# 主要类：Issue, SimulatorFeedback
# 核心设计：用户定义评估维度和提示词

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import BaseModel


class Issue(BaseModel):
    """
    单个问题
    """
    id: str = Field(default="", description="问题ID")
    
    severity: Literal["critical", "major", "minor", "suggestion"] = Field(
        ..., 
        description="严重程度：critical=必须修复, major=应该修复, minor=建议修复, suggestion=锦上添花"
    )
    category: str = Field(..., description="问题分类（用户定义）")
    description: str = Field(..., description="问题描述")
    location: Optional[str] = Field(default=None, description="问题位置（哪个字段/哪段内容）")
    suggestion: Optional[str] = Field(default=None, description="修改建议")


class SimulatorFeedback(BaseModel):
    """
    Simulator评估结果
    
    设计原则：
    - Simulator的评估维度由用户定义
    - 系统只提供执行框架
    - 用户写评估提示词，决定关注什么
    
    评估流程：
    1. 用户在设置中定义Simulator的提示词和评估维度
    2. 系统将内容+提示词发送给AI
    3. AI返回评估结果
    4. 系统解析结果，决定是否需要迭代
    """
    
    # 关联信息
    project_id: str = Field(..., description="所属项目ID")
    target_type: Literal["field", "content_core", "channel", "content_extension"] = Field(
        ..., 
        description="评估目标类型"
    )
    target_id: str = Field(..., description="评估目标ID")
    
    # ===== 评估配置（来自用户定义）=====
    evaluator_id: Optional[str] = Field(
        default=None, 
        description="使用的评估器ID（用户定义的Simulator配置）"
    )
    
    # ===== 评估结果 =====
    score: float = Field(..., description="综合评分（0-10）")
    passed: bool = Field(..., description="是否通过评估")
    
    # 问题列表
    issues: List[Issue] = Field(default_factory=list, description="发现的问题")
    
    # 各维度得分（用户定义的评估维度）
    dimension_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="各评估维度的得分"
    )
    
    # ===== 原始响应 =====
    raw_response: Optional[str] = Field(
        default=None, 
        description="AI的原始评估响应"
    )
    
    # ===== 摘要 =====
    summary: Optional[str] = Field(default=None, description="评估摘要")
    
    def get_critical_issues(self) -> List[Issue]:
        """获取严重问题"""
        return [i for i in self.issues if i.severity == "critical"]
    
    def get_major_issues(self) -> List[Issue]:
        """获取主要问题"""
        return [i for i in self.issues if i.severity == "major"]
    
    def should_iterate(self, max_critical: int = 0, max_major: int = 2) -> bool:
        """
        判断是否需要迭代
        
        Args:
            max_critical: 允许的最大严重问题数
            max_major: 允许的最大主要问题数
            
        Returns:
            bool: 是否需要迭代
        """
        critical_count = len(self.get_critical_issues())
        major_count = len(self.get_major_issues())
        
        return critical_count > max_critical or major_count > max_major
    
    def format_for_iteration(self) -> str:
        """
        格式化为迭代时注入prompt的反馈文本
        """
        lines = [f"上一轮评估得分：{self.score}/10"]
        
        if self.summary:
            lines.append(f"评估摘要：{self.summary}")
        
        critical = self.get_critical_issues()
        if critical:
            lines.append("\n【必须修复的问题】")
            for issue in critical:
                lines.append(f"- {issue.description}")
                if issue.suggestion:
                    lines.append(f"  建议：{issue.suggestion}")
        
        major = self.get_major_issues()
        if major:
            lines.append("\n【应该修复的问题】")
            for issue in major:
                lines.append(f"- {issue.description}")
                if issue.suggestion:
                    lines.append(f"  建议：{issue.suggestion}")
        
        return "\n".join(lines)



