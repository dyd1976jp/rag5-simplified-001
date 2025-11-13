# Knowledge Base Settings Tab Usage Guide

## Overview

The Knowledge Base Settings Tab provides a comprehensive interface for configuring knowledge base parameters. Users can modify basic information, chunk configuration, and retrieval settings through an intuitive form-based interface.

## Features

### 1. Basic Information
- **Name**: Edit the knowledge base display name (required, max 100 characters)
- **Description**: Add or update a detailed description (optional, max 500 characters)
- **Embedding Model**: View the vector model (read-only, cannot be changed after creation)

### 2. Chunk Configuration
- **Chunk Size**: Control document splitting size (100-2000 characters)
  - Recommended: 512-1024 characters
  - Larger values: Better context retention
  - Smaller values: More precise retrieval
  
- **Chunk Overlap**: Set overlap between adjacent chunks (0-500 characters)
  - Recommended: 10-20% of chunk size
  - Prevents information loss at chunk boundaries
  - Higher overlap increases storage costs

### 3. Retrieval Configuration
- **Top-K**: Number of most relevant chunks to return (1-20)
  - Higher values: More context but potentially less relevant
  - Lower values: More focused but may miss context
  
- **Similarity Threshold**: Minimum similarity score (0.0-1.0)
  - Higher values: More relevant but fewer results
  - Lower values: More results but potentially less relevant
  
- **Retrieval Strategy**: Choose search method
  - **Vector**: Semantic similarity-based (recommended for most cases)
  - **Fulltext**: Keyword matching (good for exact terms)
  - **Hybrid**: Combines both approaches (most comprehensive)

## Usage

### Accessing Settings

1. Navigate to a knowledge base detail page
2. Click on the "⚙️ 知识库设置" (KB Settings) tab
3. The current configuration will be displayed in the form

### Modifying Settings

1. Edit any field in the form
2. Review the help text and explanations for guidance
3. Click "💾 保存设置" (Save Settings) to apply changes
4. Click "🔄 重置" (Reset) to discard changes and reload original values

### Validation

The form validates all inputs before saving:
- Name cannot be empty
- Name must be ≤ 100 characters
- Chunk size must be between 100-2000
- Chunk overlap must be between 0 and chunk size
- Top-K must be between 1-20
- Similarity threshold must be between 0.0-1.0

### Feedback

- **Success**: Green success message with automatic page refresh
- **Validation Error**: Red error messages for each validation failure
- **API Error**: Red error message with error details
- **Progress**: Spinner indicator during save operation

## Configuration Summary

Below the form, a summary panel displays current settings with metrics:
- Chunk configuration (size and overlap)
- Retrieval parameters (Top-K and threshold)
- Retrieval strategy and embedding model

## Best Practices

### Chunk Configuration
1. Start with default values (512 size, 50 overlap)
2. Increase chunk size for documents requiring more context
3. Decrease chunk size for precise Q&A scenarios
4. Set overlap to 10-20% of chunk size

### Retrieval Configuration
1. Start with Top-K = 5 for balanced results
2. Adjust similarity threshold based on result quality
3. Use vector retrieval for general semantic search
4. Use hybrid retrieval for comprehensive coverage

### Testing Changes
1. Save configuration changes
2. Navigate to "🔍 检索测试" (Retrieval Test) tab
3. Test queries to verify improved results
4. Iterate on settings as needed

## Examples

### Example 1: Optimizing for Long Documents
```
Chunk Size: 1024
Chunk Overlap: 100
Top-K: 3
Similarity Threshold: 0.4
Retrieval Mode: vector
```

### Example 2: Optimizing for Precise Q&A
```
Chunk Size: 512
Chunk Overlap: 50
Top-K: 5
Similarity Threshold: 0.5
Retrieval Mode: hybrid
```

### Example 3: Optimizing for Technical Documentation
```
Chunk Size: 768
Chunk Overlap: 80
Top-K: 7
Similarity Threshold: 0.3
Retrieval Mode: hybrid
```

## Troubleshooting

### Settings Not Saving
- Check network connection to API server
- Verify API server is running
- Check browser console for errors
- Ensure all validation requirements are met

### Changes Not Reflected
- Wait for page refresh after save
- Clear browser cache if needed
- Verify changes in configuration summary

### Validation Errors
- Read error messages carefully
- Ensure all required fields are filled
- Check numeric values are within valid ranges
- Verify name length is within limits

## API Integration

The settings tab uses the following API endpoint:
- **PUT** `/api/v1/knowledge-bases/{kb_id}`

Request body includes:
```json
{
  "name": "string",
  "description": "string",
  "chunk_config": {
    "chunk_size": 512,
    "chunk_overlap": 50
  },
  "retrieval_config": {
    "retrieval_mode": "vector",
    "top_k": 5,
    "similarity_threshold": 0.3
  }
}
```

## Related Documentation

- [Knowledge Base Detail Page](./DETAIL_PAGE_USAGE.md)
- [API Client](./API_CLIENT_USAGE.md)
- [File Management Tab](./FILE_MANAGEMENT_USAGE.md)
