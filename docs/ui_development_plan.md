# Web UI 开发计划

## 一、问题诊断与修复

### 1.1 当前CLI问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 追问无限循环 | 没有追问次数上限 | 添加 `max_clarifications` 配置，默认3次 |
| 追问没有进度 | 没有追踪问题编号 | 显示 "问题 (2/3)" 格式 |
| "内容生产"提示误导 | 文案问题 | 改为"意图分析" |
| 无法预览整体数据 | CLI天然局限 | 开发Web UI |

### 1.2 需要先修复的后端问题

1. **追问次数限制**：在 `OrchestratorConfig` 添加 `max_clarifications = 3`
2. **追问进度**：在 `ProjectState` 添加 `clarification_count`
3. **强制结束追问**：达到上限后强制生成结果

---

## 二、技术栈选型

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Frontend (React)                      │
│  - React 18 + TypeScript                                    │
│  - TailwindCSS + Shadcn/ui                                  │
│  - Zustand (状态管理)                                        │
│  - React Query (API调用)                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────┴──────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  - FastAPI (Python)                                         │
│  - SSE (Server-Sent Events，用于流式输出)                    │
│  - 复用现有 core/ 模块                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    Core Modules (已有)                       │
│  - Orchestrator, IntentAnalyzer, ConsumerResearcher...      │
│  - AIClient, PromptEngine, ContextManager                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术选择理由

| 层级 | 技术 | 理由 |
|------|------|------|
| 前端框架 | React 18 | 生态成熟，组件丰富 |
| 类型 | TypeScript | 类型安全，减少bug |
| 样式 | TailwindCSS | 快速开发，一致性好 |
| UI组件 | Shadcn/ui | 高质量、可定制、非黑盒 |
| 状态管理 | Zustand | 轻量、简单、够用 |
| API | FastAPI | 与现有Python代码无缝集成 |
| 实时通信 | SSE | 比WebSocket简单，适合单向流 |

---

## 三、目录结构

```
/content_production_system/
├── /core/                    # 已有：核心业务模块
├── /ui/
│   └── cli.py               # 已有：CLI入口
├── /api/                    # 新增：FastAPI后端
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── projects.py      # 项目API
│   │   ├── profiles.py      # 创作者API
│   │   ├── workflow.py      # 工作流API（核心）
│   │   └── settings.py      # 设置API
│   ├── schemas/             # Pydantic请求/响应模型
│   │   └── ...
│   └── services/            # 业务逻辑封装
│       └── ...
├── /web/                    # 新增：React前端
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── /src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── /components/     # UI组件
│   │   │   ├── /layout/     # 布局组件
│   │   │   ├── /stages/     # 各阶段组件
│   │   │   ├── /settings/   # 设置组件
│   │   │   └── /shared/     # 通用组件
│   │   ├── /stores/         # Zustand状态
│   │   ├── /api/            # API调用
│   │   ├── /hooks/          # 自定义hooks
│   │   └── /types/          # TypeScript类型
│   └── /public/
└── /tests/
    ├── test_api_*.py        # API测试
    └── /web/                # 前端测试
```

---

## 四、开发阶段与Benchmark

### Phase 0: 后端API层搭建

**目标**：FastAPI基础框架 + 核心接口

**实现内容**：
1. FastAPI项目结构
2. 复用core模块的Service封装
3. 基础CRUD接口（Projects, Profiles）
4. 健康检查接口

**Benchmark测试**：
```python
# tests/test_api_health.py
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_list_profiles():
    response = client.get("/api/profiles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_project():
    response = client.post("/api/projects", json={"name": "test"})
    assert response.status_code == 201
```

---

### Phase 1: 工作流API

**目标**：完整的意图分析→内涵生产API流程

**实现内容**：
1. `/api/workflow/start` - 开始工作流
2. `/api/workflow/{id}/respond` - 回复追问
3. `/api/workflow/{id}/status` - 获取状态
4. `/api/workflow/{id}/stream` - SSE流式输出

**关键修复**：
- 追问次数限制（max 3次）
- 追问进度显示（1/3, 2/3, 3/3）
- 强制结束追问机制

**Benchmark测试**：
```python
def test_workflow_start():
    response = client.post("/api/workflow/start", json={
        "profile_id": "xxx",
        "raw_input": "我要做一个课程"
    })
    assert response.status_code == 200
    assert "workflow_id" in response.json()

def test_workflow_clarification_limit():
    # 测试追问不会超过3次
    ...

def test_workflow_stream():
    # 测试SSE流
    ...
```

---

### Phase 2: React前端基础

**目标**：三栏布局框架

**实现内容**：
1. Vite + React + TypeScript 项目
2. TailwindCSS + Shadcn/ui 配置
3. 三栏响应式布局
4. 路由配置

