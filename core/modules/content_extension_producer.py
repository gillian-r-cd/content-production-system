# core/modules/content_extension_producer.py
# 功能：外延生产模块，生产营销触达内容
# 主要类：ContentExtensionProducer
# 核心能力：渠道内容生产、基于内涵的价值点提炼

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseModule, ModuleResult
from core.models import ContentExtension, ChannelContent


class ContentExtensionProducer(BaseModule):
    """
    外延生产模块
    
    职责：
    - 基于内涵的核心价值点生产营销内容
    - 支持多渠道内容生产
    - 针对各渠道特点优化内容
    
    设计原则：
    - 外延可以在任何时候开始（只要价值点清晰）
    - 基于内涵但不完全依赖内涵
    - 用户可以先定义价值点，再生产内涵
    """
    
    name = "content_extension_producer"
    description = "生产营销触达内容（外延）"
    
    def get_template_name(self) -> str:
        return "content_extension_producer.md.j2"
    
    def run(self, input_data: Dict[str, Any]) -> ModuleResult:
        """
        执行外延生产
        
        Args:
            input_data: {
                "project_id": str,
                "action": "produce_channel" | "iterate_channel" | "extract_value_points",
                
                # produce_channel模式
                "content_extension": ContentExtension,
                "channel_name": str,
                "channel_description": str,
                
                # 可选：内涵摘要（如果有）
                "content_core_summary": str,
                
                # iterate_channel模式
                "feedback": str,
            }
            
        Returns:
            ModuleResult
        """
        action = input_data.get("action", "produce_channel")
        
        if action == "extract_value_points":
            return self._extract_value_points(input_data)
        elif action == "produce_channel":
            return self._produce_channel(input_data)
        elif action == "iterate_channel":
            return self._iterate_channel(input_data)
        else:
            return ModuleResult.fail(f"未知操作：{action}")
    
    def _extract_value_points(self, input_data: Dict[str, Any]) -> ModuleResult:
        """从内涵中提取核心价值点"""
        content_core_summary = input_data.get("content_core_summary", "")
        
        if not content_core_summary:
            return ModuleResult.fail("需要内涵内容才能提取价值点")
        
        system_prompt = """你是一个营销策略专家。请从以下内容中提取3-5个核心价值点。

价值点应该是：
- 对目标用户有吸引力的
- 能够差异化的
- 简洁有力的

请严格按照以下格式输出：

```yaml
value_points:
  - "价值点1"
  - "价值点2"
  - "价值点3"
```
"""
        
        golden = self.build_golden_context()
        if golden:
            from core.prompt_engine import GoldenContextBuilder
            system_prompt = GoldenContextBuilder.format_for_system_prompt(golden) + "\n\n" + system_prompt
        
        response = self.call_ai_structured(
            system_prompt=system_prompt,
            user_message=f"请从以下内容提取价值点：\n\n{content_core_summary}",
            output_format="yaml",
        )
        
        value_points = response.get("value_points", [])
        return ModuleResult.ok({"value_points": value_points})
    
    def _produce_channel(self, input_data: Dict[str, Any]) -> ModuleResult:
        """生产单个渠道内容"""
        project_id = input_data.get("project_id", "")
        content_extension = input_data.get("content_extension")
        channel_name = input_data.get("channel_name", "")
        channel_description = input_data.get("channel_description", "")
        content_core_summary = input_data.get("content_core_summary", "")
        
        # 如果没有ContentExtension，创建一个
        if not content_extension:
            content_extension = ContentExtension(
                id=f"ext_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
            )
        
        # 确保渠道存在
        channel = content_extension.get_channel(channel_name)
        if not channel:
            channel = content_extension.add_channel(channel_name, channel_description)
        
        # 构建prompt
        system_prompt = self.build_prompt({
            "channel": {
                "channel_name": channel_name,
                "channel_description": channel_description,
            },
            "value_points": content_extension.value_points,
            "content_core_summary": content_core_summary,
        })
        
        user_message = f"请为【{channel_name}】渠道生产营销内容。"
        
        # 调用AI
        response = self.call_ai(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature_mode="default",
        )
        
        # 更新渠道
        channel.content = response
        channel.status = "completed"
        channel.iteration_count += 1
        
        # 更新上下文
        self.context_manager.set_stage_context("content_extension", content_extension)
        
        return ModuleResult.ok({
            "channel_name": channel_name,
            "content": response,
            "content_extension": content_extension,
        })
    
    def _iterate_channel(self, input_data: Dict[str, Any]) -> ModuleResult:
        """迭代优化渠道内容"""
        content_extension = input_data.get("content_extension")
        channel_name = input_data.get("channel_name", "")
        feedback = input_data.get("feedback", "")
        content_core_summary = input_data.get("content_core_summary", "")
        
        if not content_extension:
            return ModuleResult.fail("缺少ContentExtension对象")
        
        channel = content_extension.get_channel(channel_name)
        if not channel:
            return ModuleResult.fail(f"渠道不存在：{channel_name}")
        
        # 构建prompt（带反馈）
        system_prompt = self.build_prompt({
            "channel": {
                "channel_name": channel_name,
                "channel_description": channel.channel_description,
            },
            "value_points": content_extension.value_points,
            "content_core_summary": content_core_summary,
            "iteration_feedback": feedback,
        })
        
        user_message = f"请根据反馈改进【{channel_name}】渠道的内容。\n\n当前内容：\n{channel.content}"
        
        # 调用AI
        response = self.call_ai(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature_mode="default",
        )
        
        # 更新渠道
        channel.content = response
        channel.iteration_count += 1
        
        return ModuleResult.ok({
            "channel_name": channel_name,
            "content": response,
            "iteration_count": channel.iteration_count,
            "content_extension": content_extension,
        })
    
    def produce_all_channels(
        self,
        content_extension: ContentExtension,
        content_core_summary: str = "",
    ) -> ModuleResult:
        """
        生产所有渠道内容
        
        便捷方法，按顺序生产所有pending渠道。
        """
        for channel in content_extension.channels:
            if channel.status == "pending":
                result = self._produce_channel({
                    "project_id": content_extension.project_id,
                    "content_extension": content_extension,
                    "channel_name": channel.channel_name,
                    "channel_description": channel.channel_description,
                    "content_core_summary": content_core_summary,
                })
                
                if not result.success:
                    return result
        
        content_extension.status = "completed"
        return ModuleResult.ok(content_extension)



