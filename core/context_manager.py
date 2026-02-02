# core/context_manager.py
# 功能：上下文管理器，处理@引用解析和阶段上下文
# 主要类：ContextManager
# 核心能力：解析@引用语法、管理阶段上下文、保证一致性

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Reference:
    """
    引用对象
    
    表示用户在对话中引用的一段上下文。
    """
    ref_type: str           # "stage" | "field" | "golden"
    stage: Optional[str]    # 阶段名（如：意图分析、内涵生产）
    field: Optional[str]    # 字段名（如：课程目标）
    content: str            # 引用的实际内容
    display_name: str       # 显示名称


class ContextManager:
    """
    上下文管理器
    
    核心职责：
    1. 管理项目各阶段的上下文数据
    2. 解析@引用语法
    3. 构建和维护Golden Context
    4. 支持按阶段索引的上下文查询
    
    引用语法：
    - @意图分析        引用意图分析的完整产出
    - @消费者调研      引用消费者调研的完整产出
    - @内涵.课程目标   引用内涵中的特定字段
    - @外延.介绍页     引用外延中的特定渠道
    - @全局约束        引用Golden Context
    """
    
    # 阶段别名映射
    STAGE_ALIASES = {
        "意图分析": "intent",
        "意图": "intent",
        "intent": "intent",
        "消费者调研": "consumer_research",
        "调研": "consumer_research",
        "用户画像": "consumer_research",
        "research": "consumer_research",
        "内涵": "content_core",
        "内涵生产": "content_core",
        "core": "content_core",
        "外延": "content_extension",
        "外延生产": "content_extension",
        "extension": "content_extension",
    }
    
    # Golden Context别名
    GOLDEN_ALIASES = {
        "全局约束": "all",
        "创作者特质": "creator",
        "创作者": "creator",
        "用户画像": "user",
        "目标用户": "user",
    }
    
    def __init__(self):
        """初始化上下文管理器"""
        # 各阶段的上下文数据
        self.stages: Dict[str, Any] = {
            "intent": None,
            "consumer_research": None,
            "content_core": None,
            "content_extension": None,
        }
        
        # Golden Context
        self.golden_context: Optional[Dict[str, Any]] = None
        
        # 创作者特质（用于Golden Context）
        self.creator_profile: Optional[Any] = None
    
    def set_stage_context(self, stage: str, data: Any) -> None:
        """
        设置阶段上下文
        
        Args:
            stage: 阶段名（intent, consumer_research, content_core, content_extension）
            data: 阶段数据
        """
        if stage in self.stages:
            self.stages[stage] = data
    
    def get_stage_context(self, stage: str) -> Optional[Any]:
        """
        获取阶段上下文
        
        Args:
            stage: 阶段名
            
        Returns:
            阶段数据
        """
        return self.stages.get(stage)
    
    def set_creator_profile(self, profile: Any) -> None:
        """设置创作者特质"""
        self.creator_profile = profile
    
    def update_golden_context(self) -> Dict[str, Any]:
        """
        更新Golden Context
        
        基于当前的创作者特质、意图、调研数据构建。
        
        Returns:
            更新后的Golden Context
        """
        from core.prompt_engine import GoldenContextBuilder
        
        self.golden_context = GoldenContextBuilder.build(
            creator_profile=self.creator_profile,
            intent=self.stages.get("intent"),
            consumer_research=self.stages.get("consumer_research"),
        )
        return self.golden_context
    
    def parse_references(self, text: str) -> List[Reference]:
        """
        解析文本中的@引用
        
        Args:
            text: 包含@引用的文本
            
        Returns:
            List[Reference]: 解析出的引用列表
        """
        references = []
        
        # 匹配 @xxx 或 @xxx.yyy
        pattern = r'@([\u4e00-\u9fa5\w]+)(?:\.([\u4e00-\u9fa5\w]+))?'
        matches = re.findall(pattern, text)
        
        for stage_or_type, field in matches:
            ref = self._resolve_reference(stage_or_type, field)
            if ref:
                references.append(ref)
        
        return references
    
    def _resolve_reference(
        self, 
        stage_or_type: str, 
        field: Optional[str]
    ) -> Optional[Reference]:
        """
        解析单个引用
        
        Args:
            stage_or_type: 阶段名或类型
            field: 字段名（可选）
            
        Returns:
            Reference 或 None
        """
        # 检查是否是Golden Context引用
        if stage_or_type in self.GOLDEN_ALIASES:
            return self._resolve_golden_reference(stage_or_type)
        
        # 检查是否是阶段引用
        stage_key = self.STAGE_ALIASES.get(stage_or_type)
        if stage_key:
            if field:
                return self._resolve_field_reference(stage_key, field)
            else:
                return self._resolve_stage_reference(stage_key, stage_or_type)
        
        return None
    
    def _resolve_stage_reference(
        self, 
        stage_key: str, 
        display_name: str
    ) -> Optional[Reference]:
        """解析阶段级引用"""
        stage_data = self.stages.get(stage_key)
        if not stage_data:
            return Reference(
                ref_type="stage",
                stage=stage_key,
                field=None,
                content="[该阶段尚未完成]",
                display_name=display_name,
            )
        
        # 获取格式化内容
        content = stage_data.format_for_prompt() if hasattr(stage_data, 'format_for_prompt') else str(stage_data)
        
        return Reference(
            ref_type="stage",
            stage=stage_key,
            field=None,
            content=content,
            display_name=display_name,
        )
    
    def _resolve_field_reference(
        self, 
        stage_key: str, 
        field_name: str
    ) -> Optional[Reference]:
        """解析字段级引用"""
        stage_data = self.stages.get(stage_key)
        if not stage_data:
            return Reference(
                ref_type="field",
                stage=stage_key,
                field=field_name,
                content="[该阶段尚未完成]",
                display_name=f"{stage_key}.{field_name}",
            )
        
        # 尝试获取字段内容
        content = "[字段未找到]"
        
        if stage_key == "content_core" and hasattr(stage_data, 'get_field'):
            field = stage_data.get_field(field_name)
            if field and field.content:
                content = field.content
        elif stage_key == "content_extension" and hasattr(stage_data, 'get_channel'):
            channel = stage_data.get_channel(field_name)
            if channel and channel.content:
                content = channel.content
        
        return Reference(
            ref_type="field",
            stage=stage_key,
            field=field_name,
            content=content,
            display_name=f"{stage_key}.{field_name}",
        )
    
    def _resolve_golden_reference(self, alias: str) -> Reference:
        """解析Golden Context引用"""
        from core.prompt_engine import GoldenContextBuilder
        
        if not self.golden_context:
            self.update_golden_context()
        
        content = GoldenContextBuilder.format_for_system_prompt(self.golden_context or {})
        
        return Reference(
            ref_type="golden",
            stage=None,
            field=None,
            content=content,
            display_name=alias,
        )
    
    def inject_references(self, text: str) -> str:
        """
        将文本中的@引用替换为实际内容
        
        Args:
            text: 包含@引用的文本
            
        Returns:
            替换后的文本
        """
        references = self.parse_references(text)
        
        for ref in references:
            # 构建原始引用文本
            if ref.field:
                original = f"@{ref.display_name}"
            else:
                original = f"@{ref.display_name}"
            
            # 替换为实际内容
            replacement = f"\n---引用：{ref.display_name}---\n{ref.content}\n---引用结束---\n"
            text = text.replace(original, replacement, 1)
        
        return text
    
    def get_available_references(self) -> Dict[str, List[str]]:
        """
        获取当前可用的引用列表
        
        用于UI提示用户可以引用什么。
        
        Returns:
            dict: 按类型分组的引用列表
        """
        available = {
            "stages": [],
            "fields": [],
            "golden": ["@全局约束", "@创作者特质", "@目标用户"],
        }
        
        # 阶段引用
        stage_display = {
            "intent": "意图分析",
            "consumer_research": "消费者调研",
            "content_core": "内涵",
            "content_extension": "外延",
        }
        
        for key, display in stage_display.items():
            if self.stages.get(key):
                available["stages"].append(f"@{display}")
        
        # 字段引用（内涵）
        core = self.stages.get("content_core")
        if core and hasattr(core, 'fields'):
            for field in core.fields:
                if field.content:
                    available["fields"].append(f"@内涵.{field.name}")
        
        # 渠道引用（外延）
        ext = self.stages.get("content_extension")
        if ext and hasattr(ext, 'channels'):
            for channel in ext.channels:
                if channel.content:
                    available["fields"].append(f"@外延.{channel.channel_name}")
        
        return available



