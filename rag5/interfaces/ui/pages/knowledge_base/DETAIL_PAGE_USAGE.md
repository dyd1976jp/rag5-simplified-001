# Knowledge Base Detail Page Usage Guide

## Overview

The knowledge base detail page provides a comprehensive view of a single knowledge base with three main tabs:
- **File Management**: Upload, view, and manage files (placeholder - to be implemented in Task 7-8)
- **KB Settings**: Configure knowledge base parameters (placeholder - to be implemented in Task 9)
- **Retrieval Test**: Test search functionality (placeholder - to be implemented in Task 10)

## Components

### Main Page Renderer

```python
from rag5.interfaces.ui.pages.knowledge_base.detail import render_kb_detail_page
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient

# In your Streamlit app
api_client = KnowledgeBaseAPIClient()
render_kb_detail_page(api_client)
```

### Header Component

The header displays:
- Back button to return to list
- Knowledge base name (title)
- Knowledge base ID
- Description
- Metadata (embedding model, chunk size, retrieval strategy)

```python
from rag5.interfaces.ui.pages.knowledge_base.detail import render_kb_header

kb = {
    "id": "kb_123",
    "name": "My Knowledge Base",
    "description": "Test KB",
    "embedding_model": "BAAI/bge-m3",
    "chunk_config": {
        "chunk_size": 1000,
        "chunk_overlap": 50
    },
    "retrieval_config": {
        "retrieval_mode": "vector",
        "top_k": 5,
        "similarity_threshold": 0.3
    }
}

render_kb_header(kb)
```

### Tab Components

Each tab has a dedicated render function:

```python
from rag5.interfaces.ui.pages.knowledge_base.detail import (
    render_file_management_tab,
    render_kb_settings_tab,
    render_retrieval_test_tab
)

# File Management Tab (placeholder)
render_file_management_tab("kb_123", api_client)

# Settings Tab (placeholder)
render_kb_settings_tab(kb, api_client)

# Retrieval Test Tab (placeholder)
render_retrieval_test_tab("kb_123", api_client)
```

## Navigation Flow

1. User clicks "查看" button on a knowledge base card in the list page
2. `SessionState.set_selected_kb(kb_id)` stores the selected KB ID
3. `SessionState.set_current_page("kb_detail")` triggers navigation
4. App routes to `render_kb_detail_page()`
5. Page fetches KB details using `api_client.get_knowledge_base(kb_id)`
6. Header and tabs are rendered

## State Management

The detail page uses SessionState for:
- **selected_kb_id**: Currently selected knowledge base ID
- **current_page**: Current page identifier ("kb_detail")

```python
from rag5.interfaces.ui.state import SessionState

# Set selected KB
SessionState.set_selected_kb("kb_123")

# Get selected KB
kb_id = SessionState.get_selected_kb()

# Navigate to detail page
SessionState.set_current_page("kb_detail")

# Navigate back to list
SessionState.set_current_page("kb_list")
```

## Error Handling

The page handles several error scenarios:

### No KB Selected
```
Error: "未选择知识库"
Info: "请从知识库列表中选择一个知识库"
Action: Button to return to list
```

### API Error
```
Error: "加载失败: {error_message}"
Action: Button to return to list
```

### Network Error
```
Error: "加载失败: Unable to connect to API..."
Action: Button to return to list
```

## Tab Structure

The page uses Streamlit's `st.tabs()` for navigation:

```python
tab1, tab2, tab3 = st.tabs(["📁 文件管理", "⚙️ 知识库设置", "🔍 检索测试"])

with tab1:
    # File management content
    pass

with tab2:
    # Settings content
    pass

with tab3:
    # Retrieval test content
    pass
```

## Current Implementation Status

### ✅ Implemented (Task 6)
- Main page structure with tab navigation
- Header with back button and KB information
- Error handling for missing KB or API errors
- Placeholder tabs with informational content
- Integration with SessionState for navigation
- Integration with API client for fetching KB details

### 🔜 To Be Implemented
- **Task 7-8**: File management functionality
  - File upload with progress
  - File list with search and filtering
  - File status display
  - File deletion and reprocessing
  
- **Task 9**: Settings editing functionality
  - Editable configuration form
  - Save/update functionality
  - Validation and error handling
  
- **Task 10**: Retrieval testing functionality
  - Query input and search
  - Results display with scores
  - Metadata and content viewing

## Testing

Run the test script to verify the implementation:

```bash
python test_kb_detail_page.py
```

Expected output:
```
✓ All functions imported successfully
✓ render_kb_detail_page has correct signature
✓ render_kb_header has correct signature
✓ render_file_management_tab has correct signature
✓ render_kb_settings_tab has correct signature
✓ render_retrieval_test_tab has correct signature
✓ All functions have docstrings
✓ API client instantiated
✓ All tests passed!
```

## Example Usage in App

```python
# In app.py
from rag5.interfaces.ui.pages.knowledge_base.detail import render_kb_detail_page
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient

def render_kb_management():
    """Render knowledge base management pages"""
    api_client = KnowledgeBaseAPIClient()
    
    # Get current page state
    kb_page = st.session_state.get("current_page", "kb_list")
    
    # Route to appropriate page
    if kb_page == "kb_detail":
        render_kb_detail_page(api_client)
    else:
        render_kb_list_page(api_client)
```

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **Requirement 5.1**: ✅ Page switches to detail view when KB card is clicked
- **Requirement 5.2**: ✅ Three tabs created using st.tabs
- **Requirement 5.3**: ✅ Header displays KB basic information using st.markdown
- **Requirement 5.4**: ✅ File management tab structure (placeholder for st.dataframe)
- **Requirement 5.5**: ✅ Pagination structure ready (to be implemented in Task 7)

## Next Steps

1. **Task 7**: Implement file management tab with upload and list functionality
2. **Task 8**: Add file operations (delete, reprocess)
3. **Task 9**: Implement settings editing with form and save functionality
4. **Task 10**: Implement retrieval testing with query and results display
