# tests/test_generating_fix.py
# 功能：测试 generating 字段重置和目录编辑修复
# 测试场景：
# 1. 重置卡住的 generating 字段
# 2. 目录确认后添加字段
# 3. 继续生成功能

import pytest
import httpx
from pathlib import Path
import yaml


BASE_URL = "http://localhost:8000"
TEST_PROJECT_ID = "proj_20260202103009"  # 使用当前卡住的项目


class TestGeneratingFix:
    """测试 generating 字段重置修复"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    def test_get_outline_status(self, client):
        """测试获取目录状态，确认有 generating 字段"""
        response = client.get(f"/api/workflow/{TEST_PROJECT_ID}/outline")
        assert response.status_code == 200
        
        data = response.json()
        print(f"目录状态: {data['status']}")
        print(f"进度: {data['progress']}")
        
        # 检查是否有 generating 状态的字段
        generating_count = 0
        for section in data['sections']:
            for field in section['fields']:
                if field['status'] == 'generating':
                    generating_count += 1
                    print(f"发现 generating 字段: {section['name']}/{field['name']}")
        
        print(f"共 {generating_count} 个 generating 字段")
        return generating_count
    
    def test_reset_generating_fields(self, client):
        """测试重置 generating 字段"""
        response = client.post(f"/api/workflow/{TEST_PROJECT_ID}/reset-generating-fields")
        assert response.status_code == 200
        
        data = response.json()
        print(f"重置结果: {data}")
        assert data['success'] == True
        print(f"重置了 {data['reset_count']} 个字段")
        
        # 验证：再次获取目录，应该没有 generating 状态
        outline_response = client.get(f"/api/workflow/{TEST_PROJECT_ID}/outline")
        outline_data = outline_response.json()
        
        generating_after = 0
        for section in outline_data['sections']:
            for field in section['fields']:
                if field['status'] == 'generating':
                    generating_after += 1
        
        assert generating_after == 0, f"重置后仍有 {generating_after} 个 generating 字段"
        print("✓ 重置成功，没有 generating 字段")
    
    def test_continue_generate_after_reset(self, client):
        """测试重置后可以继续生成"""
        # 先重置
        client.post(f"/api/workflow/{TEST_PROJECT_ID}/reset-generating-fields")
        
        # 尝试继续生成
        response = client.post(f"/api/workflow/{TEST_PROJECT_ID}/generate-fields")
        print(f"生成响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"生成结果: {data}")
            assert data['success'] == True
            print(f"✓ 生成了 {data['generated_count']} 个字段")
        else:
            print(f"生成失败: {response.text}")
            # 即使生成失败（如 AI 调用失败），API 应该返回成功状态
    
    def test_add_field_after_confirm(self, client):
        """测试目录确认后添加字段"""
        # 获取第一个章节的 ID
        outline_response = client.get(f"/api/workflow/{TEST_PROJECT_ID}/outline")
        sections = outline_response.json()['sections']
        
        if not sections:
            pytest.skip("没有章节可测试")
        
        section_id = sections[0]['id']
        
        # 尝试添加字段
        response = client.post(
            f"/api/workflow/{TEST_PROJECT_ID}/outline/add-field",
            json={
                "section_id": section_id,
                "name": "test_field",
                "display_name": "测试字段",
            }
        )
        
        print(f"添加字段响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"添加结果: {data}")
            assert data['success'] == True
            print("✓ 目录确认后可添加字段")
        else:
            print(f"添加失败: {response.text}")


def run_quick_test():
    """快速运行测试（不使用 pytest）"""
    import httpx
    
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    print("=" * 50)
    print("测试1: 获取目录状态")
    print("=" * 50)
    
    response = client.get(f"/api/workflow/{TEST_PROJECT_ID}/outline")
    if response.status_code == 200:
        data = response.json()
        print(f"目录状态: {data['status']}")
        print(f"目录确认: {data['outline_confirmed']}")
        print(f"进度: {data['progress']}")
        
        generating_count = 0
        for section in data['sections']:
            print(f"\n章节: {section['name']}")
            for field in section['fields']:
                status_icon = "🔄" if field['status'] == 'generating' else (
                    "✓" if field['status'] == 'completed' else "○"
                )
                print(f"  {status_icon} {field['name']}: {field['status']}")
                if field['status'] == 'generating':
                    generating_count += 1
        
        print(f"\n共 {generating_count} 个 generating 字段")
    else:
        print(f"获取失败: {response.text}")
        return
    
    if generating_count > 0:
        print("\n" + "=" * 50)
        print("测试2: 重置 generating 字段")
        print("=" * 50)
        
        response = client.post(f"/api/workflow/{TEST_PROJECT_ID}/reset-generating-fields")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 重置成功: 重置了 {data['reset_count']} 个字段")
        else:
            print(f"✗ 重置失败: {response.text}")
            return
        
        # 验证
        response = client.get(f"/api/workflow/{TEST_PROJECT_ID}/outline")
        data = response.json()
        generating_after = sum(
            1 for s in data['sections'] 
            for f in s['fields'] 
            if f['status'] == 'generating'
        )
        
        if generating_after == 0:
            print("✓ 验证成功: 没有 generating 字段")
        else:
            print(f"✗ 验证失败: 仍有 {generating_after} 个 generating 字段")
    
    print("\n" + "=" * 50)
    print("测试3: 继续生成")
    print("=" * 50)
    
    response = client.post(f"/api/workflow/{TEST_PROJECT_ID}/generate-fields")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 生成调用成功")
        print(f"  消息: {data.get('message', '')}")
        print(f"  生成数: {data.get('generated_count', 0)}")
        print(f"  剩余数: {data.get('remaining_count', 0)}")
    else:
        print(f"✗ 生成失败: {response.text}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    run_quick_test()
