# 内容品类字段Schema定义
# 功能：定义各内容品类的核心字段，这是系统个性化的基点
# 原则：流程通用，字段特异

---

## 一、字段Schema设计原则

### 1.1 核心理念

```
"个性化不在流程，而在字段"
- 所有品类共享同一个生产流程（意图→调研→设计→生产→反馈）
- 不同品类通过不同的字段来适配
```

### 1.2 字段定义规范

```yaml
字段结构:
  name: string              # 字段名（英文，snake_case）
  display_name: string      # 显示名（中文）
  type: "text" | "list" | "structured" | "number" | "boolean"
  required: boolean         # 是否必填
  description: string       # 字段说明
  example: string | list    # 示例值
  validation_hints: string[]  # 验证提示
  ai_generation_hint: string  # AI生成该字段时的提示
```

---

## 二、课程类（Education）

### 2.1 course_intro（课程介绍页）

```yaml
schema_id: "course_intro"
category: "education"
display_name: "课程介绍页"
description: "用于招生的课程介绍落地页，目标是转化"

fields:
  - name: "target_outcome"
    display_name: "学习成果"
    type: "text"
    required: true
    description: "学完后学员能做到什么（可观察、可验证的行为）"
    example: "能独立完成一个完整的数据分析报告"
    ai_generation_hint: "用「能+动词+具体成果」的格式表述"

  - name: "prerequisite"
    display_name: "前置条件"
    type: "list"
    required: false
    description: "学员需要具备什么才能学这门课"
    example: ["基础的Excel操作能力", "对数据分析有兴趣"]
    ai_generation_hint: "列出3个以内，过多会吓退潜在学员"

  - name: "pain_points"
    display_name: "痛点"
    type: "list"
    required: true
    description: "目标学员当前面临的具体问题"
    example: ["不知道如何用数据说服老板", "做的图表总是被嫌弃不专业"]
    ai_generation_hint: "用学员的语言描述，要具体不要抽象"

  - name: "solution_promise"
    display_name: "解决方案承诺"
    type: "text"
    required: true
    description: "这门课如何解决上述痛点"
    example: "通过20个真实商业案例，教你用数据讲故事"
    ai_generation_hint: "要具体、可信，避免空泛承诺"

  - name: "credibility_proof"
    display_name: "可信度证明"
    type: "structured"
    required: true
    description: "为什么相信这门课有效"
    example:
      instructor_background: "前阿里数据分析师，10年经验"
      student_results: "已有500+学员，平均涨薪30%"
      endorsements: "被XX机构推荐"
    ai_generation_hint: "优先使用数字和具体案例"

  - name: "curriculum_highlights"
    display_name: "课程亮点"
    type: "list"
    required: true
    description: "课程最吸引人的3-5个特色"
    example: ["真实企业案例", "1对1作业批改", "终身答疑群"]
    ai_generation_hint: "突出差异化，和竞品不同的点"

  - name: "risk_reversal"
    display_name: "风险逆转"
    type: "text"
    required: false
    description: "降低学员决策风险的承诺"
    example: "7天无理由退款"
    ai_generation_hint: "要真实可执行，不要过度承诺"

  - name: "cta"
    display_name: "行动号召"
    type: "text"
    required: true
    description: "希望学员采取的具体行动"
    example: "立即报名，前100名送价值299元工具包"
    ai_generation_hint: "要具体、紧迫、有诱因"
```

### 2.2 lesson（单节课程）

