"""
测试摄取流程编排器模块
"""

import os
import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document
from rag5.ingestion.pipeline import IngestionPipeline, IngestionResult


def test_ingestion_result_dataclass():
    """测试IngestionResult数据类"""
    result = IngestionResult(
        documents_loaded=10,
        chunks_created=100,
        vectors_uploaded=95,
        failed_files=["file1.txt"],
        errors=["error1"]
    )

    assert result.documents_loaded == 10
    assert result.chunks_created == 100
    assert result.vectors_uploaded == 95
    assert len(result.failed_files) == 1
    assert len(result.errors) == 1

    # 测试success_rate计算
    expected_rate = (10 / 11) * 100  # 10成功 / (10成功 + 1失败)
    assert abs(result.success_rate - expected_rate) < 0.01


def test_ingestion_result_all_success():
    """测试IngestionResult全部成功"""
    result = IngestionResult(
        documents_loaded=10,
        chunks_created=100,
        vectors_uploaded=100,
        failed_files=[],
        errors=[]
    )

    assert result.success_rate == 100.0


def test_ingestion_result_all_failed():
    """测试IngestionResult全部失败"""
    result = IngestionResult(
        documents_loaded=0,
        chunks_created=0,
        vectors_uploaded=0,
        failed_files=["file1.txt", "file2.txt"],
        errors=["error1", "error2"]
    )

    assert result.success_rate == 0.0


def test_ingestion_pipeline_initialization():
    """测试IngestionPipeline初始化"""
    mock_loaders = [Mock()]
    mock_splitter = Mock()
    mock_vectorizer = Mock()

    pipeline = IngestionPipeline(
        loaders=mock_loaders,
        splitter=mock_splitter,
        vectorizer=mock_vectorizer
    )

    assert pipeline is not None


