# 回退机制修复计划

## 问题根因分析

1. **阶段验证过于严格**：`select-scheme` 只允许 `core_design/core_production` 阶段
2. **缺少回退机制**：没有API支持从后面阶段回退
3. **内涵生产逻辑不完整**：没有正确处理 `continue` 调用

## 解决方案

### 1. 添加回退API：`POST /workflow/{id}/rollback`

功能：
- 接收目标阶段
- 自动创建版本备份
- 清除目标阶段之后的所有数据
- 重置项目状态到目标阶段

### 2. 修改 `select-scheme` 端点

- 移除严格的阶段验证
- 改为检查是否有 `content_core` 数据
- 如果从后面阶段调用，先触发回退

### 3. 修复 `continue` 端点

- 检查当前阶段状态
- 如果 `waiting_for_input=False` 才能继续
- 正确推进阶段

## 测试基准

| 测试场景 | 预期结果 |
|---------|---------|
| extension阶段点击"重新选择方案" | 成功回退到core_design，创建备份 |
| 重新选择后检查下游数据 | extension数据被清除 |
| core_production点击"开始生成" | 正确触发内容生成 |
| 生成完成后进入extension | 自动过渡 |

## TODO List

- [ ] 1. 创建 rollback API 端点
- [ ] 2. 修改 select-scheme 支持回退
- [ ] 3. 修复 continue 端点逻辑
- [ ] 4. 前端调用 rollback API
- [ ] 5. 测试完整流程


