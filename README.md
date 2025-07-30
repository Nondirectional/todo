# Todo CLI - 强大的命令行待办任务管理工具

一个基于 Typer 和 SQLAlchemy 构建的功能完整的命令行待办任务管理工具。

## 功能特性

- ✅ **完整的任务管理**：创建、查看、更新、删除、完成任务
- 📁 **分类管理**：支持任务分类组织
- 🏷️ **标签系统**：灵活的多标签支持
- 🔍 **高级搜索**：多维度任务搜索和过滤
- 📊 **统计报告**：任务完成情况分析
- 📤 **数据导入导出**：支持 JSON/CSV 格式
- 🎨 **美化界面**：Rich 库提供的彩色输出和表格
- 🌳 **多种视图**：列表、树形、仪表板视图

## 安装

1. 确保已安装 Python 3.12+
2. 安装依赖：
```bash
pip install -e .
```

## 快速开始

### 初始化数据库
```bash
todo init
```

### 基本任务操作
```bash
# 创建任务
todo task add "完成项目文档" --desc "编写用户手册" --priority high

# 列出任务
todo task list

# 查看任务详情
todo task show 1

# 完成任务
todo task complete 1

# 删除任务
todo task delete 1
```

### 分类管理
```bash
# 创建分类
todo category add "工作" --desc "工作相关任务" --color "#FF5733"

# 列出分类
todo category list

# 创建带分类的任务
todo task add "开会" --category "工作"
```

### 标签管理
```bash
# 创建标签
todo tag add "紧急" --color "#FF0000"
todo tag add "重要" --color "#FFA500"

# 创建带标签的任务
todo task add "修复bug" --tags "紧急,重要"
```

### AI 聊天助手

**首次配置：**
```bash
# 配置 API 密钥（必需）
todo chat config set --api-key "your-openai-api-key"

# 配置自定义端点（可选）
todo chat config set --base-url "https://api.example.com/v1" --model "custom-model"

# 查看当前配置
todo chat config show
```

**启动聊天：**
```bash
# 使用已保存的配置启动
todo chat start

# 临时覆盖配置启动
todo chat start --model "gpt-4"
```

**配置管理：**
```bash
# 设置配置
todo chat config set --api-key "new-key" --model "gpt-4"

# 显示配置
todo chat config show

# 重置配置
todo chat config reset

# 查看帮助
todo chat config help
```

**AI 聊天示例：**
- "创建一个任务：学习Python，优先级设为高"
- "列出所有待办任务"
- "创建一个工作分类，颜色设为蓝色"
- "搜索包含'学习'的任务"
- "完成任务1"

### 高级搜索
```bash
# 搜索任务
todo task search "文档" --status pending --priority high

# 查看过期任务
todo task search --overdue

# 按日期范围搜索
todo task search --created-after "2024-01-01" --due-before "2024-12-31"
```

### 可视化视图
```bash
# 树形视图
todo task tree --group-by category

# 仪表板视图
todo task dashboard

# 分类统计
todo stats categories

# 总体概览
todo stats overview
```

### 数据导入导出
```bash
# 导出为 JSON
todo stats export --format json --output tasks.json

# 导出为 CSV
todo stats export --format csv --output tasks.csv

# 导入数据
todo stats import tasks.json --dry-run  # 预览
todo stats import tasks.json            # 实际导入
```

## 命令参考

### 任务命令 (todo task)
- `add` - 创建新任务
- `list` - 列出任务
- `search` - 高级搜索
- `show` - 显示任务详情
- `update` - 更新任务
- `complete` - 完成任务
- `delete` - 删除任务
- `tree` - 树形视图
- `dashboard` - 仪表板视图

### 分类命令 (todo category)
- `add` - 创建分类
- `list` - 列出分类
- `update` - 更新分类
- `delete` - 删除分类

### 标签命令 (todo tag)
- `add` - 创建标签
- `list` - 列出标签
- `update` - 更新标签
- `delete` - 删除标签

### 统计命令 (todo stats)
- `overview` - 总体统计
- `categories` - 分类统计
- `export` - 导出数据
- `import` - 导入数据

### AI 聊天命令 (todo chat)
- `start` - 启动 AI 聊天助手
- `config set` - 设置聊天配置
- `config show` - 显示当前配置
- `config reset` - 重置配置
- `config help` - 查看配置帮助

## 配置

应用数据默认存储在：
- Windows: `%APPDATA%\Roaming\todo-cli\`
- macOS: `~/Library/Application Support/todo-cli/`
- Linux: `~/.local/share/todo-cli/`

包含文件：
- `todo.db` - 数据库文件
- `config.json` - 配置文件（包含 AI 聊天设置）

## 技术栈

- **Typer** - 现代 Python CLI 框架
- **SQLAlchemy** - Python SQL 工具包和 ORM
- **Rich** - 美化终端输出
- **SQLite** - 轻量级数据库

## 开发

项目结构：
```
src/
├── __init__.py
├── main.py              # 主入口
├── database.py          # 数据库配置
├── commands/            # 命令模块
│   ├── task.py
│   ├── category.py
│   ├── tag.py
│   └── stats.py
├── models/              # 数据模型
│   ├── task.py
│   ├── category.py
│   └── tag.py
└── utils/               # 工具函数
    ├── helpers.py
    └── display.py
```