# System Patterns *Optional*

This file documents recurring patterns and standards used in the project.
It is optional, but recommended to be updated as the project evolves.
2025-07-17 22:47:07 - Log of updates made.

*

## Coding Patterns

* **Agno工具包开发模式**: 
  - 继承`agno.tools.Toolkit`基类
  - 使用`register()`方法注册工具函数，支持`show_result`和`stop_after_tool_call`配置
  - 工具函数返回字符串格式的友好结果描述，包含emoji表情符号增强可读性
  - 完整的类型提示：参数使用`Optional[Type]`，返回值统一为`str`
  - 统一的错误处理模式：`try-except`包装，返回格式化错误信息

## Architectural Patterns

* **服务层集成模式**:
  - 工具包通过依赖注入方式使用现有服务层（TaskService）
  - 保持工具包轻量，业务逻辑保留在服务层
  - 工具包专注于参数验证、类型转换和结果格式化

## Testing Patterns

*   