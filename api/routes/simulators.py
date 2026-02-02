# api/routes/simulators.py
# 评估器配置API
# 功能：SimulatorConfig的CRUD操作

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

STORAGE_PATH = Path("./storage")


class SimulatorCreate(BaseModel):
    """创建评估器请求"""
    name: str
    description: str = ""
    prompt_template: str = ""
    auto_iterate: bool = True
    trigger_score: float = 6.0
    stop_score: float = 8.0
    max_iterations: int = 3


class SimulatorResponse(BaseModel):
    """评估器响应"""
    id: str
    name: str
    description: str
    prompt_template: str
    auto_iterate: bool
    trigger_score: float
    stop_score: float
    max_iterations: int
    created_at: str
    updated_at: str


def ensure_storage():
    """确保存储目录存在"""
    (STORAGE_PATH / "simulators").mkdir(parents=True, exist_ok=True)


def _load_simulator(path: Path) -> dict:
    """加载评估器配置"""
    import yaml
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _save_simulator(path: Path, data: dict):
    """保存评估器配置"""
    import yaml
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


@router.get("", response_model=List[SimulatorResponse])
async def list_simulators():
    """获取所有评估器配置"""
    ensure_storage()
    simulators_dir = STORAGE_PATH / "simulators"
    simulators = []
    
    for path in simulators_dir.glob("*.yaml"):
        try:
            data = _load_simulator(path)
            simulators.append(SimulatorResponse(
                id=data.get("id", path.stem),
                name=data.get("name", ""),
                description=data.get("description", ""),
                prompt_template=data.get("prompt_template", ""),
                auto_iterate=data.get("auto_iterate", True),
                trigger_score=data.get("trigger_score", 6.0),
                stop_score=data.get("stop_score", 8.0),
                max_iterations=data.get("max_iterations", 3),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
            ))
        except Exception as e:
            print(f"加载Simulator失败: {path}, {e}")
    
    return simulators


@router.get("/{simulator_id}", response_model=SimulatorResponse)
async def get_simulator(simulator_id: str):
    """获取单个评估器配置"""
    ensure_storage()
    path = STORAGE_PATH / "simulators" / f"{simulator_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="评估器不存在")
    
    data = _load_simulator(path)
    return SimulatorResponse(
        id=data.get("id", simulator_id),
        name=data.get("name", ""),
        description=data.get("description", ""),
        prompt_template=data.get("prompt_template", ""),
        auto_iterate=data.get("auto_iterate", True),
        trigger_score=data.get("trigger_score", 6.0),
        stop_score=data.get("stop_score", 8.0),
        max_iterations=data.get("max_iterations", 3),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


@router.post("", response_model=SimulatorResponse, status_code=201)
async def create_simulator(data: SimulatorCreate):
    """创建评估器配置"""
    ensure_storage()
    
    simulator_id = f"sim_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now().isoformat()
    
    simulator_data = {
        "id": simulator_id,
        "name": data.name,
        "description": data.description,
        "prompt_template": data.prompt_template,
        "auto_iterate": data.auto_iterate,
        "trigger_score": data.trigger_score,
        "stop_score": data.stop_score,
        "max_iterations": data.max_iterations,
        "created_at": now,
        "updated_at": now,
    }
    
    path = STORAGE_PATH / "simulators" / f"{simulator_id}.yaml"
    _save_simulator(path, simulator_data)
    
    return SimulatorResponse(**simulator_data)


@router.put("/{simulator_id}", response_model=SimulatorResponse)
async def update_simulator(simulator_id: str, data: SimulatorCreate):
    """更新评估器配置"""
    ensure_storage()
    path = STORAGE_PATH / "simulators" / f"{simulator_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="评估器不存在")
    
    existing = _load_simulator(path)
    now = datetime.now().isoformat()
    
    simulator_data = {
        "id": simulator_id,
        "name": data.name,
        "description": data.description,
        "prompt_template": data.prompt_template,
        "auto_iterate": data.auto_iterate,
        "trigger_score": data.trigger_score,
        "stop_score": data.stop_score,
        "max_iterations": data.max_iterations,
        "created_at": existing.get("created_at", now),
        "updated_at": now,
    }
    
    _save_simulator(path, simulator_data)
    
    return SimulatorResponse(**simulator_data)


@router.delete("/{simulator_id}")
async def delete_simulator(simulator_id: str):
    """删除评估器配置"""
    ensure_storage()
    path = STORAGE_PATH / "simulators" / f"{simulator_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="评估器不存在")
    
    path.unlink()
    return {"message": "删除成功"}



