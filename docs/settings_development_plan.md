# 后台设置界面开发计划

## 一、设计回顾（来自 ui_design.md）

### 设置界面结构
```
┌─────────────────────────────────────────────────────────────────────┐
│  设置                                                    [×]        │
├────────────────┬────────────────────────────────────────────────────┤
│  ┌──────────┐  │                                                    │
│  │ 项目设置  │  │                                                    │
│  ├──────────┤  │          （右侧显示选中分类的详细设置）              │
│  │ 创作者   │  │                                                    │
│  │ 特质     │  │                                                    │
│  ├──────────┤  │                                                    │
│  │ 字段模板  │  │                                                    │
│  ├──────────┤  │                                                    │
│  │ 系统提示词│  │                                                    │
│  ├──────────┤  │                                                    │
│  │ 评估器   │  │                                                    │
│  ├──────────┤  │                                                    │
│  │ 渠道管理  │  │                                                    │
│  ├──────────┤  │                                                    │
│  │ 数据管理  │  │                                                    │
│  └──────────┘  │                                                    │
└────────────────┴────────────────────────────────────────────────────┘
```

### 七个模块
1. **项目设置** - 当前项目的名称、描述、关联配置
2. **创作者特质** - 禁忌词、范例文本、自定义字段
3. **字段模板** - 内涵生产的字段定义
4. **系统提示词** - 各阶段的AI提示词模板
5. **评估器配置** - Simulator的评估规则
6. **渠道管理** - 外延生产的渠道配置
7. **数据管理** - 导出/导入/清理

---

## 二、开发阶段

### Phase 1: 设置弹窗框架

**目标**：实现设置入口、弹窗容器、左侧导航

**文件清单**：
- `web/src/components/settings/SettingsDialog.tsx` - 设置弹窗主容器
- `web/src/components/settings/SettingsNav.tsx` - 左侧导航
- `web/src/stores/uiStore.ts` - 添加settingsOpen状态

**Benchmark**：
- [ ] 点击设置按钮打开弹窗
- [ ] 左侧显示7个导航项
- [ ] 点击导航切换右侧内容
- [ ] 点击×或ESC关闭弹窗

---

### Phase 2: 创作者特质管理

**目标**：完整的Profile CRUD + 编辑界面

**文件清单**：
- `web/src/components/settings/ProfileSettings.tsx`
- `web/src/components/settings/ProfileEditor.tsx`

**功能**：
- 列表展示所有Profile
- 新建Profile
- 编辑禁忌词（forbidden_words, forbidden_topics）
- 编辑范例文本（example_texts）
- 编辑自定义字段（custom_fields）
- 删除Profile

**API对接**：
- GET /api/profiles
- POST /api/profiles
- PUT /api/profiles/{id}
- DELETE /api/profiles/{id}

**Benchmark**：
- [ ] 列表显示已有Profile
- [ ] 能新建Profile
- [ ] 能编辑所有字段
- [ ] 保存后数据持久化
- [ ] 删除确认弹窗

---

### Phase 3: 字段模板管理

**目标**：FieldSchema的CRUD + 字段编辑

**文件清单**：
- `web/src/components/settings/SchemaSettings.tsx`
- `web/src/components/settings/SchemaEditor.tsx`
- `web/src/components/settings/FieldEditor.tsx`

**功能**：
- 列表展示所有模板
- 新建模板
- 编辑模板描述
- 添加/编辑/删除字段
- 字段排序（上移/下移）
- 复制模板

**API需补充**：
- GET /api/schemas
- POST /api/schemas
- PUT /api/schemas/{id}
- DELETE /api/schemas/{id}

---

### Phase 4: 系统提示词管理

**目标**：查看和编辑各阶段的Prompt模板

**文件清单**：
- `web/src/components/settings/PromptSettings.tsx`
- `web/src/components/settings/PromptEditor.tsx`

**功能**：
- 分类展示（意图分析/消费者调研/内涵生产/外延生产/评估器）
- 查看Prompt模板
- 编辑Prompt内容
- 显示可用变量列表
- 重置为默认

**API已有**：
- GET /api/settings/prompts
- GET /api/settings/prompts/{name}
- PUT /api/settings/prompts/{name}

---

### Phase 5: 数据管理

**目标**：数据导出导入、清理

**文件清单**：
- `web/src/components/settings/DataSettings.tsx`

**功能**：
- 显示存储统计
- 导出当前项目（JSON/ZIP）
- 导入项目
- 清空数据（带确认）

**API需补充**：
- GET /api/projects/{id}/export
- POST /api/projects/import
- DELETE /api/projects/{id}/data

---

## 三、组件结构

```
web/src/components/settings/
├── SettingsDialog.tsx      # 主弹窗容器
├── SettingsNav.tsx         # 左侧导航
├── ProfileSettings.tsx     # 创作者特质
├── ProfileEditor.tsx       # Profile编辑器
├── SchemaSettings.tsx      # 字段模板
├── SchemaEditor.tsx        # Schema编辑器
├── FieldEditor.tsx         # 单个字段编辑器
├── PromptSettings.tsx      # 系统提示词
├── PromptEditor.tsx        # Prompt编辑器
├── SimulatorSettings.tsx   # 评估器配置
├── ChannelSettings.tsx     # 渠道管理
└── DataSettings.tsx        # 数据管理
```

---

## 四、API补充清单

### 现有API（已实现）
- ✅ /api/profiles - CRUD
- ✅ /api/projects - CRUD
- ✅ /api/settings/config - 系统配置
- ✅ /api/settings/prompts - Prompt模板

### 需要补充
- ⬜ /api/schemas - 字段模板CRUD
- ⬜ /api/simulators - 评估器配置CRUD
- ⬜ /api/channels - 渠道配置CRUD
- ⬜ /api/projects/{id}/export - 导出项目
- ⬜ /api/projects/import - 导入项目

---

## 五、测试计划

### 单元测试
```typescript
// 设置弹窗
- 打开/关闭状态
- 导航切换

// Profile编辑
- 表单验证
- 禁忌词添加/删除
- 范例文本编辑
- 自定义字段编辑

// 数据管理
- 导出格式正确
- 导入数据解析
```

### 集成测试
- 创建Profile → 在主界面可选
- 编辑Prompt → 下次生成使用新版
- 导出/导入 → 数据一致




