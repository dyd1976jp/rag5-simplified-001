# Knowledge Base API Client Usage Guide

This guide demonstrates how to use the `KnowledgeBaseAPIClient` for interacting with the Knowledge Base API.

## Installation

The API client is part of the `rag5` package and requires the following dependencies:
- `requests`
- `urllib3`

## Basic Usage

### Initialize the Client

```python
from rag5.interfaces.ui.pages.knowledge_base import KnowledgeBaseAPIClient

# Use default settings (http://localhost:8000)
client = KnowledgeBaseAPIClient()

# Or customize the configuration
client = KnowledgeBaseAPIClient(
    base_url="http://api.example.com:8000",
    timeout=60,
    max_retries=5
)
```

### Using Context Manager

```python
with KnowledgeBaseAPIClient() as client:
    kbs = client.list_knowledge_bases()
    print(f"Found {kbs['total']} knowledge bases")
```

## Knowledge Base Operations

### List Knowledge Bases

```python
# Get first page with 10 items
result = client.list_knowledge_bases(page=1, size=10)

print(f"Total: {result['total']}")
for kb in result['items']:
    print(f"- {kb['name']} (ID: {kb['id']})")
```

### Get Knowledge Base Details

```python
kb_id = "kb_123"
kb = client.get_knowledge_base(kb_id)

print(f"Name: {kb['name']}")
print(f"Description: {kb['description']}")
print(f"Documents: {kb['document_count']}")
print(f"Embedding Model: {kb['embedding_model']}")
```

### Create Knowledge Base

```python
kb_data = {
    "name": "Product Documentation",
    "description": "Technical documentation for our products",
    "embedding_model": "BAAI/bge-m3",
    "chunk_config": {
        "chunk_size": 512,
        "chunk_overlap": 50,
        "parser_type": "sentence",
        "separator": "\n\n"
    },
    "retrieval_config": {
        "retrieval_mode": "hybrid",
        "top_k": 5,
        "similarity_threshold": 0.3,
        "vector_weight": 0.5,
        "enable_rerank": False
    },
    "embedding_dimension": 1024
}

kb = client.create_knowledge_base(kb_data)
print(f"Created KB: {kb['id']}")
```

### Update Knowledge Base

```python
kb_id = "kb_123"
updates = {
    "description": "Updated description",
    "retrieval_config": {
        "top_k": 10,
        "similarity_threshold": 0.4
    }
}

kb = client.update_knowledge_base(kb_id, updates)
print(f"Updated KB: {kb['name']}")
```

### Delete Knowledge Base

```python
kb_id = "kb_123"
client.delete_knowledge_base(kb_id)
print("Knowledge base deleted")
```

## File Operations

### List Files

```python
kb_id = "kb_123"

# List all files
result = client.list_files(kb_id, page=1, size=20)

# Filter by status
result = client.list_files(kb_id, status="succeeded")

# Search by filename
result = client.list_files(kb_id, query="report")

for file in result['items']:
    print(f"- {file['file_name']} ({file['status']})")
```

### Upload Single File

```python
kb_id = "kb_123"
file_path = "/path/to/document.pdf"

file_info = client.upload_file(kb_id, file_path)
print(f"Uploaded: {file_info['file_name']}")
print(f"File ID: {file_info['id']}")
print(f"Status: {file_info['status']}")
```

### Upload Multiple Files (Streamlit)

```python
import streamlit as st
from rag5.interfaces.ui.pages.knowledge_base import KnowledgeBaseAPIClient

# In Streamlit app
uploaded_files = st.file_uploader(
    "Upload documents",
    accept_multiple_files=True,
    type=["txt", "pdf", "docx", "md"]
)

if uploaded_files:
    client = KnowledgeBaseAPIClient()
    
    with st.spinner("Uploading files..."):
        results = client.upload_files("kb_123", uploaded_files)
    
    st.success(f"Uploaded {len(results)} files")
    for result in results:
        st.write(f"✓ {result['file_name']}")
```

### Delete File

```python
kb_id = "kb_123"
file_id = "file_456"

client.delete_file(kb_id, file_id)
print("File deleted")
```

## Query Operations

### Query Knowledge Base

```python
kb_id = "kb_123"
query = "What is RAG?"

# Use default settings from KB
results = client.query_knowledge_base(kb_id, query)

# Override settings
results = client.query_knowledge_base(
    kb_id,
    query,
    top_k=10,
    similarity_threshold=0.5
)

for i, result in enumerate(results, 1):
    print(f"\nResult {i}:")
    print(f"Score: {result['score']:.4f}")
    print(f"Text: {result['text'][:200]}...")
    print(f"Source: {result['source']}")
```

## Error Handling

The client provides specific exception types for different error scenarios:

