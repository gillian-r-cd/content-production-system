# 内容生产系统技术架构文档
# 功能：定义系统的核心架构、数据流、模块职责和接口规范
# 主要数据结构：Project, CreatorProfile, Intent, ConsumerResearch, ContentCore, ContentExtension, SimulatorFeedback, Report

---

## 一、系统定位（第一性原理）

### 问题本质
```
用户输入：我想要什么效果（意图）
系统输出：可以直接用的内容（成品）
```

### 核心转换链
```
意图 → 消费者画像 → 内涵（完整内容生产）→ 外延（营销触达）→ 成品
         ↑                    ↓
    创作者特质（全局约束）    Simulator（全程校验）

关键区分：
- 内涵 = 核心内容的完整生产（如：整套课程素材）
- 外延 = 内涵完成后的营销触达（如：课程介绍页、宣传文案）
- 外延必须在内涵全部完成后才能开始
```

### 不做什么（边界）
- ❌ 不是创意工具（不提供灵感）
- ❌ 不是学习工具（不教创作方法）
- ❌ 不是管理工具（不做分类存档）
- ✅ 只做一件事：把意图变成可用内容

---

## 二、核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     CreatorProfile（全局约束）                    │
│              用户自定义字段 + 范例文本 + 禁忌                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────┐    ┌──────────┐    ┌─────────────────────────────────┐
│  Intent  │───▶│ Consumer │───▶│         ContentCore             │
│ Analysis │    │ Research │    │  (按用户定义的FieldSchema        │
│ 意图分析  │    │ 消费者调研 │    │   生成核心内容)                   │
└──────────┘    └──────────┘    └─────────────────────────────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                        ┌──────────┐   ┌──────────┐   ┌──────────┐
                        │Extension │   │Extension │   │Extension │
                        │ 渠道A    │   │ 渠道B    │   │ 渠道C    │
                        └──────────┘   └──────────┘   └──────────┘
                              │               │               │
                              └───────────────┼───────────────┘
                                              ▼
                                     ┌──────────────┐
                                     │  Simulator   │
                                     │ 用户定义评估维度│
                                     └──────────────┘
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                     ┌──────────────┐                ┌──────────────┐
                     │ ProcessReport│                │ QualityReport│
                     │ 流程进度报告  │                │ 内容质量报告  │
                     └──────────────┘                └──────────────┘
```

### 设计原则：用户定义一切

| 组件 | 系统提供 | 用户定义 |
|------|----------|----------|
| CreatorProfile | 基础结构 | 所有字段和值 |
| FieldSchema | 模板库（可选参考） | 从零创建或基于模板修改 |
| ConsumerResearch | AI辅助生成 | 可直接粘贴已有调研 |
| Simulator | 执行框架 | 评估维度、提示词 |
| Report | 两种报告模板 | 关注什么、报警阈值 |

---

## 三、核心数据结构

### 3.1 Project（项目容器）

```yaml
Project:
  id: string
  name: string
  depth: "light" | "standard" | "deep"  # 模块深度
  creator_profile_id: string            # 关联创作者特质
  category: string                      # 内容品类（课程/营销/小说等）
  field_schema_id: string               # 该品类的字段schema
  status: "draft" | "in_progress" | "completed" | "archived"
  created_at: timestamp
  updated_at: timestamp
```

### 3.2 CreatorProfile（创作者特质 - 全局约束）

**设计原则**：允许用户完全自定义字段，系统只提供基础容器。

```yaml
CreatorProfile:
  id: string
  name: string
  
  # ===== 必填：范例文本（最核心的约束）=====
  example_texts: string[]        # 创作者的典型文本，用于few-shot
  
  # ===== 必填：禁忌（硬性约束）=====
  taboos:
    forbidden_words: string[]    # 禁用词汇
    forbidden_topics: string[]   # 禁碰话题
  
  # ===== 可选：自定义字段（用户完全自由定义）=====
  # 用户可以添加任意字段，系统会自动注入到prompt中
  custom_fields: Map<string, any>
  
  # 示例：用户可能定义这些，也可能定义完全不同的
  # custom_fields:
  #   调性: "口语化、略带幽默"
  #   立场: "务实主义，不说大话"
  #   口头禅: ["说白了就是", "你品，你细品"]
  #   写作习惯: "喜欢用短句，每段不超过3行"
  #   偏好比喻: "喜欢用做菜、装修来比喻复杂概念"
  #   目标读者: "职场3-5年的中层管理者"

  # ===== 元信息 =====
  created_at: timestamp
  updated_at: timestamp
