"""
任务管理CLI命令
"""
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.models.task import TaskStatus, TaskPriority
from src.services.task_service import TaskService
from src.utils.date_utils import format_datetime, get_due_status, is_overdue

# 创建Rich控制台
console = Console()

# 任务服务实例
task_service = TaskService()


def add_task(
    title: str = typer.Argument(..., help="任务标题"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="任务描述"),
    priority: TaskPriority = typer.Option(TaskPriority.MEDIUM, "--priority", "-p", help="任务优先级"),
    status: TaskStatus = typer.Option(TaskStatus.PENDING, "--status", "-s", help="任务状态"),
    due_date: Optional[str] = typer.Option(None, "--due", help="截止时间(支持自然语言)")
):
    """添加新任务"""
    try:
        task = task_service.create_task(
            title=title,
            description=description,
            priority=priority,
            status=status,
            due_date=due_date
        )
        
        console.print("✅ 任务创建成功！", style="bold green")
        console.print(f"ID: {task.id}", style="dim")
        console.print(f"标题: {task.title}")
        if task.description:
            console.print(f"描述: {task.description}")
        console.print(f"优先级: {task.priority.value}")
        console.print(f"状态: {task.status.value}")
        if task.due_date:
            console.print(f"截止时间: {format_datetime(task.due_date)}")
        
    except Exception as e:
        console.print(f"❌ 创建任务失败: {e}", style="bold red")
        raise typer.Exit(1)


def list_tasks(
    status: Optional[TaskStatus] = typer.Option(None, "--status", "-s", help="筛选状态"),
    priority: Optional[TaskPriority] = typer.Option(None, "--priority", "-p", help="筛选优先级"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="限制显示数量"),
    all_tasks: bool = typer.Option(False, "--all", "-a", help="显示所有任务")
):
    """列出任务"""
    try:
        if all_tasks:
            tasks = task_service.list_tasks(limit=limit)
        else:
            # 默认只显示未完成的任务
            if status is None:
                tasks = [t for t in task_service.list_tasks(limit=limit) 
                        if t.status != TaskStatus.COMPLETED]
            else:
                tasks = task_service.list_tasks(status=status, priority=priority, limit=limit)
        
        if not tasks:
            console.print("📝 暂无任务", style="dim")
            return
        
        # 创建表格
        table = Table(title="📋 任务列表")
        table.add_column("ID", style="cyan", width=5)
        table.add_column("标题", style="white", width=30)
        table.add_column("状态", width=12)
        table.add_column("优先级", width=8)
        table.add_column("创建时间", style="dim", width=12)
        table.add_column("截止时间", width=15)
        
        for task in tasks:
            # 状态显示
            status_text = {
                TaskStatus.PENDING: "⏳ 待处理",
                TaskStatus.IN_PROGRESS: "🔄 进行中",
                TaskStatus.COMPLETED: "✅ 已完成",
                TaskStatus.CANCELLED: "❌ 已取消"
            }.get(task.status, task.status.value)
            
            # 优先级显示
            priority_text = {
                TaskPriority.HIGH: "🔴 高",
                TaskPriority.MEDIUM: "🟡 中",
                TaskPriority.LOW: "🟢 低"
            }.get(task.priority, task.priority.value)
            
            # 截止时间显示
            due_text = ""
            if task.due_date:
                due_text = format_datetime(task.due_date, "short")
                if is_overdue(task.due_date) and task.status != TaskStatus.COMPLETED:
                    due_text = f"[red]{due_text} (已过期)[/red]"
                elif get_due_status(task.due_date) == "今天到期":
                    due_text = f"[yellow]{due_text} (今天)[/yellow]"
            
            table.add_row(
                str(task.id),
                task.title[:27] + "..." if len(task.title) > 30 else task.title,
                status_text,
                priority_text,
                format_datetime(task.created_at, "short"),
                due_text
            )
        
        console.print(table)
        console.print(f"\n显示 {len(tasks)} 个任务", style="dim")
        
    except Exception as e:
        console.print(f"❌ 获取任务列表失败: {e}", style="bold red")
        raise typer.Exit(1)