```python
from rag5.interfaces.ui.pages.knowledge_base import (
    KnowledgeBaseAPIClient,
    APIConnectionError,
    APITimeoutError,
    APIHTTPError
)

client = KnowledgeBaseAPIClient()

try:
    kb = client.get_knowledge_base("kb_123")
    
except APIConnectionError as e:
    print(f"Cannot connect to API: {e}")
    print("Please ensure the API server is running")
    
except APITimeoutError as e:
    print(f"Request timed out: {e}")
    print("Try increasing the timeout or check server performance")
    
except APIHTTPError as e:
    print(f"HTTP Error {e.status_code}: {e}")
    
    if e.status_code == 404:
        print("Knowledge base not found")
    elif e.status_code == 400:
        print("Invalid request parameters")
    elif e.status_code == 409:
        print("Resource already exists")
    elif e.status_code == 500:
        print("Server error")
        
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Health Check

Check if the API is accessible:

```python
client = KnowledgeBaseAPIClient()

if client.health_check():
    print("✓ API is accessible")
else:
    print("✗ API is not accessible")
```

## Configuration

### Environment Variables

The client respects the following environment variables:

- `API_BASE_URL`: Base URL of the API (default: `http://localhost:8000`)

```bash
export API_BASE_URL=http://api.example.com:8000
```

### Timeout Configuration

```python
# Short timeout for quick operations
client = KnowledgeBaseAPIClient(timeout=10)

# Long timeout for file uploads
client = KnowledgeBaseAPIClient(timeout=120)
```

### Retry Configuration

```python
# More aggressive retry strategy
client = KnowledgeBaseAPIClient(
    max_retries=5,
    backoff_factor=0.5
)
```

## Best Practices

### 1. Use Context Manager

Always use the context manager to ensure proper cleanup:

```python
with KnowledgeBaseAPIClient() as client:
    # Your operations here
    pass
```

### 2. Handle Errors Gracefully

Always wrap API calls in try-except blocks:

```python
try:
    result = client.list_knowledge_bases()
except APIConnectionError:
    st.error("Cannot connect to API. Please check if the server is running.")
except Exception as e:
    st.error(f"An error occurred: {e}")
```

### 3. Use Pagination

For large datasets, use pagination to avoid loading too much data:

```python
page = 1
size = 20

while True:
    result = client.list_knowledge_bases(page=page, size=size)
    
    # Process items
    for kb in result['items']:
        process_kb(kb)
    
    # Check if there are more pages
    if page * size >= result['total']:
        break
    
    page += 1
```

### 4. Validate Input

Validate user input before making API calls:

```python
def create_kb_safely(name, description, embedding_model):
    # Validate inputs
    if not name or len(name) < 2:
        raise ValueError("Name must be at least 2 characters")
    
    if len(name) > 64:
        raise ValueError("Name must be at most 64 characters")
    
    # Make API call
    kb_data = {
        "name": name,
        "description": description,
        "embedding_model": embedding_model
    }
    
    return client.create_knowledge_base(kb_data)
```

### 5. Log Operations

Use logging for debugging and monitoring:

```python
import logging

logger = logging.getLogger(__name__)

try:
    kb = client.create_knowledge_base(kb_data)
    logger.info(f"Created knowledge base: {kb['id']}")
except Exception as e:
    logger.error(f"Failed to create knowledge base: {e}", exc_info=True)
    raise
```

## Streamlit Integration Example

Complete example of using the API client in a Streamlit app:

```python
import streamlit as st
from rag5.interfaces.ui.pages.knowledge_base import (
    KnowledgeBaseAPIClient,
    APIConnectionError
)

def main():
    st.title("Knowledge Base Manager")
    
    # Initialize client
    client = KnowledgeBaseAPIClient()
    
    # Check API health
    if not client.health_check():
        st.error("⚠️ Cannot connect to API. Please ensure the server is running.")
        return
    
    # List knowledge bases
    try:
        result = client.list_knowledge_bases(page=1, size=10)
        
        st.subheader(f"Knowledge Bases ({result['total']})")
        
        for kb in result['items']:
            with st.expander(kb['name']):
                st.write(f"**ID:** {kb['id']}")
                st.write(f"**Description:** {kb['description']}")
                st.write(f"**Documents:** {kb['document_count']}")
                
                if st.button("Delete", key=f"del_{kb['id']}"):
                    client.delete_knowledge_base(kb['id'])
                    st.success("Deleted!")
                    st.rerun()
    
    except APIConnectionError:
        st.error("Failed to load knowledge bases")
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Connection Refused

**Problem:** `APIConnectionError: Unable to connect to API`

**Solution:**
1. Ensure the API server is running
2. Check the base URL is correct
3. Verify firewall settings

### Timeout Errors

**Problem:** `APITimeoutError: Request timed out`

**Solution:**
1. Increase timeout: `KnowledgeBaseAPIClient(timeout=60)`
2. Check server performance
3. Reduce request size (e.g., smaller page size)

### 404 Not Found

**Problem:** `APIHTTPError: Resource not found`

**Solution:**
1. Verify the resource ID is correct
2. Check if the resource was deleted
3. Ensure you're using the correct endpoint

### 409 Conflict

**Problem:** `APIHTTPError: Conflict`

**Solution:**
1. Check if a resource with the same name already exists
2. Use a different name or update the existing resource

## API Reference

See the inline documentation in `api_client.py` for detailed API reference.
