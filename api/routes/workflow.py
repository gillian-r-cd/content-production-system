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

from core.models import Project, CreatorProfile, version_manager, FieldSchema, log_store
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
    else:
        # 状态已存在，确保 field_schema 被正确加载
        # 优先使用从 project.field_schema_id 加载的，如果已有则不覆盖
        if field_schema and not state.field_schema:
            state.field_schema = field_schema
        elif field_schema and state.field_schema and state.field_schema.id != field_schema.id:
            # 如果 project 关联的 schema 和 state 中的不一致，使用项目关联的
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


# ============ 目录结构管理 API ============

class SectionField(BaseModel):
    """章节字段"""
    id: str = ""
    name: str
    display_name: str = ""
    description: str = ""
    order: int = 0


class ContentSectionRequest(BaseModel):
    """内容章节"""
    id: str = ""
    name: str
    description: str = ""
    order: int = 0
    fields: List[SectionField] = []


class UpdateOutlineRequest(BaseModel):
    """更新目录结构请求"""
    sections: List[ContentSectionRequest]
    confirm: bool = False  # 是否确认目录结构


@router.get("/{workflow_id}/outline")
async def get_outline(workflow_id: str):
    """
    获取内涵生产的目录结构
    
    返回当前的章节和字段结构
    """
    state, _ = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        return {
            "sections": [],
            "outline_confirmed": False,
            "status": "no_content_core",
        }
    
    # 返回目录结构
    sections_data = []
    for section in state.content_core.sections:
        sections_data.append({
            "id": section.id,
            "name": section.name,
            "description": section.description,
            "order": section.order,
            "status": section.status,
            "fields": [
                {
                    "id": f.id,
                    "name": f.name,
                    "display_name": f.display_name,
                    "description": f.description,
                    "order": f.order,
                    "status": f.status,
                    "content": f.content,  # 返回完整内容
                }
                for f in section.fields
            ]
        })
    
    return {
        "sections": sections_data,
        "outline_confirmed": state.content_core.outline_confirmed,
        "status": state.content_core.status,
        "progress": {
            "completed": state.content_core.get_completed_field_count(),
            "total": state.content_core.get_total_field_count(),
            "percentage": state.content_core.get_progress_percentage(),
        }
    }


@router.patch("/{workflow_id}/outline")
async def update_outline(workflow_id: str, request: UpdateOutlineRequest):
    """
    更新目录结构
    
    保存用户对章节和字段的编辑，可选择同时确认目录结构
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 允许编辑，但如果有已完成字段，返回警告信息
    warning_message = None
    completed_count = state.content_core.get_completed_field_count()
    if completed_count > 0:
        warning_message = f"目录结构已更新。注意：有 {completed_count} 个字段已生成内容，修改目录可能影响内容一致性。"
    
    # 更新章节结构，保留已有字段的内容和状态
    from core.models import ContentSection, ContentField
    
    # 先建立现有字段的索引（按ID查找）
    existing_fields = {}
    for section in state.content_core.sections:
        for field in section.fields:
            existing_fields[field.id] = field
    
    new_sections = []
    for i, section_req in enumerate(request.sections):
        # 处理字段，保留已有内容
        new_fields = []
        for j, f in enumerate(section_req.fields):
            field_id = f.id or f"field_{i}_{j+1}"
            
            # 如果是已存在的字段，保留其内容和状态
            if field_id in existing_fields:
                existing = existing_fields[field_id]
                new_field = ContentField(
                    id=field_id,
                    name=f.name,
                    display_name=f.display_name or f.name,
                    description=f.description,
                    order=f.order if f.order else j,
                    status=existing.status,  # 保留状态
                    content=existing.content,  # 保留内容
                    clarification_answer=existing.clarification_answer,  # 保留澄清回答
                    iteration_count=existing.iteration_count,
                    iteration_history=existing.iteration_history,
                    evaluation_score=existing.evaluation_score,
                    evaluation_feedback=existing.evaluation_feedback,
                )
            else:
                # 新字段
                new_field = ContentField(
                    id=field_id,
                    name=f.name,
                    display_name=f.display_name or f.name,
                    description=f.description,
                    order=f.order if f.order else j,
                    status="pending",
                )
            new_fields.append(new_field)
        
        section = ContentSection(
            id=section_req.id or f"section_{i+1}",
            name=section_req.name,
            description=section_req.description,
            order=section_req.order if section_req.order else i,
            fields=new_fields,
        )
        new_sections.append(section)
    
    state.content_core.sections = new_sections
    
    # 如果请求确认目录
    if request.confirm:
        state.content_core.outline_confirmed = True
        state.content_core.status = "outline_confirmed"
    else:
        state.content_core.status = "outline_editing"
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "sections": len(state.content_core.sections),
        "total_fields": state.content_core.get_total_field_count(),
        "outline_confirmed": state.content_core.outline_confirmed,
        "status": state.content_core.status,
        "warning": warning_message,
    }


@router.post("/{workflow_id}/outline/confirm")
async def confirm_outline(workflow_id: str):
    """
    确认目录结构
    
    确认后才能开始内涵生产
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    if not state.content_core.sections:
        raise HTTPException(status_code=400, detail="请先添加至少一个章节")
    
    # 检查是否有字段
    total_fields = state.content_core.get_total_field_count()
    if total_fields == 0:
        raise HTTPException(status_code=400, detail="请在章节中添加至少一个字段")
    
    # 确认目录
    state.content_core.outline_confirmed = True
    state.content_core.status = "outline_confirmed"
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "message": "目录结构已确认，可以开始生产",
        "total_sections": len(state.content_core.sections),
        "total_fields": total_fields,
    }


