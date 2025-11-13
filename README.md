# RAG5 Simplified System

一个本地部署的检索增强生成（RAG）系统，具有智能查询优化能力和模块化架构。

A locally-deployed Retrieval-Augmented Generation (RAG) system with intelligent query optimization capabilities and modular architecture.

## 特性 Features

- **本地优先 Local-First**: 所有组件本地运行，无需外部 API 依赖
- **LLM 驱动的查询优化 LLM-Driven Query Optimization**: 自动增强查询以获得更好的检索效果
- **向量搜索 Vector Search**: 使用 Qdrant 进行快速准确的文档检索
- **多种接口 Multiple Interfaces**: REST API 和 Web UI
- **模块化架构 Modular Architecture**: 清晰的代码组织，易于扩展和维护
- **简单配置 Easy Setup**: 合理的默认配置，快速上手
- **中文优化 Chinese Optimization**: 专门优化的中文文本处理和分块策略
- **检索优化 Retrieval Optimization**: 自适应搜索、混合搜索和查询扩展
- **完善的调试工具 Comprehensive Debugging Tools**: 数据库诊断、日志系统和调试脚本
- **详细的日志记录 Detailed Logging**: 完整追踪从摄取到检索的全流程

## 技术栈 Tech Stack

- **LLM & Embeddings**: Ollama (qwen2.5:7b, bge-m3)
- **Vector Database**: Qdrant
- **Orchestration**: LangChain + LangGraph
- **API**: FastAPI
- **UI**: Streamlit
- **Language**: Python 3.9+

## 快速开始 Quick Start

### 1. 安装依赖 Install Dependencies

```bash
# 安装 Python 包
pip install -r requirements.txt

# 或者安装为可编辑包（推荐用于开发）
pip install -e .
```

### 2. 启动服务 Start Services

```bash
# 启动 Ollama
ollama serve

# 启动 Qdrant (使用 Docker)
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 3. 拉取模型 Pull Models

**方式 A: 使用安装脚本（推荐）**
```bash
./scripts/setup_models.sh
```

**方式 B: 手动安装**
```bash
ollama pull qwen2.5:7b
ollama pull bge-m3
```

### 4. 配置环境 Configure Environment

```bash
cp .env.example .env
# 根据需要编辑 .env 文件自定义配置
```

### 5. 摄取文档 Ingest Documents

```bash
# 使用脚本入口点（如果已安装包）
rag5-ingest /path/to/your/documents

# 或直接运行脚本
python scripts/ingest.py /path/to/your/documents
```

### 6. 运行应用 Run the Application

**方式 A: Web UI (Streamlit)**
```bash
# 使用脚本入口点（如果已安装包）
rag5-ui

# 或直接运行脚本
python scripts/run_ui.py
```

**方式 B: REST API (FastAPI)**
```bash
# 使用脚本入口点（如果已安装包）
rag5-api

