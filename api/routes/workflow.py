# api/routes/workflow.py
# 工作流API - 核心！
# 功能：管理内容生产的完整流程

from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import asyncio
import json

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.models import Project, CreatorProfile, version_manager, FieldSchema
from core.orchestrator import Orchestrator, OrchestratorConfig, ProjectState
from core.ai_client import AIClient
from core.prompt_engine import PromptEngine

router = APIRouter()

STORAGE_PATH = Path("./storage")


def load_field_schema(schema_id: str) -> Optional[FieldSchema]:
    """
    从文件加载 FieldSchema
    
    Args:
        schema_id: Schema ID
        
    Returns:
        FieldSchema 或 None
    """
    schema_path = STORAGE_PATH / "field_schemas" / f"{schema_id}.yaml"
    if schema_path.exists():
        return FieldSchema.load(schema_path)
    return None

# 内存中存储活跃的工作流状态
_active_workflows: Dict[str, ProjectState] = {}
_orchestrators: Dict[str, Orchestrator] = {}


class WorkflowStartRequest(BaseModel):
    """开始工作流请求"""
    profile_id: str
    project_name: str
    raw_input: str


class WorkflowRespondRequest(BaseModel):
    """回复追问请求"""
    answer: str


class WorkflowStatus(BaseModel):
    """工作流状态响应"""
    workflow_id: str
    project_id: str
    current_stage: str
    waiting_for_input: bool
    input_prompt: Optional[str] = None
    clarification_progress: Optional[str] = None  # "2/3"
    ai_call_count: int
    stages: Dict[str, str]  # 各阶段状态


class WorkflowStartResponse(BaseModel):
    """开始工作流响应"""
    workflow_id: str
    project_id: str
    status: WorkflowStatus


def get_orchestrator() -> Orchestrator:
    """获取或创建Orchestrator实例"""
    ai_client = AIClient()
    prompt_engine = PromptEngine(Path("config/prompts"))
    config = OrchestratorConfig(
        max_clarifications=3,
        max_iterations=3,
    )
    return Orchestrator(
        ai_client=ai_client,
        prompt_engine=prompt_engine,
        config=config,
    )


async def ensure_workflow_loaded(workflow_id: str) -> tuple:
    """
    确保工作流已加载到内存
    如果不在内存中，尝试从文件加载
    返回 (state, orchestrator)
    """
    if workflow_id in _active_workflows:
        return _active_workflows[workflow_id], _orchestrators[workflow_id]
    
    # 尝试从文件加载
    project_dir = STORAGE_PATH / "projects" / workflow_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project_file = project_dir / "project.yaml"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="项目文件不存在")
    
    # 加载Project
    project = Project.load(project_file)
    
    # 加载Profile
    profile_path = STORAGE_PATH / "creator_profiles" / f"{project.creator_profile_id}.yaml"
    if not profile_path.exists():
        raise HTTPException(status_code=400, detail="关联的创作者特质不存在")
    
    profile = CreatorProfile.load(profile_path)
    
    # 加载 FieldSchema（如果项目关联了）
    field_schema = None
    if project.field_schema_id:
        field_schema = load_field_schema(project.field_schema_id)
    
    # 创建Orchestrator并加载状态
    orchestrator = get_orchestrator()
    state = orchestrator.load_state(workflow_id)
    
    if state is None:
        state = orchestrator.create_project_state(
            project=project,
            creator_profile=profile,
            field_schema=field_schema,
        )
    elif field_schema and not state.field_schema:
        # 状态存在但没有 field_schema，补充加载
        state.field_schema = field_schema
    
    # 如果字段被初始化了，保存状态（确保持久化）
    if state.content_core and state.content_core.fields:
        orchestrator.save_state(state)
    
    # 保存到内存
    _active_workflows[workflow_id] = state
    _orchestrators[workflow_id] = orchestrator
    
    return state, orchestrator


