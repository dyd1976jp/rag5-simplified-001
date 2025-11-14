# 工具模块

工具模块提供 RAG5 系统所需的各种工具功能，包括向量搜索、嵌入生成和向量数据库管理。

## 模块结构

```
tools/
├── __init__.py           # 模块导出
├── README.md            # 本文档
├── base.py              # 工具基类
├── registry.py          # 工具注册器
├── embeddings/          # 嵌入工具
│   ├── __init__.py
│   └── ollama_embeddings.py
├── vectordb/            # 向量数据库工具
│   ├── __init__.py
│   ├── connection.py
│   ├── qdrant_client.py
│   └── retry.py
└── search/              # 搜索工具
    ├── __init__.py
    └── search_tool.py
```

## 主要组件

### 1. 工具注册器 (registry.py)

工具注册器提供工具的注册和管理功能，允许动态添加和获取工具。

#### 使用示例

```python
from rag5.tools.registry import tool_registry
from rag5.tools.search import search_knowledge_base

# 注册工具
tool_registry.register(search_knowledge_base)

# 获取所有工具
all_tools = tool_registry.get_all()
print(f"可用工具: {tool_registry.get_tool_names()}")

# 按名称获取工具
tool = tool_registry.get_by_name("search_knowledge_base")
if tool:
    result = tool.invoke({"query": "测试查询"})
```

#### 主要方法

- `register(tool, name=None)`: 注册工具
- `get_by_name(name)`: 按名称获取工具
- `get_all()`: 获取所有工具
- `get_tool_names()`: 获取所有工具名称
- `has_tool(name)`: 检查工具是否存在
- `unregister(name)`: 注销工具
- `clear()`: 清空所有工具

### 2. 嵌入工具 (embeddings/)

嵌入工具提供文本向量化功能，支持 Ollama 嵌入模型。

#### 使用示例

```python
from rag5.tools.embeddings import OllamaEmbeddingsManager

# 创建嵌入模型管理器
manager = OllamaEmbeddingsManager(
    model="bge-m3",
    base_url="http://localhost:11434"
)

# 检查模型是否可用
if manager.check_model_available():
    # 初始化模型
    manager.initialize()
    
    # 向量化单个查询
    query_vector = manager.embed_query("什么是人工智能？")
    print(f"查询向量维度: {len(query_vector)}")
    
    # 向量化多个文档
    texts = ["文档1", "文档2", "文档3"]
    doc_vectors = manager.embed_documents(texts)
    print(f"生成了 {len(doc_vectors)} 个文档向量")
else:
    print(f"请运行: ollama pull {manager.model}")
```

#### 主要方法

- `check_ollama_available()`: 检查 Ollama 服务是否可用
- `check_model_available()`: 检查嵌入模型是否可用
- `initialize()`: 初始化嵌入模型
- `embed_query(text)`: 向量化查询文本
- `embed_documents(texts)`: 向量化多个文档

### 3. 向量数据库工具 (vectordb/)

向量数据库工具提供 Qdrant 向量数据库的连接管理、搜索和上传功能。

#### 3.1 连接管理器 (connection.py)

```python
from rag5.tools.vectordb import ConnectionManager

# 创建连接管理器
manager = ConnectionManager("http://localhost:6333")

# 测试连接
if manager.test_connection():
    print("连接成功")
    
    # 获取客户端
    client = manager.get_client()
    collections = client.get_collections()
    print(f"集合数量: {len(collections.collections)}")
    
    # 关闭连接
    manager.close()

# 使用上下文管理器
with ConnectionManager("http://localhost:6333") as manager:
    client = manager.get_client()
    # 使用客户端...
```

#### 3.2 Qdrant 管理器 (qdrant_client.py)

```python
from rag5.tools.vectordb import QdrantManager
from qdrant_client.models import PointStruct

# 创建 Qdrant 管理器
manager = QdrantManager("http://localhost:6333")

# 确保集合存在
manager.ensure_collection(
    collection_name="knowledge_base",
    vector_dim=1024
)

# 上传向量
points = [
    PointStruct(
        id=1,
        vector=[0.1, 0.2, ...],  # 1024维向量
        payload={
            "text": "文档内容",
            "source": "document.pdf",
            "metadata": {"page": 1}
        }
    )
]
manager.upsert("knowledge_base", points)

# 搜索向量
query_vector = [0.1, 0.2, ...]  # 1024维查询向量
results = manager.search(
    collection_name="knowledge_base",
    query_vector=query_vector,
    limit=5,
    score_threshold=0.7
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Text: {result.payload['text']}")
    print(f"Source: {result.payload['source']}")

# 获取集合信息
info = manager.get_collection_info("knowledge_base")
print(f"向量数量: {info['vectors_count']}")

# 统计点数量
count = manager.count_points("knowledge_base")
print(f"集合中有 {count} 个向量")
```

#### 3.3 重试装饰器 (retry.py)

```python
from rag5.tools.vectordb.retry import retry_with_backoff, execute_with_retry

# 使用装饰器
@retry_with_backoff(max_retries=3, initial_delay=1.0)
def unstable_function():
    # 可能失败的操作
    return api_call()

result = unstable_function()

# 使用函数式方式
result = execute_with_retry(
    lambda: api_call(),
    max_retries=3,
    initial_delay=1.0
)
```

### 4. 搜索工具 (search/)

搜索工具提供知识库向量搜索功能，整合了嵌入和向量数据库功能。

#### 使用示例

