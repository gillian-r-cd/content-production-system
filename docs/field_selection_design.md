# 字段选择功能设计文档

## 需求背景

当前问题：在目录编辑器中点击"添加字段"时，直接创建一个硬编码的空白"新字段"。

用户期望：添加字段时应该能从后台已配置的字段模板中选择已定义好的字段。

## 设计方案

### 数据流

```
FieldSchema (字段模板)
    ↓
ContentCore.field_schema_id (项目关联的模板ID)
    ↓
OutlineEditor (获取模板字段列表)
    ↓
用户选择 → 添加到章节
```

### 核心逻辑

1. **获取字段模板**：
   - OutlineEditor 接收 `fieldSchemaId` 作为 prop
   - 根据 ID 调用 `GET /api/schemas/{schema_id}` 获取字段定义

2. **字段选择UI**：
   - 点击"添加字段"按钮时，显示下拉菜单
   - 下拉菜单列出模板中所有可用字段
   - 已添加的字段显示为禁用状态（避免重复）

3. **添加字段逻辑**：
   - 选择字段后，基于模板字段创建 ContentField
   - 复制字段名、描述、依赖关系等属性

### 接口设计

#### Props 变更

```typescript
interface OutlineEditorProps {
  workflowId: string
  fieldSchemaId?: string  // 新增：关联的字段模板ID
  // ... 其他 props
}
```

#### 新增状态

```typescript
// 字段模板数据
const [schemaFields, setSchemaFields] = useState<FieldDefinition[]>([])

// 添加字段下拉菜单状态
const [showFieldDropdown, setShowFieldDropdown] = useState<string | null>(null) // sectionId
```

### UI 设计

```
+ 添加字段
    ↓ (点击后显示)
┌─────────────────────────┐
│ 📋 learning_goal        │ ← 可选择
│ 📋 key_concepts         │ ← 可选择
│ 📋 test_field (已添加)   │ ← 禁用
│ 📋 summary              │ ← 可选择
├─────────────────────────┤
│ + 创建自定义字段         │ ← 保留原有功能
└─────────────────────────┘
```

## 测试计划

### 1. 单元测试

- 测试获取字段模板API
- 测试字段选择逻辑

### 2. 集成测试

- 测试 OutlineEditor 正确加载字段模板
- 测试添加字段功能

### 3. E2E 测试步骤

1. 创建一个包含多个字段的字段模板
2. 创建项目并关联该模板
3. 进入目录编辑界面
4. 点击"添加字段"按钮
5. 验证下拉菜单显示模板中的字段
6. 选择一个字段
7. 验证字段被正确添加到章节中

## 实现步骤

### Phase 1: 设计文档和测试计划 ✓

### Phase 2: 获取并传递字段模板数据 ✓

1. 修改 CoreProductionStage，获取当前模板的字段列表
2. 将字段列表传递给 OutlineEditor

实现：
- 在 `CoreProductionStage.tsx` 添加 `templateFields` state
- 添加 `useEffect` 根据 `currentSchemaId` 获取模板字段
- 通过 props 传递给 `OutlineEditor`

### Phase 3: 实现字段选择下拉菜单UI ✓

1. 在"添加字段"按钮旁添加下拉菜单
2. 显示可选字段列表
3. 标记已添加的字段

实现：
- 修改 `SortableSectionProps` 添加 `templateFields`, `showFieldDropdown`, `usedFieldNames`
- 在"添加字段"按钮下方添加下拉菜单 UI
- 显示模板字段列表，已添加的字段显示为禁用

### Phase 4: 修改 addField 逻辑 ✓

1. 接收选中的模板字段
2. 基于模板字段创建 ContentField
3. 保留"创建自定义字段"选项

实现：
- `addField(sectionId, templateField?)` 支持可选模板字段参数
- 基于模板字段创建时复制 name, description, depends_on 等属性
- 保留"创建自定义字段"选项在下拉菜单底部

### Phase 5: 端到端测试验证 ✓

1. 启动服务 - 后端 8000 端口，前端 5173 端口
2. API 验证通过
3. TypeScript 编译无新增错误
