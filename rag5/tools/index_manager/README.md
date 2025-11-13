# 索引管理工具

索引管理工具提供了管理向量数据库索引的功能，包括清空集合、重新索引和验证索引结果。

## 功能特性

- **清空集合**: 删除指定集合及其所有数据
- **重新索引**: 支持全量索引和增量索引
- **验证索引**: 检查集合状态并执行测试查询
- **增量索引**: 只处理新增或修改的文档，提高效率
- **详细报告**: 生成包含统计信息的索引报告

## 使用方法

### 命令行工具

#### 1. 清空集合

删除指定集合及其所有数据：

```bash
# 清空默认集合
python -m rag5.tools.index_manager.cli clear

# 清空指定集合
python -m rag5.tools.index_manager.cli clear --collection my_collection

# 跳过确认提示
python -m rag5.tools.index_manager.cli clear --collection my_collection -y
```

#### 2. 重新索引

索引指定目录下的所有支持的文档：

```bash
# 增量索引（只处理新增或修改的文件）
python -m rag5.tools.index_manager.cli reindex --directory ./docs

# 强制重新索引（清空现有数据）
python -m rag5.tools.index_manager.cli reindex --directory ./docs --force

# 指定集合名称
python -m rag5.tools.index_manager.cli reindex --directory ./docs --collection my_collection

# 跳过确认提示
python -m rag5.tools.index_manager.cli reindex --directory ./docs --force -y

# 启用详细日志
python -m rag5.tools.index_manager.cli reindex --directory ./docs --verbose
```

#### 3. 验证索引

检查集合状态并可选地执行测试查询：

```bash
# 验证默认集合
python -m rag5.tools.index_manager.cli verify

# 验证指定集合
python -m rag5.tools.index_manager.cli verify --collection my_collection

# 执行测试查询
python -m rag5.tools.index_manager.cli verify --test-query "于朦朧"

# 执行多个测试查询
python -m rag5.tools.index_manager.cli verify --test-query "查询1" --test-query "查询2"
```

### Python API

#### 基本使用

```python
from rag5.config import settings
from rag5.tools.vectordb import QdrantManager
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.ingestion import (
    IngestionPipeline,
    RecursiveSplitter,
    BatchVectorizer,
    VectorUploader
)
from rag5.tools.index_manager import IndexManager

# 初始化组件
qdrant = QdrantManager(settings.qdrant_url)
embeddings = OllamaEmbeddingsManager(settings.embed_model, settings.ollama_host)

# 创建摄取流程
splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)
vectorizer = BatchVectorizer(embeddings.embeddings, batch_size=100)
uploader = VectorUploader(qdrant, settings.collection_name)
pipeline = IngestionPipeline(splitter, vectorizer, uploader)

# 创建索引管理器
manager = IndexManager(qdrant, pipeline)
```

#### 清空集合

```python
# 清空集合
success = manager.clear_collection("knowledge_base")
if success:
    print("集合已清空")
```

#### 重新索引

```python
# 强制重新索引
report = manager.reindex_directory(
    directory="./docs",
    collection_name="knowledge_base",
    force=True,
    vector_dim=1024
)

print(f"索引报告:")
print(f"  - 成功: {report.success}")
print(f"  - 文档数: {report.documents_indexed}")
print(f"  - 向量数: {report.vectors_uploaded}")
print(f"  - 耗时: {report.total_time:.2f}秒")

# 增量索引（只处理新增或修改的文件）
report = manager.reindex_directory(
    directory="./docs",
    collection_name="knowledge_base",
    force=False  # 不清空现有数据
)
```

#### 验证索引

```python
# 验证索引结果
result = manager.verify_indexing(
    collection_name="knowledge_base",
    test_queries=["于朦朧", "测试查询"]
)

# 输出集合统计
stats = result['collection_stats']
print(f"点数量: {stats['points_count']}")
print(f"向量数量: {stats['vectors_count']}")

# 输出测试结果
for test in result['test_results']:
    print(f"查询 '{test['query']}': {test['results_count']} 个结果")
```

## 索引报告

重新索引操作会生成详细的索引报告，包含以下信息：

```python
@dataclass
class IndexReport:
    success: bool              # 是否成功
    documents_indexed: int     # 成功索引的文档数
    chunks_created: int        # 创建的文档块数
    vectors_uploaded: int      # 成功上传的向量数
    failed_files: List[str]    # 失败的文件列表
    errors: List[str]          # 错误信息列表
    total_time: float          # 总耗时（秒）
    timestamp: datetime        # 时间戳
```

## 增量索引

增量索引功能会跟踪已索引文件的修改时间，只处理新增或修改的文件：

- **新文件**: 自动检测并索引
- **修改文件**: 检测修改时间变化并重新索引
- **未修改文件**: 跳过，不重复处理

这大大提高了大型文档集的索引效率。

## 日志

索引管理工具会生成详细的日志，记录在：

- 控制台输出
- 日志文件: `logs/index_manager.log`

使用 `--verbose` 或 `-v` 参数可以启用详细日志（DEBUG级别）。

## 注意事项

1. **强制重新索引**: 使用 `--force` 参数会删除集合中的所有现有数据，请谨慎使用
2. **确认提示**: 危险操作（如清空集合、强制重新索引）会要求确认，使用 `-y` 参数可跳过
3. **增量索引**: 首次索引或需要完全重建索引时，使用 `--force` 参数
4. **文件跟踪**: 增量索引依赖文件修改时间，如果文件被移动或重命名，会被视为新文件

## 示例场景

### 场景1: 首次索引

```bash
# 首次索引，使用强制模式
python -m rag5.tools.index_manager.cli reindex \
    --directory ./docs \
    --collection knowledge_base \
    --force \
    -y
```

### 场景2: 添加新文档

```bash
# 增量索引，只处理新增文件
python -m rag5.tools.index_manager.cli reindex \
    --directory ./docs \
    --collection knowledge_base
```

### 场景3: 验证索引质量

```bash
# 验证索引并测试查询
python -m rag5.tools.index_manager.cli verify \
    --collection knowledge_base \
    --test-query "于朦朧" \
    --test-query "测试查询"
```

### 场景4: 重建索引

```bash
# 清空并重新索引
python -m rag5.tools.index_manager.cli clear --collection knowledge_base -y
python -m rag5.tools.index_manager.cli reindex \
    --directory ./docs \
    --collection knowledge_base \
    --force \
    -y
```

## 故障排除

### 问题1: 连接失败

如果出现连接错误，请检查：

- Qdrant服务是否运行
- Ollama服务是否运行
- 配置文件中的URL是否正确

### 问题2: 索引失败

如果索引失败，请检查：

- 文档格式是否支持
- 文件是否可读
- 磁盘空间是否充足
- 查看日志文件获取详细错误信息

### 问题3: 增量索引不工作

如果增量索引没有检测到新文件：

- 确认文件确实是新增或修改的
- 尝试使用 `--force` 参数强制重新索引
- 检查文件权限和修改时间

## 相关文档

- [数据摄取流程](../../ingestion/README.md)
- [向量数据库管理](../vectordb/README.md)
- [诊断工具](../diagnostics/README.md)
