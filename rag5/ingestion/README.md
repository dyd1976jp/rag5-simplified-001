# 数据摄取模块

数据摄取模块负责将文档加载、分块、向量化并存储到向量数据库的完整流程。

## 功能概述

数据摄取模块提供以下核心功能：

1. **文档加载**: 支持多种文件格式的文档加载
2. **文档分块**: 将长文档分割成适合向量化的小块
3. **向量化**: 将文本块转换为向量表示
4. **向量上传**: 批量上传向量到Qdrant数据库

## 模块结构

```
ingestion/
├── __init__.py           # 模块导出
├── README.md            # 本文档
├── pipeline.py          # 流程编排器
├── loaders/             # 文档加载器
│   ├── __init__.py
│   ├── base.py          # 加载器基类
│   ├── text_loader.py   # 文本文件加载器
│   ├── pdf_loader.py    # PDF加载器
│   └── markdown_loader.py # Markdown加载器
├── splitters/           # 文档分块器
│   ├── __init__.py
│   └── recursive_splitter.py # 递归分块器
└── vectorizers/         # 向量化器
    ├── __init__.py
    ├── batch_vectorizer.py # 批量向量化
    └── uploader.py      # 向量上传器
```

## 支持的文件格式

| 格式 | 扩展名 | 加载器 | 说明 |
|------|--------|--------|------|
| 文本 | .txt | TextLoader | 支持多种编码（UTF-8, GBK, GB2312, Latin-1） |
| PDF | .pdf | PDFLoader | 使用PyPDF解析 |
| Markdown | .md, .markdown | MarkdownLoader | 使用Unstructured解析 |

## 摄取流程

数据摄取流程包含以下步骤：

```
1. 文档加载 (Loading)
   ↓
2. 文档分块 (Splitting)
   ↓
3. 向量生成 (Vectorization)
   ↓
4. 向量上传 (Uploading)
```

### 步骤详解

#### 1. 文档加载

- 扫描目录，识别支持的文件类型
- 根据文件扩展名选择合适的加载器
- 验证文件大小和编码
- 提取文档内容和元数据

#### 2. 文档分块

- 使用递归字符分块器
- 支持中英文分隔符
- 配置块大小和重叠
- 保留文档元数据

#### 3. 向量生成

- 批量生成文档向量
- 使用嵌入模型（如bge-m3）
- 自动重试失败的块
- 创建Qdrant Point对象

#### 4. 向量上传

- 批量上传到Qdrant
- 指数退避重试机制
- 错误处理和日志记录
- 返回上传统计信息

## 使用示例

### 基本用法

```python
from rag5.config import settings
from rag5.tools.embeddings import OllamaEmbeddingsManager
from rag5.tools.vectordb import QdrantManager
from rag5.ingestion import (
    IngestionPipeline,
    RecursiveSplitter,
    BatchVectorizer,
    VectorUploader
)

# 初始化组件
embeddings_manager = OllamaEmbeddingsManager(
    model=settings.embed_model,
    base_url=settings.ollama_host
)

qdrant_manager = QdrantManager(url=settings.qdrant_url)

# 创建流程组件
splitter = RecursiveSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap
)

vectorizer = BatchVectorizer(
    embeddings=embeddings_manager.embeddings,
    batch_size=100
)

uploader = VectorUploader(
    qdrant_manager=qdrant_manager,
    collection_name=settings.collection_name,
    batch_size=100
)

# 创建摄取流程
pipeline = IngestionPipeline(
    splitter=splitter,
    vectorizer=vectorizer,
    uploader=uploader
)

# 执行摄取
result = pipeline.ingest_directory("./docs")

# 查看结果
print(f"文档加载: {result.documents_loaded}")
print(f"文档块: {result.chunks_created}")
print(f"向量上传: {result.vectors_uploaded}")
print(f"成功率: {result.success_rate:.1f}%")
```

### 摄取单个文件

```python
# 摄取单个文件
result = pipeline.ingest_file("./docs/document.pdf")

if result.errors:
    print("摄取失败:")
    for error in result.errors:
        print(f"  - {error}")
else:
    print(f"成功上传 {result.vectors_uploaded} 个向量")
```

### 自定义加载器

```python
from rag5.ingestion import BaseLoader, IngestionPipeline
from langchain_core.documents import Document

class CustomLoader(BaseLoader):
    """自定义文档加载器"""
    
    SUPPORTED_EXTENSIONS = {'.custom'}
    
    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def load(self, file_path: str) -> List[Document]:
        self._validate_file(file_path)
        # 实现自定义加载逻辑
        content = "..."
        return [Document(page_content=content, metadata={"source": file_path})]

# 使用自定义加载器
custom_loader = CustomLoader()
pipeline = IngestionPipeline(
    splitter=splitter,
    vectorizer=vectorizer,
    uploader=uploader,
    loaders=[custom_loader]  # 使用自定义加载器
)
```

### 自定义分块策略