```

**自定义字段的处理逻辑**：
```yaml
1. 用户在UI中添加任意key-value
2. 系统自动将所有custom_fields序列化为prompt片段
3. 注入到每个模块的system prompt中
4. 用户无需修改代码，字段自动生效
```

**为什么这样设计**：
- 不同创作者关注的维度完全不同
- 有人重视调性，有人重视结构，有人重视节奏
- 预设字段会限制用户，不如让用户自己定义

### 3.3 FieldSchema（字段schema - 用户定义）

**设计原则**：用户从零开始定义内容品类和字段，系统只提供模板库作为参考。

```yaml
FieldSchema:
  id: string
  name: string              # 用户给这个schema起的名字
  description: string       # 这个schema适用于什么场景
  
  # ===== 用户定义的字段列表 =====
  fields:
    - name: string          # 字段名（用户自定义）
      description: string   # 这个字段是什么（用于prompt和UI提示）
      type: "text" | "list" | "freeform"  # 简化类型
      required: boolean
      ai_hint: string       # 可选：给AI的生成提示

  # ===== 可选：基于哪个模板创建 =====
  based_on_template: string | null  # 如果从模板创建，记录来源
  
  # ===== 元信息 =====
  created_by: string        # 创建者
  is_template: boolean      # 是否作为模板供他人使用
  created_at: timestamp
  updated_at: timestamp
```

**用户创建FieldSchema的流程**：
```yaml
方式1：从零开始
  1. 用户点击"新建内容品类"
  2. 用户逐个添加字段，填写name、description
  3. 保存后可复用

方式2：基于模板
  1. 用户浏览模板库（系统预置 + 社区分享）
  2. 选择一个模板作为起点
  3. 修改、增删字段
  4. 保存为自己的schema

方式3：AI辅助创建
  1. 用户描述"我想做什么类型的内容"
  2. AI建议字段结构
  3. 用户确认/修改
```

**模板库（仅供参考，用户可完全不用）**：
```yaml
# 模板库存放在 /templates/field_schemas/
# 用户可以浏览、fork、修改
# 示例模板：
templates:
  - id: "tpl_course_intro"
    name: "课程介绍页（参考）"
    fields: [学习成果, 痛点, 解决方案, ...]
  
  - id: "tpl_marketing_copy"
    name: "营销长文案（参考）"
    fields: [钩子, 痛点放大, 解决方案, ...]

# 用户也可以把自己的schema标记为模板，分享给他人
```

**为什么这样设计**：
- 每个创作者的方法论不同，字段必须自定义
- 模板只是起点，不是规范
- 允许用户积累自己的内容品类库

### 3.4 Intent（意图分析结果）

```yaml
Intent:
  project_id: string
  
  # 核心意图
  goal: string                    # 这个内容要达成什么效果
  success_criteria: string[]      # 怎么判断内容成功了
  
  # 约束条件
  constraints:
    deadline: timestamp
    budget_tokens: number         # token预算（影响深度选择）
    must_have: string[]           # 必须包含
    must_avoid: string[]          # 必须避免
  
  # 上下文
  context:
    business_background: string   # 业务背景
    existing_assets: string[]     # 已有素材
    competitors: string[]         # 竞品参考
```

### 3.5 ConsumerResearch（消费者调研结果）

**设计原则**：支持三种输入方式，用户选择最适合的。

```yaml
ConsumerResearch:
  project_id: string
  
  # ===== 来源标记 =====
  source: "ai_generated" | "user_pasted" | "hybrid"
  
  # ===== 方式1：自由文本（用户直接粘贴）=====
  # 用户可以直接粘贴已有的调研报告、用户访谈记录等
  raw_text: string | null
  
  # ===== 方式2：结构化字段（AI生成或用户填写）=====
  # 以下字段是建议结构，用户可以只填部分，也可以完全不填
  structured: 
    persona: string              # 用户画像描述（自由格式）
    pain_points: string          # 痛点（自由格式）
    goals: string                # 目标/期望（自由格式）
    context: string              # 使用场景/上下文（自由格式）
    
  # ===== 方式3：自定义字段（用户完全自由定义）=====
  custom_fields: Map<string, any>
  
  # ===== 元信息 =====
  created_at: timestamp
  updated_at: timestamp
