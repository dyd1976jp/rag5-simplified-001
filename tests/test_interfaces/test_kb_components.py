"""
知识库组件测试

测试 rag5/interfaces/ui/pages/knowledge_base/components.py 中的所有工具函数。
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime


# ==================== 格式化函数测试 ====================

def test_format_datetime_valid():
    """测试正常的日期时间格式化"""
    from rag5.interfaces.ui.pages.knowledge_base.components import format_datetime

    # 测试 UTC 时间
    result = format_datetime("2024-01-15T10:30:00Z")
    assert result == "2024-01-15 10:30"

    # 测试带时区的时间
    result = format_datetime("2024-01-15T10:30:00+00:00")
    assert result == "2024-01-15 10:30"


def test_format_datetime_invalid():
    """测试无效日期时间字符串"""
    from rag5.interfaces.ui.pages.knowledge_base.components import format_datetime

    # 无效格式应返回原始字符串
    invalid_str = "invalid-datetime"
    result = format_datetime(invalid_str)
    assert result == invalid_str


def test_format_file_size():
    """测试文件大小格式化"""
    from rag5.interfaces.ui.pages.knowledge_base.components import format_file_size

    # 测试各种单位
    assert format_file_size(0) == "0.0 B"
    assert format_file_size(512) == "512.0 B"
    assert format_file_size(1024) == "1.0 KB"
    assert format_file_size(1048576) == "1.0 MB"
    assert format_file_size(1073741824) == "1.0 GB"
    assert format_file_size(1099511627776) == "1.0 TB"

    # 测试小数
    assert format_file_size(1536) == "1.5 KB"  # 1.5 KB
    assert format_file_size(2621440) == "2.5 MB"  # 2.5 MB


def test_format_file_size_edge_cases():
    """测试文件大小格式化边界情况"""
    from rag5.interfaces.ui.pages.knowledge_base.components import format_file_size

    # 负数
    assert format_file_size(-100) == "-100 B"

    # 超大文件
    very_large = 10 * (1024 ** 5)  # 10 PB
    result = format_file_size(very_large)
    assert "PB" in result


def test_format_percentage():
    """测试百分比格式化"""
    from rag5.interfaces.ui.pages.knowledge_base.components import format_percentage

    assert format_percentage(85.567) == "85.6%"
    assert format_percentage(100.0) == "100.0%"
    assert format_percentage(0.0) == "0.0%"
    assert format_percentage(50.123, decimals=2) == "50.12%"


def test_truncate_text():
    """测试文本截断"""
    from rag5.interfaces.ui.pages.knowledge_base.components import truncate_text

    # 短文本不应被截断
    short_text = "短文本"
    assert truncate_text(short_text, max_length=10) == short_text

    # 长文本应被截断
    long_text = "这是一段很长的文本内容，需要被截断"
    result = truncate_text(long_text, max_length=10)
    assert len(result) == 10
    assert result.endswith("...")

    # 自定义后缀
    result = truncate_text(long_text, max_length=10, suffix="…")
    assert result.endswith("…")


# ==================== 输入验证测试 ====================

def test_validate_kb_name_valid():
    """测试有效的知识库名称"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_kb_name

    valid, error = validate_kb_name("我的知识库")
    assert valid is True
    assert error is None

    valid, error = validate_kb_name("Knowledge Base 123")
    assert valid is True
    assert error is None


def test_validate_kb_name_invalid():
    """测试无效的知识库名称"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_kb_name

    # 空名称
    valid, error = validate_kb_name("")
    assert valid is False
    assert "不能为空" in error

    valid, error = validate_kb_name("   ")
    assert valid is False
    assert "不能为空" in error

    # 过长名称
    valid, error = validate_kb_name("a" * 101)
    assert valid is False
    assert "长度" in error

    # 包含特殊字符
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        valid, error = validate_kb_name(f"test{char}name")
        assert valid is False
        assert "特殊字符" in error


def test_validate_file_upload_valid():
    """测试有效的文件上传"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_file_upload

    # 创建模拟文件
    mock_file1 = Mock()
    mock_file1.name = "test.pdf"
    mock_file1.size = 1024 * 1024  # 1 MB

    mock_file2 = Mock()
    mock_file2.name = "document.txt"
    mock_file2.size = 512 * 1024  # 512 KB

    # 测试有效上传
    valid, error = validate_file_upload([mock_file1, mock_file2])
    assert valid is True
    assert error is None


def test_validate_file_upload_no_files():
    """测试没有文件的情况"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_file_upload

    valid, error = validate_file_upload([])
    assert valid is False
    assert "请选择" in error


def test_validate_file_upload_too_many_files():
    """测试文件数量超限"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_file_upload

    # 创建模拟文件
    mock_files = [Mock(name=f"file{i}.txt", size=1024) for i in range(15)]

    valid, error = validate_file_upload(mock_files, max_files=10)
    assert valid is False
    assert "最多上传" in error


