# core/orchestrator.py
# 功能：流程编排器，协调各模块执行，管理数据流转和循环控制
# 主要类：Orchestrator, ProjectState
# 核心能力：状态管理、模块调度、自迭代控制、人机交互

from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable, Literal
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
import yaml

from core.ai_client import AIClient, MockAIClient
from core.prompt_engine import PromptEngine
from core.context_manager import ContextManager
from core.models import (
    Project, CreatorProfile, FieldSchema,
    Intent, ConsumerResearch,
    ContentCore, ContentField,
    ContentExtension, ChannelContent,
    SimulatorFeedback,
    create_default_field_schema,
)
from core.modules import (
    IntentAnalyzer,
    ConsumerResearcher,
    ContentCoreProducer,
    ContentExtensionProducer,
    Simulator,
    ModuleResult,
)


@dataclass
class OrchestratorConfig:
    """编排器配置"""
    max_iterations: int = 3                     # 单字段最大迭代次数
    max_clarifications: int = 3                 # 意图分析最大追问次数
    pass_threshold: float = 7.0                 # 评估通过阈值
    auto_evaluate: bool = True                  # 是否自动评估
    alternatives_count: int = 3                 # 方案生成数量
    storage_base_path: str = "./storage"        # 存储根路径


@dataclass
class ProjectState:
    """
    项目状态
    
    管理整个项目的生产状态，包括：
    - 当前阶段
    - 各阶段的数据
    - 迭代历史
    - 等待用户输入的状态
    """
    project: Project
    creator_profile: CreatorProfile
    field_schema: Optional[FieldSchema] = None
    
    # 各阶段数据
    intent: Optional[Intent] = None
    consumer_research: Optional[ConsumerResearch] = None
    content_core: Optional[ContentCore] = None
    content_extension: Optional[ContentExtension] = None
    
    # 当前状态
    current_stage: str = "intent"
    current_field: Optional[str] = None         # 当前处理的字段
    current_channel: Optional[str] = None       # 当前处理的渠道
    
    # 等待用户输入
    waiting_for_input: bool = False
    input_prompt: Optional[str] = None
    input_callback: Optional[str] = None        # 输入回调函数名
    
    # 临时存储（用于跨回调保持数据）
    raw_intent_input: Optional[str] = None      # 保存原始意图输入
    clarification_history: list = None          # 追问历史
    clarification_count: int = 0                # 当前追问次数
    max_clarifications: int = 3                 # 最大追问次数
    
    # 统计
    ai_call_count: int = 0
    total_iterations: int = 0