@router.post("/{workflow_id}/outline/add-section")
async def add_section(workflow_id: str, name: str = "新章节"):
    """
    添加新章节
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    from core.models import ContentSection
    import uuid
    
    new_section = ContentSection(
        id=str(uuid.uuid4())[:8],
        name=name,
        order=len(state.content_core.sections),
    )
    
    state.content_core.sections.append(new_section)
    # 不重置 outline_confirmed，允许随时添加章节
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "section": {
            "id": new_section.id,
            "name": new_section.name,
            "order": new_section.order,
        }
    }


@router.delete("/{workflow_id}/sections/{section_id}")
async def delete_section(workflow_id: str, section_id: str):
    """
    删除章节
    
    删除指定章节及其所有字段。即使目录已确认，也允许删除。
    返回删除的字段数量，供前端显示警告。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 找到目标章节
    section = state.content_core.get_section(section_id)
    if not section:
        raise HTTPException(status_code=404, detail=f"章节 {section_id} 不存在")
    
    # 统计删除的内容
    deleted_fields = len(section.fields)
    completed_fields = sum(1 for f in section.fields if f.status == "completed")
    
    # 执行删除
    state.content_core.sections = [s for s in state.content_core.sections if s.id != section_id]
    
    # 重新编号
    for i, s in enumerate(state.content_core.sections):
        s.order = i
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "deleted_section": section.name,
        "deleted_fields": deleted_fields,
        "deleted_completed_fields": completed_fields,
        "warning": f"已删除章节 '{section.name}' 及其 {deleted_fields} 个字段（包含 {completed_fields} 个已完成字段）" if completed_fields > 0 else None,
    }


@router.delete("/{workflow_id}/sections/{section_id}/fields/{field_id}")
async def delete_field(workflow_id: str, section_id: str, field_id: str):
    """
    删除字段
    
    删除指定章节中的指定字段。即使目录已确认或字段已生成，也允许删除。
    返回删除的字段信息，供前端显示警告。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 找到目标章节
    section = state.content_core.get_section(section_id)
    if not section:
        raise HTTPException(status_code=404, detail=f"章节 {section_id} 不存在")
    
    # 找到目标字段
    target_field = None
    for f in section.fields:
        if f.id == field_id:
            target_field = f
            break
    
    if not target_field:
        raise HTTPException(status_code=404, detail=f"字段 {field_id} 不存在于章节 {section_id}")
    
    was_completed = target_field.status == "completed"
    field_name = target_field.display_name or target_field.name
    
    # 执行删除
    section.fields = [f for f in section.fields if f.id != field_id]
    
    # 重新编号
    for i, f in enumerate(section.fields):
        f.order = i
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "deleted_field": field_name,
        "was_completed": was_completed,
        "warning": f"已删除已完成的字段 '{field_name}'" if was_completed else None,
    }


class AddFieldRequest(BaseModel):
    """添加字段请求"""
    section_id: str
    name: str = "新字段"
    display_name: str = ""


@router.post("/{workflow_id}/outline/add-field")
async def add_field_to_section(workflow_id: str, request: AddFieldRequest):
    """
    向章节添加新字段
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    section = state.content_core.get_section(request.section_id)
    if not section:
        raise HTTPException(status_code=404, detail=f"章节 {request.section_id} 不存在")
    
    from core.models import ContentField
    import uuid
    
    new_field = ContentField(
        id=str(uuid.uuid4())[:8],
        name=request.name,
        display_name=request.display_name or request.name,
        order=len(section.fields),
        status="pending",
    )
    
    section.fields.append(new_field)
    # 不重置 outline_confirmed，允许随时添加字段
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "field": {
            "id": new_field.id,
            "name": new_field.name,
            "display_name": new_field.display_name,
            "order": new_field.order,
        }
    }


class ReorderSectionsRequest(BaseModel):
    """章节排序请求"""
    section_ids: List[str]


class ReorderFieldsRequest(BaseModel):
    """字段排序请求"""
    field_ids: List[str]


