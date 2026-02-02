# core/models/base.py
# 功能：所有数据模型的基类，提供YAML序列化/反序列化能力
# 主要类：BaseModel
# 主要方法：to_yaml(), from_yaml(), save(), load()

from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar
import yaml
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict


T = TypeVar('T', bound='BaseModel')


class BaseModel(PydanticBaseModel, ABC):
    """
    所有数据模型的基类
    
    提供：
    - Pydantic数据验证
    - YAML序列化/反序列化
    - 文件存储/加载
    
    所有子类需要定义自己的字段，使用Pydantic Field。
    """
    
    # Pydantic V2 配置
    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # 允许任意类型
        populate_by_name=True,         # 序列化时使用字段别名
        validate_assignment=True,       # 验证赋值
    )
    
    # 通用元信息字段
    id: str = Field(..., description="唯一标识符")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            dict: 模型数据的字典表示
        """
        return self.model_dump(mode='json')
    
    def to_yaml(self) -> str:
        """
        转换为YAML字符串
        
        Returns:
            str: YAML格式的字符串
        """
        data = self.to_dict()
        return yaml.dump(
            data, 
            allow_unicode=True, 
            default_flow_style=False,
            sort_keys=False
        )
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            模型实例
        """
        return cls.model_validate(data)
    
    @classmethod
    def from_yaml(cls: Type[T], yaml_str: str) -> T:
        """
        从YAML字符串创建实例
        
        Args:
            yaml_str: YAML格式的字符串
            
        Returns:
            模型实例
        """
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    def save(self, path: str | Path) -> None:
        """
        保存到YAML文件
        
        Args:
            path: 文件路径
        """
        path = Path(path)
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 更新更新时间
        self.updated_at = datetime.now()
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_yaml())
    
    @classmethod
    def load(cls: Type[T], path: str | Path) -> T:
        """
        从YAML文件加载
        
        Args:
            path: 文件路径
            
        Returns:
            模型实例
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(path)
        with open(path, 'r', encoding='utf-8') as f:
            return cls.from_yaml(f.read())
    
    def update(self, **kwargs) -> None:
        """
        更新字段值
        
        Args:
            **kwargs: 要更新的字段和值
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def __str__(self) -> str:
        """友好的字符串表示"""
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self) -> str:
        """详细的字符串表示"""
        return self.to_yaml()