# 或直接运行脚本
python scripts/run_api.py
```

## 项目结构 Project Structure

```
rag5-simplified/
├── README.md                      # 项目主文档
├── requirements.txt               # Python 依赖列表
├── setup.py                       # 包安装配置
├── .env.example                   # 环境变量模板
│
├── rag5/                          # 主包目录
│   ├── __init__.py               # 包初始化，导出主要接口
│   │
│   ├── config/                    # 配置模块
│   │   ├── __init__.py           # 导出配置接口
│   │   ├── README.md             # 配置模块说明
│   │   ├── loader.py             # 环境变量加载
│   │   ├── validator.py          # 配置验证
│   │   ├── defaults.py           # 默认值定义
│   │   └── settings.py           # 配置访问接口
│   │
│   ├── core/                      # 核心模块
│   │   ├── __init__.py           # 导出核心接口
│   │   ├── README.md             # 核心模块说明
│   │   ├── agent/                # 代理子模块
│   │   │   ├── agent.py          # 主代理类
│   │   │   ├── initializer.py   # 代理初始化
│   │   │   ├── history.py        # 对话历史管理
│   │   │   ├── messages.py       # 消息处理
│   │   │   └── errors.py         # 错误处理和重试
│   │   └── prompts/              # 提示词子模块
│   │       ├── system.py         # 系统提示词
│   │       └── tools.py          # 工具描述提示词
│   │
│   ├── tools/                     # 工具模块
│   │   ├── __init__.py           # 导出工具接口
│   │   ├── README.md             # 工具模块说明
│   │   ├── registry.py           # 工具注册器
│   │   ├── base.py               # 工具基类
│   │   ├── search/               # 搜索工具子模块
│   │   ├── embeddings/           # 嵌入工具子模块
│   │   └── vectordb/             # 向量数据库子模块
│   │
│   ├── ingestion/                 # 数据摄取模块
│   │   ├── __init__.py           # 导出摄取接口
│   │   ├── README.md             # 摄取模块说明
│   │   ├── pipeline.py           # 摄取流程编排
│   │   ├── loaders/              # 文档加载器子模块
│   │   ├── splitters/            # 文档分块器子模块
│   │   └── vectorizers/          # 向量化子模块
│   │
│   ├── interfaces/                # 接口模块
│   │   ├── __init__.py           # 导出接口
│   │   ├── README.md             # 接口模块说明
│   │   ├── api/                  # REST API 子模块
│   │   └── ui/                   # Web UI 子模块
│   │
│   └── utils/                     # 工具函数模块
│       └── __init__.py           # 导出工具函数
│
├── scripts/                       # 脚本目录
│   ├── README.md                 # 脚本说明
│   ├── ingest.py                 # 数据摄取脚本
│   ├── run_api.py                # API 启动脚本
│   ├── run_ui.py                 # UI 启动脚本
│   └── setup_models.sh           # 模型安装脚本
│
├── tests/                         # 测试目录
│   ├── conftest.py               # pytest 配置
│   ├── test_config/              # 配置模块测试
│   ├── test_core/                # 核心模块测试
│   ├── test_tools/               # 工具模块测试
│   ├── test_ingestion/           # 摄取模块测试
│   ├── test_interfaces/          # 接口模块测试
│   └── test_data/                # 测试数据
│
└── docs/                          # 文档目录（可选）
    ├── migration_guide.md        # 迁移指南
    ├── api_reference.md          # API 参考
    └── development.md            # 开发指南