**Benchmark**：
- 页面加载 < 2s
- 首屏渲染完整
- 响应式适配（1200px/900px/600px断点）

---

### Phase 3: 左侧进度栏

**目标**：阶段列表与状态显示

**实现内容**：
1. 阶段列表组件
2. 阶段状态图标（○ → ✓ ! ↻）
3. 点击跳转
4. 悬浮预览

**UI要求**（参考 ui_design.md）：
```
┌──────────┐
│ ✓ 意图    │
│ → 调研    │ ← 当前
│ ○ 内涵    │
│ ○ 外延    │
│ ○ 报告    │
└──────────┘
```

---

### Phase 4: 右侧对话区

**目标**：AI对话交互

**实现内容**：
1. 对话消息列表
2. 输入框
3. 追问进度显示（问题 2/3）
4. @引用上下文（后续）
5. SSE流式显示

**关键交互**：
- 追问时显示"问题 (2/3)"
- 追问满3次自动进入下一阶段
- 快捷回复按钮

---

### Phase 5: 中间编辑区

**目标**：各阶段内容展示与编辑

**实现内容**：
1. 意图分析阶段视图
2. 消费者调研阶段视图
3. 内涵设计阶段（方案选择卡片）
4. 内涵生产阶段（字段列表 + 编辑）
5. 外延生产阶段
6. 内容Markdown渲染与编辑

---

### Phase 6: 后台设置界面

**目标**：完整设置管理

**实现内容**：
1. 创作者特质管理
2. 字段模板管理
3. 系统提示词编辑
4. 评估器配置
5. 渠道管理
6. 数据导入导出

---

### Phase 7: 数据持久化

**目标**：本地数据存储

**实现内容**：
1. IndexedDB存储（前端）
2. 自动保存机制
3. 版本历史
4. 导入导出ZIP

---

## 五、前后端一致性保证

### 5.1 类型同步

```yaml
策略: 
  - 后端Pydantic模型生成OpenAPI Schema
  - 前端使用openapi-typescript生成TypeScript类型
  - CI中自动检查类型一致性
```

### 5.2 API契约

```yaml
RESTful规范:
  - GET /api/projects - 列表
  - POST /api/projects - 创建
  - GET /api/projects/{id} - 详情
  - PUT /api/projects/{id} - 更新
  - DELETE /api/projects/{id} - 删除

工作流API:
  - POST /api/workflow/start - 开始
  - POST /api/workflow/{id}/respond - 响应
  - GET /api/workflow/{id}/stream - SSE流
```

### 5.3 状态同步

```yaml
方案:
  - 前端Zustand管理UI状态
  - 关键数据通过API同步到后端
  - SSE推送状态变更到前端
```

---

## 六、测试策略

### 6.1 后端测试

```
tests/
├── test_api_health.py          # 健康检查
├── test_api_profiles.py        # Profile CRUD
├── test_api_projects.py        # Project CRUD
├── test_api_workflow.py        # 工作流核心
├── test_api_workflow_sse.py    # SSE流测试
└── test_api_settings.py        # 设置API
```

### 6.2 前端测试

```
web/src/__tests__/
├── components/
│   ├── ProgressBar.test.tsx
│   ├── ChatWindow.test.tsx
│   └── EditorArea.test.tsx
├── stores/
│   └── workflowStore.test.ts
└── integration/
    └── workflow.test.tsx
```

### 6.3 E2E测试

```yaml
工具: Playwright
场景:
  - 创建Profile → 创建Project → 完整工作流
  - 设置修改 → 验证生效
  - 数据导入导出
```

---

## 七、开发顺序

```
Week 1: Phase 0 + Phase 1 (后端API)
  - 搭建FastAPI
  - 实现工作流API
  - 修复追问限制问题
  
Week 2: Phase 2 + Phase 3 (前端基础)
  - React项目搭建
  - 三栏布局
  - 左侧进度栏

Week 3: Phase 4 + Phase 5 (核心交互)
  - 右侧对话区
  - 中间编辑区
  - 工作流完整串联

Week 4: Phase 6 + Phase 7 (设置与存储)
  - 后台设置
  - 数据持久化
  - 完善与测试
```

---

## 八、启动命令

### 开发模式

```bash
# 终端1：后端
cd api
uvicorn main:app --reload --port 8000

# 终端2：前端
cd web
npm run dev
```

### 生产模式

```bash
# 构建前端
cd web && npm run build

# 启动后端（静态文件托管）
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## 九、待确认事项

1. **是否需要用户登录**？（目前假设单机使用）
2. **是否需要多项目同时打开**？（目前假设单项目）
3. **Deep Research具体需要什么能力**？（联网搜索？多轮深度调研？）




