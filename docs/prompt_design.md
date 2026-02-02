# 各阶段提示词设计规范

## 概述

系统分为5个阶段，每个阶段有明确的输入输出和提示词需求：

```
Intent → Research → Core Design → Core Production → Extension
  ↓         ↓            ↓               ↓              ↓
意图分析  消费者调研   内涵设计      内涵生产       外延生产
```

---

## 1. Intent（意图分析）

### 目的
分析用户想要生产什么内容，提炼核心目标和约束。

### 输入
- 用户的原始描述（raw_input）
- CreatorProfile（创作者特质）

### 输出
- Intent 对象：goal, must_have, must_avoid, style_preference 等

### 提示词内容
- CreatorProfile 约束（禁忌词、风格范例）
- 用户的原始输入

### 不需要
- FieldSchema（字段模板）
- ConsumerResearch（目标用户）

---

## 2. Research（消费者调研）

### 目的
了解目标用户的画像、痛点和期望。

### 输入
- Intent（项目意图）
- CreatorProfile（创作者特质）

### 输出
- ConsumerResearch 对象：persona_summary, pain_points, desires 等

### 提示词内容
- CreatorProfile 约束
- Intent（项目意图）

### 不需要
- FieldSchema（字段模板）

---

## 3. Core Design（内涵设计）⚠️ 关键

### 目的
生成多个差异化的**整体设计方案**，供用户选择方向。

### 输入
- Intent（项目意图）
- ConsumerResearch（目标用户）
- FieldSchema 的**概述信息**（名称、描述、字段名称列表）

### 输出
- 多个 DesignScheme：name, description, approach, key_features 等

### 提示词内容
- CreatorProfile 约束
- Intent（项目意图）
- ConsumerResearch（目标用户画像）
- **FieldSchema 概述**（仅包含：模板名称、描述、字段名称列表）

### 不需要 ❌
- **字段的 ai_hint**（这是生产阶段才需要的具体生成指令）
- **字段的 clarification_prompt**
- **字段的详细生成提示**

### 设计方案应包含
- 整体内容结构和风格方向
- 适用场景
- 关键特点
- 推荐理由

---

## 4. Core Production（内涵生产）✅ 关键

### 目的
按字段逐个生产具体内容。

### 输入
- Intent（项目意图）
- ConsumerResearch（目标用户）
- 选中的 DesignScheme（设计方案）
- 当前字段的完整定义（**包含 ai_hint**）
- 已生成的字段内容（保持一致性）
- 用户对 clarification_prompt 的回答（如果有）

### 输出
- 当前字段的内容

### 提示词内容
- CreatorProfile 约束
- Intent + ConsumerResearch（概要）
- 选中的设计方案（简要）
- **当前字段的 ai_hint**（核心！详细的生成指令）
- 依赖字段的内容（如果有 depends_on）
- 用户的 clarification_answer（如果有）

### 不需要
- 其他未生成字段的定义
- 其他字段的 ai_hint

---

## 5. Extension（外延生产）

### 目的
基于核心内容生成营销/传播内容。

### 输入
- Intent（项目意图）
- ConsumerResearch（目标用户）
- ContentCore（已生成的核心内容）
- 渠道定义

### 输出
- 渠道内容

### 提示词内容
- CreatorProfile 约束
- Intent + ConsumerResearch
- ContentCore 的核心内容摘要
- 渠道特性

---

## 实现计划

### 1. 为 FieldSchema 添加 `format_for_design()` 方法
```python
def format_for_design(self) -> str:
    """格式化为设计阶段使用的概述（不含 ai_hint）"""
    lines = [f"内容模板：{self.name}"]
    if self.description:
        lines.append(f"说明：{self.description}")
    
    lines.append("\n包含的字段：")
    for field in self.fields:
        lines.append(f"- {field.name}：{field.description or '无描述'}")
    
    return "\n".join(lines)
```

### 2. 修改 Core Design 阶段
- 使用 `field_schema.format_for_design()` 而不是 `format_for_prompt()`

### 3. 确保 Core Production 阶段
- 使用完整的 `field_def.ai_hint`（已实现）
- 使用 `clarification_answer`（已实现）
