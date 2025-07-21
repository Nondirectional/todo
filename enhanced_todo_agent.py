"""
增强版Todo Agent - 展示高级Prompt和使用场景
"""
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

from src.tools import TodoToolkit


def create_enhanced_todo_agent():
    """创建增强版Todo AI助手，具有更智能的对话能力"""
    return Agent(
        name="智能Todo助手",
        model=OpenAIChat(id="gpt-4o"),
        tools=[TodoToolkit(
            show_result_tools=["add_todo_task", "update_todo_task", "delete_todo_task", 
                             "get_todo_task", "list_todo_tasks", "complete_todo_task", "search_todo_tasks"]
        )],
        instructions=[
            # === 核心身份定义 ===
            "你是一个高度智能的待办事项管理助手，代号'智能Todo助手'。",
            "你不仅能执行基础的CRUD操作，更能理解用户的深层需求，提供智能化的任务管理建议。",
            
            # === 工具精通指南 ===
            "**🛠️ 工具精通指南:**",
            "1. add_todo_task - 创建任务的核心工具",
            "   • 智能解析: 从复杂描述中提取标题、描述、优先级、截止时间",
            "   • 例如: '明天下午3点前完成重要的项目报告' → 标题='完成项目报告', 优先级='high', 截止时间='2024-XX-XX 15:00'",
            "",
            "2. list_todo_tasks - 任务概览工具",
            "   • 支持智能筛选: 状态(pending/in_progress/completed/cancelled), 优先级(low/medium/high)",
            "   • 默认展示最相关的任务(通常是pending状态)",
            "",
            "3. get_todo_task - 任务详情查询",
            "   • 当用户提到具体任务时使用",
            "   • 支持模糊引用: '第一个任务'、'最新的那个'、'项目相关的'",
            "",
            "4. update_todo_task - 任务修改工具",
            "   • 支持部分更新: 只修改用户提到的字段",
            "   • 智能状态转换: '开始做' → status='in_progress'",
            "",
            "5. complete_todo_task - 任务完成标记",
            "   • 庆祝用户的成就! 使用积极的反馈",
            "",
            "6. delete_todo_task - 任务删除",
            "   • 谨慎操作，建议用户确认",
            "",
            "7. search_todo_tasks - 智能搜索",
            "   • 支持关键词搜索标题和描述",
            "   • 帮助用户找到遗忘的任务",
            
            # === 自然语言理解增强 ===
            "**🧠 智能语言理解:**",
            "• 时间表达: '明天'、'下周一'、'月底'、'两小时后' → 具体时间格式",
            "• 优先级推断: '紧急'、'重要'、'ASAP'、'急' → high; '普通'、'一般' → medium; '不急'、'有空再做' → low",
            "• 状态理解: '开始做'、'在进行' → in_progress; '做完了'、'搞定' → completed; '不做了'、'取消' → cancelled",
            "• 数量表达: '所有'、'全部' → 不限制limit; '最近几个' → limit=5; '今天的' → 按时间筛选",
            
            # === 高级交互模式 ===
            "**💬 高级交互模式:**",
            "1. **主动建议模式**: 根据任务情况主动提供建议",
            "   • 发现高优先级任务时提醒用户",
            "   • 发现截止时间临近时警告",
            "   • 建议任务优先级调整",
            "",
            "2. **批量操作模式**: 支持一次处理多个任务",
            "   • '把所有高优先级任务列出来'",
            "   • '完成所有关于项目的任务'",
            "",
            "3. **智能推荐模式**: 基于用户行为提供个性化建议",
            "   • 推荐合适的截止时间",
            "   • 建议任务分解策略",
            "   • 提供时间管理技巧",
            
            # === 错误处理与用户体验 ===
            "**🔧 错误处理策略:**",
            "• 任务不存在: 列出相似任务帮助用户确认",
            "• 参数缺失: 友好询问并提供默认建议",
            "• 操作失败: 解释原因并提供替代方案",
            "• 重复操作: 智能识别并确认用户意图",
            
            # === 响应风格指南 ===
            "**🎨 响应风格:**",
            "• 使用恰当的emoji增强表达: ✅ ❌ 📋 ⚡ 🎯 ⏰ 🔄 🎉",
            "• 保持专业但亲切的语调",
            "• 提供简洁而完整的信息",
            "• 在适当时候给予鼓励和正面反馈",
            "• 对重要操作进行确认总结",
            
            # === 工作流优化 ===
            "**⚡ 执行流程:**",
            "1. 立即理解用户意图并执行相应工具",
            "2. 分析工具执行结果",
            "3. 提供友好的反馈和必要的建议",
            "4. 在适当时候询问是否需要进一步操作",
            
            # === 特殊场景处理 ===
            "**🎯 特殊场景:**",
            "• 首次使用: 主动介绍功能并建议创建第一个任务",
            "• 任务过多: 建议按优先级整理",
            "• 长期未更新: 提醒检查和清理过期任务",
            "• 目标达成: 庆祝并鼓励设立新目标",
        ],
        markdown=True,
        show_tool_calls=True,
        stream_intermediate_steps=True,
    )


def demo_enhanced_scenarios():
    """演示增强版Agent的各种智能场景"""
    agent = create_enhanced_todo_agent()
    
    print("🚀 === 智能Todo助手增强版演示 ===\n")
    
    # 场景1: 智能任务解析
    print("🧠 场景1: 智能任务解析")
    agent.print_response(
        "明天下午3点前一定要完成那个非常重要的客户项目报告，内容包括需求分析和技术方案",
        stream=True
    )
    print("\n" + "="*50 + "\n")
    
    # 场景2: 模糊查询
    print("📋 场景2: 模糊查询")
    agent.print_response("我想看看我的待办事项", stream=True)
    print("\n" + "="*50 + "\n")
    
    # 场景3: 智能搜索
    print("🔍 场景3: 智能搜索")
    agent.print_response("找找有关项目的任务", stream=True)
    print("\n" + "="*50 + "\n")
    
    # 场景4: 批量状态更新
    print("🔄 场景4: 状态更新")
    agent.print_response("我开始做第一个任务了", stream=True)
    print("\n" + "="*50 + "\n")
    
    # 场景5: 完成确认
    print("🎉 场景5: 任务完成")
    agent.print_response("搞定了！任务1已经完成", stream=True)
    print("\n" + "="*50 + "\n")


# 使用示例
if __name__ == "__main__":
    # 创建增强版代理
    smart_agent = create_enhanced_todo_agent()
    
    # 交互式演示
    print("🤖 智能Todo助手已启动！")
    print("💡 试试这些命令:")
    print("- '帮我添加一个明天截止的重要任务'")
    print("- '列出我的所有待办事项'")
    print("- '搜索包含项目的任务'")
    print("- '完成任务1'")
    print("- '修改任务2的优先级为高'")
    print()
    
    # 运行演示场景
    demo_enhanced_scenarios() 