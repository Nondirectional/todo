# Decision Log

This file records architectural and implementation decisions using a list format.
2025-07-29 11:07:02 - Log of updates made.

*

## Decision

* [2025-07-30 10:19:31] - 采用 Langchain @tool 装饰器模式实现 AI 工具集成

## Rationale

* **技术选择**：选择 Langchain @tool 装饰器而非自定义工具类
  - 简化工具定义，自动推断参数和描述
  - 与 Langchain 生态系统完全兼容
  - 减少样板代码，提高开发效率

* **架构设计**：复用现有业务逻辑而非重新实现
  - 保持代码一致性，避免重复开发
  - 降低维护成本，单一数据源
  - 确保 CLI 和 AI 工具功能同步

## Implementation Details

* **文件结构**：创建独立的 `todo/langchain_tools.py` 模块
* **工具分类**：按功能域组织（任务、分类、标签管理）
* **错误处理**：统一返回 Dict[str, Any] 格式，包含 success/error 字段
* **数据库管理**：每个工具独立管理数据库会话，确保事务安全
* **参数设计**：与 CLI 命令保持一致的参数命名和类型

* [2025-07-30 13:58:33] - 重新设计 AI 聊天命令结构，实现配置持久化

## Rationale

* **命令职责分离**：将配置管理和聊天启动分离为不同命令
  - `todo chat start` 专注于启动聊天，使用已保存配置
  - `todo chat config` 专门管理配置的增删改查
  - 提高用户体验，避免每次启动都需要输入配置

* **配置持久化需求**：用户希望避免重复输入 API 密钥等配置
  - 使用 JSON 格式存储在应用数据目录
  - 与数据库文件存放在同一位置，便于管理
  - 明文存储，简化实现复杂度

## Implementation Details

* **配置管理器**：创建独立的 `todo/config.py` 模块
* **配置文件位置**：`~/.local/share/todo-cli/config.json`（跨平台）
* **配置优先级**：命令行参数 > 配置文件 > 默认值
* **子命令结构**：使用 Typer 子应用组织 config 相关命令
* **用户体验**：提供 set/show/reset/help 等完整的配置管理功能