```

**三种使用方式**：
```yaml
方式1：直接粘贴
  - 用户已有调研报告、用户访谈、竞品分析
  - 直接粘贴到raw_text，系统原样传给AI
  - 最快，适合有积累的用户

方式2：AI辅助生成
  - 用户描述目标用户是谁
  - AI生成结构化画像
  - 用户确认或修改

方式3：混合模式
  - 粘贴部分已有资料
  - AI补充缺失的部分
  - 用户最终确认
```

**处理逻辑**：
```yaml
如果 raw_text 存在:
  直接将 raw_text 注入到下游模块的prompt
  
如果 structured 存在:
  将 structured 格式化后注入
  
如果两者都存在:
  拼接：raw_text + 格式化的structured
  
custom_fields 始终追加到最后
```

**为什么这样设计**：
- 很多创作者已经有自己的调研资料
- 强制填表会增加摩擦
- 系统应该适配用户，而不是让用户适配系统

### 3.6 ContentCore（内涵 - 完整内容生产）

**关键澄清**：
```yaml
内涵 ≠ 设计
内涵 = 核心内容的完整生产

示例：
  课程内涵: 完整的课程脚本、PPT大纲、练习题、案例素材
  文章内涵: 完整的文章正文
  产品说明书内涵: 完整的产品说明文档

内涵是"产品本身"，外延是"卖产品的营销内容"
```

```yaml
ContentCore:
  project_id: string
  field_schema_id: string         # 使用的字段模板
  
  # ===== 方案选择（生产前）=====
  selected_approach:
    approach_id: string           # 选中的方案ID
    approach_summary: string      # 方案概述
  
  # ===== 实际内容（按FieldSchema逐个字段生产）=====
  # 这里存储的是完整的、可交付的内容
  fields:
    - field_name: string          # 字段名（来自FieldSchema）
      content: text               # 该字段的完整内容
      status: "pending" | "generated" | "approved"
      version: number             # 当前版本号
      evaluation:                 # 该字段的评估结果
        score: number | null
        feedback: string | null
      history:                    # 迭代历史
        - version: number
          content: text
          evaluation: object
          created_at: timestamp
  
  # ===== 整体状态 =====
  overall_status: "in_progress" | "completed"
  overall_evaluation:
    score: number
    summary: string
  
  created_at: timestamp
  updated_at: timestamp
```

**内涵生产流程**：
```yaml
1. 方案选择：生成多个整体思路，用户选择一个
2. 逐字段生产：按FieldSchema，逐个字段生成完整内容
3. 逐字段评估：每个字段生成后，Simulator评估
4. 迭代优化：评估不通过的字段重新生成
5. 整体评估：所有字段完成后，整体评估
6. 完成确认：用户确认后，标记内涵完成

只有内涵完成，才能进入外延生产
```

### 3.7 ContentExtension（外延 - 营销触达内容）

**关键澄清**：
```yaml
外延 = 内涵完成后的营销和触达内容
外延基于内涵生成，复用内涵中的核心素材

示例：
  课程外延: 课程介绍页、小红书宣传文、邮件序列
  文章外延: 社媒摘要、newsletter引流
  产品外延: 产品详情页、电商文案

前提: 内涵必须全部完成
```

```yaml
ContentExtension:
  content_core_id: string         # 关联的内涵（必须已完成）
  
  # 渠道信息
  channel:
    id: string
    name: string                  # 渠道名称
    description: string           # 渠道说明
    format_constraints: object    # 格式约束（字数、结构等）
  
  # 从内涵中提取的素材
  extracted_from_core:
    - field_name: string          # 从内涵的哪个字段提取
      usage: string               # 在外延中如何使用
  
  # 最终内容
  content:
    title: string
    body: text                    # 完整正文
    metadata: object              # 渠道特定的元数据（hashtag等）
  
  # 评估和状态
  evaluation:
    score: number | null
    feedback: string | null
  status: "pending" | "generated" | "approved"
  
  created_at: timestamp
  updated_at: timestamp
