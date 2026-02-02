# 实施指南
# 功能：定义系统的实现路径、技术选型、MVP范围
# 原则：一步一步修改，一步一步验证

---

## 一、技术选型建议

### 1.1 核心原则

```
简单优先：能用文件就不用数据库，能用CLI就不用Web
渐进增强：先跑通流程，再优化体验
最小依赖：只引入必要的库
```

### 1.2 推荐技术栈

```yaml
语言: Python 3.10+
理由: AI生态最成熟，库丰富

数据存储: 文件系统 (YAML/JSON)
理由: 人类可读，便于调试，Git可追踪

AI接口: OpenAI API / Claude API
理由: 直接调用，不需要额外封装

配置管理: YAML
理由: 比JSON更易读写

CLI框架: Click 或 Typer
理由: 简单直观

未来可选:
  - Web界面: FastAPI + HTMX（轻量）或 Streamlit（快速原型）
  - 数据库: SQLite（单机）→ PostgreSQL（多用户）
```

---

## 二、MVP范围定义

### 2.1 MVP目标

```
一个品类（课程介绍页），走通完整流程：
意图分析 → 消费者调研 → 内涵设计 → 外延生产 → Simulator评估 → 输出
```

### 2.2 MVP包含

```yaml
必须有:
  - CreatorProfile 创建和存储
  - Intent 分析模块（standard模式）
  - ConsumerResearch 模块（light模式，自动推断）
  - ContentCore 设计模块（生成3个方案）
  - ContentExtension 生产模块（支持1个渠道）
  - Simulator 评估模块
  - 基础CLI交互

不需要:
  - Web界面
  - 多品类支持
  - Deep Research
  - 报告生成
  - 深度切换
```

### 2.3 MVP验收标准

```yaml
能够:
  1. 创建一个CreatorProfile
  2. 输入"我想做一个数据分析课程的介绍页"
  3. 系统追问澄清意图
  4. 系统生成消费者画像
  5. 系统生成3个差异化的内涵方案
  6. 用户选择一个方案
  7. 系统生成落地页文案
  8. Simulator评估并给出反馈
  9. 输出最终文案
```

---

## 三、实现路径

### Phase 0：项目初始化

```yaml
任务:
  - 创建项目结构
  - 配置依赖管理
  - 创建基础配置文件

产出:
  - requirements.txt
  - 目录结构
  - 基础配置
```

### Phase 1：数据模型

```yaml
任务:
  - 实现 CreatorProfile 数据模型
  - 实现 Intent 数据模型
  - 实现 ConsumerResearch 数据模型
  - 实现 ContentCore 数据模型
  - 实现 ContentExtension 数据模型
  - 实现 SimulatorFeedback 数据模型
  - 实现文件存储/加载工具

验证:
  - 能创建、保存、加载各种数据对象
  - YAML输出人类可读

产出:
  - core/models/*.py
  - storage/*.yaml（示例数据）
```

### Phase 2：Prompt引擎

```yaml
任务:
  - 实现 Prompt 模板加载器
  - 实现 CreatorProfile 注入逻辑
  - 实现 AI API 调用封装
  - 实现输出解析（YAML→对象）

验证:
  - 能加载prompt模板
  - 能注入CreatorProfile
  - 能调用AI并解析响应

产出:
  - core/prompt_engine.py
  - core/ai_client.py
  - config/prompts/*.md
```

### Phase 3：核心模块

```yaml
任务:
  - 实现 IntentAnalyzer
  - 实现 ConsumerResearcher
  - 实现 ContentCoreDesigner
  - 实现 ContentExtensionProducer
  - 实现 Simulator

验证:
  - 每个模块能独立运行
  - 输入输出格式正确
  - 能处理常见错误

产出:
  - core/modules/*.py

实现顺序:
  1. IntentAnalyzer（最简单，建立模式）
  2. Simulator（独立性强，可以先测）
  3. ConsumerResearcher（依赖Intent）
  4. ContentCoreDesigner（核心模块）
  5. ContentExtensionProducer（最后串联）
```

### Phase 4：流程编排

```yaml
任务:
  - 实现 Orchestrator（流程编排器）
  - 实现模块间数据传递
  - 实现循环控制逻辑
  - 实现人机交互点

验证:
  - 能完整走通一个项目
  - 循环控制正常工作
  - 交互点正确触发

产出:
  - core/orchestrator.py
```

### Phase 5：CLI界面

