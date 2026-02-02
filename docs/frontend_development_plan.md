# 前端开发计划

## 一、技术栈

```yaml
框架: React 18 + TypeScript
构建: Vite 5
样式: TailwindCSS 3.4
UI组件: Shadcn/ui (非依赖，直接复制到项目)
状态管理: Zustand
API调用: TanStack Query (React Query)
路由: React Router 6
图标: Lucide React
```

## 二、目录结构

```
/web/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── /src/
│   ├── main.tsx                    # 入口
│   ├── App.tsx                     # 根组件
│   ├── index.css                   # 全局样式
│   │
│   ├── /components/                # UI组件
│   │   ├── /ui/                    # Shadcn基础组件
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   ├── /layout/                # 布局组件
│   │   │   ├── MainLayout.tsx      # 三栏主布局
│   │   │   ├── ProgressPanel.tsx   # 左侧进度栏
│   │   │   ├── EditorPanel.tsx     # 中间编辑区
│   │   │   └── ChatPanel.tsx       # 右侧对话区
│   │   ├── /stages/                # 各阶段组件
│   │   │   ├── IntentStage.tsx     # 意图分析
│   │   │   ├── ResearchStage.tsx   # 消费者调研
│   │   │   ├── CoreDesignStage.tsx # 内涵设计
│   │   │   ├── CoreProductionStage.tsx # 内涵生产
│   │   │   └── ExtensionStage.tsx  # 外延生产
│   │   ├── /chat/                  # 对话相关
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── ContextReference.tsx # @引用
│   │   └── /settings/              # 设置相关
│   │       ├── ProfileSettings.tsx
│   │       ├── SchemaSettings.tsx
│   │       └── PromptSettings.tsx
│   │
│   ├── /stores/                    # Zustand状态
│   │   ├── workflowStore.ts        # 工作流状态
│   │   ├── uiStore.ts              # UI状态
│   │   └── settingsStore.ts        # 设置状态
│   │
│   ├── /api/                       # API调用
│   │   ├── client.ts               # axios实例
│   │   ├── profiles.ts             # Profile API
│   │   ├── projects.ts             # Project API
│   │   ├── workflow.ts             # Workflow API
│   │   └── settings.ts             # Settings API
│   │
│   ├── /hooks/                     # 自定义Hooks
│   │   ├── useWorkflow.ts
│   │   └── useChat.ts
│   │
│   ├── /types/                     # TypeScript类型
│   │   └── index.ts
│   │
│   └── /lib/                       # 工具函数
│       └── utils.ts
└── /public/
```

## 三、开发阶段与Benchmark

### Phase 2.1: 项目初始化

**目标**：Vite + React + TypeScript + TailwindCSS 基础环境

**任务清单**：
1. 创建Vite项目
2. 配置TailwindCSS
3. 配置路径别名
4. 安装基础依赖
5. 创建目录结构

**Benchmark测试**：
- [ ] `npm run dev` 能启动
- [ ] 访问 localhost:5173 显示页面
- [ ] TailwindCSS 样式生效
- [ ] TypeScript编译无错误

### Phase 2.2: Shadcn/ui 基础组件

**目标**：安装必要的UI基础组件

**任务清单**：
1. 配置Shadcn/ui
2. 添加Button组件
3. 添加Input组件
4. 添加Card组件
5. 添加Dialog组件
6. 添加Tabs组件
7. 添加ScrollArea组件

**Benchmark测试**：
- [ ] 所有组件正确渲染
- [ ] 样式一致性

### Phase 2.3: API层

**目标**：与后端API对接

**任务清单**：
1. 创建axios客户端（配置baseURL）
2. 实现Profile API
3. 实现Project API
4. 实现Workflow API
5. 实现Settings API

**Benchmark测试**：
- [ ] API调用返回正确数据
- [ ] 错误处理正确
- [ ] 类型定义完整

### Phase 3.1: 三栏主布局

**目标**：实现核心三栏布局

**任务清单**：
1. MainLayout组件（响应式三栏）
2. 可折叠侧边栏
3. 顶部导航栏
4. 状态栏

**Benchmark测试**：
- [ ] 三栏正确显示
- [ ] 响应式适配（1200px/900px断点）
- [ ] 折叠功能正常