```python
from rag5.ingestion import RecursiveSplitter

# 自定义分隔符
custom_separators = [
    "\n\n\n",  # 三个换行
    "\n\n",    # 两个换行
    "\n",      # 单个换行
    "。",      # 中文句号
    ".",       # 英文句号
    " ",       # 空格
    ""         # 字符级
]

splitter = RecursiveSplitter(
    chunk_size=1000,      # 更大的块
    chunk_overlap=100,    # 更多重叠
    separators=custom_separators
)
```

### 批量处理配置

```python
# 配置批量大小
vectorizer = BatchVectorizer(
    embeddings=embeddings_manager.embeddings,
    batch_size=50,      # 每批50个文档
    max_retries=3       # 最多重试3次
)

uploader = VectorUploader(
    qdrant_manager=qdrant_manager,
    collection_name=settings.collection_name,
    batch_size=200,     # 每批上传200个向量
    max_retries=5       # 最多重试5次
)
```

## 错误处理

摄取流程包含完善的错误处理机制：

### 文件级错误

- 文件不存在或无法访问
- 文件格式不支持
- 文件大小超过限制
- 编码错误

**处理方式**: 记录错误，跳过该文件，继续处理其他文件

### 块级错误

- 向量生成失败
- 网络连接问题

**处理方式**: 自动重试，记录失败的块，继续处理其他块

### 批次级错误

- 上传失败
- Qdrant连接问题

**处理方式**: 指数退避重试，记录失败的批次

### 查看错误信息

```python
result = pipeline.ingest_directory("./docs")

if result.failed_files:
    print("失败的文件:")
    for file in result.failed_files:
        print(f"  - {file}")

if result.errors:
    print("\n错误信息:")
    for error in result.errors:
        print(f"  - {error}")
```

## 性能优化

### 批量大小调整

根据系统资源调整批量大小：

- **内存充足**: 增大batch_size（如200-500）
- **内存有限**: 减小batch_size（如50-100）
- **网络不稳定**: 减小batch_size，增加重试次数

### 并行处理

当前实现是串行处理，未来可以考虑：

- 并行加载多个文件
- 并行生成向量
- 并行上传批次

### 缓存优化

考虑添加向量缓存：

- 避免重复向量化相同内容
- 使用文件哈希作为缓存键
- 定期清理过期缓存

## 日志配置

摄取模块使用Python标准logging模块：

```python
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 获取模块日志记录器
logger = logging.getLogger('rag5.ingestion')
logger.setLevel(logging.DEBUG)  # 详细日志
```

## 常见问题

### Q: 如何处理大文件？

A: 系统默认限制文件大小为100MB。对于更大的文件：
1. 在加载器中调整max_size参数
2. 考虑预先分割大文件
3. 增加系统内存

### Q: 如何提高摄取速度？

A: 可以采取以下措施：
1. 增大batch_size
2. 使用更快的嵌入模型
3. 优化网络连接
4. 考虑并行处理

### Q: 如何处理特殊编码的文件？

A: TextLoader支持多种编码：
1. 默认尝试UTF-8, GBK, GB2312, Latin-1
2. 可以扩展ENCODINGS列表添加更多编码
3. 或实现自定义加载器

### Q: 摄取失败如何恢复？

A: 系统设计为容错的：
1. 失败的文件会被记录在result.failed_files
2. 可以单独重新摄取失败的文件
3. 已成功的文件不会重复处理（除非删除向量）

## 扩展开发

### 添加新的文档加载器

1. 继承BaseLoader类
2. 实现supports()和load()方法
3. 注册到IngestionPipeline

```python
from rag5.ingestion import BaseLoader

class MyLoader(BaseLoader):
    SUPPORTED_EXTENSIONS = {'.myformat'}
    
    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def load(self, file_path: str) -> List[Document]:
        self._validate_file(file_path)
        # 实现加载逻辑
        pass
```

### 自定义分块策略

1. 创建新的分块器类
2. 实现split_documents()方法
3. 传递给IngestionPipeline

### 添加预处理步骤

可以在加载后、分块前添加预处理：

```python
def preprocess_documents(documents):
    """预处理文档"""
    for doc in documents:
        # 清理文本
        doc.page_content = doc.page_content.strip()
        # 添加元数据
        doc.metadata['processed'] = True
    return documents

# 在流程中使用
documents = loader.load(file_path)
documents = preprocess_documents(documents)
chunks = splitter.split_documents(documents)
```

## 相关模块

- **config**: 配置管理，提供摄取参数
- **tools.embeddings**: 嵌入模型管理
- **tools.vectordb**: Qdrant数据库管理
- **core.agent**: 使用摄取的数据进行问答

## 参考资料

- [LangChain文档加载器](https://python.langchain.com/docs/modules/data_connection/document_loaders/)
- [LangChain文本分块器](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [Qdrant文档](https://qdrant.tech/documentation/)
- [Ollama嵌入模型](https://ollama.ai/library)