```

## 配置 Configuration

所有配置通过 `.env` 文件中的环境变量管理：

All configuration is managed through environment variables in the `.env` file:

### 基础配置 Basic Configuration

| 变量 Variable | 默认值 Default | 说明 Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务 URL / Ollama service URL |
| `LLM_MODEL` | `qwen2.5:7b` | LLM 模型名称 / LLM model name |
| `EMBED_MODEL` | `bge-m3` | 嵌入模型名称 / Embedding model name |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant 服务 URL / Qdrant service URL |
| `COLLECTION_NAME` | `knowledge_base` | 向量集合名称 / Vector collection name |

### 检索配置 Retrieval Configuration

| 变量 Variable | 默认值 Default | 说明 Description |
|----------|---------|-------------|
| `TOP_K` | `5` | 搜索结果数量 / Number of search results |
| `SIMILARITY_THRESHOLD` | `0.3` | 最小相似度分数 / Minimum similarity score |
| `ENABLE_HYBRID_SEARCH` | `false` | 启用混合搜索（向量+关键词）/ Enable hybrid search |
| `VECTOR_SEARCH_WEIGHT` | `0.7` | 向量搜索权重 / Vector search weight |
| `KEYWORD_SEARCH_WEIGHT` | `0.3` | 关键词搜索权重 / Keyword search weight |
| `MIN_SIMILARITY_THRESHOLD` | `0.1` | 自适应搜索最小阈值 / Adaptive search min threshold |
| `TARGET_RESULTS` | `3` | 自适应搜索目标结果数 / Target results for adaptive search |

### 分块配置 Chunking Configuration

| 变量 Variable | 默认值 Default | 说明 Description |
|----------|---------|-------------|
| `CHUNK_SIZE` | `500` | 文档分块大小 / Document chunk size |
| `CHUNK_OVERLAP` | `50` | 分块重叠大小 / Chunk overlap size |
| `RESPECT_SENTENCE_BOUNDARY` | `true` | 尊重句子边界 / Respect sentence boundaries |
| `ENABLE_CHINESE_SPLITTER` | `true` | 启用中文优化分块 / Enable Chinese text splitter |

### 日志配置 Logging Configuration

| 变量 Variable | 默认值 Default | 说明 Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | 日志级别 / Log level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | `logs/rag_app.log` | 日志文件路径 / Log file path |
| `ENABLE_QUERY_LOGGING` | `true` | 启用查询日志 / Enable query logging |
| `ENABLE_INGESTION_LOGGING` | `true` | 启用摄取日志 / Enable ingestion logging |
| `ENABLE_CONSOLE_LOGGING` | `true` | 启用控制台日志 / Enable console logging |

详细配置说明请参考 [配置模块文档](rag5/config/README.md)。

For detailed configuration instructions, see [Config Module Documentation](rag5/config/README.md).

### 增强日志配置 Enhanced Logging Configuration

RAG5 提供增强的日志系统，可以深入了解 LLM 交互、代理推理和对话上下文管理：

RAG5 provides an enhanced logging system for deep visibility into LLM interactions, agent reasoning, and conversation context:

| 变量 Variable | 默认值 Default | 说明 Description |
|----------|---------|-------------|
| `RAG5_ENABLE_LLM_LOGGING` | `true` | 启用 LLM 请求/响应日志 / Enable LLM request/response logging |
| `RAG5_ENABLE_REFLECTION_LOGGING` | `true` | 启用代理推理日志 / Enable agent reflection logging |
| `RAG5_ENABLE_CONTEXT_LOGGING` | `true` | 启用对话上下文日志 / Enable conversation context logging |
| `RAG5_LLM_LOG_FILE` | `logs/llm_interactions.log` | LLM 交互日志文件 / LLM interaction log file |
| `RAG5_REFLECTION_LOG_FILE` | `logs/agent_reflections.log` | 代理推理日志文件 / Agent reflection log file |
| `RAG5_CONTEXT_LOG_FILE` | `logs/conversation_context.log` | 对话上下文日志文件 / Conversation context log file |
| `RAG5_LOG_PROMPTS` | `true` | 记录完整提示词 / Log complete prompts |
| `RAG5_LOG_RESPONSES` | `true` | 记录完整响应 / Log complete responses |
| `RAG5_REDACT_SENSITIVE` | `false` | 编辑敏感数据 / Redact sensitive data |
| `RAG5_ASYNC_LOGGING` | `true` | 使用异步日志写入 / Use async log writing |
| `RAG5_MAX_LOG_ENTRY_SIZE` | `102400` | 最大日志条目大小（字节）/ Max log entry size (bytes) |

**快速开始 Quick Start:**

```bash
# 启用所有增强日志功能
RAG5_ENABLE_LLM_LOGGING=true
RAG5_ENABLE_REFLECTION_LOGGING=true
RAG5_ENABLE_CONTEXT_LOGGING=true

# 查看实时日志
tail -f logs/llm_interactions.log
tail -f logs/agent_reflections.log
```

**日志分析 Log Analysis:**

```bash
# 使用 Python 脚本分析
python examples/analyze_llm_logs.py
python examples/analyze_reflections.py

