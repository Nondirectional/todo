"""
AI助手CLI命令
"""
import os
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from src.services.ai_service import TodoAIAssistant
from src.services.task_service import TaskService

# 创建Rich控制台
console = Console()

# 任务服务和AI助手实例
task_service = TaskService()
ai_assistant = TodoAIAssistant(task_service)


def chat_command(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="指定AI模型 (dashscope, openai, gemini)")
):
    """开始与AI助手对话"""
    try:
        # 如果指定了模型，直接尝试使用
        if model:
            try:
                test_response = ai_assistant.chat("测试", model_name=model)
                if not test_response or "不可用" in test_response:
                    raise Exception(f"模型 {model} 不可用")
            except Exception as e:
                console.print(f"❌ 模型 {model} 不可用: {e}", style="bold red")
                console.print("请检查相应的API密钥配置", style="dim")
                raise typer.Exit(1)
        elif not ai_assistant.is_available():
            console.print("❌ AI助手不可用", style="bold red")
            console.print("请确保：", style="dim")
            console.print("1. 已设置API密钥环境变量 (OPENAI_API_KEY, DASHSCOPE_API_KEY, GOOGLE_API_KEY)", style="dim")
            console.print("2. 网络连接正常", style="dim")
            console.print("3. API密钥有效", style="dim")
            raise typer.Exit(1)
        
        console.print("🤖 Todo AI助手已启动！", style="bold green")
        console.print("💬 开始对话吧，输入 'exit' 或 'quit' 退出", style="dim")
        console.print("", style="dim")
        
        # 显示使用提示
        tips_panel = Panel(
            """🎯 你可以这样与我对话：
            
• "帮我添加一个任务：明天下午开会讨论项目进度"
• "我需要在本周五前完成报告，优先级很高"  
• "显示我今天的任务情况"
• "给我一些时间管理建议"
• "生成今天的工作报告"

我会理解你的自然语言并帮你管理任务！""",
            title="💡 使用提示",
            border_style="blue"
        )
        console.print(tips_panel)
        console.print()
        
        # 对话循环
        while True:
            try:
                # 获取用户输入
                user_input = Prompt.ask("[bold cyan]你[/bold cyan]")
                
                if not user_input.strip():
                    continue
                
                # 检查退出命令
                if user_input.lower() in ['exit', 'quit', '退出', '再见']:
                    console.print("👋 再见！祝你工作愉快！", style="bold green")
                    break
                
                # 发送给AI助手
                with console.status("🤔 AI正在思考...", spinner="dots"):
                    response = ai_assistant.chat(user_input, model_name=model)
                
                # 显示AI回复
                console.print("[bold green]🤖 AI助手[/bold green]:")
                if response.strip().startswith('#') or '```' in response:
                    # Markdown格式回复
                    console.print(Markdown(response))
                else:
                    console.print(response)
                
                console.print()  # 空行分隔
                
            except KeyboardInterrupt:
                console.print("\n👋 对话已中断，再见！", style="yellow")
                break
            except Exception as e:
                console.print(f"❌ 对话错误: {e}", style="red")
                continue
        
    except Exception as e:
        console.print(f"❌ 启动AI助手失败: {e}", style="bold red")
        raise typer.Exit(1)


def smart_add_command(
    description: str = typer.Argument(..., help="任务描述（支持自然语言）"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="指定AI模型 (dashscope, openai, gemini)")
):
    """AI智能添加任务"""
    try:
        console.print("🤖 AI正在分析你的任务...", style="dim")
        
        # 使用AI智能添加任务
        task = ai_assistant.smart_add_task(description, model_name=model)
        
        if task:
            console.print("✅ 任务添加成功！", style="bold green")
            console.print(f"ID: {task.id}", style="dim")
            console.print(f"标题: {task.title}")
            if task.description:
                console.print(f"描述: {task.description}")
            console.print(f"优先级: {task.priority.value}")
            if task.due_date:
                from src.utils.date_utils import format_datetime
                console.print(f"截止时间: {format_datetime(task.due_date)}")
        else:
            console.print("❌ 任务添加失败", style="bold red")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"❌ 智能添加任务失败: {e}", style="bold red")
        raise typer.Exit(1)


def report_command(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="指定日期 (YYYY-MM-DD)，默认今天"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="指定AI模型 (dashscope, openai, gemini)")
):
    """生成AI工作日报"""
    try:
        # 解析日期
        target_date = datetime.now()
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                console.print("❌ 日期格式错误，请使用 YYYY-MM-DD 格式", style="bold red")
                raise typer.Exit(1)
        
        console.print(f"📊 正在生成 {target_date.strftime('%Y-%m-%d')} 的工作日报...", style="dim")
        
        # 生成日报
        with console.status("🤖 AI正在分析和生成报告...", spinner="dots"):
            report = ai_assistant.generate_daily_report(target_date, model_name=model)
        
        # 显示报告
        console.print()
        if report.strip().startswith('#') or '```' in report:
            console.print(Markdown(report))
        else:
            console.print(report)
        
        # 询问是否保存报告
        if typer.confirm("\n💾 是否保存报告到文件？"):
            filename = f"work_report_{target_date.strftime('%Y%m%d')}.md"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                console.print(f"✅ 报告已保存到: {filename}", style="bold green")
            except Exception as e:
                console.print(f"❌ 保存失败: {e}", style="red")
        
    except Exception as e:
        console.print(f"❌ 生成报告失败: {e}", style="bold red")
        raise typer.Exit(1)


