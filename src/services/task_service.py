"""
任务管理服务
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from src.models.task import Task, TaskStatus, TaskPriority
from src.models.database import get_db, db_manager
from src.utils.date_utils import parse_datetime


class TaskService:
    """任务管理服务类"""
    
    def __init__(self):
        """初始化任务服务"""
        pass
    
    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Task:
        """创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            priority: 任务优先级
            due_date: 截止时间字符串
            tags: 标签字典
            
        Returns:
            创建的任务对象
        """
        session = db_manager.get_session()
        try:
            # 解析截止时间
            parsed_due_date = None
            if due_date:
                parsed_due_date = parse_datetime(due_date)
            
            # 创建任务对象
            task = Task(
                title=title,
                description=description,
                priority=priority,
                due_date=parsed_due_date,
                tags=tags or {}
            )
            
            session.add(task)
            session.commit()
            session.refresh(task)
            
            return task
        finally:
            session.close()
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象或None
        """
        session = db_manager.get_session()
        try:
            stmt = select(Task).where(Task.id == task_id)
            result = session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            session.close()
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """列出任务
        
        Args:
            status: 筛选状态
            priority: 筛选优先级
            limit: 限制数量
            
        Returns:
            任务列表
        """
        session = db_manager.get_session()
        try:
            stmt = select(Task).order_by(Task.created_at.desc())
            
            # 应用筛选条件
            if status:
                stmt = stmt.where(Task.status == status)
            if priority:
                stmt = stmt.where(Task.priority == priority)
            if limit:
                stmt = stmt.limit(limit)
            
            result = session.execute(stmt)
            return list(result.scalars())
        finally:
            session.close()
    
    def update_task(
        self,
        task_id: int,
        **kwargs
    ) -> Optional[Task]:
        """更新任务
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的任务对象或None
        """
        session = db_manager.get_session()
        try:
            # 获取任务
            task = session.get(Task, task_id)
            if not task:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(task, key):
                    # 特殊处理时间字段
                    if key in ["due_date", "start_time"] and isinstance(value, str):
                        value = parse_datetime(value)
                    setattr(task, key, value)
            
            session.commit()
            session.refresh(task)
            
            return task
        finally:
            session.close()
    
    def complete_task(self, task_id: int) -> Optional[Task]:
        """标记任务为完成
        
        Args:
            task_id: 任务ID
            
        Returns:
            更新后的任务对象或None
        """
        return self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now()
        )
    
    def start_task(self, task_id: int) -> Optional[Task]:
        """开始任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            更新后的任务对象或None
        """
        return self.update_task(
            task_id,
            status=TaskStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            删除是否成功
        """
        session = db_manager.get_session()
        try:
            task = session.get(Task, task_id)
            if not task:
                return False
            
            session.delete(task)
            session.commit()
            return True
        finally:
            session.close()
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待处理任务"""
        return self.list_tasks(status=TaskStatus.PENDING)
    
    def get_completed_tasks(self) -> List[Task]:
        """获取已完成任务"""
        return self.list_tasks(status=TaskStatus.COMPLETED)
    
    def search_tasks(self, keyword: str) -> List[Task]:
        """搜索任务
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的任务列表
        """
        session = db_manager.get_session()
        try:
            stmt = select(Task).where(
                Task.title.contains(keyword) | 
                Task.description.contains(keyword)
            ).order_by(Task.created_at.desc())
            
            result = session.execute(stmt)
            return list(result.scalars())
        finally:
            session.close() 