```yaml
任务:
  - 实现创建CreatorProfile命令
  - 实现创建项目命令
  - 实现运行项目命令
  - 实现查看状态命令

验证:
  - 命令行操作流畅
  - 输出易读
  - 错误提示清晰

产出:
  - ui/cli.py
```

---

## 四、核心代码结构

### 4.1 目录结构

```
/content_production_system
├── requirements.txt
├── config.yaml                  # 全局配置
│
├── /config
│   ├── field_schemas/
│   │   └── course_intro.yaml
│   └── prompts/
│       ├── intent_analyzer.md
│       ├── consumer_researcher.md
│       ├── content_core_designer.md
│       ├── content_extension_producer.md
│       └── simulator.md
│
├── /core
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py              # 基础模型类
│   │   ├── creator_profile.py
│   │   ├── project.py
│   │   ├── intent.py
│   │   ├── consumer_research.py
│   │   ├── content_core.py
│   │   ├── content_extension.py
│   │   └── simulator_feedback.py
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── base.py              # 模块基类
│   │   ├── intent_analyzer.py
│   │   ├── consumer_researcher.py
│   │   ├── content_core_designer.py
│   │   ├── content_extension_producer.py
│   │   └── simulator.py
│   │
│   ├── prompt_engine.py         # Prompt加载和渲染
│   ├── ai_client.py             # AI API封装
│   └── orchestrator.py          # 流程编排
│
├── /storage
│   ├── creator_profiles/        # 存储CreatorProfile
│   └── projects/                # 存储项目数据
│
└── /ui
    └── cli.py                   # 命令行入口
```

### 4.2 关键接口定义

```python
# core/models/base.py
"""
基础模型类
功能：提供所有数据模型的基础能力
"""
from dataclasses import dataclass
from typing import Optional
import yaml

@dataclass
class BaseModel:
    """所有数据模型的基类"""
    
    def to_yaml(self) -> str:
        """转换为YAML字符串"""
        pass
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'BaseModel':
        """从YAML字符串加载"""
        pass
    
    def save(self, path: str) -> None:
        """保存到文件"""
        pass
    
    @classmethod
    def load(cls, path: str) -> 'BaseModel':
        """从文件加载"""
        pass
```

```python
# core/modules/base.py
"""
模块基类
功能：定义所有模块的通用接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseModule(ABC):
    """所有模块的基类"""
    
    def __init__(self, ai_client, prompt_engine, creator_profile):
        self.ai_client = ai_client
        self.prompt_engine = prompt_engine
        self.creator_profile = creator_profile
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Any:
        """
        执行模块逻辑
        
        Args:
            input_data: 模块输入数据
            
        Returns:
            模块输出数据
        """
        pass
    
    def build_prompt(self, template_name: str, context: Dict) -> str:
        """构建完整的prompt"""
        # 注入CreatorProfile
        context['creator_profile'] = self.creator_profile
        return self.prompt_engine.render(template_name, context)
```

```python
# core/orchestrator.py
"""
流程编排器
功能：协调各模块执行，管理数据流转，处理循环和异常
"""
class Orchestrator:
    """主流程编排器"""
    
    def __init__(self, project, config):
        self.project = project
        self.config = config
        self.modules = self._init_modules()
    
    def run(self) -> None:
        """执行完整流程"""
        # 1. 意图分析
        intent = self._run_intent_analysis()
        
        # 2. 消费者调研
        consumer_research = self._run_consumer_research(intent)
        
        # 3. 内涵设计（含选择）
        content_core = self._run_content_core_design(intent, consumer_research)
        
        # 4. 外延生产（含Simulator循环）
        extensions = self._run_extension_production(content_core)
        
        # 5. 输出结果
        self._output_results(extensions)
    
    def _run_with_loop(self, module, input_data, max_loops=3):
        """带循环控制的模块执行"""
        for i in range(max_loops):
            result = module.run(input_data)
            feedback = self.simulator.evaluate(result)
            
            if self._is_acceptable(feedback):
                return result
            
            # 注入反馈，准备下一轮
            input_data['previous_feedback'] = feedback
        
        # 达到最大循环次数，标记需要人介入
        raise LoopLimitExceeded(f"模块 {module.name} 循环次数达到上限")
```

### 4.3 AI客户端封装

```python
# core/ai_client.py
"""
AI API客户端
功能：封装AI调用，处理重试和错误
"""
import openai
from typing import Optional

class AIClient:
    """AI API调用封装"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def chat(
        self, 
        system_prompt: str, 
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        发送对话请求
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            AI响应文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def chat_with_history(
        self,
        system_prompt: str,
        messages: list,
        temperature: float = 0.7
    ) -> str:
        """支持多轮对话"""
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature
        )
        return response.choices[0].message.content
```

