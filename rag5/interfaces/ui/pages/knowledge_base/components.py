"""
知识库管理组件和工具函数

这个模块提供了知识库管理页面所需的通用工具函数和组件。
包括日期格式化、文件大小格式化、错误处理、用户反馈和输入验证等功能。
"""

import logging
import functools
from datetime import datetime
from typing import Callable, Any, Optional, List, Dict, TypeVar, Union

# 尝试导入 streamlit，如果不可用则设为 None
try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

logger = logging.getLogger(__name__)

# 类型变量用于泛型函数
T = TypeVar('T')


# ==================== 格式化工具函数 ====================

def format_datetime(dt_str: str) -> str:
    """
    格式化日期时间字符串为可读格式。

    将 ISO 格式的日期时间字符串转换为 YYYY-MM-DD HH:MM 格式。
    如果转换失败，返回原始字符串。

    参数:
        dt_str: ISO 格式的日期时间字符串 (如 "2024-01-15T10:30:00Z")

    返回:
        格式化后的日期时间字符串 (如 "2024-01-15 10:30")

    示例:
        >>> format_datetime("2024-01-15T10:30:00Z")
        '2024-01-15 10:30'
        >>> format_datetime("invalid")
        'invalid'
    """
    try:
        # 处理 UTC 时间标记
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        logger.warning(f"格式化日期时间失败 {dt_str}: {e}")
        return dt_str


def format_file_size(size_bytes: Union[int, float]) -> str:
    """
    格式化文件大小为人类可读格式。

    将字节大小转换为合适的单位 (B, KB, MB, GB, TB, PB)。

    参数:
        size_bytes: 文件大小（字节）

    返回:
        格式化后的文件大小字符串

    示例:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
        >>> format_file_size(0)
        '0.0 B'
    """
    try:
        size = float(size_bytes)

        # 处理负数和零
        if size < 0:
            return f"{size_bytes} B"
        if size == 0:
            return "0.0 B"

        # 逐级转换单位
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0

        # 超大文件
        return f"{size:.1f} PB"
    except Exception as e:
        logger.warning(f"格式化文件大小失败 {size_bytes}: {e}")
        return f"{size_bytes} B"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    格式化百分比值。

    参数:
        value: 百分比值 (0-100)
        decimals: 小数位数，默认 1

    返回:
        格式化后的百分比字符串

    示例:
        >>> format_percentage(85.567)
        '85.6%'
        >>> format_percentage(100.0)
        '100.0%'
    """
    try:
        return f"{value:.{decimals}f}%"
    except Exception as e:
        logger.warning(f"格式化百分比失败 {value}: {e}")
        return f"{value}%"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    截断长文本。

    参数:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀，默认 "..."

    返回:
        截断后的文本

    示例:
        >>> truncate_text("这是一段很长的文本内容", max_length=10)
        '这是一段很长的...'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# ==================== 错误处理包装器 ====================

def safe_api_call(
    func: Callable[..., T],
    error_message: Optional[str] = None,
    show_error: bool = True,
    default_return: Optional[T] = None
) -> Callable[..., Optional[T]]:
    """
    API 调用错误处理包装器。

    捕获 API 调用异常并显示用户友好的错误消息。
    可以用作装饰器或直接调用。

    参数:
        func: 要包装的函数
        error_message: 自定义错误消息，如果为 None 则使用默认消息
        show_error: 是否显示错误消息（使用 st.error）
        default_return: 发生错误时的默认返回值

    返回:
        包装后的函数

    示例:
        >>> @safe_api_call
        ... def fetch_data():
        ...     return api.get_data()

        >>> # 或者直接调用
        >>> result = safe_api_call(api.get_data, error_message="获取数据失败")()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 记录详细错误信息
            logger.error(f"API 调用失败 {func.__name__}: {e}", exc_info=True)

            # 显示用户友好的错误消息
            if show_error:
                msg = error_message or f"操作失败: {str(e)}"
                st.error(f"❌ {msg}")

            return default_return

    return wrapper


# ==================== 用户反馈函数 ====================

def show_success(message: str, icon: str = "✅") -> None:
    """
    显示成功消息。

    参数:
        message: 成功消息内容
        icon: 图标，默认为 ✅

    示例:
        >>> show_success("知识库创建成功")
        >>> show_success("文件上传完成", icon="📁")
    """
    if st is None:
        logger.warning("Streamlit 不可用，无法显示 UI 消息")
        logger.info(f"成功: {message}")
        return

    st.success(f"{icon} {message}")
    logger.info(f"成功: {message}")


