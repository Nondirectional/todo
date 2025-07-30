"""
Chat command module for Todo CLI.

Provides an interactive AI chat interface for managing todos using natural language.
"""

import json
import typer
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from todo.langchain_tools import ALL_TOOLS
from todo.utils.display import print_error, print_info, print_success
from todo.config import get_config_manager

# 创建子命令应用
app = typer.Typer(
    name="chat",
    help="Interactive AI chat for todo management",
    no_args_is_help=True
)

console = Console()


class TodoChatBot:
    """Todo 聊天机器人类"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
        """初始化聊天机器人
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model_name: 模型名称
        """
        self.console = Console()
        self.messages = []
        self.tools_dict = {tool.name: tool for tool in ALL_TOOLS}
        
        # 初始化模型
        try:
            self.model = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
            ).bind_tools(ALL_TOOLS)
        except Exception as e:
            raise typer.Exit(f"Failed to initialize AI model: {e}")
        
        # 设置系统提示
        system_prompt = """
你是专注于待办系统管理的 AI 助手，核心职责是通过调用系统提供的工具，协助用户高效完成任务、分类、标签的全流程管理。

你的能力包括：
1. 任务管理：创建、查看、更新、完成、删除任务
2. 分类管理：创建、查看、更新、删除分类
3. 标签管理：创建、查看、更新、删除标签
4. 高级搜索：根据各种条件搜索和过滤任务

请理解用户需求，精准匹配工具功能，确保操作准确且反馈清晰。
当用户询问当前时间时，请使用 current_datetime 工具获取准确时间。

请用简洁、友好的语言回复用户，避免过于技术性的表述。
"""
        self.messages.append(SystemMessage(system_prompt.strip()))
    
    def pretty_print_json(self, data: str) -> str:
        """格式化 JSON 字符串"""
        try:
            if isinstance(data, str):
                parsed_json = json.loads(data)
            else:
                parsed_json = data
            return json.dumps(parsed_json, indent=2, sort_keys=False, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return str(data)
    
    def display_welcome(self):
        """显示欢迎信息"""
        welcome_text = """
# 🤖 Todo AI 助手

欢迎使用 Todo AI 助手！我可以帮助您：

- 📝 **任务管理**：创建、查看、更新、完成任务
- 📁 **分类管理**：组织任务分类
- 🏷️ **标签管理**：为任务添加标签
- 🔍 **智能搜索**：快速找到需要的任务

**使用示例：**
- "创建一个任务：学习Python"
- "列出所有待办任务"
- "创建一个工作分类"
- "搜索包含'学习'的任务"