def build_status(workflow_id: str, state: ProjectState, config: OrchestratorConfig) -> WorkflowStatus:
    """构建状态响应"""
    # 各阶段状态
    stages = {
        "intent": "completed" if state.intent else ("in_progress" if state.current_stage == "intent" else "pending"),
        "research": "completed" if state.consumer_research else ("in_progress" if state.current_stage == "research" else "pending"),
        "core_design": "completed" if state.content_core and state.content_core.selected_scheme_index is not None else ("in_progress" if state.current_stage == "core_design" else "pending"),
        "core_production": "completed" if state.content_core and state.content_core.status == "completed" else ("in_progress" if state.current_stage == "core_production" else "pending"),
        "extension": "completed" if state.content_extension and state.content_extension.status == "completed" else ("in_progress" if state.current_stage == "extension" else "pending"),
    }
    
    # 追问进度
    clarification_progress = None
    if state.waiting_for_input and state.input_callback == "intent_clarification":
        clarification_progress = f"{state.clarification_count}/{config.max_clarifications}"
    
    return WorkflowStatus(
        workflow_id=workflow_id,
        project_id=state.project.id,
        current_stage=state.current_stage,
        waiting_for_input=state.waiting_for_input,
        input_prompt=state.input_prompt,
        clarification_progress=clarification_progress,
        ai_call_count=state.ai_call_count,
        stages=stages,
    )


@router.post("/start", response_model=WorkflowStartResponse)
async def start_workflow(data: WorkflowStartRequest):
    """
    开始新的工作流
    
    1. 创建Project
    2. 加载Profile
    3. 初始化Orchestrator
    4. 运行意图分析第一步
    """
    # 验证Profile
    profile_path = STORAGE_PATH / "creator_profiles" / f"{data.profile_id}.yaml"
    if not profile_path.exists():
        raise HTTPException(status_code=400, detail="创作者特质不存在")
    
    profile = CreatorProfile.load(profile_path)
    
    # 创建Project
    project_id = f"proj_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    project = Project(
        id=project_id,
        name=data.project_name,
        creator_profile_id=data.profile_id,
        status="intent",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # 保存Project
    project_dir = STORAGE_PATH / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    project.save(project_dir / "project.yaml")
    
    # 创建Orchestrator
    orchestrator = get_orchestrator()
    
    # 创建初始状态
    state = orchestrator.create_project_state(
        project=project,
        creator_profile=profile,
    )
    
    # 保存用户初始输入到对话历史
    project.add_message("user", data.raw_input)
    
    # 运行意图分析
    state = orchestrator.run_stage(state, {"raw_input": data.raw_input})
    
    # 保存AI响应到对话历史
    if state.input_prompt:
        project.add_message("assistant", state.input_prompt)
    
    # 保存到内存
    workflow_id = project_id  # 使用project_id作为workflow_id
    _active_workflows[workflow_id] = state
    _orchestrators[workflow_id] = orchestrator
    
    # 保存状态
    orchestrator.save_state(state)
    
    status = build_status(workflow_id, state, orchestrator.config)
    
    return WorkflowStartResponse(
        workflow_id=workflow_id,
        project_id=project_id,
        status=status,
    )


