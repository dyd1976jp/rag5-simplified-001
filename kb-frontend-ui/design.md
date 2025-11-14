# Knowledge Base Frontend UI Design Document

## Overview

本设计文档描述如何在现有的 rag5-simplified Streamlit UI 基础上扩展知识库管理功能。设计遵循 Streamlit 的最佳实践，保持与现有聊天界面的一致性，同时参考 PAI-RAG 的功能模式。

### Key Design Principles

1. **渐进式增强**: 在不破坏现有聊天功能的前提下添加知识库管理
2. **组件复用**: 最大化利用 Streamlit 原生组件
3. **状态管理**: 使用 SessionState 统一管理应用状态
4. **用户体验**: 提供清晰的导航和即时反馈
5. **API 集成**: 与现有 FastAPI 后端无缝集成

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit Application                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Chat Page   │  │   KB List    │  │  KB Detail   │     │
│  │  (existing)  │  │    Page      │  │    Page      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                   ┌────────▼────────┐                       │
│                   │  SessionState   │                       │
│                   │    Manager      │                       │
│                   └────────┬────────┘                       │
└────────────────────────────┼──────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   FastAPI       │
                    │   Backend       │
                    └─────────────────┘
```

### Page Navigation Flow

```
Main App (app.py)
    │
    ├─► Chat Page (default)
    │   └─► KB Selector in Sidebar
    │
    └─► Knowledge Base Management
        ├─► KB List Page
        │   ├─► Create KB Dialog
        │   └─► Delete KB Confirmation
        │
        └─► KB Detail Page
            ├─► File Management Tab
            │   ├─► Upload Files
            │   ├─► Delete Files
            │   └─► Reprocess Files
            │
            ├─► KB Settings Tab
            │   └─► Update Configuration
            │
            └─► Retrieval Test Tab
                └─► Test Search
```

## Components and Interfaces

### 1. Application Structure


#### File Structure

```
rag5/interfaces/ui/
├── __init__.py
├── app.py                    # 主应用入口（扩展）
├── state.py                  # 会话状态管理（扩展）
├── components.py             # 通用 UI 组件（扩展）
├── pages/
│   ├── __init__.py
│   ├── chat.py              # 聊天页面（重构自 app.py）
│   └── knowledge_base/
│       ├── __init__.py
│       ├── list.py          # 知识库列表页面
│       ├── detail.py        # 知识库详情页面
│       ├── components.py    # 知识库专用组件
│       └── api_client.py    # API 客户端封装
```

#### Main Application (app.py)

```python
"""
主应用入口，负责页面路由和导航。
"""

def main():
    setup_page()
    SessionState.initialize()
    
    # 侧边栏导航
    page = st.sidebar.radio(
        "导航",
        ["💬 聊天", "📚 知识库管理"],
        key="navigation"
    )
    
    if page == "💬 聊天":
        render_chat_page()
    else:
        render_kb_management()
```

### 2. Session State Management

#### Extended SessionState Class

```python
class SessionState:
    """扩展的会话状态管理器"""
    
    # 现有方法保持不变
    # ... existing methods ...
    
    # 新增知识库管理相关方法
    @staticmethod
    def get_current_page() -> str:
        """获取当前页面"""
        if "current_page" not in st.session_state:
            st.session_state.current_page = "kb_list"
        return st.session_state.current_page
    
    @staticmethod
    def set_current_page(page: str):
        """设置当前页面"""
        st.session_state.current_page = page
    
    @staticmethod
    def get_selected_kb() -> Optional[str]:
        """获取选中的知识库 ID"""
        return st.session_state.get("selected_kb_id", None)
    
    @staticmethod
    def set_selected_kb(kb_id: str):
        """设置选中的知识库"""
        st.session_state.selected_kb_id = kb_id
    
    @staticmethod
    def get_kb_for_chat() -> Optional[str]:
        """获取聊天使用的知识库 ID"""
        return st.session_state.get("chat_kb_id", None)
    
    @staticmethod
    def set_kb_for_chat(kb_id: Optional[str]):
        """设置聊天使用的知识库"""
        st.session_state.chat_kb_id = kb_id
