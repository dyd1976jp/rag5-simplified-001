# Retrieval Test Tab Usage Guide

## Overview

The Retrieval Test Tab provides an interactive interface for testing knowledge base search functionality. It allows users to query the knowledge base, adjust search parameters, and view detailed results with similarity scores and metadata.

## Features

### 1. Query Input
- **Text Input Field**: Enter your search query or question
- **Placeholder Examples**: Helpful examples like "什么是 RAG？"
- **Real-time Validation**: Search button is disabled when query is empty

### 2. Search Parameters

#### Top-K Slider
- **Range**: 1-20 results
- **Default**: 5 results
- **Purpose**: Controls how many of the most relevant document chunks to return
- **Recommendation**: 
  - Use 3-5 for focused results
  - Use 10-15 for comprehensive context

#### Custom Similarity Threshold (Advanced)
- **Optional Setting**: Enable via checkbox in advanced settings
- **Range**: 0.0 - 1.0
- **Default**: Uses knowledge base default (typically 0.3)
- **Purpose**: Filters out results below the specified similarity score
- **Recommendation**:
  - 0.7+ for high precision (fewer but more relevant results)
  - 0.5-0.7 for balanced results
  - 0.3-0.5 for high recall (more results, some less relevant)

### 3. Search Results Display

#### Result Cards
Each result is displayed in an expandable card showing:

**Header**:
- Color-coded relevance indicator:
  - 🟢 Green: High relevance (score ≥ 0.7)
  - 🟡 Yellow: Medium relevance (score ≥ 0.5)
  - 🟠 Orange: Lower relevance (score < 0.5)
- Result number
- Similarity score (0-1 scale and percentage)

**Content Section**:
- Full document chunk text
- Displayed in a scrollable text area
- Preserves original formatting

**Metadata Section**:
- File information (file_name, file_id)
- Chunk information (chunk_id, page number)
- Source information
- Additional custom metadata
- Full JSON view available in collapsible section

**Score Details**:
- Similarity score (4 decimal places)
- Percentage representation
- Relevance level classification
- Visual progress bar

### 4. Search Statistics

After search completion, view aggregate statistics:
- **Total Results**: Number of results returned
- **Average Similarity**: Mean score across all results
- **Highest Similarity**: Best matching result score
- **Lowest Similarity**: Weakest matching result score

### 5. Empty State Handling

When no results are found, the interface provides:
- Clear "no results" message
- Helpful suggestions:
  - Try different keywords
  - Lower similarity threshold
  - Increase Top-K value
  - Verify documents are uploaded and processed

### 6. Error Handling

Graceful error handling for:
- API connection failures
- Query processing errors
- Timeout issues
- Invalid parameters

## Usage Examples

### Example 1: Basic Search

```
1. Enter query: "什么是机器学习？"
2. Keep default Top-K: 5
3. Click "🔍 搜索"
4. Review results sorted by relevance
5. Expand top results to read content
```

### Example 2: High Precision Search

```
1. Enter query: "深度学习神经网络"
2. Expand "⚙️ 高级设置"
3. Enable "使用自定义相似度阈值"
4. Set threshold to 0.7
5. Set Top-K to 3
6. Click "🔍 搜索"
7. Get only highly relevant results
```

### Example 3: Comprehensive Search

```
1. Enter query: "RAG 检索增强生成"
2. Set Top-K to 15
3. Keep default threshold
4. Click "🔍 搜索"
5. Review all potentially relevant results
6. Check metadata to identify source documents
```

### Example 4: Keyword Search

```
1. Enter query: "向量数据库 embedding"
2. Set Top-K to 10
3. Click "🔍 搜索"
4. Compare similarity scores
5. Identify which documents contain these terms
```

## Understanding Similarity Scores

### Score Interpretation

- **0.9 - 1.0**: Extremely high relevance (near-exact match)
- **0.7 - 0.9**: High relevance (strong semantic match)
- **0.5 - 0.7**: Medium relevance (related content)
- **0.3 - 0.5**: Low relevance (tangentially related)
- **0.0 - 0.3**: Very low relevance (weak connection)

### Factors Affecting Scores

1. **Semantic Similarity**: How closely the query matches document meaning
2. **Keyword Overlap**: Presence of exact query terms
3. **Context Alignment**: Relevance of surrounding content
4. **Document Quality**: Well-structured documents score better
5. **Embedding Model**: Different models produce different score ranges

## Best Practices

### Query Formulation

1. **Be Specific**: "RAG 的工作原理" vs "RAG"
2. **Use Natural Language**: Ask questions as you would to a person
3. **Include Context**: "在机器学习中，什么是..." vs "什么是..."
4. **Try Variations**: Test different phrasings if results are poor

### Parameter Tuning

1. **Start with Defaults**: Use default settings first
2. **Adjust Gradually**: Make small changes to parameters
3. **Compare Results**: Test same query with different settings
4. **Document Findings**: Note which settings work best for your use case

### Result Analysis

1. **Check Top Results**: Focus on highest-scoring results first
2. **Review Metadata**: Identify source documents for relevant results
3. **Read Full Content**: Don't rely solely on scores
4. **Verify Accuracy**: Ensure results actually answer your query

### Troubleshooting

**No Results Found**:
- Lower similarity threshold
- Increase Top-K
- Simplify query
- Check if relevant documents are uploaded

**Low Relevance Scores**:
- Rephrase query
- Add more context
- Check document quality
- Verify correct knowledge base selected

**Too Many Results**:
- Increase similarity threshold
- Decrease Top-K
- Make query more specific
- Use advanced filtering

## Integration with Chat

The retrieval test tab helps you:
1. **Validate Knowledge Base**: Ensure documents are properly indexed
2. **Test Query Patterns**: Understand what queries work well
3. **Optimize Parameters**: Find best settings for your use case
4. **Debug Issues**: Identify problems with retrieval quality

Use insights from retrieval testing to improve chat interactions by:
- Understanding which documents are being retrieved
- Identifying gaps in knowledge base coverage
- Optimizing retrieval parameters for better responses
- Verifying document processing quality

## Technical Details

### API Endpoint
- **Method**: POST
- **Path**: `/api/v1/knowledge-bases/{kb_id}/query`
- **Parameters**:
  - `query` (string, required): Search query
  - `top_k` (integer, optional): Number of results
  - `similarity_threshold` (float, optional): Minimum score

### Response Format
```json
{
  "results": [
    {
      "score": 0.85,
      "text": "Document content...",
      "metadata": {
        "file_name": "doc.pdf",
        "file_id": "file_123",
        "chunk_id": "chunk_1",
        "page": 5
      }
    }
  ]
}
```

### Performance Considerations
- Queries typically complete in 100-500ms
- Larger Top-K values increase processing time
- Complex queries may take longer
- Results are not cached (always fresh)

## Keyboard Shortcuts

- **Enter**: Submit search (when query input is focused)
- **Escape**: Close expanded result cards
- **Tab**: Navigate between UI elements

## Accessibility

- All interactive elements are keyboard accessible
- Screen reader compatible
- High contrast color coding for relevance
- Clear visual hierarchy
- Descriptive labels and help text

## Future Enhancements

Planned features:
- Query history and favorites
- Export results to CSV/JSON
- Batch query testing
- A/B comparison of different parameters
- Visualization of score distributions
- Highlighting of matched terms in results

## Support

For issues or questions:
1. Check error messages for specific guidance
2. Review this documentation
3. Verify API server is running
4. Check knowledge base has processed documents
5. Consult main application documentation