```python
from rag5.tools.search import search_knowledge_base, get_search_tool
import json

# 方式1: 直接调用工具函数
result_json = search_knowledge_base.invoke({"query": "什么是人工智能？"})
result = json.loads(result_json)

print(f"找到 {result['total_count']} 个结果")
for item in result['results']:
    print(f"Score: {item['score']}")
    print(f"Content: {item['content'][:100]}...")
    print(f"Source: {item['source']}")
    print()

# 方式2: 获取工具对象
tool = get_search_tool()
result_json = tool.invoke({"query": "机器学习的应用"})

# 处理错误情况
result = json.loads(result_json)
if 'error' in result:
    print(f"搜索失败: {result['error']}")
else:
    print(f"搜索成功，找到 {result['total_count']} 个结果")
```

#### 返回格式

搜索工具返回 JSON 字符串，格式如下：

```json
{
  "results": [
    {
      "score": 0.85,
      "content": "文档内容...",
      "source": "document.pdf",
      "metadata": {
        "page": 1,
        "chapter": "第一章"
      }
    }
  ],
  "total_count": 1
}
```

错误情况：

```json
{
  "error": "错误信息",
  "results": [],
  "total_count": 0
}
```

## 工具基类 (base.py)

如果需要创建自定义工具，可以继承 `BaseTool` 基类：

```python
from rag5.tools.base import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="这是我的自定义工具"
        )
    
    def execute(self, **kwargs):
        # 实现工具逻辑
        query = kwargs.get('query', '')
        # 处理查询...
        return result
    
    def validate_params(self, **kwargs):
        # 验证参数
        return 'query' in kwargs

# 使用自定义工具
tool = MyCustomTool()
result = tool.execute(query="测试")
```

## 配置

工具模块使用全局配置，可以通过环境变量或 `.env` 文件配置：

```bash
# Ollama 配置
OLLAMA_HOST=http://localhost:11434
EMBED_MODEL=bge-m3

# Qdrant 配置
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=knowledge_base
VECTOR_DIM=1024

# 检索参数
TOP_K=5
SIMILARITY_THRESHOLD=0.7
```

在代码中访问配置：

```python
from rag5.config import settings

print(f"Ollama Host: {settings.ollama_host}")
print(f"Embed Model: {settings.embed_model}")
print(f"Qdrant URL: {settings.qdrant_url}")
print(f"Collection: {settings.collection_name}")
print(f"Top K: {settings.top_k}")
```

## 错误处理

所有工具都实现了完善的错误处理：

1. **连接错误**: 自动重试，记录警告
2. **模型不可用**: 提供清晰的错误信息和解决方案
3. **搜索失败**: 返回错误信息，不中断程序
4. **参数验证**: 在执行前验证参数有效性

示例：

```python
from rag5.tools.search import search_knowledge_base
import json

result_json = search_knowledge_base.invoke({"query": ""})
result = json.loads(result_json)

if 'error' in result:
    print(f"错误: {result['error']}")
    # 处理错误...
else:
    # 处理正常结果...
    pass
```

## 扩展工具

### 添加新工具

1. 创建工具函数或类
2. 使用 `@tool` 装饰器（LangChain）
3. 注册到工具注册器

```python
from langchain_core.tools import tool
from rag5.tools.registry import tool_registry

@tool
def my_new_tool(param: str) -> str:
    """
    我的新工具
    
    参数:
        param: 参数说明
    
    返回:
        结果说明
    """
    # 实现工具逻辑
    return f"处理结果: {param}"

# 注册工具
tool_registry.register(my_new_tool)
```

### 添加新的嵌入模型

如果需要支持其他嵌入模型，可以创建新的管理器类：

```python
from rag5.tools.embeddings.ollama_embeddings import OllamaEmbeddingsManager

class CustomEmbeddingsManager(OllamaEmbeddingsManager):
    def __init__(self, model: str, base_url: str, **kwargs):
        super().__init__(model, base_url)
        # 添加自定义初始化...
    
    def embed_query(self, text: str):
        # 自定义实现...
        pass
```

## 测试

工具模块包含完整的单元测试：

```bash
# 运行所有工具测试
pytest tests/test_tools/ -v

# 运行特定测试
pytest tests/test_tools/test_search.py -v
pytest tests/test_tools/test_embeddings.py -v
pytest tests/test_tools/test_vectordb.py -v
```

## 常见问题

### Q: 如何检查 Ollama 服务是否运行？

```python
from rag5.tools.embeddings import OllamaEmbeddingsManager

manager = OllamaEmbeddingsManager("bge-m3", "http://localhost:11434")
if manager.check_ollama_available():
    print("Ollama 服务正在运行")
else:
    print("请运行: ollama serve")
```

### Q: 如何检查嵌入模型是否已下载？

```python
from rag5.tools.embeddings import OllamaEmbeddingsManager

manager = OllamaEmbeddingsManager("bge-m3", "http://localhost:11434")
if manager.check_model_available():
    print("模型已就绪")
else:
    print("请运行: ollama pull bge-m3")
```

### Q: 如何处理搜索超时？

工具已内置重试机制，会自动处理临时性错误。如果需要自定义超时：

```python
from rag5.tools.vectordb.retry import retry_with_backoff

@retry_with_backoff(max_retries=5, initial_delay=2.0)
def my_search():
    # 搜索逻辑...
    pass
```

### Q: 如何清空向量数据库？

```python
from rag5.tools.vectordb import QdrantManager

manager = QdrantManager("http://localhost:6333")
manager.delete_collection("knowledge_base")
```

## 性能优化

1. **单例模式**: 嵌入和 Qdrant 管理器使用单例模式，避免重复初始化
2. **批量处理**: 使用 `embed_documents()` 批量向量化文档
3. **连接复用**: 连接管理器复用 Qdrant 连接
4. **重试机制**: 自动重试临时性错误，提高稳定性

## 相关文档

- [配置模块文档](../config/README.md)
- [核心模块文档](../core/README.md)
- [数据摄取模块文档](../ingestion/README.md)