```yaml
schema_id: "lesson"
category: "education"
display_name: "单节课程"
description: "一节课的内容设计"

fields:
  - name: "learning_objective"
    display_name: "学习目标"
    type: "text"
    required: true
    description: "这节课学完后能做什么"
    example: "能用VLOOKUP函数进行跨表查询"
    ai_generation_hint: "Bloom分类法：记忆→理解→应用→分析→评估→创造"

  - name: "cognitive_conflict"
    display_name: "认知冲突"
    type: "text"
    required: true
    description: "打破什么旧认知或常见误解"
    example: "VLOOKUP并不是只能从左往右查，用INDEX+MATCH可以反向"
    ai_generation_hint: "「你以为...其实...」格式"

  - name: "concept_explanation"
    display_name: "概念讲解"
    type: "structured"
    required: true
    description: "核心概念的解释结构"
    example:
      what: "VLOOKUP是什么"
      why: "为什么需要它"
      how: "怎么用"
      when: "什么时候用"
    ai_generation_hint: "What-Why-How-When四要素"

  - name: "example"
    display_name: "案例"
    type: "structured"
    required: true
    description: "辅助理解的案例"
    example:
      scenario: "你需要从员工表中查找某人的薪资"
      step_by_step: ["第一步", "第二步"]
      common_mistakes: ["忘记锁定范围", "顺序搞反"]
    ai_generation_hint: "案例要贴近学员工作场景"

  - name: "practice_task"
    display_name: "练习任务"
    type: "structured"
    required: true
    description: "课后练习设计"
    example:
      task: "用提供的数据完成XX"
      difficulty: "中等"
      expected_time: "20分钟"
      rubric: ["正确使用公式", "结果准确"]
    ai_generation_hint: "难度递进，有明确评判标准"

  - name: "transfer_scenario"
    display_name: "迁移场景"
    type: "list"
    required: false
    description: "学员可以把技能用到什么其他场景"
    example: ["跨部门数据合并", "客户信息匹配"]
    ai_generation_hint: "帮助学员举一反三"
```

---

## 三、营销类（Marketing）

### 3.1 landing_page（落地页长文案）

```yaml
schema_id: "landing_page"
category: "marketing"
display_name: "落地页长文案"
description: "销售页/落地页的完整文案"

fields:
  - name: "hook"
    display_name: "开头钩子"
    type: "text"
    required: true
    description: "吸引注意力的开场"
    example: "为什么你每天工作12小时，收入还是上不去？"
    ai_generation_hint: "用问题/痛点/反常识开头"

  - name: "problem_agitation"
    display_name: "问题放大"
    type: "structured"
    required: true
    description: "痛点描述和后果放大"
    example:
      pain_point: "时间管理混乱"
      consequences: ["错过重要deadline", "加班成常态", "家庭关系紧张"]
      emotional_weight: "你已经为此牺牲了多少个周末？"
    ai_generation_hint: "PAS公式：Problem-Agitation-Solution"

  - name: "solution_intro"
    display_name: "解决方案引入"
    type: "text"
    required: true
    description: "产品/服务是什么，如何解决问题"
    example: "「时间掌控系统」是一套经过验证的方法论..."
    ai_generation_hint: "不要急着卖，先建立解决问题的框架"

  - name: "benefits"
    display_name: "利益点"
    type: "list"
    required: true
    description: "用户能获得的具体好处"
    example: ["每周多出10小时自由时间", "重要任务完成率提升50%"]
    ai_generation_hint: "Feature→Benefit转化，用数字说话"

  - name: "social_proof"
    display_name: "社会证明"
    type: "structured"
    required: true
    description: "证明有效的第三方证据"
    example:
      testimonials: ["用户A的评价", "用户B的评价"]
      stats: "已帮助10000+职场人"
      media_mentions: ["被XX媒体报道"]
    ai_generation_hint: "越具体越可信，避免泛泛而谈"

  - name: "offer"
    display_name: "报价"
    type: "structured"
    required: true
    description: "价格呈现和价值对比"
    example:
      price: "299元"
      value_comparison: "相当于一顿下午茶的价格"
      included: ["主课程", "模板", "社群"]
      bonuses: ["限时赠送XX"]
    ai_generation_hint: "价值感 > 价格感"

  - name: "guarantee"
    display_name: "保障"
    type: "text"
    required: false
    description: "风险逆转承诺"
    example: "30天无条件退款，风险全部我来承担"
    ai_generation_hint: "降低决策门槛"

  - name: "cta"
    display_name: "行动号召"
    type: "structured"
    required: true
    description: "引导下一步行动"
    example:
      main_cta: "立即加入"
      urgency: "仅剩23个名额"
      next_step: "点击下方按钮，填写信息"
    ai_generation_hint: "一个页面一个核心CTA"

  - name: "faq"
    display_name: "常见问题"
    type: "list"
    required: false
    description: "预处理常见异议"
    example: 
      - q: "我没时间怎么办？"
        a: "每天只需要10分钟..."
    ai_generation_hint: "回答要真诚，不要回避问题"
```

