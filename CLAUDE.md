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

**Current State**: Initial setup phase - Repository scaffolding only
**Branch**: `claude/claude-md-mhy48gl18qidu2w9-01RjkXCxeamU1fV2631u67h7`

**What Currently Exists:**
- `.git/` - Git repository
- `CLAUDE.md` - This guidance document

**What Needs to Be Created:**
- All source code directories and files
- Configuration files (requirements.txt, .gitignore, etc.)
- Test suite
- Documentation files (README.md, etc.)

This repository is in its initial stages. The following sections outline the expected structure and conventions to follow as the project is built out.

---

## Expected Architecture

### Project Structure

```
rag5-simplified-001/
├── src/                      # Source code
│   ├── embeddings/          # Embedding generation modules
│   ├── retrieval/           # Document retrieval logic
│   ├── generation/          # LLM generation interface
│   ├── vectorstore/         # Vector database integration
│   ├── preprocessing/       # Document preprocessing utilities
│   └── main.py             # Main application entry point
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data and fixtures
├── data/                    # Data directory
│   ├── documents/          # Source documents
│   ├── processed/          # Preprocessed documents
│   └── vectors/            # Vector embeddings storage
├── config/                  # Configuration files
│   ├── model_config.yaml   # Model configurations
│   └── retrieval_config.yaml # Retrieval parameters
├── notebooks/               # Jupyter notebooks for experiments
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── setup.py                # Package setup
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation
├── CLAUDE.md               # This file
└── LICENSE                 # License file
```

### Technology Stack (Expected)

- **Language**: Python 3.9+
- **Embeddings**: sentence-transformers, OpenAI embeddings, or similar
- **Vector Store**: FAISS, Pinecone, Chroma, or Weaviate
- **LLM Interface**: OpenAI API, Anthropic API, or local models
- **Framework**: LangChain or custom implementation
- **Testing**: pytest
- **Documentation**: Sphinx or MkDocs

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

## Key Components

### 1. Embedding Generation

**Purpose**: Convert text to vector embeddings

**Key Considerations**:
- Model selection (dimension, performance trade-off)
- Batch processing for efficiency
- Caching strategies
- Normalization

### 2. Vector Store

**Purpose**: Store and retrieve embeddings efficiently

**Key Considerations**:
- Index type (flat, IVF, HNSW)
- Distance metric (cosine, euclidean, dot product)
- Scalability
- Persistence

### 3. Retrieval Logic

**Purpose**: Find most relevant documents for queries

**Key Considerations**:
- Similarity scoring
- Re-ranking strategies
- Filtering and metadata
- Hybrid search (dense + sparse)

### 4. Generation

**Purpose**: Generate responses using retrieved context

**Key Considerations**:
- Prompt engineering
- Context window management
- Token limits
- Response quality

### 5. Preprocessing

**Purpose**: Prepare documents for embedding

**Key Considerations**:
- Chunking strategies
- Overlap handling
- Metadata extraction
- Format normalization

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

## Dependencies & Tools

### Core Dependencies (Expected)

```txt
# requirements.txt
numpy>=1.21.0
pandas>=1.3.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.0  # or faiss-gpu
langchain>=0.1.0
openai>=1.0.0
anthropic>=0.18.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
```

### Development Dependencies

```txt
# requirements-dev.txt
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
ipython>=8.0.0
jupyter>=1.0.0
```

### Useful Commands

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

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
**Version**: 1.2.0
**Maintained By**: AI Assistants working on rag5-simplified-001