# 使用 jq 解析 JSON 日志
cat logs/llm_interactions.log | jq '.data.duration_seconds'
cat logs/agent_reflections.log | jq 'select(.data.reflection_type=="query_analysis")'
```

**隐私保护 Privacy Protection:**

```bash
# 在生产环境中启用数据编辑
RAG5_REDACT_SENSITIVE=true
RAG5_LOG_PROMPTS=false
RAG5_LOG_RESPONSES=false
```

详细说明请参考：
- [增强日志指南 Enhanced Logging Guide](docs/enhanced_logging.md) - 完整的日志系统文档
- [日志分析示例 Log Analysis Examples](examples/README.md) - 分析脚本和 jq 示例

### 统一流程日志 Unified Flow Logging

RAG5 提供统一流程日志系统，将所有查询处理事件记录到单个、按时间顺序排列的日志文件中：

RAG5 provides a unified flow logging system that records all query processing events in a single, chronologically ordered log file:

**主要优势 Key Benefits:**
- **单一数据源 Single Source of Truth**: 所有事件按时间顺序记录在一个文件中 / All events in one chronologically ordered file
- **易于阅读 Human-Readable**: 专为人类可读性设计的格式 / Format designed for human readability
- **完整追踪 Complete Tracking**: 从查询到答案的完整流程 / Complete flow from query to answer
- **性能指标 Performance Metrics**: 每个操作的内置计时信息 / Built-in timing for every operation
- **会话关联 Session Correlation**: 唯一会话 ID 便于追踪 / Unique session IDs for easy tracing

**快速开始 Quick Start:**

```bash
# 启用统一流程日志（默认已启用）
RAG5_ENABLE_FLOW_LOGGING=true
RAG5_FLOW_LOG_FILE=logs/unified_flow.log
RAG5_FLOW_DETAIL_LEVEL=normal  # minimal, normal, or verbose

# 查看日志
tail -f logs/unified_flow.log

# 分析日志
python scripts/analyze_flow_logs.py --stats
python scripts/analyze_flow_logs.py --session <session-id>
python scripts/analyze_flow_logs.py --errors
```

**日志示例 Log Example:**

```
================================================================================
[2025-11-10 14:30:45.123] QUERY_START (Session: abc-123-def) [+0.000s]
--------------------------------------------------------------------------------
Query: 李小勇和人合作入股了什么公司？
================================================================================

================================================================================
[2025-11-10 14:30:45.567] TOOL_EXECUTION (Session: abc-123-def) [+0.444s]
--------------------------------------------------------------------------------
Tool: knowledge_base_search
Status: SUCCESS
Duration: 0.222s

Output:
  Found 3 relevant documents:
  1. [Score: 0.89] 李小勇与张三合作入股ABC科技有限公司...
================================================================================

================================================================================
[2025-11-10 14:30:47.890] QUERY_COMPLETE (Session: abc-123-def) [+2.767s]
--------------------------------------------------------------------------------
Status: SUCCESS
Total Duration: 2.767s

Final Answer:
  根据搜索结果，李小勇与张三合作入股了ABC科技有限公司...
================================================================================
```

**配置选项 Configuration:**

| 变量 Variable | 默认值 Default | 说明 Description |
|----------|---------|-------------|
| `RAG5_ENABLE_FLOW_LOGGING` | `true` | 启用统一流程日志 / Enable unified flow logging |
| `RAG5_FLOW_LOG_FILE` | `logs/unified_flow.log` | 日志文件路径 / Log file path |
| `RAG5_FLOW_DETAIL_LEVEL` | `normal` | 详细级别 / Detail level (minimal/normal/verbose) |
| `RAG5_FLOW_MAX_CONTENT_LENGTH` | `500` | 内容截断长度 / Content truncation length |
| `RAG5_FLOW_ASYNC_LOGGING` | `true` | 异步写入 / Async writing |
| `RAG5_KEEP_SEPARATE_LOGS` | `true` | 保留独立日志文件 / Keep separate log files |

**分析工具 Analysis Tools:**

```python
from rag5.utils import FlowLogAnalyzer

# 初始化分析器
analyzer = FlowLogAnalyzer("logs/unified_flow.log")

# 按会话过滤
session_entries = analyzer.filter_by_session("abc-123-def")

