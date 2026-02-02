# 字段生成前的交互式问答设计

## 需求背景

用户希望在生成某个字段前，如果需要更多信息，可以先弹出对话框让用户补充。这个问答只允许1轮。

## 设计方案

### 1. 字段定义扩展

在 `FieldDefinition` 中添加 `clarification_prompt` 字段：

```python
class FieldDefinition(BaseModel):
    # ... 现有字段 ...
    
    # 生成前询问用户的问题（可选）
    clarification_prompt: str = Field(
        default="",
        description="生成该字段前需要向用户确认的问题（只问1轮）"
    )
```

### 2. 工作流状态

在 `ContentField` 中添加用户回答：

```python
class ContentField(BaseModel):
    # ... 现有字段 ...
    
    # 用户对澄清问题的回答
    clarification_answer: Optional[str] = None
```

### 3. 生成流程

```
开始生成字段
    ↓
检查是否有 clarification_prompt
    ↓ (有)
返回 "waiting_for_clarification" 状态
    ↓
前端显示问题，用户回答
    ↓
用户提交回答，存储到 clarification_answer
    ↓
继续生成，将 clarification_answer 注入到提示词
```

### 4. API 变更

#### 生成字段响应

```json
{
  "status": "waiting_for_clarification",
  "field_id": "field_123",
  "question": "请描述这个角色的核心性格特征是什么？"
}
```

#### 提交澄清回答

```
POST /api/workflow/{workflow_id}/fields/{field_id}/clarify
{
  "answer": "用户的回答"
}
```

## 实现步骤

1. 扩展 FieldDefinition 模型添加 clarification_prompt
2. 扩展 ContentField 模型添加 clarification_answer
3. 修改字段模板 UI 添加"生成前提问"配置
4. 修改生成逻辑检查并处理澄清问答
5. 前端添加澄清问答对话框

## 当前状态

此功能需要较大改动，已创建设计文档。基础修复已完成：
- ✅ 内容显示不完整问题已修复
- ✅ AI提示说明已优化
- ✅ 提示词拼接逻辑已重构
