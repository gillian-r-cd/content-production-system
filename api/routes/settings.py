# api/routes/settings.py
# 设置API

from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import yaml

router = APIRouter()

CONFIG_PATH = Path("./config.yaml")
PROMPTS_PATH = Path("./config/prompts")


class ConfigResponse(BaseModel):
    """配置响应"""
    ai: dict
    storage: dict
    orchestrator: dict
    defaults: dict


class PromptTemplate(BaseModel):
    """Prompt模板"""
    name: str
    content: str


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """获取系统配置"""
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="配置文件不存在")
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return ConfigResponse(
        ai=config.get("ai", {}),
        storage=config.get("storage", {}),
        orchestrator=config.get("orchestrator", {}),
        defaults=config.get("defaults", {}),
    )


@router.get("/prompts", response_model=List[PromptTemplate])
async def list_prompts():
    """获取所有Prompt模板"""
    if not PROMPTS_PATH.exists():
        return []
    
    templates = []
    for path in PROMPTS_PATH.glob("*.md.j2"):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        templates.append(PromptTemplate(
            name=path.stem.replace(".md", ""),
            content=content,
        ))
    
    return templates


@router.get("/prompts/{name}", response_model=PromptTemplate)
async def get_prompt(name: str):
    """获取单个Prompt模板"""
    path = PROMPTS_PATH / f"{name}.md.j2"
    if not path.exists():
        raise HTTPException(status_code=404, detail="模板不存在")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return PromptTemplate(name=name, content=content)


@router.put("/prompts/{name}")
async def update_prompt(name: str, data: PromptTemplate):
    """更新Prompt模板"""
    PROMPTS_PATH.mkdir(parents=True, exist_ok=True)
    path = PROMPTS_PATH / f"{name}.md.j2"
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data.content)
    
    return {"message": "更新成功"}



