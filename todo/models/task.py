"""
Task model - the core entity of the todo application.

Tasks represent individual todo items with various attributes like priority, status, etc.
"""

from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from todo.database import Base
from todo.models.tag import task_tags


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """Task model - core entity for todo items."""
    
    __tablename__ = "tasks"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 状态和优先级
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True)
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 外键关系
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    
    # 关系
    category = relationship("Category", back_populates="tasks")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"
    
    def __str__(self):
        return f"[{self.id}] {self.title} ({self.status.value})"
    
    @property
    def is_completed(self):
        """检查任务是否已完成"""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_overdue(self):
        """检查任务是否已过期"""
        if not self.due_date or self.is_completed:
            return False
        return self.due_date < func.now()
    
    def mark_completed(self):
        """标记任务为已完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = func.now()
    
    def mark_cancelled(self):
        """标记任务为已取消"""
        self.status = TaskStatus.CANCELLED
