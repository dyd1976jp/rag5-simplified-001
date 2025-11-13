# 核心模块

核心模块包含 RAG5 系统的核心功能，主要是代理（Agent）的实现和相关组件。

## 模块结构

```
core/
├── __init__.py           # 模块导出
├── README.md            # 本文档
├── agent/               # 代理子模块
│   ├── __init__.py      # 代理组件导出
│   ├── agent.py         # 主代理类
│   ├── initializer.py   # 代理初始化器
│   ├── messages.py      # 消息处理器
│   ├── history.py       # 对话历史管理器
│   └── errors.py        # 错误处理器
└── prompts/             # 提示词子模块
    ├── __init__.py      # 提示词导出
    ├── system.py        # 系统提示词
    └── tools.py         # 工具描述提示词
```

## 主要组件

### 1. SimpleRAGAgent（主代理类）

`SimpleRAGAgent` 是 RAG5 系统的核心，负责协调 LLM 和工具来回答用户查询。

**功能特性：**
- 分析查询以确定是否需要使用工具
- 在搜索知识库之前优化查询
- 从检索到的信息中合成答案
- 处理带有聊天历史的多轮对话
- 自动重试和错误处理

**使用示例：**

```python
from rag5.core.agent import SimpleRAGAgent

# 创建代理实例
agent = SimpleRAGAgent()

# 简单查询
answer = agent.chat("你好")
print(answer)

# 需要知识库搜索的查询
answer = agent.chat("李小勇和人合作入股了什么公司")
print(answer)

# 带聊天历史的多轮对话
history = [
    {"role": "user", "content": "公司有哪些项目？"},
    {"role": "assistant", "content": "有Alpha、Beta、Gamma三个项目"}
]
answer = agent.chat("第一个项目的进度如何？", chat_history=history)
print(answer)
```

**便捷函数：**

```python
from rag5.core.agent import ask

# 使用便捷函数，无需手动创建代理实例
answer = ask("你好")
print(answer)

# 带历史
history = [...]
answer = ask("第一个项目的进度如何？", history)
print(answer)
```

### 2. AgentInitializer（代理初始化器）

负责代理的初始化和依赖检查。

**功能特性：**
- 检查 Ollama 服务可用性
- 检查 LLM 和嵌入模型可用性
- 初始化 LLM
- 加载工具
- 创建代理执行器

**使用示例：**

```python
from rag5.core.agent import AgentInitializer

# 创建初始化器
initializer = AgentInitializer()

# 检查所有服务
status = initializer.check_services()
print(f"Ollama 服务: {'✓' if status['ollama'] else '✗'}")
print(f"LLM 模型: {'✓' if status['llm_model'] else '✗'}")
print(f"嵌入模型: {'✓' if status['embed_model'] else '✗'}")

# 如果所有服务可用，创建代理
if all(status.values()):
    agent_executor = initializer.create_agent()
```

### 3. MessageProcessor（消息处理器）

处理消息格式转换。

**功能特性：**
- 字典格式 ↔ LangChain 消息格式转换
- 从代理结果中提取 AI 响应
- 格式化对话历史为文本

**使用示例：**

```python
from rag5.core.agent import MessageProcessor

processor = MessageProcessor()

# 字典转 LangChain 格式
dict_msgs = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
]
lc_msgs = processor.dict_to_langchain(dict_msgs)

# LangChain 格式转字典
dict_msgs = processor.langchain_to_dict(lc_msgs)

# 从代理结果提取响应
result = {"messages": [...]}
answer = processor.extract_ai_response(result)

# 格式化历史
formatted = processor.format_chat_history(dict_msgs)
print(formatted)
```

### 4. ConversationHistory（对话历史管理器）

管理对话历史记录。

**功能特性：**
- 添加、获取、清空消息
- 限制返回的消息数量
- 转换为 LangChain 消息格式
- 格式化历史为文本

**使用示例：**

```python
from rag5.core.agent import ConversationHistory

# 创建历史管理器
history = ConversationHistory()

# 添加消息
history.add_user_message("你好")
history.add_assistant_message("你好！有什么可以帮助你的吗？")
history.add_user_message("今天天气怎么样？")

# 获取所有消息
all_messages = history.get_messages()
print(f"共有 {len(all_messages)} 条消息")

# 获取最近的 N 条消息
recent_messages = history.get_messages(limit=2)

# 获取最后一条消息
last_message = history.get_last_message()

# 转换为 LangChain 格式
lc_messages = history.to_langchain_messages()

# 格式化历史
formatted = history.format_history()
print(formatted)

# 清空历史
history.clear()
```

### 5. ErrorHandler（错误处理器）

提供统一的错误处理。

**功能特性：**
- 处理连接错误
- 处理超时错误
- 处理验证错误
- 处理模型错误
- 统一错误处理入口

**使用示例：**

```python
from rag5.core.agent import ErrorHandler

handler = ErrorHandler()

try:
    # 某些操作
    pass
except ConnectionError as e:
    message = handler.handle_connection_error(e, "Ollama")
    print(message)
except TimeoutError as e:
    message = handler.handle_timeout_error(e, "LLM 请求")
    print(message)
except Exception as e:
    # 统一处理
    message = handler.handle_error(e, context="处理查询")
    print(message)
```

