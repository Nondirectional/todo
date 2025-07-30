"""
Display utilities for rich console output.
"""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Confirm
from rich.align import Align
from rich.columns import Columns
from rich.tree import Tree
from datetime import datetime, timedelta
from todo.models.task import Task, TaskStatus, TaskPriority
from todo.utils.helpers import format_date, format_priority, format_status, truncate_text

console = Console()


def print_success(message: str):
    """打印成功消息"""
    console.print(f"✅ {message}", style="green")


def print_error(message: str):
    """打印错误消息"""
    console.print(f"❌ {message}", style="red")


def print_info(message: str):
    """打印信息消息"""
    console.print(f"ℹ️  {message}", style="blue")


def print_warning(message: str):
    """打印警告消息"""
    console.print(f"⚠️  {message}", style="yellow")


def create_task_table(tasks: List[Task], title: str = "Tasks", compact: bool = False) -> Table:
    """创建任务表格"""
    table = Table(title=title, show_header=True, header_style="bold magenta", show_lines=True)

    if compact:
        # 紧凑模式
        table.add_column("ID", style="cyan", no_wrap=True, width=4)
        table.add_column("Title", style="white", min_width=30)
        table.add_column("Status", style="green", width=10)
        table.add_column("Priority", style="yellow", width=8)
        table.add_column("Due", style="red", width=10)
    else:
        # 完整模式
        table.add_column("ID", style="cyan", no_wrap=True, width=4)
        table.add_column("Title", style="white", min_width=25)
        table.add_column("Status", style="green", width=12)
        table.add_column("Priority", style="yellow", width=10)
        table.add_column("Category", style="blue", width=12)
        table.add_column("Tags", style="magenta", width=15)
        table.add_column("Due Date", style="red", width=12)
        table.add_column("Created", style="dim", width=12)
    
    # 添加行
    for task in tasks:
        # 处理标签显示
        tags_str = ", ".join([tag.name for tag in task.tags]) if task.tags else ""
        tags_display = truncate_text(tags_str, 15) if tags_str else "-"

        # 处理分类显示
        category_display = task.category.name if task.category else "-"

        # 处理截止日期显示和颜色
        due_date_display = "-"
        due_date_style = "dim"
        if task.due_date:
            due_date_display = format_date(task.due_date)
            # 检查是否过期
            if task.due_date < datetime.now() and task.status != TaskStatus.COMPLETED:
                due_date_style = "bold red"
            elif task.due_date < datetime.now() + timedelta(days=1):
                due_date_style = "bold yellow"

        # 根据任务状态设置行样式
        row_style = None
        if task.status == TaskStatus.COMPLETED:
            row_style = "dim"
        elif task.status == TaskStatus.CANCELLED:
            row_style = "strike dim"

        if compact:
            table.add_row(
                str(task.id),
                truncate_text(task.title, 40),
                format_status(task.status),
                format_priority(task.priority),
                f"[{due_date_style}]{due_date_display}[/{due_date_style}]",
                style=row_style
            )
        else:
            table.add_row(
                str(task.id),
                truncate_text(task.title, 30),
                format_status(task.status),
                format_priority(task.priority),
                truncate_text(category_display, 12),
                tags_display,
                f"[{due_date_style}]{due_date_display}[/{due_date_style}]",
                format_date(task.created_at),
                style=row_style
            )
    
    return table


def display_task_detail(task: Task):
    """显示任务详细信息"""
    # 创建详细信息面板
    details = []
    details.append(f"[bold]ID:[/bold] {task.id}")
    details.append(f"[bold]Title:[/bold] {task.title}")
    details.append(f"[bold]Status:[/bold] {format_status(task.status)}")
    details.append(f"[bold]Priority:[/bold] {format_priority(task.priority)}")
    
    if task.description:
        details.append(f"[bold]Description:[/bold] {task.description}")
    
    if task.category:
        details.append(f"[bold]Category:[/bold] {task.category.name}")
    
    if task.tags:
        tags_str = ", ".join([tag.name for tag in task.tags])
        details.append(f"[bold]Tags:[/bold] {tags_str}")
    
    details.append(f"[bold]Created:[/bold] {format_date(task.created_at)}")
    details.append(f"[bold]Updated:[/bold] {format_date(task.updated_at)}")
    
    if task.due_date:
        details.append(f"[bold]Due Date:[/bold] {format_date(task.due_date)}")
    
    if task.completed_at:
        details.append(f"[bold]Completed:[/bold] {format_date(task.completed_at)}")
    
    panel = Panel(
        "\n".join(details),
        title=f"Task #{task.id}",
        border_style="blue"
    )
    
    console.print(panel)


