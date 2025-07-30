"""
Tag management commands.

This module implements all tag-related CLI commands.
"""

from typing import Optional
import typer
from rich.table import Table
from sqlalchemy.orm import Session

from todo.database import get_session
from todo.models.tag import Tag
from todo.utils.display import print_success, print_error, print_info, console

# 创建标签子命令组
app = typer.Typer(help="Tag management commands", no_args_is_help=True)


@app.command("add")
def add_tag(
    name: str = typer.Argument(..., help="Tag name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Tag description"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="Tag color (hex code, e.g., #FF5733)")
):
    """Add a new tag."""
    db = get_session()
    try:
        # 检查标签是否已存在
        existing = db.query(Tag).filter(Tag.name == name).first()
        if existing:
            print_error(f"Tag '{name}' already exists")
            raise typer.Exit(1)
        
        # 验证颜色格式
        if color and not color.startswith('#'):
            color = f"#{color}"
        
        if color and len(color) != 7:
            print_error("Color must be a valid hex code (e.g., #FF5733)")
            raise typer.Exit(1)
        
        # 创建标签
        tag = Tag(
            name=name,
            description=description,
            color=color
        )
        
        db.add(tag)
        db.commit()
        db.refresh(tag)
        
        print_success(f"Tag '{name}' created successfully with ID: {tag.id}")
        
    except Exception as e:
        db.rollback()
        print_error(f"Failed to create tag: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("list")
def list_tags():
    """List all tags."""
    db = get_session()
    try:
        tags = db.query(Tag).order_by(Tag.name).all()
        
        if not tags:
            print_info("No tags found")
            return
        
        # 创建表格
        table = Table(title="Tags", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True, width=4)
        table.add_column("Name", style="white", min_width=15)
        table.add_column("Description", style="dim", min_width=20)
        table.add_column("Color", style="yellow", width=8)
        table.add_column("Tasks", style="green", width=6)
        table.add_column("Created", style="dim", width=12)
        
        for tag in tags:
            color_display = tag.color if tag.color else "-"
            description_display = tag.description[:30] + "..." if tag.description and len(tag.description) > 30 else (tag.description or "-")
            
            table.add_row(
                str(tag.id),
                tag.name,
                description_display,
                color_display,
                str(tag.task_count),
                tag.created_at.strftime("%Y-%m-%d") if tag.created_at else "-"
            )
        
        console.print(table)
        
    except Exception as e:
        print_error(f"Failed to list tags: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("delete")
def delete_tag(
    name: str = typer.Argument(..., help="Tag name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete without confirmation")
):
    """Delete a tag."""
    db = get_session()
    try:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            print_error(f"Tag '{name}' not found")
            raise typer.Exit(1)
        
        # 检查是否有关联的任务
        if tag.task_count > 0 and not force:
            print_error(f"Tag '{name}' is used by {tag.task_count} tasks. Use --force to delete anyway.")
            raise typer.Exit(1)
        
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete tag '{name}'?")
            if not confirm:
                print_info("Tag deletion cancelled")
                return
        
        db.delete(tag)
        db.commit()
        print_success(f"Tag '{name}' deleted successfully")
        
    except Exception as e:
        db.rollback()
        print_error(f"Failed to delete tag: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command("update")
def update_tag(
    name: str = typer.Argument(..., help="Tag name to update"),
    new_name: Optional[str] = typer.Option(None, "--name", help="New tag name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New description"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="New color (hex code)")
):
    """Update a tag."""
    db = get_session()
    try:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            print_error(f"Tag '{name}' not found")
            raise typer.Exit(1)
        
        updated = False
        
        if new_name:
            # 检查新名称是否已存在
            existing = db.query(Tag).filter(Tag.name == new_name).first()
            if existing and existing.id != tag.id:
                print_error(f"Tag '{new_name}' already exists")
                raise typer.Exit(1)
            tag.name = new_name
            updated = True
        
        if description is not None:
            tag.description = description
            updated = True
        
        if color:
            if not color.startswith('#'):
                color = f"#{color}"
            if len(color) != 7:
                print_error("Color must be a valid hex code (e.g., #FF5733)")
                raise typer.Exit(1)
            tag.color = color
            updated = True
        
        if not updated:
            print_info("No changes specified")
            return
        
        db.commit()
        print_success(f"Tag updated successfully")
        
    except Exception as e:
        db.rollback()
        print_error(f"Failed to update tag: {e}")
        raise typer.Exit(1)
    finally:
        db.close()
