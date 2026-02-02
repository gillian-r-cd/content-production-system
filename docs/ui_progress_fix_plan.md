# UI进度显示修复计划
# 功能：修复阶段流转和进度显示问题
# 目标：确保用户能看到每个阶段的生成过程和结果

---

## 一、第一性原理反思

### 当前问题（从用户截图分析）

1. **阶段跳过**：消费者调研直接跳到内涵设计，违反 `Intent → ConsumerResearch → ContentCore` 流程
2. **进度盲区**：三个方案显示"暂无描述"，用户无法判断是没生成还是没展示
3. **对话历史丢失**：加载项目后右侧对话框只显示系统消息，之前的交互全部丢失
4. **状态不一致**：左侧进度栏显示"消费者调研"已完成，但中间面板显示的是"内涵设计"

### 根本原因

1. **后端**：`_run_research_stage` 没有等待用户确认，直接自动流转到下一阶段
2. **后端**：`_run_core_design_stage` 生成的方案数据没有完整保存到 `design_schemes`
3. **前端**：`CoreDesignStage` 组件读取 `design_schemes` 但字段可能为空或结构不对
4. **前端**：各阶段组件没有显示"正在生成..."的实时状态

### 正确的用户体验应该是

```
用户操作                     系统响应                        用户看到
─────────────────────────────────────────────────────────────────────
输入意图描述          →     显示"AI正在分析..."           → 加载动画
                           AI返回追问问题                 → 问题显示在右侧
回答追问              →     显示"正在生成意图..."         → 加载动画
                           意图分析完成                   → 中间面板显示意图详情
                           显示"是否确认？"               → 确认按钮
点击确认              →     显示"正在进行消费者调研..."   → 加载动画 + 实时进度
                           调研完成                       → 中间面板显示调研结果
                           显示"是否确认？"               → 确认按钮
点击确认              →     显示"正在生成设计方案..."     → 加载动画
                           方案生成完成                   → 中间面板显示3个方案详情
选择方案              →     显示"正在生成内容..."         → 逐字段生成进度
```

---

## 二、测试系统设计

### 2.1 阶段流转测试（后端）

```python
# tests/test_stage_flow.py

class TestStageFlow:
    """测试阶段不能被跳过"""
    
    def test_intent_must_complete_before_research(self):
        """意图分析必须完成后才能进入消费者调研"""
        # 创建项目，不提供意图
        # 尝试进入research阶段 → 应该失败
        pass
    
    def test_research_must_complete_before_core_design(self):
        """消费者调研必须完成后才能进入内涵设计"""
        # 创建项目，完成意图
        # 尝试跳过research进入core_design → 应该失败
        pass
    
    def test_each_stage_requires_user_confirmation(self):
        """每个阶段必须用户确认后才能进入下一阶段"""
        # 完成意图生成
        # 检查状态：waiting_for_input=True, input_callback="confirm_intent"
        pass
```

### 2.2 数据完整性测试（后端）

```python
# tests/test_data_integrity.py

class TestDataIntegrity:
    """测试每个阶段的数据必须完整"""
    
    def test_design_schemes_have_content(self):
        """设计方案必须包含具体内容"""
        # 运行core_design阶段
        # 检查每个scheme有：name, description, approach, details
        pass
    
    def test_research_has_personas(self):
        """消费者调研必须包含用户画像"""
        # 运行research阶段
        # 检查有：target_users, pain_points, needs
        pass
```

### 2.3 UI显示测试（前端）

```typescript
// tests/ui/stage-display.test.tsx

describe('StageDisplay', () => {
  it('shows loading state during AI generation', () => {
    // 当 isLoading=true 时，显示"正在生成..."
  })
  
  it('shows intent details after generation', () => {
    // 当 intent 有数据时，显示目标、成功标准、约束
  })
  
  it('shows research details after generation', () => {
    // 当 consumer_research 有数据时，显示用户画像
  })
  
  it('shows scheme details in core_design', () => {
    // 当 design_schemes 有数据时，显示每个方案的详细信息
  })
})
```

---

## 三、Benchmark 定义

### 3.1 阶段流转 Benchmark

| 测试项 | 预期结果 | 验收标准 |
|--------|----------|----------|
| Intent→Research | 用户点击"确认意图"后才进入 | waiting_for_input=True 直到用户确认 |
| Research→CoreDesign | 用户点击"确认调研"后才进入 | waiting_for_input=True 直到用户确认 |
| CoreDesign→CoreProduction | 用户选择方案后才进入 | selected_scheme_index != null |