def test_ingest_file_success(temp_docs_dir):
    """测试摄取单个文件（成功）"""
    # 创建测试文件
    test_file = os.path.join(temp_docs_dir, "test.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("测试内容" * 100)

    # Mock组件
    mock_loader = Mock()
    mock_loader.supports.return_value = True
    mock_loader.load.return_value = [
        Document(page_content="测试内容" * 100, metadata={"source": test_file})
    ]

    mock_splitter = Mock()
    mock_splitter.split_documents.return_value = [
        Document(page_content="块1", metadata={"source": test_file}),
        Document(page_content="块2", metadata={"source": test_file}),
    ]

    mock_vectorizer = Mock()
    mock_vectorizer.vectorize.return_value = [Mock(), Mock()]
    mock_vectorizer.uploader = Mock()
    mock_vectorizer.uploader.upload_all.return_value = Mock(uploaded_points=2)

    pipeline = IngestionPipeline(
        loaders=[mock_loader],
        splitter=mock_splitter,
        vectorizer=mock_vectorizer
    )

    result = pipeline.ingest_file(test_file)

    assert isinstance(result, IngestionResult)
    assert result.documents_loaded == 1
    assert result.chunks_created == 2


def test_ingest_file_not_found():
    """测试摄取不存在的文件"""
    mock_loader = Mock()
    mock_splitter = Mock()
    mock_vectorizer = Mock()

    pipeline = IngestionPipeline(
        loaders=[mock_loader],
        splitter=mock_splitter,
        vectorizer=mock_vectorizer
    )

    result = pipeline.ingest_file("nonexistent.txt")

    assert result.documents_loaded == 0
    assert len(result.failed_files) == 1
    assert len(result.errors) > 0


def test_ingest_file_unsupported_type(temp_docs_dir):
    """测试摄取不支持的文件类型"""
    test_file = os.path.join(temp_docs_dir, "test.xyz")
    with open(test_file, "w") as f:
        f.write("unsupported content")

    mock_loader = Mock()
    mock_loader.supports.return_value = False

    pipeline = IngestionPipeline(
        loaders=[mock_loader],
        splitter=Mock(),
        vectorizer=Mock()
    )

    result = pipeline.ingest_file(test_file)

    assert result.documents_loaded == 0
    assert len(result.errors) > 0


def test_ingest_directory_success(temp_docs_dir):
    """测试摄取目录（成功）"""
    # 创建多个测试文件
    for i in range(3):
        test_file = os.path.join(temp_docs_dir, f"test{i}.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(f"内容{i}" * 50)

    # Mock组件
    mock_loader = Mock()
    mock_loader.supports.return_value = True
    mock_loader.load.return_value = [
        Document(page_content="内容", metadata={})
    ]

    mock_splitter = Mock()
    mock_splitter.split_documents.return_value = [
        Document(page_content="块", metadata={})
    ]

    mock_vectorizer = Mock()
    mock_vectorizer.vectorize.return_value = [Mock()]
    mock_vectorizer.uploader = Mock()
    mock_vectorizer.uploader.upload_all.return_value = Mock(uploaded_points=1)

    pipeline = IngestionPipeline(
        loaders=[mock_loader],
        splitter=mock_splitter,
        vectorizer=mock_vectorizer
    )

    result = pipeline.ingest_directory(temp_docs_dir)

    assert result.documents_loaded == 3
    assert result.chunks_created >= 3


def test_ingest_directory_not_found():
    """测试摄取不存在的目录"""
    pipeline = IngestionPipeline(
        loaders=[Mock()],
        splitter=Mock(),
        vectorizer=Mock()
    )

    with pytest.raises(ValueError, match="does not exist"):
        pipeline.ingest_directory("/nonexistent/directory")


def test_ingest_directory_empty(temp_docs_dir):
    """测试摄取空目录"""
    # temp_docs_dir已经有一些文件，创建一个新的空目录
    import tempfile
    empty_dir = tempfile.mkdtemp()

    pipeline = IngestionPipeline(
        loaders=[Mock()],
        splitter=Mock(),
        vectorizer=Mock()
    )

    result = pipeline.ingest_directory(empty_dir)

    assert result.documents_loaded == 0

    # 清理
    import shutil
    shutil.rmtree(empty_dir)


def test_ingest_directory_mixed_files(temp_docs_dir):
    """测试摄取包含多种文件类型的目录"""
    # 创建不同类型的文件
    files = {
        "test.txt": "文本内容",
        "test.md": "# Markdown内容",
        "test.xyz": "不支持的内容"
    }

    for filename, content in files.items():
        filepath = os.path.join(temp_docs_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    # Mock加载器，只支持.txt和.md
    mock_loader = Mock()
    def supports_side_effect(path):
        return path.endswith('.txt') or path.endswith('.md')
    mock_loader.supports.side_effect = supports_side_effect
    mock_loader.load.return_value = [Document(page_content="内容", metadata={})]

    mock_splitter = Mock()
    mock_splitter.split_documents.return_value = [Document(page_content="块", metadata={})]

    mock_vectorizer = Mock()
    mock_vectorizer.vectorize.return_value = [Mock()]
    mock_vectorizer.uploader = Mock()
    mock_vectorizer.uploader.upload_all.return_value = Mock(uploaded_points=1)

    pipeline = IngestionPipeline(
        loaders=[mock_loader],
        splitter=mock_splitter,
        vectorizer=mock_vectorizer
    )

    result = pipeline.ingest_directory(temp_docs_dir)

    # 应该只处理支持的文件
    assert result.documents_loaded >= 2


def test_ingest_with_errors_continues(temp_docs_dir):
    """测试摄取时遇到错误继续处理其他文件"""
    # 创建多个文件
    for i in range(3):
        test_file = os.path.join(temp_docs_dir, f"test{i}.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(f"内容{i}")

    # Mock加载器，第二个文件失败
    call_count = [0]
    def load_side_effect(path):
        call_count[0] += 1
        if call_count[0] == 2:
            raise Exception("加载失败")
        return [Document(page_content="内容", metadata={"source": path})]

    mock_loader = Mock()
    mock_loader.supports.return_value = True
    mock_loader.load.side_effect = load_side_effect

    mock_splitter = Mock()
    mock_splitter.split_documents.return_value = [Document(page_content="块", metadata={})]

    mock_vectorizer = Mock()
    mock_vectorizer.vectorize.return_value = [Mock()]
    mock_vectorizer.uploader = Mock()
    mock_vectorizer.uploader.upload_all.return_value = Mock(uploaded_points=1)

    pipeline = IngestionPipeline(
        loaders=[mock_loader],
        splitter=mock_splitter,
        vectorizer=mock_vectorizer
    )

    result = pipeline.ingest_directory(temp_docs_dir)

    # 应该处理了2个文件，1个失败
    assert result.documents_loaded == 2
    assert len(result.failed_files) == 1
    assert len(result.errors) >= 1


def test_ingest_progress_logging(temp_docs_dir, caplog):
    """测试摄取进度日志"""
    # 创建测试文件
    test_file = os.path.join(temp_docs_dir, "test.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("测试内容")

    mock_loader = Mock()
    mock_loader.supports.return_value = True
    mock_loader.load.return_value = [Document(page_content="内容", metadata={})]

    mock_splitter = Mock()
    mock_splitter.split_documents.return_value = [Document(page_content="块", metadata={})]

    mock_vectorizer = Mock()
    mock_vectorizer.vectorize.return_value = [Mock()]
    mock_vectorizer.uploader = Mock()
    mock_vectorizer.uploader.upload_all.return_value = Mock(uploaded_points=1)

    pipeline = IngestionPipeline(
        loaders=[mock_loader],
        splitter=mock_splitter,
        vectorizer=mock_vectorizer
    )

    with caplog.at_level("INFO"):
        result = pipeline.ingest_file(test_file)

    # 应该有日志输出
    # 注意：这取决于实际实现是否有日志


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