@router.patch("/{workflow_id}/sections/reorder")
async def reorder_sections(workflow_id: str, request: ReorderSectionsRequest):
    """
    重新排序章节
    
    根据提供的section_ids列表顺序，重新排列章节。
    目录确认后仍可排序，但会有警告。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 如果有已完成字段，返回警告但允许操作
    warning_message = None
    completed_count = state.content_core.get_completed_field_count()
    if completed_count > 0:
        warning_message = f"章节已重新排序。注意：有 {completed_count} 个字段已生成内容，重新排序可能影响内容的逻辑顺序。"
    
    # 验证所有section_id都存在
    current_ids = {s.id for s in state.content_core.sections}
    requested_ids = set(request.section_ids)
    
    if current_ids != requested_ids:
        raise HTTPException(status_code=400, detail="section_ids列表与现有章节不匹配")
    
    # 重新排序
    section_map = {s.id: s for s in state.content_core.sections}
    new_sections = []
    for i, sid in enumerate(request.section_ids):
        section = section_map[sid]
        section.order = i
        new_sections.append(section)
    
    state.content_core.sections = new_sections
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "sections": [{"id": s.id, "name": s.name, "order": s.order} for s in new_sections],
        "warning": warning_message,
    }


@router.patch("/{workflow_id}/sections/{section_id}/fields/reorder")
async def reorder_fields_in_section(workflow_id: str, section_id: str, request: ReorderFieldsRequest):
    """
    重新排序章节内的字段
    
    根据提供的field_ids列表顺序，重新排列字段。
    目录确认后仍可排序未生成的字段。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 如果有已完成字段，返回警告但允许操作
    warning_message = None
    completed_count = state.content_core.get_completed_field_count()
    if completed_count > 0:
        warning_message = f"字段已重新排序。注意：有 {completed_count} 个字段已生成内容，重新排序可能影响内容的逻辑顺序。"
    
    # 找到目标章节
    section = state.content_core.get_section(section_id)
    if not section:
        raise HTTPException(status_code=404, detail=f"章节 {section_id} 不存在")
    
    # 验证所有field_id都存在
    current_ids = {f.id for f in section.fields}
    requested_ids = set(request.field_ids)
    
    if current_ids != requested_ids:
        raise HTTPException(status_code=400, detail="field_ids列表与现有字段不匹配")
    
    # 重新排序
    field_map = {f.id: f for f in section.fields}
    new_fields = []
    for i, fid in enumerate(request.field_ids):
        field = field_map[fid]
        field.order = i
        new_fields.append(field)
    
    section.fields = new_fields
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "fields": [{"id": f.id, "name": f.name, "order": f.order} for f in new_fields],
        "warning": warning_message,
    }


@router.post("/{workflow_id}/fields/{field_id}/regenerate")
async def regenerate_single_field(workflow_id: str, field_id: str):
    """
    重新生成单个字段
    
    重新生成指定字段的内容，并标记其后续依赖字段为"过期"状态。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 找到目标字段
    target_field = state.content_core.get_field(field_id)
    if not target_field:
        raise HTTPException(status_code=404, detail=f"字段 {field_id} 不存在")
    
    # 标记为生成中
    target_field.status = "generating"
    
    # 确保有 field_schema
    if not state.field_schema:
        from core.models.field_schema import create_default_field_schema
        state.field_schema = create_default_field_schema()
    
    # 设置状态为生产阶段
    state.current_stage = "core_production"
    state.project.status = "core_production"
    state.waiting_for_input = False
    
    try:
        # 调用 orchestrator 生成单个字段
        # 找到字段在章节中的位置
        for section in state.content_core.sections:
            for i, field in enumerate(section.fields):
                if field.id == field_id:
                    # 设置当前生成位置
                    state.content_core.current_section_index = state.content_core.sections.index(section)
                    state.content_core.current_field_index = i
                    break
        
        # 运行生成
        state = orchestrator.run_stage(state, {"target_field_id": field_id})
        
        # 标记后续字段为过期
        stale_count = 0
        found_target = False
        for section in state.content_core.sections:
            for field in section.fields:
                if field.id == field_id:
                    found_target = True
                    continue
                if found_target and field.status == "completed":
                    if hasattr(field, 'context_stale'):
                        field.context_stale = True
                    stale_count += 1
        
        # 更新内存和保存
        _active_workflows[workflow_id] = state
        orchestrator.save_state(state)
        
        return {
            "success": True,
            "field": {
                "id": target_field.id,
                "name": target_field.name,
                "status": target_field.status,
                "content": target_field.content,  # 返回完整内容
            },
            "downstream_stale_count": stale_count,
        }
        
    except Exception as e:
        target_field.status = "failed"
        _active_workflows[workflow_id] = state
        orchestrator.save_state(state)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/{workflow_id}/chains/{chain_id}/regenerate")
async def regenerate_chain(workflow_id: str, chain_id: str):
    """
    重新生成整条依赖链
    
    从链头开始，按顺序重新生成链中所有字段。
    chain_id 可以是链头字段的ID。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 找到链头字段
    chain_head = state.content_core.get_field(chain_id)
    if not chain_head:
        raise HTTPException(status_code=404, detail=f"链头字段 {chain_id} 不存在")
    
    # 收集链中所有字段（从链头开始到后续所有字段）
    chain_fields = []
    found_head = False
    
    for section in state.content_core.sections:
        for field in section.fields:
            if field.id == chain_id:
                found_head = True
            if found_head:
                chain_fields.append(field)
    
    if not chain_fields:
        raise HTTPException(status_code=404, detail="未找到链中的字段")
    
    # 逐个重新生成
    regenerated_count = 0
    
    for field in chain_fields:
        field.status = "generating"
        
        try:
            # 找到字段位置
            for section in state.content_core.sections:
                for i, f in enumerate(section.fields):
                    if f.id == field.id:
                        state.content_core.current_section_index = state.content_core.sections.index(section)
                        state.content_core.current_field_index = i
                        break
            
            # 运行生成
            state.waiting_for_input = False
            state = orchestrator.run_stage(state, {"target_field_id": field.id})
            regenerated_count += 1
            
        except Exception as e:
            field.status = "failed"
            # 继续处理下一个字段
            continue
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "chain_id": chain_id,
        "regenerated_count": regenerated_count,
        "total_in_chain": len(chain_fields),
        "fields": [
            {
                "id": f.id,
                "name": f.name,
                "status": f.status,
            }
            for f in chain_fields
        ]
    }