# 获取性能统计
stats = analyzer.get_timing_stats()
print(f"平均查询时间: {stats['query_complete']['avg']:.2f}s")

# 查找错误
errors = analyzer.find_errors()

# 查找慢操作
slow_ops = analyzer.find_slow_operations(threshold_seconds=5.0)

# 导出为 JSON/CSV
analyzer.export_to_json("analysis.json")
analyzer.export_to_csv("analysis.csv")
```

详细文档：
- [统一流程日志指南 Unified Flow Logging Guide](docs/unified_flow_logging.md) - 完整文档和最佳实践
- [FlowLogAnalyzer API](docs/flow_log_analyzer.md) - 分析工具 API 参考
- [CLI 使用指南 CLI Usage](scripts/CLI_USAGE.md) - 命令行工具使用

## 使用方法 Usage

### 作为 Python 包使用 Using as a Python Package

安装包后，可以在代码中直接导入使用：

After installing the package, you can import and use it in your code:

```python
from rag5 import settings, SimpleRAGAgent, ask

# 检查配置
print(f"LLM Model: {settings.llm_model}")
print(f"Embed Model: {settings.embed_model}")

# 使用代理
agent = SimpleRAGAgent()
response = agent.chat("什么是机器学习？")
print(response)

# 或使用便捷函数
response = ask("什么是机器学习？")
print(response)
```

### 数据摄取 Data Ingestion

```python
from rag5.ingestion import ingest_directory

# 摄取目录中的所有文档
result = ingest_directory("./docs")
print(f"成功处理 {result.documents_loaded} 个文档")
print(f"创建 {result.chunks_created} 个文本块")
print(f"上传 {result.vectors_uploaded} 个向量")
```

### 脚本入口点 Script Entry Points

安装包后，以下命令行工具将可用：

After installing the package, the following command-line tools are available:

- `rag5-ingest <directory>` - 摄取文档到知识库 / Ingest documents into knowledge base
- `rag5-api` - 启动 REST API 服务 / Start REST API service
- `rag5-ui` - 启动 Web UI 界面 / Start Web UI interface

### API 端点 API Endpoints

REST API 提供以下端点：

The REST API provides the following endpoints:

- `POST /chat` - 发送查询并获取回答 / Send query and get answer
- `GET /health` - 健康检查 / Health check

示例 Example:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是机器学习？", "history": []}'
```

## 调试和诊断 Debugging and Diagnostics

RAG5 提供完善的调试工具帮助您快速定位和解决问题：

RAG5 provides comprehensive debugging tools to help you quickly identify and resolve issues:

### 增强日志系统 Enhanced Logging System

RAG5 的增强日志系统提供对 LLM 交互和代理推理的深入可见性：

RAG5's enhanced logging system provides deep visibility into LLM interactions and agent reasoning:

```bash
# 启用增强日志
RAG5_ENABLE_LLM_LOGGING=true
RAG5_ENABLE_REFLECTION_LOGGING=true
RAG5_ENABLE_CONTEXT_LOGGING=true

# 查看 LLM 交互
tail -f logs/llm_interactions.log

# 分析日志
python examples/analyze_llm_logs.py
python examples/analyze_reflections.py

# 使用 jq 查询
cat logs/llm_interactions.log | jq 'select(.data.duration_seconds > 5)'
```

**日志内容 Log Contents:**
- **LLM 交互日志**: 所有发送到 LLM 的提示词和接收的响应，包含时间和 token 统计
- **代理推理日志**: 代理的决策过程、工具选择和查询重构
- **对话上下文日志**: 对话历史的演变和上下文管理

详细文档：[增强日志指南 Enhanced Logging Guide](docs/enhanced_logging.md)

### 快速诊断 Quick Diagnostics

```bash
# 运行完整系统诊断
python scripts/debug_retrieval.py

# 使用自定义查询测试
python scripts/debug_retrieval.py --query "你的查询"

# 搜索特定关键词
python scripts/debug_retrieval.py --keyword "关键词"
```

