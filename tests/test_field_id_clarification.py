# tests/test_field_id_clarification.py
# 功能：测试使用字段 ID 精确查找澄清问题
# 验证点：
#   1. 多个同名字段时，使用 ID 精确更新
#   2. 提交回答后不会再次弹窗

import sys
sys.path.insert(0, '.')


def test_field_id_precision():
    """测试字段 ID 精确查找"""
    print("\n=== 测试1: 字段 ID 精确查找 ===")
    
    from core.models import ContentCore, ContentSection, ContentField
    
    # 创建有同名字段的 content_core
    content_core = ContentCore(
        id="test_core",
        project_id="test_project",
        field_schema_id="test_schema",
        sections=[
            ContentSection(
                id="section_1",
                name="章节1",
                fields=[
                    ContentField(id="field_1", name="角色", status="completed", content="角色1内容"),
                    ContentField(id="field_2", name="场景", status="completed", content="场景1内容"),
                ]
            ),
            ContentSection(
                id="section_2",
                name="章节2",
                fields=[
                    ContentField(id="field_3", name="角色", status="pending"),  # 同名字段！
                    ContentField(id="field_4", name="场景", status="pending"),
                ]
            ),
        ]
    )
    
    # 使用名称查找 - 会返回第一个匹配的（章节1的角色）
    field_by_name = content_core.get_field("角色")
    assert field_by_name.id == "field_1", f"按名称查找应返回第一个匹配，实际返回 {field_by_name.id}"
    print(f"  ✓ 按名称查找 '角色' 返回: {field_by_name.id} (第一个匹配)")
    
    # 使用 ID 查找 - 精确匹配
    field_by_id = content_core.get_field("field_3")
    assert field_by_id.id == "field_3", f"按 ID 查找应精确匹配，实际返回 {field_by_id.id}"
    assert field_by_id.name == "角色", f"字段名应为 '角色'，实际是 {field_by_id.name}"
    print(f"  ✓ 按 ID 查找 'field_3' 返回: {field_by_id.id} (精确匹配)")
    
    # 设置澄清回答
    field_by_id.clarification_answer = "测试回答"
    
    # 验证只有 field_3 被更新
    field_1 = content_core.get_field("field_1")
    field_3 = content_core.get_field("field_3")
    
    assert field_1.clarification_answer is None, "field_1 不应被更新"
    assert field_3.clarification_answer == "测试回答", "field_3 应被更新"
    
    print(f"  ✓ field_1 (章节1的角色) 澄清回答: {field_1.clarification_answer}")
    print(f"  ✓ field_3 (章节2的角色) 澄清回答: {field_3.clarification_answer}")
    print("  ✅ 测试通过！")
    return True


def test_clarification_logic():
    """测试澄清弹窗逻辑"""
    print("\n=== 测试2: 澄清弹窗只出现一次 ===")
    
    from core.models import ContentField, FieldSchema, FieldDefinition
    
    # 创建字段定义
    field_schema = FieldSchema(
        id="test_schema",
        name="测试",
        fields=[
            FieldDefinition(
                name="角色",
                clarification_prompt="请描述角色特征：",
            ),
        ]
    )
    
    # 场景1：没有回答 - 应该弹窗
    field_no_answer = ContentField(
        id="field_1",
        name="角色",
        status="pending",
    )
    
    field_def = field_schema.get_field("角色")
    should_ask_1 = (field_def and field_def.clarification_prompt and not field_no_answer.clarification_answer)
    assert should_ask_1 == True, "没有回答时应该弹窗"
    print(f"  ✓ 没有 clarification_answer: 需要弹窗 = {should_ask_1}")
    
    # 场景2：已有回答 - 不应该弹窗
    field_with_answer = ContentField(
        id="field_1",
        name="角色",
        status="pending",
        clarification_answer="已经回答过了",
    )
    
    should_ask_2 = (field_def and field_def.clarification_prompt and not field_with_answer.clarification_answer)
    assert should_ask_2 == False, "已有回答时不应该弹窗"
    print(f"  ✓ 有 clarification_answer: 需要弹窗 = {should_ask_2}")
    
    print("  ✅ 测试通过！")
    return True


def print_summary():
    """打印修复总结"""
    print("\n" + "=" * 60)
    print("修复总结")
    print("=" * 60)
    print("""
问题：提交澄清回答后，弹窗又马上出现再问一遍
-------
原因：
  1. 多个章节可能有同名字段（如都有"角色"）
  2. clarify API 使用 field_name 查找字段
  3. get_field("角色") 返回第一个匹配的字段
  4. 实际需要回答的字段（第二个章节的"角色"）没有被更新
  5. 继续生成时，该字段仍然没有 clarification_answer，再次触发弹窗

修复方案：
  1. orchestrator: state.current_field 保存字段 ID 而不是名称
  2. API: 返回 field_id 和 field_name
  3. 前端: 保存 clarificationFieldId，提交时使用 ID
  4. clarify API: 优先使用 field_id 精确查找

关键代码变更：
  - state.current_field = current_field.id  // 使用 ID
  - clarification: { field_id, field_name, question }  // 返回 ID
  - apiClient.post(clarify, { field_id, field_name })  // 传递 ID
""")


if __name__ == "__main__":
    print("=" * 60)
    print("测试字段 ID 精确查找")
    print("=" * 60)
    
    results = []
    
    results.append(test_field_id_precision())
    results.append(test_clarification_logic())
    
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
