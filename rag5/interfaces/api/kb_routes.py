"""
Knowledge Base API Routes

This module provides FastAPI routes for knowledge base management operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel, Field, field_validator

from rag5.core.knowledge_base import (
    KnowledgeBaseManager,
    KnowledgeBase,
    ChunkConfig,
    RetrievalConfig,
    FileEntity,
    FileStatus,
    KnowledgeBaseError,
    KnowledgeBaseNotFoundError,
    KnowledgeBaseAlreadyExistsError,
    KnowledgeBaseValidationError,
    FileNotFoundError as KBFileNotFoundError,
    FileValidationError
)

logger = logging.getLogger(__name__)

# Create router
kb_router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])

# Global manager instance (will be set by the app)
_kb_manager: Optional[KnowledgeBaseManager] = None


def set_kb_manager(manager: KnowledgeBaseManager):
    """Set the global knowledge base manager instance"""
    global _kb_manager
    _kb_manager = manager


def get_kb_manager() -> KnowledgeBaseManager:
    """Get the global knowledge base manager instance"""
    if _kb_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge base manager not initialized"
        )
    return _kb_manager


# ==================== Request/Response Models ====================

class ChunkConfigRequest(BaseModel):
    """Chunk configuration request model"""
    chunk_size: int = Field(default=512, ge=100, le=2048)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    parser_type: str = Field(default="sentence")
    separator: str = Field(default="\n\n")


class RetrievalConfigRequest(BaseModel):
    """Retrieval configuration request model"""
    retrieval_mode: str = Field(default="hybrid")
    top_k: int = Field(default=5, ge=1, le=100)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    vector_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    enable_rerank: bool = Field(default=False)
    rerank_model: str = Field(default="")


class CreateKBRequest(BaseModel):
    """Create knowledge base request"""
    name: str = Field(..., min_length=2, max_length=64)
    description: str = Field(default="")
    embedding_model: str = Field(...)
    chunk_config: Optional[ChunkConfigRequest] = None
    retrieval_config: Optional[RetrievalConfigRequest] = None
    embedding_dimension: Optional[int] = Field(default=None, ge=128, le=4096)


class UpdateKBRequest(BaseModel):
    """Update knowledge base request"""
    name: Optional[str] = Field(default=None, min_length=2, max_length=64)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_config: Optional[ChunkConfigRequest] = None
    retrieval_config: Optional[RetrievalConfigRequest] = None


class KBResponse(BaseModel):
    """Knowledge base response model"""
    id: str
    name: str
    description: str
    embedding_model: str
    chunk_config: dict
    retrieval_config: dict
    created_at: str
    updated_at: str
    document_count: int
    total_size: int


class KBListResponse(BaseModel):
    """Knowledge base list response"""
    items: List[KBResponse]
    total: int
    page: int
    size: int


class FileResponse(BaseModel):
    """File entity response model"""
    id: str
    kb_id: str
    file_name: str
    file_extension: str
    file_size: int
    status: str
    failed_reason: Optional[str]
    chunk_count: int
    created_at: str
    updated_at: str


class FileListResponse(BaseModel):
    """File list response"""
    items: List[FileResponse]
    total: int
    page: int
    size: int


class QueryRequest(BaseModel):
    """Query knowledge base request"""
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=100)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class QueryResult(BaseModel):
    """Query result item"""
    id: str
    score: float
    text: str
    file_id: str
    source: str
    chunk_index: int
    kb_id: str
    metadata: dict


class QueryResponse(BaseModel):
    """Query response"""
    results: List[QueryResult]
    query: str
    kb_id: str
    total_results: int


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str


# ==================== Helper Functions ====================

def kb_to_response(kb: KnowledgeBase) -> KBResponse:
    """Convert KnowledgeBase entity to response model"""
    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        embedding_model=kb.embedding_model,
        chunk_config=kb.chunk_config.model_dump(),
        retrieval_config=kb.retrieval_config.model_dump(),
        created_at=kb.created_at.isoformat(),
        updated_at=kb.updated_at.isoformat(),
        document_count=kb.document_count,
        total_size=kb.total_size
    )


def file_to_response(file: FileEntity) -> FileResponse:
    """Convert FileEntity to response model"""
    return FileResponse(
        id=file.id,
        kb_id=file.kb_id,
        file_name=file.file_name,
        file_extension=file.file_extension,
        file_size=file.file_size,
        status=file.status.value,
        failed_reason=file.failed_reason,
        chunk_count=file.chunk_count,
        created_at=file.created_at.isoformat(),
        updated_at=file.updated_at.isoformat()
    )


# ==================== API Endpoints ====================

@kb_router.post(
    "",
    response_model=KBResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        409: {"model": ErrorResponse, "description": "Knowledge base already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Create a new knowledge base",
    description="Create a new knowledge base with specified configuration"
)
async def create_knowledge_base(request: CreateKBRequest) -> KBResponse:
    """
    Create a new knowledge base.
    
    Args:
        request: Knowledge base creation request
        
    Returns:
        Created knowledge base details
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        manager = get_kb_manager()
        
        # Convert request models to domain models
        chunk_config = None
        if request.chunk_config:
            chunk_config = ChunkConfig(**request.chunk_config.model_dump())
        
        retrieval_config = None
        if request.retrieval_config:
            retrieval_config = RetrievalConfig(**request.retrieval_config.model_dump())
        
        # Create knowledge base
        kb = await manager.create_knowledge_base(
            name=request.name,
            description=request.description,
            embedding_model=request.embedding_model,
            chunk_config=chunk_config,
            retrieval_config=retrieval_config,
            embedding_dimension=request.embedding_dimension
        )
        
        logger.info(f"Created knowledge base: {kb.name} (ID: {kb.id})")
        return kb_to_response(kb)
        
    except KnowledgeBaseAlreadyExistsError as e:
        logger.warning(f"Knowledge base already exists: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except KnowledgeBaseValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge base: {str(e)}"
        )


