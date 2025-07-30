# System Patterns *Optional*

This file documents recurring patterns and standards used in the project.
It is optional, but recommended to be updated as the project evolves.
2025-07-29 11:07:02 - Log of updates made.

*

## Coding Patterns

* **Langchain 工具封装模式**：使用 @tool 装饰器将现有业务逻辑封装为 AI 可调用的工具
  - 保持与原有 CLI 命令的参数一致性
  - 统一的错误处理和返回格式（Dict[str, Any]）
  - 数据库会话管理的标准化模式（try-except-finally）

* **配置管理模式**：统一的配置持久化和优先级处理
  - 使用 JSON 格式存储配置文件
  - 配置优先级：命令行参数 > 配置文件 > 默认值
  - 配置验证和错误处理的标准化流程

## Architectural Patterns

* **工具模块化设计**：按功能域分组工具（任务、分类、标签）
  - 提供 ALL_TOOLS、TASK_TOOLS、CATEGORY_TOOLS、TAG_TOOLS 等预定义工具集
  - 支持灵活的工具组合和选择性绑定

* **命令模块抽取模式**：将复杂功能从演示代码抽取为正式命令
  - 保持演示代码简洁，专注于核心功能展示
  - 正式命令提供完整的错误处理、配置管理和用户体验
  - 通过 Typer 子命令结构组织功能模块

* **子命令分组模式**：使用 Typer 子应用组织相关功能
  - 主命令专注于核心操作（如 start）
  - 子命令组管理相关配置和辅助功能（如 config）
  - 清晰的命令层次结构和职责分离

## Testing Patterns

*