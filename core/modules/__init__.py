# core/modules/__init__.py
# 功能：业务模块包，实现各阶段的处理逻辑
# 主要模块：IntentAnalyzer, ConsumerResearcher, ContentCoreProducer, ContentExtensionProducer, Simulator

from .base import BaseModule, ModuleResult
from .intent_analyzer import IntentAnalyzer
from .consumer_researcher import ConsumerResearcher
from .content_core_producer import ContentCoreProducer
from .content_extension_producer import ContentExtensionProducer
from .simulator import Simulator

__all__ = [
    "BaseModule",
    "ModuleResult",
    "IntentAnalyzer",
    "ConsumerResearcher",
    "ContentCoreProducer",
    "ContentExtensionProducer",
    "Simulator",
]

