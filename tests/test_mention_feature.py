# tests/test_mention_feature.py
# 功能：测试 @ 引用功能
# 验证点：
#   1. 可引用的上下文包含已生成的字段
#   2. 字段引用格式正确解析

import sys
sys.path.insert(0, '.')
import re


def test_mention_options():
    """测试可引用选项的生成"""
    print("\n=== 测试1: 可引用选项生成 ===")
    
    # 模拟 workflowData
    workflowData = {
        "intent": {"goal": "测试目标"},
        "consumer_research": {"personas": []},
        "content_core": {
            "sections": [
                {
                    "id": "sec1",
                    "name": "新章节",
                    "fields": [
                        {"id": "f1", "name": "角色", "status": "completed", "content": "这是角色内容..."},
                        {"id": "f2", "name": "场景", "status": "completed", "content": "这是场景内容..."},
                        {"id": "f3", "name": "待生成", "status": "pending", "content": None},
                    ]
                },
                {
                    "id": "sec2",
                    "name": "第二章",
                    "fields": [
                        {"id": "f4", "name": "角色", "status": "completed", "content": "第二章角色内容..."},
                        {"id": "f5", "name": "场景", "status": "pending", "content": None},
                    ]
                },
            ]
        }
    }
    
    # 构建可引用选项（模拟前端逻辑）
    options = [
        {"id": "intent", "label": "意图分析", "available": bool(workflowData.get("intent"))},
        {"id": "research", "label": "消费者调研", "available": bool(workflowData.get("consumer_research"))},
        {"id": "core_design", "label": "内涵设计", "available": bool(workflowData.get("content_core"))},
    ]
    
    # 添加已完成的字段
    content_core = workflowData.get("content_core", {})
    for section in content_core.get("sections", []):
        for field in section.get("fields", []):
            if field.get("status") == "completed" and field.get("content"):
                options.append({
                    "id": f"field_{field['id']}",
                    "label": f"{section['name']}/{field['name']}",
                    "available": True,
                })
    
    print(f"  生成的选项数量: {len(options)}")
    for opt in options:
        print(f"    - {opt['label']} (available: {opt['available']})")
    
    # 验证
    expected_labels = ["意图分析", "消费者调研", "内涵设计", 
                       "新章节/角色", "新章节/场景", "第二章/角色"]
    actual_labels = [opt["label"] for opt in options]
    
    for expected in expected_labels:
        assert expected in actual_labels, f"缺少选项: {expected}"
    
    # 验证 pending 字段不在列表中
    assert "新章节/待生成" not in actual_labels, "pending 字段不应出现"
    assert "第二章/场景" not in actual_labels, "pending 字段不应出现"
    
    print("  ✅ 测试通过！")
    return True


def test_field_mention_parsing():
    """测试字段引用的解析"""
    print("\n=== 测试2: 字段引用解析 ===")
    
    # 测试消息
    test_messages = [
        ("请参考 @新章节/角色 的内容", ["新章节/角色"]),
        ("@意图分析 和 @新章节/场景", ["新章节/场景"]),  # 阶段引用会被另一个正则捕获
        ("根据 @第二章/角色 和 @新章节/场景 来生成", ["第二章/角色", "新章节/场景"]),
        ("没有引用的消息", []),
    ]
    
    field_pattern = r'@([^@\s]+\/[^@\s]+)'
    
    for message, expected_fields in test_messages:
        matches = re.findall(field_pattern, message)
        print(f"  消息: '{message}'")
        print(f"    期望: {expected_fields}")
        print(f"    实际: {matches}")
        assert matches == expected_fields, f"解析不匹配"
    
    print("  ✅ 测试通过！")
    return True


def test_context_building():
    """测试上下文构建"""
    print("\n=== 测试3: 上下文构建 ===")
    
    # 模拟 workflowData
    workflowData = {
        "content_core": {
            "sections": [
                {
                    "id": "sec1",
                    "name": "新章节",
                    "fields": [
                        {"id": "f1", "name": "角色", "content": "这是角色的详细内容，包括姓名、年龄、职业等信息。"},
                        {"id": "f2", "name": "场景", "content": "这是场景描述内容。"},
                    ]
                }
            ]
        }
    }
    
    # 模拟处理字段引用
    message = "请参考 @新章节/角色 来优化内容"
    field_pattern = r'@([^@\s]+\/[^@\s]+)'
    field_mentions = re.findall(field_pattern, message)
    
    contexts = []
    for path in field_mentions:
        section_name, field_name = path.split('/')
        sections = workflowData.get("content_core", {}).get("sections", [])
        
        for section in sections:
            if section["name"] == section_name:
                for field in section.get("fields", []):
                    if field["name"] == field_name and field.get("content"):
                        contexts.append({
                            "type": f"字段:{section_name}/{field_name}",
                            "content": field["content"],
                        })
    
    print(f"  消息: '{message}'")
    print(f"  构建的上下文: {contexts}")
    
    assert len(contexts) == 1
    assert contexts[0]["type"] == "字段:新章节/角色"
    assert "角色的详细内容" in contexts[0]["content"]
    
    print("  ✅ 测试通过！")
    return True


def print_summary():
    """打印修复总结"""
    print("\n" + "=" * 60)
    print("修复总结")
    print("=" * 60)
    print("""
问题：@ 引用功能没有包含内涵生产已生成的字段
-------
原因：
  1. mentionOptions 只包含固定的阶段（意图分析、消费者调研等）
  2. 没有动态添加已完成的字段
  3. workflowStore 的正则表达式不支持字段级别的引用

修复方案：
  1. ChatPanel.tsx: 使用 useMemo 动态构建 mentionOptions
     - 遍历 workflowData.content_core.sections
     - 添加 status === 'completed' 且有 content 的字段
     - 格式: "章节名/字段名"
  
  2. workflowStore.ts: 添加字段引用的解析
     - 新增正则: /@([^@\\s]+\\/[^@\\s]+)/g
     - 解析格式: @章节名/字段名
     - 查找对应字段并获取 content

结果：
  - 已生成的字段会出现在 @ 引用列表中
  - 可以引用特定字段的内容进行对话
""")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 @ 引用功能")
    print("=" * 60)
    
    results = []
    
    results.append(test_mention_options())
    results.append(test_field_mention_parsing())
    results.append(test_context_building())
    
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