```

### 3. API Client

#### KnowledgeBaseAPIClient

```python
class KnowledgeBaseAPIClient:
    """知识库 API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
    
    def list_knowledge_bases(
        self, 
        page: int = 1, 
        size: int = 10
    ) -> Dict:
        """获取知识库列表"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases"
        params = {"page": page, "size": size}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_knowledge_base(self, kb_id: str) -> Dict:
        """获取知识库详情"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases/{kb_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def create_knowledge_base(self, kb_data: Dict) -> Dict:
        """创建知识库"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases"
        response = requests.post(url, json=kb_data)
        response.raise_for_status()
        return response.json()
    
    def update_knowledge_base(self, kb_id: str, kb_data: Dict) -> Dict:
        """更新知识库"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases/{kb_id}"
        response = requests.put(url, json=kb_data)
        response.raise_for_status()
        return response.json()
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases/{kb_id}"
        response = requests.delete(url)
        response.raise_for_status()
        return True
    
    def list_files(
        self, 
        kb_id: str, 
        page: int = 1, 
        size: int = 10,
        status: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict:
        """获取文件列表"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases/{kb_id}/files"
        params = {"page": page, "size": size}
        if status:
            params["status"] = status
        if query:
            params["query"] = query
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def upload_files(self, kb_id: str, files: List) -> Dict:
        """上传文件"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases/{kb_id}/files"
        files_data = [("files", file) for file in files]
        response = requests.post(url, files=files_data)
        response.raise_for_status()
        return response.json()
    
    def delete_file(self, kb_id: str, file_id: str) -> bool:
        """删除文件"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases/{kb_id}/files/{file_id}"
        response = requests.delete(url)
        response.raise_for_status()
        return True
    
    def query_knowledge_base(
        self, 
        kb_id: str, 
        query: str,
        top_k: Optional[int] = None
    ) -> Dict:
        """查询知识库"""
        url = f"{self.base_url}{self.api_prefix}/knowledge-bases/{kb_id}/query"
        data = {"query": query}
        if top_k:
            data["top_k"] = top_k
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
```

### 4. Knowledge Base List Page


#### KB List Page Component

```python
def render_kb_list_page(api_client: KnowledgeBaseAPIClient):
    """渲染知识库列表页面"""
    
    st.title("📚 知识库管理")
    
    # 顶部操作栏
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("管理您的知识库和文档")
    with col2:
        if st.button("➕ 新建知识库", use_container_width=True):
            SessionState.set_current_page("kb_create")
            st.rerun()
    
    # 获取知识库列表
    try:
        with st.spinner("加载知识库列表..."):
            response = api_client.list_knowledge_bases(
                page=st.session_state.get("kb_list_page", 1),
                size=9  # 3x3 grid
            )
            kbs = response.get("items", [])
            total_pages = response.get("pages", 1)
    except Exception as e:
        st.error(f"加载失败: {str(e)}")
        return
    
    # 显示知识库卡片
    if not kbs:
        st.info("暂无知识库，点击上方按钮创建第一个知识库")
        return
    
    # 3列网格布局
    for i in range(0, len(kbs), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(kbs):
                kb = kbs[i + j]
                with col:
                    render_kb_card(kb, api_client)
    
    # 分页控件
    if total_pages > 1:
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            current_page = st.session_state.get("kb_list_page", 1)
            new_page = st.number_input(
                "页码",
                min_value=1,
                max_value=total_pages,
                value=current_page,
                key="page_selector"
            )
            if new_page != current_page:
                st.session_state.kb_list_page = new_page
                st.rerun()


def render_kb_card(kb: Dict, api_client: KnowledgeBaseAPIClient):
    """渲染单个知识库卡片"""
    
    with st.container(border=True):
        # 标题和描述
        st.subheader(kb["name"])
        st.caption(kb.get("description", "暂无描述"))
        
        # 元信息
        st.text(f"ID: {kb['id'][:8]}...")
        st.text(f"更新: {format_datetime(kb['updated_at'])}")
        
        # 操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("查看", key=f"view_{kb['id']}", use_container_width=True):
                SessionState.set_selected_kb(kb['id'])
                SessionState.set_current_page("kb_detail")
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"delete_{kb['id']}", use_container_width=True):
                show_delete_confirmation(kb, api_client)


@st.dialog("确认删除")
def show_delete_confirmation(kb: Dict, api_client: KnowledgeBaseAPIClient):
    """显示删除确认对话框"""
    
    st.warning(f"确定要删除知识库 **{kb['name']}** 吗？")
    st.error("此操作不可撤销，将删除所有相关文件和数据！")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("取消", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("确认删除", type="primary", use_container_width=True):
            try:
                api_client.delete_knowledge_base(kb['id'])
                st.success("删除成功")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"删除失败: {str(e)}")


