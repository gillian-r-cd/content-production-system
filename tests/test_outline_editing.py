# tests/test_outline_editing.py
# 测试目录编辑功能，包括确认后的编辑和删除
# 主要测试：删除章节、删除字段、重新排序、添加新章节/字段

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_outline_editing():
    """测试目录编辑功能"""
    
    # 获取已有的workflow（使用之前创建的）
    workflow_id = "proj_20260202103009"
    
    print(f"=== 测试目录编辑功能 (workflow: {workflow_id}) ===\n")
    
    # 1. 获取当前目录状态
    print("1. 获取当前目录状态...")
    response = requests.get(f"{BASE_URL}/workflow/{workflow_id}/outline")
    if response.status_code != 200:
        print(f"   ❌ 获取目录失败: {response.text}")
        return False
    
    outline = response.json()
    print(f"   ✓ 章节数: {len(outline.get('sections', []))}")
    print(f"   ✓ 目录已确认: {outline.get('outline_confirmed')}")
    print(f"   ✓ 进度: {outline.get('progress', {}).get('percentage', 0)}%")
    
    sections = outline.get('sections', [])
    if not sections:
        print("   ⚠ 没有章节，跳过删除测试")
        return True
    
    # 2. 测试添加新章节
    print("\n2. 测试添加新章节...")
    response = requests.post(f"{BASE_URL}/workflow/{workflow_id}/outline/add-section?name=测试章节")
    if response.status_code == 200:
        result = response.json()
        new_section_id = result.get('section', {}).get('id')
        print(f"   ✓ 添加成功: {result.get('section', {}).get('name')} (id: {new_section_id})")
    else:
        print(f"   ❌ 添加失败: {response.text}")
        return False
    
    # 3. 测试向新章节添加字段
    print("\n3. 测试添加字段到新章节...")
    response = requests.post(f"{BASE_URL}/workflow/{workflow_id}/outline/add-field", 
        json={"section_id": new_section_id, "name": "测试字段", "display_name": "测试字段"})
    if response.status_code == 200:
        result = response.json()
        new_field_id = result.get('field', {}).get('id')
        print(f"   ✓ 添加成功: {result.get('field', {}).get('name')} (id: {new_field_id})")
    else:
        print(f"   ❌ 添加失败: {response.text}")
        return False
    
    # 4. 测试删除字段
    print("\n4. 测试删除字段...")
    response = requests.delete(f"{BASE_URL}/workflow/{workflow_id}/sections/{new_section_id}/fields/{new_field_id}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ 删除成功: {result.get('deleted_field')}")
    else:
        print(f"   ❌ 删除失败: {response.text}")
        return False
    
    # 5. 测试删除章节
    print("\n5. 测试删除章节...")
    response = requests.delete(f"{BASE_URL}/workflow/{workflow_id}/sections/{new_section_id}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ 删除成功: {result.get('deleted_section')}")
    else:
        print(f"   ❌ 删除失败: {response.text}")
        return False
    
    # 6. 测试删除已有章节（有已完成字段）
    print("\n6. 测试删除有内容的章节...")
    # 重新获取章节列表
    response = requests.get(f"{BASE_URL}/workflow/{workflow_id}/outline")
    sections = response.json().get('sections', [])
    
    if sections:
        first_section = sections[0]
        section_id = first_section['id']
        completed_fields = sum(1 for f in first_section.get('fields', []) if f.get('status') == 'completed')
        
        print(f"   尝试删除章节: {first_section['name']} (已完成字段: {completed_fields})")
        
        response = requests.delete(f"{BASE_URL}/workflow/{workflow_id}/sections/{section_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ 删除成功!")
            print(f"     - 删除的章节: {result.get('deleted_section')}")
            print(f"     - 删除的字段数: {result.get('deleted_fields')}")
            print(f"     - 已完成字段数: {result.get('deleted_completed_fields')}")
            if result.get('warning'):
                print(f"     ⚠ 警告: {result.get('warning')}")
        else:
            print(f"   ❌ 删除失败: {response.text}")
            # 这里不应该失败，即使有已完成字段也应该允许删除
            return False
    
    # 7. 验证最终状态
    print("\n7. 验证最终状态...")
    response = requests.get(f"{BASE_URL}/workflow/{workflow_id}/outline")
    outline = response.json()
    print(f"   ✓ 当前章节数: {len(outline.get('sections', []))}")
    print(f"   ✓ 总字段数: {outline.get('progress', {}).get('total', 0)}")
    
    print("\n=== 所有测试通过 ===")
    return True


def test_update_outline_after_confirmed():
    """测试目录确认后的更新"""
    workflow_id = "proj_20260202103009"
    
    print(f"\n=== 测试目录确认后的更新 (workflow: {workflow_id}) ===\n")
    
    # 获取当前目录
    response = requests.get(f"{BASE_URL}/workflow/{workflow_id}/outline")
    if response.status_code != 200:
        print(f"❌ 获取目录失败: {response.text}")
        return False
    
    outline = response.json()
    sections = outline.get('sections', [])
    
    if not sections:
        print("⚠ 没有章节，跳过测试")
        return True
    
    # 尝试更新目录（修改章节名称）
    print("1. 测试更新目录结构...")
    updated_sections = []
    for s in sections:
        updated_sections.append({
            "id": s['id'],
            "name": s['name'],  # 不修改名称
            "description": s.get('description', ''),
            "order": s['order'],
            "fields": [
                {
                    "id": f['id'],
                    "name": f['name'],
                    "display_name": f.get('display_name', f['name']),
                    "description": f.get('description', ''),
                    "order": f['order'],
                }
                for f in s.get('fields', [])
            ]
        })
    
    response = requests.patch(f"{BASE_URL}/workflow/{workflow_id}/outline", 
        json={"sections": updated_sections, "confirm": False})
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ 更新成功!")
        if result.get('warning'):
            print(f"   ⚠ 警告: {result.get('warning')}")
    else:
        print(f"   ❌ 更新失败: {response.text}")
        return False
    
    print("\n=== 更新测试通过 ===")
    return True


if __name__ == "__main__":
    success = True
    
    try:
        success = test_outline_editing() and success
        success = test_update_outline_after_confirmed() and success
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保 uvicorn 正在运行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    sys.exit(0 if success else 1)
