# core/prompt_engine.py
# 功能：Prompt模板加载和渲染引擎
# 主要类：PromptEngine
# 核心能力：Jinja2模板渲染、CreatorProfile动态注入、GoldenContext自动构建

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape, Undefined


class PromptEngine:
    """
    Prompt模板引擎
    
    核心职责：
    1. 加载和管理Jinja2模板
    2. 动态注入CreatorProfile和用户自定义字段
    3. 构建GoldenContext并自动注入
    4. 支持@引用语法解析（简化版）
    
    设计原则：
    - 用户定义的任何字段，都能自动注入到prompt中，无需修改代码
    - GoldenContext每次调用必须注入
    """
    
    def __init__(self, templates_dir: str | Path):
        """
        初始化Prompt引擎
        
        Args:
            templates_dir: 模板目录路径
        """
        self.templates_dir = Path(templates_dir)
        
        # 确保目录存在
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            # 允许未定义变量（返回空字符串而非报错）
            undefined=_SilentUndefined,
        )
        
        # 注册自定义过滤器
        self._register_filters()
    
    def _register_filters(self) -> None:
        """注册自定义Jinja2过滤器"""
        
        def format_list(value: List[str], separator: str = ", ") -> str:
            """列表格式化为字符串"""
            if isinstance(value, list):
                return separator.join(str(v) for v in value)
            return str(value)
        
        def format_dict(value: Dict[str, Any], prefix: str = "- ") -> str:
            """字典格式化为多行字符串"""
            if isinstance(value, dict):
                lines = []
                for k, v in value.items():
                    if isinstance(v, list):
                        lines.append(f"{prefix}{k}：{', '.join(str(i) for i in v)}")
                    else:
                        lines.append(f"{prefix}{k}：{v}")
                return "\n".join(lines)
            return str(value)
        
        def format_golden_context(golden: Dict[str, Any]) -> str:
            """格式化Golden Context为prompt文本"""
            return GoldenContextBuilder.format_for_system_prompt(golden)
        
        self.env.filters['format_list'] = format_list
        self.env.filters['format_dict'] = format_dict
        self.env.filters['format_golden_context'] = format_golden_context
    
    def load_template(self, template_name: str) -> Template:
        """
        加载模板
        
        Args:
            template_name: 模板文件名（如 intent_analyzer.md.j2）
            
        Returns:
            Jinja2 Template对象
        """
        return self.env.get_template(template_name)
    
    def render(
        self, 
        template_name: str, 
        context: Dict[str, Any],
        golden_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板文件名
            context: 渲染上下文（当前阶段的数据）
            golden_context: 黄金上下文（必须注入的核心信息）
            
        Returns:
            渲染后的字符串
        """
        template = self.load_template(template_name)
        
        # 合并上下文
        full_context = {}
        
        # 先注入golden_context（优先级低，可被覆盖）
        if golden_context:
            full_context['golden'] = golden_context
        
        # 再注入当前阶段的context
        full_context.update(context)
        
        return template.render(**full_context)
    
    def render_string(
        self, 
        template_string: str, 
        context: Dict[str, Any],
        golden_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        从字符串渲染模板
        
        用于用户自定义的prompt模板。
        
        Args:
            template_string: 模板字符串
            context: 渲染上下文
            golden_context: 黄金上下文
            
        Returns:
            渲染后的字符串
        """
        template = self.env.from_string(template_string)
        
        full_context = {}
        if golden_context:
            full_context['golden'] = golden_context
        full_context.update(context)
        
        return template.render(**full_context)
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return self.env.list_templates()


class GoldenContextBuilder:
    """
    GoldenContext构建器
    
    Golden Context = 每次LLM调用必须注入的核心信息
    
    包含：
    1. 创作者特质（禁忌、范例、自定义字段）
    2. 核心意图（目标、成功标准）
    3. 目标用户画像（从消费者调研提取）
    """
    
    @staticmethod
    def build(
        creator_profile: Optional[Any] = None,  # CreatorProfile
        intent: Optional[Any] = None,           # Intent
        consumer_research: Optional[Any] = None, # ConsumerResearch
    ) -> Dict[str, Any]:
        """
        构建Golden Context
        
        Args:
            creator_profile: 创作者特质
            intent: 意图分析结果
            consumer_research: 消费者调研结果
            
        Returns:
            dict: Golden Context数据
        """
        golden = {
            "creator_constraints": {},
            "core_intent": {},
            "target_user": {},
        }
        
        # 1. 创作者约束
        if creator_profile:
            golden["creator_constraints"] = {
                "name": creator_profile.name,
                "taboos": {
                    "forbidden_words": creator_profile.taboos.forbidden_words,
                    "forbidden_topics": creator_profile.taboos.forbidden_topics,
                    "forbidden_patterns": getattr(creator_profile.taboos, 'forbidden_patterns', []),
                },
                "voice_examples": creator_profile.example_texts,
                "custom_fields": creator_profile.custom_fields,
            }
        
        # 2. 核心意图
        if intent:
            golden["core_intent"] = intent.get_golden_context_part()
        
        # 3. 目标用户
        if consumer_research:
            golden["target_user"] = consumer_research.get_golden_context_part()
        
        return golden
    
    @staticmethod
    def format_for_system_prompt(golden: Dict[str, Any]) -> str:
        """
        将Golden Context格式化为可注入system prompt的文本
        
        Args:
            golden: Golden Context数据
            
        Returns:
            str: 格式化后的文本
        """
        lines = ["## 全局约束（每次生成必须遵守）"]
        
        # 创作者约束
        constraints = golden.get("creator_constraints", {})
        if constraints:
            if constraints.get("name"):
                lines.append(f"\n### 创作者：{constraints['name']}")
            
            taboos = constraints.get("taboos", {})
            if taboos.get("forbidden_words"):
                lines.append(f"\n🚫 禁用词汇：{', '.join(taboos['forbidden_words'])}")
            if taboos.get("forbidden_topics"):
                lines.append(f"🚫 禁碰话题：{', '.join(taboos['forbidden_topics'])}")
            
            custom_fields = constraints.get("custom_fields", {})
            if custom_fields:
                lines.append("\n### 创作者特质")
                for key, value in custom_fields.items():
                    if isinstance(value, list):
                        lines.append(f"- {key}：{', '.join(str(v) for v in value)}")
                    else:
                        lines.append(f"- {key}：{value}")
            
            examples = constraints.get("voice_examples", [])
            if examples:
                lines.append("\n### 风格参考范例")
                for i, example in enumerate(examples[:2], 1):  # 只取前2个
                    lines.append(f"---范例{i}---")
                    lines.append(example[:500])  # 限制长度
        
        # 核心意图
        intent = golden.get("core_intent", {})
        if intent:
            lines.append("\n### 核心意图")
            if intent.get("goal"):
                lines.append(f"目标：{intent['goal']}")
            if intent.get("success_criteria"):
                lines.append(f"成功标准：{', '.join(intent['success_criteria'])}")
            if intent.get("must_have"):
                lines.append(f"必须包含：{', '.join(intent['must_have'])}")
            if intent.get("must_avoid"):
                lines.append(f"必须避免：{', '.join(intent['must_avoid'])}")
        
        # 目标用户
        user = golden.get("target_user", {})
        if user:
            lines.append("\n### 目标用户")
            if user.get("persona_summary"):
                lines.append(f"画像：{user['persona_summary']}")
            if user.get("key_pain_points"):
                lines.append(f"核心痛点：{', '.join(user['key_pain_points'])}")
            if user.get("key_desires"):
                lines.append(f"核心期望：{', '.join(user['key_desires'])}")
        
        return "\n".join(lines)


class _SilentUndefined(Undefined):
    """
    静默的Undefined类
    
    当模板引用不存在的变量时，返回空字符串而非报错。
    这样用户可以在模板中使用可选字段。
    """
    
    def __str__(self):
        return ""
    
    def __repr__(self):
        return ""
    
    def __bool__(self):
        return False
    
    def __iter__(self):
        return iter([])
    
    def __getattr__(self, name):
        return _SilentUndefined()
    
    def __call__(self, *args, **kwargs):
        return _SilentUndefined()
    
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ""

