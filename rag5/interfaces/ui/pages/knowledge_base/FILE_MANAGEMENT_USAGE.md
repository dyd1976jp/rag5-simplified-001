# File Management Tab Usage Guide

## Overview

The File Management Tab provides a comprehensive interface for managing files within a knowledge base. It includes file upload, listing, searching, filtering, and deletion capabilities.

## Features

### 1. File Upload

**Multiple File Upload Support:**
- Click the file uploader to select one or more files
- Supported formats: TXT, MD, PDF, DOCX, DOC
- Shows count of selected files
- Click "开始上传" (Start Upload) to upload all selected files
- Displays success message with count of uploaded files
- Automatically refreshes the file list after upload

**Example:**
```python
# Files are uploaded via Streamlit's file_uploader component
# The API client handles the upload to the backend
uploaded_files = st.file_uploader(
    "选择文件（支持多文件上传）",
    accept_multiple_files=True,
    type=["txt", "md", "pdf", "docx", "doc"]
)
```

### 2. File List Display

**File Information Shown:**
- 📄 File name
- File size (formatted: B, KB, MB, GB, TB)
- Processing status with color indicators
- Creation timestamp
- Action buttons (delete, reprocess for failed files)

**Status Indicators:**
- 🟡 ⏳ 等待中 (Pending) - File is queued for processing
- 🔵 🔄 解析中 (Parsing) - File is being parsed
- 🔵 💾 索引中 (Persisting) - File is being indexed
- 🟢 ✅ 成功 (Succeeded) - File processed successfully
- 🔴 ❌ 失败 (Failed) - File processing failed

### 3. Search and Filter

**Search by File Name:**
- Enter keywords in the search box
- Searches file names in real-time
- Case-insensitive search

**Filter by Status:**
- Select from dropdown: 全部状态, 等待中, 解析中, 索引中, 成功, 失败
- Filters are applied immediately
- Can combine search and status filter

**Refresh:**
- Click 🔄 刷新 button to reload the file list
- Useful for checking processing status updates

### 4. Pagination

**Navigation Controls:**
- ⏮️ 首页 (First Page)
- ◀️ 上一页 (Previous Page)
- Current page indicator (第 X / Y 页)
- 下一页 ▶️ (Next Page)
- 末页 ⏭️ (Last Page)

**Settings:**
- Default page size: 10 files per page
- Page state is preserved in session

### 5. File Operations

**Delete File:**
- Click 🗑️ button on any file row
- File is immediately deleted from the knowledge base
- Success/error message is displayed
- File list automatically refreshes

**Reprocess Failed Files:**
- 🔄 button appears only for failed files
- Click to request reprocessing
- Note: Reprocess API endpoint implementation pending

**View Error Details:**
- For failed files, click "🔍 查看错误详情" expander
- Shows the error message that caused the failure
- Helps diagnose processing issues

## Usage Examples

### Example 1: Upload Files

1. Navigate to knowledge base detail page
2. Click "📁 文件管理" tab
3. Click file uploader and select files
4. Click "开始上传" button
5. Wait for success message
6. Files appear in the list below

### Example 2: Search for Specific Files

1. In the file list section, locate the search box
2. Type keywords (e.g., "report" to find all report files)
3. File list updates automatically
4. Clear search box to show all files again

### Example 3: Filter by Status

1. Click the status dropdown (default: "全部状态")
2. Select a status (e.g., "✅ 成功" to see only successful files)
3. File list updates to show only matching files
4. Select "全部状态" to show all files again

### Example 4: Delete a File

1. Locate the file you want to delete
2. Click the 🗑️ button in the action column
3. Wait for "✅ 删除成功" message
4. File is removed from the list

### Example 5: Check Failed File Details

1. Look for files with 🔴 ❌ 失败 status
2. Click "🔍 查看错误详情" expander below the file
3. Read the error message
4. Optionally click 🔄 to reprocess (when available)

## Technical Details

### Utility Functions

**format_datetime(dt_str: str) -> str**
- Converts ISO datetime to readable format (YYYY-MM-DD HH:MM)
- Handles timezone conversion
- Returns original string if parsing fails

**format_file_size(size_bytes: int) -> str**
- Converts bytes to human-readable format
- Automatically selects appropriate unit (B, KB, MB, GB, TB)
- Returns formatted string with 1 decimal place

### API Integration

The file management tab uses the following API client methods:

- `upload_files(kb_id, files)` - Upload multiple files
- `list_files(kb_id, page, size, status, query)` - Get paginated file list
- `delete_file(kb_id, file_id)` - Delete a file

### Session State

The following session state keys are used:
- `file_uploader_{kb_id}` - File uploader widget state
- `file_search_{kb_id}` - Search query
- `status_filter_{kb_id}` - Selected status filter
- `file_list_page_{kb_id}` - Current page number

## Error Handling

**Upload Errors:**
- Connection errors: "无法连接到后端服务"
- Timeout errors: "请求超时"
- HTTP errors: Specific error message from API
- Generic errors: "上传失败" with error details

**List Loading Errors:**
- API errors: "加载文件列表失败" with details
- Displays error message and stops rendering

**Delete Errors:**
- API errors: "删除失败" with details
- File remains in list if deletion fails

## Performance Considerations

- File list is paginated (10 items per page) to improve performance
- Search and filter operations are performed server-side
- Session state is used to preserve user selections
- Automatic refresh after operations ensures data consistency

## Future Enhancements

- Reprocess API endpoint implementation
- Batch file operations (delete multiple files)
- File preview functionality
- Download file capability
- Advanced filtering options (by date, size, etc.)
- Sorting options (by name, date, size, status)

## Related Components

- `api_client.py` - API client for backend communication
- `detail.py` - Main detail page with tab navigation
- `state.py` - Session state management

## Requirements Mapping

This implementation satisfies the following requirements:

- **6.1-6.5**: File upload functionality
- **7.1-7.4**: File status display and filtering
- **11.1**: Query/search functionality
- **12.1-12.4**: Search and filter controls

## Testing

Run the test suite to verify functionality:

```bash
python test_file_management_tab.py
```

The test verifies:
- Utility functions work correctly
- All required functions are implemented
- All required features are present
- Requirements coverage is complete