class ResetGeneratingFieldsRequest(BaseModel):
    """重置生成中字段请求"""
    pass  # 无需参数，重置所有 generating 状态的字段


@router.post("/{workflow_id}/reset-generating-fields")
async def reset_generating_fields(workflow_id: str):
    """
    重置所有状态为 'generating' 的字段为 'pending'
    
    用于处理生成过程中断导致字段卡住的情况
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="没有内涵生产数据")
    
    reset_count = 0
    
    # 遍历所有章节和字段
    for section in state.content_core.sections:
        for field in section.fields:
            if field.status == "generating":
                field.status = "pending"
                reset_count += 1
    
    # 也检查扁平字段列表（向后兼容）
    for field in state.content_core.fields:
        if field.status == "generating":
            field.status = "pending"
            reset_count += 1
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "reset_count": reset_count,
        "message": f"已重置 {reset_count} 个卡住的字段"
    }


class MarkStaleRequest(BaseModel):
    """标记字段过时请求"""
    modified_field_id: str


@router.post("/{workflow_id}/mark-stale")
async def mark_fields_stale(workflow_id: str, request: MarkStaleRequest):
    """
    标记依赖于已修改字段的后续字段为"过时"
    
    当某个字段内容被手动修改后，其后续字段的生成上下文可能已过期。
    此API用于标记这些后续字段，提示用户可能需要重新生成。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 找到被修改字段的位置
    modified_field_idx = None
    modified_section_idx = None
    
    for i, section in enumerate(state.content_core.sections):
        for j, field in enumerate(section.fields):
            if field.id == request.modified_field_id:
                modified_section_idx = i
                modified_field_idx = j
                break
        if modified_field_idx is not None:
            break
    
    if modified_field_idx is None:
        raise HTTPException(status_code=404, detail=f"字段 {request.modified_field_id} 不存在")
    
    # 标记后续字段为stale
    stale_count = 0
    found_modified = False
    
    for i, section in enumerate(state.content_core.sections):
        for j, field in enumerate(section.fields):
            if field.id == request.modified_field_id:
                found_modified = True
                continue
            if found_modified and field.status == "completed":
                field.context_stale = True
                stale_count += 1
    
    # 保存状态
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "stale_count": stale_count,
        "message": f"已标记 {stale_count} 个后续字段为过时状态"
    }


@router.post("/{workflow_id}/confirm-outline")
async def confirm_outline(workflow_id: str):
    """
    确认目录结构并开始生产
    
    用户编辑完目录结构后调用此API确认，之后可以开始生成字段。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先选择设计方案")
    
    if state.content_core.selected_scheme_index is None:
        raise HTTPException(status_code=400, detail="请先选择设计方案")
    
    # 检查是否有字段
    if state.content_core.get_total_field_count() == 0:
        raise HTTPException(status_code=400, detail="目录中没有字段，请先添加字段")
    
    # 确认目录结构
    state.content_core.outline_confirmed = True
    state.content_core.status = "field_production"
    state.waiting_for_input = False
    state.input_prompt = None
    state.input_callback = None
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "message": "目录结构已确认，可以开始生产",
        "total_fields": state.content_core.get_total_field_count(),
        "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
    }


@router.post("/{workflow_id}/generate-fields")
async def generate_fields(workflow_id: str):
    """
    生成内涵字段
    
    专门用于内涵生产阶段的字段生成。
    要求：
    1. 必须先选择设计方案
    2. 按章节和字段顺序逐个生成
    
    注意：目录结构可随时编辑，即使在生产过程中。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    # 确保有 content_core
    if not state.content_core:
        raise HTTPException(status_code=400, detail="请先完成设计方案选择")
    
    # 确保有选中的方案
    if state.content_core.selected_scheme_index is None:
        raise HTTPException(status_code=400, detail="请先选择设计方案")
    
    # 确保目录结构已确认
    if not state.content_core.outline_confirmed:
        raise HTTPException(status_code=400, detail="请先确认目录结构")
    
    # 确保有 field_schema
    if not state.field_schema:
        from core.models.field_schema import create_default_field_schema
        state.field_schema = create_default_field_schema()
    
    # 如果使用新的 sections 结构
    if state.content_core.sections:
        # 确保章节中有字段
        if state.content_core.get_total_field_count() == 0:
            raise HTTPException(status_code=400, detail="目录中没有待生成的字段")
    else:
        # 向后兼容：使用扁平字段列表
        if not state.content_core.fields:
            from core.models import ContentField
            for field_def in state.field_schema.get_ordered_fields():
                state.content_core.fields.append(ContentField(
                    id=field_def.id or f"field_{len(state.content_core.fields)+1}",
                    name=field_def.name,
                    status="pending",
                ))
    
    # 获取待生成的字段（包括 pending 和卡住的 generating）
    pending_fields = [
        f for f in state.content_core.get_all_fields()
        if f.status in ("pending", "generating")
    ]
    completed_before = state.content_core.get_completed_field_count()
    
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
    
    # 检查生成结果：基于 completed 数量的变化来判断是否真正生成成功
    completed_after = state.content_core.get_completed_field_count()
    generated_count = completed_after - completed_before
    
    # 计算剩余待生成字段（pending 和 generating 都算）
    remaining = [
        f for f in state.content_core.get_all_fields()
        if f.status in ("pending", "generating")
    ]
    
    # 检查是否需要用户回答问题
    if state.waiting_for_input and state.input_callback == "field_clarification":
        # state.current_field 现在存储的是字段 ID
        current_field_id = state.current_field
        current_field_obj = state.content_core.get_field(current_field_id) if current_field_id else None
        current_field_name = current_field_obj.name if current_field_obj else None
        
        # 从 field_schema 获取问题
        clarification_question = None
        if state.field_schema and current_field_name:
            field_def = state.field_schema.get_field(current_field_name)
            if field_def:
                clarification_question = field_def.clarification_prompt
        
        return {
            "success": True,
            "message": "需要用户回答问题后继续生成",
            "generated_count": generated_count,
            "remaining_count": len(remaining),
            "current_stage": state.current_stage,
            "waiting_for_clarification": True,
            "clarification": {
                "field_id": current_field_id,  # 使用 ID 精确查找
                "field_name": current_field_name,
                "question": clarification_question,
            },
            "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
        }
    
    return {
        "success": True,
        "message": f"生成了 {generated_count} 个字段" if generated_count > 0 else "字段正在生成中...",
        "generated_count": generated_count,
        "remaining_count": len(remaining),
        "current_stage": state.current_stage,
        "waiting_for_clarification": False,
        "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
    }


