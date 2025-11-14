"""
Pytest配置文件

提供测试fixtures和配置
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_docs_dir():
    """创建包含测试文档的临时目录"""
    temp_dir = tempfile.mkdtemp()

    # 创建测试 .txt 文件
    txt_file = os.path.join(temp_dir, "test.txt")
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("这是一个测试文档。\n李小勇是一位企业家。\n他创办了多家公司。")

    # 创建测试 .md 文件
    md_file = os.path.join(temp_dir, "test.md")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# 测试文档\n\n这是Markdown格式的测试文档。\n\n## 内容\n\n包含一些测试内容。")

    # 创建测试 .pdf 文件（简单的文本文件作为占位符）
    pdf_file = os.path.join(temp_dir, "test.pdf")
    with open(pdf_file, "w", encoding="utf-8") as f:
        f.write("PDF placeholder content")

    yield temp_dir

    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_embeddings():
    """Mock OllamaEmbeddings"""
    mock = Mock()
    mock.embed_query.return_value = [0.1] * 1024  # 1024维向量
    mock.embed_documents.return_value = [[0.1] * 1024]
    return mock


@pytest.fixture
def mock_qdrant_client():
    """Mock QdrantClient"""
    mock = Mock()

    # Mock get_collections
    mock_collection = Mock()
    mock_collection.name = "knowledge_base"
    mock_collections = Mock()
    mock_collections.collections = [mock_collection]
    mock.get_collections.return_value = mock_collections

    # Mock query_points
    mock_result = Mock()
    mock_result.points = []
    mock.query_points.return_value = mock_result

    # Mock upsert
    mock.upsert.return_value = None

    return mock


@pytest.fixture
def mock_llm():
    """Mock ChatOllama LLM"""
    from langchain_core.messages import AIMessage

    mock = Mock()
    mock.invoke.return_value = AIMessage(content="测试响应")
    return mock


@pytest.fixture
def mock_tools():
    """Mock tools list"""
    mock_tool = Mock()
    mock_tool.name = "search_knowledge_base"
    mock_tool.description = "搜索知识库"
    return [mock_tool]


@pytest.fixture
def mock_agent_executor():
    """Mock agent executor"""
    from langchain_core.messages import AIMessage

    mock = Mock()
    mock.invoke.return_value = {
        "messages": [AIMessage(content="这是测试响应")]
    }
    return mock


@pytest.fixture
def sample_documents():
    """创建示例文档列表"""
    from langchain_core.documents import Document

    return [
        Document(
            page_content="这是第一个测试文档。包含一些中文内容。",
            metadata={"source": "test1.txt", "page": 1}
        ),
        Document(
            page_content="这是第二个测试文档。包含更多中文内容。",
            metadata={"source": "test2.txt", "page": 1}
        ),
    ]


@pytest.fixture
def long_document():
    """创建长文档用于测试分块"""
    from langchain_core.documents import Document

    long_text = "这是一个测试句子。" * 100
    return Document(
        page_content=long_text,
        metadata={"source": "long_test.txt"}
    )


@pytest.fixture(autouse=True)
def reset_environment():
    """在每个测试前重置环境变量"""
    # 保存原始环境变量
    original_env = os.environ.copy()

    yield

    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_ollama_api():
    """Mock Ollama API响应"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:7b"},
                {"name": "bge-m3"}
            ]
        }
        mock_get.return_value = mock_response
        yield mock_get


# 配置pytest选项
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
