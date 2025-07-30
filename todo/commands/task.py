"""
Task management commands.

This module implements all task-related CLI commands including add, list, update, delete, and complete.
"""

from typing import Optional, List
from datetime import datetime
import typer
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from todo.database import get_session
from todo.models.task import Task, TaskStatus, TaskPriority
from todo.models.category import Category
from todo.models.tag import Tag
from todo.utils.display import (
    display_tasks_summary, display_task_detail, display_task_tree, display_dashboard,
    print_success, print_error, print_info, confirm_action
)
from todo.utils.helpers import parse_priority, parse_status, parse_date

# 创建任务子命令组
app = typer.Typer(help="Task management commands", no_args_is_help=True)


@app.command("add")
def add_task(
    title: str = typer.Argument(..., help="Task title"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Task description"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Task priority (low/medium/high/urgent)"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Category name"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
    due_date: Optional[str] = typer.Option(None, "--due", help="Due date (YYYY-MM-DD or YYYY-MM-DD HH:MM)")
):
    """Add a new task."""
    db = get_session()
    try:
        # 解析优先级
        task_priority = parse_priority(priority)
        
        # 解析截止日期
        task_due_date = None
        if due_date:
            try:
                task_due_date = parse_date(due_date)
            except ValueError as e:
                print_error(f"Invalid due date format: {e}")
                raise typer.Exit(1)
        
        # 创建任务
        task = Task(
            title=title,
            description=description,
            priority=task_priority,
            due_date=task_due_date
        )
        
        # 处理分类
        if category:
            db_category = db.query(Category).filter(Category.name == category).first()
            if not db_category:
                print_error(f"Category '{category}' not found. Create it first with: todo category add '{category}'")
                raise typer.Exit(1)
            task.category = db_category
        
        # 处理标签
        if tags:
            tag_names = [tag.strip() for tag in tags.split(",")]
            for tag_name in tag_names:
                db_tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not db_tag:
                    print_error(f"Tag '{tag_name}' not found. Create it first with: todo tag add '{tag_name}'")
                    raise typer.Exit(1)
                task.tags.append(db_tag)
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        print_success(f"Task created successfully with ID: {task.id}")
        display_task_detail(task)
        
    except Exception as e:
        db.rollback()
        print_error(f"Failed to create task: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("list")
def list_tasks(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of tasks to show"),
    all_tasks: bool = typer.Option(False, "--all", "-a", help="Show all tasks including completed")
):
    """List tasks with optional filters."""
    db = get_session()
    try:
        # 构建查询
        query = db.query(Task)

        # 状态过滤
        if status:
            task_status = parse_status(status)
            query = query.filter(Task.status == task_status)
        elif not all_tasks:
            # 默认不显示已完成和已取消的任务
            query = query.filter(Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))

        # 分类过滤
        if category:
            query = query.join(Category).filter(Category.name == category)

        # 标签过滤
        if tag:
            query = query.join(Task.tags).filter(Tag.name == tag)

        # 优先级过滤
        if priority:
            task_priority = parse_priority(priority)
            query = query.filter(Task.priority == task_priority)

        # 排序和限制
        query = query.order_by(Task.created_at.desc()).limit(limit)

        tasks = query.all()
        display_tasks_summary(tasks)

    except Exception as e:
        print_error(f"Failed to list tasks: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("search")
def search_tasks(
    query: Optional[str] = typer.Argument(None, help="Search query (searches in title and description)"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    due_before: Optional[str] = typer.Option(None, "--due-before", help="Tasks due before date (YYYY-MM-DD)"),
    due_after: Optional[str] = typer.Option(None, "--due-after", help="Tasks due after date (YYYY-MM-DD)"),
    created_before: Optional[str] = typer.Option(None, "--created-before", help="Tasks created before date"),
    created_after: Optional[str] = typer.Option(None, "--created-after", help="Tasks created after date"),
    overdue: bool = typer.Option(False, "--overdue", help="Show only overdue tasks"),
    no_category: bool = typer.Option(False, "--no-category", help="Show tasks without category"),
    no_tags: bool = typer.Option(False, "--no-tags", help="Show tasks without tags"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of tasks to show"),
    sort_by: str = typer.Option("created", "--sort", help="Sort by: created, updated, due, priority, title"),
    reverse: bool = typer.Option(False, "--reverse", "-r", help="Reverse sort order")
):
    """Advanced search for tasks with multiple filters."""
    db = get_session()
    try:
        # 构建查询
        db_query = db.query(Task)

        # 文本搜索
        if query:
            search_filter = or_(
                Task.title.ilike(f"%{query}%"),
                Task.description.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)

        # 状态过滤
        if status:
            task_status = parse_status(status)
            db_query = db_query.filter(Task.status == task_status)

        # 分类过滤
        if category:
            db_query = db_query.join(Category).filter(Category.name == category)
        elif no_category:
            db_query = db_query.filter(Task.category_id.is_(None))

        # 标签过滤
        if tag:
            db_query = db_query.join(Task.tags).filter(Tag.name == tag)
        elif no_tags:
            db_query = db_query.filter(~Task.tags.any())

        # 优先级过滤
        if priority:
            task_priority = parse_priority(priority)
            db_query = db_query.filter(Task.priority == task_priority)

        # 日期过滤
        if due_before:
            try:
                due_before_date = parse_date(due_before)
                db_query = db_query.filter(Task.due_date <= due_before_date)
            except ValueError as e:
                print_error(f"Invalid due_before date: {e}")
                raise typer.Exit(1)

        if due_after:
            try:
                due_after_date = parse_date(due_after)
                db_query = db_query.filter(Task.due_date >= due_after_date)
            except ValueError as e:
                print_error(f"Invalid due_after date: {e}")
                raise typer.Exit(1)

        if created_before:
            try:
                created_before_date = parse_date(created_before)
                db_query = db_query.filter(Task.created_at <= created_before_date)
            except ValueError as e:
                print_error(f"Invalid created_before date: {e}")
                raise typer.Exit(1)

        if created_after:
            try:
                created_after_date = parse_date(created_after)
                db_query = db_query.filter(Task.created_at >= created_after_date)
            except ValueError as e:
                print_error(f"Invalid created_after date: {e}")
                raise typer.Exit(1)

        # 过期任务过滤
        if overdue:
            from datetime import datetime
            db_query = db_query.filter(
                and_(
                    Task.due_date < datetime.now(),
                    Task.status != TaskStatus.COMPLETED
                )
            )

        # 排序
        sort_options = {
            "created": Task.created_at,
            "updated": Task.updated_at,
            "due": Task.due_date,
            "priority": Task.priority,
            "title": Task.title
        }

        sort_column = sort_options.get(sort_by, Task.created_at)
        if reverse:
            db_query = db_query.order_by(sort_column.asc())
        else:
            db_query = db_query.order_by(sort_column.desc())

        # 限制结果数量
        db_query = db_query.limit(limit)

        tasks = db_query.all()

        if query:
            title = f"Search Results for '{query}'"
        else:
            title = "Filtered Tasks"

        if not tasks:
            print_info("No tasks found matching the criteria")
            return

        display_tasks_summary(tasks)

    except Exception as e:
        print_error(f"Failed to search tasks: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("show")
def show_task(
    task_id: int = typer.Argument(..., help="Task ID to show")
):
    """Show detailed information about a specific task."""
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print_error(f"Task with ID {task_id} not found")
            raise typer.Exit(1)

        display_task_detail(task)

    except Exception as e:
        print_error(f"Failed to show task: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("complete")
def complete_task(
    task_id: int = typer.Argument(..., help="Task ID to complete")
):
    """Mark a task as completed."""
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print_error(f"Task with ID {task_id} not found")
            raise typer.Exit(1)

        if task.status == TaskStatus.COMPLETED:
            print_info(f"Task {task_id} is already completed")
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        db.commit()
        print_success(f"Task {task_id} marked as completed")
        display_task_detail(task)

    except Exception as e:
        db.rollback()
        print_error(f"Failed to complete task: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("delete")
def delete_task(
    task_id: int = typer.Argument(..., help="Task ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete without confirmation")
):
    """Delete a task."""
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print_error(f"Task with ID {task_id} not found")
            raise typer.Exit(1)

        if not force:
            if not confirm_action(f"Are you sure you want to delete task '{task.title}'?"):
                print_info("Task deletion cancelled")
                return

        db.delete(task)
        db.commit()
        print_success(f"Task {task_id} deleted successfully")

    except Exception as e:
        db.rollback()
        print_error(f"Failed to delete task: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("update")
def update_task(
    task_id: int = typer.Argument(..., help="Task ID to update"),
    title: Optional[str] = typer.Option(None, "--title", help="New task title"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New task description"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="New task priority"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New task status"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="New category name"),
    due_date: Optional[str] = typer.Option(None, "--due", help="New due date"),
    clear_due: bool = typer.Option(False, "--clear-due", help="Clear due date"),
    clear_category: bool = typer.Option(False, "--clear-category", help="Clear category")
):
    """Update task properties."""
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print_error(f"Task with ID {task_id} not found")
            raise typer.Exit(1)

        updated = False

        # 更新标题
        if title:
            task.title = title
            updated = True

        # 更新描述
        if description:
            task.description = description
            updated = True

        # 更新优先级
        if priority:
            task.priority = parse_priority(priority)
            updated = True

        # 更新状态
        if status:
            task.status = parse_status(status)
            if task.status == TaskStatus.COMPLETED and not task.completed_at:
                task.completed_at = datetime.now()
            updated = True

        # 更新分类
        if category:
            db_category = db.query(Category).filter(Category.name == category).first()
            if not db_category:
                print_error(f"Category '{category}' not found")
                raise typer.Exit(1)
            task.category = db_category
            updated = True

        if clear_category:
            task.category = None
            updated = True

        # 更新截止日期
        if due_date:
            try:
                task.due_date = parse_date(due_date)
                updated = True
            except ValueError as e:
                print_error(f"Invalid due date format: {e}")
                raise typer.Exit(1)

        if clear_due:
            task.due_date = None
            updated = True

        if not updated:
            print_info("No changes specified")
            return

        task.updated_at = datetime.now()
        db.commit()
        print_success(f"Task {task_id} updated successfully")
        display_task_detail(task)

    except Exception as e:
        db.rollback()
        print_error(f"Failed to update task: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("tree")
def tree_view(
    group_by: str = typer.Option("category", "--group-by", "-g", help="Group by: category or status"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of tasks to show")
):
    """Display tasks in a tree view grouped by category or status."""
    db = get_session()
    try:
        # 构建查询
        query = db.query(Task)

        if status:
            task_status = parse_status(status)
            query = query.filter(Task.status == task_status)
        else:
            # 默认不显示已完成和已取消的任务
            query = query.filter(Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))

        query = query.order_by(Task.created_at.desc()).limit(limit)
        tasks = query.all()

        display_task_tree(tasks, group_by)

    except Exception as e:
        print_error(f"Failed to display tree view: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("dashboard")
def dashboard_view(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category")
):
    """Display a dashboard overview of tasks."""
    db = get_session()
    try:
        # 构建查询
        query = db.query(Task)

        if status:
            task_status = parse_status(status)
            query = query.filter(Task.status == task_status)

        if category:
            query = query.join(Category).filter(Category.name == category)

        tasks = query.all()
        display_dashboard(tasks)

    except Exception as e:
        print_error(f"Failed to display dashboard: {e}")
        raise typer.Exit(1)
    finally:
        db.close()