```

### 3.8 Simulator（模拟器 - 用户定义评估维度）

**设计原则**：Simulator的提示词由用户编写，系统只提供执行框架。

```yaml
SimulatorConfig:
  id: string
  name: string
  
  # ===== 用户编写的评估提示词 =====
  # 这是Simulator的核心，完全由用户定义
  evaluation_prompt: string
  
  # 示例：
  # evaluation_prompt: |
  #   你是我的目标读者，一个职场3-5年的中层管理者。
  #   你最近在为团队管理问题头疼，想找实用的方法。
  #   
  #   请阅读以下内容，然后告诉我：
  #   1. 读完后你想采取什么行动？
  #   2. 有哪些地方让你觉得"这说的就是我"？
  #   3. 有哪些地方让你觉得"这不太对"或"不适合我"？
  #   4. 整体打分（1-10），为什么？
  
  # ===== 可选：触发条件 =====
  trigger: "auto" | "manual" | "on_stage_complete"
  
  # ===== 可选：评估阈值（用于自动循环）=====
  thresholds:
    pass_score: number           # 高于此分通过
    retry_score: number          # 低于此分自动重试
    max_retries: number          # 最大重试次数

SimulatorFeedback:
  target_id: string
  target_type: "core" | "extension"
  config_id: string              # 使用哪个SimulatorConfig
  
  # ===== AI的原始响应 =====
  raw_response: string           # Simulator的完整输出
  
  # ===== 可选：结构化提取（如果用户需要）=====
  extracted:
    score: number | null
    pass: boolean | null
    key_points: string[]
  
  # ===== 元信息 =====
  created_at: timestamp
```

**用户定义Simulator的流程**：
```yaml
1. 创建SimulatorConfig:
   - 用户写一段提示词，描述"我的读者是谁、关注什么"
   - 可以写多个Simulator用于不同场景

2. 关联到项目:
   - 选择这个项目使用哪个Simulator
   - 或者每次手动触发时选择

3. 执行评估:
   - 系统把内容+提示词发给AI
   - AI返回评估结果
   - 用户查看并决定是否修改
```

**为什么这样设计**：
- 不同业务对"好内容"的定义完全不同
- 预设的评估维度（clarity/relevance等）可能和用户业务无关
- 用户最懂自己的读者，应该由用户定义评估标准
- 提示词是知识资产，用户可以积累和复用

### 3.9 Report（双报告系统）

**设计原则**：报告分两种，各司其职。

#### 3.9.1 ProcessReport（流程进度报告）

```yaml
ProcessReport:
  project_id: string
  generated_at: timestamp
  
  # ===== 进度总览 =====
  progress:
    current_stage: string
    stages:
      - name: string
        status: "pending" | "in_progress" | "completed" | "blocked"
        started_at: timestamp | null
        completed_at: timestamp | null
  
  # ===== 卡点检测 =====
  blockers:
    - stage: string
      reason: string
      blocked_since: timestamp
      suggested_action: string
  
  # ===== 循环检测 =====
  loops:
    - stage: string
      loop_count: number
      loop_history:
        - attempt: number
          feedback_summary: string
          changes_made: string
  
  # ===== 需要人介入的点 =====
  decisions_needed:
    - stage: string
      question: string
      context: string
      urgency: "low" | "medium" | "high"
