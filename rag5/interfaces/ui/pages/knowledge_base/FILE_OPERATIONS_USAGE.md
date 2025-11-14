# File Operations Usage Guide

## Overview

This guide explains how to use the file operations functionality in the Knowledge Base Management UI.

## Features

### 1. File Upload

**Location:** Knowledge Base Detail Page → File Management Tab

**Steps:**
1. Navigate to a knowledge base detail page
2. Click on the "📁 文件管理" tab
3. Click "选择文件（支持多文件上传）" to select files
4. Select one or more files (TXT, MD, PDF, DOCX formats supported)
5. Review the selected files in the preview
6. Click "📤 开始上传" to start the upload

**Features:**
- Multiple file upload support
- Real-time progress bar showing upload progress
- Status text showing which file is currently being uploaded
- Preview of selected file names
- Automatic page refresh after upload completion

**Feedback Messages:**
- ✅ Success: "成功上传 X 个文件！文件将在后台处理。"
- ⚠️ Partial Success: "部分上传成功：X/Y 个文件"
- ❌ Failure: "上传失败：所有文件上传失败"

**Example:**
```
📎 已选择 3 个文件
  • document1.pdf
  • document2.txt
  • document3.md

[Progress Bar: ████████░░ 80%]
正在上传 3/3: document3.md

✅ 成功上传 3 个文件！文件将在后台处理。
```

### 2. File Delete

**Location:** Knowledge Base Detail Page → File Management Tab → File List

**Steps:**
1. Locate the file you want to delete in the file list
2. Click the "🗑️" button on the right side of the file row
3. Review the confirmation dialog with file details
4. Click "🗑️ 确认删除" to confirm, or "❌ 取消" to cancel

**Features:**
- Confirmation dialog prevents accidental deletions
- Warning about irreversible operation
- File details display (name, ID, size, status, chunk count)
- Progress indicator during deletion
- Automatic page refresh after deletion

**Confirmation Dialog:**
```
⚠️ 确定要删除文件 document.pdf 吗？
🚨 此操作不可撤销！文件及其所有相关数据将被永久删除。

📄 文件详情
文件名: document.pdf
文件ID: file_abc123
大小: 1.5 MB
状态: succeeded
文档块数: 15

[❌ 取消]  [🗑️ 确认删除]
```

**Feedback Messages:**
- ✅ Success: "文件删除成功！"
- ❌ Failure: "删除失败: {error message}"

### 3. File Reprocess

**Location:** Knowledge Base Detail Page → File Management Tab → File List (Failed Files Only)

**Steps:**
1. Locate a failed file in the file list (marked with ❌ 失败)
2. Click the "🔄" button on the left side of the file row
3. Wait for the reprocess request to be submitted
4. The page will refresh to show the updated status

**Features:**
- Only available for failed files
- Progress spinner during API call
- Graceful handling if backend endpoint not implemented
- Automatic page refresh on success

**Feedback Messages:**
- ✅ Success: "文件已加入重新处理队列"
- ⚠️ Not Implemented: "重新处理功能暂未在后端实现。请删除文件后重新上传。"
- ❌ Failure: "操作失败: {error message}"

**Note:** If the reprocess endpoint is not yet implemented in the backend, you'll see a warning message suggesting to delete and re-upload the file instead.

## File Status Indicators

Files in the list are marked with color-coded status indicators:

- 🟡 **等待中** (Pending): File is queued for processing
- 🔵 **解析中** (Parsing): File is being parsed
- 🔵 **索引中** (Persisting): File chunks are being indexed
- 🟢 **成功** (Succeeded): File processed successfully
- 🔴 **失败** (Failed): File processing failed

## Error Details

For failed files, you can view error details:

1. Locate a failed file (marked with ❌ 失败)
2. Click "🔍 查看错误详情" to expand the error message
3. Review the error details to understand what went wrong

## Tips

### Upload Tips
- Upload multiple files at once for efficiency
- Supported formats: TXT, MD, PDF, DOCX
- Files are processed in the background after upload
- Check the file list after a few moments to see processing status

### Delete Tips
- Always review the confirmation dialog before deleting
- Deletion is permanent and cannot be undone
- Deleting a file removes all its chunks from the knowledge base
- Consider the impact on search results before deleting

### Reprocess Tips
- Only failed files can be reprocessed
- If reprocess is not available, delete and re-upload the file
- Check error details before reprocessing to understand the issue
- Some errors may require file format changes before re-upload

## Troubleshooting

### Upload Issues

**Problem:** Upload fails for all files
- **Solution:** Check that the API server is running
- **Solution:** Verify file formats are supported
- **Solution:** Check file sizes are reasonable

**Problem:** Partial upload success
- **Solution:** Check error logs for specific file issues
- **Solution:** Try uploading failed files individually
- **Solution:** Verify file content is valid

### Delete Issues

**Problem:** Delete button doesn't work
- **Solution:** Refresh the page and try again
- **Solution:** Check that you have permission to delete files
- **Solution:** Verify the API server is accessible

**Problem:** File still appears after deletion
- **Solution:** Refresh the page manually
- **Solution:** Check if deletion actually succeeded (look for error message)

### Reprocess Issues

**Problem:** Reprocess button not available
- **Solution:** Only failed files can be reprocessed
- **Solution:** Check file status is "failed"

**Problem:** Reprocess shows "not implemented" message
- **Solution:** This is expected if backend endpoint not ready
- **Solution:** Delete the file and re-upload instead
- **Solution:** Contact administrator about backend implementation

## API Integration

### Upload Endpoint
```
POST /api/v1/knowledge-bases/{kb_id}/files
Content-Type: multipart/form-data

file: <binary file data>
```

### Delete Endpoint
```
DELETE /api/v1/knowledge-bases/{kb_id}/files/{file_id}
```

### Reprocess Endpoint (Future)
```
POST /api/v1/knowledge-bases/{kb_id}/files/{file_id}/reprocess
```

## Related Documentation

- [File Management Tab Usage](FILE_MANAGEMENT_USAGE.md)
- [Knowledge Base Detail Page](DETAIL_PAGE_USAGE.md)
- [API Client Documentation](API_CLIENT_USAGE.md)

## Support

For issues or questions:
1. Check the error message for specific details
2. Review the logs for debugging information
3. Consult the API documentation
4. Contact the development team
