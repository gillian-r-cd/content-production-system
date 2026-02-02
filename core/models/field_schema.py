# core/models/field_schema.py
# 功能：字段Schema模型，定义用户自定义的内容品类和字段结构
# 主要类：FieldDefinition, FieldSchema
# 核心设计：用户从零开始定义内容品类和字段，系统只提供模板库作为参考

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import BaseModel


class FieldDefinition(BaseModel):
    """
    单个字段的定义
    
    用户用这个结构定义内容的每个组成部分。
    支持字段依赖和生成顺序控制，类似小型工作流。
    """
    id: str = Field(default="", description="字段ID（自动生成）")
    
    # 字段基本信息
    name: str = Field(..., description="字段名（用户自定义）")
    description: str = Field(default="", description="字段说明（用于UI提示和AI理解）")
    
    # 字段类型
    type: Literal["text", "list", "freeform"] = Field(
        default="text", 
        description="字段类型：text=单段文本, list=列表, freeform=自由格式"
    )
    
    # 是否必填
    required: bool = Field(default=True, description="是否必填")
    
    # AI生成提示（核心！每个字段独立的提示词）
    ai_hint: str = Field(
        default="", 
        description="给AI的生成提示（帮助AI更好地生成该字段）"
    )
    
    # 示例值（可选）
    example: Optional[Any] = Field(default=None, description="示例值")
    
    # === 工作流控制 ===
    order: int = Field(
        default=0, 
        description="生成顺序（数字越小越先生成）"
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="依赖的字段名列表（这些字段的内容会作为上下文注入）"
    )


class FieldSchema(BaseModel):
    """
    字段Schema
    
    设计原则：
    - 用户从零开始定义内容品类和字段
    - 系统只提供模板库作为参考
    - 每个创作者可以积累自己的品类库
    
    创建方式：
    1. 从零开始：用户逐个添加字段
    2. 基于模板：复制模板后修改
    3. AI辅助：描述需求让AI建议结构
    """
    
    # 基本信息
    name: str = Field(..., description="Schema名称（用户自定义）")
    description: str = Field(default="", description="Schema用途说明")
    
    # 字段列表
    fields: List[FieldDefinition] = Field(
        default_factory=list,
        description="字段定义列表"
    )
    
    # 模板相关
    based_on_template: Optional[str] = Field(
        default=None, 
        description="如果从模板创建，记录来源模板ID"
    )
    is_template: bool = Field(
        default=False, 
        description="是否作为模板供他人使用"
    )
    
    # 分类标签
    category: Optional[str] = Field(
        default=None, 
        description="分类（如：education, marketing, storytelling）"
    )
    tags: List[str] = Field(default_factory=list, description="标签")
    
    def add_field(self, field: FieldDefinition) -> None:
        """添加字段"""
        # 自动生成field ID
        if not field.id:
            field.id = f"field_{len(self.fields) + 1}"
        self.fields.append(field)
    
    def remove_field(self, field_name: str) -> bool:
        """移除字段"""
        for i, field in enumerate(self.fields):
            if field.name == field_name:
                self.fields.pop(i)
                return True
        return False
    
    def get_field(self, field_name: str) -> Optional[FieldDefinition]:
        """获取字段定义"""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def get_required_fields(self) -> List[FieldDefinition]:
        """获取所有必填字段"""
        return [f for f in self.fields if f.required]
    
    def get_field_names(self) -> List[str]:
        """获取所有字段名"""
        return [f.name for f in self.fields]
    
    def get_ordered_fields(self) -> List[FieldDefinition]:
        """按生成顺序获取字段列表"""
        return sorted(self.fields, key=lambda f: (f.order, self.fields.index(f)))
    
    def format_for_prompt(self) -> str:
        """
        格式化为可注入prompt的文本
        
        Returns:
            str: 格式化后的字段结构描述
        """
        lines = [f"内容结构：{self.name}"]
        if self.description:
            lines.append(f"说明：{self.description}")
        
        lines.append("\n需要生成的字段：")
        for field in self.fields:
            required_mark = "【必填】" if field.required else "【选填】"
            lines.append(f"\n{field.name} {required_mark}")
            if field.description:
                lines.append(f"  说明：{field.description}")
            if field.ai_hint:
                lines.append(f"  生成提示：{field.ai_hint}")
            if field.example:
                lines.append(f"  示例：{field.example}")
        
        return "\n".join(lines)


def create_default_field_schema() -> FieldSchema:
    """
    创建默认的内容字段Schema
    
    用于没有指定具体品类时的通用内容生产。
    基于docs/field_schemas.md中的设计理念。
    """
    schema = FieldSchema(
        id="default_content",
        name="通用内容",
        description="适用于大多数内容生产场景的通用字段结构",
        category="general",
    )
    
    # 添加核心字段
    schema.add_field(FieldDefinition(
        name="标题",
        description="内容的核心标题，要吸引目标用户注意力",
        type="text",
        required=True,
        ai_hint="简洁有力，突出价值点，15字以内为佳",
    ))
    
    schema.add_field(FieldDefinition(
        name="大纲",
        description="内容的整体结构和主要模块",
        type="list",
        required=True,
        ai_hint="按逻辑顺序排列，每个条目是一个内容模块",
    ))
    
    schema.add_field(FieldDefinition(
        name="正文",
        description="内容的主体部分，详细展开各个模块",
        type="freeform",
        required=True,
        ai_hint="围绕大纲展开，保持创作者风格，注意节奏感",
    ))
    
    schema.add_field(FieldDefinition(
        name="摘要",
        description="内容的精华总结，用于预览或分享",
        type="text",
        required=True,
        ai_hint="100字以内，突出核心价值和亮点",
    ))
    
    return schema

