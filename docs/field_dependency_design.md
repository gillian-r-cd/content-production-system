# 字段依赖关系与拖拽排序设计文档
# 创建时间：2026-02-02
# 功能：设计字段之间的生成顺序、依赖关系和链式重新生成机制

---

## 一、需求分析

### 1.1 用户需求
1. **拖拽排序**：章节和字段支持拖拽调整顺序
2. **字段依赖关系**：设置字段之间的生成顺序和依赖关系
   - 在字段模板（FieldSchema）中可以设置默认依赖
   - 在场景目录中可以覆盖/自定义依赖（优先级更高）
3. **链式重新生成**：
   - 每个节点有"重新生成本节点"按钮
   - 每个链条开头有"重新生成本链条"按钮

### 1.2 核心概念
```
依赖链示例：
  [标题] ─────────────────────────────────────────────┐
     │                                                 │
     v                                                 │
  [大纲] ──────────────────────────────────────────┐   │
     │                                              │   │
     v                                              │   │
  [第1章内容] ── [第2章内容] ── [第3章内容]          │   │
                        │                           │   │
                        v                           │   │
                    [摘要] <────────────────────────┘───┘

链条识别：
- 链1: 标题 → 大纲
- 链2: 大纲 → 第1章内容 → 第2章内容 → 第3章内容
- 链3: 大纲 + 所有章节 → 摘要

链头节点：无依赖或只依赖前置阶段的节点
```

---

## 二、数据模型设计

### 2.1 FieldDefinition 扩展（字段模板级别）
```python
# core/models/field_schema.py - 已有，需确认

class FieldDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    type: Literal["text", "list", "freeform"] = "text"
    required: bool = True
    ai_hint: str = ""
    
    # 依赖关系（已存在）
    order: int = 0                    # 生成顺序
    depends_on: List[str] = []        # 依赖的字段名列表
    
    # 新增：依赖类型
    dependency_type: Literal["sequential", "aggregate"] = "sequential"
    # sequential: 顺序依赖，需要等待依赖字段完成后才能生成
    # aggregate: 聚合依赖，需要所有依赖字段的内容作为上下文
```

### 2.2 ContentField 扩展（场景目录级别）
```python
# core/models/content_core.py - 需扩展

class ContentField(BaseModel):
    # ... 现有字段 ...
    
    # 新增：场景级别的依赖配置（覆盖模板默认值）
    custom_depends_on: Optional[List[str]] = None    # 如果设置，覆盖模板的depends_on
    custom_dependency_type: Optional[str] = None      # 如果设置，覆盖模板的dependency_type
    
    # 新增：链式追踪
    chain_id: Optional[str] = None                    # 所属链条ID（运行时计算）
    is_chain_head: bool = False                       # 是否是链条头部
    
    # 新增：上下文过期标记（用于链式重新生成）
    context_stale: bool = False                       # 上下文是否过期
    
    def get_effective_depends_on(self, template_field: Optional[FieldDefinition] = None) -> List[str]:
        """获取有效的依赖列表（场景级别覆盖模板级别）"""
        if self.custom_depends_on is not None:
            return self.custom_depends_on
        if template_field:
            return template_field.depends_on
        return []
```

### 2.3 依赖链数据结构
```python
# 新增：core/models/dependency_chain.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class DependencyNode:
    """依赖图中的节点"""
    field_id: str
    depends_on: List[str]     # 依赖的节点ID列表
    dependents: List[str]     # 依赖于此节点的节点ID列表

class DependencyChain:
    """一条完整的依赖链"""
    id: str
    head_field_id: str        # 链头字段ID
    field_ids: List[str]      # 链中所有字段ID（按依赖顺序）
    
class DependencyGraph:
    """完整的依赖图"""
    nodes: Dict[str, DependencyNode]
    chains: List[DependencyChain]
    
    @classmethod
    def build_from_content_core(cls, content_core: "ContentCore") -> "DependencyGraph":
        """从ContentCore构建依赖图"""
        pass
    
    def get_chain_for_field(self, field_id: str) -> Optional[DependencyChain]:
        """获取字段所属的链条"""
        pass
    
    def get_downstream_fields(self, field_id: str) -> List[str]:
        """获取字段的所有下游字段（用于标记过期）"""
        pass
```

---

## 三、API 设计

### 3.1 拖拽排序 API
```yaml
# 更新章节顺序
PATCH /workflow/{workflow_id}/sections/reorder
Request:
  section_ids: List[str]  # 新的章节顺序

# 更新字段顺序
PATCH /workflow/{workflow_id}/sections/{section_id}/fields/reorder
Request:
  field_ids: List[str]    # 新的字段顺序
```

### 3.2 依赖关系配置 API
```yaml
# 更新字段依赖（场景目录级别）
PATCH /workflow/{workflow_id}/fields/{field_id}/dependencies
Request:
  depends_on: List[str]           # 依赖的字段ID列表
  dependency_type: str            # "sequential" | "aggregate"

# 获取依赖图
GET /workflow/{workflow_id}/dependency-graph
Response:
  nodes: Dict[str, DependencyNode]
  chains: List[DependencyChain]
```

### 3.3 重新生成 API
```yaml
# 重新生成单个节点
POST /workflow/{workflow_id}/fields/{field_id}/regenerate
Response:
  success: bool
  regenerated_field: ContentField
  downstream_stale_count: int  # 被标记为过期的下游字段数

# 重新生成链条
POST /workflow/{workflow_id}/chains/{chain_id}/regenerate
Response:
  success: bool
  regenerated_fields: List[ContentField]
```

---

## 四、前端组件设计