class FieldClarificationRequest(BaseModel):
    """字段澄清回答请求"""
    answer: str
    field_id: Optional[str] = None    # 字段ID，精确查找（优先使用）
    field_name: Optional[str] = None  # 字段名称，向后兼容


@router.post("/{workflow_id}/fields/clarify")
async def clarify_field(workflow_id: str, request: FieldClarificationRequest):
    """
    回答字段生成前的澄清问题
    
    用户回答问题后，系统将继续生成该字段。
    不依赖内存状态，直接设置字段的 clarification_answer。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.content_core:
        raise HTTPException(status_code=400, detail="内涵生产尚未开始")
    
    # 查找需要回答的字段
    target_field = None
    
    # 优先使用请求中的 field_id（精确匹配）
    if request.field_id:
        target_field = state.content_core.get_field(request.field_id)
    
    # 如果没有 field_id，尝试使用 field_name（向后兼容）
    if not target_field and request.field_name:
        target_field = state.content_core.get_field(request.field_name)
    
    # 如果没有指定，尝试从 current_field 获取（现在存储的是 ID）
    if not target_field and state.current_field:
        target_field = state.content_core.get_field(state.current_field)
    
    # 如果还没找到，查找第一个 pending 且需要澄清的字段
    if not target_field:
        for field in state.content_core.get_all_fields():
            if field.status == "pending" and not field.clarification_answer:
                # 检查该字段是否有 clarification_prompt
                if state.field_schema:
                    field_def = state.field_schema.get_field(field.name)
                    if field_def and field_def.clarification_prompt:
                        target_field = field
                        break
    
    if not target_field:
        raise HTTPException(status_code=400, detail="未找到需要回答的字段")
    
    # 设置澄清回答
    target_field.clarification_answer = request.answer
    
    # 重置等待状态
    state.waiting_for_input = False
    state.input_callback = None
    state.input_prompt = None
    
    # 更新内存和保存
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    # 计算剩余字段
    remaining = [
        f for f in state.content_core.get_all_fields()
        if f.status in ("pending", "generating")
    ]
    
    return {
        "success": True,
        "message": f"已收到字段 '{target_field.name}' 的回答，请继续生成",
        "field_name": target_field.name,
        "remaining_count": len(remaining),
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
    
    # 加载项目历史日志
    log_store.load_project_logs(project_id)
    
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
    
    # 确保 intent 阶段有正确的 input_callback
    # 这是关键修复：加载项目后需要设置正确的回调以处理用户输入
    if state.current_stage == "intent" and not state.intent:
        state.waiting_for_input = True
        state.input_prompt = "请描述你想要生产的内容"
        state.input_callback = "intent_input"  # 关键：设置正确的回调
    elif state.current_stage == "intent" and state.intent and not state.consumer_research:
        # 已有意图但未进入调研，等待确认
        state.waiting_for_input = True
        state.input_prompt = "意图分析已完成，请确认后进入消费者调研阶段。"
        state.input_callback = "confirm_intent"
    elif state.current_stage == "research" and state.consumer_research and not state.content_core:
        # 调研完成但未进入设计
        state.waiting_for_input = True
        state.input_prompt = "消费者调研已完成，请确认后进入内涵设计阶段。"
        state.input_callback = "confirm_research"
    elif state.current_stage == "core_design" and state.content_core and state.content_core.selected_scheme_index is None:
        # 有方案但未选择
        state.waiting_for_input = True
        state.input_prompt = "请选择一个设计方案（输入1-3的数字）："
        state.input_callback = "scheme_selection"
    
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
            "taboos": {
                "forbidden_words": profile.taboos.forbidden_words if profile.taboos else [],
                "forbidden_topics": profile.taboos.forbidden_topics if profile.taboos else [],
                "forbidden_patterns": getattr(profile.taboos, 'forbidden_patterns', []) if profile.taboos else [],
            },
            "example_texts": profile.example_texts or [],
            "custom_fields": profile.custom_fields or {},
        } if profile else None,  # 返回关联的profile完整信息
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


@router.post("/{workflow_id}/regenerate-schemes")
async def regenerate_schemes(workflow_id: str):
    """
    重新生成设计方案
    
    重新调用 AI 生成新的设计方案，替换当前方案。
    如果有已生成的内容，会先创建版本备份。
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    # 检查是否有意图和调研数据（这些是生成方案的前置条件）
    if not state.intent:
        raise HTTPException(status_code=400, detail="请先完成意图分析")
    if not state.consumer_research:
        raise HTTPException(status_code=400, detail="请先完成消费者调研")
    
    # 如果有已生成的内容，创建版本备份
    if state.content_core and state.content_core.design_schemes:
        version_manager.create_version(
            project_id=workflow_id,
            trigger_stage="core_design",
            trigger_action="regenerate_schemes",
            description="重新生成设计方案前的备份",
            stages_to_backup=["core_design"],
        )
    
    # 清空当前的设计方案（保留字段模板选择）
    field_schema = state.field_schema
    if state.content_core:
        state.content_core.design_schemes = []
        state.content_core.selected_scheme_index = None
        state.content_core.fields = []
        state.content_core.status = "scheme_generation"
    
    # 设置状态为内涵设计阶段
    state.current_stage = "core_design"
    state.project.status = "core_design"
    state.waiting_for_input = False
    
    # 确保上下文管理器有正确的数据
    orchestrator.context_manager.set_stage_context("intent", state.intent)
    orchestrator.context_manager.set_stage_context("consumer_research", state.consumer_research)
    
    # 调用 orchestrator 运行内涵设计阶段
    try:
        state = orchestrator.run_stage(state, {"action": "generate_schemes"})
        
        # 更新内存
        _active_workflows[workflow_id] = state
        
        # 保存状态
        orchestrator.save_state(state)
        
        # 返回新的方案数据
        return {
            "success": True,
            "design_schemes": state.content_core.design_schemes if state.content_core else [],
            "current_stage": state.current_stage,
            "status": build_status(workflow_id, state, orchestrator.config).model_dump(),
            "content_core": state.content_core.model_dump() if state.content_core else None,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成方案失败: {str(e)}")


class UpdateIntentRequest(BaseModel):
    """更新意图分析请求"""
    goal: Optional[str] = None
    success_criteria: Optional[List[str]] = None
    constraints: Optional[Dict[str, List[str]]] = None  # {must_have: [], must_avoid: []}


@router.patch("/{workflow_id}/intent")
async def update_intent(workflow_id: str, request: UpdateIntentRequest):
    """
    更新意图分析数据
    
    保存用户对意图分析结果的编辑
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.intent:
        raise HTTPException(status_code=400, detail="意图分析数据不存在")
    
    # 更新字段
    if request.goal is not None:
        state.intent.goal = request.goal
    if request.success_criteria is not None:
        state.intent.success_criteria = request.success_criteria
    if request.constraints is not None:
        if not state.intent.constraints:
            state.intent.constraints = {}
        if "must_have" in request.constraints:
            state.intent.constraints["must_have"] = request.constraints["must_have"]
        if "must_avoid" in request.constraints:
            state.intent.constraints["must_avoid"] = request.constraints["must_avoid"]
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "goal": state.intent.goal,
        "success_criteria": state.intent.success_criteria,
        "constraints": state.intent.constraints,
    }


class UpdateResearchRequest(BaseModel):
    """更新消费者调研请求"""
    summary: Optional[str] = None
    key_pain_points: Optional[List[str]] = None
    key_desires: Optional[List[str]] = None


@router.patch("/{workflow_id}/research")
async def update_research(workflow_id: str, request: UpdateResearchRequest):
    """
    更新消费者调研数据
    
    保存用户对调研结果的编辑
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.consumer_research:
        raise HTTPException(status_code=400, detail="消费者调研数据不存在")
    
    # 更新字段
    if request.summary is not None:
        state.consumer_research.summary = request.summary
    if request.key_pain_points is not None:
        state.consumer_research.key_pain_points = request.key_pain_points
    if request.key_desires is not None:
        state.consumer_research.key_desires = request.key_desires
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "success": True,
        "summary": state.consumer_research.summary,
        "key_pain_points": state.consumer_research.key_pain_points,
        "key_desires": state.consumer_research.key_desires,
    }


