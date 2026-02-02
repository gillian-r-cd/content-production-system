# api/routes/channels.py
# 渠道管理API
# 功能：Channel配置的CRUD操作

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

STORAGE_PATH = Path("./storage")


class FormatConstraints(BaseModel):
    """格式约束"""
    title_max_length: Optional[int] = None
    body_min_length: Optional[int] = None
    body_max_length: Optional[int] = None
    special_requirements: str = ""


class ChannelCreate(BaseModel):
    """创建渠道请求"""
    name: str
    description: str = ""
    format_constraints: Optional[FormatConstraints] = None
    prompt_template: str = ""


class ChannelResponse(BaseModel):
    """渠道响应"""
    id: str
    name: str
    description: str
    format_constraints: FormatConstraints
    prompt_template: str
    created_at: str
    updated_at: str


def ensure_storage():
    """确保存储目录存在"""
    (STORAGE_PATH / "channels").mkdir(parents=True, exist_ok=True)


def _load_channel(path: Path) -> dict:
    """加载渠道配置"""
    import yaml
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _save_channel(path: Path, data: dict):
    """保存渠道配置"""
    import yaml
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


@router.get("", response_model=List[ChannelResponse])
async def list_channels():
    """获取所有渠道配置"""
    ensure_storage()
    channels_dir = STORAGE_PATH / "channels"
    channels = []
    
    for path in channels_dir.glob("*.yaml"):
        try:
            data = _load_channel(path)
            fc = data.get("format_constraints", {}) or {}
            channels.append(ChannelResponse(
                id=data.get("id", path.stem),
                name=data.get("name", ""),
                description=data.get("description", ""),
                format_constraints=FormatConstraints(
                    title_max_length=fc.get("title_max_length"),
                    body_min_length=fc.get("body_min_length"),
                    body_max_length=fc.get("body_max_length"),
                    special_requirements=fc.get("special_requirements", ""),
                ),
                prompt_template=data.get("prompt_template", ""),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
            ))
        except Exception as e:
            print(f"加载Channel失败: {path}, {e}")
    
    return channels


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str):
    """获取单个渠道配置"""
    ensure_storage()
    path = STORAGE_PATH / "channels" / f"{channel_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="渠道不存在")
    
    data = _load_channel(path)
    fc = data.get("format_constraints", {}) or {}
    return ChannelResponse(
        id=data.get("id", channel_id),
        name=data.get("name", ""),
        description=data.get("description", ""),
        format_constraints=FormatConstraints(
            title_max_length=fc.get("title_max_length"),
            body_min_length=fc.get("body_min_length"),
            body_max_length=fc.get("body_max_length"),
            special_requirements=fc.get("special_requirements", ""),
        ),
        prompt_template=data.get("prompt_template", ""),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


@router.post("", response_model=ChannelResponse, status_code=201)
async def create_channel(data: ChannelCreate):
    """创建渠道配置"""
    ensure_storage()
    
    channel_id = f"channel_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now().isoformat()
    
    fc = data.format_constraints or FormatConstraints()
    channel_data = {
        "id": channel_id,
        "name": data.name,
        "description": data.description,
        "format_constraints": fc.model_dump(),
        "prompt_template": data.prompt_template,
        "created_at": now,
        "updated_at": now,
    }
    
    path = STORAGE_PATH / "channels" / f"{channel_id}.yaml"
    _save_channel(path, channel_data)
    
    return ChannelResponse(
        id=channel_id,
        name=data.name,
        description=data.description,
        format_constraints=fc,
        prompt_template=data.prompt_template,
        created_at=now,
        updated_at=now,
    )


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(channel_id: str, data: ChannelCreate):
    """更新渠道配置"""
    ensure_storage()
    path = STORAGE_PATH / "channels" / f"{channel_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="渠道不存在")
    
    existing = _load_channel(path)
    now = datetime.now().isoformat()
    
    fc = data.format_constraints or FormatConstraints()
    channel_data = {
        "id": channel_id,
        "name": data.name,
        "description": data.description,
        "format_constraints": fc.model_dump(),
        "prompt_template": data.prompt_template,
        "created_at": existing.get("created_at", now),
        "updated_at": now,
    }
    
    _save_channel(path, channel_data)
    
    return ChannelResponse(
        id=channel_id,
        name=data.name,
        description=data.description,
        format_constraints=fc,
        prompt_template=data.prompt_template,
        created_at=existing.get("created_at", now),
        updated_at=now,
    )


@router.delete("/{channel_id}")
async def delete_channel(channel_id: str):
    """删除渠道配置"""
    ensure_storage()
    path = STORAGE_PATH / "channels" / f"{channel_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="渠道不存在")
    
    path.unlink()
    return {"message": "删除成功"}



