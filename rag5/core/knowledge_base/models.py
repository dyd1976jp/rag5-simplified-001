"""
知识库管理数据模型

定义知识库、文件实体和相关配置的数据模型。
"""

import re
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ChunkConfig(BaseModel):
    """文档分块配置"""
    chunk_size: int = Field(default=512, ge=100, le=2048)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    parser_type: str = Field(default="sentence")
    separator: str = Field(default="\n\n")
    
    @field_validator("parser_type")
    @classmethod
    def validate_parser_type(cls, v: str) -> str:
        """验证解析器类型"""
        allowed_types = ["sentence", "recursive", "semantic"]
        if v not in allowed_types:
            raise ValueError(
                f"parser_type 必须是以下之一: {', '.join(allowed_types)}"
            )
        return v
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """验证重叠大小不超过块大小"""
        # Note: chunk_size validation happens first due to field order
        # We'll do a runtime check in the model_validator
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """模型初始化后验证"""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")


class RetrievalConfig(BaseModel):
    """文档检索配置"""
    retrieval_mode: str = Field(default="hybrid")
    top_k: int = Field(default=5, ge=1, le=100)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    vector_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    enable_rerank: bool = Field(default=False)
    rerank_model: str = Field(default="")
    
    @field_validator("retrieval_mode")
    @classmethod
    def validate_retrieval_mode(cls, v: str) -> str:
        """验证检索模式"""
        allowed_modes = ["vector", "fulltext", "hybrid"]
        if v not in allowed_modes:
            raise ValueError(
                f"retrieval_mode 必须是以下之一: {', '.join(allowed_modes)}"
            )
        return v


class KnowledgeBase(BaseModel):
    """知识库实体"""
    id: str
    name: str
    description: str = Field(default="")
    embedding_model: str
    chunk_config: ChunkConfig = Field(default_factory=ChunkConfig)
    retrieval_config: RetrievalConfig = Field(default_factory=RetrievalConfig)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 统计信息（计算得出）
    document_count: int = Field(default=0, ge=0)
    total_size: int = Field(default=0, ge=0)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证知识库名称格式"""
        if not v:
            raise ValueError("知识库名称不能为空")
        
        # 只允许字母、数字、下划线和连字符
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                "知识库名称只能包含字母、数字、下划线和连字符"
            )
        
        # 长度限制
        if len(v) < 2 or len(v) > 64:
            raise ValueError("知识库名称长度必须在 2-64 个字符之间")
        
        return v
    
    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, v: str) -> str:
        """验证嵌入模型不为空"""
        if not v or not v.strip():
            raise ValueError("embedding_model 不能为空")
        return v.strip()
    
    def model_post_init(self, __context: Any) -> None:
        """模型初始化后处理"""
        # 确保 updated_at 不早于 created_at
        if self.updated_at < self.created_at:
            self.updated_at = self.created_at


class FileStatus(str, Enum):
    """文件处理状态"""
    PENDING = "pending"
    PARSING = "parsing"
    PERSISTING = "persisting"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileEntity(BaseModel):
    """知识库中的文件实体"""
    id: str
    kb_id: str
    file_name: str
    file_path: str
    file_extension: str
    file_size: int = Field(ge=0)
    file_md5: str
    status: FileStatus = Field(default=FileStatus.PENDING)
    failed_reason: Optional[str] = Field(default=None)
    chunk_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        """验证文件名不为空"""
        if not v or not v.strip():
            raise ValueError("文件名不能为空")
        return v.strip()
    
    @field_validator("file_extension")
    @classmethod
    def validate_file_extension(cls, v: str) -> str:
        """验证文件扩展名"""
        if not v:
            raise ValueError("文件扩展名不能为空")
        
        # 确保扩展名以点开头
        if not v.startswith("."):
            v = f".{v}"
        
        # 支持的文件格式
        supported_formats = [".txt", ".md", ".pdf", ".docx"]
        if v.lower() not in supported_formats:
            raise ValueError(
                f"不支持的文件格式: {v}。支持的格式: {', '.join(supported_formats)}"
            )
        
        return v.lower()
    
    @field_validator("file_md5")
    @classmethod
    def validate_file_md5(cls, v: str) -> str:
        """验证 MD5 哈希格式"""
        if not v:
            raise ValueError("file_md5 不能为空")
        
        # MD5 哈希应该是 32 个十六进制字符
        if not re.match(r'^[a-fA-F0-9]{32}$', v):
            raise ValueError("file_md5 必须是有效的 MD5 哈希值（32 个十六进制字符）")
        
        return v.lower()
    
    def model_post_init(self, __context: Any) -> None:
        """模型初始化后处理"""
        # 确保 updated_at 不早于 created_at
        if self.updated_at < self.created_at:
            self.updated_at = self.created_at
