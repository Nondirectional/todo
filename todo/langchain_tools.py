"""
Langchain 工具方法模块

将 Todo CLI 的功能封装为 Langchain 工具，支持 AI 集成调用。
包含任务、分类、标签的完整 CRUD 操作。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from todo.database import get_session
from todo.models.task import Task, TaskStatus, TaskPriority
from todo.models.category import Category
from todo.models.tag import Tag


# ==================== 通用工具 ====================
@tool
def current_datetime():
    """获取当前日期时间"""
    return datetime.now().isoformat()


# ==================== 任务管理工具 ====================

@tool
def add_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    category: Optional[str] = None,
    tags: Optional[str] = None,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """创建新任务
    
    Args:
        title: 任务标题
        description: 任务描述（可选）
        priority: 优先级 (low/medium/high/urgent)，默认 medium
        category: 分类名称（可选）
        tags: 标签列表，用逗号分隔（可选）
        due_date: 截止日期，格式 YYYY-MM-DD 或 YYYY-MM-DD HH:MM（可选）
    
    Returns:
        包含任务信息的字典
    """
    db = get_session()
    try:
        # 解析优先级
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        task_priority = priority_map.get(priority.lower(), TaskPriority.MEDIUM)
        
        # 解析截止日期
        parsed_due_date = None
        if due_date:
            try:
                if len(due_date) == 10:  # YYYY-MM-DD
                    parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d")
                else:  # YYYY-MM-DD HH:MM
                    parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            except ValueError:
                return {"error": f"Invalid date format: {due_date}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM"}
        
        # 创建任务
        task = Task(
            title=title,
            description=description,
            priority=task_priority,
            due_date=parsed_due_date
        )
        
        # 处理分类
        if category:
            db_category = db.query(Category).filter(Category.name == category).first()
            if not db_category:
                return {"error": f"Category '{category}' not found. Create it first."}
            task.category_id = db_category.id
        
        # 处理标签
        if tags:
            tag_names = [tag.strip() for tag in tags.split(",")]
            for tag_name in tag_names:
                db_tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not db_tag:
                    return {"error": f"Tag '{tag_name}' not found. Create it first."}
                task.tags.append(db_tag)
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return {
            "success": True,
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "status": task.status.value,
            "category": task.category.name if task.category else None,
            "tags": [tag.name for tag in task.tags],
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat() if task.created_at else None
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to create task: {str(e)}"}
    finally:
        db.close()


@tool
def list_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    all_tasks: bool = False
) -> Dict[str, Any]:
    """列出任务
    
    Args:
        status: 状态过滤 (pending/in_progress/completed/cancelled)
        category: 分类过滤
        tag: 标签过滤
        priority: 优先级过滤 (low/medium/high/urgent)
        limit: 最大返回数量，默认 50
        all_tasks: 是否显示所有任务（包括已完成），默认 False
    
    Returns:
        包含任务列表的字典
    """
    db = get_session()
    try:
        # 构建查询
        query = db.query(Task)

        # 状态过滤
        if status:
            status_map = {
                "pending": TaskStatus.PENDING,
                "in_progress": TaskStatus.IN_PROGRESS,
                "completed": TaskStatus.COMPLETED,
                "cancelled": TaskStatus.CANCELLED
            }
            task_status = status_map.get(status.lower())
            if task_status:
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
            priority_map = {
                "low": TaskPriority.LOW,
                "medium": TaskPriority.MEDIUM,
                "high": TaskPriority.HIGH,
                "urgent": TaskPriority.URGENT
            }
            task_priority = priority_map.get(priority.lower())
            if task_priority:
                query = query.filter(Task.priority == task_priority)

        # 排序和限制
        query = query.order_by(Task.created_at.desc()).limit(limit)
        tasks = query.all()

        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "category": task.category.name if task.category else None,
                "tags": [tag.name for tag in task.tags],
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })

        return {
            "success": True,
            "tasks": task_list,
            "total_count": len(task_list)
        }

    except Exception as e:
        return {"error": f"Failed to list tasks: {str(e)}"}
    finally:
        db.close()


@tool
def search_tasks(
    query: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    priority: Optional[str] = None,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,
    created_before: Optional[str] = None,
    created_after: Optional[str] = None,
    overdue: bool = False,
    limit: int = 50
) -> Dict[str, Any]:
    """高级搜索任务
    
    Args:
        query: 搜索关键词（在标题和描述中搜索）
        status: 状态过滤
        category: 分类过滤
        tag: 标签过滤
        priority: 优先级过滤
        due_before: 截止日期之前 (YYYY-MM-DD)
        due_after: 截止日期之后 (YYYY-MM-DD)
        created_before: 创建日期之前 (YYYY-MM-DD)
        created_after: 创建日期之后 (YYYY-MM-DD)
        overdue: 仅显示过期任务
        limit: 最大返回数量
    
    Returns:
        包含搜索结果的字典
    """
    db = get_session()
    try:
        # 构建查询
        db_query = db.query(Task)
        
        # 关键词搜索
        if query:
            db_query = db_query.filter(
                or_(
                    Task.title.contains(query),
                    Task.description.contains(query)
                )
            )
        
        # 其他过滤条件（复用 list_tasks 的逻辑）
        # 这里可以添加更多复杂的搜索逻辑
        
        tasks = db_query.order_by(Task.created_at.desc()).limit(limit).all()
        
        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "category": task.category.name if task.category else None,
                "tags": [tag.name for tag in task.tags],
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat() if task.created_at else None
            })

        return {
            "success": True,
            "tasks": task_list,
            "total_count": len(task_list),
            "search_query": query
        }

    except Exception as e:
        return {"error": f"Failed to search tasks: {str(e)}"}
    finally:
        db.close()


@tool
def show_task(task_id: int) -> Dict[str, Any]:
    """显示任务详情
    
    Args:
        task_id: 任务 ID
    
    Returns:
        包含任务详细信息的字典
    """
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": f"Task with ID {task_id} not found"}

        return {
            "success": True,
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "category": task.category.name if task.category else None,
                "tags": [tag.name for tag in task.tags],
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
        }

    except Exception as e:
        return {"error": f"Failed to show task: {str(e)}"}
    finally:
        db.close()


@tool
def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    due_date: Optional[str] = None,
    clear_category: bool = False
) -> Dict[str, Any]:
    """更新任务

    Args:
        task_id: 任务 ID
        title: 新标题
        description: 新描述
        priority: 新优先级 (low/medium/high/urgent)
        status: 新状态 (pending/in_progress/completed/cancelled)
        category: 新分类名称
        due_date: 新截止日期 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM)
        clear_category: 清除分类

    Returns:
        包含更新结果的字典
    """
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": f"Task with ID {task_id} not found"}

        updated = False

        # 更新标题
        if title:
            task.title = title
            updated = True

        # 更新描述
        if description is not None:
            task.description = description
            updated = True

        # 更新优先级
        if priority:
            priority_map = {
                "low": TaskPriority.LOW,
                "medium": TaskPriority.MEDIUM,
                "high": TaskPriority.HIGH,
                "urgent": TaskPriority.URGENT
            }
            task_priority = priority_map.get(priority.lower())
            if task_priority:
                task.priority = task_priority
                updated = True

        # 更新状态
        if status:
            status_map = {
                "pending": TaskStatus.PENDING,
                "in_progress": TaskStatus.IN_PROGRESS,
                "completed": TaskStatus.COMPLETED,
                "cancelled": TaskStatus.CANCELLED
            }
            task_status = status_map.get(status.lower())
            if task_status:
                task.status = task_status
                if task_status == TaskStatus.COMPLETED and not task.completed_at:
                    task.completed_at = datetime.now()
                updated = True

        # 更新分类
        if category:
            db_category = db.query(Category).filter(Category.name == category).first()
            if not db_category:
                return {"error": f"Category '{category}' not found"}
            task.category_id = db_category.id
            updated = True

        if clear_category:
            task.category_id = None
            updated = True

        # 更新截止日期
        if due_date:
            try:
                if len(due_date) == 10:  # YYYY-MM-DD
                    task.due_date = datetime.strptime(due_date, "%Y-%m-%d")
                else:  # YYYY-MM-DD HH:MM
                    task.due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
                updated = True
            except ValueError:
                return {"error": f"Invalid date format: {due_date}"}

        if not updated:
            return {"error": "No changes specified"}

        db.commit()
        db.refresh(task)

        return {
            "success": True,
            "message": f"Task {task_id} updated successfully",
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "category": task.category.name if task.category else None,
                "tags": [tag.name for tag in task.tags],
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            }
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to update task: {str(e)}"}
    finally:
        db.close()


@tool
def complete_task(task_id: int) -> Dict[str, Any]:
    """完成任务

    Args:
        task_id: 任务 ID

    Returns:
        包含完成结果的字典
    """
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": f"Task with ID {task_id} not found"}

        if task.status == TaskStatus.COMPLETED:
            return {"message": f"Task {task_id} is already completed"}

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        db.commit()

        return {
            "success": True,
            "message": f"Task {task_id} marked as completed",
            "task": {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "completed_at": task.completed_at.isoformat()
            }
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to complete task: {str(e)}"}
    finally:
        db.close()


@tool
def delete_task(task_id: int) -> Dict[str, Any]:
    """删除任务

    Args:
        task_id: 任务 ID

    Returns:
        包含删除结果的字典
    """
    db = get_session()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": f"Task with ID {task_id} not found"}

        task_title = task.title
        db.delete(task)
        db.commit()

        return {
            "success": True,
            "message": f"Task '{task_title}' (ID: {task_id}) deleted successfully"
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to delete task: {str(e)}"}
    finally:
        db.close()


# ==================== 分类管理工具 ====================

@tool
def add_category(
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """创建新分类

    Args:
        name: 分类名称
        description: 分类描述（可选）
        color: 分类颜色，十六进制格式如 #FF5733（可选）

    Returns:
        包含分类信息的字典
    """
    db = get_session()
    try:
        # 检查分类是否已存在
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            return {"error": f"Category '{name}' already exists"}

        # 验证颜色格式
        if color and not color.startswith('#'):
            color = f"#{color}"

        if color and len(color) != 7:
            return {"error": "Color must be a valid hex code (e.g., #FF5733)"}

        # 创建分类
        category = Category(
            name=name,
            description=description,
            color=color
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return {
            "success": True,
            "category_id": category.id,
            "name": category.name,
            "description": category.description,
            "color": category.color,
            "created_at": category.created_at.isoformat() if category.created_at else None
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to create category: {str(e)}"}
    finally:
        db.close()


@tool
def list_categories() -> Dict[str, Any]:
    """列出所有分类

    Returns:
        包含分类列表的字典
    """
    db = get_session()
    try:
        categories = db.query(Category).order_by(Category.name).all()

        category_list = []
        for category in categories:
            # 计算该分类下的任务数量
            task_count = db.query(Task).filter(Task.category_id == category.id).count()

            category_list.append({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "task_count": task_count,
                "created_at": category.created_at.isoformat() if category.created_at else None
            })

        return {
            "success": True,
            "categories": category_list,
            "total_count": len(category_list)
        }

    except Exception as e:
        return {"error": f"Failed to list categories: {str(e)}"}
    finally:
        db.close()


@tool
def update_category(
    name: str,
    new_name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """更新分类

    Args:
        name: 要更新的分类名称
        new_name: 新的分类名称
        description: 新的描述
        color: 新的颜色（十六进制格式）

    Returns:
        包含更新结果的字典
    """
    db = get_session()
    try:
        category = db.query(Category).filter(Category.name == name).first()
        if not category:
            return {"error": f"Category '{name}' not found"}

        updated = False

        if new_name:
            # 检查新名称是否已存在
            existing = db.query(Category).filter(Category.name == new_name).first()
            if existing and existing.id != category.id:
                return {"error": f"Category '{new_name}' already exists"}
            category.name = new_name
            updated = True

        if description is not None:
            category.description = description
            updated = True

        if color:
            if not color.startswith('#'):
                color = f"#{color}"
            if len(color) != 7:
                return {"error": "Color must be a valid hex code (e.g., #FF5733)"}
            category.color = color
            updated = True

        if not updated:
            return {"error": "No changes specified"}

        db.commit()

        return {
            "success": True,
            "message": f"Category updated successfully",
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "updated_at": category.updated_at.isoformat() if category.updated_at else None
            }
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to update category: {str(e)}"}
    finally:
        db.close()


@tool
def delete_category(name: str) -> Dict[str, Any]:
    """删除分类

    Args:
        name: 分类名称

    Returns:
        包含删除结果的字典
    """
    db = get_session()
    try:
        category = db.query(Category).filter(Category.name == name).first()
        if not category:
            return {"error": f"Category '{name}' not found"}

        # 检查是否有任务使用该分类
        task_count = db.query(Task).filter(Task.category_id == category.id).count()
        if task_count > 0:
            return {"error": f"Cannot delete category '{name}' because it has {task_count} associated tasks"}

        db.delete(category)
        db.commit()

        return {
            "success": True,
            "message": f"Category '{name}' deleted successfully"
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to delete category: {str(e)}"}
    finally:
        db.close()


# ==================== 标签管理工具 ====================

@tool
def add_tag(
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """创建新标签

    Args:
        name: 标签名称
        description: 标签描述（可选）
        color: 标签颜色，十六进制格式如 #FF5733（可选）

    Returns:
        包含标签信息的字典
    """
    db = get_session()
    try:
        # 检查标签是否已存在
        existing = db.query(Tag).filter(Tag.name == name).first()
        if existing:
            return {"error": f"Tag '{name}' already exists"}

        # 验证颜色格式
        if color and not color.startswith('#'):
            color = f"#{color}"

        if color and len(color) != 7:
            return {"error": "Color must be a valid hex code (e.g., #FF5733)"}

        # 创建标签
        tag = Tag(
            name=name,
            description=description,
            color=color
        )

        db.add(tag)
        db.commit()
        db.refresh(tag)

        return {
            "success": True,
            "tag_id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "color": tag.color,
            "created_at": tag.created_at.isoformat() if tag.created_at else None
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to create tag: {str(e)}"}
    finally:
        db.close()


@tool
def list_tags() -> Dict[str, Any]:
    """列出所有标签

    Returns:
        包含标签列表的字典
    """
    db = get_session()
    try:
        tags = db.query(Tag).order_by(Tag.name).all()

        tag_list = []
        for tag in tags:
            tag_list.append({
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "color": tag.color,
                "task_count": tag.task_count,
                "created_at": tag.created_at.isoformat() if tag.created_at else None
            })

        return {
            "success": True,
            "tags": tag_list,
            "total_count": len(tag_list)
        }

    except Exception as e:
        return {"error": f"Failed to list tags: {str(e)}"}
    finally:
        db.close()


@tool
def update_tag(
    name: str,
    new_name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """更新标签

    Args:
        name: 要更新的标签名称
        new_name: 新的标签名称
        description: 新的描述
        color: 新的颜色（十六进制格式）

    Returns:
        包含更新结果的字典
    """
    db = get_session()
    try:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            return {"error": f"Tag '{name}' not found"}

        updated = False

        if new_name:
            # 检查新名称是否已存在
            existing = db.query(Tag).filter(Tag.name == new_name).first()
            if existing and existing.id != tag.id:
                return {"error": f"Tag '{new_name}' already exists"}
            tag.name = new_name
            updated = True

        if description is not None:
            tag.description = description
            updated = True

        if color:
            if not color.startswith('#'):
                color = f"#{color}"
            if len(color) != 7:
                return {"error": "Color must be a valid hex code (e.g., #FF5733)"}
            tag.color = color
            updated = True

        if not updated:
            return {"error": "No changes specified"}

        db.commit()

        return {
            "success": True,
            "message": f"Tag updated successfully",
            "tag": {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "color": tag.color,
                "updated_at": tag.updated_at.isoformat() if tag.updated_at else None
            }
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to update tag: {str(e)}"}
    finally:
        db.close()


@tool
def delete_tag(name: str) -> Dict[str, Any]:
    """删除标签

    Args:
        name: 标签名称

    Returns:
        包含删除结果的字典
    """
    db = get_session()
    try:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            return {"error": f"Tag '{name}' not found"}

        # 检查是否有任务使用该标签
        if tag.task_count > 0:
            return {"error": f"Cannot delete tag '{name}' because it has {tag.task_count} associated tasks"}

        db.delete(tag)
        db.commit()

        return {
            "success": True,
            "message": f"Tag '{name}' deleted successfully"
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to delete tag: {str(e)}"}
    finally:
        db.close()


# ==================== 工具列表导出 ====================

# 所有可用的工具列表
ALL_TOOLS = [
    # 通用工具
    current_datetime,

    # 任务管理工具
    add_task,
    list_tasks,
    search_tasks,
    show_task,
    update_task,
    complete_task,
    delete_task,

    # 分类管理工具
    add_category,
    list_categories,
    update_category,
    delete_category,

    # 标签管理工具
    add_tag,
    list_tags,
    update_tag,
    delete_tag,
]

# 按功能分组的工具
TASK_TOOLS = [add_task, list_tasks, search_tasks, show_task, update_task, complete_task, delete_task]
CATEGORY_TOOLS = [add_category, list_categories, update_category, delete_category]
TAG_TOOLS = [add_tag, list_tags, update_tag, delete_tag]
