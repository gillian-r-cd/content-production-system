# core/models/intent.py
# 功能：意图分析结果模型
# 主要类：Intent, IntentConstraints
# 核心理念：捕获用户想要达成的效果和约束条件

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import Field
from .base import BaseModel


class IntentConstraints(BaseModel):
    """
    意图约束条件
    """
    id: str = Field(default="constraints", description="固定ID")
    
    deadline: Optional[datetime] = Field(default=None, description="截止时间")
    budget_tokens: Optional[int] = Field(default=None, description="token预算（影响深度选择）")
    must_have: List[str] = Field(default_factory=list, description="必须包含的元素")
    must_avoid: List[str] = Field(default_factory=list, description="必须避免的元素")


class Intent(BaseModel):
    """
    意图分析结果
    
    核心问题：用户想通过这个内容达成什么效果？
    
    包含：
    - 核心目标
    - 成功标准
    - 约束条件
    - 上下文信息
    """
    
    # 关联项目
    project_id: str = Field(..., description="所属项目ID")
    
    # ===== 核心意图 =====
    goal: str = Field(..., description="这个内容要达成什么效果（一句话）")
    success_criteria: List[str] = Field(
        default_factory=list, 
        description="怎么判断内容成功了（可衡量的标准）"
    )
    
    # ===== 约束条件 =====
    constraints: IntentConstraints = Field(
        default_factory=lambda: IntentConstraints(id="constraints"),
        description="约束条件"
    )
    
    # ===== 上下文信息 =====
    business_background: Optional[str] = Field(
        default=None, 
        description="业务背景（帮助AI理解语境）"
    )
    existing_assets: List[str] = Field(
        default_factory=list, 
        description="已有素材（可复用的内容）"
    )
    competitors: List[str] = Field(
        default_factory=list, 
        description="竞品参考"
    )
    
    # ===== 原始输入 =====
    raw_input: Optional[str] = Field(
        default=None, 
        description="用户的原始输入（用于追溯）"
    )
    clarification_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="追问澄清的对话历史"
    )
    
    def add_clarification(self, question: str, answer: str) -> None:
        """添加追问记录"""
        self.clarification_history.append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })
    
    def format_for_prompt(self) -> str:
        """
        格式化为可注入prompt的文本
        """
        lines = [f"核心目标：{self.goal}"]
        
        if self.success_criteria:
            lines.append(f"成功标准：{', '.join(self.success_criteria)}")
        
        if self.constraints.must_have:
            lines.append(f"必须包含：{', '.join(self.constraints.must_have)}")
        
        if self.constraints.must_avoid:
            lines.append(f"必须避免：{', '.join(self.constraints.must_avoid)}")
        
        if self.business_background:
            lines.append(f"业务背景：{self.business_background}")
        
        return "\n".join(lines)
    
    def get_golden_context_part(self) -> Dict[str, Any]:
        """
        获取用于Golden Context的部分
        """
        return {
            "goal": self.goal,
            "success_criteria": self.success_criteria,
            "must_have": self.constraints.must_have,
            "must_avoid": self.constraints.must_avoid,
        }



