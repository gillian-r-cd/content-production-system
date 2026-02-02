# api/main.py
# FastAPI应用入口
# 功能：定义API路由、中间件、CORS配置

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# 修复空BASE_URL问题
if os.getenv("OPENAI_BASE_URL") == "":
    os.environ.pop("OPENAI_BASE_URL", None)

from api.routes import projects, profiles, workflow, settings, logs, schemas, simulators, channels


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("[API] Content Production System starting...")
    yield
    # 关闭时
    print("[API] Shutting down...")


app = FastAPI(
    title="内容生产系统 API",
    description="以终为始的内容生产系统后端API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS配置（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(profiles.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["Workflow"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(schemas.router, prefix="/api/schemas", tags=["Schemas"])
app.include_router(simulators.router, prefix="/api/simulators", tags=["Simulators"])
app.include_router(channels.router, prefix="/api/channels", tags=["Channels"])


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "内容生产系统 API 运行中"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "内容生产系统 API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# 静态文件（前端构建产物）
web_dist = project_root / "web" / "dist"
if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

