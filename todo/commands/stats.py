"""
Statistics and reporting commands.

This module implements statistics, reporting, and data import/export functionality.
"""

import json
import csv
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import typer
from rich.table import Table
from rich.panel import Panel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from todo.database import get_session
from todo.models.task import Task, TaskStatus, TaskPriority
from todo.models.category import Category
from todo.models.tag import Tag
from todo.utils.display import print_success, print_error, print_info, console

# 创建统计子命令组
app = typer.Typer(help="Statistics and reporting commands", no_args_is_help=True)


@app.command("overview")
def show_overview():
    """Show overall task statistics."""
    db = get_session()
    try:
        # 基本统计
        total_tasks = db.query(Task).count()
        completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        cancelled_tasks = db.query(Task).filter(Task.status == TaskStatus.CANCELLED).count()
        
        # 过期任务
        overdue_tasks = db.query(Task).filter(
            and_(
                Task.due_date < datetime.now(),
                Task.status != TaskStatus.COMPLETED
            )
        ).count()
        
        # 优先级统计
        urgent_tasks = db.query(Task).filter(
            and_(
                Task.priority == TaskPriority.URGENT,
                Task.status != TaskStatus.COMPLETED
            )
        ).count()
        
        high_tasks = db.query(Task).filter(
            and_(
                Task.priority == TaskPriority.HIGH,
                Task.status != TaskStatus.COMPLETED
            )
        ).count()
        
        # 分类统计
        categories_count = db.query(Category).count()
        tags_count = db.query(Tag).count()
        
        # 完成率
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 创建统计表格
        stats_table = Table(title="Task Statistics Overview", show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan", min_width=20)
        stats_table.add_column("Count", style="white", width=10)
        stats_table.add_column("Percentage", style="green", width=12)
        
        # 添加统计行
        stats_table.add_row("Total Tasks", str(total_tasks), "100%")
        stats_table.add_row("✅ Completed", str(completed_tasks), f"{completion_rate:.1f}%")
        stats_table.add_row("⏳ Pending", str(pending_tasks), f"{(pending_tasks/total_tasks*100) if total_tasks > 0 else 0:.1f}%")
        stats_table.add_row("🔄 In Progress", str(in_progress_tasks), f"{(in_progress_tasks/total_tasks*100) if total_tasks > 0 else 0:.1f}%")
        stats_table.add_row("❌ Cancelled", str(cancelled_tasks), f"{(cancelled_tasks/total_tasks*100) if total_tasks > 0 else 0:.1f}%")
        stats_table.add_row("⚠️ Overdue", str(overdue_tasks), "-")
        stats_table.add_row("🔴 Urgent", str(urgent_tasks), "-")
        stats_table.add_row("🟠 High Priority", str(high_tasks), "-")
        stats_table.add_row("📁 Categories", str(categories_count), "-")
        stats_table.add_row("🏷️ Tags", str(tags_count), "-")
        
        console.print(stats_table)
        
        # 显示趋势信息
        if total_tasks > 0:
            # 最近7天创建的任务
            week_ago = datetime.now() - timedelta(days=7)
            recent_tasks = db.query(Task).filter(Task.created_at >= week_ago).count()
            
            # 最近7天完成的任务
            recent_completed = db.query(Task).filter(
                and_(
                    Task.completed_at >= week_ago,
                    Task.status == TaskStatus.COMPLETED
                )
            ).count()
            
            trend_info = f"📈 Recent Activity (Last 7 days): {recent_tasks} created, {recent_completed} completed"
            console.print(Panel(trend_info, title="Trends", border_style="blue"))
        
    except Exception as e:
        print_error(f"Failed to generate overview: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("categories")
def category_stats():
    """Show statistics by category."""
    db = get_session()
    try:
        # 查询每个分类的任务统计 - 使用分别查询的方式避免复杂的case语句
        categories = db.query(Category).all()
        category_stats = []

        for category in categories:
            total = db.query(Task).filter(Task.category_id == category.id).count()
            completed = db.query(Task).filter(
                Task.category_id == category.id,
                Task.status == TaskStatus.COMPLETED
            ).count()
            pending = db.query(Task).filter(
                Task.category_id == category.id,
                Task.status == TaskStatus.PENDING
            ).count()
            in_progress = db.query(Task).filter(
                Task.category_id == category.id,
                Task.status == TaskStatus.IN_PROGRESS
            ).count()

            # 创建一个简单的对象来模拟原来的查询结果
            class CategoryStat:
                def __init__(self, name, total, completed, pending, in_progress):
                    self.name = name
                    self.total = total
                    self.completed = completed
                    self.pending = pending
                    self.in_progress = in_progress

            if total > 0:  # 只包含有任务的分类
                category_stats.append(CategoryStat(category.name, total, completed, pending, in_progress))
        
        # 无分类任务
        uncategorized = db.query(Task).filter(Task.category_id.is_(None)).count()
        uncategorized_completed = db.query(Task).filter(
            and_(Task.category_id.is_(None), Task.status == TaskStatus.COMPLETED)
        ).count()
        
        if not category_stats and uncategorized == 0:
            print_info("No categories or tasks found")
            return
        
        # 创建分类统计表格
        table = Table(title="Statistics by Category", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan", min_width=15)
        table.add_column("Total", style="white", width=8)
        table.add_column("Completed", style="green", width=10)
        table.add_column("Pending", style="yellow", width=8)
        table.add_column("In Progress", style="blue", width=12)
        table.add_column("Completion %", style="magenta", width=12)
        
        for stat in category_stats:
            completion_pct = (stat.completed / stat.total * 100) if stat.total > 0 else 0
            table.add_row(
                stat.name,
                str(stat.total),
                str(stat.completed),
                str(stat.pending),
                str(stat.in_progress),
                f"{completion_pct:.1f}%"
            )
        
        # 添加无分类任务
        if uncategorized > 0:
            uncategorized_pct = (uncategorized_completed / uncategorized * 100) if uncategorized > 0 else 0
            table.add_row(
                "[No Category]",
                str(uncategorized),
                str(uncategorized_completed),
                str(uncategorized - uncategorized_completed),
                "0",
                f"{uncategorized_pct:.1f}%"
            )
        
        console.print(table)

    except Exception as e:
        print_error(f"Failed to generate category statistics: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("export")
def export_data(
    format: str = typer.Option("json", "--format", "-f", help="Export format: json or csv"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    include_completed: bool = typer.Option(True, "--include-completed", help="Include completed tasks"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Export only specific category")
):
    """Export tasks to JSON or CSV format."""
    db = get_session()
    try:
        # 构建查询
        query = db.query(Task)

        if not include_completed:
            query = query.filter(Task.status != TaskStatus.COMPLETED)

        if category:
            query = query.join(Category).filter(Category.name == category)

        tasks = query.all()

        if not tasks:
            print_info("No tasks to export")
            return

        # 生成输出文件名
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"todo_export_{timestamp}.{format}"

        output_path = Path(output)

        if format.lower() == "json":
            export_to_json(tasks, output_path)
        elif format.lower() == "csv":
            export_to_csv(tasks, output_path)
        else:
            print_error("Unsupported format. Use 'json' or 'csv'")
            raise typer.Exit(1)

        print_success(f"Exported {len(tasks)} tasks to {output_path}")

    except Exception as e:
        print_error(f"Failed to export data: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


def export_to_json(tasks: List[Task], output_path: Path):
    """Export tasks to JSON format."""
    data = []

    for task in tasks:
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "category": task.category.name if task.category else None,
            "tags": [tag.name for tag in task.tags] if task.tags else []
        }
        data.append(task_data)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_to_csv(tasks: List[Task], output_path: Path):
    """Export tasks to CSV format."""
    fieldnames = [
        'id', 'title', 'description', 'status', 'priority',
        'created_at', 'updated_at', 'due_date', 'completed_at',
        'category', 'tags'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for task in tasks:
            row = {
                'id': task.id,
                'title': task.title,
                'description': task.description or '',
                'status': task.status.value,
                'priority': task.priority.value,
                'created_at': task.created_at.isoformat() if task.created_at else '',
                'updated_at': task.updated_at.isoformat() if task.updated_at else '',
                'due_date': task.due_date.isoformat() if task.due_date else '',
                'completed_at': task.completed_at.isoformat() if task.completed_at else '',
                'category': task.category.name if task.category else '',
                'tags': ', '.join([tag.name for tag in task.tags]) if task.tags else ''
            }
            writer.writerow(row)


@app.command("import")
def import_data(
    file_path: str = typer.Argument(..., help="Path to import file (JSON or CSV)"),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="File format: json or csv (auto-detect if not specified)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview import without making changes"),
    skip_existing: bool = typer.Option(True, "--skip-existing", help="Skip tasks with existing titles")
):
    """Import tasks from JSON or CSV file."""
    import_path = Path(file_path)

    if not import_path.exists():
        print_error(f"File not found: {file_path}")
        raise typer.Exit(1)

    # 自动检测格式
    if not format:
        format = import_path.suffix.lower().lstrip('.')
        if format not in ['json', 'csv']:
            print_error("Cannot detect file format. Please specify --format")
            raise typer.Exit(1)

    db = get_session()
    try:
        if format == "json":
            imported_count = import_from_json(db, import_path, dry_run, skip_existing)
        elif format == "csv":
            imported_count = import_from_csv(db, import_path, dry_run, skip_existing)
        else:
            print_error("Unsupported format. Use 'json' or 'csv'")
            raise typer.Exit(1)

        if dry_run:
            print_info(f"Dry run: Would import {imported_count} tasks")
        else:
            print_success(f"Successfully imported {imported_count} tasks")

    except Exception as e:
        db.rollback()
        print_error(f"Failed to import data: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


def import_from_json(db: Session, file_path: Path, dry_run: bool, skip_existing: bool) -> int:
    """Import tasks from JSON file."""
    from utils.helpers import parse_priority, parse_status, parse_date

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    imported_count = 0

    for item in data:
        title = item.get('title')
        if not title:
            continue

        # 检查是否已存在
        if skip_existing:
            existing = db.query(Task).filter(Task.title == title).first()
            if existing:
                continue

        if not dry_run:
            # 创建任务
            task = Task(
                title=title,
                description=item.get('description'),
                status=parse_status(item.get('status', 'pending')),
                priority=parse_priority(item.get('priority', 'medium'))
            )

            # 处理日期
            if item.get('due_date'):
                try:
                    task.due_date = datetime.fromisoformat(item['due_date'].replace('Z', '+00:00'))
                except:
                    pass

            # 处理分类
            if item.get('category'):
                category = db.query(Category).filter(Category.name == item['category']).first()
                if category:
                    task.category = category

            # 处理标签
            if item.get('tags'):
                for tag_name in item['tags']:
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if tag:
                        task.tags.append(tag)

            db.add(task)

        imported_count += 1

    if not dry_run:
        db.commit()

    return imported_count


def import_from_csv(db: Session, file_path: Path, dry_run: bool, skip_existing: bool) -> int:
    """Import tasks from CSV file."""
    from utils.helpers import parse_priority, parse_status

    imported_count = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            title = row.get('title')
            if not title:
                continue

            # 检查是否已存在
            if skip_existing:
                existing = db.query(Task).filter(Task.title == title).first()
                if existing:
                    continue

            if not dry_run:
                # 创建任务
                task = Task(
                    title=title,
                    description=row.get('description') or None,
                    status=parse_status(row.get('status', 'pending')),
                    priority=parse_priority(row.get('priority', 'medium'))
                )

                # 处理日期
                if row.get('due_date'):
                    try:
                        task.due_date = datetime.fromisoformat(row['due_date'])
                    except:
                        pass

                # 处理分类
                if row.get('category'):
                    category = db.query(Category).filter(Category.name == row['category']).first()
                    if category:
                        task.category = category

                # 处理标签
                if row.get('tags'):
                    tag_names = [tag.strip() for tag in row['tags'].split(',') if tag.strip()]
                    for tag_name in tag_names:
                        tag = db.query(Tag).filter(Tag.name == tag_name).first()
                        if tag:
                            task.tags.append(tag)

                db.add(task)

            imported_count += 1

    if not dry_run:
        db.commit()

    return imported_count