def setup_command():
    """设置AI助手"""
    try:
        console.print("🔧 AI助手设置向导", style="bold blue")
        console.print()
        
        # 检查各种API密钥
        openai_key = os.getenv("OPENAI_API_KEY")
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        console.print("📋 当前API密钥状态：", style="bold")
        
        if openai_key:
            console.print("✅ 已检测到 OPENAI_API_KEY", style="green")
            masked_key = openai_key[:8] + "*" * (len(openai_key) - 12) + openai_key[-4:]
            console.print(f"   密钥: {masked_key}", style="dim")
        else:
            console.print("❌ 未检测到 OPENAI_API_KEY", style="red")
        
        if dashscope_key:
            console.print("✅ 已检测到 DASHSCOPE_API_KEY", style="green")
            masked_key = dashscope_key[:8] + "*" * (len(dashscope_key) - 12) + dashscope_key[-4:]
            console.print(f"   密钥: {masked_key}", style="dim")
        else:
            console.print("❌ 未检测到 DASHSCOPE_API_KEY", style="red")
        
        if google_key:
            console.print("✅ 已检测到 GOOGLE_API_KEY", style="green")
            masked_key = google_key[:8] + "*" * (len(google_key) - 12) + google_key[-4:]
            console.print(f"   密钥: {masked_key}", style="dim")
        else:
            console.print("❌ 未检测到 GOOGLE_API_KEY", style="red")
        
        console.print()
        
        # 如果没有配置任何密钥，显示设置指南
        if not any([openai_key, dashscope_key, google_key]):
            console.print("❌ 未检测到任何API密钥", style="red")
            console.print()
            console.print("请设置至少一个API密钥：", style="bold")
            console.print()
            console.print("🔑 OpenAI (GPT模型):", style="cyan")
            console.print("1. 访问 https://platform.openai.com/api-keys", style="dim")
            console.print("2. 创建新的API密钥", style="dim")
            console.print("3. 设置环境变量：", style="dim")
            console.print("   Windows: set OPENAI_API_KEY=your_key_here", style="cyan")
            console.print("   Mac/Linux: export OPENAI_API_KEY=your_key_here", style="cyan")
            console.print()
            console.print("🔑 DashScope (阿里云通义千问):", style="cyan")
            console.print("1. 访问 https://dashscope.console.aliyun.com/", style="dim")
            console.print("2. 创建API密钥", style="dim")
            console.print("3. 设置环境变量：", style="dim")
            console.print("   Windows: set DASHSCOPE_API_KEY=your_key_here", style="cyan")
            console.print("   Mac/Linux: export DASHSCOPE_API_KEY=your_key_here", style="cyan")
            console.print()
            console.print("🔑 Google (Gemini模型):", style="cyan")
            console.print("1. 访问 https://makersuite.google.com/app/apikey", style="dim")
            console.print("2. 创建API密钥", style="dim")
            console.print("3. 设置环境变量：", style="dim")
            console.print("   Windows: set GOOGLE_API_KEY=your_key_here", style="cyan")
            console.print("   Mac/Linux: export GOOGLE_API_KEY=your_key_here", style="cyan")
            console.print()
            console.print("4. 重新启动终端", style="dim")
            return
        
        # 测试AI助手
        console.print("\n🧪 测试AI助手连接...", style="dim")
        
        # 测试可用的模型
        available_models = []
        
        if openai_key:
            try:
                test_response = ai_assistant.chat("你好，简单回复即可", model_name="openai")
                if test_response and "不可用" not in test_response:
                    available_models.append("OpenAI")
                    console.print("✅ OpenAI模型工作正常", style="green")
            except Exception as e:
                console.print(f"❌ OpenAI模型测试失败: {e}", style="red")
        
        if dashscope_key:
            try:
                test_response = ai_assistant.chat("你好，简单回复即可", model_name="dashscope")
                if test_response and "不可用" not in test_response:
                    available_models.append("DashScope")
                    console.print("✅ DashScope模型工作正常", style="green")
            except Exception as e:
                console.print(f"❌ DashScope模型测试失败: {e}", style="red")
        
        if google_key:
            try:
                test_response = ai_assistant.chat("你好，简单回复即可", model_name="gemini")
                if test_response and "不可用" not in test_response:
                    available_models.append("Gemini")
                    console.print("✅ Gemini模型工作正常", style="green")
            except Exception as e:
                console.print(f"❌ Gemini模型测试失败: {e}", style="red")
        
        if available_models:
            console.print(f"\n✅ AI助手工作正常！可用模型: {', '.join(available_models)}", style="bold green")
            console.print("🚀 你现在可以使用以下AI功能：", style="bold")
            console.print("   • todo chat        - 开始对话", style="cyan")
            console.print("   • todo smart-add    - 智能添加任务", style="cyan")
            console.print("   • todo report       - 生成工作报告", style="cyan")
            console.print("\n💡 使用 --model 参数指定AI模型：", style="bold")
            console.print("   • todo chat --model dashscope", style="cyan")
            console.print("   • todo chat --model openai", style="cyan")
            console.print("   • todo chat --model gemini", style="cyan")
        else:
            console.print("❌ 所有AI模型都不可用", style="red")
            console.print("请检查网络连接和API密钥", style="dim")
        
    except Exception as e:
        console.print(f"❌ 设置失败: {e}", style="bold red")
        raise typer.Exit(1) 