### 6. RetryHandler（重试处理器）

提供带指数退避的重试逻辑。

**功能特性：**
- 自动重试失败的操作
- 指数退避延迟
- 可配置的重试次数和延迟
- 装饰器支持

**使用示例：**

```python
from rag5.core.agent import RetryHandler, retry_with_backoff

# 使用重试处理器
handler = RetryHandler(max_retries=3, initial_delay=1.0)

def unstable_function():
    # 可能失败的函数
    return "success"

result = handler.with_retry(unstable_function)

# 使用装饰器
@retry_with_backoff(max_retries=3, exception_types=(ConnectionError,))
def connect_to_service():
    # 连接服务的代码
    pass
```

## 代理工作流程

1. **初始化阶段**
   - 检查 Ollama 服务可用性
   - 检查 LLM 和嵌入模型可用性
   - 初始化 LLM
   - 加载工具（知识库搜索等）
   - 创建代理执行器

2. **查询处理阶段**
   - 接收用户查询和可选的聊天历史
   - 准备系统提示词（包含当前时间）
   - 转换聊天历史为 LangChain 消息格式
   - 调用代理执行器处理查询
   - 代理决定是否使用工具
   - 如果需要，调用知识库搜索工具
   - 基于检索结果生成答案

3. **错误处理阶段**
   - 捕获各种异常（连接错误、超时、验证错误等）
   - 自动重试（最多 2 次）
   - 返回用户友好的错误消息

4. **响应提取阶段**
   - 从代理结果中提取 AI 响应
   - 返回最终答案

## 提示词管理

提示词模块包含系统提示词和工具描述。

### 系统提示词

定义代理的行为和工具使用规则。

```python
from rag5.core.prompts import SYSTEM_PROMPT

# 系统提示词包含：
# - 工具使用规则
# - 查询优化要求
# - 回答要求
# - 当前时间占位符
# - 对话历史占位符
```

### 工具描述

定义工具的使用说明。

```python
from rag5.core.prompts import SEARCH_TOOL_DESCRIPTION

# 工具描述包含：
# - 使用场景
# - 参数说明
# - 查询优化示例
```

## 扩展代理

### 添加新工具

1. 在 `rag5/tools/` 中创建新工具
2. 在工具注册器中注册
3. 代理会自动加载新工具

```python
from langchain.tools import tool
from rag5.tools import tool_registry

@tool
def my_custom_tool(query: str) -> str:
    """自定义工具描述"""
    # 工具实现
    return "结果"

# 注册工具
tool_registry.register(my_custom_tool)
```

### 自定义错误处理

继承 `ErrorHandler` 类并添加自定义错误处理方法：

```python
from rag5.core.agent import ErrorHandler

class CustomErrorHandler(ErrorHandler):
    @staticmethod
    def handle_custom_error(error: Exception) -> str:
        # 自定义错误处理逻辑
        return "自定义错误消息"
```

### 自定义消息处理

继承 `MessageProcessor` 类并添加自定义消息处理方法：

```python
from rag5.core.agent import MessageProcessor

class CustomMessageProcessor(MessageProcessor):
    @staticmethod
    def custom_format(messages):
        # 自定义格式化逻辑
        pass
```

## 最佳实践

1. **使用便捷函数**：对于简单场景，使用 `ask()` 函数而不是直接创建代理实例

2. **管理对话历史**：使用 `ConversationHistory` 类来管理多轮对话

3. **错误处理**：始终捕获和处理异常，使用 `ErrorHandler` 提供用户友好的错误消息

4. **服务检查**：在生产环境中，使用 `AgentInitializer.check_services()` 检查服务可用性

5. **日志记录**：启用日志以便调试和监控

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 常见问题

### Q: 如何处理长对话历史？

A: 使用 `ConversationHistory.get_messages(limit=N)` 限制传递给代理的消息数量：

```python
history = ConversationHistory()
# ... 添加消息 ...

# 只获取最近的 10 条消息
recent_messages = history.get_messages(limit=10)
answer = agent.chat(query, chat_history=recent_messages)
```

### Q: 如何自定义重试逻辑？

A: 创建自定义的 `RetryHandler` 实例：

```python
from rag5.core.agent import RetryHandler

custom_handler = RetryHandler(
    max_retries=5,
    initial_delay=2.0,
    backoff_factor=3.0,
    max_delay=120.0
)

result = custom_handler.with_retry(my_function)
```

### Q: 如何更改系统提示词？

A: 修改 `rag5/core/prompts/system.py` 中的 `SYSTEM_PROMPT` 常量，或在创建代理时传递自定义提示词。

### Q: 代理初始化失败怎么办？

A: 检查以下几点：
1. Ollama 服务是否运行：`ollama serve`
2. 模型是否已安装：`ollama pull qwen2.5:7b` 和 `ollama pull bge-m3`
3. 配置是否正确：检查 `.env` 文件
4. 查看日志获取详细错误信息

## 相关文档

- [配置模块文档](../config/README.md)
- [工具模块文档](../tools/README.md)
- [API 参考文档](../../docs/api_reference.md)
- [开发指南](../../docs/development.md)