class UpdatePersonasRequest(BaseModel):
    """更新 Personas 选择状态请求"""
    selected_persona_ids: List[str]


@router.patch("/{workflow_id}/personas")
async def update_personas_selection(workflow_id: str, request: UpdatePersonasRequest):
    """
    更新 Personas 的选择状态
    
    保存用户选择哪些 Personas 用于 Simulator 评估
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    if not state.consumer_research:
        raise HTTPException(status_code=400, detail="消费者调研数据不存在")
    
    if not state.consumer_research.personas:
        raise HTTPException(status_code=400, detail="没有可用的 Personas")
    
    # 更新每个 persona 的 selected 状态
    selected_ids = set(request.selected_persona_ids)
    for persona in state.consumer_research.personas:
        persona["selected"] = persona.get("id") in selected_ids
    
    # 更新内存
    _active_workflows[workflow_id] = state
    
    # 保存状态
    orchestrator.save_state(state)
    
    selected_count = len([p for p in state.consumer_research.personas if p.get("selected")])
    
    return {
        "success": True,
        "selected_count": selected_count,
        "personas": state.consumer_research.personas,
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


async def _handle_field_modification(
    state,
    orchestrator,
    workflow_id: str,
    message: str,
    contexts: List[Dict[str, str]],
    field_references: List[Dict[str, str]]
) -> tuple[bool, str, Optional[dict]]:
    """
    处理字段修改请求
    
    用户通过 @章节名/字段名 引用字段并要求修改时，执行以下流程：
    1. 识别目标字段
    2. 根据用户需求生成新内容
    3. 更新字段内容
    4. 返回结果
    
    Returns:
        (updated, response_message, new_data)
    """
    from datetime import datetime
    
    ai_client = orchestrator.ai_client
    
    # 解析字段引用
    target_fields = []
    for ref in field_references:
        ref_type = ref.get('type', '')
        # 格式: "字段:章节名/字段名"
        if ref_type.startswith('字段:'):
            path = ref_type.replace('字段:', '')
            if '/' in path:
                section_name, field_name = path.split('/', 1)
                # 找到对应的字段
                for section in state.content_core.sections:
                    if section.name == section_name:
                        for field in section.fields:
                            if field.name == field_name:
                                target_fields.append({
                                    'section': section,
                                    'field': field,
                                    'original_content': ref.get('content', ''),
                                })
                                break
    
    if not target_fields:
        return False, "未找到要修改的字段。请使用 @章节名/字段名 格式引用具体字段。", None
    
    # 为每个目标字段生成新内容
    modified_fields = []
    for target in target_fields:
        section = target['section']
        field = target['field']
        original_content = target['original_content']
        
        # 构建修改提示词
        system_prompt = f"""你是一个内容修改专家。用户要求修改以下内容：

