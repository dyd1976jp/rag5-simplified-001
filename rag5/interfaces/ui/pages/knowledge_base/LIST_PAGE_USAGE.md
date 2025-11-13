# Knowledge Base List Page Usage

## Overview

The knowledge base list page provides a user-friendly interface for viewing and managing knowledge bases in a card-based grid layout.

## Features

### 1. Grid Layout Display
- Knowledge bases are displayed in a 3x3 grid layout
- Each card shows:
  - Knowledge base name
  - Description (or "暂无描述" if empty)
  - Shortened ID (first 8 characters)
  - Last updated timestamp

### 2. Pagination
- Displays up to 9 knowledge bases per page (3x3 grid)
- Navigation controls:
  - Previous page button (⬅️ 上一页)
  - Page counter showing current page, total pages, and total count
  - Next page button (下一页 ➡️)
- Page state is preserved in session state

### 3. Create Knowledge Base
- Click "➕ 新建知识库" button to open creation dialog
- Configure:
  - Basic info: name, description
  - Chunk config: chunk_size, chunk_overlap
  - Embedding model selection
  - Retrieval config: top_k, similarity_threshold, retrieval_mode
- On success, automatically navigates to the new KB's detail page

### 4. Delete Knowledge Base
- Click 🗑️ button on any KB card
- Confirmation dialog appears with warning
- Deletion is permanent and removes all associated files

### 5. View Knowledge Base
- Click "查看" button to navigate to KB detail page
- Selected KB ID is stored in session state

### 6. Empty State
- When no knowledge bases exist, displays:
  - Info message: "暂无知识库，点击上方按钮创建第一个知识库"
  - Create button remains accessible

## Usage Example

```python
import streamlit as st
from rag5.interfaces.ui.pages.knowledge_base import (
    render_kb_list_page,
    KnowledgeBaseAPIClient
)

# Initialize API client
api_client = KnowledgeBaseAPIClient(base_url="http://localhost:8000")

# Render the list page
render_kb_list_page(api_client)
```

## Error Handling

The list page handles various error scenarios:

1. **API Connection Errors**: Shows error message if unable to connect to backend
2. **API Timeout**: Shows timeout error with retry suggestion
3. **HTTP Errors**: Shows specific error messages based on status code
4. **Unexpected Errors**: Logs full traceback and shows generic error message

All errors are logged for debugging purposes.

## Session State

The list page uses the following session state keys:

- `kb_list_page`: Current page number (default: 1)
- `selected_kb_id`: ID of selected knowledge base (set when clicking "查看")
- `current_page`: Current UI page identifier (set to "kb_detail" when viewing KB)

## API Requirements

The list page requires the following API endpoints:

- `GET /api/v1/knowledge-bases?page={page}&size={size}`: List knowledge bases
- `POST /api/v1/knowledge-bases`: Create knowledge base
- `DELETE /api/v1/knowledge-bases/{kb_id}`: Delete knowledge base

## Styling

The page uses Streamlit's native components with:
- Container borders for cards
- Column-based grid layout
- Consistent button styling
- Color-coded feedback (success, error, warning, info)

## Performance Considerations

- Loads 9 KBs per page to balance display and performance
- Uses spinner during API calls for user feedback
- Minimal state management to reduce memory usage
- Efficient rerun strategy to update UI after operations
