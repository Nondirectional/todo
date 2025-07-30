"""
Tag model for labeling tasks.

Tags provide a flexible way to label and categorize tasks with multiple attributes.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from todo.database import Base

# 多对多关系表：任务和标签
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Tag(Base):
    """Tag model for flexible task labeling."""
    
    __tablename__ = "tags"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # 十六进制颜色代码
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
    
    def __str__(self):
        return self.name
    
    @property
    def task_count(self):
        """返回使用该标签的任务数量"""
        return len(self.tasks) if self.tasks else 0
