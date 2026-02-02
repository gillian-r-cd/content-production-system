# core/modules/base.py
# 功能：所有业务模块的抽象基类
# 主要类：BaseModule
# 核心能力：定义模块通用接口、依赖注入、上下文管理

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar
from core.ai_client import AIClient, MockAIClient
from core.prompt_engine import PromptEngine, GoldenContextBuilder
from core.context_manager import ContextManager
from core.models import CreatorProfile


T = TypeVar('T')


class BaseModule(ABC):
    """
    所有业务模块的基类
    
    职责：
    - 定义统一的模块接口
    - 管理AI客户端和Prompt引擎依赖
    - 自动注入Golden Context
    - 提供通用的辅助方法
    
    子类需要实现：
    - run(): 执行模块主逻辑
    - get_template_name(): 返回使用的prompt模板名
    """
    
    # 模块名称（子类必须定义）
    name: str = "base_module"
    description: str = "基础模块"
    
    def __init__(
        self,
        ai_client: AIClient | MockAIClient,
        prompt_engine: PromptEngine,
        context_manager: ContextManager,
        creator_profile: Optional[CreatorProfile] = None,
    ):
        """
        初始化模块
        
        Args:
            ai_client: AI客户端（真实或Mock）
            prompt_engine: Prompt引擎
            context_manager: 上下文管理器
            creator_profile: 创作者特质（可选，也可从context_manager获取）
        """
        self.ai_client = ai_client
        self.prompt_engine = prompt_engine
        self.context_manager = context_manager
        self.creator_profile = creator_profile or context_manager.creator_profile
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> T:
        """
        执行模块主逻辑
        
        Args:
            input_data: 模块输入数据
            
        Returns:
            模块输出数据（类型由子类定义）
        """
        pass
    
    @abstractmethod
    def get_template_name(self) -> str:
        """
        返回使用的prompt模板名
        
        Returns:
            模板文件名（如 intent_analyzer.md.j2）
        """
        pass
    
    def build_golden_context(self) -> Dict[str, Any]:
        """
        构建Golden Context
        
        Returns:
            Golden Context数据
        """
        return self.context_manager.update_golden_context()
    
    def build_prompt(
        self, 
        context: Dict[str, Any],
        template_name: Optional[str] = None,
    ) -> str:
        """
        构建完整的prompt
        
        Args:
            context: 当前阶段的上下文数据
            template_name: 模板名（默认使用get_template_name()）
            
        Returns:
            渲染后的prompt
        """
        template = template_name or self.get_template_name()
        golden = self.build_golden_context()
        
        return self.prompt_engine.render(
            template,
            context,
            golden_context=golden,
        )
    
    def call_ai(
        self,
        system_prompt: str,
        user_message: str,
        temperature_mode: str = "default",
    ) -> str:
        """
        调用AI
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature_mode: 温度模式
            
        Returns:
            AI响应
        """
        return self.ai_client.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature_mode=temperature_mode,
        )
    
    def call_ai_structured(
        self,
        system_prompt: str,
        user_message: str,
        output_format: str = "yaml",
    ) -> Dict[str, Any]:
        """
        调用AI并解析结构化输出
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            output_format: 输出格式（yaml/json）
            
        Returns:
            解析后的字典
        """
        return self.ai_client.chat_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            output_format=output_format,
        )
    
    def log(self, message: str, level: str = "info") -> None:
        """
        日志输出（简单实现，后续可扩展）
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        print(f"[{self.name}] [{level.upper()}] {message}")


class ModuleResult:
    """
    模块执行结果封装
    
    用于统一返回格式，包含成功/失败状态、数据、错误信息等。
    """
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        needs_input: bool = False,
        input_prompt: Optional[str] = None,
    ):
        """
        初始化结果
        
        Args:
            success: 是否成功
            data: 结果数据
            error: 错误信息（如果失败）
            needs_input: 是否需要用户输入
            input_prompt: 如果需要输入，提示用户的问题
        """
        self.success = success
        self.data = data
        self.error = error
        self.needs_input = needs_input
        self.input_prompt = input_prompt
    
    def __bool__(self) -> bool:
        return self.success
    
    @classmethod
    def ok(cls, data: Any) -> 'ModuleResult':
        """成功结果"""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'ModuleResult':
        """失败结果"""
        return cls(success=False, error=error)
    
    @classmethod
    def need_input(cls, prompt: str) -> 'ModuleResult':
        """需要用户输入"""
        return cls(success=True, needs_input=True, input_prompt=prompt)



