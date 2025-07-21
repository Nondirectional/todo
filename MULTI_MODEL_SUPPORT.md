# Todo CLI 多模型支持功能

## 🎯 功能概述

Todo CLI 现在支持用户选择使用不同的AI模型，包括：
- **DashScope（阿里云通义千问）**
- **OpenAI GPT**
- **Google Gemini**

## ✨ 主要特性

### 1. 用户模型选择
- 支持通过 `--model` 参数指定使用的AI模型
- 支持的命令：`chat`、`smart-add`、`report`
- 模型选项：`dashscope`、`openai`、`gemini`

### 2. 自动模型选择
- 如果不指定模型，系统会按优先级自动选择
- 优先级：DashScope > Gemini > OpenAI
- 自动检测API密钥可用性

### 3. 灵活的配置
- 支持同时配置多个API密钥
- 环境变量配置：
  - `DASHSCOPE_API_KEY`
  - `OPENAI_API_KEY`
  - `GOOGLE_API_KEY`

## 🚀 使用方法

### 命令行使用

```bash
# 使用默认模型
todo chat "帮我添加一个任务"
todo smart-add "明天开会"
todo report

# 指定模型
todo chat --model dashscope "帮我添加一个任务"
todo smart-add --model openai "明天开会"
todo report --model gemini

# 配置向导
todo ai-setup
```

### 编程接口使用

```python
from todo.services.ai_service import TodoAIAssistant
from todo.services.task_service import TaskService

# 创建服务实例
task_service = TaskService()
ai_assistant = TodoAIAssistant(task_service)

# 使用指定模型
response = ai_assistant.chat("你好", model_name="dashscope")
task = ai_assistant.smart_add_task("明天开会", model_name="openai")
report = ai_assistant.generate_daily_report(model_name="gemini")

# 使用自动选择
response = ai_assistant.chat("你好")  # 自动选择可用模型
```

## 🔧 技术实现

### 1. 模型类设计
- `DashScope`: 继承自 `OpenAIChat`，支持阿里云DashScope兼容模式
- `Gemini`: 使用agno的 `Gemini` 类
- `OpenAIChat`: 使用agno的 `OpenAIChat` 类

### 2. 服务层修改
- `TodoAIAssistant._get_ai_model()`: 支持模型名称参数
- `TodoAIAssistant._create_model_by_name()`: 根据名称创建模型实例
- `TodoAIAssistant._create_agent_with_model()`: 使用指定模型创建Agent

### 3. CLI层修改
- 所有AI命令添加 `--model` 选项
- 支持模型验证和错误处理
- 更新帮助信息和错误提示

## 📋 测试功能

### 测试脚本
```bash
# 测试所有模型
python test_dashscope.py

# 测试指定模型
python test_dashscope.py dashscope
python test_dashscope.py openai
python test_dashscope.py gemini
```

### 使用示例
```bash
# 运行完整示例
python example_usage.py
```

## 🔑 API密钥配置

### DashScope
1. 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
2. 创建API密钥
3. 设置环境变量：`export DASHSCOPE_API_KEY=your_key`

### OpenAI
1. 访问 [OpenAI API Keys](https://platform.openai.com/api-keys)
2. 创建API密钥
3. 设置环境变量：`export OPENAI_API_KEY=your_key`

### Google Gemini
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建API密钥
3. 设置环境变量：`export GOOGLE_API_KEY=your_key`

## 🎉 优势

1. **用户选择权**: 用户可以根据需求和偏好选择AI模型
2. **容错性**: 支持多个模型，一个不可用时可以切换到其他模型
3. **成本控制**: 不同模型有不同的定价，用户可以选择性价比更高的模型
4. **功能差异**: 不同模型有不同的能力特点，用户可以根据任务类型选择
5. **向后兼容**: 保持原有功能不变，新增功能为可选

## 🔮 未来扩展

1. **模型配置**: 支持配置文件设置默认模型
2. **模型性能**: 添加模型性能监控和比较
3. **更多模型**: 支持更多AI服务提供商
4. **模型组合**: 支持多个模型协同工作
5. **智能路由**: 根据任务类型自动选择最适合的模型

## 📝 更新日志

- **2025-07-18**: 完成多模型支持功能
  - 添加DashScope、OpenAI、Gemini三种模型支持
  - 实现用户模型选择功能
  - 更新CLI命令和文档
  - 添加测试和示例脚本 