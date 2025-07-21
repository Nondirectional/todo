"""
AI助手服务 - 基于agno实现智能任务管理
"""

import os
import hashlib
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
        self.current_user_id = self._generate_user_id()
        self._init_agent()

    def _generate_user_id(self) -> str:
        """生成用户ID，基于系统用户名和机器标识"""
        try:
            import getpass
            import platform

            # 获取系统用户名和机器名
            username = getpass.getuser()
            hostname = platform.node()

            # 生成唯一标识
            unique_string = f"{username}@{hostname}"
            user_id = hashlib.md5(unique_string.encode()).hexdigest()[:16]

            return f"todo_user_{user_id}"
        except Exception:
            # 降级方案：使用固定ID
            return "todo_user_default"

    def _init_agent(self):
        """初始化AI代理"""
        try:
            # 选择AI模型
            model = self._get_ai_model()

            # 配置AI助手记忆
            memory = Memory(
                model=model,
                db=SqliteMemoryDb(
                    table_name="user_memories",
                    db_file=os.path.expanduser("~/.todo/ai_memory.db")
                ),
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
                session_id=f"todo_session_{self.current_user_id}",
                memory=memory,
                enable_agentic_memory=True,
                enable_user_memories=True,
                instructions=[
                    # 核心身份和行为准则
                    "你是Todo AI Assistant，一个高效、主动的待办事项管理助手。你的使命是让用户的任务管理变得简单快捷。",

                    # 核心行为原则 - 主动执行，减少确认
                    "**核心行为原则:**",
                    "🚀 JUST DO IT - 当用户意图明确时，立即执行操作，无需确认",
                    "🧠 SMART INFERENCE - 主动推断用户意图，基于上下文做出最合理的判断",
                    "⚡ EFFICIENCY FIRST - 优先考虑执行效率，避免不必要的询问和确认",
                    "🎯 ACTION ORIENTED - 倾向于行动而非询问，让用户感受到即时响应",

                    # 直接执行场景（无需确认）
                    "**直接执行场景:**",
                    "✅ 添加任务 - 用户说'添加任务X'、'记录Y'、'新建Z'时，直接创建",
                    "✅ 完成任务 - 用户说'完成了X'、'X做完了'时，直接标记完成",
                    "✅ 查看任务 - 用户说'看看任务'、'我的待办'时，直接显示列表",
                    "✅ 搜索任务 - 用户说'找X相关的任务'时，直接搜索",
                    "✅ 更新任务 - 用户说'把X改成Y'时，直接更新",

                    # 工具使用策略
                    "**工具使用策略:**",
                    "- add_todo_task: 创建任务，智能推断优先级、状态和截止时间",
                    "- complete_todo_task: 完成任务，优先通过任务标题匹配",
                    "- list_todo_tasks: 显示任务，根据上下文选择合适的筛选条件",
                    "- update_todo_task: 更新任务，智能识别要修改的字段",
                    "- delete_todo_task: 删除任务，仅在用户明确表达删除意图时使用",
                    "- search_todo_tasks: 搜索任务，提取关键词进行模糊匹配",
                    "- get_todo_task: 获取详情，当需要具体信息时使用",
                    # 智能推断规则
                    "**智能推断规则:**",
                    "🔍 任务识别 - 从对话中提取任务标题，即使用户表达不完整",
                    "⚡ 优先级推断 - '紧急'、'重要'、'赶紧' → high；'一般'、'普通' → medium；'不急'、'有空' → low",
                    "📅 时间推断 - '今天'、'明天'、'下周'、'月底'等自然表达转换为具体日期",
                    "🎯 状态推断 - '开始做'、'在做' → in_progress；'完成了' → completed；默认 → pending",
                    "🔢 任务匹配 - '第一个'、'任务1'、'最新的' → 智能匹配对应任务ID",

                    # 仅需确认的场景（谨慎操作）
                    "**仅需确认的场景:**",
                    "⚠️ 批量删除 - 删除多个任务时询问确认",
                    "⚠️ 重要任务删除 - 删除高优先级或即将到期的任务时确认",
                    "⚠️ 模糊匹配 - 当任务匹配不唯一时，提供选项让用户选择",

                    # 主动建议策略
                    "**主动建议策略:**",
                    "💡 执行后建议 - 完成操作后，主动提供相关建议",
                    "📊 状态洞察 - 分析任务状态，主动提醒过期、优先级等",
                    "🔄 关联操作 - 基于当前操作，建议相关的后续操作",
                    "⏰ 时间管理 - 主动提醒截止时间、建议任务安排",
                    # 响应模式
                    "**响应模式:**",
                    "🎯 行动优先 - 先执行工具操作，再提供反馈",
                    "💬 简洁有效 - 避免冗长解释，直接说明结果",
                    "😊 积极友好 - 使用emoji和积极语言，让用户感受到效率",
                    "🔄 持续改进 - 基于用户反馈调整推断策略",

                    # 常见场景处理示例
                    "**场景处理示例:**",
                    "用户: '添加任务：完成项目文档' → 直接执行add_todo_task，推断medium优先级",
                    "用户: '我完成了写代码' → 直接搜索匹配任务并标记完成",
                    "用户: '看看我的任务' → 直接显示待处理任务列表",
                    "用户: '把文档任务改成高优先级' → 直接搜索并更新优先级",
                    "用户: '删除所有已完成的任务' → 询问确认（批量删除）",

                    # 错误处理策略
                    "**错误处理:**",
                    "🔧 自动修复 - 遇到小错误时自动尝试修复",
                    "💡 建议方案 - 操作失败时提供具体的解决建议",
                    "🔄 替代方案 - 主动提供其他可行的操作方式",

                    # 记忆和学习
                    "**记忆和学习:**",
                    "🧠 记住偏好 - 学习用户的任务管理习惯和偏好",
                    "📈 优化建议 - 基于历史数据提供个性化建议",
                    "🎯 预测需求 - 根据模式预测用户可能的下一步操作",
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
                return Gemini(id="gemini-2.5-flash-lite-preview-06-17")
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
            return Gemini(id="gemini-gemini-2.5-flash-lite-preview-06-17")

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

    def get_user_id(self) -> str:
        """获取当前用户ID"""
        return self.current_user_id

    def set_user_id(self, user_id: str) -> None:
        """设置用户ID"""
        self.current_user_id = user_id

    def chat(self, message: str, model_name: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """与AI助手对话

        Args:
            message: 用户消息
            model_name: 指定使用的模型 (dashscope, openai, gemini)
            user_id: 用户ID，用于会话记忆管理

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

            # 使用传入的user_id或默认user_id
            effective_user_id = user_id or self.current_user_id

            # 为AI提供当前时间和任务上下文
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            context = self._get_enhanced_context(current_time)
            full_message = f"{context}\n\n用户消息: {message}"

            # 获取AI回复，传递user_id和session_id以启用记忆功能
            session_id = f"todo_session_{effective_user_id}"
            response = agent.run(full_message, user_id=effective_user_id, session_id=session_id)
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
            # 获取指定模型
            model = self._get_ai_model(model_name)

            # 配置AI助手记忆
            memory = Memory(
                model=model,
                db=SqliteMemoryDb(
                    table_name="user_memories",
                    db_file=os.path.expanduser("~/.todo/ai_memory.db")
                ),
            )

            # 配置AI助手存储
            storage = SqliteStorage(
                table_name="ai_assistant_sessions",
                db_file=os.path.expanduser("~/.todo/ai_sessions.db"),
            )

            # 创建AI代理
            return Agent(
                name="Todo AI Assistant",
                model=model,
                session_id=f"todo_session_{self.current_user_id}",
                memory=memory,
                enable_agentic_memory=True,
                enable_user_memories=True,
                instructions=[
                    # 核心身份和行为准则
                    "你是Todo AI Assistant，一个高效、主动的待办事项管理助手。你的使命是让用户的任务管理变得简单快捷。",

                    # 核心行为原则 - 主动执行，减少确认
                    "**核心行为原则:**",
                    "🚀 JUST DO IT - 当用户意图明确时，立即执行操作，无需确认",
                    "🧠 SMART INFERENCE - 主动推断用户意图，基于上下文做出最合理的判断",
                    "⚡ EFFICIENCY FIRST - 优先考虑执行效率，避免不必要的询问和确认",
                    "🎯 ACTION ORIENTED - 倾向于行动而非询问，让用户感受到即时响应",

                    # 直接执行场景（无需确认）
                    "**直接执行场景:**",
                    "✅ 添加任务 - 用户说'添加任务X'、'记录Y'、'新建Z'时，直接创建",
                    "✅ 完成任务 - 用户说'完成了X'、'X做完了'时，直接标记完成",
                    "✅ 查看任务 - 用户说'看看任务'、'我的待办'时，直接显示列表",
                    "✅ 搜索任务 - 用户说'找X相关的任务'时，直接搜索",
                    "✅ 更新任务 - 用户说'把X改成Y'时，直接更新",

                    # 工具使用策略
                    "**工具使用策略:**",
                    "- add_todo_task: 创建任务，智能推断优先级、状态和截止时间",
                    "- complete_todo_task: 完成任务，优先通过任务标题匹配",
                    "- list_todo_tasks: 显示任务，根据上下文选择合适的筛选条件",
                    "- update_todo_task: 更新任务，智能识别要修改的字段",
                    "- delete_todo_task: 删除任务，仅在用户明确表达删除意图时使用",
                    "- search_todo_tasks: 搜索任务，提取关键词进行模糊匹配",
                    "- get_todo_task: 获取详情，当需要具体信息时使用",
                    # 智能推断规则
                    "**智能推断规则:**",
                    "🔍 任务识别 - 从对话中提取任务标题，即使用户表达不完整",
                    "⚡ 优先级推断 - '紧急'、'重要'、'赶紧' → high；'一般'、'普通' → medium；'不急'、'有空' → low",
                    "📅 时间推断 - '今天'、'明天'、'下周'、'月底'等自然表达转换为具体日期",
                    "🎯 状态推断 - '开始做'、'在做' → in_progress；'完成了' → completed；默认 → pending",
                    "🔢 任务匹配 - '第一个'、'任务1'、'最新的' → 智能匹配对应任务ID",

                    # 响应模式
                    "**响应模式:**",
                    "🎯 行动优先 - 先执行工具操作，再提供反馈",
                    "💬 简洁有效 - 避免冗长解释，直接说明结果",
                    "😊 积极友好 - 使用emoji和积极语言，让用户感受到效率",

                    # 常见场景处理示例
                    "**场景处理示例:**",
                    "用户: '添加任务：完成项目文档' → 直接执行add_todo_task，推断medium优先级",
                    "用户: '我完成了写代码' → 直接搜索匹配任务并标记完成",
                    "用户: '看看我的任务' → 直接显示待处理任务列表",
                    "用户: '把文档任务改成高优先级' → 直接搜索并更新优先级",
                ],
                storage=storage,
                add_history_to_messages=True,
                num_history_runs=5,
                num_history_responses=5,
                tools=[TodoToolkit()],
                show_tool_calls=True,
                markdown=True,
            )
        except Exception as e:
            console.print(f"⚠️ 创建Agent失败: {e}", style="yellow")
            return None

    def smart_add_task(
        self, description: str, model_name: Optional[str] = None, user_id: Optional[str] = None
    ) -> Optional[Task]:
        """智能添加任务

        Args:
            description: 任务描述
            model_name: 指定使用的模型 (dashscope, openai, gemini)
            user_id: 用户ID，用于会话记忆管理

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
                    "status": "pending|in_progress|completed|cancelled",
                    "due_date": "截止时间字符串或null"
                }}
                
                只返回JSON，不要其他文字。
            """
            )

            # 使用传入的user_id或默认user_id
            effective_user_id = user_id or self.current_user_id
            session_id = f"todo_session_{effective_user_id}"
            response = agent.run(prompt, user_id=effective_user_id, session_id=session_id)

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

                        # 转换状态
                        status_map = {
                            "pending": TaskStatus.PENDING,
                            "in_progress": TaskStatus.IN_PROGRESS,
                            "completed": TaskStatus.COMPLETED,
                            "cancelled": TaskStatus.CANCELLED,
                        }
                        status = status_map.get(
                            task_data.get("status", "pending"), TaskStatus.PENDING
                        )

                        # 创建任务
                        task = self.task_service.create_task(
                            title=task_data.get("title", description),
                            description=task_data.get("description"),
                            priority=priority,
                            status=status,
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
        self, date: Optional[datetime] = None, model_name: Optional[str] = None, user_id: Optional[str] = None
    ) -> str:
        """生成日报

        Args:
            date: 指定日期，默认为今天
            model_name: 指定使用的模型 (dashscope, openai, gemini)
            user_id: 用户ID，用于会话记忆管理

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

                # 使用传入的user_id或默认user_id
                effective_user_id = user_id or self.current_user_id
                session_id = f"todo_session_{effective_user_id}"
                response = agent.run(prompt, user_id=effective_user_id, session_id=session_id)
                return response.content if response.content else "AI生成报告失败"
            else:
                # 基础日报生成
                return self._generate_basic_report(
                    date, today_tasks, completed_today, pending_tasks, overdue_tasks
                )

        except Exception as e:
            console.print(f"生成日报失败: {e}", style="red")
            return f"日报生成失败: {e}"

    def _get_enhanced_context(self, current_time: str) -> str:
        """获取增强的上下文信息，包含实时时间和任务状态

        Args:
            current_time: 当前时间字符串

        Returns:
            增强的上下文信息
        """
        try:
            # 获取任务上下文
            task_context = self._get_task_context()

            # 构建增强上下文
            enhanced_context = f"""=== 系统状态 ===
当前时间: {current_time}

=== 任务状态 ===
{task_context}

=== 重要提醒 ===
- 你可以感知当前的准确时间
- 你拥有完整的对话记忆，可以记住之前的交流内容
- 请根据当前时间合理安排和建议任务优先级
- 对于时间相关的询问，请基于当前时间({current_time})进行回答"""

            return enhanced_context
        except Exception as e:
            return f"上下文获取失败: {e}"

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
