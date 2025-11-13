"""
测试文档加载器模块
"""

import os
import pytest
import tempfile
from pathlib import Path
from rag5.ingestion.loaders import TextLoader, PDFLoader, MarkdownLoader, BaseLoader


def test_text_loader_initialization():
    """测试TextLoader初始化"""
    loader = TextLoader()
    assert loader is not None


def test_text_loader_supports():
    """测试TextLoader支持的文件类型"""
    loader = TextLoader()

    assert loader.supports("test.txt") is True
    assert loader.supports("test.TXT") is True
    assert loader.supports("test.pdf") is False
    assert loader.supports("test.md") is False


def test_text_loader_load_file(temp_docs_dir):
    """测试TextLoader加载文件"""
    loader = TextLoader()

    # 创建测试文件
    test_file = os.path.join(temp_docs_dir, "test.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("这是测试内容。\n李小勇是企业家。")

    docs = loader.load(test_file)

    assert len(docs) > 0
    assert "李小勇" in docs[0].page_content
    assert docs[0].metadata["source"] == test_file


def test_text_loader_load_with_different_encodings(temp_docs_dir):
    """测试TextLoader加载不同编码的文件"""
    loader = TextLoader()

    # 测试UTF-8
    test_file = os.path.join(temp_docs_dir, "utf8.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("UTF-8编码的中文内容")

    docs = loader.load(test_file)
    assert len(docs) > 0
    assert "中文" in docs[0].page_content


def test_text_loader_load_nonexistent_file():
    """测试TextLoader加载不存在的文件"""
    loader = TextLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent.txt")


def test_pdf_loader_initialization():
    """测试PDFLoader初始化"""
    loader = PDFLoader()
    assert loader is not None


def test_pdf_loader_supports():
    """测试PDFLoader支持的文件类型"""
    loader = PDFLoader()

    assert loader.supports("test.pdf") is True
    assert loader.supports("test.PDF") is True
    assert loader.supports("test.txt") is False
    assert loader.supports("test.md") is False


def test_markdown_loader_initialization():
    """测试MarkdownLoader初始化"""
    loader = MarkdownLoader()
    assert loader is not None


def test_markdown_loader_supports():
    """测试MarkdownLoader支持的文件类型"""
    loader = MarkdownLoader()

    assert loader.supports("test.md") is True
    assert loader.supports("test.MD") is True
    assert loader.supports("test.markdown") is True
    assert loader.supports("test.MARKDOWN") is True
    assert loader.supports("test.txt") is False
    assert loader.supports("test.pdf") is False


def test_markdown_loader_load_file(temp_docs_dir):
    """测试MarkdownLoader加载文件"""
    loader = MarkdownLoader()

    # 创建测试Markdown文件
    test_file = os.path.join(temp_docs_dir, "test.md")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# 标题\n\n这是Markdown内容。\n\n## 子标题\n\n更多内容。")

    try:
        docs = loader.load(test_file)
        assert len(docs) > 0
        assert "标题" in docs[0].page_content or "Markdown" in docs[0].page_content
    except Exception as e:
        # 如果unstructured包有问题，跳过测试
        if "unstructured" in str(e).lower():
            pytest.skip("Unstructured package not properly configured")
        else:
            raise


def test_base_loader_is_abstract():
    """测试BaseLoader是抽象类"""
    with pytest.raises(TypeError):
        BaseLoader()


def test_loader_metadata_preservation(temp_docs_dir):
    """测试加载器保留元数据"""
    loader = TextLoader()

    test_file = os.path.join(temp_docs_dir, "metadata_test.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("测试内容")

    docs = loader.load(test_file)

    assert "source" in docs[0].metadata
    assert docs[0].metadata["source"] == test_file


def test_text_loader_empty_file(temp_docs_dir):
    """测试TextLoader加载空文件"""
    loader = TextLoader()

    test_file = os.path.join(temp_docs_dir, "empty.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        pass  # 创建空文件

    docs = loader.load(test_file)

    # 应该返回空列表或包含空内容的文档
    assert isinstance(docs, list)


def test_text_loader_large_file(temp_docs_dir):
    """测试TextLoader加载大文件"""
    loader = TextLoader()

    test_file = os.path.join(temp_docs_dir, "large.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        # 写入大量内容
        for i in range(1000):
            f.write(f"这是第{i}行内容。\n")

    docs = loader.load(test_file)

    assert len(docs) > 0
    assert len(docs[0].page_content) > 0


def test_text_loader_special_characters(temp_docs_dir):
    """测试TextLoader处理特殊字符"""
    loader = TextLoader()

    test_file = os.path.join(temp_docs_dir, "special.txt")
    special_content = "特殊字符：！@#￥%……&*（）——+{}|：""《》？"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(special_content)

    docs = loader.load(test_file)

    assert len(docs) > 0
    # 特殊字符应该被保留
    assert "特殊字符" in docs[0].page_content


def test_loader_file_extension_case_insensitive(temp_docs_dir):
    """测试加载器文件扩展名不区分大小写"""
    loader = TextLoader()

    # 测试大写扩展名
    test_file = os.path.join(temp_docs_dir, "test.TXT")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("测试内容")

    assert loader.supports(test_file) is True
    docs = loader.load(test_file)
    assert len(docs) > 0


def test_multiple_loaders_integration(temp_docs_dir):
    """测试多个加载器集成"""
    loaders = [TextLoader(), MarkdownLoader()]

    # 创建不同类型的文件
    files = {
        "test.txt": "文本内容",
        "test.md": "# Markdown内容"
    }

    for filename, content in files.items():
        filepath = os.path.join(temp_docs_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    # 使用合适的加载器加载每个文件
    all_docs = []
    for filename in files.keys():
        filepath = os.path.join(temp_docs_dir, filename)
        for loader in loaders:
            if loader.supports(filepath):
                try:
                    docs = loader.load(filepath)
                    all_docs.extend(docs)
                    break
                except Exception as e:
                    if "unstructured" in str(e).lower():
                        continue
                    raise

    assert len(all_docs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