def complete_task(
    task_id: int = typer.Argument(..., help="任务ID")
):
    """标记任务为完成"""
    try:
        task = task_service.complete_task(task_id)
        if not task:
            console.print(f"❌ 未找到ID为 {task_id} 的任务", style="bold red")
            raise typer.Exit(1)
        
        console.print(f"✅ 任务 '{task.title}' 已标记为完成！", style="bold green")
        console.print(f"完成时间: {format_datetime(task.completed_at)}", style="dim")
        
    except Exception as e:
        console.print(f"❌ 标记任务完成失败: {e}", style="bold red")
        raise typer.Exit(1)


def start_task(
    task_id: int = typer.Argument(..., help="任务ID")
):
    """开始任务"""
    try:
        task = task_service.start_task(task_id)
        if not task:
            console.print(f"❌ 未找到ID为 {task_id} 的任务", style="bold red")
            raise typer.Exit(1)
        
        console.print(f"🔄 任务 '{task.title}' 已开始！", style="bold green")
        console.print(f"开始时间: {format_datetime(task.start_time)}", style="dim")
        
    except Exception as e:
        console.print(f"❌ 开始任务失败: {e}", style="bold red")
        raise typer.Exit(1)


def show_task(
    task_id: int = typer.Argument(..., help="任务ID")
):
    """显示任务详情"""
    try:
        task = task_service.get_task(task_id)
        if not task:
            console.print(f"❌ 未找到ID为 {task_id} 的任务", style="bold red")
            raise typer.Exit(1)
        
        # 创建详情面板
        details = []
        details.append(f"[bold]ID:[/bold] {task.id}")
        details.append(f"[bold]标题:[/bold] {task.title}")
        
        if task.description:
            details.append(f"[bold]描述:[/bold] {task.description}")
        
        status_icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.CANCELLED: "❌"
        }
        details.append(f"[bold]状态:[/bold] {status_icons.get(task.status, '')} {task.status.value}")
        
        priority_icons = {
            TaskPriority.HIGH: "🔴",
            TaskPriority.MEDIUM: "🟡",
            TaskPriority.LOW: "🟢"
        }
        details.append(f"[bold]优先级:[/bold] {priority_icons.get(task.priority, '')} {task.priority.value}")
        
        details.append(f"[bold]创建时间:[/bold] {format_datetime(task.created_at)}")
        
        if task.start_time:
            details.append(f"[bold]开始时间:[/bold] {format_datetime(task.start_time)}")
        
        if task.due_date:
            due_status = get_due_status(task.due_date)
            due_text = format_datetime(task.due_date)
            if due_status:
                due_text += f" ({due_status})"
            details.append(f"[bold]截止时间:[/bold] {due_text}")
        
        if task.completed_at:
            details.append(f"[bold]完成时间:[/bold] {format_datetime(task.completed_at)}")
        
        details.append(f"[bold]更新时间:[/bold] {format_datetime(task.updated_at)}")
        
        if task.tags:
            details.append(f"[bold]标签:[/bold] {task.tags}")
        
        panel = Panel(
            "\n".join(details),
            title=f"📋 任务详情",
            border_style="blue"
        )
        console.print(panel)
        
    except Exception as e:
        console.print(f"❌ 获取任务详情失败: {e}", style="bold red")
        raise typer.Exit(1)