### 3.2 数据完整性 Benchmark

| 数据字段 | 必填项 | 验收标准 |
|----------|--------|----------|
| design_schemes[].name | ✅ | 非空字符串 |
| design_schemes[].description | ✅ | 长度 > 20 字符 |
| design_schemes[].approach | ✅ | 非空字符串 |
| consumer_research.target_users | ✅ | 数组长度 > 0 |
| consumer_research.pain_points | ✅ | 数组长度 > 0 |

### 3.3 UI显示 Benchmark

| UI元素 | 状态 | 预期显示 |
|--------|------|----------|
| 中间面板 | isLoading=true | "正在生成..." + 加载动画 |
| 中间面板 | intent有数据 | 目标、成功标准、约束条件 |
| 中间面板 | schemes有数据 | 每个方案的name、description、approach |
| 右侧对话 | 加载项目后 | 恢复所有历史对话 |

---

## 四、详细 TODO List

### Phase 1: 修复阶段流转（后端）

- [ ] **1.1** 修改 `_run_intent_stage`：生成意图后设置 `waiting_for_input=True, input_callback="confirm_intent"`
- [ ] **1.2** 添加 `_handle_confirm_intent`：用户确认后才进入 research 阶段
- [ ] **1.3** 修改 `_run_research_stage`：生成调研后设置 `waiting_for_input=True, input_callback="confirm_research"`
- [ ] **1.4** 添加 `_handle_confirm_research`：用户确认后才进入 core_design 阶段
- [ ] **1.5** 修改 `_run_core_design_stage`：生成方案后设置 `waiting_for_input=True, input_callback="select_scheme"`
- [ ] **1.6** 单元测试：每个阶段的 waiting_for_input 正确设置

### Phase 2: 修复数据结构（后端）

- [ ] **2.1** 检查 `ContentCore.design_schemes` 的数据结构定义
- [ ] **2.2** 修改 `content_core_designer.py`：确保返回完整的 scheme 数据
- [ ] **2.3** 检查 `ConsumerResearch` 的数据结构定义
- [ ] **2.4** 修改 `consumer_researcher.py`：确保返回完整的调研数据
- [ ] **2.5** 单元测试：验证生成的数据结构完整

### Phase 3: 修复UI显示（前端）

- [ ] **3.1** 修改 `IntentStage.tsx`：显示完整的意图信息 + 确认按钮
- [ ] **3.2** 创建 `ResearchStage.tsx`：显示完整的调研信息 + 确认按钮
- [ ] **3.3** 修改 `CoreDesignStage.tsx`：显示完整的方案信息（name, description, approach）
- [ ] **3.4** 添加加载状态组件：统一的"正在生成..."显示
- [ ] **3.5** 修改 `EditorPanel.tsx`：根据 `isLoading` 显示加载状态

### Phase 4: 修复进度实时显示

- [ ] **4.1** 后端：在生成过程中发送进度事件（可选，SSE）
- [ ] **4.2** 前端：显示当前正在执行的步骤
- [ ] **4.3** 前端：显示 AI 调用次数变化

### Phase 5: 端到端测试

- [ ] **5.1** 测试完整流程：Intent → Research → CoreDesign → CoreProduction
- [ ] **5.2** 测试项目加载：加载后显示正确的阶段和数据
- [ ] **5.3** 测试对话历史：加载后恢复所有历史消息

---

## 五、执行顺序

**先后端，后前端，边做边测**

1. **Phase 1.1-1.6**（后端阶段流转）→ 运行单元测试验证
2. **Phase 2.1-2.5**（后端数据结构）→ 运行单元测试验证
3. **Phase 3.1-3.5**（前端UI）→ 手动验证
4. **Phase 5.1-5.3**（端到端测试）→ 完整流程验证

---

## 六、立即开始的第一步

**检查并修复后端 `_run_research_stage` 为什么没有等待用户确认**

当前代码：
```python
def _run_research_stage(self, state, input_data):
    result = researcher.run(...)
    if result.success:
        state.current_stage = "core_design"  # ❌ 直接跳转，没有等待确认
```

应该修改为：
```python
def _run_research_stage(self, state, input_data):
    result = researcher.run(...)
    if result.success:
        state.consumer_research = result.data
        state.waiting_for_input = True  # ✅ 等待用户确认
        state.input_prompt = "消费者调研已完成，请确认后进入内涵设计"
        state.input_callback = "confirm_research"
        # 不要在这里改变 current_stage
```


