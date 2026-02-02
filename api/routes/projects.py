# api/routes/projects.py
# 项目API

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.models import Project

router = APIRouter()

STORAGE_PATH = Path("./storage")


class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str
    description: Optional[str] = ""
    creator_profile_id: str


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: str
    creator_profile_id: str
    status: str
    created_at: str
    updated_at: str


class ProjectListItem(BaseModel):
    """项目列表项"""
    id: str
    name: str
    status: str
    created_at: str


def ensure_storage():
    """确保存储目录存在"""
    (STORAGE_PATH / "projects").mkdir(parents=True, exist_ok=True)


@router.get("", response_model=List[ProjectListItem])
async def list_projects():
    """获取所有项目"""
    ensure_storage()
    projects_dir = STORAGE_PATH / "projects"
    projects = []
    
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            project_file = project_dir / "project.yaml"
            if project_file.exists():
                try:
                    project = Project.load(project_file)
                    projects.append(ProjectListItem(
                        id=project.id,
                        name=project.name,
                        status=project.status,
                        created_at=str(project.created_at) if project.created_at else "",
                    ))
                except Exception as e:
                    print(f"加载项目失败: {project_dir}, {e}")
    
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """获取单个项目详情"""
    ensure_storage()
    project_file = STORAGE_PATH / "projects" / project_id / "project.yaml"
    
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = Project.load(project_file)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description or "",
        creator_profile_id=project.creator_profile_id,
        status=project.status,
        created_at=str(project.created_at) if project.created_at else "",
        updated_at=str(project.updated_at) if project.updated_at else "",
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate):
    """创建项目"""
    ensure_storage()
    
    # 验证Profile存在
    profile_path = STORAGE_PATH / "creator_profiles" / f"{data.creator_profile_id}.yaml"
    if not profile_path.exists():
        raise HTTPException(status_code=400, detail="创作者特质不存在")
    
    project_id = f"proj_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now()
    
    project = Project(
        id=project_id,
        name=data.name,
        description=data.description,
        creator_profile_id=data.creator_profile_id,
        status="draft",  # 使用有效的状态值
        created_at=now,
        updated_at=now,
    )
    
    project_dir = STORAGE_PATH / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    project.save(project_dir / "project.yaml")
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description or "",
        creator_profile_id=project.creator_profile_id,
        status=project.status,
        created_at=str(project.created_at),
        updated_at=str(project.updated_at),
    )


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    description: Optional[str] = None


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, data: ProjectUpdate):
    """更新项目"""
    ensure_storage()
    project_file = STORAGE_PATH / "projects" / project_id / "project.yaml"
    
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = Project.load(project_file)
    
    # 更新字段
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    
    project.updated_at = datetime.now()
    project.save(project_file)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description or "",
        creator_profile_id=project.creator_profile_id,
        status=project.status,
        created_at=str(project.created_at) if project.created_at else "",
        updated_at=str(project.updated_at) if project.updated_at else "",
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    ensure_storage()
    project_dir = STORAGE_PATH / "projects" / project_id
    
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    import shutil
    shutil.rmtree(project_dir)
    return {"message": "删除成功"}