@kb_router.get(
    "",
    response_model=KBListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="List all knowledge bases",
    description="Get a paginated list of all knowledge bases"
)
async def list_knowledge_bases(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Page size")
) -> KBListResponse:
    """
    List all knowledge bases with pagination.
    
    Args:
        page: Page number (starting from 1)
        size: Number of items per page
        
    Returns:
        Paginated list of knowledge bases
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        manager = get_kb_manager()
        
        kbs, total = await manager.list_knowledge_bases(page=page, size=size)
        
        items = [kb_to_response(kb) for kb in kbs]
        
        logger.info(f"Listed {len(items)} knowledge bases (total: {total})")
        return KBListResponse(
            items=items,
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        logger.error(f"Failed to list knowledge bases: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge bases: {str(e)}"
        )


@kb_router.get(
    "/{kb_id}",
    response_model=KBResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get knowledge base details",
    description="Get detailed information about a specific knowledge base"
)
async def get_knowledge_base(kb_id: str) -> KBResponse:
    """
    Get knowledge base by ID.
    
    Args:
        kb_id: Knowledge base ID
        
    Returns:
        Knowledge base details
        
    Raises:
        HTTPException: If knowledge base not found or retrieval fails
    """
    try:
        manager = get_kb_manager()
        
        kb = await manager.get_knowledge_base(kb_id)
        
        logger.info(f"Retrieved knowledge base: {kb.name} (ID: {kb_id})")
        return kb_to_response(kb)
        
    except KnowledgeBaseNotFoundError as e:
        logger.warning(f"Knowledge base not found: {kb_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge base: {str(e)}"
        )


@kb_router.put(
    "/{kb_id}",
    response_model=KBResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        409: {"model": ErrorResponse, "description": "Name already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Update knowledge base",
    description="Update knowledge base configuration"
)
async def update_knowledge_base(kb_id: str, request: UpdateKBRequest) -> KBResponse:
    """
    Update knowledge base configuration.
    
    Args:
        kb_id: Knowledge base ID
        request: Update request with fields to change
        
    Returns:
        Updated knowledge base details
        
    Raises:
        HTTPException: If update fails
    """
    try:
        manager = get_kb_manager()
        
        # Build updates dictionary
        updates = {}
        
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.embedding_model is not None:
            updates["embedding_model"] = request.embedding_model
        if request.chunk_config is not None:
            updates["chunk_config"] = ChunkConfig(**request.chunk_config.model_dump())
        if request.retrieval_config is not None:
            updates["retrieval_config"] = RetrievalConfig(**request.retrieval_config.model_dump())
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update knowledge base
        kb = await manager.update_knowledge_base(kb_id, **updates)
        
        logger.info(f"Updated knowledge base: {kb.name} (ID: {kb_id})")
        return kb_to_response(kb)
        
    except KnowledgeBaseNotFoundError as e:
        logger.warning(f"Knowledge base not found: {kb_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except KnowledgeBaseAlreadyExistsError as e:
        logger.warning(f"Name already exists: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except KnowledgeBaseValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update knowledge base: {str(e)}"
        )


@kb_router.delete(
    "/{kb_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Delete knowledge base",
    description="Delete a knowledge base and all its associated data"
)
async def delete_knowledge_base(kb_id: str):
    """
    Delete knowledge base.
    
    Args:
        kb_id: Knowledge base ID
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        manager = get_kb_manager()
        
        await manager.delete_knowledge_base(kb_id)
        
        logger.info(f"Deleted knowledge base: {kb_id}")
        return None
        
    except KnowledgeBaseNotFoundError as e:
        logger.warning(f"Knowledge base not found: {kb_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge base: {str(e)}"
        )


