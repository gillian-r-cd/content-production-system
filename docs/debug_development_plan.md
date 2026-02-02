# 调试功能与问题修复开发计划

## 一、问题分析

### 问题1: API超时 (60秒)
- **现象**：意图分析完成后，API调用超时
- **原因**：消费者调研或内涵生产阶段AI生成耗时超过60秒
- **解决方案**：
  1. 增加超时时间到180秒
  2. 后端使用流式响应（SSE）
  3. 前端显示加载进度

### 问题2: 缺少调试视图
- **需求**：查看每一步的输入(prompt)和输出(response)
- **解决方案**：
  1. 后端记录每次AI调用日志
  2. 设置界面增加"调试日志"页面
  3. 显示完整prompt模板和变量替换结果

---

## 二、开发阶段

### Phase 1: 修复超时问题

**文件清单**：
- `web/src/api/client.ts` - 增加超时时间
- `api/routes/workflow.py` - 增加SSE流式响应支持

**Benchmark**：
- [ ] API调用不再超时
- [ ] 长时间操作显示加载状态
- [ ] 超时后显示友好提示

---

### Phase 2: 后端AI调用日志

**目标**：记录每次AI调用的完整信息

**数据模型**：
```yaml
AICallLog:
  id: string
  project_id: string
  stage: string
  timestamp: datetime
  
  # 输入
  system_prompt: string
  user_message: string
  full_prompt: string  # 渲染后的完整prompt
  
  # 输出
  response: string
  tokens_used: int
  duration_ms: int
  
  # 元信息
  model: string
  temperature: float
  success: bool
  error: string | null
```

**文件清单**：
- `core/models/ai_call_log.py` - 日志模型
- `core/ai_client.py` - 修改，记录每次调用
- `api/routes/logs.py` - 日志查询API

**API设计**：
```
GET /api/logs/ai-calls?project_id=xxx
GET /api/logs/ai-calls/{log_id}
```

---

### Phase 3: 调试面板UI

**目标**：设置界面增加调试日志查看

**文件清单**：
- `web/src/components/settings/DebugSettings.tsx`
- 更新 `SettingsDialog.tsx` 添加调试tab

**功能**：
- 按项目筛选日志
- 显示每次调用的prompt/response
- 展开查看完整prompt
- 显示token使用和耗时

**UI设计**：
```
┌─────────────────────────────────────────────────────────────┐
│ 调试日志                              [项目筛选: ▼] [刷新]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 意图分析 | 2026-02-01 20:30:15 | 3.2s | 1,234 tokens   ││
│ │ ├ System Prompt: 你是一个专业的内容策划师...          ││
│ │ ├ User Message: 我想做一个团队管理课程                ││
│ │ └ Response: { goal: "...", success_criteria: [...] }  ││
│ │                                        [查看完整▼]    ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 消费者调研 | 2026-02-01 20:31:20 | 8.5s | 2,456 tokens ││
│ │ ...                                                     ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、实施步骤

1. **Phase 1** (fix-1): 增加超时时间 + 加载状态优化
2. **Phase 2** (debug-2): 后端AI调用日志记录
3. **Phase 3** (debug-1): 前端调试面板

---

## 四、测试计划

### Phase 1 测试
- 意图分析完成后能正常进入下一阶段
- 超时时显示友好错误提示
- 加载动画正确显示

### Phase 2 测试
- AI调用后日志正确保存
- 日志包含完整prompt和response
- 日志API返回正确数据

### Phase 3 测试
- 调试面板显示日志列表
- 点击展开显示完整内容
- 项目筛选正常工作




