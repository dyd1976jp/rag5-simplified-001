# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Rules

**IMPORTANT: These rules must be strictly followed for all development work.**

### 1. Language Requirements
- **所有对话必须使用中文** - All conversations with the user must be in Chinese
- Code comments should be in Chinese when appropriate
- Documentation can be bilingual (English for technical terms, Chinese for explanations)

### 2. Code Cleanliness
- **临时测试代码必须及时删除** - Delete temporary test code immediately after use
- Do not commit debug print statements, commented-out code blocks, or experimental code
- Before committing, review all changes to ensure no temporary code remains
- Use proper logging instead of print statements for debugging

### 3. File Organization
- **文件必须有规律地放置在指定目录** - Files must be organized systematically in designated directories
- Follow the established project structure:
  - Source code: `rag5/` (organized by component)
  - Scripts: `scripts/` (executable utilities)
  - Tests: `tests/` (mirroring source structure)
  - Configuration: root level (`.env`, `pyproject.toml`, etc.)
  - Documentation: root level or `docs/`
  - Data/Runtime: `data/`, `logs/`, `qdrant_storage/` (gitignored)
  - Archives: `BK/` (old/moved files only)
- Never create files in arbitrary locations
- If unsure where a file belongs, ask before creating it

### 4. Commit Guidelines
- Write clear, descriptive commit messages (in Chinese or English)
- Keep commits atomic (one logical change per commit)
- Clean up temporary files before committing
- Use meaningful branch names for features/fixes

## Project Overview

RAG5 is a locally-deployed Retrieval-Augmented Generation (RAG) system with FastAPI/Streamlit interfaces. It provides a complete knowledge base ingestion and Q&A pipeline using Ollama for LLM/embeddings and Qdrant for vector storage.

**Tech Stack:**
- **LLM & Embeddings**: Ollama (default: `qwen2.5:7b` for LLM, `bge-m3` for embeddings)
- **Vector Database**: Qdrant (local Docker instance)
- **Frameworks**: LangChain, LangGraph
- **Interfaces**: FastAPI REST API, Streamlit Web UI
- **Language**: Python 3.9+

## Common Commands

### Setup and Installation
```bash
# Install package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Pull required Ollama models
./scripts/setup_models.sh

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Running Services
```bash
# Start Web UI (Streamlit)
python scripts/run_ui.py
# Or after installation:
rag5-ui

# Start REST API (FastAPI)
python scripts/run_api.py
# Or after installation:
rag5-api

# Ingest documents into knowledge base
python scripts/ingest.py /path/to/docs
# Or after installation:
rag5-ingest /path/to/docs
```

### Testing
```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_core/
pytest tests/test_tools/
pytest tests/test_ingestion/

# Run a single test
pytest tests/test_core/test_agent.py::test_agent_handles_context

# Run with coverage
pytest --cov=rag5 --cov-report=html

# Run verbose mode
pytest -v

# Run end-to-end tests
python scripts/test_e2e.py

# Run performance tests
python scripts/test_performance.py
```

### Code Quality
```bash
# Format code with black
black rag5/ tests/

# Check style with flake8
flake8 rag5/

# Type checking with mypy
mypy rag5/
```

### Debugging and Diagnostics
```bash
# Run retrieval diagnostics
python scripts/debug_retrieval.py

# Debug with custom query
python scripts/debug_retrieval.py --query "your query"

# Search for specific keyword
python scripts/debug_retrieval.py --keyword "关键词"

# Check database collection status
python -m rag5.tools.diagnostics.db_check --collection knowledge_base

# Search in database
python -m rag5.tools.diagnostics.db_check --search "keyword"

# Verify embeddings
python -m rag5.tools.diagnostics.db_check --verify-embeddings

# Reindex documents
python -m rag5.tools.index_manager reindex --directory ./docs --force

# View unified flow logs
tail -f logs/unified_flow.log

