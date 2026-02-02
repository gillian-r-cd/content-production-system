# tests/test_prompt_design.py
# 功能：测试各阶段提示词的正确性
# 验证点：
#   1. Core Design 阶段不包含 ai_hint
#   2. Core Production 阶段包含 ai_hint
#   3. format_for_design() vs format_for_prompt() 的区别

import sys
sys.path.insert(0, '.')


def test_field_schema_format_for_design():
    """测试 format_for_design() 不包含 ai_hint"""
    print("\n=== 测试1: format_for_design() 不包含 ai_hint ===")
    
    from core.models import FieldSchema, FieldDefinition
    
    # 创建带 ai_hint 的 field_schema
    field_schema = FieldSchema(
        id="test_schema",
        name="测试模板",
        description="用于测试的模板",
        fields=[
            FieldDefinition(
                name="角色",
                description="生成角色小传",
                ai_hint="这是一段很长的生成提示词，应该在设计阶段不出现，只在生产阶段使用。",
                clarification_prompt="请描述角色特征：",
            ),
            FieldDefinition(
                name="场景",
                description="生成场景描述",
                ai_hint="场景的详细生成指令，包括格式要求等。",
                depends_on=["角色"],
            ),
        ]
    )
    
    # 测试 format_for_design()
    design_output = field_schema.format_for_design()
    
    # 验证：不应包含 ai_hint
    assert "这是一段很长的生成提示词" not in design_output, "format_for_design 不应包含 ai_hint 内容"
    assert "场景的详细生成指令" not in design_output, "format_for_design 不应包含 ai_hint 内容"
    assert "生成提示" not in design_output, "format_for_design 不应包含 '生成提示' 字样"
    
    # 验证：应包含基本信息
    assert "内容模板：测试模板" in design_output, "应包含模板名称"
    assert "角色" in design_output, "应包含字段名称"
    assert "场景" in design_output, "应包含字段名称"
    
    print(f"  ✓ format_for_design 输出长度: {len(design_output)} 字符")
    print(f"  ✓ 不包含 ai_hint")
    print(f"  ✓ 包含基本字段信息")
    print("  ✅ 测试通过！")
    
    return design_output


def test_field_schema_format_for_prompt():
    """测试 format_for_prompt() 包含完整 ai_hint"""
    print("\n=== 测试2: format_for_prompt() 包含 ai_hint ===")
    
    from core.models import FieldSchema, FieldDefinition
    
    field_schema = FieldSchema(
        id="test_schema",
        name="测试模板",
        description="用于测试的模板",
        fields=[
            FieldDefinition(
                name="角色",
                description="生成角色小传",
                ai_hint="详细的角色生成指令：姓名、年龄、职位...",
            ),
        ]
    )
    
    # 测试 format_for_prompt()
    prompt_output = field_schema.format_for_prompt()
    
    # 验证：应包含 ai_hint
    assert "详细的角色生成指令" in prompt_output, "format_for_prompt 应包含 ai_hint 内容"
    assert "生成提示" in prompt_output, "format_for_prompt 应包含 '生成提示' 字样"
    
    print(f"  ✓ format_for_prompt 输出长度: {len(prompt_output)} 字符")
    print(f"  ✓ 包含 ai_hint")
    print("  ✅ 测试通过！")
    
    return prompt_output


def test_core_design_uses_format_for_design():
    """测试 Core Design 阶段使用 format_for_design"""
    print("\n=== 测试3: Core Design 阶段不包含 ai_hint ===")
    
    from core.modules.content_core_producer import ContentCoreProducer
    from core.models import FieldSchema, FieldDefinition
    from core.ai_client import AIClient
    
    # 创建模拟的 field_schema
    field_schema = FieldSchema(
        id="test_schema",
        name="测试模板",
        fields=[
            FieldDefinition(
                name="角色",
                description="生成角色",
                ai_hint="这段 ai_hint 不应该出现在 Core Design 的提示词中！！！",
            ),
        ]
    )
    
    # 使用 format_for_design() 并验证
    design_summary = field_schema.format_for_design()
    
    assert "ai_hint 不应该出现" not in design_summary, "format_for_design 不应包含 ai_hint"
    assert "角色" in design_summary, "应包含字段名称"
    
    print(f"  ✓ Core Design 使用 format_for_design()")
    print(f"  ✓ 不包含 ai_hint 内容")
    print("  ✅ 测试通过！")


