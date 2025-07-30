"""
Category model for organizing tasks.

Categories provide a way to group related tasks together.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from todo.database import Base


class Category(Base):
    """Category model for task organization."""
    
    __tablename__ = "categories"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # 十六进制颜色代码，如 #FF5733
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    tasks = relationship("Task", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
    
    def __str__(self):
        return self.name
    
    @property
    def task_count(self):
        """返回该分类下的任务数量"""
        return len(self.tasks) if self.tasks else 0
