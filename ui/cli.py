# ui/cli.py
# 功能：命令行界面入口
# 主要命令：profile, project, run
# 核心能力：创作者管理、项目管理、交互式内容生产

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
import yaml
from datetime import datetime

from core.models import (
    Project, CreatorProfile, Taboos,
    FieldSchema, FieldDefinition,
)
from core.ai_client import AIClient, MockAIClient
from core.prompt_engine import PromptEngine
from core.orchestrator import Orchestrator, OrchestratorConfig


# 创建CLI应用
app = typer.Typer(
    name="content-prod",
    help="内容生产系统 - 以终为始的AI内容生产工具",
    add_completion=False,
)

# 子命令组
profile_app = typer.Typer(help="创作者特质管理")
project_app = typer.Typer(help="项目管理")

app.add_typer(profile_app, name="profile")
app.add_typer(project_app, name="project")

# Rich控制台
console = Console()

# 配置
CONFIG_PATH = Path("config.yaml")
STORAGE_PATH = Path("storage")


def load_config() -> dict:
    """加载配置"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def ensure_storage_dirs():
    """确保存储目录存在"""
    (STORAGE_PATH / "creator_profiles").mkdir(parents=True, exist_ok=True)
    (STORAGE_PATH / "projects").mkdir(parents=True, exist_ok=True)


# ===== Profile 命令 =====

@profile_app.command("create")
def profile_create(
    name: str = typer.Option(None, "--name", "-n", help="创作者名称"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="交互模式"),
):
    """创建新的创作者特质"""
    ensure_storage_dirs()
    
    if interactive:
        console.print(Panel("创建创作者特质", style="bold blue"))
        
        if not name:
            name = Prompt.ask("请输入创作者名称")
        
        # 收集禁忌词
        forbidden_words = []
        console.print("\n[yellow]禁用词汇（不想在内容中出现的词，输入空行结束）：[/yellow]")
        while True:
            word = Prompt.ask("禁用词", default="")
            if not word:
                break
            forbidden_words.append(word)
        
        # 收集范例文本
        example_texts = []
        console.print("\n[yellow]范例文本（你的典型风格文本，输入空行结束）：[/yellow]")
        while True:
            text = Prompt.ask("范例", default="")
            if not text:
                break
            example_texts.append(text)
        
        # 收集自定义字段
        custom_fields = {}
        console.print("\n[yellow]自定义特质（如调性、写作习惯等，输入空行结束）：[/yellow]")
        while True:
            key = Prompt.ask("特质名", default="")
            if not key:
                break
            value = Prompt.ask(f"{key}的值")
            custom_fields[key] = value
    else:
        if not name:
            console.print("[red]非交互模式需要指定 --name[/red]")
            raise typer.Exit(1)
        forbidden_words = []
        example_texts = []
        custom_fields = {}
    
    # 创建Profile
    profile_id = f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    profile = CreatorProfile(
        id=profile_id,
        name=name,
        example_texts=example_texts,
        taboos=Taboos(
            id="taboos",
            forbidden_words=forbidden_words,
        ),
        custom_fields=custom_fields,
    )
    
    # 保存
    save_path = STORAGE_PATH / "creator_profiles" / f"{profile_id}.yaml"
    profile.save(save_path)
    
    console.print(f"\n[green]创作者特质已创建：{profile_id}[/green]")
    console.print(f"  保存路径：{save_path}")


@profile_app.command("list")
def profile_list():
    """列出所有创作者特质"""
    ensure_storage_dirs()
    
    profiles_dir = STORAGE_PATH / "creator_profiles"
    profiles = list(profiles_dir.glob("*.yaml"))
    
    if not profiles:
        console.print("[yellow]暂无创作者特质，使用 'profile create' 创建[/yellow]")
        return
    
    table = Table(title="创作者特质列表")
    table.add_column("ID", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("禁用词数", justify="right")
    table.add_column("范例数", justify="right")
    
    for profile_path in profiles:
        try:
            profile = CreatorProfile.load(profile_path)
            table.add_row(
                profile.id,
                profile.name,
                str(len(profile.taboos.forbidden_words)),
                str(len(profile.example_texts)),
            )
        except Exception as e:
            table.add_row(profile_path.stem, "[red]加载失败[/red]", "-", "-")
    
    console.print(table)


@profile_app.command("show")
def profile_show(
    profile_id: str = typer.Argument(..., help="创作者ID"),
):
    """显示创作者特质详情"""
    profile_path = STORAGE_PATH / "creator_profiles" / f"{profile_id}.yaml"
    
    if not profile_path.exists():
        console.print(f"[red]找不到创作者：{profile_id}[/red]")
        raise typer.Exit(1)
    
    profile = CreatorProfile.load(profile_path)
    
    console.print(Panel(f"创作者：{profile.name}", style="bold blue"))
    console.print(profile.format_for_prompt())


# ===== Project 命令 =====

@project_app.command("create")
def project_create(
    name: str = typer.Option(None, "--name", "-n", help="项目名称"),
    profile_id: str = typer.Option(None, "--profile", "-p", help="关联的创作者ID"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="交互模式"),
):
    """创建新项目"""
    ensure_storage_dirs()
    
    if interactive:
        console.print(Panel("创建新项目", style="bold blue"))
        
        if not name:
            name = Prompt.ask("请输入项目名称")
        
        # 选择创作者
        if not profile_id:
            profiles_dir = STORAGE_PATH / "creator_profiles"
            profiles = list(profiles_dir.glob("*.yaml"))
            
            if not profiles:
                console.print("[yellow]请先创建创作者特质（profile create）[/yellow]")
                raise typer.Exit(1)
            
            console.print("\n可用的创作者：")
            for i, p in enumerate(profiles, 1):
                try:
                    profile = CreatorProfile.load(p)
                    console.print(f"  {i}. {profile.id} - {profile.name}")
                except:
                    pass
            
            choice = Prompt.ask("选择创作者（输入序号）", default="1")
            profile_id = profiles[int(choice) - 1].stem
    else:
        if not name or not profile_id:
            console.print("[red]非交互模式需要指定 --name 和 --profile[/red]")
            raise typer.Exit(1)
    
    # 创建Project
    project_id = f"proj_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    project = Project(
        id=project_id,
        name=name,
        creator_profile_id=profile_id,
    )
    
    # 保存
    project_dir = STORAGE_PATH / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    project.save(project_dir / "project.yaml")
    
    console.print(f"\n[green]项目已创建：{project_id}[/green]")
    console.print(f"  保存路径：{project_dir}")


@project_app.command("list")
def project_list():
    """列出所有项目"""
    ensure_storage_dirs()
    
    projects_dir = STORAGE_PATH / "projects"
    projects = [d for d in projects_dir.iterdir() if d.is_dir()]
    
    if not projects:
        console.print("[yellow]暂无项目，使用 'project create' 创建[/yellow]")
        return
    
    table = Table(title="项目列表")
    table.add_column("ID", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("阶段", style="yellow")
    table.add_column("创建时间")
    
    for project_dir in projects:
        project_file = project_dir / "project.yaml"
        if project_file.exists():
            try:
                project = Project.load(project_file)
                table.add_row(
                    project.id,
                    project.name,
                    project.get_stage_display_name(),
                    project.created_at.strftime("%Y-%m-%d %H:%M"),
                )
            except Exception as e:
                table.add_row(project_dir.name, "[red]加载失败[/red]", "-", "-")
    
    console.print(table)


# ===== Run 命令 =====

@app.command("run")
def run_project(
    project_id: str = typer.Argument(None, help="项目ID（可选，不指定则创建新项目）"),
    mock: bool = typer.Option(False, "--mock", help="使用Mock AI（测试模式）"),
):
    """运行内容生产流程"""
    ensure_storage_dirs()
    config = load_config()
    
    console.print(Panel("内容生产系统", style="bold blue"))
    
    # 加载或创建项目
    if project_id:
        project_dir = STORAGE_PATH / "projects" / project_id
        if not project_dir.exists():
            console.print(f"[red]找不到项目：{project_id}[/red]")
            raise typer.Exit(1)
        project = Project.load(project_dir / "project.yaml")
    else:
        # 交互式创建项目
        name = Prompt.ask("请输入项目名称")
        
        # 选择创作者
        profiles_dir = STORAGE_PATH / "creator_profiles"
        profiles = list(profiles_dir.glob("*.yaml"))
        
        if not profiles:
            console.print("[yellow]请先创建创作者特质（profile create）[/yellow]")
            raise typer.Exit(1)
        
        console.print("\n可用的创作者：")
        for i, p in enumerate(profiles, 1):
            try:
                profile = CreatorProfile.load(p)
                console.print(f"  {i}. {profile.name}")
            except:
                pass
        
        choice = Prompt.ask("选择创作者", default="1")
        profile_id = profiles[int(choice) - 1].stem
        
        project_id = f"proj_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        project = Project(
            id=project_id,
            name=name,
            creator_profile_id=profile_id,
        )
    
    # 加载创作者
    profile_path = STORAGE_PATH / "creator_profiles" / f"{project.creator_profile_id}.yaml"
    if not profile_path.exists():
        console.print(f"[red]找不到创作者：{project.creator_profile_id}[/red]")
        raise typer.Exit(1)
    
    creator_profile = CreatorProfile.load(profile_path)
    
    console.print(f"\n项目：{project.name}")
    console.print(f"创作者：{creator_profile.name}")
    
    # 创建AI客户端
    if mock:
        console.print("[yellow]使用Mock模式[/yellow]")
        ai_client = MockAIClient({})
    else:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[red]请设置OPENAI_API_KEY环境变量[/red]")
            raise typer.Exit(1)
        ai_client = AIClient(api_key=api_key)
    
    # 创建编排器
    prompt_engine = PromptEngine(Path("config/prompts"))
    orchestrator = Orchestrator(
        ai_client=ai_client,
        prompt_engine=prompt_engine,
    )
    
    # 注册事件回调
    orchestrator.on("stage_changed", lambda d: console.print(f"\n[blue]>> 进入阶段：{d['stage']}[/blue]"))
    orchestrator.on("content_generated", lambda d: console.print(f"[green]内容生成完成[/green]"))
    orchestrator.on("evaluation_done", lambda d: console.print(f"  评估得分：{d['score']}/10"))
    
    # 创建项目状态
    state = orchestrator.create_project_state(
        project=project,
        creator_profile=creator_profile,
    )
    
    # 交互式回调
    def interactive_callback(prompt: str) -> str:
        return Prompt.ask(prompt)
    
    # 获取初始输入
    console.print("\n[bold]【意图分析】请描述你想要生产的内容：[/bold]")
    console.print("[dim]（AI可能会追问1-3个问题来澄清需求）[/dim]")
    initial_input = Prompt.ask(">")
    
    # 运行流程
    console.print("\n[bold]开始意图分析...[/bold]\n")
    
    try:
        final_state = orchestrator.run_full_flow(
            state=state,
            initial_input=initial_input,
            interactive_callback=interactive_callback,
        )
        
        # 保存结果
        save_path = orchestrator.save_state(final_state)
        
        console.print(f"\n[green]项目完成！[/green]")
        console.print(f"  AI调用次数：{final_state.ai_call_count}")
        console.print(f"  保存路径：{save_path}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]已中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]错误：{e}[/red]")
        raise


# ===== 主入口 =====

@app.command("version")
def version():
    """显示版本信息"""
    console.print("内容生产系统 v0.1.0")


@app.callback()
def main():
    """内容生产系统 - 以终为始的AI内容生产工具"""
    pass


if __name__ == "__main__":
    app()