class Orchestrator:
    """
    流程编排器
    
    核心职责：
    1. 管理项目状态和流程推进
    2. 协调各模块执行
    3. 处理自迭代循环
    4. 管理人机交互点
    
    工作流程：
    Intent → ConsumerResearch → ContentCore(方案选择→逐字段生产) → ContentExtension → 完成
    
    每个阶段都可能触发Simulator评估和迭代。
    """
    
    def __init__(
        self,
        ai_client: AIClient | MockAIClient,
        prompt_engine: PromptEngine,
        config: Optional[OrchestratorConfig] = None,
    ):
        """
        初始化编排器
        
        Args:
            ai_client: AI客户端
            prompt_engine: Prompt引擎
            config: 编排器配置
        """
        self.ai_client = ai_client
        self.prompt_engine = prompt_engine
        self.config = config or OrchestratorConfig()
        
        # 上下文管理器
        self.context_manager = ContextManager()
        
        # 模块实例（延迟初始化）
        self._modules: Dict[str, Any] = {}
        
        # 事件回调
        self._callbacks: Dict[str, List[Callable]] = {
            "stage_changed": [],
            "content_generated": [],
            "evaluation_done": [],
            "iteration_started": [],
            "waiting_input": [],
            "completed": [],
        }
    
    def _get_module(self, module_name: str):
        """获取模块实例（懒加载）"""
        if module_name not in self._modules:
            module_classes = {
                "intent_analyzer": IntentAnalyzer,
                "consumer_researcher": ConsumerResearcher,
                "content_core_producer": ContentCoreProducer,
                "content_extension_producer": ContentExtensionProducer,
                "simulator": Simulator,
            }
            
            if module_name in module_classes:
                self._modules[module_name] = module_classes[module_name](
                    ai_client=self.ai_client,
                    prompt_engine=self.prompt_engine,
                    context_manager=self.context_manager,
                )
        
        return self._modules.get(module_name)
    
    def on(self, event: str, callback: Callable) -> None:
        """注册事件回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _emit(self, event: str, data: Any = None) -> None:
        """触发事件"""
        for callback in self._callbacks.get(event, []):
            callback(data)
    
    def create_project_state(
        self,
        project: Project,
        creator_profile: CreatorProfile,
        field_schema: Optional[FieldSchema] = None,
    ) -> ProjectState:
        """
        创建项目状态
        
        Args:
            project: 项目对象
            creator_profile: 创作者特质
            field_schema: 字段schema（可选）
            
        Returns:
            ProjectState: 初始化的项目状态
        """
        # 设置上下文
        self.context_manager.set_creator_profile(creator_profile)
        
        return ProjectState(
            project=project,
            creator_profile=creator_profile,
            field_schema=field_schema,
        )
    
    def run_stage(
        self,
        state: ProjectState,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> ProjectState:
        """
        运行当前阶段
        
        Args:
            state: 项目状态
            input_data: 用户输入数据（如果之前在等待输入）
            
        Returns:
            ProjectState: 更新后的状态
        """
        # 设置AI调用上下文（用于日志记录）
        self.ai_client.set_context(
            project_id=state.project.id,
            stage=state.current_stage
        )
        
        # 如果在等待输入，处理输入
        if state.waiting_for_input and input_data:
            return self._handle_input(state, input_data)
        
        # 根据当前阶段执行
        stage_handlers = {
            "intent": self._run_intent_stage,
            "research": self._run_research_stage,
            "core_design": self._run_core_design_stage,
            "core_production": self._run_core_production_stage,
            "extension": self._run_extension_stage,
        }
        
        handler = stage_handlers.get(state.current_stage)
        if handler:
            return handler(state, input_data or {})
        
        return state
    
    def _run_intent_stage(
        self, 
        state: ProjectState, 
        input_data: Dict[str, Any]
    ) -> ProjectState:
        """运行意图分析阶段"""
        analyzer = self._get_module("intent_analyzer")
        
        raw_input = input_data.get("raw_input", "")
        if not raw_input:
            state.waiting_for_input = True
            state.input_prompt = "请描述你想要生产的内容："
            state.input_callback = "intent_input"
            self._emit("waiting_input", state)
            return state
        
        # 保存原始输入，用于追问后重新分析
        state.raw_intent_input = raw_input
        if state.clarification_history is None:
            state.clarification_history = []
        
        clarifications = input_data.get("clarifications", state.clarification_history or [])
        
        result = analyzer.run({
            "project_id": state.project.id,
            "raw_input": raw_input,
            "previous_clarifications": clarifications,
        })
        
        state.ai_call_count += 1
        
        if result.needs_input:
            # 检查是否达到追问上限
            if state.clarification_count >= self.config.max_clarifications:
                # 达到上限，强制让AI基于已有信息生成结果
                self._emit("clarification_limit_reached", {
                    "count": state.clarification_count,
                    "max": self.config.max_clarifications,
                })
                # 重新调用，附加强制完成指令
                force_result = analyzer.run({
                    "project_id": state.project.id,
                    "raw_input": raw_input + "\n\n【系统指令】已追问" + str(self.config.max_clarifications) + "次，请直接基于已有信息生成意图分析结果，不要再追问。",
                    "previous_clarifications": clarifications,
                })
                state.ai_call_count += 1
                if force_result.success and force_result.data:
                    state.intent = force_result.data
                    state.project.intent_id = state.intent.id
                    # 清理临时数据
                    state.raw_intent_input = None
                    state.clarification_history = None
                    state.clarification_count = 0
                    # ✅ 修复：即使达到追问上限，也等待用户确认意图再进入下一阶段
                    state.waiting_for_input = True
                    state.input_prompt = "意图分析已完成，请确认后进入消费者调研阶段。"
                    state.input_callback = "confirm_intent"
                    self._emit("intent_ready", {"intent": state.intent})
                return state
            
            # 继续追问，显示进度
            state.clarification_count += 1
            state.waiting_for_input = True
            # 追问提示带进度：问题 (2/3)
            progress = f"问题 ({state.clarification_count}/{self.config.max_clarifications})"
            state.input_prompt = f"{progress}: {result.input_prompt}"
            state.input_callback = "intent_clarification"
            self._emit("waiting_input", state)
            return state
        
        if result.success:
            state.intent = result.data
            state.project.intent_id = state.intent.id
            # 清理临时数据
            state.raw_intent_input = None
            state.clarification_history = None
            state.clarification_count = 0
            
            # ✅ 设置意图上下文到 context_manager
            self.context_manager.set_stage_context("intent", state.intent)
            
            # ✅ 等待用户确认意图，而不是直接进入下一阶段
            state.waiting_for_input = True
            state.input_prompt = "意图分析已完成，请确认后进入消费者调研阶段。"
            state.input_callback = "confirm_intent"
            self._emit("intent_ready", {"intent": state.intent})
        
        return state
    
    def _run_research_stage(
        self, 
        state: ProjectState, 
        input_data: Dict[str, Any]
    ) -> ProjectState:
        """运行消费者调研阶段"""
        researcher = self._get_module("consumer_researcher")
        
        mode = input_data.get("mode", "ai_generated")
        
        result = researcher.run({
            "project_id": state.project.id,
            "mode": mode,
            "pasted_content": input_data.get("pasted_content", ""),
            "additional_context": input_data.get("additional_context", ""),
        })
        
        state.ai_call_count += 1
        
        if result.success:
            state.consumer_research = result.data
            state.project.consumer_research_id = state.consumer_research.id
            
            # ✅ 设置消费者调研上下文到 context_manager
            self.context_manager.set_stage_context("consumer_research", state.consumer_research)
            
            # ✅ 等待用户确认调研结果，而不是直接进入下一阶段
            state.waiting_for_input = True
            state.input_prompt = "消费者调研已完成，请确认后进入内涵设计阶段。"
            state.input_callback = "confirm_research"
            self._emit("research_ready", {"research": state.consumer_research})
        
        return state
    
    def _run_core_design_stage(
        self, 
        state: ProjectState, 
        input_data: Dict[str, Any]
    ) -> ProjectState:
        """运行内涵设计阶段（方案生成和选择）"""
        producer = self._get_module("content_core_producer")
        
        # 如果没有field_schema，使用默认的
        if not state.field_schema:
            state.field_schema = create_default_field_schema()
            self.context_manager.set_field_schema(state.field_schema)
        
        action = input_data.get("action", "generate_schemes")
        
        if action == "generate_schemes":
            result = producer.run({
                "project_id": state.project.id,
                "field_schema": state.field_schema,
                "action": "generate_schemes",
                "scheme_count": self.config.alternatives_count,
            })
            
            state.ai_call_count += 1
            
            if result.success:
                state.content_core = result.data
                
                # 确保字段列表已初始化（从field_schema）
                if not state.content_core.fields and state.field_schema:
                    for field_def in state.field_schema.fields:
                        state.content_core.fields.append(ContentField(
                            id=field_def.id or f"field_{len(state.content_core.fields)+1}",
                            name=field_def.name,
                            status="pending",
                        ))
                
                # 等待用户选择方案
                state.waiting_for_input = True
                state.input_prompt = "请选择一个设计方案（输入1-3的数字）："
                state.input_callback = "scheme_selection"
                self._emit("content_generated", {
                    "type": "schemes",
                    "schemes": state.content_core.design_schemes,
                })
        
        elif action == "select_scheme":
            scheme_index = input_data.get("scheme_index", 0)
            if state.content_core:
                state.content_core.selected_scheme_index = scheme_index
                # 选择方案后，进入目录编辑阶段，而不是直接开始生产
                state.content_core.status = "outline_editing"
                state.current_stage = "core_production"
                state.project.status = "core_production"
                
                # 初始化目录结构（如果还没有）
                if not state.content_core.sections and state.field_schema:
                    from core.models import ContentSection, ContentField
                    # 创建默认章节
                    section = ContentSection(
                        id="section_default",
                        name="新章节",
                        description="",
                        order=0,
                        fields=[]
                    )
                    # 从字段模板创建字段
                    for i, field_def in enumerate(state.field_schema.get_ordered_fields()):
                        section.fields.append(ContentField(
                            id=f"field_{field_def.name}_{i}",
                            name=field_def.name,
                            display_name=field_def.name,
                            description=field_def.description,
                            order=i,
                            status="pending",
                        ))
                    state.content_core.sections = [section]
                
                # 设置等待用户确认目录结构
                state.waiting_for_input = True
                state.input_prompt = "方案已选择，请在左侧编辑目录结构后点击「确认目录结构」开始生产"
                state.input_callback = "confirm_outline"
                
                self._emit("stage_changed", {"stage": "core_production"})
        
        return state
    
    def _run_core_production_stage(
        self, 
        state: ProjectState, 
        input_data: Dict[str, Any]
    ) -> ProjectState:
        """运行内涵生产阶段（逐字段生产）"""
        producer = self._get_module("content_core_producer")
        
        if not state.content_core:
            return state
        
        # 确保有field_schema
        if not state.field_schema:
            state.field_schema = create_default_field_schema()
        
        # 确保字段列表已初始化（按 order 排序）
        if not state.content_core.fields and state.field_schema:
            for field_def in state.field_schema.get_ordered_fields():
                state.content_core.fields.append(ContentField(
                    id=field_def.id or f"field_{len(state.content_core.fields)+1}",
                    name=field_def.name,
                    status="pending",
                ))
        
        # 获取下一个待处理字段（优先处理 generating 状态的，然后是 pending）
        # 这样可以恢复卡住的生成任务
        all_fields = state.content_core.get_all_fields()
        generating_fields = [f for f in all_fields if f.status == "generating"]
        pending_fields = [f for f in all_fields if f.status == "pending"]
        
        # 优先恢复 generating 状态的字段
        next_fields = generating_fields if generating_fields else pending_fields
        
        if not next_fields:
            # 所有字段完成，进入外延阶段
            state.content_core.status = "completed"
            state.current_stage = "extension"
            state.project.status = "extension"
            state.project.content_core_id = state.content_core.id
            self._emit("stage_changed", {"stage": "extension"})
            return state
        
        current_field = next_fields[0]
        # 保存字段ID，用于精确查找（跨章节可能有同名字段）
        state.current_field = current_field.id  # 使用 ID 而不是名称
        
        # ========== 检查生成前提问（clarification_prompt）==========
        # 从 field_schema 获取字段定义
        field_def = None
        if state.field_schema:
            field_def = state.field_schema.get_field(current_field.name)
        
        # 如果有生成前提问且用户还没回答，等待用户输入
        if field_def and field_def.clarification_prompt and not current_field.clarification_answer:
            state.waiting_for_input = True
            # 不设置 input_prompt，避免问题出现在右侧对话框
            # 弹窗从 API 响应的 clarification 字段获取问题（从 field_schema 获取）
            state.input_prompt = None
            state.input_callback = "field_clarification"
            # 不标记为 generating，保持 pending 状态
            self._emit("clarification_needed", {
                "field_id": current_field.id,
                "field_name": current_field.name,
                "question": field_def.clarification_prompt,
            })
            return state
        
        # 标记字段为生成中
        current_field.status = "generating"
        
        # 获取选中的设计方案作为上下文
        selected_scheme = None
        if state.content_core.selected_scheme_index is not None:
            scheme_idx = state.content_core.selected_scheme_index
            if scheme_idx < len(state.content_core.design_schemes):
                selected_scheme = state.content_core.design_schemes[scheme_idx]
        
        # 生产字段 - 使用设计方案作为额外上下文，包含用户的澄清回答
        result = producer.run({
            "action": "produce_field",
            "content_core": state.content_core,
            "field_name": current_field.name,
            "field_schema": state.field_schema,
            "selected_scheme": selected_scheme,  # 传入选中的方案
        })
        
        state.ai_call_count += 1
        
        if result.success:
            content = result.data.get("content", "")
            # 更新字段状态 - 使用字段ID精确查找（因为跨章节可能有同名字段）
            field = state.content_core.get_field(state.current_field)
            if field:
                field.content = content
                field.status = "completed"
                field.iteration_count += 1
            
            self._emit("content_generated", {
                "type": "field",
                "field_name": current_field.name,
                "content": content,
            })
            
            # 添加到项目消息
            if hasattr(state.project, 'add_message'):
                state.project.add_message(
                    "system", 
                    f"字段【{current_field.name}】生成完成",
                    "core_production"
                )
        else:
            # 生成失败
            current_field.status = "failed"
            if hasattr(state.project, 'add_message'):
                state.project.add_message(
                    "system", 
                    f"字段【{current_field.name}】生成失败: {result.error}",
                    "core_production"
                )
        
        return state
    
    def _run_extension_stage(
        self, 
        state: ProjectState, 
        input_data: Dict[str, Any]
    ) -> ProjectState:
        """运行外延生产阶段"""
        producer = self._get_module("content_extension_producer")
        
        action = input_data.get("action", "setup")
        
        if action == "setup":
            # 初始化外延
            if not state.content_extension:
                state.content_extension = ContentExtension(
                    id=f"ext_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    project_id=state.project.id,
                    content_core_id=state.content_core.id if state.content_core else None,
                )
            
            # 等待用户添加渠道
            state.waiting_for_input = True
            state.input_prompt = "请输入要生产的渠道名称（如：课程介绍页，或输入'完成'结束）："
            state.input_callback = "add_channel"
        
        elif action == "add_channel":
            channel_name = input_data.get("channel_name", "")
            if channel_name and channel_name != "完成":
                if state.content_extension:
                    state.content_extension.add_channel(channel_name)
                    state.current_channel = channel_name
                    
                    # 生产渠道内容
                    result = producer.run({
                        "project_id": state.project.id,
                        "action": "produce_channel",
                        "content_extension": state.content_extension,
                        "channel_name": channel_name,
                        "content_core_summary": state.content_core.format_for_prompt() if state.content_core else "",
                    })
                    
                    state.ai_call_count += 1
                    
                    if result.success:
                        self._emit("content_generated", {
                            "type": "channel",
                            "channel_name": channel_name,
                            "content": result.data["content"],
                        })
                    
                    # 继续添加渠道
                    state.waiting_for_input = True
                    state.input_prompt = "请输入下一个渠道名称（或输入'完成'结束）："
                    state.input_callback = "add_channel"
            else:
                # 完成
                if state.content_extension:
                    state.content_extension.status = "completed"
                state.current_stage = "completed"
                state.project.status = "completed"
                state.project.content_extension_id = state.content_extension.id if state.content_extension else None
                self._emit("completed", {"project": state.project})
        
        return state
    
    def _handle_input(
        self, 
        state: ProjectState, 
        input_data: Dict[str, Any]
    ) -> ProjectState:
        """处理用户输入"""
        callback = state.input_callback
        state.waiting_for_input = False
        state.input_prompt = None
        state.input_callback = None
        
        # 如果 callback 为空但在 intent 阶段，推断用户意图
        if not callback and state.current_stage == "intent":
            if not state.intent:
                callback = "intent_input"
            else:
                callback = "confirm_intent"
        
        if callback == "intent_input":
            # 用户输入作为 raw_input
            answer = input_data.get("answer", "")
            if answer:
                return self._run_intent_stage(state, {"raw_input": answer})
            return self._run_intent_stage(state, input_data)
        
        elif callback == "intent_clarification":
            # 保存问答到历史
            if state.clarification_history is None:
                state.clarification_history = []
            state.clarification_history.append({
                "question": state.input_prompt or "追问",
                "answer": input_data.get("answer", ""),
            })
            
            # 使用保存的原始输入重新分析
            raw_input = state.raw_intent_input or (state.intent.raw_input if state.intent else "")
            return self._run_intent_stage(state, {
                "raw_input": raw_input,
                "clarifications": state.clarification_history,
            })
        
        elif callback == "confirm_intent":
            # 用户确认意图，进入消费者调研阶段
            state.current_stage = "research"
            state.project.status = "research"
            self._emit("stage_changed", {"stage": "research"})
            # 自动开始消费者调研
            return self._run_research_stage(state, {})
        
        elif callback == "confirm_research":
            # 用户确认调研结果，进入内涵设计阶段
            state.current_stage = "core_design"
            state.project.status = "core_design"
            self._emit("stage_changed", {"stage": "core_design"})
            # 自动开始生成设计方案
            return self._run_core_design_stage(state, {"action": "generate_schemes"})
        
        elif callback == "confirm_outline":
            # 用户确认目录结构，开始生产
            if state.content_core:
                state.content_core.outline_confirmed = True
                state.content_core.status = "field_production"
            # 继续到内涵生产阶段
            return self._run_core_production_stage(state, {})
        
        elif callback == "field_clarification":
            # 用户回答了字段生成前的问题
            answer = input_data.get("answer", "")
            # 保存回答到当前字段
            if state.current_field and state.content_core:
                field = state.content_core.get_field(state.current_field)
                if field:
                    field.clarification_answer = answer
            # 继续生成字段
            return self._run_core_production_stage(state, {})
        
        elif callback == "scheme_selection":
            scheme_index = int(input_data.get("answer", "1")) - 1
            return self._run_core_design_stage(state, {
                "action": "select_scheme",
                "scheme_index": scheme_index,
            })
        
        elif callback == "add_channel":
            return self._run_extension_stage(state, {
                "action": "add_channel",
                "channel_name": input_data.get("answer", ""),
            })
        
        return state
    
    def run_full_flow(
        self,
        state: ProjectState,
        initial_input: str,
        interactive_callback: Optional[Callable[[str], str]] = None,
    ) -> ProjectState:
        """
        运行完整流程
        
        非交互模式下自动运行，交互模式下通过callback获取用户输入。
        
        Args:
            state: 项目状态
            initial_input: 初始用户输入
            interactive_callback: 交互回调函数（接收提示，返回用户输入）
            
        Returns:
            ProjectState: 最终状态
        """
        # 运行意图分析
        state = self.run_stage(state, {"raw_input": initial_input})
        
        # 循环处理直到完成或需要输入
        while state.current_stage != "completed":
            if state.waiting_for_input:
                if interactive_callback:
                    user_input = interactive_callback(state.input_prompt)
                    state = self.run_stage(state, {"answer": user_input})
                else:
                    # 非交互模式，使用默认值
                    if state.input_callback == "scheme_selection":
                        state = self.run_stage(state, {"answer": "1"})
                    elif state.input_callback == "add_channel":
                        # 默认添加一个渠道然后完成
                        if not state.content_extension or not state.content_extension.channels:
                            state = self.run_stage(state, {"answer": "课程介绍页"})
                        else:
                            state = self.run_stage(state, {"answer": "完成"})
                    else:
                        break
            else:
                state = self.run_stage(state, {})
        
        return state
    
    def save_state(self, state: ProjectState, path: Optional[str] = None) -> str:
        """保存项目状态到文件"""
        if path is None:
            path = Path(self.config.storage_base_path) / "projects" / state.project.id
        
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # 保存各组件
        state.project.save(path / "project.yaml")
        
        if state.intent:
            state.intent.save(path / "intent.yaml")
        if state.consumer_research:
            state.consumer_research.save(path / "consumer_research.yaml")
        if state.content_core:
            state.content_core.save(path / "content_core.yaml")
        if state.content_extension:
            state.content_extension.save(path / "content_extension.yaml")
        
        return str(path)
    
    def load_state(self, project_id: str, path: Optional[str] = None) -> Optional[ProjectState]:
        """从文件加载项目状态"""
        if path is None:
            path = Path(self.config.storage_base_path) / "projects" / project_id
        else:
            path = Path(path)
        
        if not path.exists():
            return None
        
        # 加载Project
        project_file = path / "project.yaml"
        if not project_file.exists():
            return None
        
        from core.models import Project, CreatorProfile, Intent, ConsumerResearch, ContentCore, ContentExtension
        
        project = Project.load(project_file)
        
        # 加载Profile
        profile_path = Path(self.config.storage_base_path) / "creator_profiles" / f"{project.creator_profile_id}.yaml"
        creator_profile = CreatorProfile.load(profile_path) if profile_path.exists() else None
        
        # 加载各组件
        intent = None
        intent_file = path / "intent.yaml"
        if intent_file.exists():
            intent = Intent.load(intent_file)
        
        consumer_research = None
        research_file = path / "consumer_research.yaml"
        if research_file.exists():
            consumer_research = ConsumerResearch.load(research_file)
        
        content_core = None
        core_file = path / "content_core.yaml"
        if core_file.exists():
            content_core = ContentCore.load(core_file)
        
        content_extension = None
        ext_file = path / "content_extension.yaml"
        if ext_file.exists():
            content_extension = ContentExtension.load(ext_file)
        
        # 加载项目关联的 FieldSchema（关键！用于注入 ai_hint 到生成提示词）
        field_schema = None
        if project.field_schema_id:
            # 从存储路径加载用户配置的字段模板
            schema_path = Path(self.config.storage_base_path) / "field_schemas" / f"{project.field_schema_id}.yaml"
            if schema_path.exists():
                from core.models import FieldSchema
                field_schema = FieldSchema.load(schema_path)
        
        # 如果没有关联 field_schema 且 content_core 存在但 fields 为空，使用默认 schema
        if field_schema is None and content_core and not content_core.fields:
            field_schema = create_default_field_schema()
            for field_def in field_schema.fields:
                content_core.fields.append(ContentField(
                    id=field_def.id or f"field_{len(content_core.fields)+1}",
                    name=field_def.name,
                    status="pending",
                ))
        
        # 确定当前阶段和等待状态
        current_stage = project.status
        waiting_for_input = False
        input_prompt = None
        input_callback = None
        
        if current_stage == "draft":
            current_stage = "intent"
            waiting_for_input = True
            input_prompt = "请描述你想要生产的内容"
            input_callback = "intent_input"
        elif current_stage == "intent":
            if not intent:
                waiting_for_input = True
                input_prompt = "请描述你想要生产的内容"
                input_callback = "intent_input"
            else:
                # 意图已完成，等待确认
                waiting_for_input = True
                input_prompt = "意图分析已完成，请确认后进入消费者调研阶段。"
                input_callback = "confirm_intent"
        elif current_stage == "research":
            if consumer_research:
                # 调研已完成，等待确认
                waiting_for_input = True
                input_prompt = "消费者调研已完成，请确认后进入内涵设计阶段。"
                input_callback = "confirm_research"
        elif current_stage == "core_design":
            if content_core and content_core.design_schemes and content_core.selected_scheme_index is None:
                # 方案已生成但未选择
                waiting_for_input = True
                input_prompt = "请选择一个设计方案"
                input_callback = "scheme_selection"
        elif current_stage == "completed":
            # 项目已完成，不需要输入
            waiting_for_input = False
            input_prompt = None
        
        # 创建状态
        state = ProjectState(
            project=project,
            creator_profile=creator_profile,
            field_schema=field_schema,  # 包含默认schema（如果初始化了字段）
            current_stage=current_stage,
            intent=intent,
            consumer_research=consumer_research,
            content_core=content_core,
            content_extension=content_extension,
            waiting_for_input=waiting_for_input,
            input_prompt=input_prompt,
            input_callback=input_callback,
        )
        
        # ✅ 恢复 context_manager 的阶段上下文
        if intent:
            self.context_manager.set_stage_context("intent", intent)
        if consumer_research:
            self.context_manager.set_stage_context("consumer_research", consumer_research)
        if content_core:
            self.context_manager.set_stage_context("content_core", content_core)
        if content_extension:
            self.context_manager.set_stage_context("content_extension", content_extension)
        if creator_profile:
            self.context_manager.set_creator_profile(creator_profile)
        
        return state

