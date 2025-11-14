# 知识库组件使用指南

## 概述

`components.py` 模块提供了知识库管理页面所需的通用工具函数和 UI 组件。

## 环境要求

```bash
# 安装 Streamlit（如果还没有）
pip install streamlit

# 或安装完整依赖
pip install -r requirements.txt
```

## 组件列表

### 1. 格式化工具函数

```python
from rag5.interfaces.ui.pages.knowledge_base.components import (
    format_datetime,
    format_file_size,
    format_percentage,
    truncate_text
)

# 日期时间格式化
formatted = format_datetime("2024-01-15T10:30:00Z")
# 输出: "2024-01-15 10:30"

# 文件大小格式化
size = format_file_size(1048576)
# 输出: "1.0 MB"

# 百分比格式化
percent = format_percentage(85.567)
# 输出: "85.6%"

# 文本截断
short = truncate_text("很长的文本...", max_length=10)
# 输出: "很长的文本..."
```

### 2. 用户反馈函数

```python
from rag5.interfaces.ui.pages.knowledge_base.components import (
    show_success,
    show_error,
    show_warning,
    show_info,
    show_spinner
)

# 在 Streamlit 应用中使用
show_success("知识库创建成功！")
show_error("加载失败", details="连接超时")
show_warning("此操作不可撤销")
show_info("暂无数据")

# 使用加载旋转器
with show_spinner("正在处理..."):
    # 执行耗时操作
    process_files()
```

### 3. 输入验证函数

```python
from rag5.interfaces.ui.pages.knowledge_base.components import (
    validate_kb_name,
    validate_file_upload,
    validate_chunk_config,
    validate_retrieval_config
)

# 验证知识库名称
valid, error = validate_kb_name("我的知识库")
if not valid:
    st.error(error)

# 验证文件上传
valid, error = validate_file_upload(
    uploaded_files,
    allowed_extensions=['.pdf', '.txt'],
    max_file_size=10 * 1024 * 1024,  # 10 MB
    max_files=10
)

# 验证分块配置
valid, error = validate_chunk_config(chunk_size=500, chunk_overlap=50)

# 验证检索配置
valid, error = validate_retrieval_config(top_k=5, similarity_threshold=0.7)
```

### 4. UI 组件

```python
from rag5.interfaces.ui.pages.knowledge_base.components import (
    render_status_badge,
    create_progress_bar
)

# 渲染状态徽章
render_status_badge("success")  # 绿色徽章
render_status_badge("error")    # 红色徽章
render_status_badge("processing")  # 橙色徽章

# 创建进度条
create_progress_bar(
    current=30,
    total=100,
    label="上传进度"
)
```

## 测试组件

### 方式 1: 运行演示应用

```bash
# 启动 Streamlit 演示应用
streamlit run test_components_demo.py
```

这将打开一个交互式演示页面，展示所有组件的功能。

### 方式 2: 在实际 UI 中测试

```bash
# 启动知识库管理 UI
python scripts/run_ui.py
# 或
rag5-ui
```

导航到知识库管理页面，所有组件都已集成到实际界面中。

### 方式 3: Python 脚本测试

```python
# test_components.py
from rag5.interfaces.ui.pages.knowledge_base.components import *

# 测试格式化函数
assert format_file_size(1024) == "1.0 KB"
assert format_percentage(50.5) == "50.5%"

# 测试验证函数
valid, _ = validate_kb_name("测试")
assert valid is True

valid, error = validate_kb_name("")
assert valid is False

print("✅ 所有测试通过！")
```

## 在页面中使用

### 示例：在知识库详情页中使用

```python
# rag5/interfaces/ui/pages/knowledge_base/detail.py

from .components import (
    format_datetime,
    format_file_size,
    show_success,
    show_error,
    validate_chunk_config,
)

def render_kb_settings_tab(kb, api_client):
    """渲染知识库设置标签页"""

    # 使用表单
    with st.form("kb_settings"):
        chunk_size = st.number_input("分块大小", value=500)
        chunk_overlap = st.number_input("分块重叠", value=50)

        submitted = st.form_submit_button("保存设置")

        if submitted:
            # 验证配置
            valid, error = validate_chunk_config(chunk_size, chunk_overlap)
            if not valid:
                show_error(f"配置无效: {error}")
                return

            try:
                # 保存设置
                api_client.update_knowledge_base(kb['id'], {
                    'chunk_size': chunk_size,
                    'chunk_overlap': chunk_overlap
                })
                show_success("设置保存成功！")
            except Exception as e:
                show_error("保存失败", details=str(e))
```

## 设计原则

### 1. 可选的 Streamlit 依赖

组件被设计为即使在没有 Streamlit 的环境中也能工作（格式化和验证函数）。UI 反馈函数在没有 Streamlit 时会使用日志记录。

```python
# 这些函数在任何环境都能工作
format_datetime("2024-01-15T10:30:00Z")
validate_kb_name("测试")

# 这些函数需要 Streamlit
show_success("消息")  # 如果没有 Streamlit，会记录到日志
```

### 2. 完整的类型注解

所有函数都有完整的类型提示，便于 IDE 自动补全和类型检查。

```python
def format_file_size(size_bytes: Union[int, float]) -> str:
    ...

def validate_kb_name(name: str) -> tuple[bool, Optional[str]]:
    ...
```

### 3. 详细的文档字符串

每个函数都有详细的中文文档字符串，包括参数说明、返回值、示例等。

## 故障排查

### 问题：导入 Streamlit 失败

```bash
# 解决方案：安装 Streamlit
pip install streamlit
```

### 问题：UI 组件不显示

确保在 Streamlit 应用上下文中调用 UI 函数：

```python
# ❌ 错误 - 在普通 Python 脚本中
show_success("消息")  # 不会显示 UI

# ✅ 正确 - 在 Streamlit 应用中
# app.py
import streamlit as st
from components import show_success

st.title("我的应用")
show_success("欢迎！")  # 会正确显示
```

### 问题：验证函数返回意外结果

检查输入类型和值：

```python
# 确保传入正确类型
validate_chunk_config(500, 50)  # ✅ 正确
validate_chunk_config("500", "50")  # ❌ 错误 - 应该是数字

# 检查返回值
valid, error = validate_kb_name("")
if not valid:
    print(f"验证失败: {error}")  # 打印错误信息
```

## 扩展组件

如需添加新组件：

1. **添加函数到 `components.py`**
2. **添加到 `__all__` 导出列表**
3. **更新本文档**
4. **添加测试到 `tests/test_interfaces/test_kb_components.py`**

示例：

```python
# components.py

def new_component(param: str) -> str:
    """
    新组件说明。

    参数:
        param: 参数说明

    返回:
        返回值说明

    示例:
        >>> new_component("test")
        'result'
    """
    # 实现
    return "result"

# 添加到导出列表
__all__ = [
    # ...
    'new_component',
]
```

## 参考资料

- [Streamlit 文档](https://docs.streamlit.io/)
- [Python 类型注解](https://docs.python.org/3/library/typing.html)
- 项目 README: `/home/user/rag5-simplified-001/README.md`
