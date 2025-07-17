"""
Todo CLI应用主入口
"""
import typer
from rich.console import Console
from rich.table import Table

from ..models.database import init_db
from ..services.task_service import TaskService
from . import task_commands
from . import ai_commands

# 创建Typer应用
app = typer.Typer(
    name="todo",
    help="🚀 一个强大的命令行待办管理工具，具备AI助手功能",
    no_args_is_help=True
)

# 创建Rich控制台
console = Console()

# 任务服务实例
task_service = TaskService()


@app.callback()
def main():
    """
    🚀 Todo CLI - 智能任务管理工具
    
    使用AI助手帮助你更好地管理任务和生成报告。
    """
    # 初始化数据库
    init_db()


# 注册基础任务管理命令
app.command(name="add", help="添加新任务")(task_commands.add_task)
app.command(name="list", help="列出任务")(task_commands.list_tasks) 
app.command(name="show", help="显示任务详情")(task_commands.show_task)
app.command(name="complete", help="标记任务完成")(task_commands.complete_task)
app.command(name="start", help="开始任务")(task_commands.start_task)
app.command(name="update", help="更新任务")(task_commands.update_task)
app.command(name="delete", help="删除任务")(task_commands.delete_task)
app.command(name="search", help="搜索任务")(task_commands.search_tasks)

# 便捷别名
app.command(name="ls")(task_commands.list_tasks)  # list别名
app.command(name="rm")(task_commands.delete_task)  # delete别名
app.command(name="done")(task_commands.complete_task)  # complete别名

# 注册AI功能命令
app.command(name="chat", help="🤖 与AI助手对话")(ai_commands.chat_command)
app.command(name="smart-add", help="🤖 AI智能添加任务")(ai_commands.smart_add_command)
app.command(name="report", help="📊 生成AI工作日报")(ai_commands.report_command)
app.command(name="ai-setup", help="🔧 设置AI助手")(ai_commands.setup_command)


@app.command(name="version")
def show_version():
    """显示版本信息"""
    from .. import __version__
    console.print(f"Todo CLI 版本: {__version__}", style="bold green")


@app.command(name="init")
def init_command():
    """初始化Todo应用"""
    try:
        init_db()
        console.print("✅ Todo应用初始化成功！", style="bold green")
        console.print("数据库文件位置: ~/.todo/todo.db", style="dim")
        console.print("\n🚀 开始使用:", style="bold")
        console.print("  todo add '学习Python'    # 添加任务")
        console.print("  todo list                # 查看任务")
        console.print("  todo chat                # AI助手对话")
        console.print("  todo smart-add '任务描述' # AI智能添加")
        console.print("  todo report              # 生成AI日报")
        console.print("  todo --help             # 查看所有命令")
    except Exception as e:
        console.print(f"❌ 初始化失败: {e}", style="bold red")
        raise typer.Exit(1)


@app.command(name="stats")
def show_stats():
    """显示任务统计信息"""
    try:
        from ..models.task import TaskStatus
        
        pending = len(task_service.list_tasks(status=TaskStatus.PENDING))
        in_progress = len(task_service.list_tasks(status=TaskStatus.IN_PROGRESS))
        completed = len(task_service.list_tasks(status=TaskStatus.COMPLETED))
        cancelled = len(task_service.list_tasks(status=TaskStatus.CANCELLED))
        
        total = pending + in_progress + completed + cancelled
        
        if total == 0:
            console.print("📊 暂无任务数据", style="dim")
            return
        
        # 创建统计表格
        table = Table(title="📊 任务统计")
        table.add_column("状态", style="white")
        table.add_column("数量", style="cyan")
        table.add_column("百分比", style="green")
        
        def add_stat_row(status, count, icon):
            percentage = f"{count/total*100:.1f}%" if total > 0 else "0%"
            table.add_row(f"{icon} {status}", str(count), percentage)
        
        add_stat_row("待处理", pending, "⏳")
        add_stat_row("进行中", in_progress, "🔄")
        add_stat_row("已完成", completed, "✅")
        add_stat_row("已取消", cancelled, "❌")
        add_stat_row("总计", total, "📋")
        
        console.print(table)
        
        # 完成率
        if total > 0:
            completion_rate = completed / total * 100
            console.print(f"\n完成率: {completion_rate:.1f}%", style="bold green")
        
    except Exception as e:
        console.print(f"❌ 获取统计信息失败: {e}", style="bold red")
        raise typer.Exit(1)


@app.command(name="features")
def show_features():
    """显示功能特性说明"""
    console.print("🎯 Todo CLI 功能特性", style="bold blue")
    console.print()
    
    # 基础功能
    console.print("📋 [bold green]基础任务管理[/bold green]")
    console.print("  • add/list/show/update/delete - 完整CRUD操作")
    console.print("  • start/complete - 任务状态管理")
    console.print("  • search - 任务搜索")
    console.print("  • stats - 统计信息")
    console.print()
    
    # AI功能
    console.print("🤖 [bold cyan]AI智能助手[/bold cyan]")
    console.print("  • chat - 自然语言对话管理任务")
    console.print("  • smart-add - AI智能解析任务描述")
    console.print("  • report - AI生成工作日报")
    console.print("  • ai-setup - AI助手配置向导")
    console.print()
    
    # 特色功能
    console.print("✨ [bold yellow]特色功能[/bold yellow]")
    console.print("  • 自然语言时间解析 (tomorrow, next week)")
    console.print("  • 过期任务提醒")
    console.print("  • 美观的表格界面")
    console.print("  • 数据持久化存储")
    console.print("  • 便捷命令别名 (ls, rm, done)")
    console.print()
    
    console.print("💡 [bold]提示[/bold]: 使用 'todo <命令> --help' 查看详细用法")


if __name__ == "__main__":
    app() 