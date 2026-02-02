# core/modules/simulator.py
# 功能：Simulator评估模块，模拟目标用户评估内容质量
# 主要类：Simulator
# 核心能力：内容评估、问题识别、迭代建议

from typing import Any, Dict, List, Optional
from datetime import datetime
import yaml

from .base import BaseModule, ModuleResult
from core.models import SimulatorFeedback, Issue


class Simulator(BaseModule):
    """
    Simulator评估模块
    
    职责：
    - 从目标用户视角评估内容质量
    - 识别内容中的问题和改进点
    - 生成结构化的评估反馈
    - 决定是否需要迭代
    
    设计原则：
    - 评估维度由用户定义
    - 用户可以自定义评估提示词
    - 系统提供默认评估框架
    """
    
    name = "simulator"
    description = "模拟目标用户评估内容质量"
    
    def get_template_name(self) -> str:
        return "simulator.md.j2"
    
    def run(self, input_data: Dict[str, Any]) -> ModuleResult:
        """
        执行内容评估
        
        Args:
            input_data: {
                "project_id": str,
                "target_type": "field" | "content_core" | "channel" | "content_extension",
                "target_id": str,
                "content": str,                 # 待评估内容
                "evaluation_criteria": str,     # 评估标准（可选，用户自定义）
                "evaluator_id": str,            # 评估器ID（可选）
            }
            
        Returns:
            ModuleResult: 包含SimulatorFeedback
        """
        project_id = input_data.get("project_id", "")
        target_type = input_data.get("target_type", "field")
        target_id = input_data.get("target_id", "")
        content = input_data.get("content", "")
        evaluation_criteria = input_data.get("evaluation_criteria", "")
        evaluator_id = input_data.get("evaluator_id")
        
        if not content:
            return ModuleResult.fail("没有内容可评估")
        
        # 构建prompt
        system_prompt = self.build_prompt({
            "content_to_evaluate": content,
            "evaluation_criteria": evaluation_criteria,
        })
        
        user_message = f"请评估以下内容：\n\n{content}"
        
        # 调用AI
        response = self.call_ai_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            output_format="yaml",
        )
        
        return self._create_feedback(
            project_id, target_type, target_id, 
            response, evaluator_id, content
        )
    
    def _create_feedback(
        self,
        project_id: str,
        target_type: str,
        target_id: str,
        response: Dict[str, Any],
        evaluator_id: Optional[str],
        content: str,
    ) -> ModuleResult:
        """创建SimulatorFeedback对象"""
        
        if "parse_error" in response:
            # 解析失败，返回默认通过
            self.log(f"评估响应解析失败，默认通过：{response.get('parse_error')}", "warning")
            feedback = SimulatorFeedback(
                id=f"feedback_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                target_type=target_type,
                target_id=target_id,
                score=7.0,
                passed=True,
                summary="评估响应解析失败，已默认通过",
                raw_response=response.get("raw_response", ""),
            )
            return ModuleResult.ok(feedback)
        
        try:
            # 解析问题列表
            issues = []
            for i, issue_data in enumerate(response.get("issues", [])):
                if isinstance(issue_data, dict):
                    issues.append(Issue(
                        id=f"issue_{i+1}",
                        severity=issue_data.get("severity", "minor"),
                        category=issue_data.get("category", "未分类"),
                        description=issue_data.get("description", ""),
                        location=issue_data.get("location"),
                        suggestion=issue_data.get("suggestion"),
                    ))
            
            score = float(response.get("score", 7.0))
            passed = response.get("passed", score >= 7.0)
            
            feedback = SimulatorFeedback(
                id=f"feedback_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                target_type=target_type,
                target_id=target_id,
                evaluator_id=evaluator_id,
                score=score,
                passed=passed,
                issues=issues,
                dimension_scores=response.get("dimension_scores", {}),
                summary=response.get("summary", ""),
                raw_response=yaml.dump(response, allow_unicode=True),
            )
            
            return ModuleResult.ok(feedback)
            
        except Exception as e:
            self.log(f"创建SimulatorFeedback失败：{e}", "error")
            return ModuleResult.fail(f"创建评估反馈失败：{e}")
    
    def evaluate_field(
        self,
        project_id: str,
        field_name: str,
        field_content: str,
        field_description: str = "",
    ) -> ModuleResult:
        """
        评估单个字段
        
        便捷方法，用于评估内涵中的单个字段。
        """
        return self.run({
            "project_id": project_id,
            "target_type": "field",
            "target_id": field_name,
            "content": f"字段名：{field_name}\n{field_description}\n\n内容：\n{field_content}",
        })
    
    def evaluate_content_core(
        self,
        project_id: str,
        content_core_id: str,
        full_content: str,
    ) -> ModuleResult:
        """
        评估完整内涵
        
        便捷方法，用于整体评估内涵。
        """
        return self.run({
            "project_id": project_id,
            "target_type": "content_core",
            "target_id": content_core_id,
            "content": full_content,
        })
    
    def evaluate_channel(
        self,
        project_id: str,
        channel_name: str,
        channel_content: str,
    ) -> ModuleResult:
        """
        评估渠道内容
        
        便捷方法，用于评估外延中的单个渠道。
        """
        return self.run({
            "project_id": project_id,
            "target_type": "channel",
            "target_id": channel_name,
            "content": f"渠道：{channel_name}\n\n内容：\n{channel_content}",
        })