@st.dialog("创建知识库")
def render_create_kb_dialog(api_client: KnowledgeBaseAPIClient):
    """渲染创建知识库对话框"""
    
    st.subheader("新建知识库")
    
    # 基本信息
    name = st.text_input("知识库名称*", placeholder="例如：产品文档")
    description = st.text_area("描述", placeholder="描述知识库内容（可选）")
    
    # 切片配置
    st.divider()
    st.markdown("**切片配置**")
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.number_input("切片大小", min_value=100, max_value=2000, value=1000)
    with col2:
        chunk_overlap = st.number_input("切片重叠", min_value=0, max_value=200, value=50)
    
    # 向量模型
    st.divider()
    st.markdown("**向量模型**")
    embedding_model = st.selectbox(
        "选择向量模型",
        ["BAAI/bge-m3", "BAAI/bge-small-zh-v1.5"]
    )
    
    # 检索配置
    st.divider()
    st.markdown("**检索配置**")
    col1, col2 = st.columns(2)
    with col1:
        top_k = st.slider("Top-K", min_value=1, max_value=20, value=5)
    with col2:
        similarity_threshold = st.slider(
            "相似度阈值", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.3,
            step=0.01
        )
    
    retrieval_mode = st.radio(
        "检索策略",
        ["vector", "fulltext", "hybrid"],
        format_func=lambda x: {"vector": "向量检索", "fulltext": "全文检索", "hybrid": "混合检索"}[x]
    )
    
    # 提交按钮
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("取消", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("创建", type="primary", use_container_width=True):
            if not name:
                st.error("请输入知识库名称")
                return
            
            try:
                kb_data = {
                    "name": name,
                    "description": description,
                    "embedding_model": embedding_model,
                    "chunk_config": {
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    },
                    "retrieval_config": {
                        "retrieval_mode": retrieval_mode,
                        "top_k": top_k,
                        "similarity_threshold": similarity_threshold
                    }
                }
                
                result = api_client.create_knowledge_base(kb_data)
                st.success("创建成功！")
                time.sleep(1)
                SessionState.set_selected_kb(result['id'])
                SessionState.set_current_page("kb_detail")
                st.rerun()
            except Exception as e:
                st.error(f"创建失败: {str(e)}")
```

### 5. Knowledge Base Detail Page


#### KB Detail Page Component

```python
def render_kb_detail_page(api_client: KnowledgeBaseAPIClient):
    """渲染知识库详情页面"""
    
    kb_id = SessionState.get_selected_kb()
    if not kb_id:
        st.error("未选择知识库")
        return
    
    # 获取知识库信息
    try:
        kb = api_client.get_knowledge_base(kb_id)
    except Exception as e:
        st.error(f"加载失败: {str(e)}")
        return
    
    # 顶部导航和信息
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← 返回列表"):
            SessionState.set_current_page("kb_list")
            st.rerun()
    
    with col2:
        st.title(kb["name"])
        st.caption(f"ID: {kb['id']} | 描述: {kb.get('description', '暂无')}")
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📁 文件管理", "⚙️ 知识库设置", "🔍 检索测试"])
    
    with tab1:
        render_file_management_tab(kb_id, api_client)
    
    with tab2:
        render_kb_settings_tab(kb, api_client)
    
    with tab3:
        render_retrieval_test_tab(kb_id, api_client)


def render_file_management_tab(kb_id: str, api_client: KnowledgeBaseAPIClient):
    """渲染文件管理标签页"""
    
    # 文件上传
    st.subheader("上传文件")
    uploaded_files = st.file_uploader(
        "选择文件",
        accept_multiple_files=True,
        type=["txt", "md", "pdf", "docx"],
        key="file_uploader"
    )
    
    if uploaded_files:
        if st.button("开始上传", type="primary"):
            with st.spinner("上传中..."):
                try:
                    api_client.upload_files(kb_id, uploaded_files)
                    st.success(f"成功上传 {len(uploaded_files)} 个文件")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"上传失败: {str(e)}")
    
    st.divider()
    
    # 文件列表
    st.subheader("文件列表")
    
    # 筛选和搜索
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_query = st.text_input("搜索文件名", key="file_search")
    with col2:
        status_filter = st.selectbox(
            "状态筛选",
            ["all", "pending", "parsing", "persisting", "succeeded", "failed"],
            format_func=lambda x: {
                "all": "全部",
                "pending": "等待中",
                "parsing": "解析中",
                "persisting": "索引中",
                "succeeded": "成功",
                "failed": "失败"
            }[x]
        )
    with col3:
        if st.button("🔄 刷新"):
            st.rerun()
    
    # 获取文件列表
    try:
        response = api_client.list_files(
            kb_id,
            page=st.session_state.get("file_list_page", 1),
            size=10,
            status=None if status_filter == "all" else status_filter,
            query=search_query if search_query else None
        )
        files = response.get("items", [])
        total_pages = response.get("pages", 1)
    except Exception as e:
        st.error(f"加载文件列表失败: {str(e)}")
        return
    
    if not files:
        st.info("暂无文件")
        return
    
    # 显示文件表格
    for file in files:
        render_file_row(file, kb_id, api_client)
    
    # 分页
    if total_pages > 1:
        st.divider()
        current_page = st.session_state.get("file_list_page", 1)
        new_page = st.number_input(
            "页码",
            min_value=1,
            max_value=total_pages,
            value=current_page,
            key="file_page_selector"
        )
        if new_page != current_page:
            st.session_state.file_list_page = new_page
            st.rerun()


