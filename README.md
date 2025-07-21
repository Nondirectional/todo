# Todo CLI - 智能任务管理工具

一个功能强大的命令行待办事项管理程序，集成了AI助手功能，支持智能任务管理和自动化报告生成。

## ✨ 主要功能

- **任务管理**: 创建、更新、完成、删除待办事项
- **时间跟踪**: 支持创建时间、开始时间、截止时间、完成时间管理
- **数据持久化**: 使用SQLite数据库存储任务数据
- **AI助手集成**: 支持多种AI模型（OpenAI、DashScope）
- **智能功能**: 对话式任务记录、智能任务解析、AI日报生成
- **命令行界面**: 使用Typer框架提供友好的CLI交互体验

## 🚀 快速开始

### 安装

1. 克隆项目
```bash
git clone <repository-url>
cd todo
```

2. 安装依赖
```bash
# 使用uv（推荐）
uv sync

# 或使用pip
pip install -e .
```

### 基础使用

```bash
# 添加任务
todo add "完成项目文档"

# 列出所有任务
todo list

# 完成任务
todo complete 1

# 查看任务详情
todo show 1
```

## 🤖 AI助手功能

### 支持的AI模型

项目支持多种AI模型，用户可以选择使用：

1. **DashScope（阿里云通义千问）** - 阿里云AI服务
2. **OpenAI GPT** - OpenAI官方模型
3. **Google Gemini** - Google AI模型

**自动选择机制**：如果不指定模型，系统会按优先级自动选择可用的模型。

### 配置AI模型

#### 使用DashScope（推荐）

1. 获取DashScope API密钥
   - 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
   - 创建API密钥

2. 设置环境变量
```bash
export DASHSCOPE_API_KEY=your_dashscope_api_key
```

#### 使用OpenAI

```bash
export OPENAI_API_KEY=your_openai_api_key
```

#### 使用Google Gemini

```bash
export GOOGLE_API_KEY=your_google_api_key
```

### AI功能使用

```bash
# 对话式任务管理（使用默认模型）
todo chat "帮我添加一个明天下午3点的会议"

# 指定AI模型进行对话
todo chat --model dashscope "帮我添加一个明天下午3点的会议"
todo chat --model openai "帮我添加一个明天下午3点的会议"
todo chat --model gemini "帮我添加一个明天下午3点的会议"

# 智能添加任务（使用默认模型）
todo smart-add "明天上午9点开始写代码，优先级高"

# 指定AI模型智能添加任务
todo smart-add --model dashscope "明天上午9点开始写代码，优先级高"

# 生成工作日报（使用默认模型）
todo report

# 指定AI模型生成日报
todo report --model gemini

# AI配置向导
todo ai-setup
```

## 📋 命令参考

### 基础任务命令

```bash
# 添加任务
todo add <title> [--description TEXT] [--priority {low,medium,high}] [--due-date DATE]

# 列出任务
todo list [--status {pending,in-progress,completed}] [--priority {low,medium,high}]

# 查看任务详情
todo show <task-id>

# 更新任务
todo update <task-id> [--title TEXT] [--description TEXT] [--priority {low,medium,high}] [--due-date DATE]

# 开始任务
todo start <task-id>

# 完成任务
todo complete <task-id>

# 删除任务
todo delete <task-id>

# 搜索任务
todo search <keyword>
```

### AI助手命令

```bash
# 与AI助手对话
todo chat <message> [--model {dashscope,openai,gemini}]

# 智能添加任务
todo smart-add <description> [--model {dashscope,openai,gemini}]

# 生成日报
todo report [--date DATE] [--model {dashscope,openai,gemini}]

# AI配置向导
todo ai-setup
```

## 🔧 配置

### 环境变量

- `DASHSCOPE_API_KEY`: DashScope API密钥
- `OPENAI_API_KEY`: OpenAI API密钥
- `GOOGLE_API_KEY`: Google Gemini API密钥
- `TODO_DB_PATH`: 数据库文件路径（可选）

### 数据存储

- 任务数据: `~/.todo/tasks.db`
- AI会话数据: `~/.todo/ai_sessions.db`

## 🛠️ 开发

### 项目结构

```
todo/
├── todo/
│   ├── cli/           # 命令行界面
│   ├── models/        # 数据模型
│   ├── services/      # 业务逻辑
│   └── utils/         # 工具函数
├── memory-bank/       # 项目记忆库
├── pyproject.toml     # 项目配置
└── README.md
```

### 运行测试

```bash
# 测试所有AI模型
python test_dashscope.py

# 测试指定模型
python test_dashscope.py dashscope
python test_dashscope.py openai
python test_dashscope.py gemini
```

### 添加新的AI模型

项目支持扩展新的AI模型。参考 `DashScopeOpenAIChat` 类的实现：

```python
@dataclass
class CustomAIModel(BaseOpenAIChat):
    id: str = "your-model-id"
    name: str = "YourModel"
    api_key: Optional[str] = "not-provided"
    base_url: Optional[Union[str, httpx.URL]] = "your-api-endpoint"
    
    role_map = {
        "system": "system",
        "user": "user", 
        "assistant": "assistant",
        "tool": "tool",
    }
```

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请提交Issue或联系开发者。
