# core/modules/consumer_researcher.py
# 功能：消费者调研模块，构建目标用户画像
# 主要类：ConsumerResearcher
# 核心能力：用户画像生成、痛点分析、支持直接粘贴调研资料

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseModule, ModuleResult
from core.models import ConsumerResearch, StructuredResearch


class ConsumerResearcher(BaseModule):
    """
    消费者调研模块
    
    职责：
    - 基于意图生成目标用户画像
    - 支持用户直接粘贴已有调研资料
    - 支持AI辅助补充调研
    - 提取用于Golden Context的关键信息
    
    三种工作模式：
    1. AI生成：完全由AI基于意图推断用户画像
    2. 用户粘贴：用户直接粘贴已有调研资料
    3. 混合模式：用户粘贴部分资料，AI补充
    """
    
    name = "consumer_researcher"
    description = "构建目标用户画像和消费者调研"
    
    def get_template_name(self) -> str:
        return "consumer_researcher.md.j2"
    
    def run(self, input_data: Dict[str, Any]) -> ModuleResult:
        """
        执行消费者调研
        
        Args:
            input_data: {
                "project_id": str,
                "mode": "ai_generated" | "user_pasted" | "hybrid",
                "pasted_content": str,      # 用户粘贴的调研资料（可选）
                "additional_context": str,  # 补充说明（可选）
            }
            
        Returns:
            ModuleResult: 包含ConsumerResearch
        """
        project_id = input_data.get("project_id", "")
        mode = input_data.get("mode", "ai_generated")
        pasted_content = input_data.get("pasted_content", "")
        additional_context = input_data.get("additional_context", "")
        
        # 获取意图（从context_manager）
        intent = self.context_manager.get_stage_context("intent")
        
        if mode == "user_pasted" and pasted_content:
            # 纯粘贴模式：直接使用用户资料，AI提取关键信息
            return self._handle_pasted_mode(
                project_id, pasted_content, intent
            )
        elif mode == "hybrid" and pasted_content:
            # 混合模式：AI基于粘贴资料补充
            return self._handle_hybrid_mode(
                project_id, pasted_content, additional_context, intent
            )
        else:
            # AI生成模式
            return self._handle_ai_mode(
                project_id, additional_context, intent
            )
    
    def _handle_ai_mode(
        self,
        project_id: str,
        additional_context: str,
        intent: Any,
    ) -> ModuleResult:
        """AI生成模式"""
        # 构建专门的Persona生成prompt
        intent_text = intent.format_for_prompt() if intent and hasattr(intent, 'format_for_prompt') else str(intent) if intent else ""
        
        system_prompt = f"""你是一个用户研究专家。请基于项目意图，生成目标用户画像分析。

【项目意图】
{intent_text}

请生成以下内容：

1. **总体用户画像摘要**：一句话描述目标用户群体
2. **2-3个典型用户角色(Personas)**：每个角色包含具体的姓名、职位、背景描述、核心痛点、核心期望
3. **核心痛点列表**：目标用户群体共同的3-5个痛点
4. **核心期望列表**：目标用户群体共同的3-5个期望

请严格按以下YAML格式输出：

```yaml
persona_summary: "目标用户的一句话画像描述"
personas:
  - id: "persona_1"
    name: "张明"
    role: "某公司销售经理"
    background: "35岁，从业8年，带领5人团队，负责华东区业务..."
    pain_points:
      - "缺乏系统的团队辅导方法"
      - "下属执行力不足但不知如何改善"
    desires:
      - "希望团队业绩稳定提升"
      - "希望成为受下属信赖的领导"
  - id: "persona_2"
    name: "李婷"
    role: "新晋管理者"
    background: "28岁，刚从业务骨干晋升为主管..."
    pain_points:
      - "不知道如何与曾经的同事建立上下级关系"
    desires:
      - "快速建立管理者的威信"
key_pain_points:
  - "痛点1"
  - "痛点2"
  - "痛点3"
key_desires:
  - "期望1"
  - "期望2"
  - "期望3"
```

注意：
1. 每个Persona的名字要具体、有代表性
2. 背景描述要详细，让读者能想象出这个人
3. 痛点和期望要与项目意图紧密相关
"""
        
        user_message = "请基于以上意图，构建目标用户画像。"
        if additional_context:
            user_message += f"\n补充信息：{additional_context}"
        
        # 调用AI
        response = self.call_ai_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            output_format="yaml",
        )
        
        return self._create_research(
            project_id, "ai_generated", response, None
        )
    
    def _handle_pasted_mode(
        self,
        project_id: str,
        pasted_content: str,
        intent: Any,
    ) -> ModuleResult:
        """用户粘贴模式：从粘贴内容中提取关键信息"""
        # 构建提取提示
        system_prompt = """你是一个用户研究专家。请从用户提供的调研资料中提取关键信息。

请严格按照以下YAML格式输出：

```yaml
persona_summary: "一句话用户画像摘要"
key_pain_points:
  - "核心痛点1"
  - "核心痛点2"
key_desires:
  - "核心期望1"
  - "核心期望2"
```

注意：只提取资料中明确提到或可合理推断的信息，不要编造。
"""
        
        user_message = f"请从以下调研资料中提取关键信息：\n\n{pasted_content}"
        
        response = self.call_ai_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            output_format="yaml",
        )
        
        return self._create_research(
            project_id, "user_pasted", response, pasted_content
        )
    
    def _handle_hybrid_mode(
        self,
        project_id: str,
        pasted_content: str,
        additional_context: str,
        intent: Any,
    ) -> ModuleResult:
        """混合模式：基于粘贴资料补充"""
        # 构建prompt
        system_prompt = self.build_prompt({
            "intent": intent.format_for_prompt() if intent else "",
            "existing_research": pasted_content,
        })
        
        user_message = "请基于已有调研资料，补充完善用户画像。"
        if additional_context:
            user_message += f"\n补充信息：{additional_context}"
        
        response = self.call_ai_structured(
            system_prompt=system_prompt,
            user_message=user_message,
            output_format="yaml",
        )
        
        return self._create_research(
            project_id, "hybrid", response, pasted_content
        )
    
    def _create_research(
        self,
        project_id: str,
        source: str,
        response: Dict[str, Any],
        raw_text: Optional[str],
    ) -> ModuleResult:
        """创建ConsumerResearch对象"""
        
        if "parse_error" in response:
            return ModuleResult.fail(f"AI响应解析失败：{response.get('parse_error')}")
        
        try:
            # 处理personas
            personas = response.get("personas", [])
            if not isinstance(personas, list):
                personas = []
            
            # 确保每个persona有必要字段
            processed_personas = []
            for i, p in enumerate(personas):
                if isinstance(p, dict):
                    processed_personas.append({
                        "id": p.get("id", f"persona_{i+1}"),
                        "name": p.get("name", f"用户{i+1}"),
                        "role": p.get("role", "目标用户"),
                        "background": p.get("background", ""),
                        "pain_points": p.get("pain_points", []),
                        "desires": p.get("desires", []),
                        "selected": False,  # 默认未选中
                    })
            
            research = ConsumerResearch(
                id=f"research_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                project_id=project_id,
                source=source,
                raw_text=raw_text,
                structured=StructuredResearch(
                    id="structured",
                    persona=response.get("persona_details", {}).get("demographics", "")
                        if isinstance(response.get("persona_details"), dict) else None,
                    pain_points=response.get("pain_points", "")
                        if isinstance(response.get("pain_points"), str) else None,
                    goals=response.get("desires", "")
                        if isinstance(response.get("desires"), str) else None,
                ),
                summary=response.get("persona_summary", ""),
                key_pain_points=response.get("key_pain_points", []),
                key_desires=response.get("key_desires", []),
                personas=processed_personas,  # 添加personas
            )
            
            # 更新上下文
            self.context_manager.set_stage_context("consumer_research", research)
            
            # 日志记录
            self.log(f"生成消费者调研完成，包含 {len(processed_personas)} 个用户画像", "info")
            
            return ModuleResult.ok(research)
            
        except Exception as e:
            self.log(f"创建ConsumerResearch失败：{e}", "error")
            return ModuleResult.fail(f"创建调研对象失败：{e}")