```

#### 3.9.2 QualityReport（内容质量报告）

```yaml
QualityReport:
  project_id: string
  generated_at: timestamp
  
  # ===== 各阶段产出的评估 =====
  evaluations:
    - stage: string
      artifact_type: string        # 产出类型（Intent/ContentCore/Extension等）
      simulator_used: string       # 使用了哪个Simulator
      
      # Simulator的评估结果
      evaluation:
        raw_response: string       # 原始评估
        score: number | null       # 如果有打分
        passed: boolean
        key_issues: string[]       # 关键问题
    
  # ===== 上下游一致性检查 =====
  # 检查各阶段产出是否对齐
  alignment_checks:
    - from_stage: string
      to_stage: string
      check_description: string    # 检查什么
      result: "aligned" | "misaligned" | "uncertain"
      details: string
  
  # ===== 整体质量评估 =====
  overall:
    intent_to_output_alignment: string  # 最终产出是否符合最初意图
    creator_voice_consistency: string   # 是否保持创作者风格
    recommendations: string[]           # 改进建议
```

**两种报告的关系**：
```yaml
ProcessReport:
  - 回答"进展到哪了？卡在哪了？"
  - 用于human-out-of-the-loop时追踪状态
  - 重点是流程，不是内容

QualityReport:
  - 回答"内容质量如何？哪里需要改？"
  - 汇总所有Simulator的评估结果
  - 检查端到端的一致性（意图→最终产出）
  - 重点是内容，不是流程
```

**触发时机**：
```yaml
ProcessReport:
  - 每个阶段完成时自动更新
  - 检测到卡点时立即生成
  - 用户可随时查看

QualityReport:
  - 项目完成时生成完整报告
  - 用户手动触发中间检查
  - Simulator评估不通过时生成局部报告
```

---

## 四、模块职责与接口

### 4.1 IntentAnalyzer（意图分析模块）

```yaml
职责: 把用户的模糊意图转化为结构化的Intent对象

输入:
  - user_input: string          # 用户原始输入
  - creator_profile: CreatorProfile
  - project_depth: "light" | "standard" | "deep"

输出:
  - intent: Intent

行为:
  light模式: 快速提取，用默认值填充缺失项
  standard模式: 追问澄清，确保核心字段完整
  deep模式: 深度挖掘，探索隐含需求
```

### 4.2 ConsumerResearcher（消费者调研模块）

```yaml
职责: 构建目标消费者画像

输入:
  - intent: Intent
  - creator_profile: CreatorProfile
  - project_depth: "light" | "standard" | "deep"

输出:
  - consumer_research: ConsumerResearch

行为:
  light模式: 基于intent推断，用通用画像
  standard模式: AI调研 + 人确认关键假设
  deep模式: Deep Research + 专家校验
```

### 4.3 ContentCoreDesigner（内涵设计模块）

```yaml
职责: 设计内容的核心价值和结构

输入:
  - intent: Intent
  - consumer_research: ConsumerResearch
  - creator_profile: CreatorProfile
  - field_schema: FieldSchema
  - project_depth: "light" | "standard" | "deep"

输出:
  - content_core: ContentCore
  - alternatives: ContentCore[]    # 批量方案（设计阶段）

行为:
  所有模式: 批量生成多个方案供选择
  选定后: 只保留一个方案进入下一阶段
```

### 4.4 ContentExtensionProducer（外延生产模块）

```yaml
职责: 把内涵适配到具体渠道

输入:
  - content_core: ContentCore
  - channels: Channel[]           # 目标渠道列表
  - creator_profile: CreatorProfile

输出:
  - extensions: ContentExtension[]

行为:
  一个content_core → 多个content_extension（一对多）
  每个渠道独立生产，但共享同一个内涵
```

### 4.5 Simulator（模拟器模块）

```yaml
职责: 模拟消费者反应，评估内容效果

输入:
  - target: ContentCore | ContentExtension
  - consumer_research: ConsumerResearch
  - creator_profile: CreatorProfile
  - intent: Intent

输出:
  - feedback: SimulatorFeedback

调用时机:
  - ContentCore生成后（评估内涵）
  - 每个ContentExtension生成后（评估外延）
  - 可配置为自动触发或手动触发
```

### 4.6 ReportGenerator（报告生成模块）

```yaml
职责: 生成全景报告，支持human-out-of-the-loop

输入:
  - project: Project
  - all_artifacts: 所有中间产物

输出:
  - report: Report

触发条件:
  - 定时触发（可配置间隔）
  - 阶段完成时触发
  - 异常检测时触发
  - 用户主动请求