@router.post("/{workflow_id}/respond", response_model=WorkflowStatus)
async def respond_to_workflow(workflow_id: str, data: WorkflowRespondRequest):
    """
    回复追问或用户输入
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.waiting_for_input:
        raise HTTPException(status_code=400, detail="当前不需要输入")
    
    # 保存用户消息到对话历史
    previous_prompt = state.input_prompt
    state.project.add_message("user", data.answer)
    
    # 处理用户输入
    state = orchestrator.run_stage(state, {"answer": data.answer})
    
    # 如果不再需要输入，继续运行直到需要输入或完成
    while not state.waiting_for_input and state.current_stage != "completed":
        state = orchestrator.run_stage(state, {})
    
    # 保存AI响应到对话历史
    if state.input_prompt:
        state.project.add_message("assistant", state.input_prompt)
    elif state.current_stage != state.project.status:
        # 阶段变化，添加系统消息
        state.project.add_message("system", f"进入阶段: {state.current_stage}")
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return build_status(workflow_id, state, orchestrator.config)


@router.get("/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    return build_status(workflow_id, state, orchestrator.config)


@router.get("/{workflow_id}/data")
async def get_workflow_data(workflow_id: str):
    """获取工作流的完整数据"""
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    return {
        "project": {
            "id": state.project.id,
            "name": state.project.name,
            "status": state.project.status,
        },
        "intent": state.intent.model_dump() if state.intent else None,
        "consumer_research": state.consumer_research.model_dump() if state.consumer_research else None,
        "content_core": state.content_core.model_dump() if state.content_core else None,
        "content_extension": state.content_extension.model_dump() if state.content_extension else None,
        "conversation_history": state.project.conversation_history,
    }


@router.post("/{workflow_id}/continue")
async def continue_workflow(workflow_id: str):
    """
    继续运行工作流
    
    智能处理：
    - 如果在 core_production 阶段，开始/继续字段生成
    - 如果在 extension 阶段，开始/继续外延生产
    - 其他情况正常推进
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if state.current_stage == "completed":
        raise HTTPException(status_code=400, detail="工作流已完成")
    
    # 特殊处理 core_production 阶段
    if state.current_stage == "core_production":
        # 确保有选中的方案
        if not state.content_core or state.content_core.selected_scheme_index is None:
            raise HTTPException(status_code=400, detail="请先选择设计方案")
        
        # 标记为不等待输入，开始生成
        state.waiting_for_input = False
    
    # 特殊处理 extension 阶段
    if state.current_stage == "extension":
        state.waiting_for_input = False
    
    # 如果仍需要用户输入（其他阶段），报错
    if state.waiting_for_input and state.current_stage not in ["core_production", "extension"]:
        raise HTTPException(status_code=400, detail="需要用户输入")
    
    # 运行下一步
    state = orchestrator.run_stage(state, {})
    
    # 继续运行直到需要输入或完成
    max_iterations = 10  # 防止无限循环
    iterations = 0
    while not state.waiting_for_input and state.current_stage != "completed" and iterations < max_iterations:
        state = orchestrator.run_stage(state, {})
        iterations += 1
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return build_status(workflow_id, state, orchestrator.config)