### 数据库诊断工具 Database Diagnostic Tools

```bash
# 检查集合状态
python -m rag5.tools.diagnostics.db_check --collection knowledge_base

# 搜索关键词
python -m rag5.tools.diagnostics.db_check --search "关键词"

# 验证嵌入模型
python -m rag5.tools.diagnostics.db_check --verify-embeddings
```

### 索引管理工具 Index Management Tools

```bash
# 重新索引文档
python -m rag5.tools.index_manager reindex --directory ./docs --force

# 清空集合
python -m rag5.tools.index_manager clear --collection knowledge_base

# 验证索引
python -m rag5.tools.index_manager verify --collection knowledge_base
```

### 详细文档 Detailed Documentation

- [调试指南 Debugging Guide](docs/debugging_guide.md) - 完整的调试方法和故障排除
- [调试脚本文档 Debug Script Documentation](scripts/DEBUG_RETRIEVAL_README.md) - 调试脚本详细使用说明
- [数据库诊断工具 Database Diagnostics](rag5/tools/diagnostics/README.md) - 数据库检查和验证
- [索引管理工具 Index Manager](rag5/tools/index_manager/README.md) - 索引管理和维护

## 检索优化 Retrieval Optimization

RAG5 提供多种检索优化策略以提高准确性和召回率：

RAG5 provides multiple retrieval optimization strategies to improve accuracy and recall:

### 自适应搜索 Adaptive Search

自动调整相似度阈值以获得足够的结果：

```python
from rag5.tools.search import AdaptiveSearchTool

results = adaptive_tool.search_with_fallback(
    query="你的查询",
    initial_threshold=0.5,
    min_threshold=0.1,
    target_results=3
)
```

### 混合搜索 Hybrid Search

结合向量搜索和关键词搜索：

```python
from rag5.tools.search import HybridSearchTool

results = hybrid_tool.hybrid_search(
    query="你的查询",
    vector_weight=0.7,
    keyword_weight=0.3
)
```

### 查询扩展 Query Expansion

通过添加同义词扩展查询：

```python
from rag5.tools.search import QueryExpander

expander = QueryExpander()
expanded_query = expander.expand_query("原始查询")
```

详细说明：[检索优化指南 Retrieval Optimization Guide](docs/retrieval_optimization.md)

## 中文文本处理 Chinese Text Processing

RAG5 专门优化了中文文本处理流程：

RAG5 has specially optimized Chinese text processing:

### 中文分块器 Chinese Text Splitter

```python
from rag5.ingestion.splitters import ChineseTextSplitter

splitter = ChineseTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    respect_sentence_boundary=True
)
chunks = splitter.split_text("中文文本")
```

### 中文文本诊断 Chinese Text Diagnostics

```python
from rag5.utils import ChineseTextDiagnostic

diagnostic = ChineseTextDiagnostic()
result = diagnostic.analyze_text("中文文本")
print(f"中文占比: {result['chinese_ratio']:.1%}")
```

### 自动检测 Auto Detection

摄取流程自动检测中文并选择合适的分块器：

```bash
# 在 .env 中配置
ENABLE_CHINESE_SPLITTER=true
RESPECT_SENTENCE_BOUNDARY=true
```

详细说明：[中文文本处理指南 Chinese Text Processing Guide](docs/chinese_text_processing.md)

## 模块文档 Module Documentation

每个模块都有详细的中文文档说明：

Each module has detailed documentation in Chinese:

- [配置模块 Config Module](rag5/config/README.md) - 配置管理和验证
- [核心模块 Core Module](rag5/core/README.md) - 代理和提示词管理
- [工具模块 Tools Module](rag5/tools/README.md) - 搜索、嵌入和向量数据库工具
- [摄取模块 Ingestion Module](rag5/ingestion/README.md) - 文档加载、分块和向量化
- [接口模块 Interfaces Module](rag5/interfaces/README.md) - API 和 UI 接口
- [脚本说明 Scripts Documentation](scripts/README.md) - 命令行脚本使用说明

