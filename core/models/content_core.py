# core/models/content_core.py
# 功能：内涵生产模型，管理核心内容的完整生产
# 主要类：ContentField, ContentSection, ContentCore
# 核心理念：内涵=核心内容的完整生产（如：整套课程素材）
# 结构：一级标题(Section) -> 二级字段(Field)，支持多组字段并行

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import BaseModel
import uuid


class ContentField(BaseModel):
    """
    单个内容字段的生产结果
    
    对应FieldSchema中定义的每个字段。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="字段ID")
    
    # 字段信息（来自FieldSchema）
    name: str = Field(..., description="字段名")
    display_name: str = Field(default="", description="显示名称")
    description: str = Field(default="", description="字段说明")
    order: int = Field(default=0, description="排序顺序")
    
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
    
    # 依赖关系（场景级别覆盖）
    custom_depends_on: Optional[List[str]] = Field(
        default=None,
        description="场景级别的依赖配置（覆盖模板默认值）"
    )
    custom_dependency_type: Optional[str] = Field(
        default=None,
        description="场景级别的依赖类型（覆盖模板默认值）"
    )
    
    # 链式追踪
    chain_id: Optional[str] = Field(default=None, description="所属链条ID")
    is_chain_head: bool = Field(default=False, description="是否是链条头部")
    
    # 上下文过期标记
    context_stale: bool = Field(default=False, description="上下文是否过期")
    
    # 生成前交互
    clarification_answer: Optional[str] = Field(
        default=None,
        description="用户对澄清问题的回答（用于生成时注入）"
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


class ContentSection(BaseModel):
    """
    内容章节（一级标题）
    
    用于组织字段，支持多组字段并行存在于一个内容中。
    例如：一个课程可能有多个章节，每个章节下有自己的一组字段。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="章节ID")
    name: str = Field(..., description="章节名称（一级标题）")
    description: str = Field(default="", description="章节说明")
    order: int = Field(default=0, description="排序顺序")
    
    # 该章节下的字段列表
    fields: List[ContentField] = Field(
        default_factory=list,
        description="章节下的字段列表"
    )
    
    # 章节状态
    status: Literal["pending", "in_progress", "completed"] = Field(
        default="pending",
        description="章节状态"
    )
    
    def get_field(self, field_id: str) -> Optional[ContentField]:
        """获取指定字段"""
        for field in self.fields:
            if field.id == field_id or field.name == field_id:
                return field
        return None
    
    def get_completed_count(self) -> int:
        """获取已完成字段数"""
        return len([f for f in self.fields if f.status == "completed"])
    
    def get_total_count(self) -> int:
        """获取字段总数"""
        return len(self.fields)
    
    def is_completed(self) -> bool:
        """检查章节是否全部完成"""
        return all(f.status == "completed" for f in self.fields) if self.fields else False


