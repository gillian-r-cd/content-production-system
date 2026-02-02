# core/models/report.py
# 功能：报告模型，包括流程报告和质量报告
# 主要类：ProcessReport, QualityReport
# 核心设计：两种报告——流程进度+内容质量

from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
from pydantic import Field
from .base import BaseModel


class StageStatus(BaseModel):
    """
    单个阶段的状态
    """
    id: str = Field(default="", description="阶段ID")
    
    name: str = Field(..., description="阶段名称")
    status: Literal["pending", "in_progress", "completed", "blocked", "skipped"] = Field(
        ..., 
        description="状态"
    )
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    
    # 阻塞信息
    blocked_reason: Optional[str] = Field(default=None, description="阻塞原因")
    blocked_since: Optional[datetime] = Field(default=None, description="阻塞开始时间")
    
    # 迭代信息
    iteration_count: int = Field(default=0, description="迭代次数")
    
    def duration_seconds(self) -> Optional[int]:
        """计算阶段耗时（秒）"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None


class ProcessReport(BaseModel):
    """
    流程进度报告
    
    关注：项目整体进度、各阶段状态、卡点分析
    """
    
    # 关联信息
    project_id: str = Field(..., description="所属项目ID")
    
    # ===== 整体状态 =====
    overall_status: Literal["not_started", "in_progress", "completed", "blocked"] = Field(
        default="not_started",
        description="整体状态"
    )
    overall_progress: float = Field(default=0.0, description="整体进度（0-100）")
    
    # ===== 各阶段状态 =====
    stages: List[StageStatus] = Field(
        default_factory=list,
        description="各阶段状态"
    )
    
    # ===== 卡点分析 =====
    current_blockers: List[str] = Field(
        default_factory=list,
        description="当前卡点"
    )
    blocker_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="历史卡点记录"
    )
    
    # ===== 时间统计 =====
    total_duration_seconds: Optional[int] = Field(
        default=None, 
        description="总耗时（秒）"
    )
    ai_call_count: int = Field(default=0, description="AI调用次数")
    total_tokens_used: int = Field(default=0, description="总token消耗")
    
    def get_current_stage(self) -> Optional[StageStatus]:
        """获取当前进行中的阶段"""
        for stage in self.stages:
            if stage.status == "in_progress":
                return stage
        return None
    
    def get_blocked_stages(self) -> List[StageStatus]:
        """获取被阻塞的阶段"""
        return [s for s in self.stages if s.status == "blocked"]


class QualityReport(BaseModel):
    """
    内容质量报告
    
    关注：内容质量评估、各维度得分、改进建议
    """
    
    # 关联信息
    project_id: str = Field(..., description="所属项目ID")
    
    # ===== 整体质量 =====
    overall_score: float = Field(default=0.0, description="整体质量分（0-10）")
    quality_level: Literal["excellent", "good", "acceptable", "needs_improvement", "poor"] = Field(
        default="needs_improvement",
        description="质量等级"
    )
    
    # ===== 各维度评估 =====
    dimension_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="各评估维度得分"
    )
    
    # ===== 各阶段产出质量 =====
    stage_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="各阶段产出的质量分"
    )
    
    # ===== 问题汇总 =====
    total_issues: int = Field(default=0, description="问题总数")
    critical_issues: int = Field(default=0, description="严重问题数")
    major_issues: int = Field(default=0, description="主要问题数")
    
    issue_summary: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="问题汇总"
    )
    
    # ===== 改进建议 =====
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="改进建议"
    )
    
    # ===== 符合度检查 =====
    intent_alignment: Optional[float] = Field(
        default=None, 
        description="与意图的对齐度（0-100）"
    )
    style_consistency: Optional[float] = Field(
        default=None, 
        description="风格一致性（0-100）"
    )
    taboo_violations: List[str] = Field(
        default_factory=list,
        description="触犯的禁忌"
    )
    
    def format_summary(self) -> str:
        """生成报告摘要"""
        lines = [
            f"整体质量：{self.overall_score}/10 ({self.quality_level})",
            f"问题统计：{self.critical_issues}个严重 / {self.major_issues}个主要 / {self.total_issues}个总计",
        ]
        
        if self.intent_alignment is not None:
            lines.append(f"意图对齐度：{self.intent_alignment}%")
        
        if self.style_consistency is not None:
            lines.append(f"风格一致性：{self.style_consistency}%")
        
        if self.taboo_violations:
            lines.append(f"禁忌违规：{', '.join(self.taboo_violations)}")
        
        if self.improvement_suggestions:
            lines.append("\n改进建议：")
            for suggestion in self.improvement_suggestions[:3]:
                lines.append(f"- {suggestion}")
        
        return "\n".join(lines)



