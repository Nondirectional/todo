"""
Main entry point for the Todo CLI application.

This module sets up the main Typer application and registers all subcommands.
"""

import typer
from rich.console import Console

from todo.commands import task, category, tag, stats, chat
from todo.database import init_db

# 创建主应用实例
app = typer.Typer(
    name="todo",
    no_args_is_help=True,
    help="A powerful CLI todo task management tool",
    rich_markup_mode="rich",
)

# 创建控制台实例用于美化输出
console = Console()

# 注册子命令组
app.add_typer(task.app, name="task", help="Task management commands", no_args_is_help=True)
app.add_typer(category.app, name="category", help="Category management commands", no_args_is_help=True)
app.add_typer(tag.app, name="tag", help="Tag management commands", no_args_is_help=True)
app.add_typer(stats.app, name="stats", help="Statistics and reporting commands", no_args_is_help=True)
app.add_typer(chat.app, name="chat", help="Interactive AI chat for todo management", no_args_is_help=True)


@app.callback()
def main():
    """
    Todo CLI - A powerful command-line todo task management tool.
    
    Use subcommands to manage your tasks, categories, and tags efficiently.
    """
    # 确保数据库已初始化
    init_db()


@app.command()
def init():
    """Initialize the todo database and configuration."""
    try:
        init_db()
        console.print("✅ Todo database initialized successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Failed to initialize database: {e}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
