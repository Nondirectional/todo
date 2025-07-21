"""
Todo Agno工具包 - 为AI助手提供自主待办管理能力
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from agno.tools import Toolkit, tool

from src.services.task_service import TaskService
from src.models.task import Task, TaskStatus, TaskPriority


class TodoToolkit(Toolkit):
    """
    Todo工具包 - 为AI助手提供完整的待办事项管理功能
    
    支持的操作：
    - 添加待办事项
    - 更新待办事项
    - 删除待办事项
    - 查询待办事项
    - 列出待办事项
    - 完成待办事项
    - 搜索待办事项
    """
    
    def __init__(
        self,
        add_task: bool = True,
        update_task: bool = True,
        delete_task: bool = True,
        get_task: bool = True,
        list_tasks: bool = True,
        complete_task: bool = True,
        search_tasks: bool = True,
        show_result_tools: Optional[List[str]] = None,
        stop_after_tool_call_tools: Optional[List[str]] = None,
        **kwargs
    ):
        """
        初始化Todo工具包
        
        Args:
            add_task: 启用添加任务工具
            update_task: 启用更新任务工具
            delete_task: 启用删除任务工具
            get_task: 启用查询任务工具
            list_tasks: 启用列表任务工具
            complete_task: 启用完成任务工具
            search_tasks: 启用搜索任务工具
            show_result_tools: 显示结果的工具名称列表
            stop_after_tool_call_tools: 执行后停止的工具名称列表
        """
        # 构建工具列表
        tools = []
        self.task_service = TaskService()
        
        if add_task:
            tools.append(self.add_todo_task)
        if update_task:
            tools.append(self.update_todo_task)
        if delete_task:
            tools.append(self.delete_todo_task)
        if get_task:
            tools.append(self.get_todo_task)
        if list_tasks:
            tools.append(self.list_todo_tasks)
        if complete_task:
            tools.append(self.complete_todo_task)
        if search_tasks:
            tools.append(self.search_todo_tasks)
        
        # 初始化Toolkit
        super().__init__(
            name="todo_toolkit",
            tools=tools,
            show_result_tools=show_result_tools,
            stop_after_tool_call_tools=stop_after_tool_call_tools,
            **kwargs
        )

    def add_todo_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        status: str = "pending",
        due_date: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加新的待办事项

        Args:
            title: 任务标题，必填
            description: 任务描述，可选
            priority: 任务优先级，可选值：low, medium, high，默认为medium
            status: 任务状态，可选值：pending, in_progress, completed, cancelled，默认为pending
            due_date: 截止时间，格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD，可选
            tags: 标签字典，可选

        Returns:
            创建结果的文本描述
        """
        try:
            # 验证优先级
            try:
                task_priority = TaskPriority(priority.lower())
            except ValueError:
                return f"错误：无效的优先级 '{priority}'，请使用 low, medium 或 high"

            # 验证状态
            try:
                task_status = TaskStatus(status.lower())
            except ValueError:
                return f"错误：无效的状态 '{status}'，请使用 pending, in_progress, completed 或 cancelled"

            # 创建任务
            task = self.task_service.create_task(
                title=title,
                description=description,
                priority=task_priority,
                status=task_status,
                due_date=due_date,
                tags=tags
            )
            
            result_parts = [f"✅ 成功创建任务 #{task.id}: {task.title}"]
            if description:
                result_parts.append(f"📝 描述: {description}")
            if priority != "medium":
                result_parts.append(f"⚡ 优先级: {priority}")
            if status != "pending":
                result_parts.append(f"📊 状态: {status}")
            if due_date:
                result_parts.append(f"⏰ 截止时间: {due_date}")
            if tags:
                result_parts.append(f"🏷️ 标签: {tags}")
                
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"❌ 创建任务失败: {str(e)}"

    def update_todo_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        更新现有的待办事项
        
        Args:
            task_id: 任务ID，必填
            title: 新的任务标题，可选
            description: 新的任务描述，可选
            priority: 新的任务优先级，可选值：low, medium, high
            due_date: 新的截止时间，格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD，可选
            status: 新的任务状态，可选值：pending, in_progress, completed, cancelled
            tags: 新的标签字典，可选
            
        Returns:
            更新结果的文本描述
        """
        try:
            # 检查任务是否存在
            existing_task = self.task_service.get_task(task_id)
            if not existing_task:
                return f"❌ 任务 #{task_id} 不存在"
            
            # 准备更新参数
            update_params = {}
            changes = []
            
            if title is not None:
                update_params["title"] = title
                changes.append(f"标题: {title}")
            if description is not None:
                update_params["description"] = description
                changes.append(f"描述: {description}")
            if priority is not None:
                try:
                    task_priority = TaskPriority(priority.lower())
                    update_params["priority"] = task_priority
                    changes.append(f"优先级: {priority}")
                except ValueError:
                    return f"错误：无效的优先级 '{priority}'，请使用 low, medium 或 high"
            if due_date is not None:
                update_params["due_date"] = due_date
                changes.append(f"截止时间: {due_date}")
            if status is not None:
                try:
                    task_status = TaskStatus(status.lower())
                    update_params["status"] = task_status
                    changes.append(f"状态: {status}")
                except ValueError:
                    return f"错误：无效的状态 '{status}'，请使用 pending, in_progress, completed 或 cancelled"
            if tags is not None:
                update_params["tags"] = tags
                changes.append(f"标签: {tags}")
            
            if not update_params:
                return "❌ 没有提供要更新的字段"
            
            # 执行更新
            updated_task = self.task_service.update_task(task_id, **update_params)
            if updated_task:
                return f"✅ 成功更新任务 #{task_id}: {updated_task.title}\n🔄 更新内容: {', '.join(changes)}"
            else:
                return f"❌ 更新任务 #{task_id} 失败"
                
        except Exception as e:
            return f"❌ 更新任务失败: {str(e)}"

    def delete_todo_task(self, task_id: int) -> str:
        """
        删除指定的待办事项
        
        Args:
            task_id: 要删除的任务ID
            
        Returns:
            删除结果的文本描述
        """
        try:
            # 先获取任务信息以便确认
            task = self.task_service.get_task(task_id)
            if not task:
                return f"❌ 任务 #{task_id} 不存在"
            
            # 执行删除
            success = self.task_service.delete_task(task_id)
            if success:
                return f"✅ 成功删除任务 #{task_id}: {task.title}"
            else:
                return f"❌ 删除任务 #{task_id} 失败"
                
        except Exception as e:
            return f"❌ 删除任务失败: {str(e)}"

    def get_todo_task(self, task_id: int) -> str:
        """
        查询指定的待办事项详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详情的文本描述
        """
        try:
            task = self.task_service.get_task(task_id)
            if not task:
                return f"❌ 任务 #{task_id} 不存在"
            
            # 格式化任务信息
            result_parts = [
                f"📋 任务 #{task.id}: {task.title}",
                f"📝 状态: {task.status.value}",
                f"⚡ 优先级: {task.priority.value}",
                f"📅 创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            if task.description:
                result_parts.append(f"📄 描述: {task.description}")
            if task.due_date:
                result_parts.append(f"⏰ 截止时间: {task.due_date.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.start_time:
                result_parts.append(f"▶️ 开始时间: {task.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.completed_at:
                result_parts.append(f"✅ 完成时间: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.tags:
                result_parts.append(f"🏷️ 标签: {task.tags}")
                
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"❌ 查询任务失败: {str(e)}"

    def list_todo_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: Optional[int] = 10
    ) -> str:
        """
        列出待办事项
        
        Args:
            status: 筛选状态，可选值：pending, in_progress, completed, cancelled
            priority: 筛选优先级，可选值：low, medium, high
            limit: 限制返回数量，默认10条
            
        Returns:
            任务列表的文本描述
        """
        try:
            # 验证筛选条件
            task_status = None
            if status:
                try:
                    task_status = TaskStatus(status.lower())
                except ValueError:
                    return f"错误：无效的状态 '{status}'，请使用 pending, in_progress, completed 或 cancelled"
            
            task_priority = None
            if priority:
                try:
                    task_priority = TaskPriority(priority.lower())
                except ValueError:
                    return f"错误：无效的优先级 '{priority}'，请使用 low, medium 或 high"
            
            # 获取任务列表
            tasks = self.task_service.list_tasks(
                status=task_status,
                priority=task_priority,
                limit=limit
            )
            
            if not tasks:
                filter_desc = []
                if status:
                    filter_desc.append(f"状态: {status}")
                if priority:
                    filter_desc.append(f"优先级: {priority}")
                filter_text = f" ({', '.join(filter_desc)})" if filter_desc else ""
                return f"📝 没有找到符合条件的任务{filter_text}"
            
            # 格式化任务列表
            result_parts = [f"📋 共找到 {len(tasks)} 个任务：\n"]
            for task in tasks:
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄", 
                    "completed": "✅",
                    "cancelled": "❌"
                }.get(task.status.value, "📝")
                
                priority_emoji = {
                    "low": "🔹",
                    "medium": "🔸",
                    "high": "🔴"
                }.get(task.priority.value, "🔸")
                
                task_line = f"{status_emoji} #{task.id} {task.title} {priority_emoji}"
                if task.due_date:
                    task_line += f" ⏰ {task.due_date.strftime('%m/%d')}"
                result_parts.append(task_line)
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"❌ 获取任务列表失败: {str(e)}"

    def complete_todo_task(self, task_id: int) -> str:
        """
        将指定的待办事项标记为完成
        
        Args:
            task_id: 要完成的任务ID
            
        Returns:
            完成操作结果的文本描述
        """
        try:
            # 检查任务是否存在
            existing_task = self.task_service.get_task(task_id)
            if not existing_task:
                return f"❌ 任务 #{task_id} 不存在"
            
            if existing_task.status == TaskStatus.COMPLETED:
                return f"ℹ️ 任务 #{task_id}: {existing_task.title} 已经是完成状态"
            
            # 标记为完成
            completed_task = self.task_service.complete_task(task_id)
            if completed_task:
                return f"🎉 成功完成任务 #{task_id}: {completed_task.title}\n✅ 完成时间: {completed_task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                return f"❌ 完成任务 #{task_id} 失败"
                
        except Exception as e:
            return f"❌ 完成任务失败: {str(e)}"

    def search_todo_tasks(self, keyword: str) -> str:
        """
        搜索包含关键词的待办事项
        
        Args:
            keyword: 搜索关键词（在标题和描述中搜索）
            
        Returns:
            搜索结果的文本描述
        """
        try:
            if not keyword or not keyword.strip():
                return "❌ 请提供搜索关键词"
            
            # 执行搜索
            tasks = self.task_service.search_tasks(keyword.strip())
            
            if not tasks:
                return f"🔍 没有找到包含 '{keyword}' 的任务"
            
            # 格式化搜索结果
            result_parts = [f"🔍 搜索 '{keyword}' 找到 {len(tasks)} 个结果：\n"]
            for task in tasks:
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅", 
                    "cancelled": "❌"
                }.get(task.status.value, "📝")
                
                priority_emoji = {
                    "low": "🔹",
                    "medium": "🔸",
                    "high": "🔴"
                }.get(task.priority.value, "🔸")
                
                task_line = f"{status_emoji} #{task.id} {task.title} {priority_emoji}"
                if task.description and keyword.lower() in task.description.lower():
                    task_line += f"\n   📄 {task.description[:50]}..."
                result_parts.append(task_line)
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"❌ 搜索任务失败: {str(e)}" 
        

if __name__ == "__main__":
    todo_toolkit = TodoToolkit()
    print(todo_toolkit.add_todo_task("test", "test", "high", "2025-07-18 12:11:51", {"test": "test"}))