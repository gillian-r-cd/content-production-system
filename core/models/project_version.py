# core/models/project_version.py
# 项目版本备份模型
# 功能：在上游修改时备份下游数据

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
from pathlib import Path
import yaml
import shutil

from .base import BaseModel


class ProjectVersion(BaseModel):
    """
    项目版本备份
    
    当用户修改上游阶段（如意图分析）时，
    如果已有下游数据（如消费者调研、内涵设计），
    系统会自动创建版本备份。
    """
    
    id: str = Field(description="版本ID，格式: v_YYYYMMDD_HHMMSS")
    project_id: str = Field(description="所属项目ID")
    
    # 版本信息
    version_number: int = Field(default=1, description="版本号")
    description: str = Field(default="", description="用户添加的版本描述")
    trigger_stage: str = Field(description="触发备份的阶段，如 intent, research")
    trigger_action: str = Field(default="edit", description="触发动作：edit, regenerate")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 备份的阶段数据（记录哪些阶段被备份）
    backed_up_stages: List[str] = Field(
        default_factory=list, 
        description="被备份的阶段列表"
    )
    
    # 元信息
    parent_version: Optional[str] = Field(default=None, description="父版本ID（如果有）")
    is_active: bool = Field(default=False, description="是否是当前活跃版本")
    
    def get_backup_path(self, storage_base: str = "./storage") -> Path:
        """获取备份存储路径"""
        return Path(storage_base) / "projects" / self.project_id / "versions" / self.id
    
    def save_backup(self, storage_base: str = "./storage") -> None:
        """保存版本元数据"""
        backup_path = self.get_backup_path(storage_base)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 保存版本元数据
        with open(backup_path / "version.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, sort_keys=False)
    
    @classmethod
    def load(cls, version_path: Path) -> "ProjectVersion":
        """从文件加载版本"""
        version_file = version_path / "version.yaml"
        if not version_file.exists():
            raise FileNotFoundError(f"版本文件不存在: {version_file}")
        
        with open(version_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)


class VersionManager:
    """
    版本管理器
    
    负责：
    1. 检测是否需要创建版本
    2. 创建版本备份
    3. 恢复版本
    4. 列出版本历史
    """
    
    def __init__(self, storage_base: str = "./storage"):
        self.storage_base = Path(storage_base)
    
    def get_project_versions_path(self, project_id: str) -> Path:
        """获取项目版本目录"""
        return self.storage_base / "projects" / project_id / "versions"
    
    def list_versions(self, project_id: str) -> List[ProjectVersion]:
        """列出项目的所有版本"""
        versions_path = self.get_project_versions_path(project_id)
        if not versions_path.exists():
            return []
        
        versions = []
        for version_dir in sorted(versions_path.iterdir(), reverse=True):
            if version_dir.is_dir():
                try:
                    version = ProjectVersion.load(version_dir)
                    versions.append(version)
                except Exception as e:
                    print(f"加载版本失败: {version_dir}, error: {e}")
        
        return versions
    
    def get_next_version_number(self, project_id: str) -> int:
        """获取下一个版本号"""
        versions = self.list_versions(project_id)
        if not versions:
            return 1
        return max(v.version_number for v in versions) + 1
    
    def should_create_version(
        self, 
        project_id: str, 
        modified_stage: str,
        downstream_stages: Dict[str, bool]
    ) -> bool:
        """
        检测是否需要创建版本
        
        Args:
            project_id: 项目ID
            modified_stage: 被修改的阶段
            downstream_stages: 下游阶段是否有数据 {stage_name: has_data}
        
        Returns:
            bool: 是否需要创建版本
        """
        # 定义阶段顺序
        stage_order = ["intent", "research", "core_design", "core_production", "extension"]
        
        modified_index = stage_order.index(modified_stage) if modified_stage in stage_order else -1
        if modified_index == -1:
            return False
        
        # 检查是否有下游数据
        for stage in stage_order[modified_index + 1:]:
            if downstream_stages.get(stage, False):
                return True
        
        return False
    
    def create_version(
        self,
        project_id: str,
        trigger_stage: str,
        trigger_action: str = "edit",
        description: str = "",
        stages_to_backup: List[str] = None,
    ) -> ProjectVersion:
        """
        创建版本备份
        
        Args:
            project_id: 项目ID
            trigger_stage: 触发备份的阶段
            trigger_action: 触发动作
            description: 版本描述
            stages_to_backup: 需要备份的阶段列表
        
        Returns:
            ProjectVersion: 创建的版本对象
        """
        version_id = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        version_number = self.get_next_version_number(project_id)
        
        version = ProjectVersion(
            id=version_id,
            project_id=project_id,
            version_number=version_number,
            description=description,
            trigger_stage=trigger_stage,
            trigger_action=trigger_action,
            backed_up_stages=stages_to_backup or [],
        )
        
        # 创建备份目录
        backup_path = version.get_backup_path(str(self.storage_base))
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 复制需要备份的文件
        project_path = self.storage_base / "projects" / project_id
        
        stage_files = {
            "intent": "intent.yaml",
            "research": "consumer_research.yaml",
            "core_design": "content_core.yaml",
            "core_production": "content_core.yaml",  # 同一个文件
            "extension": "content_extension.yaml",
        }
        
        for stage in (stages_to_backup or []):
            file_name = stage_files.get(stage)
            if file_name:
                source = project_path / file_name
                if source.exists():
                    shutil.copy2(source, backup_path / file_name)
        
        # 保存版本元数据
        version.save_backup(str(self.storage_base))
        
        return version
    
    def restore_version(self, project_id: str, version_id: str) -> bool:
        """
        恢复到指定版本
        
        Args:
            project_id: 项目ID
            version_id: 版本ID
        
        Returns:
            bool: 是否成功
        """
        version_path = self.get_project_versions_path(project_id) / version_id
        if not version_path.exists():
            return False
        
        project_path = self.storage_base / "projects" / project_id
        
        # 在恢复前，先备份当前状态
        self.create_version(
            project_id=project_id,
            trigger_stage="restore",
            trigger_action="restore",
            description=f"恢复前自动备份",
            stages_to_backup=["intent", "research", "core_design", "extension"],
        )
        
        # 复制版本文件到项目目录
        for file in version_path.iterdir():
            if file.suffix == ".yaml" and file.name != "version.yaml":
                shutil.copy2(file, project_path / file.name)
        
        return True
    
    def delete_version(self, project_id: str, version_id: str) -> bool:
        """删除版本"""
        version_path = self.get_project_versions_path(project_id) / version_id
        if version_path.exists():
            shutil.rmtree(version_path)
            return True
        return False


# 全局版本管理器
version_manager = VersionManager()