**UI规范**（来自ui_design.md）：
```yaml
左侧进度栏:
  默认宽度: 200px
  最小宽度: 150px
  可折叠: 是

中间编辑区:
  宽度: 自适应

右侧对话区:
  默认宽度: 350px
  最小宽度: 280px
  可折叠: 是
```

### Phase 3.2: 左侧进度栏

**目标**：阶段列表与状态显示

**任务清单**：
1. ProgressPanel组件
2. 阶段状态图标（○ → ✓ ! ↻）
3. 点击切换阶段
4. 悬浮预览

**状态类型**：
```yaml
pending: ○ 灰色
in_progress: → 蓝色
completed: ✓ 绿色
blocked: ! 红色
iterating: ↻ 橙色
```

**Benchmark测试**：
- [ ] 阶段正确显示
- [ ] 点击切换工作
- [ ] 状态图标正确

### Phase 3.3: 右侧对话区

**目标**：AI对话交互

**任务清单**：
1. ChatPanel组件
2. ChatMessage组件
3. ChatInput组件
4. 追问进度显示（问题 2/3）
5. 快捷回复按钮

**Benchmark测试**：
- [ ] 消息正确渲染
- [ ] 输入发送正常
- [ ] 追问进度显示

### Phase 4: 意图分析流程

**目标**：完整的意图分析交互

**任务清单**：
1. 工作流Store（Zustand）
2. IntentStage组件
3. 与Workflow API对接
4. 追问交互流程
5. 结果展示与编辑

**Benchmark测试**：
- [ ] 开始工作流成功
- [ ] 追问交互正常
- [ ] 追问不超过3次
- [ ] 结果正确显示

### Phase 5: 完整工作流

**目标**：全流程串联

**任务清单**：
1. ResearchStage组件
2. CoreDesignStage组件（方案选择）
3. CoreProductionStage组件（字段生产）
4. ExtensionStage组件
5. 阶段切换动画

**Benchmark测试**：
- [ ] 完整流程可运行
- [ ] 数据正确传递
- [ ] 状态正确保存

### Phase 6: 后台设置

**目标**：配置管理界面

**任务清单**：
1. 设置入口（顶部导航）
2. ProfileSettings组件
3. SchemaSettings组件
4. PromptSettings组件

**Benchmark测试**：
- [ ] 设置保存成功
- [ ] 设置立即生效

### Phase 7: 本地持久化

**目标**：IndexedDB存储

**任务清单**：
1. 自动保存机制
2. 版本历史
3. 导入导出

---

## 四、前后端一致性保证

### 4.1 类型同步

后端Pydantic模型 → OpenAPI Schema → TypeScript类型

```typescript
// src/types/index.ts
// 从后端API响应推导类型

export interface Profile {
  id: string;
  name: string;
  taboos: {
    forbidden_words: string[];
    forbidden_topics: string[];
  };
  example_texts: string[];
  custom_fields: Record<string, string>;
}

export interface WorkflowStatus {
  workflow_id: string;
  project_id: string;
  current_stage: string;
  waiting_for_input: boolean;
  input_prompt: string | null;
  clarification_progress: string | null; // "2/3"
  ai_call_count: number;
  stages: Record<string, string>;
}
```

### 4.2 状态同步

```
用户操作 → Zustand Store → API调用 → 后端处理 → 响应 → 更新Store → UI更新
```

### 4.3 UI与设计文档一致

严格按照 `docs/ui_design.md` 实现：
- 三栏布局
- 阶段状态图标
- 对话区@引用
- 后台设置界面

---

## 五、配色方案

```css
/* 来自 ui_design.md */
:root {
  --primary: #1a73e8;
  --success: #34a853;
  --warning: #fbbc05;
  --error: #ea4335;
  --neutral: #5f6368;
  
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-tertiary: #e8eaed;
  
  --text-primary: #202124;
  --text-secondary: #5f6368;
  --text-disabled: #9aa0a6;
}
```

---

## 六、开发命令

```bash
# 前端开发
cd web
npm install
npm run dev          # 启动开发服务器 (localhost:5173)

# 后端API（需要同时运行）
cd ..
python -m uvicorn api.main:app --reload --port 8000
```

---

## 七、测试策略

### 单元测试

```bash
npm run test         # Vitest
```

### E2E测试

```bash
npm run test:e2e     # Playwright
```

### 测试覆盖场景

1. **Profile管理**：创建、编辑、删除
2. **工作流**：开始→追问→完成
3. **阶段切换**：正向/回退
4. **设置**：保存生效