### 日志和分析文档 Logging and Analysis Documentation

- [增强日志指南 Enhanced Logging Guide](docs/enhanced_logging.md) - LLM 交互和代理推理日志
- [日志分析示例 Log Analysis Examples](examples/README.md) - 分析脚本和 jq 查询示例

## 开发 Development

### 安装开发依赖 Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### 运行测试 Run Tests

```bash
# 运行所有测试
pytest

# 运行特定模块的测试
pytest tests/test_config/
pytest tests/test_core/
pytest tests/test_tools/

# 查看测试覆盖率
pytest --cov=rag5 --cov-report=html
```

### 代码风格 Code Style

```bash
# 格式化代码
black rag5/

# 检查代码风格
flake8 rag5/

# 类型检查
mypy rag5/
```

## 扩展系统 Extending the System

### 添加新工具 Adding New Tools

```python
from langchain.tools import tool
from rag5.tools import tool_registry

@tool
def my_custom_tool(query: str) -> str:
    """自定义工具的描述"""
    # 实现工具逻辑
    return result

# 注册工具
tool_registry.register(my_custom_tool)
```

### 添加新的文档加载器 Adding New Document Loaders

```python
from rag5.ingestion.loaders import BaseLoader
from langchain.schema import Document

class CustomLoader(BaseLoader):
    """自定义文档加载器"""
    
    def load(self, file_path: str) -> List[Document]:
        """加载文档"""
        # 实现加载逻辑
        return documents
    
    def supports(self, file_path: str) -> bool:
        """检查是否支持该文件类型"""
        return file_path.endswith('.custom')
```

详细的开发指南请参考 [开发文档](docs/development.md)（如果可用）。

For detailed development guide, see [Development Documentation](docs/development.md) (if available).

## 常见问题 FAQ

### Q1: 查询返回"没有找到相关信息"怎么办？

**A:** 这是最常见的问题，通常有以下几种解决方案：

1. **降低相似度阈值**
   ```bash
   # 在 .env 中设置
   SIMILARITY_THRESHOLD=0.2  # 从默认的 0.3 降低
   ```

2. **启用混合搜索**
   ```bash
   ENABLE_HYBRID_SEARCH=true
   ```

3. **使用调试脚本诊断**
   ```bash
   python scripts/debug_retrieval.py --query "你的查询"
   ```

4. **重新索引文档**
   ```bash
   python -m rag5.tools.index_manager reindex --directory ./docs --force
   ```

详细排查步骤请参考 [调试指南](docs/debugging_guide.md)。

### Q2: 如何优化中文检索效果？

**A:** RAG5 提供了专门的中文优化功能：

1. **启用中文分块器**
   ```bash
   # .env
   ENABLE_CHINESE_SPLITTER=true
   RESPECT_SENTENCE_BOUNDARY=true
   ```

2. **调整分块参数**
   ```bash
   CHUNK_SIZE=500          # 适合中文的分块大小
   CHUNK_OVERLAP=50        # 重叠大小
   ```

3. **使用混合搜索**
   ```bash
   ENABLE_HYBRID_SEARCH=true
   VECTOR_SEARCH_WEIGHT=0.7
   KEYWORD_SEARCH_WEIGHT=0.3
   ```

详细说明请参考 [中文文本处理指南](docs/chinese_text_processing.md)。

### Q3: 如何检查文档是否已正确索引？

**A:** 使用数据库诊断工具：

```bash
# 查看集合统计
python -m rag5.tools.diagnostics.db_check --collection knowledge_base

# 搜索特定关键词
python -m rag5.tools.diagnostics.db_check --search "关键词"

# 获取样本数据
python -m rag5.tools.diagnostics.db_check --samples 10
```

### Q4: 服务启动失败怎么办？

**A:** 检查以下几点：