def show_error(message: str, icon: str = "❌", details: Optional[str] = None) -> None:
    """
    显示错误消息。

    参数:
        message: 错误消息内容
        icon: 图标，默认为 ❌
        details: 详细错误信息（可选），会显示在可展开的区域中

    示例:
        >>> show_error("加载失败")
        >>> show_error("API 错误", details="连接超时: 无法连接到服务器")
    """
    error_msg = f"错误: {message} {f'- 详情: {details}' if details else ''}"
    logger.error(error_msg)

    if st is None:
        logger.warning("Streamlit 不可用，无法显示 UI 消息")
        return

    st.error(f"{icon} {message}")

    # 如果有详细信息，显示在可展开区域
    if details:
        with st.expander("查看详细错误信息"):
            st.code(details, language="text")


def show_warning(message: str, icon: str = "⚠️") -> None:
    """
    显示警告消息。

    参数:
        message: 警告消息内容
        icon: 图标，默认为 ⚠️

    示例:
        >>> show_warning("此操作不可撤销")
        >>> show_warning("文件格式可能不受支持", icon="🔔")
    """
    logger.warning(f"警告: {message}")

    if st is None:
        logger.warning("Streamlit 不可用，无法显示 UI 消息")
        return

    st.warning(f"{icon} {message}")


def show_info(message: str, icon: str = "ℹ️") -> None:
    """
    显示信息消息。

    参数:
        message: 信息消息内容
        icon: 图标，默认为 ℹ️

    示例:
        >>> show_info("暂无数据")
        >>> show_info("请先选择知识库", icon="📋")
    """
    logger.info(f"信息: {message}")

    if st is None:
        logger.warning("Streamlit 不可用，无法显示 UI 消息")
        return

    st.info(f"{icon} {message}")


def show_spinner(message: str = "处理中..."):
    """
    显示加载旋转器上下文管理器。

    参数:
        message: 加载消息，默认为 "处理中..."

    返回:
        Streamlit spinner 上下文管理器（如果 streamlit 可用）
        否则返回一个空的上下文管理器

    示例:
        >>> with show_spinner("正在上传文件..."):
        ...     upload_files()
    """
    if st is None:
        # 返回一个空的上下文管理器
        from contextlib import nullcontext
        return nullcontext()

    return st.spinner(message)


# ==================== 输入验证函数 ====================

def validate_kb_name(name: str) -> tuple[bool, Optional[str]]:
    """
    验证知识库名称。

    检查名称是否符合要求：
    - 不能为空
    - 长度在 1-100 字符之间
    - 不能包含特殊字符 (/, \\, :, *, ?, ", <, >, |)

    参数:
        name: 知识库名称

    返回:
        (is_valid, error_message) 元组
        - is_valid: 是否有效
        - error_message: 错误消息（如果无效）

    示例:
        >>> validate_kb_name("我的知识库")
        (True, None)
        >>> validate_kb_name("")
        (False, '知识库名称不能为空')
        >>> validate_kb_name("a" * 101)
        (False, '知识库名称长度不能超过 100 个字符')
    """
    # 检查是否为空
    if not name or not name.strip():
        return False, "知识库名称不能为空"

    # 检查长度
    if len(name) > 100:
        return False, "知识库名称长度不能超过 100 个字符"

    # 检查特殊字符
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            return False, f"知识库名称不能包含特殊字符: {', '.join(invalid_chars)}"

    return True, None


def validate_file_upload(
    uploaded_files: List[Any],
    allowed_extensions: Optional[List[str]] = None,
    max_file_size: Optional[int] = None,
    max_files: Optional[int] = None
) -> tuple[bool, Optional[str]]:
    """
    验证文件上传。

    检查上传的文件是否符合要求：
    - 文件数量限制
    - 文件类型限制
    - 文件大小限制

    参数:
        uploaded_files: 上传的文件列表
        allowed_extensions: 允许的文件扩展名列表，如 ['.pdf', '.txt']
        max_file_size: 单个文件最大大小（字节），None 表示不限制
        max_files: 最大文件数量，None 表示不限制

    返回:
        (is_valid, error_message) 元组
        - is_valid: 是否有效
        - error_message: 错误消息（如果无效）

    示例:
        >>> files = [uploaded_file1, uploaded_file2]
        >>> validate_file_upload(files, allowed_extensions=['.pdf'], max_files=10)
        (True, None)
    """
    # 检查是否有文件
    if not uploaded_files:
        return False, "请选择要上传的文件"

    # 检查文件数量
    if max_files and len(uploaded_files) > max_files:
        return False, f"一次最多上传 {max_files} 个文件，当前选择了 {len(uploaded_files)} 个"

    # 检查每个文件
    for file in uploaded_files:
        # 检查文件类型
        if allowed_extensions:
            file_ext = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
            if file_ext not in [ext.lower() for ext in allowed_extensions]:
                return False, f"文件 {file.name} 类型不支持。支持的类型: {', '.join(allowed_extensions)}"

        # 检查文件大小
        if max_file_size and hasattr(file, 'size'):
            if file.size > max_file_size:
                max_size_str = format_file_size(max_file_size)
                file_size_str = format_file_size(file.size)
                return False, f"文件 {file.name} 大小 ({file_size_str}) 超过限制 ({max_size_str})"

    return True, None