# Analyze flow logs
python scripts/analyze_flow_logs.py --stats
python scripts/analyze_flow_logs.py --session <session-id>
```

### Knowledge Base Management
```bash
# Manage knowledge bases (create, list, delete, etc.)
python scripts/kb_manager.py list
python scripts/kb_manager.py create --name "my_kb" --description "My KB"
python scripts/kb_manager.py delete --id <kb_id>

# Migrate knowledge bases
python scripts/migrate_kb.py
```

## Architecture Overview

### Core Components

**1. Agent System** ([rag5/core/agent/](rag5/core/agent/))
- `agent.py`: Main `SimpleRAGAgent` class - orchestrates LLM interactions using LangGraph
- `initializer.py`: Sets up LangChain LLM, tools, and agent executor
- `messages.py`: Message formatting and conversion between formats
- `history.py`: Conversation history management with token limits
- `errors.py`: Error handling and retry logic with exponential backoff

**2. Knowledge Base System** ([rag5/core/knowledge_base/](rag5/core/knowledge_base/))
- `models.py`: Data models (`KnowledgeBase`, `FileEntity`, `ChunkConfig`, `RetrievalConfig`)
- `database.py`: SQLite persistence layer for KB metadata
- `provider.py`: In-memory cache layer for fast KB access
- `vector_manager.py`: Qdrant collection management per knowledge base
- `manager.py`: High-level KB operations (create, update, delete, file upload)

**3. Search Tools** ([rag5/tools/search/](rag5/tools/search/))
- `search_tool.py`: Base vector search with Qdrant integration
- `adaptive_search.py`: Auto-adjusts similarity threshold for better recall
- `hybrid_search.py`: Combines vector + keyword search
- `query_expander.py`: Expands queries with synonyms

**4. Ingestion Pipeline** ([rag5/ingestion/](rag5/ingestion/))
- `loaders/`: Document loaders (PDF, TXT, MD, DOCX)
- `splitters/`: Text chunking with Chinese text optimization
- `vectorizers/`: Batch embedding generation and Qdrant upload
- `pipeline.py`: Orchestrates load → chunk → embed → store flow

**5. Interfaces**
- `interfaces/api/`: FastAPI REST endpoints ([rag5/interfaces/api/](rag5/interfaces/api/))
- `interfaces/ui/`: Streamlit multi-page app ([rag5/interfaces/ui/](rag5/interfaces/ui/))
  - `pages/chat.py`: Main chat interface
  - `pages/knowledge_base/`: KB management UI
  - `state.py`: Session state management
  - `components.py`: Reusable UI components

### Configuration System

Configuration is managed through environment variables (`.env` file) and the `rag5/config/` module:
- `settings.py`: Pydantic-based settings loaded from environment
- Supports Ollama, Qdrant, chunking, retrieval, and logging configurations
- Key settings: `LLM_MODEL`, `EMBED_MODEL`, `QDRANT_URL`, `CHUNK_SIZE`, `TOP_K`, `SIMILARITY_THRESHOLD`

### Logging System

RAG5 has a sophisticated multi-layer logging system:

1. **Unified Flow Logging** (`logs/unified_flow.log`):
   - Single chronological log file for complete query processing
   - Human-readable format with session tracking
   - Configurable detail levels: minimal, normal, verbose

2. **Enhanced Logging**:
   - `logs/llm_interactions.log`: All LLM prompts and responses with timing
   - `logs/agent_reflections.log`: Agent reasoning and decision-making
   - `logs/conversation_context.log`: Conversation history evolution

3. **Analysis Tools**:
   - `scripts/analyze_flow_logs.py`: Parse and analyze unified flow logs
   - `rag5/utils/`: FlowLogAnalyzer, LLMLogger, ReflectionLogger classes

### Data Flow

**Query Processing:**
1. User query → `SimpleRAGAgent.chat()`
2. Agent analyzes query via LLM reflection
3. Tool selection: `search_knowledge_base` called with query
4. Vector search in Qdrant (with optional adaptive/hybrid search)
5. Retrieved context + query → LLM prompt
6. LLM generates answer → returned to user
7. All steps logged to unified flow log

**Document Ingestion:**
1. Directory scan → Document loader (by file extension)
2. Text extraction → Chunking (respects sentence boundaries, Chinese-aware)
3. Batch embedding generation (Ollama)
4. Vector upload to Qdrant collection
5. Metadata stored in KB database

## Important Patterns

### Multi-Knowledge Base Support

The system supports multiple isolated knowledge bases (v2.0+):
- Each KB has its own Qdrant collection
- Independent chunk and retrieval configurations per KB
- SQLite metadata storage in `data/knowledge_bases.db`
- Backward compatibility with "default" KB for legacy code

### Chinese Text Processing

Special handling for Chinese content:
- `ChineseTextSplitter`: Respects sentence boundaries using Chinese punctuation
- Auto-detection of Chinese text ratio
- Optimized chunk sizes and overlap for Chinese (500/50 default)
- Enable with `ENABLE_CHINESE_SPLITTER=true` in `.env`

### Error Handling

- Retry logic with exponential backoff for LLM/embedding calls
- Graceful degradation when tools fail
- Comprehensive error logging to separate error streams
- User-friendly error messages in UI/API responses

### Testing Strategy

- **Unit tests**: Each module has tests in `tests/test_<module>/`
- **Integration tests**: `tests/test_integration/` for KB + agent workflows
- **E2E tests**: `scripts/test_e2e.py` for complete user scenarios
- **Performance tests**: `scripts/test_performance.py` for benchmarking

## Development Workflow

### Adding a New Search Feature

1. Create implementation in `rag5/tools/search/<feature>.py`
2. Export from `rag5/tools/search/__init__.py`
3. Add configuration to `.env.example` and `rag5/config/settings.py`
4. Write tests in `tests/test_tools/test_search.py`
5. Update documentation

### Adding a New Document Type

1. Create loader in `rag5/ingestion/loaders/<type>_loader.py`
2. Implement `BaseLoader` interface (`load()`, `supports()`)
3. Register in `rag5/ingestion/loaders/__init__.py`
4. Add file extension to `SUPPORTED_EXTENSIONS`
5. Add any new dependencies to `requirements.txt`
6. Test with sample documents

### Modifying Agent Behavior

- Edit prompts in `rag5/core/prompts/` (system prompts, tool descriptions)
- Modify tool calling logic in `rag5/core/agent/agent.py`
- Update reflection/reasoning in `SimpleRAGAgent._analyze_query()`
- Test thoroughly as changes affect all queries

## Common Issues

### Embedding Model Stability
`bge-m3` has known stability issues in some Ollama versions. Consider using `nomic-embed-text` (768 dim) instead:
```bash
ollama pull nomic-embed-text
# Update .env:
# EMBED_MODEL=nomic-embed-text
# VECTOR_DIM=768
# Clear existing collection if switching models
```

### Service Dependencies
Ensure Qdrant and Ollama are running:
```bash
# Check Qdrant
curl http://localhost:6333/collections

# Check Ollama
curl http://localhost:11434/api/tags

# Start Qdrant if needed
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### No Search Results
Common causes:
1. Similarity threshold too high → lower `SIMILARITY_THRESHOLD` in `.env`
2. Wrong embedding model → verify `EMBED_MODEL` matches indexed documents
3. Documents not indexed → run `python scripts/ingest.py <dir>`
4. Use `scripts/debug_retrieval.py` to diagnose

## Project Structure Notes

- `BK/`: Archived/moved files (see `BK/moved_files.log`) - ignore for current development
- `data/`: Runtime data (SQLite DB, caches) - not in git
- `logs/`: Log files - not in git
- `qdrant_storage/`: Qdrant data directory - not in git
- All tests deleted in recent commits - need to be recreated if testing is required
