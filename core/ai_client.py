# core/ai_client.py
# 功能：AI API客户端封装
# 主要类：AIClient
# 核心能力：OpenAI API调用、重试机制、响应解析、调用日志

import os
import json
import yaml
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pathlib import Path
from dotenv import load_dotenv

from core.models.ai_call_log import AICallLog, log_store

# 加载环境变量
load_dotenv()

# 修复：空的OPENAI_BASE_URL会导致OpenAI客户端出错
if os.getenv("OPENAI_BASE_URL") == "":
    os.environ.pop("OPENAI_BASE_URL", None)


class AIClient:
    """
    AI API客户端
    
    封装OpenAI API调用，提供：
    - 单轮对话
    - 多轮对话
    - 结构化输出解析
    - 重试机制
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        """
        初始化AI客户端
        
        Args:
            api_key: API密钥（优先级：参数 > 环境变量）
            model: 模型名称（优先级：参数 > 环境变量 > config.yaml）
            base_url: API Base URL（优先级：参数 > 环境变量）
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # API密钥
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到OPENAI_API_KEY。请在.env文件中设置或通过参数传入。")
        
        # 模型
        self.model = (
            model or 
            os.getenv("OPENAI_MODEL") or 
            self.config.get("ai", {}).get("model", "gpt-4")
        )
        
        # Base URL（只有非空值才使用）
        env_base_url = os.getenv("OPENAI_BASE_URL")
        self.base_url = base_url or (env_base_url if env_base_url else None)
        
        # 温度配置
        self.temperatures = self.config.get("ai", {}).get("temperature", {
            "default": 0.7,
            "creative": 0.9,
            "precise": 0.3,
        })
        
        # 初始化OpenAI客户端
        self._init_client()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            # 默认查找项目根目录的config.yaml
            config_path = Path(__file__).parent.parent / "config.yaml"
        else:
            config_path = Path(config_path)
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _init_client(self) -> None:
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            import httpx
            
            # 设置更长的超时时间（180秒）
            timeout = httpx.Timeout(180.0, connect=30.0)
            
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": timeout,
            }
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            self.client = OpenAI(**client_kwargs)
        except ImportError:
            raise ImportError("请安装openai库：pip install openai")
    
    # 当前项目ID（用于日志关联）
    current_project_id: Optional[str] = None
    current_stage: str = ""
    
    def set_context(self, project_id: Optional[str] = None, stage: str = "") -> None:
        """设置当前上下文（用于日志记录）"""
        self.current_project_id = project_id
        self.current_stage = stage
    
    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature_mode: Literal["default", "creative", "precise"] = "default",
    ) -> str:
        """
        单轮对话
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数（直接指定）
            max_tokens: 最大token数
            temperature_mode: 温度模式（使用预设值）
            
        Returns:
            AI响应文本
        """
        if temperature is None:
            temperature = self.temperatures.get(temperature_mode, 0.7)
        
        # 构建API参数（只包含有值的参数）
        api_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
        }
        if max_tokens is not None:
            api_kwargs["max_tokens"] = max_tokens
        
        # 记录开始时间
        start_time = time.time()
        error_msg = None
        response_text = ""
        tokens_input = 0
        tokens_output = 0
        
        try:
            response = self.client.chat.completions.create(**api_kwargs)
            response_text = response.choices[0].message.content or ""
            
            # 获取token使用量
            if hasattr(response, 'usage') and response.usage:
                tokens_input = response.usage.prompt_tokens or 0
                tokens_output = response.usage.completion_tokens or 0
        except Exception as e:
            error_msg = str(e)
            raise
        finally:
            # 记录日志
            duration_ms = int((time.time() - start_time) * 1000)
            log = AICallLog(
                project_id=self.current_project_id,
                stage=self.current_stage,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                system_prompt=system_prompt,
                user_message=user_message,
                full_prompt=f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_message}",
                response=response_text,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                success=error_msg is None,
                error=error_msg,
            )
            log_store.add(log)
        
        return response_text
    
    def chat_with_history(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        temperature_mode: Literal["default", "creative", "precise"] = "default",
    ) -> str:
        """
        多轮对话
        
        Args:
            system_prompt: 系统提示词
            messages: 对话历史，格式：[{"role": "user/assistant", "content": "..."}]
            temperature: 温度参数
            temperature_mode: 温度模式
            
        Returns:
            AI响应文本
        """
        if temperature is None:
            temperature = self.temperatures.get(temperature_mode, 0.7)
        
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    
    def chat_structured(
        self,
        system_prompt: str,
        user_message: str,
        output_format: Literal["yaml", "json"] = "yaml",
        temperature_mode: Literal["default", "creative", "precise"] = "precise",
    ) -> Dict[str, Any]:
        """
        结构化输出对话
        
        自动在提示词中添加格式要求，并解析响应。
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            output_format: 输出格式（yaml更易读，json更严格）
            temperature_mode: 温度模式
            
        Returns:
            解析后的字典
        """
        # 添加格式要求
        format_instruction = f"\n\n请严格按照{output_format.upper()}格式输出结果，不要包含任何其他内容。"
        enhanced_prompt = system_prompt + format_instruction
        
        # 调用API
        response = self.chat(
            system_prompt=enhanced_prompt,
            user_message=user_message,
            temperature_mode=temperature_mode,
        )
        
        # 解析响应
        return self._parse_structured_response(response, output_format)
    
    def _parse_structured_response(
        self, 
        response: str, 
        output_format: str
    ) -> Dict[str, Any]:
        """
        解析结构化响应
        
        尝试提取和解析YAML或JSON内容。
        """
        # 清理响应
        content = response.strip()
        
        # 尝试提取代码块
        if "```" in content:
            # 提取代码块内容
            import re
            pattern = r'```(?:yaml|json)?\s*(.*?)```'
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                content = matches[0].strip()
        
        # 解析
        try:
            if output_format == "yaml":
                return yaml.safe_load(content)
            else:
                return json.loads(content)
        except Exception as e:
            # 解析失败，返回原始内容
            return {"raw_response": response, "parse_error": str(e)}
    
    def generate_alternatives(
        self,
        system_prompt: str,
        user_message: str,
        count: int = 3,
        temperature: float = 0.9,
    ) -> List[str]:
        """
        生成多个备选方案
        
        用于方案选择阶段，生成多个差异化的选项。
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            count: 生成数量
            temperature: 温度（高温度增加多样性）
            
        Returns:
            备选方案列表
        """
        # 添加多样性要求
        enhanced_prompt = system_prompt + f"\n\n请生成{count}个差异化的方案，用'---方案分隔---'分开。"
        
        response = self.chat(
            system_prompt=enhanced_prompt,
            user_message=user_message,
            temperature=temperature,
        )
        
        # 分割方案
        alternatives = response.split("---方案分隔---")
        return [alt.strip() for alt in alternatives if alt.strip()]


