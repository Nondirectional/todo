"""
数据库配置和操作
"""
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from .task import Base


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为 ~/.todo/todo.db
        """
        if db_path is None:
            # 默认数据库路径
            home_dir = Path.home()
            todo_dir = home_dir / ".todo"
            todo_dir.mkdir(exist_ok=True)
            db_path = str(todo_dir / "todo.db")
        
        self.db_path = db_path
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
    
    def init_database(self) -> None:
        """初始化数据库连接和表结构"""
        # 创建数据库引擎
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False  # 设为True可以看到SQL输出，用于调试
        )
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # 创建所有表
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        if self.SessionLocal is None:
            raise RuntimeError("数据库未初始化，请先调用 init_database()")
        return self.SessionLocal()
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db() -> Session:
    """获取数据库会话的便捷函数"""
    session = db_manager.get_session()
    try:
        return session
    finally:
        session.close()


def init_db(db_path: Optional[str] = None) -> None:
    """初始化数据库的便捷函数"""
    global db_manager
    if db_path:
        db_manager = DatabaseManager(db_path)
    db_manager.init_database() 