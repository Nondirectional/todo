"""
简化版 Todo AI 聊天演示

这是一个简化的演示版本，展示如何使用 Langchain 工具与 Todo 系统交互。
正式版本请使用: todo chat start --api-key "your-key"
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from todo.langchain_tools import ALL_TOOLS


def simple_chat_demo():
    """简单的聊天演示"""
    print("=== Todo AI 聊天演示 ===")
    print("注意：这是演示版本，需要配置有效的 API 密钥")
    print("正式使用请运行: todo chat start --api-key 'your-key'")
    print()
    
    # 工具字典
    tools_dict = {tool.name: tool for tool in ALL_TOOLS}
    
    # 初始化模型（需要有效的 API 密钥）
    try:
        model = ChatOpenAI(
            model="gpt-3.5-turbo",
            # 需要设置有效的 API 密钥
            # api_key="your-api-key-here",
        ).bind_tools(ALL_TOOLS)
    except Exception as e:
        print(f"模型初始化失败: {e}")
        print("请设置有效的 OPENAI_API_KEY 环境变量或使用 todo chat start 命令")
        return
    
    # 系统提示
    system_prompt = """
你是专注于待办系统管理的 AI 助手。请帮助用户管理任务、分类和标签。
"""
    
    messages = [SystemMessage(system_prompt)]
    
    print("开始聊天（输入 'exit' 退出）:")
    
    while True:
        try:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("再见！")
                break
            
            if not user_input.strip():
                continue
            
            # 添加用户消息
            messages.append(HumanMessage(user_input))
            
            # 获取 AI 响应
            response = model.invoke(messages)
            messages.append(response)
            
            # 处理工具调用
            if response.tool_calls:
                print("\n--- 工具执行 ---")
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    print(f"调用工具: {tool_name}")
                    print(f"参数: {tool_args}")
                    
                    # 执行工具
                    tool_output = tools_dict[tool_name].invoke(tool_call)
                    messages.append(tool_output)
                    
                    # 显示结果
                    try:
                        result = json.loads(tool_output.content)
                        print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"结果: {tool_output.content}")
                
                # 获取最终响应
                final_response = model.invoke(messages)
                messages.append(final_response)
                print(f"\nAI: {final_response.content}")
            else:
                print(f"\nAI: {response.content}")
            
            # 保持消息历史在合理范围内
            if len(messages) > 15:
                messages = messages[:1] + messages[-10:]  # 保留系统消息和最近10条
                
        except KeyboardInterrupt:
            print("\n聊天被中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            continue


def show_available_tools():
    """显示可用的工具"""
    print("=== 可用的 Langchain 工具 ===")
    print()
    
    # 按类别分组显示
    categories = {
        "任务管理": ["add_task", "list_tasks", "search_tasks", "show_task", "update_task", "complete_task", "delete_task"],
        "分类管理": ["add_category", "list_categories", "update_category", "delete_category"],
        "标签管理": ["add_tag", "list_tags", "update_tag", "delete_tag"],
        "通用工具": ["current_datetime"]
    }
    
    for category, tool_names in categories.items():
        print(f"📁 {category}:")
        for tool_name in tool_names:
            for tool in ALL_TOOLS:
                if tool.name == tool_name:
                    print(f"  - {tool.name}: {tool.description}")
                    break
        print()


def show_usage_examples():
    """显示使用示例"""
    print("=== 使用示例 ===")
    print()
    
    examples = [
        {
            "category": "任务管理",
            "examples": [
                "创建一个任务：学习Python",
                "列出所有待办任务",
                "搜索包含'学习'的任务",
                "完成任务1",
                "删除任务2"
            ]
        },
        {
            "category": "分类管理", 
            "examples": [
                "创建一个工作分类",
                "列出所有分类",
                "更新工作分类的描述"
            ]
        },
        {
            "category": "标签管理",
            "examples": [
                "创建一个紧急标签",
                "列出所有标签",
                "删除过期标签"
            ]
        }
    ]
    
    for item in examples:
        print(f"📁 {item['category']}:")
        for example in item['examples']:
            print(f"  - \"{example}\"")
        print()


def main():
    """主函数"""
    print("Todo Langchain 工具演示")
    print("=" * 40)
    
    while True:
        print("\n选择操作:")
        print("1. 查看可用工具")
        print("2. 查看使用示例")
        print("3. 开始聊天演示")
        print("4. 退出")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            show_available_tools()
        elif choice == "2":
            show_usage_examples()
        elif choice == "3":
            simple_chat_demo()
        elif choice == "4":
            print("再见！")
            break
        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    main()