def display_tasks_summary(tasks: List[Task]):
    """显示任务摘要统计"""
    if not tasks:
        print_info("No tasks found.")
        return
    
    # 统计信息
    total = len(tasks)
    completed = len([t for t in tasks if t.status.value == "completed"])
    pending = len([t for t in tasks if t.status.value == "pending"])
    in_progress = len([t for t in tasks if t.status.value == "in_progress"])
    
    summary = f"Total: {total} | ✅ Completed: {completed} | ⏳ Pending: {pending} | 🔄 In Progress: {in_progress}"
    
    console.print(Panel(summary, title="Summary", border_style="green"))
    
    # 显示任务表格
    table = create_task_table(tasks)
    console.print(table)


def display_task_tree(tasks: List[Task], group_by: str = "category"):
    """以树形结构显示任务"""
    if not tasks:
        print_info("No tasks found.")
        return

    tree = Tree("📋 Tasks", style="bold blue")

    if group_by == "category":
        # 按分类分组
        categories = {}
        uncategorized = []

        for task in tasks:
            if task.category:
                cat_name = task.category.name
                if cat_name not in categories:
                    categories[cat_name] = []
                categories[cat_name].append(task)
            else:
                uncategorized.append(task)

        # 添加分类节点
        for cat_name, cat_tasks in categories.items():
            cat_node = tree.add(f"📁 {cat_name} ({len(cat_tasks)})")
            for task in cat_tasks:
                status_icon = get_status_icon(task.status)
                priority_icon = get_priority_icon(task.priority)
                cat_node.add(f"{status_icon} {priority_icon} {task.title}")

        # 添加无分类任务
        if uncategorized:
            uncat_node = tree.add(f"📂 Uncategorized ({len(uncategorized)})")
            for task in uncategorized:
                status_icon = get_status_icon(task.status)
                priority_icon = get_priority_icon(task.priority)
                uncat_node.add(f"{status_icon} {priority_icon} {task.title}")

    elif group_by == "status":
        # 按状态分组
        status_groups = {}
        for task in tasks:
            status = task.status.value
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(task)

        for status, status_tasks in status_groups.items():
            status_node = tree.add(f"{format_status(TaskStatus(status))} ({len(status_tasks)})")
            for task in status_tasks:
                priority_icon = get_priority_icon(task.priority)
                status_node.add(f"{priority_icon} {task.title}")

    console.print(tree)


def get_status_icon(status: TaskStatus) -> str:
    """获取状态图标"""
    icons = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.CANCELLED: "❌"
    }
    return icons.get(status, "❓")


def get_priority_icon(priority: TaskPriority) -> str:
    """获取优先级图标"""
    icons = {
        TaskPriority.LOW: "🟢",
        TaskPriority.MEDIUM: "🟡",
        TaskPriority.HIGH: "🟠",
        TaskPriority.URGENT: "🔴"
    }
    return icons.get(priority, "⚪")


def show_progress_bar(current: int, total: int, description: str = "Progress"):
    """显示进度条"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(description, total=total)
        progress.update(task, completed=current)


def display_dashboard(tasks: List[Task]):
    """显示仪表板视图"""
    if not tasks:
        print_info("No tasks found.")
        return

    # 统计信息
    total = len(tasks)
    completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    pending = len([t for t in tasks if t.status == TaskStatus.PENDING])
    in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    overdue = len([t for t in tasks if t.due_date and t.due_date < datetime.now() and t.status != TaskStatus.COMPLETED])

    # 创建统计面板
    stats_panels = []

    # 总任务数
    stats_panels.append(
        Panel(
            Align.center(f"[bold cyan]{total}[/bold cyan]\nTotal Tasks"),
            border_style="cyan"
        )
    )

    # 已完成
    completion_rate = (completed / total * 100) if total > 0 else 0
    stats_panels.append(
        Panel(
            Align.center(f"[bold green]{completed}[/bold green]\nCompleted\n[dim]{completion_rate:.1f}%[/dim]"),
            border_style="green"
        )
    )

    # 进行中
    stats_panels.append(
        Panel(
            Align.center(f"[bold blue]{in_progress}[/bold blue]\nIn Progress"),
            border_style="blue"
        )
    )

    # 待处理
    stats_panels.append(
        Panel(
            Align.center(f"[bold yellow]{pending}[/bold yellow]\nPending"),
            border_style="yellow"
        )
    )

    # 过期
    if overdue > 0:
        stats_panels.append(
            Panel(
                Align.center(f"[bold red]{overdue}[/bold red]\nOverdue"),
                border_style="red"
            )
        )

    # 显示统计面板
    console.print(Columns(stats_panels, equal=True, expand=True))
    console.print()

    # 显示最近的任务
    recent_tasks = sorted(tasks, key=lambda t: t.created_at or datetime.min, reverse=True)[:5]
    if recent_tasks:
        console.print(Panel("📋 Recent Tasks", style="bold magenta"))
        recent_table = create_task_table(recent_tasks, title="", compact=True)
        console.print(recent_table)


def confirm_action(message: str, default: bool = False) -> bool:
    """确认操作"""
    return Confirm.ask(message, default=default)
