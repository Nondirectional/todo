"""
Category management commands.

This module implements all category-related CLI commands.
"""

from typing import Optional
import typer
from rich.table import Table
from sqlalchemy.orm import Session

from todo.database import get_session
from todo.models.category import Category
from todo.utils.display import print_success, print_error, print_info, console

# 创建分类子命令组
app = typer.Typer(help="Category management commands", no_args_is_help=True)


@app.command("add")
def add_category(
    name: str = typer.Argument(..., help="Category name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Category description"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="Category color (hex code, e.g., #FF5733)")
):
    """Add a new category."""
    db = get_session()
    try:
        # 检查分类是否已存在
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            print_error(f"Category '{name}' already exists")
            raise typer.Exit(1)
        
        # 验证颜色格式
        if color and not color.startswith('#'):
            color = f"#{color}"
        
        if color and len(color) != 7:
            print_error("Color must be a valid hex code (e.g., #FF5733)")
            raise typer.Exit(1)
        
        # 创建分类
        category = Category(
            name=name,
            description=description,
            color=color
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        print_success(f"Category '{name}' created successfully with ID: {category.id}")
        
    except Exception as e:
        db.rollback()
        print_error(f"Failed to create category: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("list")
def list_categories():
    """List all categories."""
    db = get_session()
    try:
        categories = db.query(Category).order_by(Category.name).all()
        
        if not categories:
            print_info("No categories found")
            return
        
        # 创建表格
        table = Table(title="Categories", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True, width=4)
        table.add_column("Name", style="white", min_width=15)
        table.add_column("Description", style="dim", min_width=20)
        table.add_column("Color", style="yellow", width=8)
        table.add_column("Tasks", style="green", width=6)
        table.add_column("Created", style="dim", width=12)
        
        for category in categories:
            color_display = category.color if category.color else "-"
            description_display = category.description[:30] + "..." if category.description and len(category.description) > 30 else (category.description or "-")
            
            table.add_row(
                str(category.id),
                category.name,
                description_display,
                color_display,
                str(category.task_count),
                category.created_at.strftime("%Y-%m-%d") if category.created_at else "-"
            )
        
        console.print(table)
        
    except Exception as e:
        print_error(f"Failed to list categories: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("delete")
def delete_category(
    name: str = typer.Argument(..., help="Category name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete without confirmation")
):
    """Delete a category."""
    db = get_session()
    try:
        category = db.query(Category).filter(Category.name == name).first()
        if not category:
            print_error(f"Category '{name}' not found")
            raise typer.Exit(1)
        
        # 检查是否有关联的任务
        if category.task_count > 0 and not force:
            print_error(f"Category '{name}' has {category.task_count} associated tasks. Use --force to delete anyway.")
            raise typer.Exit(1)
        
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete category '{name}'?")
            if not confirm:
                print_info("Category deletion cancelled")
                return
        
        db.delete(category)
        db.commit()
        print_success(f"Category '{name}' deleted successfully")
        
    except Exception as e:
        db.rollback()
        print_error(f"Failed to delete category: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("update")
def update_category(
    name: str = typer.Argument(..., help="Category name to update"),
    new_name: Optional[str] = typer.Option(None, "--name", help="New category name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New description"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="New color (hex code)")
):
    """Update a category."""
    db = get_session()
    try:
        category = db.query(Category).filter(Category.name == name).first()
        if not category:
            print_error(f"Category '{name}' not found")
            raise typer.Exit(1)
        
        updated = False
        
        if new_name:
            # 检查新名称是否已存在
            existing = db.query(Category).filter(Category.name == new_name).first()
            if existing and existing.id != category.id:
                print_error(f"Category '{new_name}' already exists")
                raise typer.Exit(1)
            category.name = new_name
            updated = True
        
        if description is not None:
            category.description = description
            updated = True
        
        if color:
            if not color.startswith('#'):
                color = f"#{color}"
            if len(color) != 7:
                print_error("Color must be a valid hex code (e.g., #FF5733)")
                raise typer.Exit(1)
            category.color = color
            updated = True
        
        if not updated:
            print_info("No changes specified")
            return
        
        db.commit()
        print_success(f"Category updated successfully")
        
    except Exception as e:
        db.rollback()
        print_error(f"Failed to update category: {e}")
        raise typer.Exit(1)
    finally:
        db.close()