输入 `exit` 或 `quit` 退出聊天。
"""
        self.console.print(Panel(Markdown(welcome_text), title="Todo AI 助手", border_style="blue"))
    
    def display_tool_result(self, tool_name: str, args: dict, result: str):
        """显示工具执行结果"""
        # 解析结果
        try:
            result_data = json.loads(result) if isinstance(result, str) else result
            
            # 创建结果表格
            table = Table(title=f"🔧 工具执行: {tool_name}", show_header=True, header_style="bold magenta")
            table.add_column("参数", style="cyan", width=20)
            table.add_column("值", style="white")
            
            # 添加参数行
            for key, value in args.items():
                table.add_row(key, str(value))
            
            self.console.print(table)
            
            # 显示结果
            if isinstance(result_data, dict):
                if result_data.get("success"):
                    self.console.print(Panel(
                        self.pretty_print_json(result_data), 
                        title="✅ 执行成功", 
                        border_style="green"
                    ))
                elif result_data.get("error"):
                    self.console.print(Panel(
                        result_data["error"], 
                        title="❌ 执行失败", 
                        border_style="red"
                    ))
                else:
                    self.console.print(Panel(
                        self.pretty_print_json(result_data), 
                        title="📋 执行结果", 
                        border_style="yellow"
                    ))
            else:
                self.console.print(Panel(str(result_data), title="📋 执行结果", border_style="yellow"))
                
        except Exception as e:
            self.console.print(Panel(f"结果解析错误: {e}\n原始结果: {result}", title="⚠️ 警告", border_style="yellow"))
    
    def chat(self):
        """开始聊天循环"""
        self.display_welcome()
        
        while True:
            try:
                # 获取用户输入
                user_input = self.console.input("\n[bold blue]You:[/bold blue] ")
                
                if user_input.lower() in ['exit', 'quit', '退出']:
                    self.console.print("[bold green]再见！感谢使用 Todo AI 助手！[/bold green]")
                    break
                
                if not user_input.strip():
                    continue
                
                # 添加用户消息
                self.messages.append(HumanMessage(user_input))
                
                # 获取 AI 响应
                response = self.model.invoke(self.messages)
                self.messages.append(response)
                
                # 处理工具调用
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        
                        # 执行工具
                        tool_output = self.tools_dict[tool_name].invoke(tool_call)
                        self.messages.append(tool_output)
                        
                        # 显示工具执行结果
                        self.display_tool_result(tool_name, tool_args, tool_output.content)
                    
                    # 获取最终响应
                    final_response = self.model.invoke(self.messages)
                    self.messages.append(final_response)
                    
                    # 显示 AI 回复
                    self.console.print(f"\n[bold green]AI:[/bold green] {final_response.content}")
                else:
                    # 直接显示 AI 回复
                    self.console.print(f"\n[bold green]AI:[/bold green] {response.content}")
                
                # 消息修剪，保持对话历史在合理范围内
                if len(self.messages) > 20:
                    # 保留系统消息和最近的对话
                    system_msg = self.messages[0]
                    recent_msgs = self.messages[-15:]
                    self.messages = [system_msg] + recent_msgs
                    
            except KeyboardInterrupt:
                self.console.print("\n[bold yellow]聊天被中断[/bold yellow]")
                break
            except Exception as e:
                self.console.print(f"[bold red]发生错误: {e}[/bold red]")
                continue


@app.command()
def start(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Override API key from config"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-u", help="Override API base URL from config"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model name from config")
):
    """Start interactive AI chat for todo management."""
    try:
        config_mgr = get_config_manager()

        # 获取有效配置（命令行参数 > 配置文件 > 默认值）
        effective_config = config_mgr.get_effective_chat_config(
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        # 检查 API 密钥
        if not effective_config['api_key']:
            print_error("API key is required. Please configure it first:")
            print_info("  todo chat config set --api-key 'your-api-key'")
            print_info("Or use the --api-key option:")
            print_info("  todo chat start --api-key 'your-api-key'")
            raise typer.Exit(1)

        print_info("Initializing Todo AI Assistant...")

        # 创建并启动聊天机器人
        bot = TodoChatBot(
            api_key=effective_config['api_key'],
            base_url=effective_config['base_url'],
            model_name=effective_config['model']
        )
        bot.chat()

    except Exception as e:
        print_error(f"Failed to start chat: {e}")
        raise typer.Exit(1)


# 创建配置子命令组
config_app = typer.Typer(name="config", help="Manage chat configuration")


@config_app.command("set")
def config_set(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Set API key"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-u", help="Set API base URL"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Set model name")
):
    """Set chat configuration."""
    config_mgr = get_config_manager()

    # 检查是否有任何配置项
    if not any([api_key, base_url, model]):
        print_error("At least one configuration option is required.")
        print_info("Available options: --api-key, --base-url, --model")
        raise typer.Exit(1)

    try:
        # 保存配置
        config_mgr.set_chat_config(
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        print_success("Chat configuration updated successfully!")

        # 显示更新的配置项
        if api_key:
            print_info(f"API Key: {'*' * (len(api_key) - 8) + api_key[-8:] if len(api_key) > 8 else '***'}")
        if base_url:
            print_info(f"Base URL: {base_url}")
        if model:
            print_info(f"Model: {model}")

    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        raise typer.Exit(1)


@config_app.command("show")
def config_show():
    """Show current chat configuration."""
    config_mgr = get_config_manager()
    chat_config = config_mgr.get_chat_config()

    if not chat_config:
        print_info("No chat configuration found.")
        print_info("Use 'todo chat config set' to configure chat settings.")
        return

    # 创建配置表格
    table = Table(title="Chat Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", width=15)
    table.add_column("Value", style="white")

    # 添加配置项
    api_key = chat_config.get('api_key', 'Not set')
    if api_key != 'Not set' and len(api_key) > 8:
        api_key = '*' * (len(api_key) - 8) + api_key[-8:]

    table.add_row("API Key", api_key)
    table.add_row("Base URL", chat_config.get('base_url', 'Not set'))
    table.add_row("Model", chat_config.get('model', 'Not set'))

    console.print(table)


@config_app.command("reset")
def config_reset(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Reset chat configuration."""
    config_mgr = get_config_manager()

    if not config_mgr.has_chat_config():
        print_info("No chat configuration to reset.")
        return

    if not confirm:
        if not typer.confirm("Are you sure you want to reset all chat configuration?"):
            print_info("Reset cancelled.")
            return

    try:
        config_mgr.reset_chat_config()
        print_success("Chat configuration reset successfully!")
    except Exception as e:
        print_error(f"Failed to reset configuration: {e}")
        raise typer.Exit(1)


@config_app.command("help")
def config_help():
    """Show configuration help and examples."""
    help_text = """
# Todo Chat Configuration

## Quick Setup
```bash
# Set API key (required)
todo chat config set --api-key "your-api-key-here"

# Set custom endpoint
todo chat config set --base-url "https://api.example.com/v1" --model "custom-model"
```

## Configuration Commands
- `todo chat config set` - Set configuration options
- `todo chat config show` - Display current configuration
- `todo chat config reset` - Reset all configuration
- `todo chat config help` - Show this help

## Supported Models
- **OpenAI**: gpt-3.5-turbo, gpt-4, gpt-4-turbo
- **Compatible APIs**: Any OpenAI-compatible endpoint

## Example Configurations
```bash
# OpenAI (default)
todo chat config set --api-key "sk-..."

# DeepSeek
todo chat config set --api-key "your-key" --base-url "https://api.deepseek.com/v1" --model "deepseek-chat"

# Alibaba Qwen
todo chat config set --api-key "your-key" --base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" --model "qwen-turbo"
```

## Priority Order
Command line options > Saved configuration > Default values
"""
    console.print(Panel(Markdown(help_text), title="Chat Configuration Help", border_style="blue"))


# 将配置子命令添加到主应用
app.add_typer(config_app, name="config")