【当前内容】
{original_content}

【用户要求】
{message}

请根据用户的要求，生成修改后的完整内容。

要求：
1. 保持原有内容的结构和风格
2. 只修改用户明确要求修改的部分
3. 如果用户要求不清晰，合理推断并执行
4. 直接输出修改后的完整内容，不要包含解释或说明
"""
        
        # 添加创作者约束
        if state.creator_profile:
            taboos = state.creator_profile.taboos
            if taboos:
                constraints = []
                if hasattr(taboos, 'forbidden_words') and taboos.forbidden_words:
                    constraints.append(f"禁用词汇: {', '.join(taboos.forbidden_words[:10])}")
                if hasattr(taboos, 'forbidden_topics') and taboos.forbidden_topics:
                    constraints.append(f"禁碰话题: {', '.join(taboos.forbidden_topics[:5])}")
                if constraints:
                    system_prompt += f"\n\n【创作者约束】\n" + "\n".join(constraints)
        
        # 调用 AI 生成新内容
        new_content = ai_client.chat(
            system_prompt=system_prompt,
            user_message="请生成修改后的内容。",
        )
        
        # 更新字段
        field.content = new_content
        field.updated_at = datetime.now()
        field.iteration_count += 1
        
        modified_fields.append({
            'section_name': section.name,
            'field_name': field.name,
            'field_id': field.id,
        })
    
    # 保存状态
    _active_workflows[workflow_id] = state
    orchestrator.save_state(state)
    
    # 构建响应
    field_names = [f"{f['section_name']}/{f['field_name']}" for f in modified_fields]
    response = f"已修改以下字段：{', '.join(field_names)}。请在左侧查看更新后的内容。"
    
    # 返回更新的数据
    new_data = {
        "content_core": state.content_core.model_dump() if state.content_core else None,
    }
    
    return True, response, new_data


def _detect_action_intent(message: str) -> tuple[Optional[str], Optional[str]]:
    """
    检测用户消息中的操作意图
    
    Returns:
        (action_type, target_stage): 操作类型和目标阶段
    """
    import re
    
    message_lower = message.lower()
    
    # 重新生成类操作
    regenerate_patterns = [
        (r'重新生成.*?(?:内涵设计|设计方案|方案)', 'regenerate', 'core_design'),
        (r'重新生成.*?(?:意图|意图分析)', 'regenerate', 'intent'),
        (r'重新生成.*?(?:调研|消费者调研|用户画像)', 'regenerate', 'research'),
        (r'(?:再生成|重做).*?方案', 'regenerate', 'core_design'),
    ]
    
    for pattern, action, stage in regenerate_patterns:
        if re.search(pattern, message):
            return (action, stage)
    
    return (None, None)


@router.post("/{workflow_id}/agent-chat")
async def agent_chat(workflow_id: str, request: AgentChatRequest):
    """
    Agent对话 - 支持@引用的智能对话和操作执行
    
    用户可以通过@引用来指定上下文，AI会理解并处理用户的请求。
    支持操作命令：
    - "重新生成内涵设计" / "重新生成方案" - 重新生成设计方案
    - "@意图分析 修改目标为XXX"
    - "@消费者调研 调整用户画像"
    """
    state, orchestrator = await ensure_workflow_loaded(workflow_id)
    
    message = request.message
    contexts = request.contexts
    
    # 检测是否有操作意图
    action_type, target_stage = _detect_action_intent(message)
    
    updated = False
    action_response = None
    new_data = None
    
    # 执行操作
    if action_type == "regenerate" and target_stage == "core_design":
        # 重新生成内涵设计方案
        try:
            # 检查前置条件
            if not state.intent:
                action_response = "无法重新生成设计方案：请先完成意图分析。"
            elif not state.consumer_research:
                action_response = "无法重新生成设计方案：请先完成消费者调研。"
            else:
                # 如果有现有方案，创建版本备份
                if state.content_core and state.content_core.design_schemes:
                    version_manager.create_version(
                        project_id=workflow_id,
                        trigger_stage="core_design",
                        trigger_action="agent_regenerate",
                        description=f"Agent重新生成前的备份: {message[:50]}",
                        stages_to_backup=["core_design"],
                    )
                
                # 清空当前方案
                if state.content_core:
                    state.content_core.design_schemes = []
                    state.content_core.selected_scheme_index = None
                    state.content_core.fields = []
                    state.content_core.status = "scheme_generation"
                
                # 设置状态
                state.current_stage = "core_design"
                state.project.status = "core_design"
                state.waiting_for_input = False
                
                # 确保上下文正确
                orchestrator.context_manager.set_stage_context("intent", state.intent)
                orchestrator.context_manager.set_stage_context("consumer_research", state.consumer_research)
                
                # 调用 orchestrator 重新生成
                state = orchestrator.run_stage(state, {"action": "generate_schemes"})
                
                # 更新内存
                _active_workflows[workflow_id] = state
                
                # 保存状态
                orchestrator.save_state(state)
                
                updated = True
                new_data = {
                    "content_core": state.content_core.model_dump() if state.content_core else None,
                }
                action_response = f"已重新生成 {len(state.content_core.design_schemes) if state.content_core else 0} 个设计方案，请在左侧查看并选择。"
                
        except Exception as e:
            action_response = f"重新生成失败: {str(e)}"
    
    # 如果没有执行操作，先判断是否是字段修改请求
    if not action_response:
        # 检查是否引用了具体字段（格式：字段:章节名/字段名）
        field_references = [ctx for ctx in contexts if ctx.get('type', '').startswith('字段:')]
        
        # 如果引用了具体字段且消息中包含修改关键词，执行字段修改
        modification_keywords = ['修改', '改写', '重写', '调整', '优化', '换成', '改成', '更新', '改为']
        is_modification_request = any(kw in message for kw in modification_keywords)
        
        if field_references and is_modification_request and state.content_core:
            # 执行字段修改
            try:
                updated, action_response, new_data = await _handle_field_modification(
                    state=state,
                    orchestrator=orchestrator,
                    workflow_id=workflow_id,
                    message=message,
                    contexts=contexts,
                    field_references=field_references
                )
            except Exception as e:
                action_response = f"修改字段失败: {str(e)}"
                updated = False
                new_data = None
        else:
            # 普通对话流程
            # 构建上下文提示
            context_text = ""
            for ctx in contexts:
                context_text += f"\n\n【{ctx.get('type', '上下文')}】\n{ctx.get('content', '')}"
            
            # 构建Agent系统提示
            system_prompt = """你是一个内容生产助手。用户正在进行内容生产项目，可以通过@引用来查看和修改各阶段的内容。

你的职责：
1. 理解用户的意图
2. 基于引用的上下文回答问题或提供建议
3. 如果用户要求修改内容，告诉他们可以使用 @章节名/字段名 来引用并修改具体字段
4. 保持回复简洁有用

提示：
- 使用 @章节名/字段名 来引用具体字段，然后说明修改需求
- 例如："@新章节/角色 把年龄改成30岁"

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
            action_response = ai_client.chat(
                system_prompt=system_prompt,
                user_message=message,
            )
    
    # 记录对话
    if hasattr(state.project, 'add_message'):
        state.project.add_message("user", message, state.current_stage)
        state.project.add_message("assistant", action_response, state.current_stage)
    
    # 保存状态
    orchestrator.save_state(state)
    
    return {
        "response": action_response,
        "updated": updated,
        "current_stage": state.current_stage,
        "data": new_data,
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