def render_file_row(file: Dict, kb_id: str, api_client: KnowledgeBaseAPIClient):
    """渲染单个文件行"""
    
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        
        with col1:
            st.markdown(f"**{file['file_name']}**")
            st.caption(f"大小: {format_file_size(file['file_size'])}")
        
        with col2:
            status = file['status']
            status_colors = {
                "pending": "🟡",
                "parsing": "🔵",
                "persisting": "🔵",
                "succeeded": "🟢",
                "failed": "🔴"
            }
            st.markdown(f"{status_colors.get(status, '⚪')} {status}")
        
        with col3:
            st.caption(format_datetime(file['created_at']))
        
        with col4:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if file['status'] == 'failed':
                    if st.button("🔄", key=f"reprocess_{file['id']}", help="重新处理"):
                        try:
                            # Call reprocess API
                            st.success("已加入处理队列")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"操作失败: {str(e)}")
            
            with btn_col2:
                if st.button("🗑️", key=f"del_file_{file['id']}", help="删除"):
                    try:
                        api_client.delete_file(kb_id, file['id'])
                        st.success("删除成功")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败: {str(e)}")
        
        # 显示失败原因
        if file['status'] == 'failed' and file.get('failed_reason'):
            with st.expander("查看错误详情"):
                st.error(file['failed_reason'])


def render_kb_settings_tab(kb: Dict, api_client: KnowledgeBaseAPIClient):
    """渲染知识库设置标签页"""
    
    st.subheader("知识库配置")
    
    with st.form("kb_settings_form"):
        # 基本信息
        st.markdown("**基本信息**")
        name = st.text_input("名称", value=kb["name"])
        description = st.text_area("描述", value=kb.get("description", ""))
        
        st.divider()
        
        # 切片配置
        st.markdown("**切片配置**")
        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.number_input(
                "切片大小",
                min_value=100,
                max_value=2000,
                value=kb["chunk_config"]["chunk_size"]
            )
        with col2:
            chunk_overlap = st.number_input(
                "切片重叠",
                min_value=0,
                max_value=200,
                value=kb["chunk_config"]["chunk_overlap"]
            )
        
        st.divider()
        
        # 检索配置
        st.markdown("**检索配置**")
        col1, col2 = st.columns(2)
        with col1:
            top_k = st.slider(
                "Top-K",
                min_value=1,
                max_value=20,
                value=kb["retrieval_config"]["top_k"]
            )
        with col2:
            similarity_threshold = st.slider(
                "相似度阈值",
                min_value=0.0,
                max_value=1.0,
                value=kb["retrieval_config"]["similarity_threshold"],
                step=0.01
            )
        
        retrieval_mode = st.radio(
            "检索策略",
            ["vector", "fulltext", "hybrid"],
            index=["vector", "fulltext", "hybrid"].index(
                kb["retrieval_config"]["retrieval_mode"]
            ),
            format_func=lambda x: {
                "vector": "向量检索",
                "fulltext": "全文检索",
                "hybrid": "混合检索"
            }[x]
        )
        
        # 提交按钮
        submitted = st.form_submit_button("保存设置", type="primary")
        
        if submitted:
            try:
                update_data = {
                    "name": name,
                    "description": description,
                    "chunk_config": {
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    },
                    "retrieval_config": {
                        "retrieval_mode": retrieval_mode,
                        "top_k": top_k,
                        "similarity_threshold": similarity_threshold
                    }
                }
                
                api_client.update_knowledge_base(kb["id"], update_data)
                st.success("保存成功！")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {str(e)}")


