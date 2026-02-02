# 后台设置模块完整开发计划

## 一、模块清单与状态

| 模块 | 状态 | 优先级 | 依赖 |
|------|------|--------|------|
| 创作者特质 | ✅ 完成 | P0 | - |
| 系统提示词 | ✅ 完成 | P0 | - |
| 数据管理 | ✅ 完成 | P1 | - |
| 调试日志 | ✅ 完成 | P1 | - |
| 项目设置 | 🔲 待开发 | P0 | - |
| 字段模板 | 🔲 待开发 | P0 | API |
| 评估器配置 | 🔲 待开发 | P1 | API |
| 渠道管理 | 🔲 待开发 | P1 | API |

---

## 二、Phase 1: 项目设置

### 功能需求
- 显示/编辑当前项目名称、描述
- 选择关联的创作者特质
- 选择使用的字段模板
- 查看项目创建/更新时间

### 文件清单
- `web/src/components/settings/ProjectSettings.tsx`

### Benchmark
- [ ] 显示当前项目信息
- [ ] 能修改项目名称和描述
- [ ] 能切换关联的Profile
- [ ] 保存后数据持久化

---

## 三、Phase 2: 字段模板管理

### 功能需求（来自ui_design.md）
- 模板列表展示（名称、描述、字段数量）
- 新建模板
- 编辑模板基本信息
- 添加/编辑/删除字段
- 字段属性：名称、描述、类型、是否必填、AI提示
- 字段排序（上移/下移）
- 复制模板

### 数据模型
```typescript
interface FieldSchema {
  id: string
  name: string
  description: string
  fields: Field[]
}

interface Field {
  name: string
  description: string
  type: 'text' | 'list' | 'structured'
  required: boolean
  ai_hint: string
}
```

### API需求
```
GET    /api/schemas           - 列表
POST   /api/schemas           - 创建
GET    /api/schemas/{id}      - 获取单个
PUT    /api/schemas/{id}      - 更新
DELETE /api/schemas/{id}      - 删除
```

### 文件清单
- `api/routes/schemas.py` - 后端API
- `web/src/api/schemas.ts` - 前端API调用
- `web/src/components/settings/SchemaSettings.tsx` - 主页面
- `web/src/components/settings/SchemaEditor.tsx` - 模板编辑器
- `web/src/components/settings/FieldEditor.tsx` - 字段编辑器

### Benchmark
- [ ] 列表显示所有模板
- [ ] 能创建新模板
- [ ] 能添加/编辑/删除字段
- [ ] 能调整字段顺序
- [ ] 能复制模板
- [ ] 保存后数据持久化

---

## 四、Phase 3: 评估器配置

### 功能需求
- 评估器列表
- 新建评估器
- 编辑评估提示词
- 配置自动迭代条件（触发分数、停止分数、最大迭代次数）

### 数据模型
```typescript
interface SimulatorConfig {
  id: string
  name: string
  description: string
  prompt_template: string
  auto_iterate: boolean
  trigger_score: number  // 低于此分数触发迭代
  stop_score: number     // 高于此分数停止
  max_iterations: number
}
```

### API需求
```
GET    /api/simulators           - 列表
POST   /api/simulators           - 创建
PUT    /api/simulators/{id}      - 更新
DELETE /api/simulators/{id}      - 删除
```

### 文件清单
- `api/routes/simulators.py`
- `web/src/components/settings/SimulatorSettings.tsx`

### Benchmark
- [ ] 列表显示所有评估器
- [ ] 能创建/编辑/删除评估器
- [ ] 能配置迭代条件
- [ ] 保存后数据持久化

---

## 五、Phase 4: 渠道管理

### 功能需求
- 渠道列表（小红书、公众号、邮件等）
- 新建渠道
- 编辑渠道配置（描述、格式约束、生成提示词）

### 数据模型
```typescript
interface Channel {
  id: string
  name: string
  description: string
  format_constraints: {
    title_max_length?: number
    body_word_range?: [number, number]
    special_requirements?: string
  }
  prompt_template: string
}
```

### API需求
```
GET    /api/channels           - 列表
POST   /api/channels           - 创建
PUT    /api/channels/{id}      - 更新
DELETE /api/channels/{id}      - 删除
```

### 文件清单
- `api/routes/channels.py`
- `web/src/components/settings/ChannelSettings.tsx`

### Benchmark
- [ ] 列表显示所有渠道
- [ ] 能创建/编辑/删除渠道
- [ ] 能配置格式约束
- [ ] 保存后数据持久化

---

## 六、测试策略

### 单元测试
- 每个设置组件的表单验证
- CRUD操作正确性

### 集成测试
- 创建模板 → 项目可选用
- 创建渠道 → 外延生产可选用
- 修改评估器 → 评估时使用新配置

### E2E测试
- 完整设置流程：创建Profile → 创建模板 → 创建评估器 → 创建渠道
- 工作流使用自定义配置

---

## 七、实施顺序

1. **Phase 1**: 项目设置（简单，无需新API）
2. **Phase 2**: 字段模板（核心功能，需要API）
3. **Phase 3**: 评估器配置（依赖字段模板）
4. **Phase 4**: 渠道管理（依赖评估器）

预计总工作量：4个Phase，每个Phase约30分钟