@kb_router.post(
    "/{kb_id}/files",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or request"},
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Upload file to knowledge base",
    description="Upload a document file to a knowledge base for processing"
)
async def upload_file(
    kb_id: str,
    file: UploadFile = File(..., description="File to upload")
) -> FileResponse:
    """
    Upload a file to knowledge base.
    
    Args:
        kb_id: Knowledge base ID
        file: File to upload
        
    Returns:
        Created file entity details
        
    Raises:
        HTTPException: If upload fails
    """
    import tempfile
    import os
    
    temp_file_path = None
    
    try:
        manager = get_kb_manager()
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required"
            )
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        # Upload file to knowledge base
        file_entity = await manager.upload_file(
            kb_id=kb_id,
            file_path=temp_file_path,
            file_name=file.filename
        )
        
        logger.info(f"Uploaded file: {file.filename} to KB {kb_id} (File ID: {file_entity.id})")
        return file_to_response(file_entity)
        
    except KnowledgeBaseNotFoundError as e:
        logger.warning(f"Knowledge base not found: {kb_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileValidationError as e:
        logger.warning(f"File validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to upload file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@kb_router.get(
    "/{kb_id}/files",
    response_model=FileListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="List files in knowledge base",
    description="Get a paginated list of files in a knowledge base"
)
async def list_files(
    kb_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by file status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Page size")
) -> FileListResponse:
    """
    List files in knowledge base.
    
    Args:
        kb_id: Knowledge base ID
        status_filter: Optional status filter (pending, parsing, persisting, succeeded, failed, cancelled)
        page: Page number (starting from 1)
        size: Number of items per page
        
    Returns:
        Paginated list of files
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        manager = get_kb_manager()
        
        # Parse status filter
        file_status = None
        if status_filter:
            try:
                file_status = FileStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}. Valid values: pending, parsing, persisting, succeeded, failed, cancelled"
                )
        
        files, total = await manager.list_files(
            kb_id=kb_id,
            status=file_status,
            page=page,
            size=size
        )
        
        items = [file_to_response(f) for f in files]
        
        logger.info(f"Listed {len(items)} files in KB {kb_id} (total: {total})")
        return FileListResponse(
            items=items,
            total=total,
            page=page,
            size=size
        )
        
    except KnowledgeBaseNotFoundError as e:
        logger.warning(f"Knowledge base not found: {kb_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to list files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )


@kb_router.delete(
    "/{kb_id}/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base or file not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Delete file from knowledge base",
    description="Delete a file and all its associated chunks from a knowledge base"
)
async def delete_file(kb_id: str, file_id: str):
    """
    Delete file from knowledge base.
    
    Args:
        kb_id: Knowledge base ID
        file_id: File ID
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        manager = get_kb_manager()
        
        await manager.delete_file(kb_id=kb_id, file_id=file_id)
        
        logger.info(f"Deleted file {file_id} from KB {kb_id}")
        return None
        
    except (KnowledgeBaseNotFoundError, KBFileNotFoundError) as e:
        logger.warning(f"Resource not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileValidationError as e:
        logger.warning(f"File validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@kb_router.post(
    "/{kb_id}/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query"},
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Query knowledge base",
    description="Search for relevant documents in a knowledge base"
)
async def query_knowledge_base(kb_id: str, request: QueryRequest) -> QueryResponse:
    """
    Query knowledge base.
    
    Args:
        kb_id: Knowledge base ID
        request: Query request
        
    Returns:
        Query results with relevant documents
        
    Raises:
        HTTPException: If query fails
    """
    try:
        manager = get_kb_manager()
        
        results = await manager.query_knowledge_base(
            kb_id=kb_id,
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        # Convert results to response model
        query_results = [
            QueryResult(
                id=r["id"],
                score=r["score"],
                text=r["text"],
                file_id=r["file_id"],
                source=r["source"],
                chunk_index=r["chunk_index"],
                kb_id=r["kb_id"],
                metadata=r["metadata"]
            )
            for r in results
        ]
        
        logger.info(f"Query KB {kb_id}: found {len(query_results)} results")
        return QueryResponse(
            results=query_results,
            query=request.query,
            kb_id=kb_id,
            total_results=len(query_results)
        )
        
    except KnowledgeBaseNotFoundError as e:
        logger.warning(f"Knowledge base not found: {kb_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Invalid query: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to query knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query knowledge base: {str(e)}"
        )