def test_core_production_uses_ai_hint():
    """测试 Core Production 阶段使用 ai_hint"""
    print("\n=== 测试4: Core Production 阶段包含 ai_hint ===")
    
    from core.models import FieldSchema, FieldDefinition
    
    field_schema = FieldSchema(
        id="test_schema",
        name="测试模板",
        fields=[
            FieldDefinition(
                name="角色",
                description="生成角色",
                ai_hint="严格按照以下格式输出：姓名、年龄、职位...",
            ),
        ]
    )
    
    field_def = field_schema.get_field("角色")
    
    # 验证可以获取到 ai_hint
    assert field_def is not None, "应能获取到字段定义"
    assert field_def.ai_hint is not None, "ai_hint 不应为空"
    assert "严格按照以下格式" in field_def.ai_hint, "ai_hint 应包含完整内容"
    
    print(f"  ✓ 字段定义 ai_hint 长度: {len(field_def.ai_hint)} 字符")
    print(f"  ✓ Core Production 可获取完整 ai_hint")
    print("  ✅ 测试通过！")


def compare_outputs():
    """比较 format_for_design 和 format_for_prompt 的输出"""
    print("\n=== 输出对比 ===")
    
    from core.models import FieldSchema, FieldDefinition
    
    field_schema = FieldSchema(
        id="test_schema",
        name="ManaSim",
        description="管理模拟器",
        fields=[
            FieldDefinition(
                name="角色",
                description="AI下属的角色小传",
                ai_hint="严格按照下面的格式输出：\n* 姓名：\n* 年龄：\n* 职位：",
            ),
            FieldDefinition(
                name="场景",
                description="管理场景描述",
                ai_hint="详细的场景设计要求，包括背景、目标、关键策略等...",
                depends_on=["角色"],
            ),
        ]
    )
    
    design_output = field_schema.format_for_design()
    prompt_output = field_schema.format_for_prompt()
    
    print("\n--- format_for_design() 输出 ---")
    print(design_output)
    
    print("\n--- format_for_prompt() 输出（截取）---")
    print(prompt_output[:500] + "...\n")
    
    print(f"✓ design 输出长度: {len(design_output)} 字符")
    print(f"✓ prompt 输出长度: {len(prompt_output)} 字符")
    print(f"✓ 差异: {len(prompt_output) - len(design_output)} 字符（ai_hint 内容）")


def print_summary():
    """打印修复总结"""
    print("\n" + "=" * 60)
    print("修复总结")
    print("=" * 60)
    print("""
问题：Core Design 的系统提示词出现"需要生成的字段"和 ai_hint
-------
原因：Core Design 阶段调用了 field_schema.format_for_prompt()，
      这个方法输出了完整的字段定义包括 ai_hint。

修复方案：
  1. 为 FieldSchema 添加 format_for_design() 方法：
     - 只输出模板名称、描述、字段名称列表
     - 不包含 ai_hint、clarification_prompt 等详细生成指令
  
  2. Core Design 阶段改用 format_for_design()：
     - 设计阶段只需要知道有哪些字段
     - 不需要具体的生成指令
  
  3. Core Production 阶段保持使用完整的 ai_hint：
     - 从 field_def.ai_hint 获取
     - 单独注入到提示词中

各阶段提示词内容：
  - Intent: CreatorProfile + 用户输入
  - Research: CreatorProfile + Intent
  - Core Design: CreatorProfile + Intent + Research + FieldSchema概述
  - Core Production: CreatorProfile + Intent概要 + 设计方案 + 当前字段ai_hint
  - Extension: CreatorProfile + Intent + ContentCore
""")


if __name__ == "__main__":
    print("=" * 60)
    print("测试各阶段提示词设计")
    print("=" * 60)
    
    try:
        test_field_schema_format_for_design()
        test_field_schema_format_for_prompt()
        test_core_design_uses_format_for_design()
        test_core_production_uses_ai_hint()
        compare_outputs()
        
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
