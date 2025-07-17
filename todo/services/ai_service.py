"""
AI助手服务 - 基于agno实现智能任务管理
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from rich.console import Console

from .task_service import TaskService
from ..models.task import Task, TaskStatus, TaskPriority
from ..utils.date_utils import format_datetime, parse_datetime

console = Console()


class TodoAIAssistant:
    """Todo AI助手类"""
    
    def __init__(self, task_service: TaskService):
        """初始化AI助手
        
        Args:
            task_service: 任务服务实例
        """
        self.task_service = task_service
        self.agent: Optional[Agent] = None
        self._init_agent()
    
    def _init_agent(self):
        """初始化AI代理"""
        try:
            # 配置AI助手存储
            storage = SqliteStorage(
                table_name="ai_assistant_sessions", 
                db_file=os.path.expanduser("~/.todo/ai_sessions.db")
            )
            
            # 创建AI代理
            self.agent = Agent(
                name="Todo AI Assistant",
                model=OpenAIChat(id="gpt-4o-mini"),  # 使用更经济的模型
                instructions=dedent("""\
                    你是一个专业的任务管理AI助手！🤖
                    
                    你的职责：
                    1. 帮助用户通过自然语言对话来管理待办事项
                    2. 理解用户的任务描述并提取关键信息（标题、描述、优先级、截止时间）
                    3. 生成日报和周报
                    4. 提供任务管理建议和时间规划建议
                    
                    交互风格：
                    - 友好、专业且富有同理心
                    - 用简洁明了的语言
                    - 主动询问必要的细节
                    - 提供建设性的建议
                    
                    任务信息提取规则：
                    - 标题：用户描述的核心任务
                    - 描述：详细说明或背景信息
                    - 优先级：根据紧急程度判断（high/medium/low）
                    - 截止时间：提取时间表达（支持自然语言）
                    
                    输出格式：
                    对于任务创建请求，请以JSON格式输出：
                    {
                        "action": "create_task",
                        "title": "任务标题",
                        "description": "详细描述",
                        "priority": "high|medium|low",
                        "due_date": "截止时间字符串或null"
                    }
                    
                    对于其他对话，正常回复即可。
                """),
                storage=storage,
                add_history_to_messages=True,
                num_history_responses=5,
                markdown=True,
            )
        except Exception as e:
            console.print(f"⚠️ AI助手初始化失败: {e}", style="yellow")
            console.print("将以基础模式运行（无AI功能）", style="dim")
            self.agent = None
    
    def is_available(self) -> bool:
        """检查AI助手是否可用"""
        return self.agent is not None
    
    def chat(self, message: str) -> str:
        """与AI助手对话
        
        Args:
            message: 用户消息
            
        Returns:
            AI助手回复
        """
        if not self.is_available() or self.agent is None:
            return "AI助手当前不可用，请检查网络连接或API密钥配置。"
        
        try:
            # 为AI提供当前任务上下文
            context = self._get_task_context()
            full_message = f"{context}\n\n用户消息: {message}"
            
            # 获取AI回复
            response = self.agent.run(full_message)
            return response.content if response.content else "AI助手回复为空"
        except Exception as e:
            console.print(f"AI对话错误: {e}", style="red")
            return f"抱歉，AI处理过程中出现错误: {e}"
    
    def smart_add_task(self, description: str) -> Optional[Task]:
        """智能添加任务
        
        Args:
            description: 任务描述
            
        Returns:
            创建的任务对象或None
        """
        if not self.is_available() or self.agent is None:
            console.print("AI助手不可用，请使用基础的 'todo add' 命令", style="yellow")
            return None
        
        try:
            # 让AI分析任务描述
            prompt = dedent(f"""\
                用户想要添加以下任务："{description}"
                
                请分析并提取任务信息，以JSON格式回复：
                {{
                    "action": "create_task",
                    "title": "任务标题",
                    "description": "详细描述",
                    "priority": "high|medium|low",
                    "due_date": "截止时间字符串或null"
                }}
                
                只返回JSON，不要其他文字。
            """)
            
            response = self.agent.run(prompt)
            
            # 尝试解析JSON响应
            import json
            if response.content:
                try:
                    task_data = json.loads(response.content)
                    if task_data.get("action") == "create_task":
                        # 转换优先级
                        priority_map = {
                            "high": TaskPriority.HIGH,
                            "medium": TaskPriority.MEDIUM,
                            "low": TaskPriority.LOW
                        }
                        priority = priority_map.get(task_data.get("priority", "medium"), TaskPriority.MEDIUM)
                        
                        # 创建任务
                        task = self.task_service.create_task(
                            title=task_data.get("title", description),
                            description=task_data.get("description"),
                            priority=priority,
                            due_date=task_data.get("due_date")
                        )
                        return task
                except json.JSONDecodeError:
                    # 如果JSON解析失败，回退到基础创建
                    console.print("AI响应格式异常，使用基础模式创建任务", style="yellow")
                    pass
            
            # 回退到基础任务创建
            task = self.task_service.create_task(
                title=description,
                priority=TaskPriority.MEDIUM
            )
            return task
            
        except Exception as e:
            console.print(f"智能添加任务失败: {e}", style="red")
            return None
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> str:
        """生成日报
        
        Args:
            date: 指定日期，默认为今天
            
        Returns:
            日报内容
        """
        if not date:
            date = datetime.now()
        
        try:
            # 获取指定日期的任务数据
            all_tasks = self.task_service.list_tasks()
            date_str = date.strftime("%Y-%m-%d")
            
            # 筛选今日相关任务
            today_tasks = []
            completed_today = []
            
            for task in all_tasks:
                # 今日创建的任务
                if task.created_at.strftime("%Y-%m-%d") == date_str:
                    today_tasks.append(task)
                
                # 今日完成的任务
                if (task.completed_at and 
                    task.completed_at.strftime("%Y-%m-%d") == date_str):
                    completed_today.append(task)
            
            # 获取待处理和过期任务
            pending_tasks = self.task_service.get_pending_tasks()
            overdue_tasks = [t for t in pending_tasks if t.due_date and t.due_date < date]
            
            if self.is_available() and self.agent is not None:
                # 使用AI生成报告
                prompt = dedent(f"""\
                    请为 {date.strftime('%Y年%m月%d日')} 生成一份工作日报。
                    
                    数据统计：
                    - 今日新增任务：{len(today_tasks)} 个
                    - 今日完成任务：{len(completed_today)} 个
                    - 待处理任务：{len(pending_tasks)} 个
                    - 过期任务：{len(overdue_tasks)} 个
                    
                    今日完成的任务：
                    {self._format_tasks_for_ai(completed_today)}
                    
                    待处理任务：
                    {self._format_tasks_for_ai(pending_tasks[:5])}  # 只显示前5个
                    
                    请生成一份专业的工作日报，包括：
                    1. 工作摘要
                    2. 主要成就
                    3. 明日重点
                    4. 时间管理建议
                    
                    使用友好、激励的语调，并用Markdown格式输出。
                """)
                
                response = self.agent.run(prompt)
                return response.content if response.content else "AI生成报告失败"
            else:
                # 基础日报生成
                return self._generate_basic_report(date, today_tasks, completed_today, pending_tasks, overdue_tasks)
                
        except Exception as e:
            console.print(f"生成日报失败: {e}", style="red")
            return f"日报生成失败: {e}"
    
    def _get_task_context(self) -> str:
        """获取当前任务上下文信息"""
        try:
            pending_tasks = self.task_service.get_pending_tasks()
            recent_completed = self.task_service.get_completed_tasks()[:3]
            
            context = "当前任务状态：\n"
            context += f"- 待处理任务：{len(pending_tasks)} 个\n"
            
            if pending_tasks:
                context += "最近的待处理任务：\n"
                for task in pending_tasks[:3]:
                    due_info = f"，截止：{format_datetime(task.due_date, 'short')}" if task.due_date else ""
                    context += f"  - {task.title} ({task.priority.value}{due_info})\n"
            
            if recent_completed:
                context += "最近完成的任务：\n"
                for task in recent_completed:
                    context += f"  - {task.title}\n"
            
            return context
        except Exception:
            return "任务上下文获取失败"
    
    def _format_tasks_for_ai(self, tasks: List[Task]) -> str:
        """为AI格式化任务列表"""
        if not tasks:
            return "无"
        
        formatted = []
        for task in tasks:
            due_info = f"，截止：{format_datetime(task.due_date)}" if task.due_date else ""
            formatted.append(f"- {task.title} ({task.priority.value}{due_info})")
        
        return "\n".join(formatted)
    
    def _generate_basic_report(self, date: datetime, today_tasks: List[Task], 
                             completed_today: List[Task], pending_tasks: List[Task], 
                             overdue_tasks: List[Task]) -> str:
        """生成基础日报（无AI）"""
        report = f"# {date.strftime('%Y年%m月%d日')} 工作日报\n\n"
        
        report += "## 📊 数据统计\n"
        report += f"- 今日新增任务：{len(today_tasks)} 个\n"
        report += f"- 今日完成任务：{len(completed_today)} 个\n"
        report += f"- 待处理任务：{len(pending_tasks)} 个\n"
        report += f"- 过期任务：{len(overdue_tasks)} 个\n\n"
        
        if completed_today:
            report += "## ✅ 今日完成\n"
            for task in completed_today:
                report += f"- {task.title}\n"
            report += "\n"
        
        if pending_tasks:
            report += "## ⏳ 待处理任务\n"
            for task in pending_tasks[:5]:
                due_info = f" (截止：{format_datetime(task.due_date, 'short')})" if task.due_date else ""
                report += f"- {task.title}{due_info}\n"
            if len(pending_tasks) > 5:
                report += f"- ... 还有 {len(pending_tasks) - 5} 个任务\n"
            report += "\n"
        
        if overdue_tasks:
            report += "## ⚠️ 过期任务\n"
            for task in overdue_tasks:
                overdue_due_info = f"过期：{format_datetime(task.due_date, 'short')}" if task.due_date else "过期"
                report += f"- {task.title} ({overdue_due_info})\n"
            report += "\n"
        
        report += "## 💡 建议\n"
        if overdue_tasks:
            report += "- 优先处理过期任务\n"
        if len(pending_tasks) > 10:
            report += "- 任务较多，建议按优先级整理\n"
        report += "- 保持专注，一次专心做一件事\n"
        
        return report 