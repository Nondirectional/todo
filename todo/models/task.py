"""
Task数据模型定义
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json

from sqlalchemy import String, Text, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy声明式基类"""
    pass


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    """任务数据模型"""
    __tablename__ = "tasks"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 状态和优先级
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.PENDING)
    priority: Mapped[TaskPriority] = mapped_column(default=TaskPriority.MEDIUM)
    
    # 时间字段
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    start_time: Mapped[Optional[datetime]]
    due_date: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # 扩展字段
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    def __repr__(self) -> str:
        return f"Task(id={self.id!r}, title={self.title!r}, status={self.status!r})"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags or {}
        } 