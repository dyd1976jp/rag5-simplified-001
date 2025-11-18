"""
Knowledge Base API Client

This module provides a client for interacting with the Knowledge Base API.
"""

import logging
import os
from typing import List, Dict, Optional, Any, BinaryIO
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors"""
    pass


class APIConnectionError(APIError):
    """Exception raised when unable to connect to API"""
    pass


class APITimeoutError(APIError):
    """Exception raised when API request times out"""
    pass


class APIHTTPError(APIError):
    """Exception raised for HTTP errors"""
    
    def __init__(self, message: str, status_code: int, response_text: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class KnowledgeBaseAPIClient:
    """
    Client for Knowledge Base API operations.
    
    Provides methods for managing knowledge bases, files, and queries with
    built-in error handling, retry logic, and timeout configuration.
    
    Example:
        >>> client = KnowledgeBaseAPIClient()
        >>> kbs = client.list_knowledge_bases()
        >>> print(f"Found {kbs['total']} knowledge bases")
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.3
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API (defaults to http://localhost:8000)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
        """
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self.api_prefix = "/api/v1"
        self.timeout = timeout
        
        # Create session with retry logic
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.debug(f"Initialized API client with base URL: {self.base_url}")
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL
        """
        return urljoin(self.base_url, f"{self.api_prefix}{endpoint}")
    
    def _handle_response(self, response: requests.Response) -> Any:
        """
        Handle API response and raise appropriate exceptions.
        
        Args:
            response: Response object
            
        Returns:
            Parsed JSON response
            
        Raises:
            APIHTTPError: For HTTP errors
        """
        try:
            response.raise_for_status()
            
            # Handle 204 No Content
            if response.status_code == 204:
                return None
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code
            
            # Try to extract error message from response
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", str(e))
            except:
                error_msg = response.text or str(e)
            
            # Provide user-friendly error messages
            if status_code == 400:
                message = f"Invalid request: {error_msg}"
            elif status_code == 404:
                message = f"Resource not found: {error_msg}"
            elif status_code == 409:
                message = f"Conflict: {error_msg}"
            elif status_code == 500:
                message = f"Server error: {error_msg}"
            elif status_code == 503:
                message = "Service unavailable. Please ensure the API server is running."
            else:
                message = f"HTTP {status_code}: {error_msg}"
            
            logger.error(f"API HTTP error: {message}")
            raise APIHTTPError(message, status_code, response.text)
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data
            
        Raises:
            APIConnectionError: If connection fails
            APITimeoutError: If request times out
            APIHTTPError: For HTTP errors
        """
        url = self._build_url(endpoint)
        
        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        
        try:
            logger.debug(f"{method} {url}")
            response = self.session.request(method, url, **kwargs)
            return self._handle_response(response)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Unable to connect to API at {self.base_url}. Please ensure the server is running."
            logger.error(f"Connection error: {e}")
            raise APIConnectionError(error_msg) from e
            
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timed out after {self.timeout} seconds"
            logger.error(f"Timeout error: {e}")
            raise APITimeoutError(error_msg) from e
    
    # ==================== Knowledge Base Operations ====================
    
    def list_knowledge_bases(
        self,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        Get list of knowledge bases.
        
        Args:
            page: Page number (starting from 1)
            size: Number of items per page
            
        Returns:
            Dictionary with 'items', 'total', 'page', 'size' keys
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> result = client.list_knowledge_bases(page=1, size=10)
            >>> for kb in result['items']:
            ...     print(kb['name'])
        """
        params = {"page": page, "size": size}
        return self._request("GET", "/knowledge-bases", params=params)
    
    def get_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """
        Get knowledge base details.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            Knowledge base details
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> kb = client.get_knowledge_base("kb_123")
            >>> print(kb['name'])
        """
        return self._request("GET", f"/knowledge-bases/{kb_id}")
    
    def create_knowledge_base(self, kb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new knowledge base.
        
        Args:
            kb_data: Knowledge base configuration including:
                - name (str): Knowledge base name
                - description (str): Description
                - embedding_model (str): Embedding model name
                - chunk_config (dict, optional): Chunk configuration
                - retrieval_config (dict, optional): Retrieval configuration
                - embedding_dimension (int, optional): Vector dimension
                
        Returns:
            Created knowledge base details
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> kb_data = {
            ...     "name": "My KB",
            ...     "description": "Test knowledge base",
            ...     "embedding_model": "BAAI/bge-m3",
            ...     "chunk_config": {
            ...         "chunk_size": 512,
            ...         "chunk_overlap": 50
            ...     }
            ... }
            >>> kb = client.create_knowledge_base(kb_data)
            >>> print(f"Created KB: {kb['id']}")
        """
        return self._request("POST", "/knowledge-bases", json=kb_data)

    def list_embedding_models(self, include_all: bool = False) -> Dict[str, Any]:
        """
        获取可用的嵌入模型列表。

        Args:
            include_all: 是否包含所有 Ollama 模型（不仅仅是嵌入模型）

        Returns:
            包含 models、default_model 等信息的字典

        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> result = client.list_embedding_models()
            >>> for model in result['models']:
            ...     print(model['name'], model.get('dimension'))
        """
        params = {"include_all": include_all}
        return self._request("GET", "/knowledge-bases/embedding-models", params=params)
    
    def update_knowledge_base(
        self,
        kb_id: str,
        kb_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update knowledge base configuration.
        
        Args:
            kb_id: Knowledge base ID
            kb_data: Fields to update (name, description, chunk_config, retrieval_config)
            
        Returns:
            Updated knowledge base details
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> updates = {
            ...     "description": "Updated description",
            ...     "retrieval_config": {
            ...         "top_k": 10
            ...     }
            ... }
            >>> kb = client.update_knowledge_base("kb_123", updates)
        """
        return self._request("PUT", f"/knowledge-bases/{kb_id}", json=kb_data)
    
    def delete_knowledge_base(self, kb_id: str) -> None:
        """
        Delete a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> client.delete_knowledge_base("kb_123")
        """
        self._request("DELETE", f"/knowledge-bases/{kb_id}")
    
    # ==================== File Operations ====================
    
    def list_files(
        self,
        kb_id: str,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get list of files in a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            page: Page number (starting from 1)
            size: Number of items per page
            status: Filter by status (pending, parsing, persisting, succeeded, failed)
            query: Search query for file names
            
        Returns:
            Dictionary with 'items', 'total', 'page', 'size' keys
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> result = client.list_files("kb_123", status="succeeded")
            >>> print(f"Found {result['total']} files")
        """
        params = {"page": page, "size": size}
        if status:
            params["status"] = status
        if query:
            params["query"] = query
        
        return self._request("GET", f"/knowledge-bases/{kb_id}/files", params=params)
    
    def upload_file(
        self,
        kb_id: str,
        file_path: str,
        file_name: Optional[str] = None,
        file_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a single file to knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            file_path: Path to file to upload
            file_name: Optional custom file name (defaults to basename of file_path)
            file_source: Optional original page URL to persist with file metadata
            
        Returns:
            Created file entity details
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> file_info = client.upload_file("kb_123", "/path/to/doc.pdf")
            >>> print(f"Uploaded: {file_info['file_name']}")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_name is None:
            file_name = os.path.basename(file_path)
        
        with open(file_path, "rb") as f:
            params = {}
            if file_source:
                params["file_source"] = file_source

            files = {"file": (file_name, f)}
            return self._request(
                "POST",
                f"/knowledge-bases/{kb_id}/files",
                files=files,
                params=params or None
            )
    
    def upload_files(
        self,
        kb_id: str,
        files: List[Any],
        original_page_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple files to knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            files: List of file objects (from Streamlit file_uploader)
            original_page_url: Optional URL tying all uploaded files to their source page
            
        Returns:
            List of created file entity details
            
        Example:
            >>> # In Streamlit context
            >>> uploaded_files = st.file_uploader("Upload", accept_multiple_files=True)
            >>> if uploaded_files:
            ...     results = client.upload_files("kb_123", uploaded_files)
            ...     print(f"Uploaded {len(results)} files")
        """
        results = []
        
        params = {}
        if original_page_url:
            params["file_source"] = original_page_url

        for file in files:
            try:
                # Handle Streamlit UploadedFile objects
                if hasattr(file, 'name') and hasattr(file, 'read'):
                    file_name = file.name
                    file_content = file.read()
                    
                    # Reset file pointer if possible
                    if hasattr(file, 'seek'):
                        file.seek(0)
                    
                    files_data = {"file": (file_name, file_content)}
                    result = self._request(
                        "POST",
                        f"/knowledge-bases/{kb_id}/files",
                        files=files_data,
                        params=params or None
                    )
                    results.append(result)
                else:
                    logger.warning(f"Skipping invalid file object: {file}")
                    
            except Exception as e:
                logger.error(f"Failed to upload file {getattr(file, 'name', 'unknown')}: {e}")
                # Continue with other files
                
        return results
    
    def delete_file(self, kb_id: str, file_id: str) -> None:
        """
        Delete a file from knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            file_id: File ID
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> client.delete_file("kb_123", "file_456")
        """
        self._request("DELETE", f"/knowledge-bases/{kb_id}/files/{file_id}")
    
    def reprocess_file(self, kb_id: str, file_id: str) -> Dict[str, Any]:
        """
        Reprocess a failed file.
        
        Note: This endpoint is not yet implemented in the backend.
        This method is a placeholder for future implementation.
        
        Args:
            kb_id: Knowledge base ID
            file_id: File ID
            
        Returns:
            File entity details after reprocessing is queued
            
        Raises:
            APIHTTPError: If the endpoint is not implemented (501)
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> try:
            ...     result = client.reprocess_file("kb_123", "file_456")
            ... except APIHTTPError as e:
            ...     if e.status_code == 501:
            ...         print("Reprocess endpoint not yet implemented")
        """
        # This endpoint doesn't exist yet in the backend
        # When implemented, it should be: POST /knowledge-bases/{kb_id}/files/{file_id}/reprocess
        try:
            return self._request("POST", f"/knowledge-bases/{kb_id}/files/{file_id}/reprocess")
        except APIHTTPError as e:
            if e.status_code == 404:
                # Endpoint not found - not implemented yet
                raise APIHTTPError(
                    "File reprocess endpoint not yet implemented in backend",
                    501,
                    "Not Implemented"
                )
            raise
    
    # ==================== Query Operations ====================
    
    def query_knowledge_base(
        self,
        kb_id: str,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Query knowledge base for relevant documents.
        
        Args:
            kb_id: Knowledge base ID
            query: Search query
            top_k: Number of results to return (overrides KB default)
            similarity_threshold: Minimum similarity score (overrides KB default)
            
        Returns:
            List of query results with scores and content
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> results = client.query_knowledge_base(
            ...     "kb_123",
            ...     "What is RAG?",
            ...     top_k=5
            ... )
            >>> for result in results:
            ...     print(f"Score: {result['score']:.3f}")
            ...     print(f"Text: {result['text'][:100]}...")
        """
        data = {"query": query}
        if top_k is not None:
            data["top_k"] = top_k
        if similarity_threshold is not None:
            data["similarity_threshold"] = similarity_threshold
        
        response = self._request(
            "POST",
            f"/knowledge-bases/{kb_id}/query",
            json=data
        )
        
        # Return just the results list
        return response.get("results", [])
    
    # ==================== Health Check ====================
    
    def health_check(self) -> bool:
        """
        Check if API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
            
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> if client.health_check():
            ...     print("API is accessible")
            ... else:
            ...     print("API is not accessible")
        """
        try:
            # Try to list knowledge bases as a health check
            self.list_knowledge_bases(page=1, size=1)
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def close(self):
        """
        Close the session and cleanup resources.
        
        Example:
            >>> client = KnowledgeBaseAPIClient()
            >>> try:
            ...     # Use client
            ...     pass
            ... finally:
            ...     client.close()
        """
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