```

---

## 五、工作流程定义

### 5.1 主流程

```yaml
1. 初始化:
   - 用户选择/创建 CreatorProfile
   - 用户选择内容品类 → 加载对应 FieldSchema
   - 用户选择项目深度（light/standard/deep）

2. 意图分析:
   - 用户输入原始需求
   - IntentAnalyzer 生成 Intent
   - [standard/deep] 用户确认或修改

3. 消费者调研:
   - ConsumerResearcher 生成 ConsumerResearch
   - [standard/deep] 用户确认关键假设

4. 内涵生产（核心内容的完整生产）:
   - 4.1 方案设计：批量生成多个整体思路，用户选择一个
   - 4.2 逐字段生产：按FieldSchema逐个字段生成完整内容
   - 4.3 逐字段评估：每个字段生成后，Simulator评估
   - 4.4 迭代优化：评估不通过的字段重新生成
   - 4.5 整体评估：所有字段完成后，整体评估
   - 4.6 用户确认：确认内涵完成，才能进入外延

5. 外延生产（可随时开始）:
   - 时机：只要用户愿意，随时可以调用
   - 早期（内涵未完成）：基于意图和价值点生成初版
   - 后期（内涵已完成）：基于完整素材生成精确版
   - 系统自动识别可引用的上下文，注入到提示词
   - Simulator 评估
   - 内涵更新后，可重新生成外延以保持一致

6. 输出:
   - 生成最终 Report
   - 导出所有 ContentExtension
```

### 5.2 循环控制

```yaml
最大循环次数: 3（可配置）

循环触发条件:
  - Simulator反馈中有 critical 问题
  - Simulator反馈中 major 问题 >= 2

循环退出条件:
  - 无 critical 问题 且 major 问题 < 2
  - 达到最大循环次数 → 标记异常，请求人介入
```

### 5.3 深度切换

```yaml
用户可以在流程中动态调整深度:
  - 某个模块卡住 → 切换到 deep 模式深挖
  - 时间紧迫 → 切换到 light 模式快速通过
  - 切换只影响当前模块，不影响其他模块
```

---

## 六、AI Prompting 策略

### 6.1 系统提示词结构

```yaml
每个模块的AI调用都包含:

1. 角色设定:
   - 明确AI在该模块中的角色
   - 明确能力边界

2. 上下文注入:
   - CreatorProfile（必须）
   - 前序模块的输出（按需）
   - FieldSchema（内涵设计时）

3. 任务指令:
   - 明确输入输出格式
   - 明确质量标准
   - 明确禁止事项

4. 输出约束:
   - 结构化输出（JSON/YAML）
   - 长度限制
   - 风格约束（来自CreatorProfile）
```

### 6.2 CreatorProfile 注入模板

```
你正在为以下创作者生产内容：

【调性】
- 正式度：{formality}/5
- 幽默感：{humor}/5
- 能量级：{energy}/5

【立场】
- 务实-理想主义：{pragmatic_idealistic}/5
- 中立-激进：{neutral_radical}/5

【禁忌 - 严格遵守】
- 禁用词汇：{forbidden_words}
- 禁碰话题：{forbidden_topics}

【标志性表达 - 尽量使用】
- 口头禅：{catchphrases}
- 惯用结构：{preferred_structures}

【范例文本 - 模仿风格】
{example_texts}
```

### 6.3 Simulator 提示词（用户定义）

**Simulator的提示词由用户编写**，系统只负责：
1. 注入上下文变量（如 `{content}`, `{intent}` 等）
2. 执行调用
3. 收集结果

**可用变量**（用户在提示词中可使用）：
```yaml
{content}           # 待评估的内容
{intent}            # 项目意图
{consumer_research} # 消费者调研结果
{creator_profile}   # 创作者特质
{stage}             # 当前阶段
```

**用户编写示例**：
```markdown
# 示例1：简洁型
你是我的目标读者。读完下面的内容后，告诉我：
1. 你会采取什么行动？
2. 哪里让你感觉"不对"？
3. 打分1-10

【内容】
{content}

# 示例2：详细型
你现在扮演以下角色：
{consumer_research}

你正在浏览内容，评估是否值得花时间。