def render_retrieval_test_tab(kb_id: str, api_client: KnowledgeBaseAPIClient):
    """渲染检索测试标签页"""
    
    st.subheader("检索测试")
    st.markdown("测试知识库的检索效果")
    
    # 查询输入
    query = st.text_input("输入查询内容", placeholder="例如：什么是 RAG？")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        top_k = st.slider("返回结果数量", min_value=1, max_value=20, value=5)
    with col2:
        search_button = st.button("🔍 搜索", type="primary", use_container_width=True)
    
    if search_button and query:
        with st.spinner("搜索中..."):
            try:
                results = api_client.query_knowledge_base(kb_id, query, top_k)
                
                if not results:
                    st.info("未找到相关内容")
                    return
                
                st.success(f"找到 {len(results)} 条结果")
                
                # 显示结果
                for i, result in enumerate(results, 1):
                    with st.expander(f"结果 {i} - 相似度: {result.get('score', 0):.4f}"):
                        st.markdown(f"**内容:**")
                        st.text(result.get('content', ''))
                        
                        st.markdown(f"**元数据:**")
                        metadata = result.get('metadata', {})
                        st.json(metadata)
            
            except Exception as e:
                st.error(f"搜索失败: {str(e)}")


### 6. Chat Page Integration


#### Chat Page with KB Selector

```python
def render_chat_page():
    """渲染聊天页面（扩展版）"""
    
    # 页面标题
    render_page_header()
    
    # 侧边栏 - 知识库选择器
    with st.sidebar:
        st.divider()
        st.subheader("🎯 知识库选择")
        
        try:
            api_client = KnowledgeBaseAPIClient()
            response = api_client.list_knowledge_bases(page=1, size=100)
            kbs = response.get("items", [])
            
            kb_options = ["默认（全部）"] + [kb["name"] for kb in kbs]
            kb_ids = [None] + [kb["id"] for kb in kbs]
            
            selected_index = st.selectbox(
                "选择知识库",
                range(len(kb_options)),
                format_func=lambda i: kb_options[i],
                key="chat_kb_selector"
            )
            
            selected_kb_id = kb_ids[selected_index]
            SessionState.set_kb_for_chat(selected_kb_id)
            
            if selected_kb_id:
                st.info(f"当前使用: {kb_options[selected_index]}")
            else:
                st.info("当前使用: 全部知识库")
        
        except Exception as e:
            st.warning(f"无法加载知识库列表: {str(e)}")
    
    # 聊天界面（保持原有逻辑）
    render_chat_interface()


def handle_user_input_with_kb(prompt: str):
    """处理用户输入（支持知识库选择）"""
    
    # 输入验证
    if not prompt or not prompt.strip():
        SessionState.set_error("请输入有效的问题。")
        return None
    
    if len(prompt) > settings.max_query_length:
        SessionState.set_error(f"问题长度不能超过 {settings.max_query_length} 个字符。")
        return None
    
    # 添加用户消息
    SessionState.add_message("user", prompt)
    
    # 准备历史记录
    history = SessionState.get_history(limit=20)
    
    # 获取选定的知识库
    kb_id = SessionState.get_kb_for_chat()
    
    # 调用代理（传入知识库 ID）
    try:
        response = ask(prompt, history, kb_id=kb_id)
        return response
    except Exception as e:
        error_msg = f"抱歉，处理您的问题时出现错误：{str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
```

### 7. Utility Functions

```python
def format_datetime(dt_str: str) -> str:
    """格式化日期时间"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
```

## Error Handling

### API Error Handling

```python
def safe_api_call(func, *args, **kwargs):
    """安全的 API 调用包装器"""
    try:
        return func(*args, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error("无法连接到后端服务，请确保 API 服务正在运行")
        return None
    except requests.exceptions.Timeout:
        st.error("请求超时，请稍后重试")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("资源不存在")
        elif e.response.status_code == 400:
            st.error(f"请求参数错误: {e.response.text}")
        elif e.response.status_code == 500:
            st.error("服务器内部错误")
        else:
            st.error(f"请求失败: {str(e)}")
        return None
    except Exception as e:
        st.error(f"未知错误: {str(e)}")
        logger.exception("Unexpected error in API call")
        return None
```

