# api/routes/schemas.py
# 字段模板API
# 功能：FieldSchema的CRUD操作

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.models import FieldSchema, FieldDefinition

router = APIRouter()

STORAGE_PATH = Path("./storage")


class FieldCreate(BaseModel):
    """字段定义"""
    name: str
    description: str = ""
    field_type: str = "text"  # text, list, freeform (前端用field_type，后端用type)
    required: bool = True
    ai_hint: str = ""
    order: int = 0  # 生成顺序
    depends_on: Optional[List[str]] = None  # 依赖的字段名列表
    
    def to_field_definition(self) -> FieldDefinition:
        """转换为FieldDefinition（字段名映射）"""
        return FieldDefinition(
            name=self.name,
            description=self.description,
            type=self.field_type,  # field_type -> type
            required=self.required,
            ai_hint=self.ai_hint,
            order=self.order,
            depends_on=self.depends_on or [],
        )


class SchemaCreate(BaseModel):
    """创建Schema请求"""
    name: str
    description: str = ""
    fields: List[FieldCreate] = []


class FieldResponse(BaseModel):
    """字段响应"""
    name: str
    description: str
    field_type: str  # 前端使用field_type
    required: bool
    ai_hint: str
    order: int = 0
    depends_on: List[str] = []
    
    @classmethod
    def from_field_definition(cls, f: FieldDefinition) -> "FieldResponse":
        """从FieldDefinition创建（字段名映射）"""
        return cls(
            name=f.name,
            description=f.description or "",
            field_type=f.type or "text",  # type -> field_type
            required=f.required if f.required is not None else True,
            ai_hint=f.ai_hint or "",
            order=f.order if hasattr(f, 'order') else 0,
            depends_on=f.depends_on if hasattr(f, 'depends_on') else [],
        )


class SchemaResponse(BaseModel):
    """Schema响应"""
    id: str
    name: str
    description: str
    fields: List[FieldResponse]
    created_at: str
    updated_at: str


def ensure_storage():
    """确保存储目录存在"""
    (STORAGE_PATH / "field_schemas").mkdir(parents=True, exist_ok=True)


@router.get("", response_model=List[SchemaResponse])
async def list_schemas():
    """获取所有字段模板"""
    ensure_storage()
    schemas_dir = STORAGE_PATH / "field_schemas"
    schemas = []
    
    for path in schemas_dir.glob("*.yaml"):
        try:
            schema = FieldSchema.load(path)
            schemas.append(SchemaResponse(
                id=schema.id,
                name=schema.name,
                description=schema.description or "",
                fields=[FieldResponse.from_field_definition(f) for f in (schema.fields or [])],
                created_at=schema.created_at.isoformat() if schema.created_at else "",
                updated_at=schema.updated_at.isoformat() if schema.updated_at else "",
            ))
        except Exception as e:
            print(f"加载Schema失败: {path}, {e}")
    
    return schemas


@router.get("/{schema_id}", response_model=SchemaResponse)
async def get_schema(schema_id: str):
    """获取单个字段模板"""
    ensure_storage()
    path = STORAGE_PATH / "field_schemas" / f"{schema_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    
    schema = FieldSchema.load(path)
    return SchemaResponse(
        id=schema.id,
        name=schema.name,
        description=schema.description or "",
        fields=[FieldResponse.from_field_definition(f) for f in (schema.fields or [])],
        created_at=schema.created_at.isoformat() if schema.created_at else "",
        updated_at=schema.updated_at.isoformat() if schema.updated_at else "",
    )


@router.post("", response_model=SchemaResponse, status_code=201)
async def create_schema(data: SchemaCreate):
    """创建字段模板"""
    ensure_storage()
    
    schema_id = f"schema_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 使用辅助方法转换字段
    fields = [f.to_field_definition() for f in data.fields]
    
    schema = FieldSchema(
        id=schema_id,
        name=data.name,
        description=data.description,
        fields=fields,
    )
    
    path = STORAGE_PATH / "field_schemas" / f"{schema_id}.yaml"
    schema.save(path)
    
    return SchemaResponse(
        id=schema.id,
        name=schema.name,
        description=schema.description or "",
        fields=[FieldResponse.from_field_definition(f) for f in fields],
        created_at=schema.created_at.isoformat() if schema.created_at else "",
        updated_at=schema.updated_at.isoformat() if schema.updated_at else "",
    )


@router.put("/{schema_id}", response_model=SchemaResponse)
async def update_schema(schema_id: str, data: SchemaCreate):
    """更新字段模板"""
    ensure_storage()
    path = STORAGE_PATH / "field_schemas" / f"{schema_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    
    schema = FieldSchema.load(path)
    
    schema.name = data.name
    schema.description = data.description
    schema.fields = [f.to_field_definition() for f in data.fields]
    schema.updated_at = datetime.now()
    
    schema.save(path)
    
    return SchemaResponse(
        id=schema.id,
        name=schema.name,
        description=schema.description or "",
        fields=[FieldResponse.from_field_definition(f) for f in schema.fields],
        created_at=schema.created_at.isoformat() if schema.created_at else "",
        updated_at=schema.updated_at.isoformat() if schema.updated_at else "",
    )


@router.delete("/{schema_id}")
async def delete_schema(schema_id: str):
    """删除字段模板"""
    ensure_storage()
    path = STORAGE_PATH / "field_schemas" / f"{schema_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    
    path.unlink()
    return {"message": "删除成功"}


@router.post("/{schema_id}/copy", response_model=SchemaResponse, status_code=201)
async def copy_schema(schema_id: str):
    """复制字段模板"""
    ensure_storage()
    path = STORAGE_PATH / "field_schemas" / f"{schema_id}.yaml"
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    
    original = FieldSchema.load(path)
    
    new_id = f"schema_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_schema = FieldSchema(
        id=new_id,
        name=f"{original.name} (副本)",
        description=original.description,
        fields=original.fields,
    )
    
    new_path = STORAGE_PATH / "field_schemas" / f"{new_id}.yaml"
    new_schema.save(new_path)
    
    return SchemaResponse(
        id=new_schema.id,
        name=new_schema.name,
        description=new_schema.description or "",
        fields=[FieldResponse.from_field_definition(f) for f in (new_schema.fields or [])],
        created_at=new_schema.created_at.isoformat() if new_schema.created_at else "",
        updated_at=new_schema.updated_at.isoformat() if new_schema.updated_at else "",
    )



