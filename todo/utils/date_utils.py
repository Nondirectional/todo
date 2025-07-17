"""
时间处理工具函数
"""
from datetime import datetime
from typing import Optional

import pendulum
from pendulum import DateTime


def parse_datetime(date_str: str) -> Optional[datetime]:
    """解析时间字符串为datetime对象
    
    支持多种格式：
    - 2024-01-15
    - 2024-01-15 14:30
    - tomorrow
    - next week
    - in 2 hours
    
    Args:
        date_str: 时间字符串
        
    Returns:
        解析后的datetime对象，失败返回None
    """
    if not date_str:
        return None
    
    try:
        # 使用pendulum解析相对时间
        parsed = pendulum.parse(date_str, strict=False)
        if parsed:
            return parsed.to_python_datetime()
    except Exception:
        pass
    
    # 尝试常见的相对时间表达
    try:
        now = pendulum.now()
        date_str_lower = date_str.lower()
        
        if date_str_lower in ["today", "今天"]:
            return now.to_python_datetime()
        elif date_str_lower in ["tomorrow", "明天"]:
            return now.add(days=1).to_python_datetime()
        elif date_str_lower in ["next week", "下周"]:
            return now.add(weeks=1).to_python_datetime()
        elif date_str_lower in ["next month", "下月"]:
            return now.add(months=1).to_python_datetime()
    except Exception:
        pass
    
    return None


def format_datetime(dt: datetime, format_type: str = "default") -> str:
    """格式化datetime对象为字符串
    
    Args:
        dt: datetime对象
        format_type: 格式类型 ("default", "short", "relative")
        
    Returns:
        格式化后的时间字符串
    """
    if not dt:
        return ""
    
    pdt = pendulum.instance(dt)
    
    if format_type == "short":
        return pdt.format("MM-DD HH:mm")
    elif format_type == "relative":
        return pdt.diff_for_humans()
    else:  # default
        return pdt.format("YYYY-MM-DD HH:mm:ss")


def is_overdue(due_date: Optional[datetime]) -> bool:
    """检查任务是否已过期
    
    Args:
        due_date: 截止时间
        
    Returns:
        是否过期
    """
    if not due_date:
        return False
    
    now = pendulum.now()
    return pendulum.instance(due_date) < now


def get_due_status(due_date: Optional[datetime]) -> str:
    """获取截止状态描述
    
    Args:
        due_date: 截止时间
        
    Returns:
        状态描述 ("已过期", "今天到期", "明天到期", 等)
    """
    if not due_date:
        return ""
    
    now = pendulum.now()
    due_pdt = pendulum.instance(due_date)
    
    if due_pdt < now:
        return "已过期"
    elif due_pdt.date() == now.date():
        return "今天到期"
    elif due_pdt.date() == now.add(days=1).date():
        return "明天到期"
    else:
        return due_pdt.diff_for_humans() 