### User Feedback

```python
def show_success(message: str, duration: int = 3):
    """显示成功消息"""
    st.success(message)
    if duration > 0:
        time.sleep(duration)


def show_error(message: str):
    """显示错误消息"""
    st.error(message)


def show_warning(message: str):
    """显示警告消息"""
    st.warning(message)


def show_info(message: str):
    """显示信息消息"""
    st.info(message)
```

## Testing Strategy

### Unit Tests

1. **API Client Tests**
   - Test all API methods with mocked responses
   - Test error handling for different HTTP status codes
   - Test request parameter formatting

2. **State Management Tests**
   - Test SessionState methods
   - Test state persistence across reruns
   - Test state initialization

3. **Utility Function Tests**
   - Test datetime formatting
   - Test file size formatting
   - Test data validation

### Integration Tests

1. **Page Navigation Tests**
   - Test navigation between pages
   - Test state preservation during navigation
   - Test back button functionality

2. **File Upload Tests**
   - Test single file upload
   - Test multiple file upload
   - Test file type validation
   - Test upload error handling

3. **KB CRUD Tests**
   - Test create knowledge base flow
   - Test update knowledge base flow
   - Test delete knowledge base flow
   - Test list knowledge bases with pagination

### Manual Testing Checklist

- [ ] 页面导航流畅
- [ ] 知识库列表正确显示
- [ ] 创建知识库功能正常
- [ ] 删除知识库有确认提示
- [ ] 文件上传成功
- [ ] 文件状态正确显示
- [ ] 文件筛选和搜索工作正常
- [ ] 知识库配置保存成功
- [ ] 检索测试返回正确结果
- [ ] 聊天界面知识库选择器工作正常
- [ ] 错误消息清晰易懂
- [ ] 加载状态正确显示

## Performance Optimization

### Caching Strategy

```python
@st.cache_data(ttl=60)
def get_knowledge_bases_cached(api_client: KnowledgeBaseAPIClient):
    """缓存知识库列表（60秒）"""
    return api_client.list_knowledge_bases(page=1, size=100)


@st.cache_data(ttl=30)
def get_kb_files_cached(api_client: KnowledgeBaseAPIClient, kb_id: str):
    """缓存文件列表（30秒）"""
    return api_client.list_files(kb_id, page=1, size=100)
```

### Lazy Loading

- 知识库列表分页加载
- 文件列表分页加载
- 检索结果按需展开

### State Optimization

- 最小化 st.rerun() 调用
- 使用 st.session_state 缓存 API 响应
- 避免不必要的 API 调用

## Security Considerations

### Input Validation

```python
def validate_kb_name(name: str) -> bool:
    """验证知识库名称"""
    if not name or len(name) < 2:
        return False
    if len(name) > 100:
        return False
    # 只允许字母、数字、下划线、连字符
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))


def validate_file_upload(file) -> bool:
    """验证上传文件"""
    # 检查文件大小（最大 100MB）
    if file.size > 100 * 1024 * 1024:
        return False
    
    # 检查文件类型
    allowed_extensions = ['.txt', '.md', '.pdf', '.docx']
    return any(file.name.endswith(ext) for ext in allowed_extensions)
```

### API Security

- 使用 HTTPS 连接后端 API
- 实现请求超时机制
- 添加请求重试逻辑
- 敏感信息不在前端存储

## Deployment

### Environment Configuration

```python
# config.py
import os

class UIConfig:
    """UI 配置"""
    
    # API 配置
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    
    # UI 配置
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "9"))
    FILE_PAGE_SIZE = int(os.getenv("FILE_PAGE_SIZE", "10"))
    
    # 缓存配置
    CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))
```

### Docker Support

```dockerfile
# Dockerfile for Streamlit UI
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag5/ ./rag5/

EXPOSE 8501

CMD ["streamlit", "run", "rag5/interfaces/ui/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
```

## Future Enhancements

1. **高级功能**
   - 批量文件操作
   - 文件预览功能
   - 知识库导出/导入
   - 元数据编辑

2. **用户体验**
   - 深色模式支持
   - 多语言支持
   - 键盘快捷键
   - 拖拽上传文件

3. **性能优化**
   - 虚拟滚动大列表
   - WebSocket 实时更新
   - 增量加载
   - 离线缓存

4. **监控和分析**
   - 使用统计
   - 性能监控
   - 错误追踪
   - 用户行为分析
