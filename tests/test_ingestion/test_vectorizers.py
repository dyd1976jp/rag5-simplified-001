"""
测试向量化器模块
"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document
from qdrant_client.models import PointStruct
from rag5.ingestion.vectorizers import BatchVectorizer, VectorUploader, UploadResult


def test_batch_vectorizer_initialization(mock_embeddings):
    """测试BatchVectorizer初始化"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings, batch_size=100)

    assert vectorizer is not None
    assert vectorizer.batch_size == 100


def test_batch_vectorizer_default_batch_size(mock_embeddings):
    """测试BatchVectorizer默认批次大小"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    assert vectorizer.batch_size > 0


def test_vectorize_single_document(mock_embeddings, sample_documents):
    """测试向量化单个文档"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    points = vectorizer.vectorize(sample_documents[:1])

    assert len(points) == 1
    assert isinstance(points[0], PointStruct)
    assert len(points[0].vector) == 1024


def test_vectorize_multiple_documents(mock_embeddings, sample_documents):
    """测试向量化多个文档"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    points = vectorizer.vectorize(sample_documents)

    assert len(points) == len(sample_documents)
    for point in points:
        assert isinstance(point, PointStruct)
        assert len(point.vector) == 1024


def test_vectorize_empty_list(mock_embeddings):
    """测试向量化空列表"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    points = vectorizer.vectorize([])

    assert len(points) == 0


def test_vectorize_preserves_metadata(mock_embeddings):
    """测试向量化保留元数据"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    doc = Document(
        page_content="测试内容",
        metadata={"source": "test.txt", "page": 1, "custom": "value"}
    )

    points = vectorizer.vectorize([doc])

    assert points[0].payload["text"] == "测试内容"
    assert points[0].payload["source"] == "test.txt"
    assert points[0].payload["metadata"]["page"] == 1
    assert points[0].payload["metadata"]["custom"] == "value"


def test_vectorize_batch_processing(mock_embeddings):
    """测试批量处理"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings, batch_size=10)

    # 创建大量文档
    docs = [
        Document(page_content=f"文档{i}", metadata={"id": i})
        for i in range(25)
    ]

    points = vectorizer.vectorize(docs)

    assert len(points) == 25


def test_vector_uploader_initialization(mock_qdrant_client):
    """测试VectorUploader初始化"""
    uploader = VectorUploader(
        qdrant_manager=mock_qdrant_client,
        collection_name="test_collection"
    )

    assert uploader is not None
    assert uploader.collection_name == "test_collection"


def test_upload_batch_success(mock_qdrant_client):
    """测试上传批次（成功）"""
    uploader = VectorUploader(
        qdrant_manager=mock_qdrant_client,
        collection_name="test_collection"
    )

    points = [
        PointStruct(
            id=f"id-{i}",
            vector=[0.1] * 1024,
            payload={"text": f"内容{i}"}
        )
        for i in range(10)
    ]

    count = uploader.upload_batch(points)

    assert count == 10
    assert mock_qdrant_client.upsert.called


def test_upload_batch_empty_list(mock_qdrant_client):
    """测试上传空批次"""
    uploader = VectorUploader(
        qdrant_manager=mock_qdrant_client,
        collection_name="test_collection"
    )

    count = uploader.upload_batch([])

    assert count == 0
    # 不应该调用upsert
    mock_qdrant_client.upsert.assert_not_called()


def test_upload_all_single_batch(mock_qdrant_client):
    """测试上传所有（单批次）"""
    uploader = VectorUploader(
        qdrant_manager=mock_qdrant_client,
        collection_name="test_collection"
    )

    points = [
        PointStruct(
            id=f"id-{i}",
            vector=[0.1] * 1024,
            payload={"text": f"内容{i}"}
        )
        for i in range(50)
    ]

    result = uploader.upload_all(points, batch_size=100)

    assert isinstance(result, UploadResult)
    assert result.total_points == 50
    assert result.uploaded_points == 50
    assert result.failed_batches == 0
    assert result.success_rate == 100.0


def test_upload_all_multiple_batches(mock_qdrant_client):
    """测试上传所有（多批次）"""
    uploader = VectorUploader(
        qdrant_manager=mock_qdrant_client,
        collection_name="test_collection"
    )

    points = [
        PointStruct(
            id=f"id-{i}",
            vector=[0.1] * 1024,
            payload={"text": f"内容{i}"}
        )
        for i in range(250)
    ]

    result = uploader.upload_all(points, batch_size=100)

    assert result.total_points == 250
    assert result.uploaded_points == 250
    # 应该调用upsert 3次（100 + 100 + 50）
    assert mock_qdrant_client.upsert.call_count == 3


def test_upload_all_with_failures(mock_qdrant_client):
    """测试上传所有（有失败）"""
    # 模拟部分失败
    mock_qdrant_client.upsert.side_effect = [
        None,  # 第一批成功
        Exception("上传失败"),  # 第二批失败
        None,  # 第三批成功
    ]

    uploader = VectorUploader(
        qdrant_manager=mock_qdrant_client,
        collection_name="test_collection"
    )

    points = [
        PointStruct(
            id=f"id-{i}",
            vector=[0.1] * 1024,
            payload={"text": f"内容{i}"}
        )
        for i in range(250)
    ]

    result = uploader.upload_all(points, batch_size=100)

    assert result.total_points == 250
    assert result.uploaded_points == 200  # 第一批和第三批成功
    assert result.failed_batches == 1
    assert result.success_rate < 100.0


def test_upload_result_dataclass():
    """测试UploadResult数据类"""
    result = UploadResult(
        total_points=100,
        uploaded_points=95,
        failed_batches=1
    )

    assert result.total_points == 100
    assert result.uploaded_points == 95
    assert result.failed_batches == 1
    assert result.success_rate == 95.0


def test_upload_result_zero_total():
    """测试UploadResult零总数"""
    result = UploadResult(
        total_points=0,
        uploaded_points=0,
        failed_batches=0
    )

    assert result.success_rate == 0.0


def test_vectorize_with_chinese_content(mock_embeddings):
    """测试向量化中文内容"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    doc = Document(
        page_content="这是中文测试内容，包含标点符号。",
        metadata={"source": "chinese.txt"}
    )

    points = vectorizer.vectorize([doc])

    assert len(points) == 1
    assert points[0].payload["text"] == "这是中文测试内容，包含标点符号。"


def test_vectorize_with_long_content(mock_embeddings):
    """测试向量化长内容"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    long_content = "这是一个很长的测试内容。" * 100
    doc = Document(
        page_content=long_content,
        metadata={"source": "long.txt"}
    )

    points = vectorizer.vectorize([doc])

    assert len(points) == 1
    assert len(points[0].payload["text"]) > 0


def test_vectorize_generates_unique_ids(mock_embeddings, sample_documents):
    """测试向量化生成唯一ID"""
    vectorizer = BatchVectorizer(embeddings=mock_embeddings)

    points = vectorizer.vectorize(sample_documents)

    ids = [point.id for point in points]
    # 所有ID应该是唯一的
    assert len(ids) == len(set(ids))


def test_upload_error_handling(mock_qdrant_client):
    """测试上传错误处理"""
    mock_qdrant_client.upsert.side_effect = Exception("连接错误")

    uploader = VectorUploader(
        qdrant_manager=mock_qdrant_client,
        collection_name="test_collection"
    )

    points = [
        PointStruct(
            id="id-1",
            vector=[0.1] * 1024,
            payload={"text": "内容"}
        )
    ]

    result = uploader.upload_all(points, batch_size=100)

    assert result.uploaded_points == 0
    assert result.failed_batches == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