### 4.1 拖拽排序组件
```typescript
// 使用 @dnd-kit 库
// web/src/components/stages/OutlineEditor.tsx

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
```

### 4.2 依赖关系配置组件
```typescript
// web/src/components/settings/DependencyEditor.tsx
// 可视化依赖关系编辑器

interface DependencyEditorProps {
  fields: ContentField[]
  onDependencyChange: (fieldId: string, dependsOn: string[]) => void
}

// 显示方式：
// 1. 每个字段旁边有一个"设置依赖"图标
// 2. 点击后显示下拉多选，可选择依赖的字段
// 3. 可视化显示依赖连线（可选）
```

### 4.3 重新生成按钮组件
```typescript
// 在 OutlineEditor 中每个字段和链头添加重新生成按钮

// 单字段重新生成按钮
<RegenerateButton 
  type="field" 
  fieldId={field.id}
  onRegenerate={handleRegenerateField}
/>

// 链条重新生成按钮（仅在链头显示）
{field.is_chain_head && (
  <RegenerateButton 
    type="chain" 
    chainId={field.chain_id}
    onRegenerate={handleRegenerateChain}
  />
)}
```

---

## 五、测试计划

### 5.1 单元测试

```python
# tests/test_drag_reorder.py
# 测试拖拽排序功能

def test_section_reorder():
    """测试章节拖拽排序"""
    # Benchmark: 章节顺序按新顺序更新
    pass

def test_field_reorder_within_section():
    """测试章节内字段拖拽排序"""
    # Benchmark: 字段order正确更新
    pass
```

```python
# tests/test_dependency_system.py
# 测试依赖关系系统

def test_dependency_graph_build():
    """测试依赖图构建"""
    # Benchmark: 依赖图正确反映字段关系
    pass

def test_chain_identification():
    """测试链条识别"""
    # Benchmark: 链头和链条成员正确识别
    pass

def test_downstream_marking():
    """测试下游字段标记"""
    # Benchmark: 修改字段后下游字段正确标记为过期
    pass
```

```python
# tests/test_regeneration.py
# 测试重新生成功能

def test_single_field_regenerate():
    """测试单字段重新生成"""
    # Benchmark: 字段内容更新，下游标记过期
    pass

def test_chain_regenerate():
    """测试链条重新生成"""
    # Benchmark: 链中所有字段按顺序重新生成
    pass
```

### 5.2 集成测试

```python
# tests/test_dependency_integration.py
# 端到端集成测试

def test_full_workflow_with_dependencies():
    """测试完整工作流：配置依赖 → 生成 → 修改 → 重新生成"""
    # 1. 创建项目
    # 2. 配置字段依赖
    # 3. 生成内容（验证顺序）
    # 4. 修改某字段
    # 5. 验证下游标记过期
    # 6. 重新生成链条
    # 7. 验证所有内容更新
    pass
```

### 5.3 前端测试

```typescript
// web/src/__tests__/OutlineEditor.test.tsx
// 使用 @testing-library/react

describe('OutlineEditor', () => {
  it('should reorder sections on drag', async () => {
    // Benchmark: 拖拽后sections顺序更新
  })
  
  it('should show regenerate button for each field', () => {
    // Benchmark: 每个字段有重新生成按钮
  })
  
  it('should show chain regenerate button for chain heads', () => {
    // Benchmark: 链头有链条重新生成按钮
  })
})
```

---

## 六、实施步骤

### Phase 1: 修复拖拽排序（优先级最高）
1. 安装 @dnd-kit 依赖
2. 重构 OutlineEditor，实现章节拖拽
3. 实现章节内字段拖拽
4. 添加后端排序 API
5. 测试验证

### Phase 2: 扩展数据模型
1. 扩展 ContentField 模型
2. 创建 DependencyGraph 模块
3. 更新 API 响应包含依赖信息
4. 单元测试

### Phase 3: 实现依赖配置UI（模板级别）
1. 在 SchemaSettings 中添加依赖配置
2. 可视化依赖关系
3. 测试验证

### Phase 4: 实现依赖配置UI（场景目录级别）
1. 在 OutlineEditor 中添加依赖配置
2. 实现覆盖模板默认值的逻辑
3. 测试验证

### Phase 5: 实现重新生成功能
1. 添加重新生成 API
2. 前端按钮和交互
3. 链条重新生成逻辑
4. 端到端测试

---

## 七、Benchmark 定义

| 功能 | Benchmark | 验收标准 |
|------|-----------|----------|
| 章节拖拽 | 拖拽后章节顺序正确更新 | API 返回的 sections 顺序与拖拽结果一致 |
| 字段拖拽 | 拖拽后字段order正确更新 | API 返回的字段 order 与拖拽结果一致 |
| 依赖配置 | 可以设置字段依赖关系 | depends_on 正确保存和读取 |
| 场景覆盖 | 场景级别依赖覆盖模板 | custom_depends_on 优先于 depends_on |
| 链条识别 | 正确识别依赖链和链头 | DependencyGraph.chains 正确 |
| 单节点重生成 | 重新生成单个字段 | 字段内容更新，API调用成功 |
| 链条重生成 | 按顺序重新生成链中所有字段 | 所有字段按依赖顺序更新 |
| 过期标记 | 修改后下游字段标记过期 | context_stale = True |

---

## 八、风险与注意事项

1. **循环依赖检测**：需要在设置依赖时检测并禁止循环依赖
2. **性能考虑**：大量字段时依赖图计算可能较慢，考虑缓存
3. **向后兼容**：现有项目没有依赖配置，需要优雅降级
4. **并发控制**：多个字段同时重新生成时的顺序控制
