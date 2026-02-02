# core/models/creator_profile.py
# 功能：创作者特质模型，定义创作者的风格约束
# 主要类：CreatorProfile, Taboos
# 核心设计：允许用户完全自定义字段，系统只提供基础容器

from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import BaseModel


class Taboos(BaseModel):
    """
    禁忌配置
    
    定义创作者绝对不能触碰的内容，这是硬性约束。
    """
    id: str = Field(default="taboos", description="固定ID")
    forbidden_words: List[str] = Field(default_factory=list, description="禁用词汇")
    forbidden_topics: List[str] = Field(default_factory=list, description="禁碰话题")
    forbidden_patterns: List[str] = Field(default_factory=list, description="禁用表达模式")


class CreatorProfile(BaseModel):
    """
    创作者特质
    
    设计原则：
    - 允许用户完全自定义字段
    - 系统只强制要求 example_texts 和 taboos
    - custom_fields 可以添加任意 key-value
    
    使用方式：
    - 不同创作者关注的维度完全不同
    - 有人重视调性，有人重视结构，有人重视节奏
    - 预设字段会限制用户，不如让用户自己定义
    """
    
    # 基础信息
    name: str = Field(..., description="创作者名称/昵称")
    description: Optional[str] = Field(default=None, description="创作者简介")
    
    # ===== 必填：范例文本（最核心的约束）=====
    example_texts: List[str] = Field(
        default_factory=list, 
        description="创作者的典型文本，用于few-shot学习风格"
    )
    
    # ===== 必填：禁忌（硬性约束）=====
    taboos: Taboos = Field(
        default_factory=lambda: Taboos(id="taboos"),
        description="禁止事项"
    )
    
    # ===== 可选：自定义字段（用户完全自由定义）=====
    # 用户可以添加任意字段，系统会自动注入到prompt中
    # 示例：
    #   调性: "口语化、略带幽默"
    #   立场: "务实主义，不说大话"
    #   口头禅: ["说白了就是", "你品，你细品"]
    #   写作习惯: "喜欢用短句，每段不超过3行"
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="用户自定义的特质字段"
    )
    
    def add_custom_field(self, key: str, value: Any) -> None:
        """添加自定义字段"""
        self.custom_fields[key] = value
    
    def remove_custom_field(self, key: str) -> None:
        """移除自定义字段"""
        if key in self.custom_fields:
            del self.custom_fields[key]
    
    def get_all_constraints(self) -> Dict[str, Any]:
        """
        获取所有约束（用于注入prompt）
        
        Returns:
            dict: 包含所有约束信息的字典
        """
        return {
            "name": self.name,
            "example_texts": self.example_texts,
            "taboos": {
                "forbidden_words": self.taboos.forbidden_words,
                "forbidden_topics": self.taboos.forbidden_topics,
                "forbidden_patterns": self.taboos.forbidden_patterns,
            },
            "custom_fields": self.custom_fields,
        }
    
    def format_for_prompt(self) -> str:
        """
        格式化为可注入prompt的文本
        
        Returns:
            str: 格式化后的创作者特质描述
        """
        lines = [f"创作者：{self.name}"]
        
        # 禁忌
        if self.taboos.forbidden_words:
            lines.append(f"\n禁用词汇：{', '.join(self.taboos.forbidden_words)}")
        if self.taboos.forbidden_topics:
            lines.append(f"禁碰话题：{', '.join(self.taboos.forbidden_topics)}")
        if self.taboos.forbidden_patterns:
            lines.append(f"禁用模式：{', '.join(self.taboos.forbidden_patterns)}")
        
        # 自定义字段
        if self.custom_fields:
            lines.append("\n创作者特质：")
            for key, value in self.custom_fields.items():
                if isinstance(value, list):
                    lines.append(f"- {key}：{', '.join(str(v) for v in value)}")
                else:
                    lines.append(f"- {key}：{value}")
        
        # 范例文本
        if self.example_texts:
            lines.append("\n参考范例（模仿风格）：")
            for i, text in enumerate(self.example_texts, 1):
                lines.append(f"---范例{i}---")
                lines.append(text)
        
        return "\n".join(lines)