【待评估内容】
{content}

【评估任务】
请回答：
- 这个内容是否解决了我的问题？具体哪些点解决了？
- 作者的说法我信吗？为什么？
- 我会分享给朋友吗？为什么？
- 有哪些地方让我想关掉页面？

# 示例3：专业型（课程场景）
你是一个想学{topic}的职场人，已经看过3个同类课程的介绍页。

【这个课程的介绍页】
{content}

请评估：
1. 和其他课程比，这个有什么不同？
2. 学习目标清楚吗？学完能做到什么？
3. 价格值吗？为什么？
4. 你会报名吗？
```

**系统默认模板**（用户不写时使用）：
```markdown
请评估以下内容是否能达成目标。

【目标】
{intent}

【内容】
{content}

【评估要求】
1. 是否达成目标？(1-10分)
2. 主要问题是什么？
3. 如何改进？
```

---

## 七、人机交互点定义

### 7.1 必须人介入的点

```yaml
1. 意图确认:
   - 确认 Intent.goal 是否准确捕捉需求
   - 确认 success_criteria 是否可衡量

2. 方案选择:
   - 从批量生成的 ContentCore 中选择一个

3. 最终验收:
   - 确认 ContentExtension 可以发布
```

### 7.2 可选人介入的点

```yaml
1. 消费者画像确认（standard/deep模式）
2. Simulator反馈后的修改方向
3. 循环3次后的异常处理
```

### 7.3 不需要人介入的点

```yaml
1. 调研数据收集（AI执行）
2. 内容生产（AI执行）
3. 自动质量检查（Simulator执行）
4. 报告生成（自动）
```

---

## 八、文件结构规划

```
/content_production_system
├── /config
│   ├── field_schemas/           # 各品类的字段schema
│   │   ├── course.yaml
│   │   ├── marketing.yaml
│   │   └── ...
│   └── prompts/                 # 各模块的prompt模板
│       ├── intent_analyzer.md
│       ├── consumer_researcher.md
│       ├── content_core_designer.md
│       ├── content_extension_producer.md
│       └── simulator.md
│
├── /core
│   ├── models/                  # 数据模型定义
│   │   ├── project.py
│   │   ├── creator_profile.py
│   │   ├── intent.py
│   │   ├── consumer_research.py
│   │   ├── content_core.py
│   │   ├── content_extension.py
│   │   ├── simulator_feedback.py
│   │   └── report.py
│   │
│   ├── modules/                 # 核心模块
│   │   ├── intent_analyzer.py
│   │   ├── consumer_researcher.py
│   │   ├── content_core_designer.py
│   │   ├── content_extension_producer.py
│   │   ├── simulator.py
│   │   └── report_generator.py
│   │
│   └── orchestrator.py          # 流程编排器
│
├── /storage
│   ├── creator_profiles/        # 创作者特质存储
│   └── projects/                # 项目数据存储
│
└── /ui                          # 交互界面（可选）
    ├── cli.py                   # 命令行界面
    └── web/                     # Web界面（可选）
```

---

## 九、实现优先级

### P0（核心MVP）
1. CreatorProfile 数据结构与存储
2. Intent 分析模块（standard模式）
3. ContentCore 设计模块（支持1个品类）
4. Simulator 评估模块
5. 基础CLI交互

### P1（完整单品类）
1. ConsumerResearch 模块
2. ContentExtension 生产模块
3. Report 生成模块
4. 循环控制逻辑

### P2（多品类扩展）
1. FieldSchema 体系
2. 多品类支持（课程、营销、小说等）
3. 深度切换（light/standard/deep）

### P3（体验优化）
1. Web界面
2. 批量项目管理
3. CreatorProfile学习（从历史内容中提取特质）

---

## 十、关键设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 数据格式 | YAML/JSON | 人类可读，AI易处理 |
| 存储方式 | 文件系统 | 简单，便于版本控制，MVP够用 |
| 批量方案数 | 3个 | 平衡选择丰富度和token成本 |
| 最大循环次数 | 3次 | 防止无限循环，超过则请求人介入 |
| Simulator调用时机 | 每个产出后 | 尽早发现问题，避免下游浪费 |

