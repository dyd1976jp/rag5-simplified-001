# 诊断工具模块

提供 Qdrant 向量数据库的检查、诊断和验证功能。

## 功能概述

### QdrantInspector 类

核心诊断类，提供以下功能：

1. **集合统计信息** - 获取集合的点数量、向量数量和状态
2. **关键词搜索** - 通过遍历 payload 搜索包含特定关键词的文档
3. **样本数据获取** - 获取集合中的样本数据点用于检查
4. **嵌入模型验证** - 验证嵌入模型是否正常工作

### 命令行工具

`db_check.py` 提供便捷的命令行接口用于数据库诊断。

## 使用方法

### 1. 作为 Python 模块使用

```python
from rag5.tools.vectordb import QdrantManager
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.diagnostics import QdrantInspector
from rag5.config import settings

# 初始化管理器
qdrant = QdrantManager(settings.qdrant_url)
embeddings = OllamaEmbeddingsManager(
    model=settings.embed_model,
    base_url=settings.ollama_host
)

# 创建检查器
inspector = QdrantInspector(qdrant, embeddings)

# 获取集合统计
stats = inspector.get_collection_stats("knowledge_base")
print(f"集合中有 {stats['points_count']} 个点")

# 搜索关键词
results = inspector.search_by_keyword("knowledge_base", "于朦朧", limit=10)
for result in results:
    print(f"找到: {result['source']}, 出现 {result['keyword_count']} 次")

# 获取样本数据
samples = inspector.get_sample_points("knowledge_base", limit=5)
for sample in samples:
    print(f"样本 {sample['id']}: 维度={sample['vector_dim']}")

# 验证嵌入模型
result = inspector.verify_embeddings("knowledge_base")
if result['model_working']:
    print(f"✓ 模型正常，向量维度: {result['vector_dim']}")
else:
    print(f"✗ 模型异常: {result.get('error')}")
```

### 2. 使用命令行工具

#### 检查集合统计信息

```bash
python -m rag5.tools.diagnostics.db_check --collection knowledge_base
```

输出示例：
```
================================================================================
  集合统计信息: knowledge_base
================================================================================

✓ 集合状态: green
  - 点数量: 150
  - 向量数量: 150
  - 已索引向量: 150
```

#### 搜索关键词

```bash
python -m rag5.tools.diagnostics.db_check --collection knowledge_base --search "于朦朧"
```

输出示例：
```
================================================================================
  关键词搜索: '于朦朧'
================================================================================

✓ 找到 3 个包含关键词 '于朦朧' 的结果:

1. ID: 123e4567-e89b-12d3-a456-426614174000
   来源: 1i0ae3sumrl64W5nn7PshnNla14b1c.txt
   出现次数: 5
   文本预览: ...于朦朧在剧中饰演...
```

#### 获取样本数据

```bash
python -m rag5.tools.diagnostics.db_check --collection knowledge_base --samples 10
```

#### 验证嵌入模型

```bash
python -m rag5.tools.diagnostics.db_check --collection knowledge_base --verify-embeddings
```

输出示例：
```
================================================================================
  嵌入模型验证
================================================================================

✓ 嵌入模型验证成功
  - 模型名称: bge-m3
  - 向量维度: 1024
  - 期望维度: 1024
  - 维度匹配: ✓
  - 成功测试: 3/3
  - 平均时间: 0.234s

测试详情:
  1. ✓ '这是一个测试文本'
     维度=1024, 时间=0.245s
  2. ✓ '人工智能是什么？'
     维度=1024, 时间=0.223s
  3. ✓ '于朦朧是谁？'
     维度=1024, 时间=0.234s
```

#### 完整诊断（执行所有检查）

```bash
python -m rag5.tools.diagnostics.db_check --collection knowledge_base --all
```

这将执行所有检查并生成完整的诊断报告，包括：
- 集合统计信息
- 关键词搜索（默认搜索"于朦朧"）
- 样本数据（默认 5 个样本）
- 嵌入模型验证
- 诊断报告（发现的问题和建议）

#### 启用调试日志

```bash
python -m rag5.tools.diagnostics.db_check --collection knowledge_base --all --debug
```

## API 参考

### QdrantInspector

#### `__init__(qdrant_manager, embeddings_manager=None)`

初始化检查器。

**参数:**
- `qdrant_manager`: QdrantManager 实例
- `embeddings_manager`: OllamaEmbeddingsManager 实例（可选）

#### `get_collection_stats(collection_name: str) -> Dict[str, Any]`

获取集合统计信息。

**返回:**
```python
{
    "exists": bool,
    "points_count": int,
    "vectors_count": int,
    "indexed_vectors_count": int,
    "status": str
}
```

#### `search_by_keyword(collection_name: str, keyword: str, limit: int = 10) -> List[Dict[str, Any]]`

通过关键词搜索文档。

**返回:**
```python
[
    {
        "id": str,
        "text": str,
        "full_text": str,
        "source": str,
        "contains_keyword": bool,
        "keyword_count": int
    }
]
```

#### `get_sample_points(collection_name: str, limit: int = 5) -> List[Dict[str, Any]]`

获取样本数据点。

**返回:**
```python
[
    {
        "id": str,
        "vector_dim": int,
        "payload": dict,
        "has_text": bool,
        "has_source": bool,
        "text_preview": str
    }
]
```

#### `verify_embeddings(collection_name: str, test_texts: Optional[List[str]] = None) -> Dict[str, Any]`

验证嵌入模型。

**返回:**
```python
{
    "model_working": bool,
    "model_name": str,
    "vector_dim": int,
    "expected_dim": int,
    "dimension_match": bool,
    "test_results": List[dict],
    "average_time": float,
    "total_tests": int,
    "successful_tests": int
}
```

## 常见问题

### Q: 为什么关键词搜索很慢？

A: 关键词搜索需要遍历所有点的 payload，对于大型集合可能需要一些时间。这是正常的，因为它不使用向量搜索，而是直接检查文本内容。

### Q: 如何解决"集合不存在"的错误？

A: 首先需要索引文档：
```bash
python -m rag5.interfaces.cli ingest <directory>
```

### Q: 嵌入模型验证失败怎么办？

A: 检查以下几点：
1. Ollama 服务是否运行：`ollama serve`
2. 模型是否已下载：`ollama pull bge-m3`
3. 配置文件中的模型名称是否正确

### Q: 向量维度不匹配怎么办？

A: 这通常意味着集合中的向量是用不同的模型创建的。解决方法：
1. 清空集合
2. 使用当前模型重新索引文档

## 故障排查流程

1. **检查集合状态**
   ```bash
   python -m rag5.tools.diagnostics.db_check --collection knowledge_base
   ```

2. **验证数据存在**
   ```bash
   python -m rag5.tools.diagnostics.db_check --collection knowledge_base --samples 5
   ```

3. **搜索特定内容**
   ```bash
   python -m rag5.tools.diagnostics.db_check --collection knowledge_base --search "关键词"
   ```

4. **验证嵌入模型**
   ```bash
   python -m rag5.tools.diagnostics.db_check --collection knowledge_base --verify-embeddings
   ```

5. **完整诊断**
   ```bash
   python -m rag5.tools.diagnostics.db_check --collection knowledge_base --all
   ```

## 相关文档

- [Qdrant 客户端文档](../vectordb/README.md)
- [嵌入模型文档](../embeddings/README.md)
- [配置文档](../../config/README.md)
