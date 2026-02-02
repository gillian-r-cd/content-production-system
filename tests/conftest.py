# tests/conftest.py
# 功能：pytest全局配置和fixture定义
# 主要fixture：mock_ai_client, sample_creator_profile, sample_field_schema

# ===== 必须在其他导入之前处理环境变量 =====
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载.env文件（在导入任何其他模块之前）
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"Loaded .env from {env_path}")

# 修复：如果OPENAI_BASE_URL是空字符串，删除它
# OpenAI库会读取这个环境变量，空字符串会导致错误
if os.getenv("OPENAI_BASE_URL") == "":
    os.environ.pop("OPENAI_BASE_URL", None)
    print("Removed empty OPENAI_BASE_URL")

# ===== 现在可以安全导入其他模块 =====
import pytest


@pytest.fixture
def project_root_path():
    """返回项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture
def fixtures_path():
    """返回测试fixtures目录路径"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_storage(tmp_path):
    """
    创建临时存储目录结构，用于测试
    
    返回：
        dict: 包含各个存储目录的路径
    """
    storage = {
        "base": tmp_path / "storage",
        "creator_profiles": tmp_path / "storage" / "creator_profiles",
        "projects": tmp_path / "storage" / "projects",
    }
    
    for path in storage.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return storage


@pytest.fixture
def sample_creator_profile_data():
    """
    返回示例CreatorProfile数据（字典格式）
    用于测试序列化和模块功能
    """
    return {
        "id": "test_creator_001",
        "name": "测试创作者",
        "example_texts": [
            "说白了就是，很多人学东西学不会，不是因为笨，是因为他们总想一步到位。",
            "你品，你细品：学习这事儿，慢就是快。"
        ],
        "taboos": {
            "forbidden_words": ["躺赚", "割韭菜", "暴富"],
            "forbidden_topics": ["政治", "宗教"]
        },
        "custom_fields": {
            "调性": "口语化、略带自嘲",
            "写作节奏": "短句为主，每段不超过3行",
            "偏好结构": "先抛结论，再讲为什么",
            "口头禅": "说白了就是、你品你细品"
        }
    }


@pytest.fixture
def sample_field_schema_data():
    """
    返回示例FieldSchema数据（字典格式）
    用于测试品类字段定义
    """
    return {
        "id": "test_schema_001",
        "name": "测试课程介绍页",
        "description": "用于测试的课程介绍页字段模板",
        "fields": [
            {
                "name": "课程目标",
                "description": "学完后学员能做到什么",
                "type": "text",
                "required": True,
                "ai_hint": "用「能+动词+具体成果」的格式表述"
            },
            {
                "name": "痛点列表",
                "description": "目标学员当前面临的问题",
                "type": "list",
                "required": True,
                "ai_hint": "用学员的语言描述，要具体不要抽象"
            },
            {
                "name": "解决方案",
                "description": "这门课如何解决痛点",
                "type": "text",
                "required": True,
                "ai_hint": "要具体、可信，避免空泛承诺"
            }
        ],
        "is_template": True
    }


@pytest.fixture
def mock_ai_response():
    """
    返回模拟的AI响应
    用于测试不依赖真实API的场景
    """
    return {
        "intent_analysis": {
            "goal": "制作一个数据分析入门课程的介绍页",
            "success_criteria": ["转化率>5%", "用户停留时间>2分钟"],
            "must_have": ["学习成果", "课程大纲"],
            "must_avoid": ["过度承诺", "虚假案例"]
        },
        "consumer_research": {
            "persona": "职场3年，想转行数据分析的白领",
            "pain_points": ["不知道从何学起", "担心学不会"],
            "goals": ["找到数据分析工作", "提升职场竞争力"]
        }
    }

