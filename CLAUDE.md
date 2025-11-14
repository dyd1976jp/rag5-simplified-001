# CLAUDE.md - AI Assistant Guide for rag5-simplified-001

## Repository Overview

**Project Name**: rag5-simplified-001
**Type**: Retrieval-Augmented Generation (RAG) System - Simplified Implementation
**Purpose**: A simplified RAG implementation focusing on efficient document retrieval and generation

## Table of Contents

1. [Language Requirements](#language-requirements)
2. [Repository Status](#repository-status)
3. [Expected Architecture](#expected-architecture)
4. [Development Workflow](#development-workflow)
5. [Code Conventions](#code-conventions)
6. [Key Components](#key-components)
7. [Testing Strategy](#testing-strategy)
8. [Dependencies & Tools](#dependencies--tools)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)

---

## Language Requirements

**项目语言规范 / Project Language Standards**

### 对话语言 / Communication Language

- **AI 助手与用户的对话必须使用中文**
- All conversations between AI assistants and users must be conducted in Chinese
- 问题讨论、建议、解释等都应使用中文

### 代码注释与文档 / Code Comments and Documentation

- **所有代码注释必须使用中文**
- **所有文档字符串 (docstrings) 必须使用中文**
- **README、文档文件等说明性内容必须使用中文**
- 变量名、函数名、类名等标识符应使用英文（符合 Python 规范）
- Git 提交信息可以使用中文或英文

### 示例 / Examples

```python
from typing import List, Dict, Optional
import numpy as np


def retrieve_documents(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict[str, any]]:
    """检索与查询相关的文档。

    根据给定的查询字符串，从向量数据库中检索最相关的文档。
    使用余弦相似度进行排序，并返回得分最高的文档。

    参数:
        query: 查询字符串
        top_k: 返回的文档数量
        similarity_threshold: 最小相似度阈值

    返回:
        包含文档内容和元数据的字典列表

    异常:
        ValueError: 当查询为空或 top_k 无效时

    示例:
        >>> docs = retrieve_documents("什么是 RAG？", top_k=3)
        >>> len(docs) <= 3
        True
    """
    if not query:
        raise ValueError("查询不能为空")

    # 实现检索逻辑
    # TODO: 添加向量嵌入生成
    # TODO: 执行相似度搜索
    pass
```

### 配置文件 / Configuration Files

配置文件（YAML、JSON等）中的键名使用英文，注释和描述使用中文：

```yaml
# 模型配置
model_config:
  embedding_model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  dimension: 384  # 嵌入向量维度
  normalize: true  # 是否归一化向量

# 检索配置
retrieval_config:
  top_k: 5  # 返回文档数量
  similarity_metric: "cosine"  # 相似度计算方式：cosine, euclidean, dot_product
```

### 重要提醒 / Important Notes

- ✅ **必须做**: 所有注释、文档、对话使用中文
- ✅ **推荐做**: Git 提交信息使用中文，便于团队理解
- ❌ **不要做**: 代码标识符（变量名、函数名、类名）使用中文
- ❌ **不要做**: 与用户对话时使用英文

---

## Repository Status

**Current State**: 功能完整的 RAG 系统 (Fully Functional RAG System)
**Version**: 2.0.0
**Branch**: `claude/claude-md-mhy48gl18qidu2w9-01RjkXCxeamU1fV2631u67h7`

**已实现的功能 (Implemented Features):**
- ✅ 核心 RAG 引擎 (基于 LangChain + LangGraph)
- ✅ Ollama LLM 集成 (qwen2.5:7b + bge-m3 embeddings)
- ✅ Qdrant 向量数据库集成
- ✅ 文档摄取管道 (加载器、分块器、向量化器)
- ✅ 知识库管理系统
- ✅ REST API 接口 (FastAPI)
- ✅ Web UI 界面 (Streamlit)
- ✅ 完整的测试套件
- ✅ 调试和性能分析工具
- ✅ 日志系统和监控

**项目文件结构 (Current Structure):**
- `rag5/` - 主要源代码
- `tests/` - 测试套件
- `scripts/` - 工具脚本
- `examples/` - 使用示例
- `docs/` - 文档
- `kb-frontend-ui/` - 前端 UI 设计文档
- `data/`, `text/` - 数据目录
- `README.md` - 完整的项目文档
- `requirements.txt` - Python 依赖
- `setup.py` - 包配置

---

## 实际架构 (Actual Architecture)

### 项目结构 (Project Structure)

```
rag5-simplified-001/
├── rag5/                       # 主要源代码包
│   ├── __init__.py            # 包入口，延迟导入优化
│   ├── config/                # 配置管理
│   │   ├── settings.py        # 设置加载
│   │   ├── loader.py          # 配置加载器
│   │   └── validator.py       # 配置验证
│   ├── core/                  # 核心模块
│   │   ├── agent/             # RAG Agent 实现
│   │   ├── knowledge_base/    # 知识库管理
│   │   └── prompts/           # 提示词模板
│   ├── ingestion/             # 数据摄取模块
│   │   ├── loaders/           # 文档加载器 (PDF, TXT, etc.)
│   │   ├── splitters/         # 文本分块器
│   │   ├── vectorizers/       # 向量化器
│   │   └── pipeline.py        # 摄取流水线
│   ├── tools/                 # 工具系统
│   │   ├── search/            # 向量搜索工具
│   │   ├── embeddings/        # 嵌入生成工具
│   │   ├── database/          # 数据库工具
│   │   └── registry.py        # 工具注册表
│   ├── interfaces/            # 接口层
│   │   ├── api/               # REST API (FastAPI)
│   │   └── ui/                # Web UI (Streamlit)
│   └── utils/                 # 工具函数
│       ├── logger.py          # 日志系统
│       ├── monitoring.py      # 监控工具
│       └── security.py        # 安全工具
├── tests/                     # 测试套件
│   ├── test_config/           # 配置测试
│   ├── test_core/             # 核心功能测试
│   ├── test_ingestion/        # 摄取模块测试
│   ├── test_tools/            # 工具测试
│   ├── test_interfaces/       # 接口测试
│   ├── test_integration/      # 集成测试
│   ├── test_performance/      # 性能测试
│   └── test_utils/            # 工具函数测试
├── scripts/                   # 工具脚本
│   ├── ingest.py              # 文档摄取脚本
│   ├── run_api.py             # API 服务器启动
│   ├── run_ui.py              # UI 启动脚本
│   ├── kb_manager.py          # 知识库管理
│   ├── debug_retrieval.py     # 检索调试
│   ├── test_e2e.py            # 端到端测试
│   └── validate_*.py          # 验证脚本
├── examples/                  # 使用示例
│   ├── kb_management/         # 知识库管理示例
│   └── analyze_*.py           # 分析脚本示例
├── kb-frontend-ui/            # 前端 UI 设计文档
│   ├── design.md              # UI 设计文档
│   ├── requirements.md        # UI 需求文档
│   └── tasks.md               # UI 任务清单
├── data/                      # 数据存储目录
├── text/                      # 文本数据目录
├── docs/                      # 文档目录
├── requirements.txt           # Python 依赖
├── setup.py                   # 包安装配置
├── setup_models.sh            # 模型安装脚本
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略规则
├── README.md                  # 项目文档 (中英双语)
└── CLAUDE.md                  # AI 助手指南 (本文件)
```

### 技术栈 (Technology Stack)

**实际使用的技术：**

- **语言 (Language)**: Python 3.9+
- **LLM 模型 (LLM)**: Ollama (qwen2.5:7b)
- **嵌入模型 (Embeddings)**: Ollama (bge-m3)
- **向量数据库 (Vector Store)**: Qdrant
- **编排框架 (Orchestration)**: LangChain + LangGraph
- **API 框架 (API)**: FastAPI
- **UI 框架 (UI)**: Streamlit
- **文档处理 (Document Processing)**: pypdf, unstructured
- **测试 (Testing)**: pytest, pytest-cov, pytest-asyncio
- **配置管理 (Config)**: python-dotenv
- **HTTP 客户端 (HTTP)**: httpx, requests

**部署特点：**
- 🏠 **本地优先 (Local-First)**: 所有组件本地运行
- 🔒 **无外部依赖 (No External Dependencies)**: 不需要 OpenAI/Anthropic API
- 🚀 **快速部署 (Quick Deploy)**: Docker + 脚本自动化
- 🇨🇳 **中文优化 (Chinese Optimized)**: 专门优化的中文处理

---

## Development Workflow

### Branch Strategy

- **Feature Branches**: `claude/claude-md-*` for AI assistant work
- **Main Branch**: Protected, requires review
- **Development Branch**: `dev` for integration

### Commit Guidelines

1. **Commit Message Format**:
   ```
   <type>: <subject>

   <body>
   ```

   Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

2. **Examples**:
   - `feat: add FAISS vector store integration`
   - `fix: resolve embedding dimension mismatch`
   - `docs: update RAG pipeline documentation`
   - `refactor: simplify retrieval scoring logic`

3. **Commit Best Practices**:
   - Keep commits atomic and focused
   - Write descriptive commit messages
   - Reference issues when applicable

### Pull Request Process

1. Create feature branch from main
2. Implement changes with tests
3. Run full test suite
4. Update documentation
5. Push to remote: `git push -u origin <branch-name>`
6. Create PR with descriptive title and summary
7. Address review feedback

---

## Code Conventions

### Python Style

- **Style Guide**: PEP 8
- **Line Length**: 88 characters (Black formatter)
- **Imports**: Organize as stdlib, third-party, local
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public functions and classes

### Example Function Structure

```python
from typing import List, Dict, Optional
import numpy as np


def retrieve_documents(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict[str, any]]:
    """Retrieve relevant documents for a given query.

    Args:
        query: The search query string
        top_k: Number of top documents to retrieve
        similarity_threshold: Minimum similarity score

    Returns:
        List of document dictionaries with content and metadata

    Raises:
        ValueError: If query is empty or top_k is invalid

    Example:
        >>> docs = retrieve_documents("What is RAG?", top_k=3)
        >>> len(docs) <= 3
        True
    """
    if not query:
        raise ValueError("Query cannot be empty")

    # Implementation here
    pass
```

### Error Handling

- Use specific exceptions over generic ones
- Always log errors with context
- Provide meaningful error messages
- Handle edge cases explicitly

### Configuration Management

- Use YAML or JSON for configuration files
- Never hardcode API keys or secrets
- Use environment variables for sensitive data
- Provide `.env.example` template

---

## 关键组件说明 (Key Components)

### 1. 配置管理 (Configuration Management)

**位置**: `rag5/config/`

**功能**:
- 环境变量加载和验证
- 配置文件管理
- 默认值处理
- 类型验证

**关键文件**:
- `settings.py` - 主配置类，使用 Pydantic
- `loader.py` - 配置加载器
- `validator.py` - 配置验证器

**使用示例**:
```python
from rag5 import settings

# 访问配置
print(f"LLM 模型: {settings.llm_model}")
print(f"嵌入模型: {settings.embedding_model}")
print(f"Qdrant URL: {settings.qdrant_url}")
```

### 2. 核心代理系统 (Core Agent System)

**位置**: `rag5/core/agent/`

**功能**:
- RAG 代理实现 (基于 LangChain)
- 查询处理和优化
- 工具调用协调
- 对话历史管理

**关键文件**:
- `SimpleRAGAgent` - 主代理类
- `AgentInitializer` - 代理初始化
- `MessageProcessor` - 消息处理
- `ConversationHistory` - 对话历史

**使用示例**:
```python
from rag5 import ask

# 简单提问
answer = ask("什么是 RAG?")
print(answer)
```

### 3. 知识库管理 (Knowledge Base Management)

**位置**: `rag5/core/knowledge_base/`

**功能**:
- 知识库创建和删除
- 文档管理
- 元数据管理
- 多知识库支持

**关键操作**:
- 创建知识库
- 切换知识库
- 查询知识库信息
- 删除知识库

### 4. 数据摄取管道 (Ingestion Pipeline)

**位置**: `rag5/ingestion/`

**功能**:
- 文档加载 (PDF, TXT, Markdown 等)
- 智能分块 (中文优化)
- 向量化
- 批量处理

**子模块**:
- `loaders/` - 各种文档加载器
- `splitters/` - 文本分块器 (递归分块、字符分块)
- `vectorizers/` - 向量化器 (Ollama embeddings)
- `pipeline.py` - 完整的摄取流水线

**使用示例**:
```python
from rag5 import ingest_directory

# 摄取整个目录
result = ingest_directory("./docs")
print(f"处理了 {result.documents_loaded} 个文档")
```

### 5. 工具系统 (Tools System)

**位置**: `rag5/tools/`

**功能**:
- 向量搜索工具
- 嵌入生成工具
- 数据库管理工具
- 工具注册和发现

**子模块**:
- `search/` - 向量搜索实现
- `embeddings/` - 嵌入生成
- `database/` - Qdrant 数据库操作
- `registry.py` - 工具注册表

### 6. 接口层 (Interfaces)

**位置**: `rag5/interfaces/`

**API 接口** (`api/`):
- REST API 端点
- FastAPI 实现
- 异步处理
- 错误处理

**Web UI** (`ui/`):
- Streamlit 界面
- 交互式对话
- 知识库管理
- 实时日志查看

**启动方式**:
```bash
# API 接口
python scripts/run_api.py
# 或
rag5-api

# Web UI
python scripts/run_ui.py
# 或
rag5-ui
```

### 7. 工具函数 (Utilities)

**位置**: `rag5/utils/`

**功能**:
- 日志系统 (`logger.py`)
- 性能监控 (`monitoring.py`)
- 安全工具 (`security.py`)
- 通用辅助函数

**日志使用**:
```python
from rag5.utils import get_logger

logger = get_logger(__name__)
logger.info("开始处理文档")
```

---

## Testing Strategy

### Unit Tests

- Test individual functions in isolation
- Mock external dependencies (APIs, databases)
- Cover edge cases and error conditions
- Aim for 80%+ code coverage

### Integration Tests

- Test component interactions
- Use test databases/vector stores
- Validate end-to-end workflows
- Test with realistic data

### Test Organization

```python
# tests/unit/test_embeddings.py
import pytest
from src.embeddings import EmbeddingGenerator


class TestEmbeddingGenerator:
    @pytest.fixture
    def generator(self):
        return EmbeddingGenerator(model_name="test-model")

    def test_embed_single_text(self, generator):
        text = "Sample text"
        embedding = generator.embed(text)
        assert embedding.shape[0] == 384  # Expected dimension

    def test_embed_empty_text_raises_error(self, generator):
        with pytest.raises(ValueError):
            generator.embed("")
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_embeddings.py

# Run with verbose output
pytest -v
```

---

## 依赖和工具 (Dependencies & Tools)

### 核心依赖 (Core Dependencies)

**实际的 requirements.txt:**

```txt
# LangChain 框架和相关组件
langchain>=0.1.0,<0.3.0
langchain-community>=0.0.10,<0.3.0
langchain-ollama>=0.1.0,<0.2.0
langgraph>=0.0.20,<0.3.0

# 向量数据库
qdrant-client>=1.7.0,<2.0.0

# Web 框架
fastapi>=0.109.0,<0.111.0
uvicorn[standard]>=0.27.0,<0.30.0
streamlit>=1.30.0,<2.0.0

# 配置管理
python-dotenv>=1.0.0,<2.0.0

# 文档处理
pypdf>=3.17.0,<5.0.0
unstructured>=0.11.0,<0.15.0

# HTTP 客户端
httpx>=0.25.0,<0.28.0
requests>=2.31.0,<3.0.0

# 测试依赖（可选，用于开发）
pytest>=7.4.0,<8.0.0
pytest-cov>=4.1.0,<5.0.0
pytest-asyncio>=0.21.0,<0.24.0
```

### 外部服务依赖

**必需的外部服务:**

1. **Ollama** - 本地 LLM 服务
   ```bash
   # 安装 Ollama (参考官方文档)
   # 启动服务
   ollama serve

   # 拉取模型
   ollama pull qwen2.5:7b
   ollama pull bge-m3
   ```

2. **Qdrant** - 向量数据库
   ```bash
   # 使用 Docker 运行
   docker run -p 6333:6333 \
     -v $(pwd)/qdrant_storage:/qdrant/storage \
     qdrant/qdrant
   ```

### 常用命令 (Useful Commands)

```bash
# ====== 环境设置 ======
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 安装为可编辑包（推荐开发使用）
pip install -e .

# ====== 模型设置 ======
# 使用自动化脚本
./setup_models.sh

# 或手动拉取
ollama pull qwen2.5:7b
ollama pull bge-m3

# ====== 数据摄取 ======
# 摄取文档目录
rag5-ingest /path/to/documents
# 或
python scripts/ingest.py /path/to/documents

# ====== 运行服务 ======
# 启动 Web UI
rag5-ui
# 或
python scripts/run_ui.py

# 启动 API 服务
rag5-api
# 或
python scripts/run_api.py

# ====== 测试 ======
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=rag5 --cov-report=html

# 运行特定测试文件
pytest tests/test_core/test_agent.py

# 运行端到端测试
python scripts/test_e2e.py

# ====== 调试工具 ======
# 检索调试
python scripts/debug_retrieval.py "测试查询"

# 日志分析
python scripts/analyze_flow_logs.py

# 性能测试
python scripts/test_performance.py

# 验证安全性
python scripts/validate_security.py

# ====== 知识库管理 ======
# 知识库管理器
python scripts/kb_manager.py

# 知识库迁移
python scripts/migrate_kb.py

# ====== 代码质量 ======
# 格式化代码（如果使用 black）
# black rag5/ tests/

# 类型检查（如果使用 mypy）
# mypy rag5/
```

### 开发工具脚本

项目包含多个实用脚本：

| 脚本 | 功能 | 位置 |
|------|------|------|
| `ingest.py` | 文档摄取 | `scripts/` |
| `run_api.py` | 启动 API 服务器 | `scripts/` |
| `run_ui.py` | 启动 Web UI | `scripts/` |
| `kb_manager.py` | 知识库管理 | `scripts/` |
| `debug_retrieval.py` | 检索调试 | `scripts/` |
| `test_e2e.py` | 端到端测试 | `scripts/` |
| `test_performance.py` | 性能测试 | `scripts/` |
| `validate_security.py` | 安全验证 | `scripts/` |
| `validate_performance.py` | 性能验证 | `scripts/` |
| `analyze_flow_logs.py` | 日志分析 | `scripts/` |
| `compress_logs.py` | 日志压缩 | `scripts/` |
| `migrate_kb.py` | 知识库迁移 | `scripts/` |

### 环境变量配置

参考 `.env.example` 文件配置环境变量：

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
vim .env
```

**主要配置项：**
- `OLLAMA_BASE_URL` - Ollama 服务地址
- `LLM_MODEL` - LLM 模型名称
- `EMBEDDING_MODEL` - 嵌入模型名称
- `QDRANT_URL` - Qdrant 服务地址
- `COLLECTION_NAME` - 向量集合名称
- `CHUNK_SIZE` - 文本分块大小
- `CHUNK_OVERLAP` - 分块重叠大小

---

## Common Tasks

### Adding a New Document Source

1. Create preprocessor in `src/preprocessing/`
2. Implement document loader
3. Add chunking strategy
4. Generate embeddings
5. Store in vector database
6. Add tests
7. Update documentation

### Modifying Retrieval Logic

1. Locate retrieval module: `src/retrieval/`
2. Update similarity scoring or ranking
3. Test with various queries
4. Benchmark performance
5. Update configuration if needed

### Changing Embedding Model

1. Update configuration: `config/model_config.yaml`
2. Verify dimension compatibility
3. Re-generate embeddings for existing documents
4. Update vector store index
5. Test retrieval quality
6. Document migration process

### Debugging Poor Retrieval Results

1. Check embedding quality
2. Verify vector store indexing
3. Review similarity thresholds
4. Inspect query preprocessing
5. Test with known relevant documents
6. Consider re-ranking strategies

---

## Troubleshooting

### Common Issues

#### 1. Dimension Mismatch Errors

**Symptom**: Error when querying vector store about dimension mismatch

**Solution**:
- Verify embedding model dimensions match vector store configuration
- Check if model was changed without re-indexing
- Ensure query and document embeddings use same model

#### 2. Slow Retrieval Performance

**Symptom**: Queries take too long to return results

**Solution**:
- Check index type (consider HNSW or IVF for large datasets)
- Optimize top_k parameter
- Enable GPU acceleration if available
- Review vector store configuration

#### 3. Poor Retrieval Quality

**Symptom**: Retrieved documents not relevant to query

**Solution**:
- Review chunking strategy (chunk size, overlap)
- Test different embedding models
- Implement hybrid search
- Add metadata filtering
- Consider re-ranking

#### 4. Memory Issues

**Symptom**: Out of memory errors during embedding or retrieval

**Solution**:
- Implement batch processing
- Use memory-mapped index for FAISS
- Reduce batch size
- Consider distributed vector store

---

## Security Considerations

1. **API Keys**: Never commit API keys to git
2. **Environment Variables**: Use `.env` files (gitignored)
3. **Input Validation**: Sanitize all user inputs
4. **Rate Limiting**: Implement for API calls
5. **Access Control**: Restrict sensitive document access

---

## Performance Optimization

### Embedding Generation

- Batch process documents
- Use GPU acceleration
- Cache embeddings
- Implement async processing

### Vector Search

- Choose appropriate index type
- Tune search parameters
- Use approximate nearest neighbor (ANN)
- Consider quantization for large datasets

### Generation

- Implement streaming responses
- Cache frequent queries
- Optimize prompt length
- Use smaller models where appropriate

---

## AI Assistant Guidelines

### When Modifying Code

1. **Always read files before editing** - Understand context first
2. **Run tests after changes** - Ensure nothing breaks
3. **Update documentation** - Keep docs in sync with code
4. **Follow existing patterns** - Maintain consistency
5. **Type hints required** - Add type annotations
6. **Write docstrings** - Document public interfaces

### When Adding Features

1. **Check existing implementation** - Avoid duplication
2. **Start with tests** - TDD approach when appropriate
3. **Update CLAUDE.md** - Document new patterns
4. **Consider performance** - Profile if needed
5. **Add configuration** - Make features configurable

### When Debugging

1. **Reproduce the issue** - Create minimal test case
2. **Add logging** - Use appropriate log levels
3. **Check recent changes** - Review git history
4. **Verify assumptions** - Use assertions and tests
5. **Document the fix** - Explain root cause

### Code Review Checklist

- [ ] Code follows PEP 8 style
- [ ] Type hints present
- [ ] Docstrings complete
- [ ] Tests added/updated
- [ ] Error handling appropriate
- [ ] No hardcoded values
- [ ] Performance considered
- [ ] Documentation updated
- [ ] Commit messages clear
- [ ] No commented-out code

---

## Git Workflow for AI Assistants

### Committing Changes

```bash
# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "$(cat <<'EOF'
feat: add semantic chunking strategy

- Implement sentence-based chunking
- Add overlap parameter configuration
- Include metadata preservation
- Add unit tests for chunking logic
EOF
)"
```

### Pushing Changes

```bash
# Push to feature branch with retry logic
git push -u origin claude/claude-md-mhy48gl18qidu2w9-01RjkXCxeamU1fV2631u67h7

# If network failure, retry with exponential backoff
# (automated by system)
```

### Creating Pull Requests

1. Ensure all tests pass
2. Run linting and type checking
3. Update CHANGELOG if exists
4. Write comprehensive PR description
5. Include testing instructions

---

## Resources

### RAG Concepts

- **Chunking Strategies**: Fixed size, semantic, sentence-based
- **Embedding Models**: sentence-transformers, OpenAI, Cohere
- **Vector Stores**: FAISS (local), Pinecone (cloud), Chroma
- **Retrieval Methods**: Dense, sparse, hybrid
- **Re-ranking**: Cross-encoders, reciprocal rank fusion

### Useful Links

- [LangChain Documentation](https://python.langchain.com/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Best Practices](https://www.anthropic.com/index/contextual-retrieval)

---

## Changelog

### 2025-11-14 - 重大更新：反映实际项目状态 / Major Update: Actual Project State

**重要更新 - 从 main 分支同步代码**

- ✅ **项目状态更新**: 从"初始阶段"更新为"功能完整的 RAG 系统 v2.0.0"
- ✅ **实际架构文档**: 更新项目结构以反映真实的 `rag5/` 代码库
- ✅ **技术栈更新**:
  - LLM: Ollama (qwen2.5:7b)
  - Embeddings: Ollama (bge-m3)
  - Vector DB: Qdrant (替代 FAISS)
  - Framework: LangChain + LangGraph
- ✅ **关键组件说明**: 详细记录了 7 个主要模块
  - 配置管理 (config)
  - 核心代理系统 (core/agent)
  - 知识库管理 (core/knowledge_base)
  - 数据摄取管道 (ingestion)
  - 工具系统 (tools)
  - 接口层 (interfaces)
  - 工具函数 (utils)
- ✅ **依赖更新**: 使用实际的 requirements.txt 内容
- ✅ **开发工具**: 记录了 12+ 个实用脚本
- ✅ **环境配置**: 添加了外部服务依赖说明 (Ollama, Qdrant)
- 📈 **版本**: 1.2.0 → 2.0.0 (反映项目实际版本)

### 2025-11-14 - 添加语言规范要求 / Language Requirements Added

- 新增"Language Requirements"章节，明确中文使用规范
- 要求所有对话、注释、文档使用中文
- 提供中文注释和文档字符串的示例代码
- 添加配置文件的中文注释示例
- 更新版本到 1.2.0

### 2025-11-14 - Repository State Update

- Updated branch name to current feature branch
- Clarified current repository state (only git + CLAUDE.md exist)
- Added explicit list of what exists vs. what needs to be created
- Updated last modified date and version

### 2025-11-13 - Initial Creation

- Created CLAUDE.md with comprehensive guidelines
- Established project structure and conventions
- Documented expected architecture and workflows
- Added troubleshooting and best practices

---

## Contact & Support

For questions or issues:
1. Check this CLAUDE.md first
2. Review existing documentation
3. Search git history for context
4. Consult relevant API documentation

---

**Last Updated**: 2025-11-14
**Version**: 2.0.0
**Maintained By**: AI Assistants working on rag5-simplified-001
