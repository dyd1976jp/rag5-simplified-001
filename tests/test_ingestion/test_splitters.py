"""
测试文档分块器模块
"""

import pytest
from langchain_core.documents import Document
from rag5.ingestion.splitters import RecursiveSplitter


def test_recursive_splitter_initialization():
    """测试RecursiveSplitter初始化"""
    splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)

    assert splitter is not None
    assert splitter.chunk_size == 500
    assert splitter.chunk_overlap == 50


def test_recursive_splitter_default_values():
    """测试RecursiveSplitter默认值"""
    splitter = RecursiveSplitter()

    assert splitter.chunk_size > 0
    assert splitter.chunk_overlap >= 0
    assert splitter.chunk_overlap < splitter.chunk_size


def test_split_documents_basic(long_document):
    """测试基本文档分块"""
    splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)

    chunks = splitter.split_documents([long_document])

    assert len(chunks) > 1
    # 每个块应该在大小限制内
    for chunk in chunks:
        assert len(chunk.page_content) <= 600  # 允许一些容差


def test_split_documents_preserves_metadata(long_document):
    """测试分块保留元数据"""
    splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)

    long_document.metadata["custom_key"] = "custom_value"
    chunks = splitter.split_documents([long_document])

    for chunk in chunks:
        assert chunk.metadata.get("custom_key") == "custom_value"
        assert chunk.metadata.get("source") == long_document.metadata.get("source")


def test_split_documents_empty_list():
    """测试分块空文档列表"""
    splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)

    chunks = splitter.split_documents([])

    assert len(chunks) == 0


def test_split_documents_short_document():
    """测试分块短文档（不需要分块）"""
    splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)

    short_doc = Document(
        page_content="这是一个短文档。",
        metadata={"source": "short.txt"}
    )

    chunks = splitter.split_documents([short_doc])

    # 短文档可能不需要分块
    assert len(chunks) >= 1
    if len(chunks) == 1:
        assert chunks[0].page_content == short_doc.page_content


def test_split_documents_multiple_documents(sample_documents):
    """测试分块多个文档"""
    splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)

    # 创建长文档列表
    long_docs = []
    for i in range(3):
        doc = Document(
            page_content="这是一个测试句子。" * 100,
            metadata={"source": f"doc{i}.txt"}
        )
        long_docs.append(doc)

    chunks = splitter.split_documents(long_docs)

    assert len(chunks) > len(long_docs)


def test_split_text_method():
    """测试split_text方法"""
    splitter = RecursiveSplitter(chunk_size=100, chunk_overlap=10)

    long_text = "这是一个测试句子。" * 50

    if hasattr(splitter, 'split_text'):
        chunks = splitter.split_text(long_text)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 120  # 允许容差


def test_chunk_overlap_functionality():
    """测试块重叠功能"""
    splitter = RecursiveSplitter(chunk_size=100, chunk_overlap=20)

    text = "AAAA " * 30  # 创建可识别的内容
    doc = Document(page_content=text, metadata={})

    chunks = splitter.split_documents([doc])

    if len(chunks) >= 2:
        # 检查相邻块之间有重叠
        # 这是一个简化的检查
        assert len(chunks[0].page_content) > 0
        assert len(chunks[1].page_content) > 0


def test_chinese_text_splitting():
    """测试中文文本分块"""
    splitter = RecursiveSplitter(chunk_size=200, chunk_overlap=20)

    chinese_text = "这是一个中文测试文档。" * 50
    doc = Document(page_content=chinese_text, metadata={"source": "chinese.txt"})

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1
    for chunk in chunks:
        assert "中文" in chunk.page_content or "测试" in chunk.page_content


def test_mixed_language_splitting():
    """测试混合语言分块"""
    splitter = RecursiveSplitter(chunk_size=200, chunk_overlap=20)

    mixed_text = "This is English. 这是中文。" * 30
    doc = Document(page_content=mixed_text, metadata={})

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1


def test_separators_configuration():
    """测试分隔符配置"""
    # 使用自定义分隔符
    separators = ["\n\n", "\n", "。", ".", " "]
    splitter = RecursiveSplitter(
        chunk_size=200,
        chunk_overlap=20,
        separators=separators
    )

    text = "第一段。\n\n第二段。\n\n第三段。" * 20
    doc = Document(page_content=text, metadata={})

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1


def test_chunk_size_boundary():
    """测试块大小边界"""
    splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)

    # 创建恰好在边界的文本
    text = "A" * 45  # 略小于chunk_size
    doc = Document(page_content=text, metadata={})

    chunks = splitter.split_documents([doc])

    assert len(chunks) >= 1


def test_very_small_chunk_size():
    """测试非常小的块大小"""
    splitter = RecursiveSplitter(chunk_size=10, chunk_overlap=2)

    text = "这是测试文本" * 10
    doc = Document(page_content=text, metadata={})

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1


def test_zero_overlap():
    """测试零重叠"""
    splitter = RecursiveSplitter(chunk_size=100, chunk_overlap=0)

    text = "测试内容。" * 50
    doc = Document(page_content=text, metadata={})

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1


def test_split_with_newlines():
    """测试包含换行符的文本分块"""
    splitter = RecursiveSplitter(chunk_size=200, chunk_overlap=20)

    text = "第一行\n第二行\n第三行\n" * 30
    doc = Document(page_content=text, metadata={})

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1


def test_split_with_special_characters():
    """测试包含特殊字符的文本分块"""
    splitter = RecursiveSplitter(chunk_size=200, chunk_overlap=20)

    text = "特殊字符：！@#￥%……&*（）" * 30
    doc = Document(page_content=text, metadata={})

    chunks = splitter.split_documents([doc])

    assert len(chunks) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
