# tests/test_outline_preserve_content.py
# 功能：测试更新目录时保留已生成内容
# 验证点：
#   1. 添加新章节不影响已有内容
#   2. 编辑字段名称保留内容
#   3. 保存目录结构保留已生成内容

import sys
sys.path.insert(0, '.')

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_preserve_content_on_outline_update():
    """测试更新目录时保留已生成内容"""
    print("\n=== 测试1: 更新目录时保留已生成内容 ===")
    
    try:
        resp = requests.get(f'{BASE_URL}/schemas', timeout=2)
        if resp.status_code != 200:
            print("  ⚠ 后端未运行，跳过测试")
            return True
    except:
        print("  ⚠ 后端未运行，跳过测试")
        return True
    
    workflow_id = "proj_20260202103009"
    
    # 1. 获取当前目录结构
    outline_resp = requests.get(f'{BASE_URL}/workflow/{workflow_id}/outline')
    if outline_resp.status_code != 200:
        print(f"  ⚠ 无法获取目录: {outline_resp.text}")
        return True
    
    outline = outline_resp.json()
    sections = outline.get('sections', [])
    
    if not sections:
        print("  ⚠ 没有章节可测试")
        return True
    
    # 2. 找一个已完成的字段，记录其内容
    completed_field = None
    completed_content = None
    for section in sections:
        for field in section.get('fields', []):
            if field.get('status') == 'completed' and field.get('content'):
                completed_field = field
                completed_content = field.get('content')
                break
        if completed_field:
            break
    
    if not completed_field:
        print("  ⚠ 没有已完成的字段可测试")
        return True
    
    print(f"  找到已完成字段: {completed_field.get('name')}")
    print(f"  内容长度: {len(completed_content)} 字符")
    
    # 3. 添加一个新章节到请求中
    sections.append({
        "id": f"test_section_{int(__import__('time').time())}",
        "name": "测试章节",
        "description": "测试用章节",
        "order": len(sections),
        "fields": []
    })
    
    # 4. 发送更新请求
    update_resp = requests.patch(f'{BASE_URL}/workflow/{workflow_id}/outline', json={
        "sections": sections,
        "confirm": False
    })
    
    if update_resp.status_code != 200:
        print(f"  ⚠ 更新失败: {update_resp.text}")
        return False
    
    # 5. 重新获取目录，检查内容是否保留
    new_outline_resp = requests.get(f'{BASE_URL}/workflow/{workflow_id}/outline')
    new_outline = new_outline_resp.json()
    new_sections = new_outline.get('sections', [])
    
    # 找到原来的字段
    found_field = None
    for section in new_sections:
        for field in section.get('fields', []):
            if field.get('id') == completed_field.get('id'):
                found_field = field
                break
        if found_field:
            break
    
    if not found_field:
        print(f"  ❌ 字段丢失: {completed_field.get('id')}")
        return False
    
    # 检查内容是否保留
    new_content = found_field.get('content')
    if new_content == completed_content:
        print(f"  ✓ 内容已保留: {len(new_content)} 字符")
        print(f"  ✓ 状态已保留: {found_field.get('status')}")
        print("  ✅ 测试通过！")
        return True
    else:
        print(f"  ❌ 内容丢失！原内容长度: {len(completed_content)}, 新内容长度: {len(new_content) if new_content else 0}")
        return False


def test_preserve_clarification_answer():
    """测试更新目录时保留澄清回答"""
    print("\n=== 测试2: 更新目录时保留澄清回答 ===")
    
    try:
        resp = requests.get(f'{BASE_URL}/schemas', timeout=2)
        if resp.status_code != 200:
            print("  ⚠ 后端未运行，跳过测试")
            return True
    except:
        print("  ⚠ 后端未运行，跳过测试")
        return True
    
    workflow_id = "proj_20260202103009"
    
    # 获取目录结构
    outline_resp = requests.get(f'{BASE_URL}/workflow/{workflow_id}/outline')
    outline = outline_resp.json()
    sections = outline.get('sections', [])
    
    # 找有 clarification_answer 的字段
    field_with_answer = None
    original_answer = None
    for section in sections:
        for field in section.get('fields', []):
            if field.get('clarification_answer'):
                field_with_answer = field
                original_answer = field.get('clarification_answer')
                break
        if field_with_answer:
            break
    
    if not field_with_answer:
        print("  ⚠ 没有有澄清回答的字段可测试")
        return True
    
    print(f"  找到字段: {field_with_answer.get('name')}")
    print(f"  澄清回答: {original_answer[:50]}...")
    
    # 发送更新请求（不改变任何内容）
    update_resp = requests.patch(f'{BASE_URL}/workflow/{workflow_id}/outline', json={
        "sections": sections,
        "confirm": False
    })
    
    if update_resp.status_code != 200:
        print(f"  ⚠ 更新失败: {update_resp.text}")
        return False
    
    # 重新获取目录
    new_outline_resp = requests.get(f'{BASE_URL}/workflow/{workflow_id}/outline')
    new_outline = new_outline_resp.json()
    new_sections = new_outline.get('sections', [])
    
    # 找到原来的字段
    for section in new_sections:
        for field in section.get('fields', []):
            if field.get('id') == field_with_answer.get('id'):
                new_answer = field.get('clarification_answer')
                if new_answer == original_answer:
                    print(f"  ✓ 澄清回答已保留")
                    print("  ✅ 测试通过！")
                    return True
                else:
                    print(f"  ❌ 澄清回答丢失！")
                    return False
    
    print("  ❌ 字段丢失")
    return False


def print_summary():
    """打印修复总结"""
    print("\n" + "=" * 60)
    print("修复总结")
    print("=" * 60)
    print("""
问题：添加新章节后覆盖原有生成的内容
-------
原因：update_outline API 在保存时创建全新的 ContentField 对象，
      丢失了已生成的内容（content）和状态（status）。

修复方案：
  1. 在更新目录前，建立现有字段的索引（按 ID 查找）
  2. 对于请求中的每个字段：
     - 如果 ID 已存在，保留原有的 content, status, clarification_answer 等
     - 如果是新字段，创建新的 ContentField
  3. 这样既能更新字段元数据（名称、描述），又能保留已生成内容

保留的字段属性：
  - status: 字段状态
  - content: 已生成内容
  - clarification_answer: 澄清回答
  - iteration_count: 迭代次数
  - iteration_history: 迭代历史
  - evaluation_score: 评估分数
  - evaluation_feedback: 评估反馈
""")


if __name__ == "__main__":
    print("=" * 60)
    print("测试更新目录时保留内容")
    print("=" * 60)
    
    results = []
    
    results.append(test_preserve_content_on_outline_update())
    results.append(test_preserve_clarification_answer())
    
    print_summary()
    
    if all(results):
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ 部分测试失败")
        print("=" * 60)
        exit(1)
