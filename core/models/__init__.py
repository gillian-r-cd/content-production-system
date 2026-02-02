# core/models/__init__.py
# 功能：数据模型包，定义系统的核心数据结构
# 主要模型：CreatorProfile, Project, Intent, ConsumerResearch, ContentCore, ContentExtension, FieldSchema, SimulatorFeedback

from .base import BaseModel
from .creator_profile import CreatorProfile, Taboos
from .field_schema import FieldSchema, FieldDefinition, create_default_field_schema
from .project import Project
from .intent import Intent, IntentConstraints
from .consumer_research import ConsumerResearch, StructuredResearch
from .content_core import ContentCore, ContentField
from .content_extension import ContentExtension, ChannelContent
from .simulator_feedback import SimulatorFeedback, Issue
from .report import ProcessReport, QualityReport, StageStatus
from .ai_call_log import AICallLog, log_store
from .project_version import ProjectVersion, VersionManager, version_manager

__all__ = [
    # 基类
    "BaseModel",
    # 创作者
    "CreatorProfile", "Taboos",
    # 品类定义
    "FieldSchema", "FieldDefinition", "create_default_field_schema",
    # 项目
    "Project",
    # 意图
    "Intent", "IntentConstraints",
    # 调研
    "ConsumerResearch", "StructuredResearch",
    # 内涵
    "ContentCore", "ContentField",
    # 外延
    "ContentExtension", "ChannelContent",
    # 评估
    "SimulatorFeedback", "Issue",
    # 报告
    "ProcessReport", "QualityReport", "StageStatus",
    # 日志
    "AICallLog", "log_store",
    # 版本管理
    "ProjectVersion", "VersionManager", "version_manager",
]

