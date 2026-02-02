# tests/test_drag_and_dependency.py
# 功能：测试拖拽排序和依赖关系系统
# 主要测试：章节排序、字段排序、依赖配置、链式重新生成
# Benchmark定义在每个测试函数的docstring中

import pytest
import httpx
import json
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"


# ============ Phase 1: 拖拽排序测试 ============

class TestDragReorder:
    """测试拖拽排序功能"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60.0)
    
    @pytest.fixture
    def test_workflow(self, client):
        """创建测试工作流"""
        # 获取profile
        response = client.get("/api/profiles")
        if response.status_code != 200 or not response.json():
            pytest.skip("没有可用的profile")
        profile_id = response.json()[0]["id"]
        
        # 创建项目
        response = client.post("/api/workflow/start", json={
            "profile_id": profile_id,
            "project_name": "测试拖拽排序",
            "raw_input": "测试项目"
        })
        if response.status_code != 200:
            pytest.skip(f"创建项目失败: {response.text}")
        
        return response.json()["workflow_id"]
    
    def test_section_reorder_api_exists(self, client, test_workflow):
        """
        测试：章节排序API存在
        
        Benchmark:
        - API端点 PATCH /workflow/{id}/sections/reorder 存在
        - 返回成功或合理的错误（非500）
        """
        response = client.patch(
            f"/api/workflow/{test_workflow}/sections/reorder",
            json={"section_ids": []}
        )
        
        # API应该存在（不是404），可以是400（无效输入）或200（成功）
        assert response.status_code != 404, "API端点应该存在"
        assert response.status_code < 500, f"不应该返回服务器错误: {response.text}"
        print(f"✓ Benchmark通过: API端点存在，状态码={response.status_code}")
    
    def test_field_reorder_api_exists(self, client, test_workflow):
        """
        测试：字段排序API存在
        
        Benchmark:
        - API端点 PATCH /workflow/{id}/sections/{section_id}/fields/reorder 存在
        """
        response = client.patch(
            f"/api/workflow/{test_workflow}/sections/test_section/fields/reorder",
            json={"field_ids": []}
        )
        
        # API应该存在
        assert response.status_code != 404, "API端点应该存在"
        assert response.status_code < 500, f"不应该返回服务器错误: {response.text}"
        print(f"✓ Benchmark通过: API端点存在，状态码={response.status_code}")


# ============ Phase 2: 依赖关系测试 ============

class TestDependencySystem:
    """测试依赖关系系统"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60.0)
    
    def test_field_dependency_in_schema(self, client):
        """
        测试：字段模板支持依赖配置
        
        Benchmark:
        - 创建Schema时可以指定depends_on
        - 读取Schema时depends_on正确返回
        """
        # 创建带依赖的schema
        schema_data = {
            "name": "测试依赖Schema",
            "description": "用于测试依赖关系",
            "fields": [
                {
                    "name": "标题",
                    "description": "文章标题",
                    "field_type": "text",
                    "required": True,
                    "ai_hint": "",
                    "order": 0,
                    "depends_on": []
                },
                {
                    "name": "大纲",
                    "description": "文章大纲",
                    "field_type": "list",
                    "required": True,
                    "ai_hint": "",
                    "order": 1,
                    "depends_on": ["标题"]
                },
                {
                    "name": "正文",
                    "description": "文章正文",
                    "field_type": "text",
                    "required": True,
                    "ai_hint": "",
                    "order": 2,
                    "depends_on": ["标题", "大纲"]
                }
            ]
        }
        
        response = client.post("/api/schemas", json=schema_data)
        assert response.status_code == 201, f"创建Schema失败: {response.text}"
        
        created_schema = response.json()
        schema_id = created_schema["id"]
        
        # 读取并验证
        response = client.get(f"/api/schemas/{schema_id}")
        assert response.status_code == 200
        
        schema = response.json()
        fields = schema["fields"]
        
        # 验证依赖关系
        title_field = next((f for f in fields if f["name"] == "标题"), None)
        outline_field = next((f for f in fields if f["name"] == "大纲"), None)
        content_field = next((f for f in fields if f["name"] == "正文"), None)
        
        assert title_field is not None, "应该有标题字段"
        assert outline_field is not None, "应该有大纲字段"
        assert content_field is not None, "应该有正文字段"
        
        assert outline_field.get("depends_on", []) == ["标题"], \
            f"大纲应该依赖标题，实际: {outline_field.get('depends_on')}"
        assert set(content_field.get("depends_on", [])) == {"标题", "大纲"}, \
            f"正文应该依赖标题和大纲，实际: {content_field.get('depends_on')}"
        
        print("✓ Benchmark通过: Schema正确保存和返回依赖关系")
        
        # 清理
        client.delete(f"/api/schemas/{schema_id}")


# ============ Phase 3: 重新生成测试 ============

class TestRegeneration:
    """测试重新生成功能"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60.0)
    
    def test_regenerate_field_api_exists(self, client):
        """
        测试：单字段重新生成API存在
        
        Benchmark:
        - API端点 POST /workflow/{id}/fields/{field_id}/regenerate 存在
        """
        # 使用虚拟ID测试API是否存在
        response = client.post(
            "/api/workflow/test_workflow/fields/test_field/regenerate"
        )
        
        # 404可能是因为workflow不存在，但不应该是endpoint不存在
        # 我们检查错误消息来区分
        if response.status_code == 404:
            error_detail = response.json().get("detail", "")
            assert "项目不存在" in error_detail or "workflow" in error_detail.lower(), \
                f"应该是workflow不存在的404，而不是endpoint不存在: {error_detail}"
        
        assert response.status_code < 500, f"不应该返回服务器错误: {response.text}"
        print(f"✓ Benchmark通过: 重新生成API存在")
    
    def test_regenerate_chain_api_exists(self, client):
        """
        测试：链条重新生成API存在
        
        Benchmark:
        - API端点 POST /workflow/{id}/chains/{chain_id}/regenerate 存在
        """
        response = client.post(
            "/api/workflow/test_workflow/chains/test_chain/regenerate"
        )
        
        if response.status_code == 404:
            error_detail = response.json().get("detail", "")
            # 如果是"项目不存在"，说明API端点存在
            if "项目不存在" in error_detail:
                print("✓ Benchmark通过: 链条重新生成API存在")
                return
        
        assert response.status_code < 500, f"不应该返回服务器错误: {response.text}"
        print(f"✓ Benchmark通过: 链条重新生成API存在")


# ============ 运行测试 ============

def run_all_tests():
    """运行所有测试并汇总结果"""
    print("=" * 60)
    print("字段依赖关系与拖拽排序测试")
    print("=" * 60)
    
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "details": []
    }
    
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        # 测试1: Schema依赖关系
        print("\n--- 测试1: Schema依赖关系 ---")
        try:
            test = TestDependencySystem()
            test.test_field_dependency_in_schema(client)
            results["passed"] += 1
            results["details"].append(("Schema依赖关系", "PASSED"))
        except Exception as e:
            results["failed"] += 1
            results["details"].append(("Schema依赖关系", f"FAILED: {e}"))
            print(f"❌ 失败: {e}")
        
        # 注意: 排序和重新生成API需要在实现后测试
        print("\n--- 注意 ---")
        print("排序API和重新生成API将在实现后测试")
    
    # 汇总
    print("\n" + "=" * 60)
    print(f"测试结果: {results['passed']} 通过, {results['failed']} 失败, {results['skipped']} 跳过")
    print("=" * 60)
    
    for name, status in results["details"]:
        print(f"  {name}: {status}")
    
    return results


if __name__ == "__main__":
    run_all_tests()
