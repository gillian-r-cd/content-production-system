# 内容生产系统 (Content Production System)

以终为始的内容生产系统 —— 把意图变成可用内容。

## 核心理念

```
用户输入：我想要什么效果（意图）
系统输出：可以直接用的内容（成品）
```

### 关键概念

| 概念 | 含义 |
|------|------|
| **内涵** | 核心内容的完整生产（如：整套课程素材） |
| **外延** | 内涵完成后的营销触达（如：介绍页、推广文案） |
| **CreatorProfile** | 创作者特质，全局约束所有内容的风格 |
| **FieldSchema** | 用户自定义的内容品类和字段结构 |
| **Simulator** | AI模拟目标用户，评估内容质量 |

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API

```bash
# 复制环境变量模板
copy env.example .env    # Windows
# cp env.example .env    # Linux/Mac

# 编辑.env文件，填入你的OpenAI API Key
# OPENAI_API_KEY=sk-xxxxxx
```

### 3. 启动服务

#### 后端 (FastAPI)

```bash
# 激活虚拟环境后
uvicorn api.main:app --reload --port 8000

# 后端运行在 http://localhost:8000
# API文档: http://localhost:8000/docs
```

#### 前端 (React + Vite)

```bash
# 进入前端目录
cd web

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev

# 前端运行在 http://localhost:5174
```

#### 同时启动

```bash
# 终端1 - 后端
.\venv\Scripts\Activate.ps1  # Windows
uvicorn api.main:app --reload --port 8000

# 终端2 - 前端
cd web
npm run dev
```

### 4. CLI工具（可选）

```bash
# 查看帮助
python -m ui.cli --help

# 创建CreatorProfile
python -m ui.cli profile create

# 创建项目
python -m ui.cli project create

# 运行项目
python -m ui.cli run <project_id>
```

## 项目结构

```
/content_production_system/
├── .env                     # 环境变量（API密钥等）
├── config.yaml              # 全局配置
├── requirements.txt         # Python依赖
│
├── /api/                    # FastAPI 后端
│   ├── main.py              # 应用入口
│   └── routes/              # API路由
│       ├── workflow.py      # 工作流API
│       ├── profiles.py      # 创作者特质API
│       ├── projects.py      # 项目API
│       └── schemas.py       # 字段模板API
│
├── /web/                    # React 前端
│   ├── package.json         # 前端依赖
│   └── src/
│       ├── components/      # UI组件
│       ├── stores/          # Zustand状态管理
│       └── api/             # API客户端
│
├── /core/                   # 核心业务逻辑
│   ├── models/              # 数据模型
│   ├── modules/             # 业务模块
│   ├── ai_client.py         # AI API封装
│   ├── context_manager.py   # 上下文管理
│   └── orchestrator.py      # 流程编排
│
├── /config/
│   └── prompts/             # Prompt模板（Jinja2）
│
├── /storage/                # 运行时数据
│   ├── creator_profiles/    # 创作者特质
│   ├── projects/            # 项目数据
│   └── field_schemas/       # 字段模板
│
└── /tests/                  # 测试
```

## 数据流

```
CreatorProfile（全局约束）
        ↓
Intent → ConsumerResearch → ContentCore → ContentExtension
                                 ↓              ↓
                            Simulator ←────────┘
                                 ↓
                              Report
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_models.py

# 查看覆盖率
pytest --cov=core
```

### 开发文档

详细设计文档在 `/docs/` 目录：

- `architecture.md` - 系统架构
- `context_management.md` - 上下文管理
- `ai_prompting_guide.md` - Prompt设计
- `implementation_guide.md` - 实施指南

## License

MIT