class MockAIClient:
    """
    模拟AI客户端（用于测试）
    
    不实际调用API，返回预设的响应。
    """
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """
        初始化Mock客户端
        
        Args:
            responses: 预设响应，键为请求内容的一部分，值为响应
        """
        self.responses = responses or {}
        self.model = "mock-model"
        self.call_history: List[Dict[str, Any]] = []
    
    def chat(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> str:
        """模拟单轮对话"""
        self.call_history.append({
            "system_prompt": system_prompt,
            "user_message": user_message,
            "kwargs": kwargs,
        })
        
        # 查找匹配的预设响应
        for key, response in self.responses.items():
            if key in user_message or key in system_prompt:
                return response
        
        return f"[Mock Response] 收到消息：{user_message[:100]}..."
    
    def chat_with_history(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """模拟多轮对话"""
        self.call_history.append({
            "system_prompt": system_prompt,
            "messages": messages,
            "kwargs": kwargs,
        })
        
        last_message = messages[-1]["content"] if messages else ""
        return self.chat(system_prompt, last_message, **kwargs)
    
    def chat_structured(
        self,
        system_prompt: str,
        user_message: str,
        output_format: str = "yaml",
        **kwargs
    ) -> Dict[str, Any]:
        """模拟结构化输出"""
        response = self.chat(system_prompt, user_message, **kwargs)
        
        # 尝试解析
        try:
            if output_format == "yaml":
                return yaml.safe_load(response)
            else:
                return json.loads(response)
        except:
            return {"raw_response": response}
    
    def generate_alternatives(
        self,
        system_prompt: str,
        user_message: str,
        count: int = 3,
        **kwargs
    ) -> List[str]:
        """模拟生成多个方案"""
        return [f"方案{i+1}：基于'{user_message[:50]}...'的建议" for i in range(count)]