### 3.2 social_post（社媒短文案）

```yaml
schema_id: "social_post"
category: "marketing"
display_name: "社媒短文案"
description: "小红书/微博/朋友圈等短内容"

fields:
  - name: "hook"
    display_name: "开头钩子"
    type: "text"
    required: true
    description: "前两行决定用户是否继续看"
    example: "我用这个方法，3个月涨粉10万👇"
    ai_generation_hint: "要在信息流中「跳出来」"

  - name: "core_content"
    display_name: "核心内容"
    type: "text"
    required: true
    description: "主体内容"
    example: "第一步...第二步...第三步..."
    ai_generation_hint: "短句、分段、易扫读"

  - name: "value_point"
    display_name: "价值点"
    type: "text"
    required: true
    description: "用户能获得什么"
    example: "学会这个，你也能..."
    ai_generation_hint: "和用户利益强相关"

  - name: "engagement_hook"
    display_name: "互动引导"
    type: "text"
    required: true
    description: "引导评论/收藏/转发"
    example: "你最想解决的问题是什么？评论区告诉我"
    ai_generation_hint: "问问题比让人点赞更有效"

  - name: "hashtags"
    display_name: "标签"
    type: "list"
    required: false
    description: "相关话题标签"
    example: ["#职场干货", "#自我提升"]
    ai_generation_hint: "热门标签+垂直标签组合"
```

### 3.3 email_campaign（邮件营销）

```yaml
schema_id: "email_campaign"
category: "marketing"
display_name: "邮件营销"
description: "营销邮件/用户召回邮件"

fields:
  - name: "subject_line"
    display_name: "主题行"
    type: "text"
    required: true
    description: "决定打开率的关键"
    example: "张三，你上次看的课程还有最后3个名额"
    ai_generation_hint: "个人化+紧迫感+好奇心"

  - name: "preview_text"
    display_name: "预览文本"
    type: "text"
    required: false
    description: "主题行后显示的预览"
    example: "专属优惠明天到期..."
    ai_generation_hint: "补充主题行，不要重复"

  - name: "greeting"
    display_name: "称呼"
    type: "text"
    required: true
    description: "开头称呼"
    example: "Hi {first_name},"
    ai_generation_hint: "能用名字就用名字"

  - name: "body"
    display_name: "正文"
    type: "structured"
    required: true
    description: "邮件主体"
    example:
      opener: "还记得上次我们聊的XX吗？"
      value: "今天想分享一个..."
      connection: "我觉得这对你特别有用，因为..."
    ai_generation_hint: "像给朋友写信，不像广告"

  - name: "cta"
    display_name: "行动号召"
    type: "structured"
    required: true
    description: "引导的具体行动"
    example:
      button_text: "查看详情"
      link: "{link}"
      urgency: "优惠24小时后结束"
    ai_generation_hint: "一封邮件一个核心CTA"

  - name: "signature"
    display_name: "署名"
    type: "text"
    required: true
    description: "发件人署名"
    example: "Best,\n张三"
    ai_generation_hint: "用真人名字，不用品牌名"
```

---

## 四、内容运营类（Content Ops）

### 4.1 article（公众号长文）