class ContentCore(BaseModel):
    """
    内涵生产结果
    
    设计原则：
    - 内涵=核心内容的完整生产
    - 支持一级标题(Section) + 二级字段(Field)的层次结构
    - 每个字段可以独立迭代优化
    
    工作流程：
    1. 先生成多个整体方案供选择
    2. 选择方案后，编辑和确认目录结构（sections + fields）
    3. 确认目录后，逐字段详细生产
    4. 每个字段可以独立评估和迭代
    5. 全部字段完成后，整体评估
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
    
    # ===== 阶段2：目录结构（一级标题+二级字段）=====
    sections: List[ContentSection] = Field(
        default_factory=list,
        description="内容章节列表（一级标题）"
    )
    outline_confirmed: bool = Field(
        default=False,
        description="目录结构是否已确认（确认后才能开始生产）"
    )
    
    # ===== 向后兼容：扁平字段列表 =====
    fields: List[ContentField] = Field(
        default_factory=list,
        description="各字段的生产结果（向后兼容，推荐使用sections）"
    )
    
    # ===== 整体状态 =====
    status: Literal[
        "scheme_generation",    # 方案生成中
        "scheme_selection",     # 等待选择方案
        "outline_editing",      # 目录编辑中
        "outline_confirmed",    # 目录已确认，等待开始生产
        "field_production",     # 字段生产中
        "evaluation",           # 整体评估中
        "completed"             # 全部完成
    ] = Field(
        default="scheme_generation",
        description="当前阶段"
    )
    
    # ===== 生产进度 =====
    current_section_index: int = Field(default=0, description="当前生产的章节索引")
    current_field_index: int = Field(default=0, description="当前生产的字段索引")
    
    # ===== 整体评估 =====
    overall_score: Optional[float] = Field(default=None, description="整体评估分数")
    overall_feedback: Optional[str] = Field(default=None, description="整体评估反馈")
    
    def get_section(self, section_id: str) -> Optional[ContentSection]:
        """获取指定章节"""
        for section in self.sections:
            if section.id == section_id or section.name == section_id:
                return section
        return None
    
    def get_field(self, field_name: str) -> Optional[ContentField]:
        """获取指定字段（优先从sections中查找，向后兼容fields）"""
        # 先从sections中查找
        for section in self.sections:
            for field in section.fields:
                if field.name == field_name or field.id == field_name:
                    return field
        # 向后兼容：从扁平fields中查找
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def get_all_fields(self) -> List[ContentField]:
        """获取所有字段（优先从sections中获取）"""
        if self.sections:
            all_fields = []
            for section in self.sections:
                all_fields.extend(section.fields)
            return all_fields
        return self.fields
    
    def get_completed_fields(self) -> List[ContentField]:
        """获取已完成的字段"""
        return [f for f in self.get_all_fields() if f.status == "completed"]
    
    def get_pending_fields(self) -> List[ContentField]:
        """获取待处理的字段"""
        return [f for f in self.get_all_fields() if f.status == "pending"]
    
    def is_all_fields_completed(self) -> bool:
        """检查是否所有字段都已完成"""
        all_fields = self.get_all_fields()
        return all(f.status == "completed" for f in all_fields) if all_fields else False
    
    def get_total_field_count(self) -> int:
        """获取总字段数"""
        return len(self.get_all_fields())
    
    def get_completed_field_count(self) -> int:
        """获取已完成字段数"""
        return len(self.get_completed_fields())
    
    def get_progress_percentage(self) -> float:
        """获取生产进度百分比"""
        total = self.get_total_field_count()
        if total == 0:
            return 0.0
        return (self.get_completed_field_count() / total) * 100
    
    def format_for_prompt(self) -> str:
        """
        格式化为可注入prompt的文本
        返回已完成字段的内容
        """
        lines = ["【已完成的内容】"]
        
        if self.sections:
            for section in self.sections:
                section_completed = [f for f in section.fields if f.status == "completed"]
                if section_completed:
                    lines.append(f"\n# {section.name}")
                    for field in section_completed:
                        lines.append(f"\n## {field.display_name or field.name}")
                        lines.append(field.content or "")
        else:
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
            for field in self.get_all_fields()
            if field.content
        }
    
    def initialize_default_sections(self, field_schema=None) -> None:
        """
        根据FieldSchema初始化默认的章节结构
        如果没有schema，创建一个默认章节
        """
        if field_schema and hasattr(field_schema, 'fields'):
            # 将所有字段放入一个默认章节
            default_section = ContentSection(
                id="main",
                name="主要内容",
                order=0,
                fields=[
                    ContentField(
                        id=f.id if hasattr(f, 'id') else f.name,
                        name=f.name,
                        display_name=getattr(f, 'display_name', f.name),
                        description=getattr(f, 'description', ''),
                        order=i,
                        status="pending",
                    )
                    for i, f in enumerate(field_schema.get_ordered_fields())
                ]
            )
            self.sections = [default_section]
        else:
            # 创建默认章节和字段
            self.sections = [
                ContentSection(
                    id="main",
                    name="主要内容",
                    order=0,
                    fields=[
                        ContentField(id="title", name="title", display_name="标题", order=0),
                        ContentField(id="outline", name="outline", display_name="大纲", order=1),
                        ContentField(id="content", name="content", display_name="正文", order=2),
                        ContentField(id="summary", name="summary", display_name="摘要", order=3),
                    ]
                )
            ]