def update_task(
    task_id: int = typer.Argument(..., help="任务ID"),
    title: Optional[str] = typer.Option(None, "--title", help="新标题"),
    description: Optional[str] = typer.Option(None, "--desc", help="新描述"),
    priority: Optional[TaskPriority] = typer.Option(None, "--priority", help="新优先级"),
    due_date: Optional[str] = typer.Option(None, "--due", help="新截止时间"),
    status: Optional[TaskStatus] = typer.Option(None, "--status", help="新状态")
):
    """更新任务信息"""
    try:
        # 构建更新字典
        updates = {}
        if title:
            updates["title"] = title
        if description:
            updates["description"] = description
        if priority:
            updates["priority"] = priority
        if due_date:
            updates["due_date"] = due_date
        if status:
            updates["status"] = status
        
        if not updates:
            console.print("❌ 请至少指定一个要更新的字段", style="bold red")
            raise typer.Exit(1)
        
        task = task_service.update_task(task_id, **updates)
        if not task:
            console.print(f"❌ 未找到ID为 {task_id} 的任务", style="bold red")
            raise typer.Exit(1)
        
        console.print(f"✅ 任务 '{task.title}' 更新成功！", style="bold green")
        
        # 显示更新的字段
        for key, value in updates.items():
            console.print(f"  {key}: {value}", style="dim")
        
    except Exception as e:
        console.print(f"❌ 更新任务失败: {e}", style="bold red")
        raise typer.Exit(1)


def delete_task(
    task_id: int = typer.Argument(..., help="任务ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除，不询问确认")
):
    """删除任务"""
    try:
        # 先获取任务信息
        task = task_service.get_task(task_id)
        if not task:
            console.print(f"❌ 未找到ID为 {task_id} 的任务", style="bold red")
            raise typer.Exit(1)
        
        # 确认删除
        if not force:
            confirm = typer.confirm(f"确定要删除任务 '{task.title}' 吗？")
            if not confirm:
                console.print("取消删除", style="dim")
                return
        
        success = task_service.delete_task(task_id)
        if success:
            console.print(f"✅ 任务 '{task.title}' 已删除", style="bold green")
        else:
            console.print("❌ 删除任务失败", style="bold red")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"❌ 删除任务失败: {e}", style="bold red")
        raise typer.Exit(1)


def search_tasks(
    keyword: str = typer.Argument(..., help="搜索关键词"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="限制结果数量")
):
    """搜索任务"""
    try:
        tasks = task_service.search_tasks(keyword)
        
        if limit:
            tasks = tasks[:limit]
        
        if not tasks:
            console.print(f"🔍 未找到包含 '{keyword}' 的任务", style="dim")
            return
        
        console.print(f"🔍 搜索结果 (关键词: '{keyword}'):", style="bold")
        
        # 重用list_tasks的表格显示逻辑
        table = Table()
        table.add_column("ID", style="cyan", width=5)
        table.add_column("标题", style="white", width=30)
        table.add_column("状态", width=12)
        table.add_column("优先级", width=8)
        table.add_column("创建时间", style="dim", width=12)
        
        for task in tasks:
            status_text = {
                TaskStatus.PENDING: "⏳ 待处理",
                TaskStatus.IN_PROGRESS: "🔄 进行中",
                TaskStatus.COMPLETED: "✅ 已完成",
                TaskStatus.CANCELLED: "❌ 已取消"
            }.get(task.status, task.status.value)
            
            priority_text = {
                TaskPriority.HIGH: "🔴 高",
                TaskPriority.MEDIUM: "🟡 中",
                TaskPriority.LOW: "🟢 低"
            }.get(task.priority, task.priority.value)
            
            # 高亮关键词
            highlighted_title = task.title.replace(
                keyword, f"[bold yellow]{keyword}[/bold yellow]"
            )
            
            table.add_row(
                str(task.id),
                highlighted_title[:27] + "..." if len(task.title) > 30 else highlighted_title,
                status_text,
                priority_text,
                format_datetime(task.created_at, "short")
            )
        
        console.print(table)
        console.print(f"\n找到 {len(tasks)} 个结果", style="dim")
        
    except Exception as e:
        console.print(f"❌ 搜索任务失败: {e}", style="bold red")
        raise typer.Exit(1) 