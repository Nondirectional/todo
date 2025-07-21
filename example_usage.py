#!/usr/bin/env python3
"""
Todo CLI 多模型使用示例
"""
import os
from src.services.ai_service import TodoAIAssistant
from src.services.task_service import TaskService

def main():
    """主函数 - 演示多模型使用"""
    print("🚀 Todo CLI 多模型使用示例")
    print("=" * 50)
    
    # 创建服务实例
    task_service = TaskService()
    ai_assistant = TodoAIAssistant(task_service)
    
    # 检查可用的模型
    print("📋 检查可用的AI模型...")
    available_models = []
    
    models_to_test = [
        ("dashscope", "DASHSCOPE_API_KEY", "DashScope"),
        ("openai", "OPENAI_API_KEY", "OpenAI"),
        ("gemini", "AIzaSyCvv--6bMedSbInwKisQ9Yh40UDI6w_Qz4", "Gemini")
    ]
    
    for model_name, env_var, display_name in models_to_test:
        if os.getenv(env_var):
            try:
                response = ai_assistant.chat("测试连接", model_name=model_name)
                if response and "不可用" not in response:
                    available_models.append(model_name)
                    print(f"✅ {display_name} 可用")
                else:
                    print(f"❌ {display_name} 不可用")
            except Exception as e:
                print(f"❌ {display_name} 测试失败: {e}")
        else:
            print(f"⏭️ {display_name} 未配置API密钥")
    
    print()
    
    if not available_models:
        print("❌ 没有可用的AI模型，请配置相应的API密钥")
        return
    
    # 演示使用不同模型
    print("🎯 演示使用不同AI模型...")
    print()
    
    # 示例任务描述
    task_description = "明天下午3点开会讨论项目进度，优先级高"
    
    for model_name in available_models:
        print(f"🤖 使用 {model_name.upper()} 模型:")
        print("-" * 30)
        
        try:
            # 智能添加任务
            print(f"📝 智能添加任务: {task_description}")
            task = ai_assistant.smart_add_task(task_description, model_name=model_name)
            
            if task:
                print(f"✅ 任务创建成功!")
                print(f"   ID: {task.id}")
                print(f"   标题: {task.title}")
                print(f"   优先级: {task.priority.value}")
                if task.due_date:
                    print(f"   截止时间: {task.due_date}")
            else:
                print("❌ 任务创建失败")
            
            # 简单对话
            print(f"\n💬 简单对话测试")
            response = ai_assistant.chat("你好，请简单介绍一下自己", model_name=model_name)
            print(f"AI回复: {response[:100]}...")
            
        except Exception as e:
            print(f"❌ 使用 {model_name} 模型时出错: {e}")
        
        print("\n" + "=" * 50 + "\n")
    
    # 演示自动选择模型
    print("🎲 演示自动选择模型（不指定模型名称）:")
    print("-" * 40)
    
    try:
        response = ai_assistant.chat("请给我一些时间管理建议")
        print(f"AI回复: {response[:200]}...")
    except Exception as e:
        print(f"❌ 自动选择模型时出错: {e}")
    
    print("\n✨ 示例完成！")
    print("\n💡 使用提示:")
    print("• 在命令行中使用 --model 参数指定AI模型")
    print("• 例如: todo chat --model dashscope '你的消息'")
    print("• 不指定模型时会自动选择可用的模型")

if __name__ == "__main__":
    main() 