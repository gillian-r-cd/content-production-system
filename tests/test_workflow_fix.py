# tests/test_workflow_fix.py
# 功能：验证工作流修复 - 加载项目后发送消息能正确进入下一阶段
# 主要测试：load_project后respond能正确处理

import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:8000"


def test_workflow_load_and_respond():
    """
    测试：加载项目 → 发送描述 → 验证进入下一阶段
    
    Benchmark:
    1. load_project 返回 input_callback = "intent_input"
    2. respond 后 current_stage 从 "intent" 变为其他阶段或有追问
    3. AI 有有效响应
    """
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        # 1. 获取项目列表
        response = client.get("/api/projects")
        assert response.status_code == 200, f"获取项目列表失败: {response.text}"
        projects = response.json()
        
        if not projects:
            print("没有项目，跳过测试")
            return
        
        project_id = projects[0]["id"]
        print(f"测试项目: {project_id}")
        
        # 2. 加载项目
        response = client.post(f"/api/workflow/load/{project_id}")
        assert response.status_code == 200, f"加载项目失败: {response.text}"
        data = response.json()
        
        print(f"加载结果:")
        print(f"  - workflow_id: {data['workflow_id']}")
        print(f"  - current_stage: {data['status']['current_stage']}")
        print(f"  - waiting_for_input: {data['status']['waiting_for_input']}")
        print(f"  - input_prompt: {data['status'].get('input_prompt', 'None')}")
        
        # Benchmark 1: 验证 intent 阶段有正确设置
        if data['status']['current_stage'] == 'intent' and not data['data'].get('intent'):
            assert data['status']['waiting_for_input'] == True, "应该等待用户输入"
            assert data['status']['input_prompt'] is not None, "应该有输入提示"
            print("✓ Benchmark 1 通过: intent 阶段正确设置")
        
        # 3. 如果在 intent 阶段且没有 intent，发送描述
        if data['status']['current_stage'] == 'intent' and not data['data'].get('intent'):
            test_input = "我想制作一个关于 AI 辅导工具的培训课程，帮助销售人员提升管理能力"
            
            print(f"\n发送描述: {test_input[:50]}...")
            
            response = client.post(
                f"/api/workflow/{project_id}/respond",
                json={"answer": test_input}
            )
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                print(f"响应内容: {response.text}")
                assert False, f"respond 失败: {response.text}"
            
            result = response.json()
            
            print(f"respond 结果:")
            print(f"  - current_stage: {result['current_stage']}")
            print(f"  - waiting_for_input: {result['waiting_for_input']}")
            print(f"  - input_prompt: {result.get('input_prompt', 'None')[:100] if result.get('input_prompt') else 'None'}...")
            
            # Benchmark 2: 验证有响应
            # 要么阶段变化，要么有追问，都说明处理成功
            stage_changed = result['current_stage'] != 'intent'
            has_clarification = result['waiting_for_input'] and result.get('input_prompt')
            
            assert stage_changed or has_clarification, \
                "应该有阶段变化或追问，但都没有"
            
            print("✓ Benchmark 2 通过: respond 正确处理")
            
            # Benchmark 3: 验证 AI 调用次数增加
            assert result['ai_call_count'] > 0, "应该有 AI 调用"
            print(f"✓ Benchmark 3 通过: AI 调用次数 = {result['ai_call_count']}")
        
        else:
            print(f"项目已在 {data['status']['current_stage']} 阶段，跳过 intent 测试")
        
        print("\n✅ 所有测试通过!")


def test_workflow_start_flow():
    """
    测试：完整的 start 流程
    
    Benchmark:
    1. 创建项目成功
    2. 调用 start 后有响应
    3. 状态正确更新
    """
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        # 1. 获取 profile
        response = client.get("/api/profiles")
        assert response.status_code == 200
        profiles = response.json()
        
        if not profiles:
            print("没有 profile，跳过测试")
            return
        
        profile_id = profiles[0]["id"]
        print(f"使用 profile: {profile_id}")
        
        # 2. 启动工作流
        test_input = "测试项目：AI 销售培训课程"
        response = client.post("/api/workflow/start", json={
            "profile_id": profile_id,
            "project_name": "测试项目_workflow_fix",
            "raw_input": test_input
        })
        
        print(f"start 响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"响应内容: {response.text}")
            assert False, f"start 失败: {response.text}"
        
        result = response.json()
        
        print(f"start 结果:")
        print(f"  - workflow_id: {result['workflow_id']}")
        print(f"  - current_stage: {result['status']['current_stage']}")
        print(f"  - waiting_for_input: {result['status']['waiting_for_input']}")
        
        # 验证
        assert result['workflow_id'], "应该有 workflow_id"
        assert result['status']['ai_call_count'] > 0, "应该有 AI 调用"
        
        print("✅ start 流程测试通过!")


if __name__ == "__main__":
    print("=" * 60)
    print("工作流修复验证测试")
    print("=" * 60)
    
    print("\n--- 测试 1: 加载项目后发送描述 ---")
    try:
        test_workflow_load_and_respond()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n--- 测试 2: 完整 start 流程 ---")
    try:
        test_workflow_start_flow()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
