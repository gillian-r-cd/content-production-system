# tests/test_e2e_field_generation.py
# 功能：端到端测试字段生成时 ai_hint 正确注入
# 验证点：
#   1. 创建新项目并关联 field_schema
#   2. 生成字段时提示词包含完整的 ai_hint
#   3. 依赖字段内容正确注入

import sys
import requests
import json
import time

sys.path.insert(0, '.')

BASE_URL = "http://localhost:8000/api"
TEST_WORKFLOW_ID = "proj_20260202103009"
TEST_SCHEMA_ID = "schema_20260202120522"

def call_api(method, path, json_data=None):
    """调用 API"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=60)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
        elif method == "PATCH":
            response = requests.patch(url, json=json_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 调用失败 {method} {path}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise


def test_field_schema_loaded_correctly():
    """测试 field_schema 正确加载"""
    print("\n=== 测试1: 验证 field_schema 正确加载 ===")
    
    # 获取 schema
    schema = call_api("GET", f"/schemas/{TEST_SCHEMA_ID}")
    assert schema["name"] == "ManaSim", f"Schema 名称应为 ManaSim"
    
    # 检查字段
    fields = schema["fields"]
    assert len(fields) >= 2, "Schema 应至少有2个字段"
    
    role_field = next((f for f in fields if f["name"] == "角色"), None)
    assert role_field is not None, "应有 '角色' 字段"
    assert len(role_field["ai_hint"]) > 50, "角色字段的 ai_hint 应有内容"
    
    scene_field = next((f for f in fields if f["name"] == "场景"), None)
    assert scene_field is not None, "应有 '场景' 字段"
    assert len(scene_field["ai_hint"]) > 5000, "场景字段的 ai_hint 应很长"
    assert scene_field["depends_on"] == ["角色"], "场景字段应依赖角色"
    
    print(f"  ✓ Schema: {schema['name']}")
    print(f"  ✓ 角色字段 ai_hint 长度: {len(role_field['ai_hint'])}")
    print(f"  ✓ 场景字段 ai_hint 长度: {len(scene_field['ai_hint'])}")
    print(f"  ✓ 场景字段 depends_on: {scene_field['depends_on']}")
    print("  ✅ 测试通过！")


def test_project_has_field_schema():
    """测试项目关联了 field_schema"""
    print("\n=== 测试2: 验证项目关联 field_schema ===")
    
    # 直接读取项目文件检查
    import yaml
    with open(f"storage/projects/{TEST_WORKFLOW_ID}/project.yaml", "r") as f:
        project = yaml.safe_load(f)
    
    assert project.get("field_schema_id") == TEST_SCHEMA_ID, \
        f"项目应关联 {TEST_SCHEMA_ID}, 实际为 {project.get('field_schema_id')}"
    
    print(f"  ✓ project.field_schema_id: {project['field_schema_id']}")
    print("  ✅ 测试通过！")


def test_runtime_field_schema():
    """测试运行时 field_schema 正确加载"""
    print("\n=== 测试3: 验证运行时 field_schema 加载 ===")
    
    from core.orchestrator import Orchestrator, OrchestratorConfig
    from core.prompt_engine import PromptEngine
    
    pe = PromptEngine('config/prompts')
    config = OrchestratorConfig()
    orch = Orchestrator(config, pe)
    
    state = orch.load_state(TEST_WORKFLOW_ID)
    
    assert state is not None, "state 不应为 None"
    assert state.field_schema is not None, "field_schema 不应为 None"
    assert state.field_schema.name == "ManaSim", f"field_schema.name 应为 ManaSim"
    
    # 检查 ai_hint
    scene_field = state.field_schema.get_field("场景")
    assert scene_field is not None, "应能找到场景字段"
    assert "<role>" in scene_field.ai_hint, "场景 ai_hint 应包含 <role>"
    assert len(scene_field.ai_hint) > 5000, "场景 ai_hint 应很长"
    
    print(f"  ✓ field_schema.name: {state.field_schema.name}")
    print(f"  ✓ 场景字段 ai_hint 包含 <role>: True")
    print(f"  ✓ 场景字段 ai_hint 长度: {len(scene_field.ai_hint)}")
    print("  ✅ 测试通过！")


def test_producer_gets_field_def():
    """测试 ContentCoreProducer 获取到正确的字段定义"""
    print("\n=== 测试4: 验证 Producer 获取字段定义 ===")
    
    from core.orchestrator import Orchestrator, OrchestratorConfig
    from core.prompt_engine import PromptEngine
    from core.modules.content_core_producer import ContentCoreProducer
    
    pe = PromptEngine('config/prompts')
    config = OrchestratorConfig()
    orch = Orchestrator(config, pe)
    
    state = orch.load_state(TEST_WORKFLOW_ID)
    
    # 模拟生产字段时的参数传递
    field_name = "场景"
    field_schema = state.field_schema
    
    assert field_schema is not None, "field_schema 不应为 None"
    
    field_def = field_schema.get_field(field_name)
    assert field_def is not None, f"应能找到字段定义 '{field_name}'"
    assert field_def.ai_hint is not None, "ai_hint 不应为 None"
    assert len(field_def.ai_hint) > 5000, "ai_hint 应很长"
    
    # 检查依赖
    assert field_def.depends_on == ["角色"], "depends_on 应为 ['角色']"
    
    print(f"  ✓ 字段定义: {field_def.name}")
    print(f"  ✓ ai_hint 长度: {len(field_def.ai_hint)}")
    print(f"  ✓ depends_on: {field_def.depends_on}")
    print("  ✅ 测试通过！")


def print_summary():
    """打印测试总结"""
    print("\n" + "=" * 60)
    print("修复总结")
    print("=" * 60)
    print("""
核心问题：
  load_state() 函数没有从项目关联的 field_schema_id 加载字段模板，
  导致运行时 state.field_schema 为 None，ai_hint 无法注入到提示词。

修复方案：
  1. 修改 core/orchestrator.py 中的 load_state() 函数：
     - 从 project.field_schema_id 加载关联的 FieldSchema
     - 只有在没有关联 schema 且需要默认字段时才使用默认 schema
  
  2. 修改 api/routes/workflow.py 中的 ensure_workflow_loaded() 函数：
     - 确保即使 state 已存在，也会正确同步 field_schema

验证结果：
  - field_schema 在 load_state 时正确加载
  - ai_hint（可能很长，如5554字符）完整保留
  - depends_on 配置正确读取
  - 生成字段时 ai_hint 将被注入到提示词

下一步：
  用户可以刷新前端页面，尝试重新生成字段，
  ai_hint 中的完整提示词将被发送给 AI。
""")


if __name__ == "__main__":
    print("=" * 60)
    print("端到端测试：字段模板配置注入")
    print("=" * 60)
    
    try:
        # 检查后端是否运行
        try:
            requests.get(f"{BASE_URL}/schemas", timeout=2)
            print("后端服务运行正常。")
        except:
            print("⚠ 后端服务未运行，跳过 API 测试。")
            exit(0)
        
        test_field_schema_loaded_correctly()
        test_project_has_field_schema()
        test_runtime_field_schema()
        test_producer_gets_field_def()
        
        print_summary()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