@router.post("/{workflow_id}/generate-fields")
async def generate_fields(workflow_id: str):
    """
    生成内涵字段
    
    专门用于内涵生产阶段的字段生成，不依赖当前项目状态。
    会自动回退到 core_production 阶段并开始生成。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    # 确保有 content_core
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 确保有选中的方案
    if state.content_core.selected_scheme_index is None:
        raise HTTPException(status_code=400, detail="请先选择设计方案")
    
    # 确保有 field_schema
    if not state.field_schema:
        from core.models.field_schema import create_default_field_schema
        state.field_schema = create_default_field_schema()
    
    # 确保字段列表已初始化
    if not state.content_core.fields:
        from core.models import ContentField
        for field_def in state.field_schema.get_ordered_fields():
            state.content_core.fields.append(ContentField(
                id=field_def.id or f"field_{len(state.content_core.fields)+1}",
                name=field_def.name,
                status="pending",
            ))
    
    # 获取待生成的字段
    pending_fields = state.content_core.get_pending_fields()
    
    if not pending_fields:
        return {
            "success": True,
            "message": "所有字段已生成完成",
            "generated_count": 0,
            "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
        }
    
    # 强制设置为 core_production 阶段
    state.current_stage = "core_production"
    state.project.status = "core_production"
    state.waiting_for_input = False
    
    # 生成字段（每次调用生成一个）
    state = orchestrator.run_stage(state, {})
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    # 检查生成结果
    current_pending = state.content_core.get_pending_fields()
    generated_count = len(pending_fields) - len(current_pending)
    
    return {
        "success": True,
        "message": f"生成了 {generated_count} 个字段",
        "generated_count": generated_count,
        "remaining_count": len(current_pending),
        "current_stage": state.current_stage,
        "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
    }


@router.post("/load/{project_id}")
async def load_project(project_id: str):
    """
    加载既往项目的进度
    从文件系统读取所有已保存的状态
    """
    project_dir = STORAGE_PATH / "projects" / project_id
    
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project_file = project_dir / "project.yaml"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="项目文件不存在")
    
    # 加载Project
    project = Project.load(project_file)
    
    # 加载Profile（如果不存在则继续，只是不设置profile）
    profile = None
    profile_path = STORAGE_PATH / "creator_profiles" / f"{project.creator_profile_id}.yaml"
    if profile_path.exists():
        profile = CreatorProfile.load(profile_path)
    
    # 创建Orchestrator
    orchestrator = get_orchestrator()
    
    # 从文件加载状态
    state = orchestrator.load_state(project_id)
    
    if state is None:
        # 如果没有保存的状态，创建新状态
        state = orchestrator.create_project_state(
            project=project,
            creator_profile=profile,
        )
    
    # 保存到内存
    workflow_id = project_id
    _active_workflows[workflow_id] = state
    _orchestrators[workflow_id] = orchestrator
    
    status = build_status(workflow_id, state, orchestrator.config)
    
    # 返回完整数据（包括关联的创作者特质）
    return {
        "workflow_id": workflow_id,
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description or "",
            "status": project.status,
            "created_at": str(project.created_at) if project.created_at else "",
            "creator_profile_id": project.creator_profile_id,  # 包含关联的profile ID
        },
        "profile": {
            "id": profile.id,
            "name": profile.name,
        } if profile else None,  # 返回关联的profile基本信息
        "status": status.model_dump(),
        "data": {
            "intent": state.intent.model_dump() if state.intent else None,
            "consumer_research": state.consumer_research.model_dump() if state.consumer_research else None,
            "content_core": state.content_core.model_dump() if state.content_core else None,
            "content_extension": state.content_extension.model_dump() if state.content_extension else None,
        },
        "conversation_history": project.conversation_history,
    }


class RollbackRequest(BaseModel):
    """回退请求"""
    target_stage: str  # 目标阶段
    description: str = ""  # 备份描述


@router.post("/{workflow_id}/rollback")
async def rollback_to_stage(workflow_id: str, request: RollbackRequest):
    """
    回退到指定阶段
    
    功能：
    1. 创建当前状态的版本备份
    2. 清除目标阶段之后的所有数据
    3. 重置项目状态到目标阶段
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    # 阶段顺序
    stage_order = ["intent", "research", "core_design", "core_production", "extension", "completed"]
    
    target_stage = request.target_stage
    if target_stage not in stage_order:
        raise HTTPException(status_code=400, detail=f"无效的目标阶段: {target_stage}")
    
    current_index = stage_order.index(state.current_stage) if state.current_stage in stage_order else 0
    target_index = stage_order.index(target_stage)
    
    if target_index >= current_index:
        raise HTTPException(status_code=400, detail=f"只能回退到之前的阶段")
    
    # 创建版本备份
    stages_to_backup = []
    if state.intent:
        stages_to_backup.append("intent")
    if state.consumer_research:
        stages_to_backup.append("research")
    if state.content_core:
        stages_to_backup.append("core_design")
    if state.content_extension:
        stages_to_backup.append("extension")
    
    version = version_manager.create_version(
        project_id=workflow_id,
        trigger_stage=target_stage,
        trigger_action="rollback",
        description=request.description or f"回退到{target_stage}阶段前的备份",
        stages_to_backup=stages_to_backup,
    )
    
    # 清除目标阶段之后的数据
    if target_index <= stage_order.index("research"):
        state.consumer_research = None
    if target_index <= stage_order.index("core_design"):
        state.content_core = None
    if target_index <= stage_order.index("core_production"):
        if state.content_core:
            state.content_core.selected_scheme_index = None
            state.content_core.fields = []
            state.content_core.status = "scheme_selection"
    if target_index <= stage_order.index("extension"):
        state.content_extension = None
    
    # 重置状态
    state.current_stage = target_stage
    state.project.status = target_stage
    state.waiting_for_input = True
    state.input_prompt = f"已回退到{target_stage}阶段"
    
    # 添加系统消息
    state.project.add_message("system", f"已回退到{target_stage}阶段，之前的版本已备份 (V{version.version_number})")
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "target_stage": target_stage,
        "version_id": version.id,
        "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
    }


class SchemeSelectRequest(BaseModel):
    """选择方案请求"""
    scheme_index: int
    schema_id: Optional[str] = None  # 要使用的字段模板ID
    force_rollback: bool = False  # 强制回退（从后面阶段调用时）


