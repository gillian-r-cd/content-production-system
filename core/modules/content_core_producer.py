# core/modules/content_core_producer.py
# 功能：内涵生产模块，按字段生产核心内容
# 主要类：ContentCoreProducer
# 核心能力：方案生成、逐字段生产、迭代优化

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseModule, ModuleResult
from core.models import ContentCore, ContentField, FieldSchema


class ContentCoreProducer(BaseModule):
    """
    内涵生产模块
    
    职责：
    - 生成多个设计方案供选择
    - 按FieldSchema逐字段生产内容
    - 支持单字段迭代优化
    - 整体质量把控
    
    工作流程：
    1. 生成多个差异化的设计方案
    2. 用户选择一个方案
    3. 按FieldSchema定义的字段逐个生产
    4. 每个字段可独立评估和迭代
    5. 全部完成后整体评估
    """
    
    name = "content_core_producer"
    description = "生产核心内容（内涵）"
    
    def get_template_name(self) -> str:
        return "content_core_producer.md.j2"
    
    def run(self, input_data: Dict[str, Any]) -> ModuleResult:
        """
        执行内涵生产
        
        支持多种操作模式。
        
        Args:
            input_data: {
                "project_id": str,
                "field_schema": FieldSchema,    # 字段定义
                "action": "generate_schemes" | "produce_field" | "iterate_field",
                
                # generate_schemes模式
                "scheme_count": int,            # 生成方案数量（默认3）
                
                # produce_field模式
                "content_core": ContentCore,    # 当前内涵对象
                "field_name": str,              # 要生产的字段名
                
                # iterate_field模式
                "feedback": str,                # 迭代反馈
            }
            
        Returns:
            ModuleResult
        """
        action = input_data.get("action", "produce_field")
        
        if action == "generate_schemes":
            return self._generate_schemes(input_data)
        elif action == "produce_field":
            return self._produce_field(input_data)
        elif action == "iterate_field":
            return self._iterate_field(input_data)
        else:
            return ModuleResult.fail(f"未知操作：{action}")
    
    def _generate_schemes(self, input_data: Dict[str, Any]) -> ModuleResult:
        """生成设计方案"""
        project_id = input_data.get("project_id", "")
        field_schema = input_data.get("field_schema")
        scheme_count = input_data.get("scheme_count", 3)
        
        # 获取意图和消费者调研上下文
        intent_context = ""
        research_context = ""
        if self.context_manager:
            intent = self.context_manager.get_stage_context("intent")
            if intent:
                intent_context = f"\n【项目意图】\n{intent.format_for_prompt() if hasattr(intent, 'format_for_prompt') else str(intent)}\n"
            research = self.context_manager.get_stage_context("consumer_research")
            if research:
                research_context = f"\n【目标用户】\n{research.format_for_prompt() if hasattr(research, 'format_for_prompt') else str(research)}\n"
        
        # 构建prompt - 要求严格的结构化输出
        # 使用 format_for_design() 而不是 format_for_prompt()，因为设计阶段不需要 ai_hint
        field_schema_summary = ""
        if field_schema:
            field_schema_summary = field_schema.format_for_design()
        
        system_prompt = f"""你是一个内容策略专家。请为以下内容品类生成{scheme_count}个差异化的设计方案。

{field_schema_summary}
{intent_context}
{research_context}

每个方案应该有明确的差异点，让用户能够选择最适合的方向。

【重要】请严格按照以下YAML格式输出，不要添加任何额外的格式或说明：

```yaml
schemes:
  - name: "方案简短名称（10字以内）"
    type: "方案类型（如：稳妥型/创意型/激进型）"
    description: "一句话概述这个方案的核心特点（30字左右）"
    approach: "详细说明这个方案的整体思路和实现方式（100-200字）"
    target_scenario: "适合使用这个方案的场景"
    key_features:
      - "关键特点1"
      - "关键特点2"
      - "关键特点3"
    recommended: false
  - name: "第二个方案名称"
    type: "类型"
    description: "描述"
    approach: "思路"
    target_scenario: "场景"
    key_features:
      - "特点1"
    recommended: true
```

注意事项：
1. name 必须是简短的方案名称，不要包含方案编号
2. type 标注方案的风格类型
3. description 是简短概述，让用户快速了解差异
4. approach 是详细说明
5. 只有一个方案的recommended设为true（最推荐的方案）
"""
        
        golden = self.build_golden_context()
        if golden:
            from core.prompt_engine import GoldenContextBuilder
            system_prompt = GoldenContextBuilder.format_for_system_prompt(golden) + "\n\n" + system_prompt
        
        # 调用AI获取结构化输出
        response = self.ai_client.chat_structured(
            system_prompt=system_prompt,
            user_message="请生成设计方案。",
            output_format="yaml",
            temperature_mode="creative",
        )
        
        # 解析方案列表
        schemes = self._parse_schemes_response(response, scheme_count)
        
        # 日志输出方案信息用于调试
        self.log(f"生成了 {len(schemes)} 个方案", "info")
        for i, scheme in enumerate(schemes):
            self.log(f"方案{i+1}: {scheme.get('name', '未命名')} - {scheme.get('description', '无描述')[:50]}...", "debug")
        
        # 创建ContentCore
        content_core = ContentCore(
            id=f"core_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_id=project_id,
            field_schema_id=field_schema.id if field_schema else "",
            design_schemes=schemes,
            status="scheme_selection",
        )
        
        # 初始化字段列表
        if field_schema:
            for field_def in field_schema.fields:
                content_core.fields.append(ContentField(
                    id=field_def.id or f"field_{len(content_core.fields)+1}",
                    name=field_def.name,
                    status="pending",
                ))
        
        return ModuleResult.ok(content_core)
    
    def _parse_schemes_response(self, response: Dict[str, Any], scheme_count: int) -> List[Dict[str, Any]]:
        """
        解析AI返回的方案数据，确保数据结构正确
        
        处理多种可能的格式：
        1. 正确格式: { schemes: [{ name, description, approach, ... }] }
        2. 旧格式: { schemes: [{ scheme: "长文本...", index: 0 }] }
        3. 字符串格式: { schemes: ["方案1内容", "方案2内容"] }
        """
        import re
        
        schemes = response.get("schemes", [])
        
        # 如果schemes不是列表，尝试从其他地方提取
        if not isinstance(schemes, list):
            # 可能是直接返回了方案列表
            if isinstance(response, list):
                schemes = response
            else:
                schemes = []
        
        parsed_schemes = []
        
        for i, scheme in enumerate(schemes):
            parsed = {
                "name": f"方案 {i+1}",
                "type": "",
                "description": "",
                "approach": "",
                "target_scenario": "",
                "key_features": [],
                "recommended": False,
            }
            
            if isinstance(scheme, dict):
                # 处理旧格式: { scheme: "长文本...", index: 0 }
                if "scheme" in scheme and isinstance(scheme.get("scheme"), str):
                    long_text = scheme["scheme"]
                    # 尝试从长文本中提取结构化信息
                    parsed = self._extract_scheme_from_text(long_text, i)
                else:
                    # 正确格式，直接使用
                    parsed["name"] = scheme.get("name", f"方案 {i+1}")
                    parsed["type"] = scheme.get("type", "")
                    parsed["description"] = scheme.get("description", scheme.get("summary", ""))
                    parsed["approach"] = scheme.get("approach", "")
                    parsed["target_scenario"] = scheme.get("target_scenario", "")
                    parsed["key_features"] = scheme.get("key_features", [])
                    parsed["recommended"] = scheme.get("recommended", False)
                    
                    # 如果description为空但有其他信息，尝试生成
                    if not parsed["description"] and parsed["approach"]:
                        parsed["description"] = parsed["approach"][:50] + "..."
                        
            elif isinstance(scheme, str):
                # 字符串格式，尝试提取
                parsed = self._extract_scheme_from_text(scheme, i)
            
            parsed_schemes.append(parsed)
        
        # 如果解析失败，创建默认方案
        if not parsed_schemes:
            parsed_schemes = [
                {
                    "name": f"方案 {i+1}",
                    "type": ["稳妥型", "创意型", "激进型"][i] if i < 3 else "标准型",
                    "description": "待生成的设计方案",
                    "approach": "请稍候，AI正在生成详细方案...",
                    "target_scenario": "",
                    "key_features": [],
                    "recommended": i == 0,
                }
                for i in range(scheme_count)
            ]
        
        return parsed_schemes
    
    def _extract_scheme_from_text(self, text: str, index: int) -> Dict[str, Any]:
        """从长文本中提取方案结构化信息"""
        import re
        
        result = {
            "name": f"方案 {index+1}",
            "type": "",
            "description": "",
            "approach": "",
            "target_scenario": "",
            "key_features": [],
            "recommended": False,
        }
        
        # 尝试提取方案名称（通常在开头）
        # 匹配模式如: "方案一：**「10分钟GROW微练营」**" 或 "**方案名称**"
        name_patterns = [
            r'方案[一二三][:：]?\s*[\*]*[「【]?([^」】\*\n]+)[」】]?[\*]*',
            r'名称[:：]\s*(.+?)[\n\r]',
            r'^\s*[\*]+\s*(.+?)\s*[\*]+',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                result["name"] = match.group(1).strip()[:30]  # 限制长度
                break
        
        # 尝试提取核心定位/描述
        desc_patterns = [
            r'核心定位[:：]\s*(.+?)(?:\n|$)',
            r'定位[:：]\s*(.+?)(?:\n|$)',
            r'简介[:：]\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, text)
            if match:
                result["description"] = match.group(1).strip()[:100]
                break
        
        # 如果没有找到描述，取前100个字符
        if not result["description"]:
            # 移除markdown格式
            clean_text = re.sub(r'[\*#]+', '', text)
            result["description"] = clean_text[:100].strip() + "..."
        
        # 提取主要特点作为key_features
        feature_patterns = [
            r'主要特点[:：]?\s*\n((?:\s*[-•]\s*.+\n?)+)',
            r'特点[:：]?\s*\n((?:\s*[-•]\s*.+\n?)+)',
            r'[-•]\s*(.+?)(?:\n|$)',
        ]
        
        features = []
        for pattern in feature_patterns:
            matches = re.findall(pattern, text)
            for match in matches[:5]:  # 最多5个特点
                feature = match.strip()
                if feature and len(feature) < 100:
                    features.append(feature)
        result["key_features"] = features[:5]
        
        # 完整文本作为approach
        result["approach"] = text.strip()
        
        return result
    
    def _produce_field(self, input_data: Dict[str, Any]) -> ModuleResult:
        """
        生产单个字段
        
        提示词结构（优化后，避免重复）：
        1. 角色定义 + 任务说明
        2. 全局约束（创作者禁忌、风格范例）
        3. 设计方案（当前选中的方案）
        4. 依赖字段内容（如果有依赖）
        5. 当前字段的生成指令（ai_hint是核心！）
        """
        content_core = input_data.get("content_core")
        field_name = input_data.get("field_name", "")
        field_schema = input_data.get("field_schema")
        selected_scheme = input_data.get("selected_scheme")
        
        if not content_core:
            return ModuleResult.fail("缺少ContentCore对象")
        
        # 获取字段定义（从 field_schema）
        field_def = None
        if field_schema:
            field_def = field_schema.get_field(field_name)
        
        # 获取当前字段对象（从 content_core，用于获取 clarification_answer）
        current_field = content_core.get_field(field_name)
        
        # ========== 1. 构建角色定义 ==========
        role_prompt = "你是一个专业的内容生产专家，正在为用户生成高质量的内容。"
        
        # ========== 2. 构建全局约束（精简版，避免重复） ==========
        constraints_prompt = ""
        golden = self.build_golden_context()
        if golden:
            constraints = golden.get("creator_constraints", {})
            if constraints:
                lines = ["【创作者约束】"]
                taboos = constraints.get("taboos", {})
                if taboos.get("forbidden_words"):
                    lines.append(f"🚫 禁用词汇：{', '.join(taboos['forbidden_words'][:10])}")  # 只取前10个
                if taboos.get("forbidden_topics"):
                    lines.append(f"🚫 禁碰话题：{', '.join(taboos['forbidden_topics'][:5])}")  # 只取前5个
                examples = constraints.get("voice_examples", [])
                if examples:
                    lines.append(f"\n📝 风格参考（节选）：\n{examples[0][:300]}...")  # 只取第一个示例的前300字
                constraints_prompt = "\n".join(lines) + "\n"
        
        # ========== 3. 构建设计方案上下文 ==========
        scheme_prompt = ""
        if selected_scheme and isinstance(selected_scheme, dict):
            scheme_prompt = f"""【当前设计方案】
方案名称：{selected_scheme.get('name', '未命名')}
方案描述：{selected_scheme.get('description', '')}
实现方法：{selected_scheme.get('approach', '')}
"""
        
        # ========== 4. 构建依赖字段内容 ==========
        # 两种依赖来源：
        # 1. 显式依赖（field_def.depends_on 定义的字段）
        # 2. 隐式依赖（同章节内已完成的字段）
        
        dependency_prompt = ""
        dep_contents = []
        
        # 4.1 显式依赖
        if field_def and hasattr(field_def, 'depends_on') and field_def.depends_on:
            for dep_name in field_def.depends_on:
                dep_field = content_core.get_field(dep_name)
                if dep_field and dep_field.content:
                    dep_contents.append(f"## {dep_name}\n{dep_field.content}")
        
        # 4.2 隐式依赖：同章节内已完成的字段（自动注入）
        # 找到当前字段所在的章节
        current_section = None
        current_field_order = 0
        for section in content_core.sections:
            for i, field in enumerate(section.fields):
                if field.id == current_field.id if current_field else field.name == field_name:
                    current_section = section
                    current_field_order = i
                    break
            if current_section:
                break
        
        # 获取同章节内在当前字段之前已完成的字段
        if current_section:
            for i, field in enumerate(current_section.fields):
                if i >= current_field_order:
                    break
                if field.status == "completed" and field.content:
                    # 避免重复添加显式依赖
                    if not any(f"## {field.name}\n" in dep for dep in dep_contents):
                        dep_contents.append(f"## {field.name}\n{field.content}")
        
        if dep_contents:
            dependency_prompt = "【参考内容（已生成的依赖字段）】\n" + "\n\n".join(dep_contents) + "\n"
        
        # ========== 5. 构建当前字段的生成指令（ai_hint是核心！）==========
        # ai_hint 是用户定义的提示词，应该被突出使用
        field_prompt = f"""【生成任务】
字段名称：{field_name}
字段说明：{field_def.description if field_def and field_def.description else '无'}
"""
        
        # ai_hint 是核心提示词，单独突出
        if field_def and field_def.ai_hint:
            field_prompt += f"""
⭐ 生成要求（重要！请严格遵循）：
{field_def.ai_hint}
"""
        
        if field_def and field_def.example:
            field_prompt += f"\n参考示例：{field_def.example}\n"
        
        # ========== 6. 用户澄清回答（如果有）==========
        # 这是用户在生成前回答的问题，应该作为重要上下文
        if current_field and current_field.clarification_answer:
            field_prompt += f"""
📝 用户补充信息：
{current_field.clarification_answer}
"""
        
        # ========== 组装最终提示词 ==========
        system_prompt = f"""{role_prompt}

{constraints_prompt}
{scheme_prompt}
{dependency_prompt}
{field_prompt}

请直接输出【{field_name}】的内容，不需要添加标题或额外格式。"""
        
        user_message = f"请生成【{field_name}】字段的内容。"
        
        self.log(f"开始生成字段: {field_name}", "info")
        if field_def and field_def.ai_hint:
            self.log(f"字段 ai_hint: {field_def.ai_hint[:100]}...", "debug")
        
        # 调用AI
        response = self.call_ai(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature_mode="default",
        )
        
        self.log(f"字段 {field_name} 生成完成，长度: {len(response)}", "info")
        
        return ModuleResult.ok({
            "field_name": field_name,
            "content": response,
            "content_core": content_core,
        })
    
    def _iterate_field(self, input_data: Dict[str, Any]) -> ModuleResult:
        """迭代优化字段"""
        content_core = input_data.get("content_core")
        field_name = input_data.get("field_name", "")
        field_schema = input_data.get("field_schema")
        feedback = input_data.get("feedback", "")
        
        if not content_core:
            return ModuleResult.fail("缺少ContentCore对象")
        
        field = content_core.get_field(field_name)
        if not field:
            return ModuleResult.fail(f"字段不存在：{field_name}")
        
        # 获取字段定义
        field_def = None
        if field_schema:
            field_def = field_schema.get_field(field_name)
        
        # 记录迭代历史
        if field.content:
            field.add_iteration(field.content, feedback, 0)
        
        # 构建prompt（带反馈）
        system_prompt = self.build_prompt({
            "current_field": {
                "name": field_name,
                "description": field_def.description if field_def else "",
                "ai_hint": field_def.ai_hint if field_def else "",
            } if field_def else {"name": field_name},
            "previous_fields": [
                {"name": f.name, "content": f.content}
                for f in content_core.get_completed_fields()
                if f.name != field_name
            ],
            "iteration_feedback": feedback,
        })
        
        user_message = f"请根据反馈改进【{field_name}】字段的内容。"
        
        # 调用AI
        response = self.call_ai(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature_mode="default",
        )
        
        # 更新字段
        field.content = response
        field.iteration_count += 1
        
        return ModuleResult.ok({
            "field_name": field_name,
            "content": response,
            "iteration_count": field.iteration_count,
            "content_core": content_core,
        })
    
    def produce_all_fields(
        self,
        content_core: ContentCore,
        field_schema: FieldSchema,
    ) -> ModuleResult:
        """
        生产所有字段
        
        便捷方法，按顺序生产所有pending字段。
        """
        pending_fields = content_core.get_pending_fields()
        
        for field in pending_fields:
            result = self._produce_field({
                "content_core": content_core,
                "field_name": field.name,
                "field_schema": field_schema,
            })
            
            if not result.success:
                return result
        
        content_core.status = "evaluation"
        return ModuleResult.ok(content_core)