---

## 五、测试策略

### 5.1 单元测试

```yaml
测试范围:
  - 数据模型的序列化/反序列化
  - Prompt模板渲染
  - AI响应解析

不需要测试:
  - AI生成内容的质量（这是集成测试）
```

### 5.2 集成测试

```yaml
测试方式:
  - 使用mock的AI响应（预录制的响应）
  - 验证完整流程能跑通
  - 验证模块间数据传递正确

测试用例:
  - 正常流程：意图明确 → 顺利产出
  - 循环流程：Simulator拒绝 → 重新生成 → 通过
  - 异常流程：达到循环上限 → 抛出异常
```

### 5.3 端到端测试

```yaml
测试方式:
  - 使用真实AI
  - 人工验收输出质量

验收标准:
  - 输出内容可读、通顺
  - 符合CreatorProfile约束
  - 满足Intent定义的目标
```

---

## 六、配置示例

### 6.1 全局配置

```yaml
# config.yaml
ai:
  provider: "openai"  # openai | anthropic
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"  # 从环境变量读取
  temperature:
    default: 0.7
    creative: 0.9      # 用于方案生成
    precise: 0.3       # 用于格式化输出

storage:
  base_path: "./storage"
  creator_profiles_dir: "creator_profiles"
  projects_dir: "projects"

orchestrator:
  max_loops: 3
  loop_exit_threshold:
    critical_issues: 0
    major_issues: 2

defaults:
  project_depth: "standard"
  alternatives_count: 3
```

### 6.2 创作者特质示例

```yaml
# storage/creator_profiles/example_creator.yaml
id: "example_creator"
name: "范例创作者"

tone:
  formality: 3
  humor: 4
  energy: 4

stance:
  pragmatic_idealistic: 2
  neutral_radical: 2

taboos:
  forbidden_words: 
    - "躺赚"
    - "割韭菜"
    - "暴富"
  forbidden_topics:
    - "政治"
    - "宗教"
  forbidden_patterns:
    - "只需要...就能..."
    - "月入过万"

signatures:
  catchphrases:
    - "说白了就是"
    - "你品，你细品"
  preferred_structures:
    - "先说结论：...原因有三..."
    - "问题是...解法是...为什么管用..."
  preferred_metaphors:
    - 用做菜比喻复杂流程
    - 用装修比喻系统设计
  example_texts:
    - |
      说白了就是，很多人学东西学不会，不是因为笨，
      是因为他们总想一步到位。
      
      你品，你细品：小时候学骑车，有人一上来就想骑得飞快，
      结果摔得最惨；有人先学会平衡，再学会踩踏，最后才加速，
      反而最快学会。
      
      学习这事儿，慢就是快。
```

---

## 七、常见问题处理

### 7.1 AI输出格式错误

```yaml
问题: AI没有按YAML格式输出

处理:
  1. 追加提示："请严格按照指定YAML格式重新输出"
  2. 最多重试2次
  3. 仍然失败则记录日志，请求人工处理

预防:
  - 在prompt中提供输出示例
  - 使用structured output（如果API支持）
```

### 7.2 循环无法收敛

```yaml
问题: Simulator反复拒绝，循环达到上限

处理:
  1. 记录所有反馈历史
  2. 标记项目为"需要人介入"
  3. 生成诊断报告：
     - 哪些问题反复出现
     - AI尝试了什么修改
     - 建议的人工干预方向
```

### 7.3 意图不明确

```yaml
问题: 用户输入太模糊，无法提取明确意图

处理:
  1. 进入追问模式
  2. 最多追问3轮
  3. 仍不明确则：
     - 列出多个可能的解读
     - 请用户确认选择哪个
```

---

## 八、下一步规划

### MVP之后

```yaml
优先级1（完善单品类体验）:
  - 添加ConsumerResearch的standard/deep模式
  - 添加Report生成模块
  - 支持更多渠道（小红书、邮件）

优先级2（多品类扩展）:
  - 实现完整的FieldSchema体系
  - 添加"营销文"品类
  - 添加"课程设计"品类

优先级3（体验优化）:
  - Web界面
  - CreatorProfile自动学习（从历史内容提取）
  - 项目模板（快速启动常见场景）

优先级4（高级功能）:
  - 多项目管理
  - 团队协作
  - 版本控制和回滚
```



