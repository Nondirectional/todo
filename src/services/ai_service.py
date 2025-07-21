"""
AI助手服务 - 基于agno实现智能任务管理
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from textwrap import dedent
from dataclasses import dataclass
from typing import Optional, Union

import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.storage.sqlite import SqliteStorage
from rich.console import Console

from src.services.task_service import TaskService
from src.models.task import Task, TaskStatus, TaskPriority
from src.utils.date_utils import format_datetime, parse_datetime
from src.tools.todo import TodoToolkit
from agno.tools.calculator import CalculatorTools
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

console = Console()


@dataclass
class DashScope(OpenAIChat):
    """
    DashScope模型类，用于与阿里云DashScope兼容模式交互

    Args:
        id (str): 模型ID，默认为 "not-provided"
        name (str): 模型名称，默认为 "DashScope"
        api_key (Optional[str]): API密钥，默认为 "not-provided"
        base_url (Optional[Union[str, httpx.URL]]): 基础URL，默认为DashScope兼容模式地址
    """

    id: str = "not-provided"
    name: str = "DashScope"
    api_key: Optional[str] = "not-provided"
    base_url: Optional[Union[str, httpx.URL]] = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    role_map = {
        "system": "system",
        "user": "user",
        "assistant": "assistant",
        "tool": "tool",
    }


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
            # 选择AI模型
            model = self._get_ai_model()

            # 配置AI助手记忆
            memory = Memory(
                model=model,
                db=SqliteMemoryDb(db_file=os.path.expanduser("~/.todo/ai_memory.db")),
            )

            # 配置AI助手存储
            storage = SqliteStorage(
                table_name="ai_assistant_sessions",
                db_file=os.path.expanduser("~/.todo/ai_sessions.db"),
            )

            # 创建AI代理
            self.agent = Agent(
                name="Todo AI Assistant",
                model=model,
                memory=memory,
                enable_agentic_memory=True,
                enable_user_memories=True,
                instructions=[
                    # 核心身份和职责
                    f"现在的时间是：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}，你是一个专业的待办事项管理助手，名为Todo AI Assistant。你的核心职责是帮助用户高效管理他们的待办事项。",
                    # 工具使用指南
                    "**工具使用指南:**",
                    "- add_todo_task: 当用户想要创建新任务时使用，支持标题、描述、优先级(low/medium/high)、截止时间等参数",
                    "- list_todo_tasks: 当用户想查看任务列表时使用，支持按状态和优先级筛选",
                    "- get_todo_task: 当用户询问特定任务详情时使用，需要任务ID",
                    "- update_todo_task: 当用户想修改任务信息时使用，可更新标题、描述、优先级、状态、截止时间等",
                    "- complete_todo_task: 当用户说完成了某个任务时使用",
                    "- delete_todo_task: 当用户想删除任务时使用",
                    "- search_todo_tasks: 当用户搜索包含特定关键词的任务时使用",
                    # 自然语言理解
                    "**自然语言理解:**",
                    "- '添加任务'、'创建任务'、'新建'、'记录' → 使用add_todo_task",
                    "- '列出'、'显示'、'查看所有'、'我的任务' → 使用list_todo_tasks",
                    "- '查看任务X'、'任务X的详情' → 使用get_todo_task",
                    "- '修改'、'更新'、'改变' → 使用update_todo_task",
                    "- '完成了'、'做完了'、'已完成' → 使用complete_todo_task",
                    "- '删除'、'移除'、'取消' → 使用delete_todo_task",
                    "- '搜索'、'查找'、'包含' → 使用search_todo_tasks",
                    # 交互原则
                    "**交互原则:**",
                    "1. 始终首先使用合适的工具执行用户请求",
                    "2. 根据工具返回结果向用户提供友好的反馈",
                    "3. 如果用户请求不明确，主动询问需要的参数(如任务ID、具体内容等)",
                    "4. 当操作成功时，提供积极的确认反馈",
                    "5. 当操作失败时，解释原因并建议解决方案",
                    "6. 主动提供有用的建议，如提醒截止时间、优先级管理等",
                    # 参数处理指南
                    "**参数处理:**",
                    "- 优先级: 根据用户描述推断，紧急/重要→high，一般→medium，不急→low",
                    "- 截止时间: 识别'明天'、'下周'、'月底'等自然表达，转换为具体日期格式",
                    "- 任务ID: 当用户说'任务1'、'第一个任务'时，提取数字作为task_id",
                    "- 状态: pending(待处理)、in_progress(进行中)、completed(已完成)、cancelled(已取消)",
                    # 回应风格
                    "**回应风格:**",
                    "- 使用友好、专业但不过于正式的语气",
                    "- 多使用emoji来增强表达效果(如✅表示成功、❌表示错误、📋表示列表等)",
                    "- 对于复杂操作，分步骤说明",
                    "- 在适当时候提供操作建议和最佳实践",
                    # 特殊功能
                    "**特殊功能:**",
                    "- 日报生成: 当用户要求生成日报时，使用工具获取今日任务完成情况并生成报告",
                    "- 智能任务添加: 从用户的自然语言描述中智能提取任务信息",
                    "- 批量操作: 支持一次处理多个相关任务的请求",
                ],
                storage=storage,
                add_history_to_messages=True,
                num_history_runs=5,
                num_history_responses=5,
                tools=[
                    TodoToolkit(),
                    CalculatorTools(
                        add=True,
                        subtract=True,
                        multiply=True,
                        divide=True,
                        exponentiate=True,
                        factorial=True,
                        is_prime=True,
                        square_root=True,
                    ),
                ],
                markdown=True,
            )
        except Exception as e:
            console.print(f"⚠️ AI助手初始化失败: {e}", style="yellow")
            console.print("将以基础模式运行（无AI功能）", style="dim")
            self.agent = None

    def _get_ai_model(self, model_name: Optional[str] = None):
        """获取AI模型实例

        Args:
            model_name: 模型名称 (dashscope, openai, gemini)，如果为None则自动选择

        Returns:
            AI模型实例
        """
        # 检查环境变量
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        # 如果指定了模型名称，优先使用指定的模型
        if model_name:
            return self._create_model_by_name(
                model_name, dashscope_api_key, openai_api_key, google_api_key
            )

        # 自动选择模型（按优先级）
        # 1. DashScope
        if dashscope_api_key:
            try:
                console.print("🔧 使用DashScope AI模型", style="blue")
                return DashScope(id="qwen-plus", api_key=dashscope_api_key)
            except Exception as e:
                console.print(f"⚠️ DashScope模型初始化失败: {e}", style="yellow")

        # 2. Gemini
        if google_api_key:
            try:
                console.print("🔧 使用Gemini AI模型", style="blue")
                return Gemini(id="gemini-2.0-flash-exp")
            except Exception as e:
                console.print(f"⚠️ Gemini模型初始化失败: {e}", style="yellow")

        # 3. OpenAI
        if openai_api_key:
            try:
                console.print("🔧 使用OpenAI AI模型", style="blue")
                return OpenAIChat(id="gpt-4o-mini")
            except Exception as e:
                console.print(f"⚠️ OpenAI模型初始化失败: {e}", style="yellow")

        # 如果都没有配置，使用默认的OpenAI模型（需要用户配置API密钥）
        console.print("🔧 使用默认OpenAI模型（请配置API密钥）", style="blue")
        return OpenAIChat(id="gpt-4o-mini")

    def _create_model_by_name(
        self,
        model_name: str,
        dashscope_api_key: Optional[str],
        openai_api_key: Optional[str],
        google_api_key: Optional[str],
    ):
        """根据模型名称创建模型实例

        Args:
            model_name: 模型名称
            dashscope_api_key: DashScope API密钥
            openai_api_key: OpenAI API密钥
            google_api_key: Google API密钥

        Returns:
            AI模型实例
        """
        model_name = model_name.lower()

        if model_name == "dashscope":
            if not dashscope_api_key:
                raise ValueError("未配置DASHSCOPE_API_KEY环境变量")
            console.print("🔧 使用DashScope AI模型", style="blue")
            return DashScope(id="qwen-turbo", api_key=dashscope_api_key)

        elif model_name == "gemini":
            if not google_api_key:
                raise ValueError("未配置GOOGLE_API_KEY环境变量")
            console.print("🔧 使用Gemini AI模型", style="blue")
            return Gemini(id="gemini-2.0-flash-exp")

        elif model_name == "openai":
            if not openai_api_key:
                raise ValueError("未配置OPENAI_API_KEY环境变量")
            console.print("🔧 使用OpenAI AI模型", style="blue")
            return OpenAIChat(id="gpt-4o-mini")

        else:
            raise ValueError(
                f"不支持的模型类型: {model_name}。支持的类型: dashscope, gemini, openai"
            )

    def is_available(self) -> bool:
        """检查AI助手是否可用"""
        return self.agent is not None

    def chat(self, message: str, model_name: Optional[str] = None) -> str:
        """与AI助手对话

        Args:
            message: 用户消息
            model_name: 指定使用的模型 (dashscope, openai, gemini)

        Returns:
            AI助手回复
        """
        try:
            # 如果指定了模型，创建新的agent
            if model_name:
                agent = self._create_agent_with_model(model_name)
            else:
                agent = self.agent

            if not agent:
                return "AI助手当前不可用，请检查网络连接或API密钥配置。"

            # 为AI提供当前任务上下文
            context = self._get_task_context()
            full_message = f"{context}\n\n用户消息: {message}"

            # 获取AI回复
            response = agent.run(full_message)
            return response.content if response.content else "AI助手回复为空"
        except Exception as e:
            console.print(f"AI对话错误: {e}", style="red")
            return f"抱歉，AI处理过程中出现错误: {e}"

    def _create_agent_with_model(self, model_name: str) -> Optional[Agent]:
        """使用指定模型创建Agent

        Args:
            model_name: 模型名称

        Returns:
            Agent实例或None
        """
        try:
            # 配置AI助手存储
            storage = SqliteStorage(
                table_name="ai_assistant_sessions",
                db_file=os.path.expanduser("~/.todo/ai_sessions.db"),
            )

            # 获取指定模型
            model = self._get_ai_model(model_name)

            # 创建AI代理
            return Agent(
                name="Todo AI Assistant",
                model=model,
                instructions=[
                    # 核心身份和职责
                    f"现在的时间是：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}，你是一个专业的待办事项管理助手，名为Todo AI Assistant。你的核心职责是帮助用户高效管理他们的待办事项。",
                    # 工具使用指南
                    "**工具使用指南:**",
                    "- add_todo_task: 当用户想要创建新任务时使用，支持标题、描述、优先级(low/medium/high)、截止时间等参数",
                    "- list_todo_tasks: 当用户想查看任务列表时使用，支持按状态和优先级筛选",
                    "- get_todo_task: 当用户询问特定任务详情时使用，需要任务ID",
                    "- update_todo_task: 当用户想修改任务信息时使用，可更新标题、描述、优先级、状态、截止时间等",
                    "- complete_todo_task: 当用户说完成了某个任务时使用",
                    "- delete_todo_task: 当用户想删除任务时使用",
                    "- search_todo_tasks: 当用户搜索包含特定关键词的任务时使用",
                    # 自然语言理解
                    "**自然语言理解:**",
                    "- '添加任务'、'创建任务'、'新建'、'记录' → 使用add_todo_task",
                    "- '列出'、'显示'、'查看所有'、'我的任务' → 使用list_todo_tasks",
                    "- '查看任务X'、'任务X的详情' → 使用get_todo_task",
                    "- '修改'、'更新'、'改变' → 使用update_todo_task",
                    "- '完成了'、'做完了'、'已完成' → 使用complete_todo_task",
                    "- '删除'、'移除'、'取消' → 使用delete_todo_task",
                    "- '搜索'、'查找'、'包含' → 使用search_todo_tasks",
                    # 交互原则
                    "**交互原则:**",
                    "1. 始终首先使用合适的工具执行用户请求",
                    "2. 根据工具返回结果向用户提供友好的反馈",
                    "3. 如果用户请求不明确，主动询问需要的参数(如任务ID、具体内容等)",
                    "4. 当操作成功时，提供积极的确认反馈",
                    "5. 当操作失败时，解释原因并建议解决方案",
                    "6. 主动提供有用的建议，如提醒截止时间、优先级管理等",
                    # 参数处理指南
                    "**参数处理:**",
                    "- 优先级: 根据用户描述推断，紧急/重要→high，一般→medium，不急→low",
                    "- 截止时间: 识别'明天'、'下周'、'月底'等自然表达，转换为具体日期格式",
                    "- 任务ID: 当用户说'任务1'、'第一个任务'时，提取数字作为task_id",
                    "- 状态: pending(待处理)、in_progress(进行中)、completed(已完成)、cancelled(已取消)",
                    # 回应风格
                    "**回应风格:**",
                    "- 使用友好、专业但不过于正式的语气",
                    "- 多使用emoji来增强表达效果(如✅表示成功、❌表示错误、📋表示列表等)",
                    "- 对于复杂操作，分步骤说明",
                    "- 在适当时候提供操作建议和最佳实践",
                    # 特殊功能
                    "**特殊功能:**",
                    "- 日报生成: 当用户要求生成日报时，使用工具获取今日任务完成情况并生成报告",
                    "- 智能任务添加: 从用户的自然语言描述中智能提取任务信息",
                    "- 批量操作: 支持一次处理多个相关任务的请求",
                ],
                storage=storage,
                add_history_to_messages=True,
                num_history_responses=5,
                tools=[TodoToolkit()],
                show_tool_calls=True,
                markdown=True,
            )
        except Exception as e:
            console.print(f"⚠️ 创建Agent失败: {e}", style="yellow")
            return None

    def smart_add_task(
        self, description: str, model_name: Optional[str] = None
    ) -> Optional[Task]:
        """智能添加任务

        Args:
            description: 任务描述
            model_name: 指定使用的模型 (dashscope, openai, gemini)

        Returns:
            创建的任务对象或None
        """
        try:
            # 如果指定了模型，创建新的agent
            if model_name:
                agent = self._create_agent_with_model(model_name)
            else:
                agent = self.agent

            if not agent:
                console.print(
                    "AI助手不可用，请使用基础的 'todo add' 命令", style="yellow"
                )
                return None

            # 让AI分析任务描述
            prompt = dedent(
                f"""\
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
            """
            )

            response = agent.run(prompt)

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
                            "low": TaskPriority.LOW,
                        }
                        priority = priority_map.get(
                            task_data.get("priority", "medium"), TaskPriority.MEDIUM
                        )

                        # 创建任务
                        task = self.task_service.create_task(
                            title=task_data.get("title", description),
                            description=task_data.get("description"),
                            priority=priority,
                            due_date=task_data.get("due_date"),
                        )
                        return task
                except json.JSONDecodeError:
                    # 如果JSON解析失败，回退到基础创建
                    console.print(
                        "AI响应格式异常，使用基础模式创建任务", style="yellow"
                    )
                    pass

            # 回退到基础任务创建
            task = self.task_service.create_task(
                title=description, priority=TaskPriority.MEDIUM
            )
            return task

        except Exception as e:
            console.print(f"智能添加任务失败: {e}", style="red")
            return None

    def generate_daily_report(
        self, date: Optional[datetime] = None, model_name: Optional[str] = None
    ) -> str:
        """生成日报

        Args:
            date: 指定日期，默认为今天
            model_name: 指定使用的模型 (dashscope, openai, gemini)

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
                if (
                    task.completed_at
                    and task.completed_at.strftime("%Y-%m-%d") == date_str
                ):
                    completed_today.append(task)

            # 获取待处理和过期任务
            pending_tasks = self.task_service.get_pending_tasks()
            overdue_tasks = [
                t for t in pending_tasks if t.due_date and t.due_date < date
            ]

            # 如果指定了模型，创建新的agent
            if model_name:
                agent = self._create_agent_with_model(model_name)
            else:
                agent = self.agent

            if agent:
                # 使用AI生成报告
                prompt = dedent(
                    f"""\
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
                """
                )

                response = agent.run(prompt)
                return response.content if response.content else "AI生成报告失败"
            else:
                # 基础日报生成
                return self._generate_basic_report(
                    date, today_tasks, completed_today, pending_tasks, overdue_tasks
                )

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
                    due_info = (
                        f"，截止：{format_datetime(task.due_date, 'short')}"
                        if task.due_date
                        else ""
                    )
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
            due_info = (
                f"，截止：{format_datetime(task.due_date)}" if task.due_date else ""
            )
            formatted.append(f"- {task.title} ({task.priority.value}{due_info})")

        return "\n".join(formatted)

    def _generate_basic_report(
        self,
        date: datetime,
        today_tasks: List[Task],
        completed_today: List[Task],
        pending_tasks: List[Task],
        overdue_tasks: List[Task],
    ) -> str:
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
                due_info = (
                    f" (截止：{format_datetime(task.due_date, 'short')})"
                    if task.due_date
                    else ""
                )
                report += f"- {task.title}{due_info}\n"
            if len(pending_tasks) > 5:
                report += f"- ... 还有 {len(pending_tasks) - 5} 个任务\n"
            report += "\n"

        if overdue_tasks:
            report += "## ⚠️ 过期任务\n"
            for task in overdue_tasks:
                overdue_due_info = (
                    f"过期：{format_datetime(task.due_date, 'short')}"
                    if task.due_date
                    else "过期"
                )
                report += f"- {task.title} ({overdue_due_info})\n"
            report += "\n"

        report += "## 💡 建议\n"
        if overdue_tasks:
            report += "- 优先处理过期任务\n"
        if len(pending_tasks) > 10:
            report += "- 任务较多，建议按优先级整理\n"
        report += "- 保持专注，一次专心做一件事\n"

        return report