def test_validate_file_upload_invalid_extension():
    """测试不支持的文件类型"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_file_upload

    mock_file = Mock()
    mock_file.name = "test.exe"
    mock_file.size = 1024

    valid, error = validate_file_upload(
        [mock_file],
        allowed_extensions=['.pdf', '.txt', '.md']
    )
    assert valid is False
    assert "类型不支持" in error


def test_validate_file_upload_size_exceeded():
    """测试文件大小超限"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_file_upload

    mock_file = Mock()
    mock_file.name = "large_file.pdf"
    mock_file.size = 10 * 1024 * 1024  # 10 MB

    valid, error = validate_file_upload(
        [mock_file],
        max_file_size=5 * 1024 * 1024  # 5 MB 限制
    )
    assert valid is False
    assert "超过限制" in error


def test_validate_chunk_config_valid():
    """测试有效的分块配置"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_chunk_config

    valid, error = validate_chunk_config(500, 50)
    assert valid is True
    assert error is None

    valid, error = validate_chunk_config(1000, 200)
    assert valid is True
    assert error is None


def test_validate_chunk_config_invalid():
    """测试无效的分块配置"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_chunk_config

    # chunk_size 为 0
    valid, error = validate_chunk_config(0, 50)
    assert valid is False
    assert "必须大于 0" in error

    # chunk_overlap 为负数
    valid, error = validate_chunk_config(500, -10)
    assert valid is False
    assert "不能为负数" in error

    # chunk_overlap 大于 chunk_size
    valid, error = validate_chunk_config(100, 200)
    assert valid is False
    assert "不能大于" in error

    # chunk_size 过大
    valid, error = validate_chunk_config(15000, 100)
    assert valid is False
    assert "不建议超过" in error


def test_validate_retrieval_config_valid():
    """测试有效的检索配置"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_retrieval_config

    valid, error = validate_retrieval_config(5, 0.7)
    assert valid is True
    assert error is None

    valid, error = validate_retrieval_config(10, 0.5)
    assert valid is True
    assert error is None


def test_validate_retrieval_config_invalid():
    """测试无效的检索配置"""
    from rag5.interfaces.ui.pages.knowledge_base.components import validate_retrieval_config

    # top_k 为 0
    valid, error = validate_retrieval_config(0, 0.7)
    assert valid is False
    assert "必须大于 0" in error

    # top_k 过大
    valid, error = validate_retrieval_config(150, 0.7)
    assert valid is False
    assert "不建议超过" in error

    # similarity_threshold 超出范围
    valid, error = validate_retrieval_config(5, -0.1)
    assert valid is False
    assert "必须在 0 和 1 之间" in error

    valid, error = validate_retrieval_config(5, 1.5)
    assert valid is False
    assert "必须在 0 和 1 之间" in error


# ==================== 错误处理测试 ====================

def test_safe_api_call_success():
    """测试成功的 API 调用"""
    from rag5.interfaces.ui.pages.knowledge_base.components import safe_api_call

    def test_func():
        return "success"

    wrapped = safe_api_call(test_func)
    result = wrapped()
    assert result == "success"


def test_safe_api_call_error():
    """测试失败的 API 调用"""
    from rag5.interfaces.ui.pages.knowledge_base.components import safe_api_call

    def test_func():
        raise ValueError("Test error")

    wrapped = safe_api_call(test_func, show_error=False)
    result = wrapped()
    assert result is None


def test_safe_api_call_default_return():
    """测试自定义默认返回值"""
    from rag5.interfaces.ui.pages.knowledge_base.components import safe_api_call

    def test_func():
        raise ValueError("Test error")

    wrapped = safe_api_call(test_func, show_error=False, default_return="default")
    result = wrapped()
    assert result == "default"


# ==================== 用户反馈函数测试（需要 mock streamlit）====================

@pytest.mark.skip(reason="需要 mock streamlit，暂时跳过")
def test_show_success():
    """测试成功消息显示"""
    from rag5.interfaces.ui.pages.knowledge_base.components import show_success
    # TODO: Mock streamlit 后添加测试


@pytest.mark.skip(reason="需要 mock streamlit，暂时跳过")
def test_show_error():
    """测试错误消息显示"""
    from rag5.interfaces.ui.pages.knowledge_base.components import show_error
    # TODO: Mock streamlit 后添加测试


@pytest.mark.skip(reason="需要 mock streamlit，暂时跳过")
def test_show_warning():
    """测试警告消息显示"""
    from rag5.interfaces.ui.pages.knowledge_base.components import show_warning
    # TODO: Mock streamlit 后添加测试


@pytest.mark.skip(reason="需要 mock streamlit，暂时跳过")
def test_show_info():
    """测试信息消息显示"""
    from rag5.interfaces.ui.pages.knowledge_base.components import show_info
    # TODO: Mock streamlit 后添加测试
