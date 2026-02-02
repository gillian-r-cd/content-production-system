# tests/test_settings_fix.py
# 功能：验证设置相关修复 - 项目描述保存、Profile完整数据
# 主要测试：PUT项目、load_project返回完整profile

import httpx

BASE_URL = "http://localhost:8000"


def test_project_update():
    """
    测试：项目描述保存
    
    Benchmark:
    1. PUT /projects/{id} 返回 200
    2. 更新后 GET 能获取到新的描述
    """
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. 获取项目列表
        response = client.get("/api/projects")
        assert response.status_code == 200, f"获取项目列表失败: {response.text}"
        projects = response.json()
        
        if not projects:
            print("没有项目，跳过测试")
            return
        
        project_id = projects[0]["id"]
        print(f"测试项目: {project_id}")
        
        # 2. 更新项目描述
        new_description = "测试更新的项目描述_" + str(int(__import__('time').time()))
        response = client.put(f"/api/projects/{project_id}", json={
            "description": new_description
        })
        
        print(f"PUT 响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"响应内容: {response.text}")
            assert False, f"PUT 失败: {response.text}"
        
        result = response.json()
        print(f"  - 返回的描述: {result.get('description', 'None')[:50]}...")
        
        # Benchmark 1: 验证返回正确
        assert result.get('description') == new_description, "返回的描述不匹配"
        print("✓ Benchmark 1 通过: PUT 返回正确")
        
        # 3. GET 验证
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        result = response.json()
        
        # Benchmark 2: 验证持久化
        assert result.get('description') == new_description, "GET 的描述不匹配"
        print("✓ Benchmark 2 通过: 描述已持久化")
        
        print("✅ 项目更新测试通过!")


def test_load_project_full_profile():
    """
    测试：load_project 返回完整 profile 数据
    
    Benchmark:
    1. profile 包含 taboos 字段
    2. profile.taboos 包含 forbidden_words
    3. profile 包含 example_texts
    """
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. 获取项目列表
        response = client.get("/api/projects")
        assert response.status_code == 200
        projects = response.json()
        
        if not projects:
            print("没有项目，跳过测试")
            return
        
        project_id = projects[0]["id"]
        print(f"测试项目: {project_id}")
        
        # 2. 加载项目
        response = client.post(f"/api/workflow/load/{project_id}")
        
        print(f"load_project 响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"响应内容: {response.text}")
            assert False, f"load_project 失败: {response.text}"
        
        data = response.json()
        profile = data.get("profile")
        
        print(f"Profile 数据:")
        print(f"  - id: {profile.get('id') if profile else 'None'}")
        print(f"  - name: {profile.get('name') if profile else 'None'}")
        
        if not profile:
            print("项目没有关联 profile，跳过测试")
            return
        
        # Benchmark 1: 验证包含 taboos
        taboos = profile.get("taboos")
        assert taboos is not None, "profile 缺少 taboos 字段"
        print(f"  - taboos: {taboos}")
        print("✓ Benchmark 1 通过: profile 包含 taboos")
        
        # Benchmark 2: 验证 taboos 结构
        forbidden_words = taboos.get("forbidden_words", [])
        forbidden_topics = taboos.get("forbidden_topics", [])
        print(f"  - forbidden_words count: {len(forbidden_words)}")
        print(f"  - forbidden_topics count: {len(forbidden_topics)}")
        assert "forbidden_words" in taboos, "taboos 缺少 forbidden_words"
        assert "forbidden_topics" in taboos, "taboos 缺少 forbidden_topics"
        print("✓ Benchmark 2 通过: taboos 结构正确")
        
        # Benchmark 3: 验证 example_texts
        example_texts = profile.get("example_texts", [])
        print(f"  - example_texts count: {len(example_texts)}")
        assert "example_texts" in profile, "profile 缺少 example_texts"
        print("✓ Benchmark 3 通过: profile 包含 example_texts")
        
        print("✅ load_project 完整 profile 测试通过!")


def test_simulator_api():
    """
    测试：Simulator API
    
    Benchmark:
    1. GET /simulators 返回列表
    2. POST 创建成功
    3. GET 单个返回正确
    4. PUT 更新成功
    5. DELETE 删除成功
    """
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. 获取列表
        response = client.get("/api/simulators")
        assert response.status_code == 200, f"获取列表失败: {response.text}"
        print(f"当前 Simulator 数量: {len(response.json())}")
        print("✓ Benchmark 1 通过: GET 列表成功")
        
        # 2. 创建
        test_data = {
            "name": "测试评估器",
            "description": "用于测试的评估器",
            "prompt_template": "测试提示词 {content}",
            "auto_iterate": True,
            "trigger_score": 6.0,
            "stop_score": 8.0,
            "max_iterations": 3,
        }
        response = client.post("/api/simulators", json=test_data)
        assert response.status_code == 201, f"创建失败: {response.text}"
        created = response.json()
        simulator_id = created["id"]
        print(f"创建成功: {simulator_id}")
        print("✓ Benchmark 2 通过: POST 创建成功")
        
        # 3. 获取单个
        response = client.get(f"/api/simulators/{simulator_id}")
        assert response.status_code == 200
        assert response.json()["name"] == test_data["name"]
        print("✓ Benchmark 3 通过: GET 单个成功")
        
        # 4. 更新
        updated_data = {**test_data, "name": "更新后的评估器"}
        response = client.put(f"/api/simulators/{simulator_id}", json=updated_data)
        assert response.status_code == 200
        assert response.json()["name"] == "更新后的评估器"
        print("✓ Benchmark 4 通过: PUT 更新成功")
        
        # 5. 删除
        response = client.delete(f"/api/simulators/{simulator_id}")
        assert response.status_code == 200
        print("✓ Benchmark 5 通过: DELETE 删除成功")
        
        print("✅ Simulator API 测试通过!")


if __name__ == "__main__":
    print("=" * 60)
    print("设置相关修复验证测试")
    print("=" * 60)
    
    print("\n--- 测试 1: 项目描述保存 ---")
    try:
        test_project_update()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n--- 测试 2: load_project 返回完整 profile ---")
    try:
        test_load_project_full_profile()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n--- 测试 3: Simulator API ---")
    try:
        test_simulator_api()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
