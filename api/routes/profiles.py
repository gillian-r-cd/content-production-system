# api/routes/profiles.py
# 创作者特质API

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.models import CreatorProfile, Taboos

router = APIRouter()

STORAGE_PATH = Path("./storage")


class ProfileCreate(BaseModel):
    """创建Profile请求"""
    name: str
    taboos: Optional[dict] = None
    example_texts: Optional[List[str]] = None
    custom_fields: Optional[dict] = None


class ProfileResponse(BaseModel):
    """Profile响应"""
    id: str
    name: str
    taboos: dict
    example_texts: List[str]
    custom_fields: dict


def ensure_storage():
    """确保存储目录存在"""
    (STORAGE_PATH / "creator_profiles").mkdir(parents=True, exist_ok=True)


@router.get("", response_model=List[ProfileResponse])
async def list_profiles():
    """获取所有创作者特质"""
    ensure_storage()
    profiles_dir = STORAGE_PATH / "creator_profiles"
    profiles = []
    
    for path in profiles_dir.glob("*.yaml"):
        try:
            profile = CreatorProfile.load(path)
            profiles.append(ProfileResponse(
                id=profile.id,
                name=profile.name,
                taboos=profile.taboos.model_dump() if profile.taboos else {},
                example_texts=profile.example_texts or [],
                custom_fields=profile.custom_fields or {},
            ))
        except Exception as e:
            print(f"加载Profile失败: {path}, {e}")
    
    return profiles


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str):
    """获取单个创作者特质"""
    ensure_storage()
    path = STORAGE_PATH / "creator_profiles" / f"{profile_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Profile不存在")
    
    profile = CreatorProfile.load(path)
    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        taboos=profile.taboos.model_dump() if profile.taboos else {},
        example_texts=profile.example_texts or [],
        custom_fields=profile.custom_fields or {},
    )


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(data: ProfileCreate):
    """创建创作者特质"""
    ensure_storage()
    
    profile_id = f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    taboos = Taboos(
        id="taboos",
        forbidden_words=data.taboos.get("forbidden_words", []) if data.taboos else [],
        forbidden_topics=data.taboos.get("forbidden_topics", []) if data.taboos else [],
    )
    
    profile = CreatorProfile(
        id=profile_id,
        name=data.name,
        taboos=taboos,
        example_texts=data.example_texts or [],
        custom_fields=data.custom_fields or {},
    )
    
    path = STORAGE_PATH / "creator_profiles" / f"{profile_id}.yaml"
    profile.save(path)
    
    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        taboos=profile.taboos.model_dump() if profile.taboos else {},
        example_texts=profile.example_texts or [],
        custom_fields=profile.custom_fields or {},
    )


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: str, data: ProfileCreate):
    """更新创作者特质"""
    ensure_storage()
    path = STORAGE_PATH / "creator_profiles" / f"{profile_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Profile不存在")
    
    profile = CreatorProfile.load(path)
    
    profile.name = data.name
    if data.taboos:
        profile.taboos = Taboos(
            id="taboos",
            forbidden_words=data.taboos.get("forbidden_words", []),
            forbidden_topics=data.taboos.get("forbidden_topics", []),
        )
    if data.example_texts is not None:
        profile.example_texts = data.example_texts
    if data.custom_fields is not None:
        profile.custom_fields = data.custom_fields
    
    profile.save(path)
    
    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        taboos=profile.taboos.model_dump() if profile.taboos else {},
        example_texts=profile.example_texts or [],
        custom_fields=profile.custom_fields or {},
    )


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    """删除创作者特质"""
    ensure_storage()
    path = STORAGE_PATH / "creator_profiles" / f"{profile_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Profile不存在")
    
    path.unlink()
    return {"message": "删除成功"}