@router.post("/{workflow_id}/select-scheme")
async def select_scheme(workflow_id: str, request: SchemeSelectRequest):
    """
    选择设计方案
    
    支持从任何阶段调用：
    - 如果当前在 core_design/core_production，直接选择
    - 如果当前在更后面的阶段，需要先回退
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    stage_order = ["intent", "research", "core_design", "core_production", "extension", "completed"]
    current_index = stage_order.index(state.current_stage) if state.current_stage in stage_order else 0
    core_design_index = stage_order.index("core_design")
    
    # 如果当前阶段在 core_design 之后，需要先回退
    if current_index > core_design_index:
        if not request.force_rollback:
            # 返回提示，让前端确认是否回退
            return {
                "success": False,
                "need_rollback": True,
                "current_stage": state.current_stage,
                "message": f"当前在{state.current_stage}阶段，重新选择方案将清除后续数据",
            }
        
        # 执行回退
        stages_to_backup = []
        if state.content_core:
            stages_to_backup.append("core_design")
        if state.content_extension:
            stages_to_backup.append("extension")
        
        if stages_to_backup:
            version_manager.create_version(
                project_id=workflow_id,
                trigger_stage="core_design",
                trigger_action="reselect_scheme",
                description="重新选择方案前的备份",
                stages_to_backup=stages_to_backup,
            )
        
        # 清除下游数据
        if state.content_core:
            state.content_core.selected_scheme_index = None
            state.content_core.fields = []
            state.content_core.status = "scheme_selection"
        state.content_extension = None
    
    # 验证方案索引
    if not state.content_core or not state.content_core.design_schemes:
        raise HTTPException(status_code=400, detail="尚未生成设计方案")
    
    if request.scheme_index < 0 or request.scheme_index >= len(state.content_core.design_schemes):
        raise HTTPException(status_code=400, detail=f"方案索引无效，有效范围: 0-{len(state.content_core.design_schemes)-1}")
    
    # 更新选择
    state.content_core.selected_scheme_index = request.scheme_index
    
    # 如果指定了字段模板，加载并设置
    if request.schema_id:
        field_schema = load_field_schema(request.schema_id)
        if field_schema:
            state.field_schema = field_schema
            state.project.field_schema_id = request.schema_id
            state.content_core.field_schema_id = request.schema_id
            
            # 根据新的 FieldSchema 初始化字段列表
            state.content_core.fields = []
            from core.models import ContentField
            for field_def in field_schema.get_ordered_fields():
                state.content_core.fields.append(ContentField(
                    id=field_def.id or f"field_{len(state.content_core.fields)+1}",
                    name=field_def.name,
                    status="pending",
                ))
    
    # 添加系统消息
    scheme_name = f"方案 {request.scheme_index + 1}"
    if isinstance(state.content_core.design_schemes[request.scheme_index], dict):
        scheme_name = state.content_core.design_schemes[request.scheme_index].get("name", scheme_name)
    
    schema_info = f"（字段模板: {state.field_schema.name}）" if state.field_schema else ""
    state.project.add_message("system", f"已选择: {scheme_name}{schema_info}")
    
    # 更新阶段到内涵生产
    state.current_stage = "core_production"
    state.project.status = "core_production"
    state.content_core.status = "field_production"
    state.waiting_for_input = False
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "selected_scheme_index": request.scheme_index,
        "schema_id": request.schema_id,
        "field_count": len(state.content_core.fields) if state.content_core else 0,
        "current_stage": state.current_stage,
        "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
    }


class UpdateFieldRequest(BaseModel):
    """更新字段请求"""
    stage: str  # intent, consumer_research, content_core, content_extension
    field: str
    value: Any
    index: Optional[int] = None  # 如果是列表字段，指定索引


@router.patch("/{workflow_id}/update-field")
async def update_field(workflow_id: str, request: UpdateFieldRequest):
    """
    更新任意阶段的任意字段
    
    支持嵌套更新，如 content_core.design_schemes[0].name
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    stage_data = None
    if request.stage == "intent":
        stage_data = state.intent
    elif request.stage == "consumer_research":
        stage_data = state.consumer_research
    elif request.stage == "content_core":
        stage_data = state.content_core
    elif request.stage == "content_extension":
        stage_data = state.content_extension
    else:
        raise HTTPException(status_code=400, detail=f"未知阶段: {request.stage}")
    
    if stage_data is None:
        raise HTTPException(status_code=400, detail=f"阶段 {request.stage} 数据不存在")
    
    # 更新字段
    try:
        if request.index is not None:
            # 列表字段更新
            current_list = getattr(stage_data, request.field, [])
            if isinstance(current_list, list) and 0 <= request.index < len(current_list):
                current_list[request.index] = request.value
                setattr(stage_data, request.field, current_list)
            else:
                raise HTTPException(status_code=400, detail=f"索引 {request.index} 无效")
        else:
            # 直接字段更新
            setattr(stage_data, request.field, request.value)
    except AttributeError:
        raise HTTPException(status_code=400, detail=f"字段 {request.field} 不存在")
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "stage": request.stage,
        "field": request.field,
    }


