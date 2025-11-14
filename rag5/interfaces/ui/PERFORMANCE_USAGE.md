# UI 性能优化使用指南

## 概述

`performance.py` 模块提供了 Streamlit UI 应用的性能优化功能，包括缓存、懒加载和状态优化等策略。

## 功能模块

### 1. 缓存策略（Caching Strategy）

使用 Streamlit 的 `@st.cache_data` 装饰器缓存 API 响应，减少重复调用。

#### 函数说明

| 函数 | 缓存时间 | 用途 |
|------|---------|------|
| `get_knowledge_bases_cached()` | 60 秒（可配置） | 缓存知识库列表 |
| `get_kb_files_cached()` | 30 秒 | 缓存文件列表 |

#### 使用示例

```python
from rag5.interfaces.ui.performance import get_knowledge_bases_cached, get_kb_files_cached
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient

# 初始化 API 客户端
api_client = KnowledgeBaseAPIClient()

# 使用缓存获取知识库列表
response = get_knowledge_bases_cached(api_client)
kbs = response.get("items", [])

# 使用缓存获取文件列表
files_response = get_kb_files_cached(api_client, kb_id="kb_123")
files = files_response.get("items", [])
```

#### 优势

- ✅ 自动缓存，减少 API 调用
- ✅ 可配置的 TTL（生存时间）
- ✅ Streamlit 原生支持，稳定可靠

### 2. 状态优化器（StateOptimizer）

优化 Streamlit 状态管理和页面重载。

#### 方法说明

| 方法 | 功能 |
|------|------|
| `mark_for_rerun(key)` | 标记需要重新运行页面 |
| `should_rerun(key)` | 检查是否需要重新运行 |
| `cache_api_response(key, response)` | 在 session_state 中缓存响应 |
| `get_cached_response(key)` | 获取缓存的响应 |
| `clear_cache(key=None)` | 清除缓存 |

#### 使用示例

##### 优化页面重载

```python
from rag5.interfaces.ui.performance import StateOptimizer
import streamlit as st

# 在数据更新后标记需要重新运行
def update_data():
    # 更新数据逻辑
    StateOptimizer.mark_for_rerun("data_updated")

# 检查是否需要重新运行
if StateOptimizer.should_rerun("data_updated"):
    st.rerun()
```

##### 缓存 API 响应

```python
from rag5.interfaces.ui.performance import StateOptimizer

# 先检查缓存
cached_response = StateOptimizer.get_cached_response("kb_list")

if cached_response is None:
    # 缓存未命中，调用 API
    response = api_client.list_knowledge_bases()
    # 缓存响应
    StateOptimizer.cache_api_response("kb_list", response)
else:
    # 使用缓存的响应
    response = cached_response
```

##### 清除缓存

```python
from rag5.interfaces.ui.performance import StateOptimizer

# 清除特定缓存
StateOptimizer.clear_cache("kb_list")

# 清除所有缓存
StateOptimizer.clear_cache()
```

### 3. 懒加载器（LazyLoader）

实现懒加载策略，按需加载数据。

#### 方法说明

| 方法 | 功能 |
|------|------|
| `should_load_page(page, loaded_pages)` | 判断是否需要加载页面 |
| `mark_page_loaded(page, loaded_pages)` | 标记页面已加载 |
| `get_loaded_pages_key(prefix)` | 获取已加载页面的键名 |
| `init_loaded_pages(prefix)` | 初始化已加载页面集合 |

#### 使用示例

```python
from rag5.interfaces.ui.performance import LazyLoader
import streamlit as st

# 初始化已加载页面集合
LazyLoader.init_loaded_pages("kb_list")

# 获取已加载页面
key = LazyLoader.get_loaded_pages_key("kb_list")
loaded_pages = st.session_state.get(key, set())

# 当前页码
current_page = st.session_state.get("current_page", 1)

# 检查是否需要加载
if LazyLoader.should_load_page(current_page, loaded_pages):
    # 加载数据
    response = api_client.list_knowledge_bases(page=current_page)

    # 标记已加载
    LazyLoader.mark_page_loaded(current_page, loaded_pages)
    st.session_state[key] = loaded_pages
```

### 4. 性能监控器（PerformanceMonitor）

监控缓存命中率，识别性能瓶颈。

#### 方法说明

| 方法 | 功能 |
|------|------|
| `log_cache_hit(key)` | 记录缓存命中 |
| `log_cache_miss(key)` | 记录缓存未命中 |
| `get_cache_stats()` | 获取缓存统计信息 |

#### 使用示例

```python
from rag5.interfaces.ui.performance import PerformanceMonitor, StateOptimizer

# 检查缓存并记录统计
cached_response = StateOptimizer.get_cached_response("kb_list")

if cached_response is not None:
    # 缓存命中
    PerformanceMonitor.log_cache_hit("kb_list")
    response = cached_response
else:
    # 缓存未命中
    PerformanceMonitor.log_cache_miss("kb_list")
    response = api_client.list_knowledge_bases()
    StateOptimizer.cache_api_response("kb_list", response)

# 查看统计信息
stats = PerformanceMonitor.get_cache_stats()
print(f"缓存命中: {stats['hits']}")
print(f"缓存未命中: {stats['misses']}")
```

## 完整实例

### 优化知识库列表页面