1. **确认服务正在运行**
   ```bash
   # 检查 Qdrant
   curl http://localhost:6333/collections
   
   # 检查 Ollama
   curl http://localhost:11434/api/tags
   ```

2. **检查模型是否已安装**
   ```bash
   ollama list
   # 如果没有，运行：
   ./scripts/setup_models.sh
   ```

3. **查看日志**
   ```bash
   tail -f logs/rag_app.log
   ```

### Q5: 如何提高检索速度？

**A:** 可以尝试以下优化：

1. **减少返回结果数**
   ```bash
   TOP_K=3  # 从 5 减少到 3
   ```

2. **提高相似度阈值**
   ```bash
   SIMILARITY_THRESHOLD=0.5  # 过滤更多结果
   ```

3. **增大分块大小**
   ```bash
   CHUNK_SIZE=800  # 减少总分块数
   ```

4. **禁用不必要的功能**
   ```bash
   ENABLE_HYBRID_SEARCH=false  # 如果不需要
   ```

### Q6: 如何查看详细的调试信息？

**A:** 启用 DEBUG 日志级别：

```bash
# .env
LOG_LEVEL=DEBUG
ENABLE_QUERY_LOGGING=true
ENABLE_INGESTION_LOGGING=true
ENABLE_CONSOLE_LOGGING=true
```

然后查看日志：
```bash
tail -f logs/rag_app.log
```

### Q7: 如何备份和恢复数据？

**A:** 备份 Qdrant 数据和配置：

```bash
# 备份
cp -r qdrant_storage backups/qdrant_$(date +%Y%m%d)
cp .env backups/env_$(date +%Y%m%d)

# 恢复
cp -r backups/qdrant_20240115 qdrant_storage
cp backups/env_20240115 .env
```

### Q8: 支持哪些文档格式？

**A:** 当前支持：
- 文本文件 (.txt)
- Markdown (.md)
- PDF (.pdf) - 需要安装 pypdf
- Word (.docx) - 需要安装 python-docx

可以通过添加自定义加载器支持更多格式。

### Q9: 如何更新已索引的文档？

**A:** 使用强制重新索引：

```bash
python -m rag5.tools.index_manager reindex --directory ./docs --force
```

这会清空现有数据并重新索引所有文档。

### Q10: 在哪里可以找到更多帮助？

**A:** 参考以下文档：
- [调试指南](docs/debugging_guide.md) - 完整的故障排除指南
- [检索优化指南](docs/retrieval_optimization.md) - 提高检索效果
- [中文文本处理指南](docs/chinese_text_processing.md) - 中文优化
- [调试脚本文档](scripts/DEBUG_RETRIEVAL_README.md) - 调试工具使用

## 故障排除 Troubleshooting

### 常见错误和解决方案

#### 1. ConnectionError: Cannot connect to Qdrant

**原因：** Qdrant 服务未运行

**解决：**
```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

#### 2. OllamaError: Model not found

**原因：** 模型未安装

**解决：**
```bash
ollama pull bge-m3
ollama pull qwen2.5:7b
```

#### 3. IngestionError: Failed to load document

**原因：** 文档格式或编码问题

**解决：**
```bash
# 检查文件编码
file -I your_document.txt

# 转换为 UTF-8
iconv -f GBK -t UTF-8 input.txt > output.txt
```

#### 4. No results found

**原因：** 相似度阈值过高或文档未索引

**解决：**
```bash
# 运行诊断
python scripts/debug_retrieval.py

# 降低阈值
# 在 .env 中设置 SIMILARITY_THRESHOLD=0.2

# 重新索引
python -m rag5.tools.index_manager reindex --directory ./docs --force
```

### 获取详细帮助

如果问题仍未解决：

1. 运行完整诊断：`python scripts/debug_retrieval.py`
2. 查看诊断报告：`logs/debug_report_*.txt`
3. 查看详细日志：`logs/rag_app.log`
4. 参考 [调试指南](docs/debugging_guide.md)
5. 提交 issue 并附上诊断报告和日志

## License

MIT