class ChangeSchemaRequest(BaseModel):
    """更换字段模板请求"""
    schema_id: str
    force: bool = False  # 是否强制更换（会重置内涵生产数据）


@router.post("/{workflow_id}/change-schema")
async def change_field_schema(workflow_id: str, request: ChangeSchemaRequest):
    """
    更换项目的字段模板
    
    如果项目已有内涵生产数据，需要 force=True 确认重置
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    # 检查是否有已生成的内涵数据需要重置
    has_production_data = (
        state.content_core and 
        (state.content_core.fields or state.content_core.selected_scheme_index is not None)
    )
    
    if has_production_data and not request.force:
        return {
            "success": False,
            "need_confirm": True,
            "message": "项目已有内涵生产数据，更换模板将重置这些数据。请设置 force=True 确认。",
            "current_fields": [f.name for f in state.content_core.fields] if state.content_core else [],
        }
    
    # 加载新的字段模板
    new_schema = load_field_schema(request.schema_id)
    if not new_schema:
        raise HTTPException(status_code=404, detail=f"字段模板 {request.schema_id} 不存在")
    
    # 如果有数据需要重置，先创建版本备份
    if has_production_data:
        version_manager.create_version(
            project_id=workflow_id,
            trigger_stage="core_production",
            trigger_action="change_schema",
            description=f"更换字段模板为 {new_schema.name}",
            stages_to_backup=["core_design", "extension"],
        )
        
        # 重置内涵生产数据
        if state.content_core:
            state.content_core.fields = []
            state.content_core.selected_scheme_index = None
            state.content_core.status = "scheme_selection"
        state.content_extension = None
        
        # 回退项目状态到内涵生产阶段
        state.current_stage = "core_production"
        state.project.status = "core_production"
        state.waiting_for_input = False
    
    # 更新字段模板
    state.field_schema = new_schema
    state.project.field_schema_id = request.schema_id
    
    # 如果有 content_core，根据新模板初始化字段列表
    if state.content_core:
        from core.models import ContentField
        state.content_core.field_schema_id = request.schema_id
        for field_def in new_schema.get_ordered_fields():
            state.content_core.fields.append(ContentField(
                id=field_def.id or f"field_{len(state.content_core.fields)+1}",
                name=field_def.name,
                status="pending",
            ))
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "schema_id": request.schema_id,
        "schema_name": new_schema.name,
        "field_count": len(new_schema.fields),
        "fields": [f.name for f in new_schema.get_ordered_fields()],
    }


class AgentChatRequest(BaseModel):
    """Agent对话请求"""
    message: str
    contexts: List[Dict[str, str]] = []


@router.post("/{workflow_id}/agent-chat")
async def agent_chat(workflow_id: str, request: AgentChatRequest):
    """
    Agent对话 - 支持@引用的智能对话
    
    用户可以通过@引用来指定上下文，AI会理解并处理用户的请求。
    例如：
    - "@意图分析 修改目标为XXX"
    - "@消费者调研 调整用户画像"
    - "@内涵设计 选择方案1"
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    message = request.message
    contexts = request.contexts
    
    # 构建上下文提示
    context_text = ""
    for ctx in contexts:
        context_text += f"\n\n【{ctx.get('type', '上下文')}】\n{ctx.get('content', '')}"
    
    # 构建Agent系统提示
    system_prompt = """你是一个内容生产助手。用户正在进行内容生产项目，可以通过@引用来查看和修改各阶段的内容。

你的职责：
1. 理解用户的意图
2. 基于引用的上下文回答问题或提供建议
3. 如果用户要求修改内容，明确说明修改建议
4. 保持回复简洁有用

当前项目阶段：{}
当前项目状态：{}

{}
""".format(
        state.current_stage,
        "等待用户输入" if state.waiting_for_input else "自动运行中",
        context_text if context_text else "暂无引用上下文",
    )
    
    # 添加Golden Context
    golden_context = ""
    if state.creator_profile:
        golden_context += f"\n创作者特质：{state.creator_profile.name}"
    if state.intent:
        golden_context += f"\n项目目标：{state.intent.goal if hasattr(state.intent, 'goal') else '未定义'}"
    
    if golden_context:
        system_prompt += f"\n\n【Golden Context】{golden_context}"
    
    # 调用AI
    ai_client = orchestrator.ai_client
    response = ai_client.chat(
        system_prompt=system_prompt,
        user_message=message,
    )
    
    # 记录对话
    if hasattr(state.project, 'add_message'):
        state.project.add_message("user", message, state.current_stage)
        state.project.add_message("assistant", response, state.current_stage)
    
    # 保存状态
    orchestrator.save_state(state)
    
    # 检查是否需要执行修改操作
    # 这里可以扩展：解析AI的响应，判断是否有具体的修改操作需要执行
    updated = False
    
    return {
        "response": response,
        "updated": updated,
        "current_stage": state.current_stage,
    }


