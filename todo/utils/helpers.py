"""
Helper functions for formatting and utility operations.
"""

from datetime import datetime
from typing import Optional
from todo.models.task import TaskStatus, TaskPriority


def format_date(date: Optional[datetime]) -> str:
    """格式化日期显示"""
    if not date:
        return "N/A"
    return date.strftime("%Y-%m-%d %H:%M")


def format_priority(priority: TaskPriority) -> str:
    """格式化优先级显示"""
    priority_map = {
        TaskPriority.LOW: "🟢 Low",
        TaskPriority.MEDIUM: "🟡 Medium", 
        TaskPriority.HIGH: "🟠 High",
        TaskPriority.URGENT: "🔴 Urgent"
    }
    return priority_map.get(priority, str(priority.value))


def format_status(status: TaskStatus) -> str:
    """格式化状态显示"""
    status_map = {
        TaskStatus.PENDING: "⏳ Pending",
        TaskStatus.IN_PROGRESS: "🔄 In Progress",
        TaskStatus.COMPLETED: "✅ Completed",
        TaskStatus.CANCELLED: "❌ Cancelled"
    }
    return status_map.get(status, str(status.value))


def parse_priority(priority_str: str) -> TaskPriority:
    """解析优先级字符串"""
    priority_map = {
        "low": TaskPriority.LOW,
        "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT,
        "l": TaskPriority.LOW,
        "m": TaskPriority.MEDIUM,
        "h": TaskPriority.HIGH,
        "u": TaskPriority.URGENT
    }
    return priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)


def parse_status(status_str: str) -> TaskStatus:
    """解析状态字符串"""
    status_map = {
        "pending": TaskStatus.PENDING,
        "in_progress": TaskStatus.IN_PROGRESS,
        "completed": TaskStatus.COMPLETED,
        "cancelled": TaskStatus.CANCELLED,
        "p": TaskStatus.PENDING,
        "i": TaskStatus.IN_PROGRESS,
        "c": TaskStatus.COMPLETED,
        "x": TaskStatus.CANCELLED
    }
    return status_map.get(status_str.lower(), TaskStatus.PENDING)


def parse_date(date_str: str) -> Optional[datetime]:
    """解析日期字符串"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%m-%d",
        "%m/%d",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str}")


def truncate_text(text: str, max_length: int = 50) -> str:
    """截断文本并添加省略号"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