```yaml
schema_id: "article"
category: "content_ops"
display_name: "公众号长文"
description: "1500-3000字的深度内容"

fields:
  - name: "title"
    display_name: "标题"
    type: "text"
    required: true
    description: "决定打开率"
    example: "我花了3年才明白的职场真相（早看到少走弯路）"
    ai_generation_hint: "悬念/数字/痛点/反常识"

  - name: "opening"
    display_name: "开篇"
    type: "text"
    required: true
    description: "前100字决定是否继续"
    example: "上周，一个读者私信问我..."
    ai_generation_hint: "故事/问题/场景/金句"

  - name: "thesis"
    display_name: "核心观点"
    type: "text"
    required: true
    description: "全文要传递的一个核心观点"
    example: "真正的高效不是做得多，而是做得对"
    ai_generation_hint: "一句话能说清楚"

  - name: "structure"
    display_name: "结构"
    type: "list"
    required: true
    description: "文章骨架"
    example:
      - section: "1. 为什么大多数人越忙越穷"
        points: ["忙不等于有效", "时间投入产出比"]
      - section: "2. 高效人士的3个共同特点"
        points: ["特点一", "特点二", "特点三"]
    ai_generation_hint: "先搭骨架再填肉"

  - name: "examples"
    display_name: "案例/故事"
    type: "list"
    required: true
    description: "支撑观点的案例"
    example: ["我自己的经历", "某CEO的故事", "研究数据"]
    ai_generation_hint: "个人故事+名人案例+数据组合"

  - name: "takeaway"
    display_name: "金句/要点"
    type: "list"
    required: true
    description: "可以被划线/截图的金句"
    example: ["真正的自由是知道什么时候说不", "时间不是管出来的，是选出来的"]
    ai_generation_hint: "朗朗上口，能脱离上下文独立存在"

  - name: "ending"
    display_name: "结尾"
    type: "text"
    required: true
    description: "升华/总结/行动引导"
    example: "如果你也觉得有用，转发给需要的朋友吧"
    ai_generation_hint: "回扣主题+引导互动"
```

---

## 五、Schema扩展指南

### 5.1 如何新增品类

```yaml
步骤:
  1. 识别品类核心目标:
     - 这类内容要达成什么效果？
     - 成功的标准是什么？
  
  2. 拆解该品类的最佳实践:
     - 找10个优秀案例
     - 提取共同的结构元素
     - 识别必须有vs可选有的元素
  
  3. 定义字段:
     - 每个元素定义为一个字段
     - 明确类型、是否必填
     - 写清楚AI生成提示
  
  4. 验证:
     - 用这套字段能不能覆盖原来的优秀案例
     - 是不是每个字段都必要
     - 有没有遗漏的关键元素

示例问题:
  - 如果去掉这个字段，内容还完整吗？
  - 这两个字段是不是重复了？
  - AI能根据这个字段描述生成吗？
```

### 5.2 字段类型说明

```yaml
text:
  - 单段文本
  - 适用于：标题、核心观点、一句话描述

list:
  - 多项列表
  - 适用于：要点、步骤、案例列表

structured:
  - 嵌套结构
  - 适用于：有多个子维度的复合信息
  - 需要定义子字段

number:
  - 数字
  - 适用于：字数限制、时长、评分

boolean:
  - 是/否
  - 适用于：开关类设置
```

---

## 六、品类对照表

| 品类ID | 显示名 | 典型场景 | 核心字段数 |
|--------|--------|----------|------------|
| course_intro | 课程介绍页 | 招生转化 | 8 |
| lesson | 单节课程 | 教学设计 | 6 |
| landing_page | 落地页长文案 | 销售页 | 9 |
| social_post | 社媒短文案 | 日常运营 | 5 |
| email_campaign | 邮件营销 | 用户召回 | 6 |
| article | 公众号长文 | 内容运营 | 7 |