# ============ 版本管理 API ============

class CreateVersionRequest(BaseModel):
    """创建版本请求"""
    description: str = ""
    trigger_stage: str = "manual"
    trigger_action: str = "manual"


@router.get("/{workflow_id}/versions")
async def list_versions(workflow_id: str):
    """列出项目的所有版本"""
    versions = version_manager.list_versions(workflow_id)
    return {
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "description": v.description,
                "trigger_stage": v.trigger_stage,
                "trigger_action": v.trigger_action,
                "created_at": str(v.created_at),
                "backed_up_stages": v.backed_up_stages,
            }
            for v in versions
        ]
    }


@router.post("/{workflow_id}/versions")
async def create_version(workflow_id: str, request: CreateVersionRequest):
    """手动创建版本备份"""
    state, _ = await ensure_workflow_loaded(workflow_id)
    
    # 确定需要备份的阶段
    stages_to_backup = []
    if state.intent:
        stages_to_backup.append("intent")
    if state.consumer_research:
        stages_to_backup.append("research")
    if state.content_core:
        stages_to_backup.append("core_design")
    if state.content_extension:
        stages_to_backup.append("extension")
    
    version = version_manager.create_version(
        project_id=workflow_id,
        trigger_stage=request.trigger_stage,
        trigger_action=request.trigger_action,
        description=request.description,
        stages_to_backup=stages_to_backup,
    )
    
    return {
        "success": True,
        "version": {
            "id": version.id,
            "version_number": version.version_number,
            "description": version.description,
            "backed_up_stages": version.backed_up_stages,
        }
    }


@router.post("/{workflow_id}/versions/{version_id}/restore")
async def restore_version(workflow_id: str, version_id: str):
    """恢复到指定版本"""
    success = version_manager.restore_version(workflow_id, version_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 重新加载状态
    if workflow_id in _active_workflows:
        del _active_workflows[workflow_id]
    if workflow_id in _orchestrators:
        del _orchestrators[workflow_id]
    
    return {"success": True, "message": "版本已恢复"}


@router.delete("/{workflow_id}/versions/{version_id}")
async def delete_version(workflow_id: str, version_id: str):
    """删除版本"""
    success = version_manager.delete_version(workflow_id, version_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return {"success": True}


@router.post("/{workflow_id}/check-version-needed")
async def check_version_needed(workflow_id: str, data: Dict[str, Any]):
    """
    检查是否需要创建版本
    
    在用户修改上游阶段前调用，检查是否有下游数据需要备份
    """
    state, _ = await ensure_workflow_loaded(workflow_id)
    modified_stage = data.get("stage", "")
    
    # 构建下游状态
    downstream_stages = {
        "research": state.consumer_research is not None,
        "core_design": state.content_core is not None,
        "core_production": state.content_core is not None and state.content_core.status == "completed",
        "extension": state.content_extension is not None,
    }
    
    should_create = version_manager.should_create_version(
        workflow_id, modified_stage, downstream_stages
    )
    
    return {
        "should_create_version": should_create,
        "downstream_stages": [k for k, v in downstream_stages.items() if v],
        "message": "修改此阶段将影响下游数据，建议先创建版本备份" if should_create else "",
    }