def validate_chunk_config(chunk_size: int, chunk_overlap: int) -> tuple[bool, Optional[str]]:
    """
    验证文本分块配置。

    参数:
        chunk_size: 分块大小
        chunk_overlap: 分块重叠大小

    返回:
        (is_valid, error_message) 元组

    示例:
        >>> validate_chunk_config(500, 50)
        (True, None)
        >>> validate_chunk_config(100, 200)
        (False, '分块重叠不能大于分块大小')
    """
    if chunk_size <= 0:
        return False, "分块大小必须大于 0"

    if chunk_overlap < 0:
        return False, "分块重叠不能为负数"

    if chunk_overlap >= chunk_size:
        return False, "分块重叠不能大于或等于分块大小"

    if chunk_size > 10000:
        return False, "分块大小不建议超过 10000"

    return True, None


def validate_retrieval_config(
    top_k: int,
    similarity_threshold: float
) -> tuple[bool, Optional[str]]:
    """
    验证检索配置。

    参数:
        top_k: 返回结果数量
        similarity_threshold: 相似度阈值 (0-1)

    返回:
        (is_valid, error_message) 元组

    示例:
        >>> validate_retrieval_config(5, 0.7)
        (True, None)
        >>> validate_retrieval_config(0, 0.7)
        (False, 'top_k 必须大于 0')
    """
    if top_k <= 0:
        return False, "top_k 必须大于 0"

    if top_k > 100:
        return False, "top_k 不建议超过 100"

    if not 0 <= similarity_threshold <= 1:
        return False, "相似度阈值必须在 0 和 1 之间"

    return True, None


# ==================== UI 组件辅助函数 ====================

def render_status_badge(
    status: str,
    status_colors: Optional[Dict[str, str]] = None
) -> None:
    """
    渲染状态徽章。

    参数:
        status: 状态文本
        status_colors: 状态颜色映射字典，格式为 {status: color}
                      默认颜色: success=green, error=red, processing=orange, pending=gray

    示例:
        >>> render_status_badge("success")
        >>> render_status_badge("处理中", {"处理中": "orange"})
    """
    if st is None:
        logger.warning("Streamlit 不可用，无法显示状态徽章")
        logger.info(f"状态: {status}")
        return

    # 默认颜色映射
    default_colors = {
        'success': 'green',
        'completed': 'green',
        'error': 'red',
        'failed': 'red',
        'processing': 'orange',
        'pending': 'gray',
        'warning': 'orange'
    }

    # 合并自定义颜色
    colors = {**default_colors, **(status_colors or {})}

    # 获取颜色
    color = colors.get(status.lower(), 'blue')

    # 渲染徽章
    st.markdown(
        f'<span style="background-color: {color}; color: white; '
        f'padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">'
        f'{status}</span>',
        unsafe_allow_html=True
    )


def create_progress_bar(current: int, total: int, label: str = "") -> None:
    """
    创建进度条。

    参数:
        current: 当前进度值
        total: 总进度值
        label: 进度条标签

    示例:
        >>> create_progress_bar(3, 10, "上传进度")
    """
    if total <= 0:
        total = 1

    progress = min(current / total, 1.0)

    if st is None:
        logger.warning("Streamlit 不可用，无法显示进度条")
        logger.info(f"进度: {current}/{total} ({format_percentage(progress * 100)})")
        return

    if label:
        st.write(label)

    st.progress(progress)
    st.caption(f"{current} / {total} ({format_percentage(progress * 100)})")


# ==================== 导出所有公共函数 ====================

__all__ = [
    # 格式化工具
    'format_datetime',
    'format_file_size',
    'format_percentage',
    'truncate_text',

    # 错误处理
    'safe_api_call',

    # 用户反馈
    'show_success',
    'show_error',
    'show_warning',
    'show_info',
    'show_spinner',

    # 输入验证
    'validate_kb_name',
    'validate_file_upload',
    'validate_chunk_config',
    'validate_retrieval_config',

    # UI 组件
    'render_status_badge',
    'create_progress_bar',
]
