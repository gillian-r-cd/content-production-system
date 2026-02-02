# api/routes/logs.py
# AI调用日志API
# 功能：查询AI调用历史记录，用于调试

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.models import log_store

router = APIRouter()


class AICallLogResponse(BaseModel):
    """AI调用日志响应"""
    id: str
    project_id: Optional[str]
    stage: str
    timestamp: str
    duration_ms: int
    
    system_prompt: str
    user_message: str
    full_prompt: str
    
    response: str
    
    model: str
    temperature: float
    tokens_input: int
    tokens_output: int
    
    success: bool
    error: Optional[str]


@router.get("", response_model=List[AICallLogResponse])
async def list_logs(
    project_id: Optional[str] = Query(None, description="按项目ID筛选"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=200),
):
    """
    获取AI调用日志列表
    
    支持按项目ID筛选，默认返回最近50条
    """
    if project_id:
        logs = log_store.get_by_project(project_id)
    else:
        logs = log_store.get_recent(limit)
    
    return [
        AICallLogResponse(
            id=log.id,
            project_id=log.project_id,
            stage=log.stage,
            timestamp=log.timestamp.isoformat(),
            duration_ms=log.duration_ms,
            system_prompt=log.system_prompt,
            user_message=log.user_message,
            full_prompt=log.full_prompt,
            response=log.response,
            model=log.model,
            temperature=log.temperature,
            tokens_input=log.tokens_input,
            tokens_output=log.tokens_output,
            success=log.success,
            error=log.error,
        )
        for log in logs[:limit]
    ]


@router.get("/summary")
async def get_logs_summary():
    """
    获取日志摘要统计
    """
    all_logs = log_store.get_all()
    
    total_calls = len(all_logs)
    successful_calls = sum(1 for log in all_logs if log.success)
    total_tokens = sum(log.tokens_input + log.tokens_output for log in all_logs)
    total_duration = sum(log.duration_ms for log in all_logs)
    
    # 按阶段统计
    stage_stats = {}
    for log in all_logs:
        if log.stage not in stage_stats:
            stage_stats[log.stage] = {"count": 0, "tokens": 0, "duration_ms": 0}
        stage_stats[log.stage]["count"] += 1
        stage_stats[log.stage]["tokens"] += log.tokens_input + log.tokens_output
        stage_stats[log.stage]["duration_ms"] += log.duration_ms
    
    return {
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": total_calls - successful_calls,
        "total_tokens": total_tokens,
        "total_duration_ms": total_duration,
        "avg_duration_ms": total_duration // total_calls if total_calls > 0 else 0,
        "stage_stats": stage_stats,
    }


@router.delete("")
async def clear_logs():
    """清空所有日志"""
    log_store.clear()
    return {"message": "日志已清空"}



