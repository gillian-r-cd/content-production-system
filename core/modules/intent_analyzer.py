# core/modules/intent_analyzer.py
# 功能：意图分析模块，从用户输入中提取精准的内容生产意图
# 主要类：IntentAnalyzer
# 核心能力：意图提取、追问澄清、成功标准生成

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseModule, ModuleResult
from core.models import Intent, IntentConstraints


class IntentAnalyzer(BaseModule):
    """
    意图分析模块
    
    职责：
    - 从用户的模糊输入中提取精准意图
    - 识别核心目标和成功标准
    - 发现并提出需要澄清的问题
    - 生成结构化的Intent对象
    
    工作流程：
    1. 用户输入原始需求
    2. AI分析并提取结构化意图
    3. 如果信息不完整，生成追问问题
    4. 用户回答追问
    5. 最终输出完整的Intent
    """
    
    name = "intent_analyzer"
    description = "从用户输入中分析和提取内容生产意图"
    
    def get_template_name(self) -> str:
        return "intent_analyzer.md.j2"
    
    def run(self, input_data: Dict[str, Any]) -> ModuleResult:
        """
        执行意图分析
        
        Args:
            input_data: {
                "project_id": str,
                "raw_input": str,           # 用户原始输入
                "previous_clarifications": List[Dict],  # 之前的追问历史（可选）
            }
            
        Returns:
            ModuleResult: 包含Intent或追问问题
        """
        project_id = input_data.get("project_id", "")
        raw_input = input_data.get("raw_input", "")
        previous = input_data.get("previous_clarifications", [])
        
        if not raw_input:
            return ModuleResult.fail("请提供内容生产需求")
        
        # 构建用户消息
        user_message = self._build_user_message(raw_input, previous)
        
        # 构建prompt
        system_prompt = self.build_prompt({
            "raw_input": raw_input,
            "previous_clarifications": previous,
        })
        
        # 调用AI
        response = self.call_ai_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            output_format="yaml",
        )
        
        # 解析响应
        return self._parse_response(response, project_id, raw_input, previous)
    
    def _build_user_message(
        self, 
        raw_input: str, 
        previous: List[Dict]
    ) -> str:
        """构建发送给AI的用户消息"""
        parts = [f"用户的需求描述：\n{raw_input}"]
        
        if previous:
            parts.append("\n之前的追问和回答：")
            for item in previous:
                parts.append(f"问：{item.get('question', '')}")
                parts.append(f"答：{item.get('answer', '')}")
        
        return "\n".join(parts)
    
    def _parse_response(
        self, 
        response: Dict[str, Any],
        project_id: str,
        raw_input: str,
        previous: List[Dict],
    ) -> ModuleResult:
        """解析AI响应"""
        
        # 检查是否有解析错误
        if "parse_error" in response:
            self.log(f"AI响应解析失败：{response.get('parse_error')}", "warning")
            return ModuleResult.fail(f"AI响应格式错误，请重试")
        
        # 检查是否需要追问
        if response.get("needs_clarification", False):
            questions = response.get("clarification_questions", [])
            if questions:
                # 返回第一个追问问题
                return ModuleResult.need_input(questions[0])
        
        # 构建Intent对象
        try:
            intent = Intent(
                id=f"intent_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                goal=response.get("goal", ""),
                success_criteria=response.get("success_criteria", []),
                constraints=IntentConstraints(
                    id="constraints",
                    must_have=response.get("must_have", []),
                    must_avoid=response.get("must_avoid", []),
                ),
                business_background=response.get("business_background"),
                raw_input=raw_input,
                clarification_history=previous,
            )
            
            # 更新上下文
            self.context_manager.set_stage_context("intent", intent)
            
            return ModuleResult.ok(intent)
            
        except Exception as e:
            self.log(f"创建Intent失败：{e}", "error")
            return ModuleResult.fail(f"创建意图对象失败：{e}")
    
    def refine_with_answer(
        self,
        current_intent: Intent,
        question: str,
        answer: str,
    ) -> ModuleResult:
        """
        根据用户回答的追问，继续分析
        
        Args:
            current_intent: 当前的Intent（可能不完整）
            question: 追问的问题
            answer: 用户的回答
            
        Returns:
            ModuleResult: 更新后的Intent或新的追问
        """
        # 添加到澄清历史
        clarifications = current_intent.clarification_history.copy()
        clarifications.append({"question": question, "answer": answer})
        
        # 重新运行分析
        return self.run({
            "project_id": current_intent.project_id,
            "raw_input": current_intent.raw_input,
            "previous_clarifications": clarifications,
        })



