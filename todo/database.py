"""
Database configuration and initialization module.

This module handles SQLAlchemy setup, database connection, and table creation.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import typer

# 创建基础模型类
Base = declarative_base()

# 数据库配置
def get_db_path() -> Path:
    """获取数据库文件路径"""
    app_dir = typer.get_app_dir("todo-cli")
    os.makedirs(app_dir, exist_ok=True)
    return Path(app_dir) / "todo.db"

# 创建数据库引擎
DATABASE_URL = f"sqlite:///{get_db_path()}"
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设置为True可以看到SQL语句
    connect_args={"check_same_thread": False}  # SQLite特定配置
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型以确保它们被注册到Base.metadata
    from todo.models import task, category, tag
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)


def get_session():
    """获取数据库会话（用于命令行操作）"""
    return SessionLocal()