```python
import streamlit as st
from rag5.interfaces.ui.performance import (
    get_knowledge_bases_cached,
    StateOptimizer,
    LazyLoader,
    PerformanceMonitor
)
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient
from rag5.interfaces.ui.config import config

def render_kb_list_page():
    """渲染知识库列表页面（优化版）"""

    st.title("📚 知识库管理")

    # 初始化 API 客户端
    api_client = KnowledgeBaseAPIClient(
        base_url=config.API_BASE_URL,
        timeout=config.API_TIMEOUT
    )

    # 使用缓存获取知识库列表
    try:
        with st.spinner("加载知识库列表..."):
            # 先检查 session_state 缓存
            cached_response = StateOptimizer.get_cached_response("kb_list")

            if cached_response is not None:
                # 缓存命中
                PerformanceMonitor.log_cache_hit("kb_list")
                response = cached_response
            else:
                # 缓存未命中，使用 Streamlit 缓存
                PerformanceMonitor.log_cache_miss("kb_list")
                response = get_knowledge_bases_cached(api_client)
                StateOptimizer.cache_api_response("kb_list", response)

            kbs = response.get("items", [])
            total_pages = response.get("pages", 1)
    except Exception as e:
        st.error(f"加载失败: {str(e)}")
        return

    # 显示知识库卡片
    if not kbs:
        st.info("暂无知识库")
        return

    # 使用配置的页面大小
    page_size = config.PAGE_SIZE

    # 3 列网格布局
    for i in range(0, len(kbs), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(kbs):
                kb = kbs[i + j]
                with col:
                    render_kb_card(kb)

    # 检查是否需要重新运行
    if StateOptimizer.should_rerun("kb_list_updated"):
        st.rerun()
```

### 优化文件列表页面

```python
def render_file_list(kb_id: str):
    """渲染文件列表（优化版）"""

    api_client = KnowledgeBaseAPIClient()

    # 初始化懒加载
    LazyLoader.init_loaded_pages(f"files_{kb_id}")
    key = LazyLoader.get_loaded_pages_key(f"files_{kb_id}")
    loaded_pages = st.session_state.get(key, set())

    # 当前页码
    current_page = st.session_state.get("file_list_page", 1)

    # 检查是否需要加载
    if LazyLoader.should_load_page(current_page, loaded_pages):
        # 使用缓存获取文件列表
        try:
            response = get_kb_files_cached(api_client, kb_id)
            files = response.get("items", [])

            # 标记已加载
            LazyLoader.mark_page_loaded(current_page, loaded_pages)
            st.session_state[key] = loaded_pages
        except Exception as e:
            st.error(f"加载文件列表失败: {str(e)}")
            return

    # 显示文件列表
    # ...
```

## 性能优化最佳实践

### 1. 合理使用缓存

- ✅ 对频繁访问的数据使用缓存
- ✅ 根据数据更新频率设置合适的 TTL
- ✅ 在数据更新后及时清除相关缓存
- ❌ 不要缓存过大的数据集
- ❌ 不要缓存敏感信息

### 2. 优化页面重载

- ✅ 使用 `StateOptimizer` 控制 `st.rerun()` 调用
- ✅ 只在必要时重新运行页面
- ✅ 批量更新状态后再重载
- ❌ 避免在循环中调用 `st.rerun()`
- ❌ 避免无条件的页面重载

### 3. 实施懒加载

- ✅ 对大型列表使用分页
- ✅ 按需加载详细信息
- ✅ 使用虚拟滚动处理长列表
- ❌ 避免一次性加载所有数据
- ❌ 避免预加载不常用的数据

### 4. 监控性能

- ✅ 定期查看缓存统计
- ✅ 识别缓存命中率低的地方
- ✅ 优化高频调用的 API
- ✅ 记录性能瓶颈
- ❌ 不要过度监控影响性能

## 常见问题

### Q1: 缓存何时失效？

**A:** 缓存有两种失效方式：
1. TTL 到期自动失效
2. 手动调用 `clear_cache()` 清除

### Q2: 如何调整缓存时间？

**A:** 通过环境变量设置：
```bash
export CACHE_TTL=120  # 设置为 120 秒
```

或直接在缓存装饰器中指定：
```python
@st.cache_data(ttl=120)  # 120 秒
def my_cached_function():
    pass
```

### Q3: 懒加载适用于什么场景？

**A:** 适用场景：
- 大型数据列表（100+ 项）
- 分页展示
- 树形结构的展开
- 图片/文件的延迟加载

### Q4: 如何处理缓存一致性？

**A:** 在数据更新后清除相关缓存：
```python
# 更新数据后
api_client.update_knowledge_base(kb_id, data)

# 清除缓存
StateOptimizer.clear_cache("kb_list")
get_knowledge_bases_cached.clear()  # 清除 Streamlit 缓存

# 标记需要重新运行
StateOptimizer.mark_for_rerun("kb_list_updated")
```

## 测试

运行性能优化模块测试：

```bash
# 运行所有测试
pytest tests/test_interfaces/test_ui_performance.py -v

# 运行特定测试类
pytest tests/test_interfaces/test_ui_performance.py::TestStateOptimizer -v
pytest tests/test_interfaces/test_ui_performance.py::TestLazyLoader -v
pytest tests/test_interfaces/test_ui_performance.py::TestPerformanceMonitor -v
```

## 参考链接

- [Streamlit Caching](https://docs.streamlit.io/library/advanced-features/caching)
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)
- [Streamlit Performance](https://docs.streamlit.io/library/advanced-features/performance)
