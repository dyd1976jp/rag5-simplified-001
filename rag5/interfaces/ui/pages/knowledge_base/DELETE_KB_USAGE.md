# Delete Knowledge Base Dialog Usage Guide

## Overview

The delete knowledge base functionality provides a safe way to remove knowledge bases from the system with proper confirmation and error handling.

## Features

- **Confirmation Dialog**: Uses Streamlit's `@st.dialog` decorator for modal confirmation
- **Warning Messages**: Clear warnings about irreversible operations
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Automatic Refresh**: Refreshes the list after successful deletion

## Implementation Details

### Function Signature

```python
@st.dialog("确认删除")
def show_delete_confirmation(kb: Dict[str, Any], api_client: KnowledgeBaseAPIClient):
    """
    Show delete confirmation dialog.
    
    Args:
        kb: Knowledge base data dictionary with 'id' and 'name' keys
        api_client: API client instance for making delete requests
    """
```

### User Flow

1. User clicks the delete button (🗑️) on a knowledge base card
2. A modal dialog appears with:
   - Warning message showing the KB name
   - Error message about irreversibility
   - Cancel and Confirm buttons
3. If user clicks "Cancel":
   - Dialog closes and returns to list
4. If user clicks "Confirm":
   - Shows spinner with "删除中..." message
   - Calls API to delete the knowledge base
   - On success: Shows success message and refreshes list
   - On failure: Shows error message with details

## Usage Example

### In Knowledge Base List Page

```python
from rag5.interfaces.ui.pages.knowledge_base.list import render_kb_card
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient

# Initialize API client
api_client = KnowledgeBaseAPIClient()

# Render KB card (includes delete button)
kb = {
    "id": "kb_123",
    "name": "My Knowledge Base",
    "description": "Test KB",
    "updated_at": "2024-01-15T10:30:00Z"
}

render_kb_card(kb, api_client)
```

### Direct Usage

```python
from rag5.interfaces.ui.pages.knowledge_base.list import show_delete_confirmation
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient

# Initialize API client
api_client = KnowledgeBaseAPIClient()

# Show delete confirmation
kb = {
    "id": "kb_123",
    "name": "My Knowledge Base"
}

# This will open a modal dialog
show_delete_confirmation(kb, api_client)
```

## Requirements Satisfied

This implementation satisfies **Requirement 4** from the requirements document:

### Requirement 4.1
✅ **WHEN** user clicks delete button on KB card, **THE** system **SHALL** use `st.dialog` to display confirmation dialog

### Requirement 4.2
✅ **THE** system **SHALL** use `st.warning` to warn that delete operation is irreversible

### Requirement 4.3
✅ **WHEN** user confirms delete, **THE** system **SHALL** call delete API and use `st.rerun` to refresh page

### Requirement 4.4
✅ **IF** delete fails, **THEN THE** system **SHALL** use `st.error` to display error message

## Error Handling

The function handles multiple error scenarios:

### API Errors
```python
try:
    api_client.delete_knowledge_base(kb['id'])
except APIError as e:
    st.error(f"删除失败: {str(e)}")
    logger.error(f"Failed to delete knowledge base {kb['id']}: {e}")
```

### Unexpected Errors
```python
except Exception as e:
    st.error(f"删除失败: {str(e)}")
    logger.exception(f"Unexpected error deleting knowledge base {kb['id']}")
```

## UI Components

### Warning Message
```python
st.warning(f"确定要删除知识库 **{kb['name']}** 吗？")
```

### Error Message
```python
st.error("此操作不可撤销，将删除所有相关文件和数据！")
```

### Action Buttons
```python
col1, col2 = st.columns(2)
with col1:
    if st.button("取消", use_container_width=True):
        st.rerun()

with col2:
    if st.button("确认删除", type="primary", use_container_width=True):
        # Delete logic
```

### Loading Indicator
```python
with st.spinner("删除中..."):
    api_client.delete_knowledge_base(kb['id'])
```

### Success Message
```python
st.success("删除成功")
time.sleep(1)  # Brief pause to show message
st.rerun()
```

## Testing

The delete functionality is tested in `test_delete_kb_dialog.py`:

- ✅ Warning messages display correctly
- ✅ Cancel button triggers rerun
- ✅ Successful deletion calls API and refreshes
- ✅ API errors are handled gracefully
- ✅ Unexpected errors are caught and displayed

Run tests:
```bash
python test_delete_kb_dialog.py
```

## Logging

The function logs important events:

```python
logger.info(f"Deleted knowledge base: {kb['id']}")
logger.error(f"Failed to delete knowledge base {kb['id']}: {e}")
logger.exception(f"Unexpected error deleting knowledge base {kb['id']}")
```

## Best Practices

1. **Always confirm destructive actions**: The dialog ensures users don't accidentally delete KBs
2. **Clear warnings**: Users understand the consequences before confirming
3. **Error feedback**: Users know immediately if something goes wrong
4. **Logging**: All operations are logged for debugging and audit trails
5. **Graceful degradation**: Errors don't crash the app, just show messages

## Integration with List Page

The delete button is integrated into the KB card component:

```python
def render_kb_card(kb: Dict[str, Any], api_client: KnowledgeBaseAPIClient):
    with st.container(border=True):
        # ... card content ...
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("查看", key=f"view_{kb['id']}", use_container_width=True):
                # View logic
        
        with col2:
            if st.button("🗑️", key=f"delete_{kb['id']}", 
                        use_container_width=True, help="删除知识库"):
                show_delete_confirmation(kb, api_client)
```

## Security Considerations

1. **Confirmation required**: Users must explicitly confirm deletion
2. **Clear warnings**: Users are warned about data loss
3. **API validation**: Backend validates permissions and existence
4. **Logging**: All delete operations are logged

## Future Enhancements

Potential improvements for future versions:

1. **Soft delete**: Option to archive instead of permanently delete
2. **Undo functionality**: Brief window to undo deletion
3. **Batch delete**: Select and delete multiple KBs at once
4. **Export before delete**: Option to export KB data before deletion
5. **Dependency check**: Warn if KB is used in active configurations

## Related Documentation

- [API Client Usage](./API_CLIENT_USAGE.md)
- [List Page Usage](./LIST_PAGE_USAGE.md)
- [Knowledge Base Management](../../../../../docs/KNOWLEDGE_BASE_MANAGEMENT.md)
