# web/backend/main.py
# FastAPI后端 - 封装核心Python逻辑为REST API

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# 导入核心模块
from core.models import CreatorProfile, Project, FieldSchema
from core.ai_client import AIClient
from core.prompt_engine import PromptEngine
from core.context_manager import ContextManager
from core.orchestrator import Orchestrator, ProjectState

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import os
if os.getenv("OPENAI_BASE_URL") == "":
    os.environ.pop("OPENAI_BASE_URL", None)

app = FastAPI(
    title="内容生产系统 API",
    description="以终为始的AI内容生产系统后端API",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储路径
STORAGE_PATH = project_root / "storage"

# ===== 数据模型 =====

class ProfileCreate(BaseModel):
    name: str
    taboos: Optional[Dict[str, List[str]]] = None
    example_texts: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, str]] = None

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    creator_profile_id: str

class IntentInput(BaseModel):
    project_id: str
    raw_input: str
    clarifications: Optional[List[Dict[str, str]]] = None

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    project_id: str
    messages: List[ChatMessage]
    stage: str  # "intent" | "research" | "core" | "extension"

# ===== API路由 =====

@app.get("/")
async def root():
    return {"message": "内容生产系统 API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# ----- Profile 相关 -----

@app.get("/api/profiles")
async def list_profiles():
    """列出所有创作者特质"""
    profiles_dir = STORAGE_PATH / "creator_profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    
    profiles = []
    for profile_path in profiles_dir.glob("*.yaml"):
        try:
            profile = CreatorProfile.load(profile_path)
            profiles.append({
                "id": profile.id,
                "name": profile.name,
                "taboos_count": len(profile.taboos.forbidden_words) if profile.taboos else 0,
                "examples_count": len(profile.example_texts),
            })
        except Exception as e:
            print(f"加载profile失败: {profile_path}, {e}")
    
    return {"profiles": profiles}

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """获取创作者特质详情"""
    profile_path = STORAGE_PATH / "creator_profiles" / f"{profile_id}.yaml"
    
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = CreatorProfile.load(profile_path)
    return profile.to_dict()

@app.post("/api/profiles")
async def create_profile(data: ProfileCreate):
    """创建新的创作者特质"""
    from core.models import Taboos
    
    profiles_dir = STORAGE_PATH / "creator_profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    
    profile_id = f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    profile = CreatorProfile(
        id=profile_id,
        name=data.name,
        taboos=Taboos(
            id="taboos",
            forbidden_words=data.taboos.get("forbidden_words", []) if data.taboos else [],
            forbidden_topics=data.taboos.get("forbidden_topics", []) if data.taboos else [],
        ),
        example_texts=data.example_texts or [],
        custom_fields=data.custom_fields or {},
    )
    
    profile.save(profiles_dir / f"{profile_id}.yaml")
    
    return {"id": profile_id, "message": "创建成功"}

# ----- Project 相关 -----

@app.get("/api/projects")
async def list_projects():
    """列出所有项目"""
    projects_dir = STORAGE_PATH / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    
    projects = []
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            project_file = project_dir / "project.yaml"
            if project_file.exists():
                try:
                    project = Project.load(project_file)
                    projects.append({
                        "id": project.id,
                        "name": project.name,
                        "status": project.status,
                        "current_stage": project.current_stage,
                        "creator_profile_id": project.creator_profile_id,
                    })
                except Exception as e:
                    print(f"加载project失败: {project_dir}, {e}")
    
    return {"projects": projects}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    project_dir = STORAGE_PATH / "projects" / project_id
    project_file = project_dir / "project.yaml"
    
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = Project.load(project_file)
    
    # 加载项目状态
    state_file = project_dir / "state.yaml"
    state_data = None
    if state_file.exists():
        import yaml
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f)
    
    return {
        "project": project.to_dict(),
        "state": state_data,
    }

@app.post("/api/projects")
async def create_project(data: ProjectCreate):
    """创建新项目"""
    # 验证profile存在
    profile_path = STORAGE_PATH / "creator_profiles" / f"{data.creator_profile_id}.yaml"
    if not profile_path.exists():
        raise HTTPException(status_code=400, detail="Profile not found")
    
    projects_dir = STORAGE_PATH / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    
    project_id = f"proj_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    project_dir = projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    project = Project(
        id=project_id,
        name=data.name,
        description=data.description,
        creator_profile_id=data.creator_profile_id,
    )
    
    project.save(project_dir / "project.yaml")
    
    return {"id": project_id, "message": "创建成功"}

# ----- 内容生产流程 -----

# 全局存储运行中的Orchestrator实例
active_orchestrators: Dict[str, tuple] = {}  # project_id -> (orchestrator, state)

@app.post("/api/projects/{project_id}/start")
async def start_project(project_id: str, data: IntentInput):
    """启动项目内容生产流程"""
    project_dir = STORAGE_PATH / "projects" / project_id
    project_file = project_dir / "project.yaml"
    
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = Project.load(project_file)
    
    # 加载profile
    profile_path = STORAGE_PATH / "creator_profiles" / f"{project.creator_profile_id}.yaml"
    if not profile_path.exists():
        raise HTTPException(status_code=400, detail="Profile not found")
    
    creator_profile = CreatorProfile.load(profile_path)
    
    # 创建Orchestrator
    ai_client = AIClient()
    prompt_engine = PromptEngine(project_root / "config" / "prompts")
    orchestrator = Orchestrator(ai_client=ai_client, prompt_engine=prompt_engine)
    
    # 创建状态
    state = orchestrator.create_project_state(
        project=project,
        creator_profile=creator_profile,
    )
    
    # 运行意图分析
    state = orchestrator.run_stage(state, {"raw_input": data.raw_input})
    
    # 保存状态
    active_orchestrators[project_id] = (orchestrator, state)
    
    return {
        "project_id": project_id,
        "current_stage": state.current_stage,
        "waiting_for_input": state.waiting_for_input,
        "input_prompt": state.input_prompt,
        "intent": state.intent.to_dict() if state.intent else None,
    }

@app.post("/api/projects/{project_id}/continue")
async def continue_project(project_id: str, data: Dict[str, Any]):
    """继续项目流程（回答追问等）"""
    if project_id not in active_orchestrators:
        raise HTTPException(status_code=400, detail="Project not active. Call /start first.")
    
    orchestrator, state = active_orchestrators[project_id]
    
    # 继续运行
    state = orchestrator.run_stage(state, {"answer": data.get("answer", "")})
    
    # 更新缓存
    active_orchestrators[project_id] = (orchestrator, state)
    
    return {
        "project_id": project_id,
        "current_stage": state.current_stage,
        "waiting_for_input": state.waiting_for_input,
        "input_prompt": state.input_prompt,
        "intent": state.intent.to_dict() if state.intent else None,
        "consumer_research": state.consumer_research.to_dict() if state.consumer_research else None,
        "ai_call_count": state.ai_call_count,
    }

# ----- Field Schema 相关 -----

@app.get("/api/field-schemas")
async def list_field_schemas():
    """列出所有字段模板"""
    schemas_dir = project_root / "config" / "field_schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    
    schemas = []
    for schema_path in schemas_dir.glob("*.yaml"):
        try:
            schema = FieldSchema.load(schema_path)
            schemas.append({
                "id": schema.id,
                "name": schema.name,
                "description": schema.description,
                "fields_count": len(schema.fields),
            })
        except Exception as e:
            print(f"加载schema失败: {schema_path}, {e}")
    
    return {"schemas": schemas}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

