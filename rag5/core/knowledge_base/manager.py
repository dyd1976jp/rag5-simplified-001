"""
知识库管理器

核心服务类，协调数据库、向量存储和缓存层，提供完整的知识库管理功能。
"""

import hashlib
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any, BinaryIO

from rag5.core.knowledge_base.models import (
    KnowledgeBase,
    ChunkConfig,
    RetrievalConfig,
    FileEntity,
    FileStatus
)
from rag5.core.knowledge_base.database import KnowledgeBaseDatabase
from rag5.core.knowledge_base.provider import KnowledgeBaseProvider
from rag5.core.knowledge_base.vector_manager import VectorStoreManager

logger = logging.getLogger(__name__)


class KnowledgeBaseError(Exception):
    """知识库操作异常基类"""
    pass


class KnowledgeBaseNotFoundError(KnowledgeBaseError):
    """知识库不存在异常"""
    pass


class KnowledgeBaseAlreadyExistsError(KnowledgeBaseError):
    """知识库已存在异常"""
    pass


class KnowledgeBaseValidationError(KnowledgeBaseError):
    """知识库验证异常"""
    pass


class FileNotFoundError(KnowledgeBaseError):
    """文件不存在异常"""
    pass


class FileValidationError(KnowledgeBaseError):
    """文件验证异常"""
    pass


class KnowledgeBaseManager:
    """
    知识库管理器
    
    核心服务类，提供知识库的完整生命周期管理：
    - 创建、更新、删除知识库
    - 列出和查询知识库
    - 协调数据库、向量存储和缓存层
    - 处理错误和事务
    
    属性:
        db: 数据库操作实例
        vector_manager: 向量存储管理器
        provider: 内存缓存提供者
    
    示例:
        >>> from rag5.core.knowledge_base import KnowledgeBaseManager
        >>> from rag5.tools.vectordb import QdrantManager
        >>>
        >>> # 初始化管理器
        >>> qdrant = QdrantManager("http://localhost:6333")
        >>> manager = KnowledgeBaseManager(
        ...     db_path="./data/kb.db",
        ...     qdrant_manager=qdrant
        ... )
        >>>
        >>> # 创建知识库
        >>> kb = await manager.create_knowledge_base(
        ...     name="my_kb",
        ...     description="My knowledge base",
        ...     embedding_model="nomic-embed-text"
        ... )
        >>>
        >>> # 列出知识库
        >>> kbs, total = await manager.list_knowledge_bases(page=1, size=10)
        >>>
        >>> # 获取知识库详情
        >>> kb = await manager.get_knowledge_base(kb_id="kb_123")
        >>>
        >>> # 更新知识库
        >>> updated_kb = await manager.update_knowledge_base(
        ...     kb_id="kb_123",
        ...     description="Updated description"
        ... )
        >>>
        >>> # 删除知识库
        >>> success = await manager.delete_knowledge_base(kb_id="kb_123")
    """
    
    # 支持的文件格式
    SUPPORTED_FORMATS = [".txt", ".md", ".pdf", ".docx"]
    
    # 默认文件大小限制（100MB）
    DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024
    
    def __init__(
        self,
        db_path: str,
        qdrant_manager,
        file_storage_path: str = "./docs",
        embedding_dimension: int = 1024,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE
    ):
        """
        初始化知识库管理器
        
        参数:
            db_path: SQLite 数据库文件路径
            qdrant_manager: Qdrant 管理器实例
            file_storage_path: 文件存储路径
            embedding_dimension: 默认向量维度
            max_file_size: 最大文件大小（字节）
        """
        self.db = KnowledgeBaseDatabase(db_path)
        self.vector_manager = VectorStoreManager(qdrant_manager)
        self.provider = KnowledgeBaseProvider()
        self.embedding_dimension = embedding_dimension
        self.file_storage_path = Path(file_storage_path)
        self.max_file_size = max_file_size
        
        # 确保文件存储目录存在
        self.file_storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"知识库管理器初始化完成 (db: {db_path}, storage: {file_storage_path})")
    
    async def initialize(self) -> int:
        """
        初始化管理器，从数据库加载知识库到缓存
        
        返回:
            加载的知识库数量
        
        示例:
            >>> count = await manager.initialize()
            >>> print(f"加载了 {count} 个知识库")
        """
        try:
            count = await self.provider.load_from_db(self.db)
            logger.info(f"知识库管理器初始化完成，加载 {count} 个知识库")
            return count
        except Exception as e:
            logger.error(f"初始化知识库管理器失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"初始化失败: {e}")
    
    async def create_knowledge_base(
        self,
        name: str,
        description: str,
        embedding_model: str,
        chunk_config: Optional[ChunkConfig] = None,
        retrieval_config: Optional[RetrievalConfig] = None,
        embedding_dimension: Optional[int] = None
    ) -> KnowledgeBase:
        """
        创建新知识库
        
        步骤:
        1. 验证名称唯一性和格式
        2. 创建数据库记录
        3. 初始化向量存储集合
        4. 添加到缓存
        5. 返回创建的实体
        
        参数:
            name: 知识库名称（唯一，字母数字下划线连字符）
            description: 知识库描述
            embedding_model: 嵌入模型名称
            chunk_config: 分块配置（可选，使用默认值）
            retrieval_config: 检索配置（可选，使用默认值）
            embedding_dimension: 向量维度（可选，使用默认值）
        
        返回:
            创建的知识库实体
        
        异常:
            KnowledgeBaseAlreadyExistsError: 名称已存在
            KnowledgeBaseValidationError: 验证失败
            KnowledgeBaseError: 创建失败
        
        示例:
            >>> kb = await manager.create_knowledge_base(
            ...     name="tech_docs",
            ...     description="Technical documentation",
            ...     embedding_model="nomic-embed-text",
            ...     chunk_config=ChunkConfig(chunk_size=1024)
            ... )
            >>> print(f"创建知识库: {kb.id}")
        """
        try:
            logger.info(f"开始创建知识库: {name}")
            
            # 1. 验证名称唯一性
            if self.provider.exists_by_name(name):
                raise KnowledgeBaseAlreadyExistsError(
                    f"知识库名称 '{name}' 已存在"
                )
            
            # 也检查数据库（防止缓存不一致）
            existing_kb = self.db.get_kb_by_name(name)
            if existing_kb:
                raise KnowledgeBaseAlreadyExistsError(
                    f"知识库名称 '{name}' 已存在"
                )
            
            # 2. 创建知识库实体
            kb_id = f"kb_{uuid.uuid4().hex}"
            
            # 使用默认配置（如果未提供）
            if chunk_config is None:
                chunk_config = ChunkConfig()
            if retrieval_config is None:
                retrieval_config = RetrievalConfig()
            
            kb = KnowledgeBase(
                id=kb_id,
                name=name,
                description=description,
                embedding_model=embedding_model,
                chunk_config=chunk_config,
                retrieval_config=retrieval_config,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.debug(f"知识库实体创建: {kb.id}")
            
            # 3. 创建数据库记录
            try:
                self.db.create_kb(kb)
                logger.debug(f"数据库记录创建成功: {kb.id}")
            except Exception as e:
                logger.error(f"创建数据库记录失败: {e}")
                raise KnowledgeBaseError(f"创建数据库记录失败: {e}")
            
            # 4. 初始化向量存储集合
            try:
                vector_dim = embedding_dimension or self.embedding_dimension
                await self.vector_manager.create_collection(
                    kb_id=kb.id,
                    embedding_dimension=vector_dim
                )
                logger.debug(f"向量集合创建成功: {kb.id}")
            except Exception as e:
                # 回滚：删除数据库记录
                logger.error(f"创建向量集合失败，回滚数据库记录: {e}")
                try:
                    self.db.delete_kb(kb.id)
                except Exception as rollback_error:
                    logger.error(f"回滚失败: {rollback_error}")
                raise KnowledgeBaseError(f"创建向量集合失败: {e}")
            
            # 5. 添加到缓存
            self.provider.add(kb)
            logger.debug(f"知识库添加到缓存: {kb.id}")
            
            logger.info(f"✓ 知识库创建成功: {name} (ID: {kb.id})")
            return kb
            
        except KnowledgeBaseError:
            raise
        except Exception as e:
            logger.error(f"创建知识库时发生未预期的错误: {e}", exc_info=True)
            raise KnowledgeBaseError(f"创建知识库失败: {e}")
    
    async def list_knowledge_bases(
        self,
        page: int = 1,
        size: int = 10
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        列出所有知识库（分页）
        
        参数:
            page: 页码（从 1 开始）
            size: 每页数量
        
        返回:
            (知识库列表, 总数)
        
        异常:
            KnowledgeBaseError: 查询失败
        
        示例:
            >>> kbs, total = await manager.list_knowledge_bases(page=1, size=10)
            >>> print(f"共 {total} 个知识库，当前页 {len(kbs)} 个")
            >>> for kb in kbs:
            ...     print(f"- {kb.name}: {kb.document_count} 个文档")
        """
        try:
            # 验证分页参数
            if page < 1:
                page = 1
            if size < 1:
                size = 10
            if size > 100:
                size = 100
            
            offset = (page - 1) * size
            
            logger.debug(f"列出知识库: page={page}, size={size}, offset={offset}")
            
            # 从数据库查询（包含最新统计信息）
            kbs, total = self.db.list_kbs(offset=offset, limit=size)
            
            logger.info(f"查询到 {len(kbs)} 个知识库（共 {total} 个）")
            return kbs, total
            
        except Exception as e:
            logger.error(f"列出知识库失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"列出知识库失败: {e}")
    
    async def get_knowledge_base(self, kb_id: str) -> KnowledgeBase:
        """
        获取知识库详情（包含统计信息）
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            知识库实体
        
        异常:
            KnowledgeBaseNotFoundError: 知识库不存在
            KnowledgeBaseError: 查询失败
        
        示例:
            >>> kb = await manager.get_knowledge_base("kb_123")
            >>> print(f"{kb.name}: {kb.document_count} 文档, {kb.total_size} 字节")
        """
        try:
            logger.debug(f"获取知识库: {kb_id}")
            
            # 从数据库查询（获取最新统计信息）
            kb = self.db.get_kb(kb_id)
            
            if not kb:
                raise KnowledgeBaseNotFoundError(
                    f"知识库不存在: {kb_id}"
                )
            
            logger.debug(f"找到知识库: {kb.name} (ID: {kb_id})")
            return kb
            
        except KnowledgeBaseNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取知识库失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"获取知识库失败: {e}")
    
    async def update_knowledge_base(
        self,
        kb_id: str,
        **updates
    ) -> KnowledgeBase:
        """
        更新知识库配置
        
        支持更新的字段:
        - name: 知识库名称
        - description: 描述
        - embedding_model: 嵌入模型（警告：需要重新嵌入）
        - chunk_config: 分块配置
        - retrieval_config: 检索配置
        
        参数:
            kb_id: 知识库 ID
            **updates: 要更新的字段
        
        返回:
            更新后的知识库实体
        
        异常:
            KnowledgeBaseNotFoundError: 知识库不存在
            KnowledgeBaseAlreadyExistsError: 新名称已存在
            KnowledgeBaseValidationError: 验证失败
            KnowledgeBaseError: 更新失败
        
        示例:
            >>> kb = await manager.update_knowledge_base(
            ...     kb_id="kb_123",
            ...     description="Updated description",
            ...     retrieval_config=RetrievalConfig(top_k=10)
            ... )
        """
        try:
            logger.info(f"更新知识库: {kb_id}")
            logger.debug(f"更新字段: {list(updates.keys())}")
            
            # 1. 验证知识库存在
            existing_kb = self.db.get_kb(kb_id)
            if not existing_kb:
                raise KnowledgeBaseNotFoundError(
                    f"知识库不存在: {kb_id}"
                )
            
            # 2. 验证名称唯一性（如果更新名称）
            if "name" in updates:
                new_name = updates["name"]
                if new_name != existing_kb.name:
                    # 检查新名称是否已被使用
                    if self.provider.exists_by_name(new_name):
                        raise KnowledgeBaseAlreadyExistsError(
                            f"知识库名称 '{new_name}' 已存在"
                        )
                    
                    # 也检查数据库
                    name_check = self.db.get_kb_by_name(new_name)
                    if name_check:
                        raise KnowledgeBaseAlreadyExistsError(
                            f"知识库名称 '{new_name}' 已存在"
                        )
            
            # 3. 检查嵌入模型变更（需要警告）
            if "embedding_model" in updates:
                new_model = updates["embedding_model"]
                if new_model != existing_kb.embedding_model:
                    logger.warning(
                        f"知识库 {kb_id} 的嵌入模型从 '{existing_kb.embedding_model}' "
                        f"变更为 '{new_model}'。现有文档需要重新嵌入。"
                    )
            
            # 4. 更新数据库
            updated_kb = self.db.update_kb(kb_id, **updates)
            
            if not updated_kb:
                raise KnowledgeBaseError(f"更新数据库失败: {kb_id}")
            
            logger.debug(f"数据库更新成功: {kb_id}")
            
            # 5. 更新缓存
            self.provider.update(updated_kb)
            logger.debug(f"缓存更新成功: {kb_id}")
            
            logger.info(f"✓ 知识库更新成功: {kb_id}")
            return updated_kb
            
        except (KnowledgeBaseNotFoundError, KnowledgeBaseAlreadyExistsError):
            raise
        except Exception as e:
            logger.error(f"更新知识库失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"更新知识库失败: {e}")
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        删除知识库及其所有关联数据
        
        步骤:
        1. 验证知识库存在
        2. 删除向量存储集合
        3. 删除数据库记录（级联删除文件记录）
        4. 从缓存中移除
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            是否成功删除
        
        异常:
            KnowledgeBaseNotFoundError: 知识库不存在
            KnowledgeBaseError: 删除失败
        
        示例:
            >>> success = await manager.delete_knowledge_base("kb_123")
            >>> if success:
            ...     print("知识库已删除")
        """
        try:
            logger.info(f"删除知识库: {kb_id}")
            
            # 1. 验证知识库存在
            kb = self.db.get_kb(kb_id)
            if not kb:
                raise KnowledgeBaseNotFoundError(
                    f"知识库不存在: {kb_id}"
                )
            
            kb_name = kb.name
            logger.debug(f"准备删除知识库: {kb_name} (ID: {kb_id})")
            
            # 2. 删除向量存储集合
            try:
                await self.vector_manager.delete_collection(kb_id)
                logger.debug(f"向量集合已删除: {kb_id}")
            except Exception as e:
                logger.warning(f"删除向量集合失败（继续删除）: {e}")
                # 继续删除，不因向量存储失败而中断
            
            # 3. 删除数据库记录（级联删除文件）
            deleted = self.db.delete_kb(kb_id)
            
            if not deleted:
                raise KnowledgeBaseError(f"删除数据库记录失败: {kb_id}")
            
            logger.debug(f"数据库记录已删除: {kb_id}")
            
            # 4. 从缓存中移除
            self.provider.delete(kb_id)
            logger.debug(f"缓存已清除: {kb_id}")
            
            logger.info(f"✓ 知识库删除成功: {kb_name} (ID: {kb_id})")
            return True
            
        except KnowledgeBaseNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除知识库失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"删除知识库失败: {e}")
    
    def get_kb_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """
        根据名称获取知识库（从缓存）
        
        参数:
            name: 知识库名称
        
        返回:
            知识库实体，如果不存在则返回 None
        
        示例:
            >>> kb = manager.get_kb_by_name("tech_docs")
            >>> if kb:
            ...     print(f"找到知识库: {kb.id}")
        """
        return self.provider.get_by_name(name)
    
    def get_kb_from_cache(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        从缓存获取知识库（不包含最新统计信息）
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            知识库实体，如果不存在则返回 None
        
        示例:
            >>> kb = manager.get_kb_from_cache("kb_123")
            >>> if kb:
            ...     print(f"缓存中的知识库: {kb.name}")
        """
        return self.provider.get(kb_id)
    
    async def refresh_cache(self) -> int:
        """
        刷新缓存，从数据库重新加载所有知识库
        
        返回:
            加载的知识库数量
        
        示例:
            >>> count = await manager.refresh_cache()
            >>> print(f"刷新了 {count} 个知识库")
        """
        try:
            count = await self.provider.load_from_db(self.db)
            logger.info(f"缓存刷新完成，加载 {count} 个知识库")
            return count
        except Exception as e:
            logger.error(f"刷新缓存失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"刷新缓存失败: {e}")
    
    # ==================== 文件管理操作 ====================
    
    async def upload_file(
        self,
        kb_id: str,
        file_path: str,
        file_name: Optional[str] = None
    ) -> FileEntity:
        """
        上传文件到知识库
        
        步骤:
        1. 验证知识库存在
        2. 验证文件格式和大小
        3. 计算 MD5 哈希
        4. 存储文件到文件系统
        5. 创建 FileEntity 记录（PENDING 状态）
        
        参数:
            kb_id: 知识库 ID
            file_path: 源文件路径
            file_name: 可选的文件名（默认使用源文件名）
        
        返回:
            创建的文件实体
        
        异常:
            KnowledgeBaseNotFoundError: 知识库不存在
            FileValidationError: 文件验证失败
            KnowledgeBaseError: 上传失败
        
        示例:
            >>> file = await manager.upload_file(
            ...     kb_id="kb_123",
            ...     file_path="/path/to/document.pdf",
            ...     file_name="my_document.pdf"
            ... )
            >>> print(f"文件已上传: {file.id}, 状态: {file.status}")
        """
        try:
            logger.info(f"开始上传文件到知识库 {kb_id}: {file_path}")
            
            # 1. 验证知识库存在
            kb = self.db.get_kb(kb_id)
            if not kb:
                raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")
            
            # 2. 验证文件存在
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileValidationError(f"文件不存在: {file_path}")
            
            if not source_path.is_file():
                raise FileValidationError(f"不是有效的文件: {file_path}")
            
            # 3. 获取文件信息
            if file_name is None:
                file_name = source_path.name
            
            file_extension = source_path.suffix.lower()
            file_size = source_path.stat().st_size
            
            # 4. 验证文件格式
            if file_extension not in self.SUPPORTED_FORMATS:
                raise FileValidationError(
                    f"不支持的文件格式: {file_extension}。"
                    f"支持的格式: {', '.join(self.SUPPORTED_FORMATS)}"
                )
            
            # 5. 验证文件大小
            if file_size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                actual_mb = file_size / (1024 * 1024)
                raise FileValidationError(
                    f"文件过大: {actual_mb:.2f}MB，最大允许: {max_mb:.2f}MB"
                )
            
            if file_size == 0:
                raise FileValidationError("文件为空")
            
            logger.debug(f"文件验证通过: {file_name} ({file_size} 字节)")
            
            # 6. 计算 MD5 哈希
            file_md5 = self._calculate_md5(source_path)
            logger.debug(f"文件 MD5: {file_md5}")
            
            # 7. 创建文件 ID 和存储路径
            file_id = f"file_{uuid.uuid4().hex}"
            
            # 使用知识库 ID 作为子目录
            kb_storage_dir = self.file_storage_path / kb_id
            kb_storage_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用文件 ID 作为文件名，保留扩展名
            stored_file_name = f"{file_id}{file_extension}"
            stored_file_path = kb_storage_dir / stored_file_name
            
            # 8. 复制文件到存储位置
            try:
                shutil.copy2(source_path, stored_file_path)
                logger.debug(f"文件已复制到: {stored_file_path}")
            except Exception as e:
                logger.error(f"复制文件失败: {e}")
                raise KnowledgeBaseError(f"存储文件失败: {e}")
            
            # 9. 创建 FileEntity 记录
            file_entity = FileEntity(
                id=file_id,
                kb_id=kb_id,
                file_name=file_name,
                file_path=str(stored_file_path),
                file_extension=file_extension,
                file_size=file_size,
                file_md5=file_md5,
                status=FileStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 10. 保存到数据库
            try:
                self.db.create_file(file_entity)
                logger.debug(f"文件记录已创建: {file_id}")
            except Exception as e:
                # 回滚：删除已存储的文件
                logger.error(f"创建文件记录失败，删除已存储的文件: {e}")
                try:
                    stored_file_path.unlink()
                except Exception as cleanup_error:
                    logger.error(f"清理文件失败: {cleanup_error}")
                raise KnowledgeBaseError(f"创建文件记录失败: {e}")
            
            logger.info(f"✓ 文件上传成功: {file_name} (ID: {file_id})")
            return file_entity
            
        except (KnowledgeBaseNotFoundError, FileValidationError):
            raise
        except Exception as e:
            logger.error(f"上传文件时发生未预期的错误: {e}", exc_info=True)
            raise KnowledgeBaseError(f"上传文件失败: {e}")
    
    async def list_files(
        self,
        kb_id: str,
        status: Optional[FileStatus] = None,
        page: int = 1,
        size: int = 10
    ) -> Tuple[List[FileEntity], int]:
        """
        列出知识库中的文件（分页）
        
        参数:
            kb_id: 知识库 ID
            status: 可选的状态过滤
            page: 页码（从 1 开始）
            size: 每页数量
        
        返回:
            (文件列表, 总数)
        
        异常:
            KnowledgeBaseNotFoundError: 知识库不存在
            KnowledgeBaseError: 查询失败
        
        示例:
            >>> files, total = await manager.list_files(
            ...     kb_id="kb_123",
            ...     status=FileStatus.SUCCEEDED,
            ...     page=1,
            ...     size=10
            ... )
            >>> print(f"共 {total} 个文件，当前页 {len(files)} 个")
            >>> for file in files:
            ...     print(f"- {file.file_name}: {file.status}")
        """
        try:
            logger.debug(f"列出知识库 {kb_id} 的文件: page={page}, size={size}, status={status}")
            
            # 验证知识库存在
            kb = self.db.get_kb(kb_id)
            if not kb:
                raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")
            
            # 验证分页参数
            if page < 1:
                page = 1
            if size < 1:
                size = 10
            if size > 100:
                size = 100
            
            offset = (page - 1) * size
            
            # 从数据库查询
            files, total = self.db.list_files(
                kb_id=kb_id,
                status=status,
                offset=offset,
                limit=size
            )
            
            logger.info(f"查询到 {len(files)} 个文件（共 {total} 个）")
            return files, total
            
        except KnowledgeBaseNotFoundError:
            raise
        except Exception as e:
            logger.error(f"列出文件失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"列出文件失败: {e}")
    
    async def delete_file(self, kb_id: str, file_id: str) -> bool:
        """
        删除文件及其关联数据
        
        步骤:
        1. 验证知识库和文件存在
        2. 从向量存储中删除文件的所有块
        3. 从文件系统中删除文件
        4. 从数据库中删除文件记录
        
        参数:
            kb_id: 知识库 ID
            file_id: 文件 ID
        
        返回:
            是否成功删除
        
        异常:
            KnowledgeBaseNotFoundError: 知识库不存在
            FileNotFoundError: 文件不存在
            KnowledgeBaseError: 删除失败
        
        示例:
            >>> success = await manager.delete_file("kb_123", "file_456")
            >>> if success:
            ...     print("文件已删除")
        """
        try:
            logger.info(f"删除文件: {file_id} (知识库: {kb_id})")
            
            # 1. 验证知识库存在
            kb = self.db.get_kb(kb_id)
            if not kb:
                raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")
            
            # 2. 验证文件存在
            file_entity = self.db.get_file(file_id)
            if not file_entity:
                raise FileNotFoundError(f"文件不存在: {file_id}")
            
            # 验证文件属于指定的知识库
            if file_entity.kb_id != kb_id:
                raise FileValidationError(
                    f"文件 {file_id} 不属于知识库 {kb_id}"
                )
            
            file_name = file_entity.file_name
            file_path = Path(file_entity.file_path)
            
            logger.debug(f"准备删除文件: {file_name} (ID: {file_id})")
            
            # 3. 从向量存储中删除文件的所有块
            if file_entity.status == FileStatus.SUCCEEDED and file_entity.chunk_count > 0:
                try:
                    await self.vector_manager.delete_by_file_id(kb_id, file_id)
                    logger.debug(f"向量数据已删除: {file_id}")
                except Exception as e:
                    logger.warning(f"删除向量数据失败（继续删除）: {e}")
                    # 继续删除，不因向量存储失败而中断
            
            # 4. 从文件系统中删除文件
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"文件已从存储中删除: {file_path}")
                except Exception as e:
                    logger.warning(f"删除存储文件失败（继续删除）: {e}")
                    # 继续删除，不因文件系统失败而中断
            else:
                logger.warning(f"存储文件不存在: {file_path}")
            
            # 5. 从数据库中删除文件记录
            deleted = self.db.delete_file(file_id)
            
            if not deleted:
                raise KnowledgeBaseError(f"删除文件记录失败: {file_id}")
            
            logger.debug(f"数据库记录已删除: {file_id}")
            
            logger.info(f"✓ 文件删除成功: {file_name} (ID: {file_id})")
            return True
            
        except (KnowledgeBaseNotFoundError, FileNotFoundError, FileValidationError):
            raise
        except Exception as e:
            logger.error(f"删除文件失败: {e}", exc_info=True)
            raise KnowledgeBaseError(f"删除文件失败: {e}")
    
    async def process_file(self, file_id: str) -> FileEntity:
        """
        处理上传的文件（异步后台任务）
        
        步骤:
        1. 更新状态为 PARSING
        2. 使用知识库的 ChunkConfig 加载和分块文档
        3. 更新状态为 PERSISTING
        4. 使用知识库的 embedding_model 生成嵌入
        5. 存储块到向量存储
        6. 更新状态为 SUCCEEDED
        7. 更新 chunk_count
        
        参数:
            file_id: 文件 ID
        
        返回:
            更新后的文件实体
        
        异常:
            FileNotFoundError: 文件不存在
            KnowledgeBaseError: 处理失败
        
        示例:
            >>> file = await manager.process_file("file_123")
            >>> print(f"处理完成: {file.status}, 块数: {file.chunk_count}")
        """
        try:
            logger.info(f"开始处理文件: {file_id}")
            
            # 获取文件记录
            file_entity = self.db.get_file(file_id)
            if not file_entity:
                raise FileNotFoundError(f"文件不存在: {file_id}")
            
            # 获取知识库配置
            kb = self.db.get_kb(file_entity.kb_id)
            if not kb:
                raise KnowledgeBaseError(
                    f"知识库不存在: {file_entity.kb_id}"
                )
            
            file_path = Path(file_entity.file_path)
            if not file_path.exists():
                raise FileNotFoundError(
                    f"文件不存在于存储中: {file_entity.file_path}"
                )
            
            logger.info(
                f"处理文件 {file_entity.file_name} "
                f"(知识库: {kb.name}, 模型: {kb.embedding_model})"
            )
            
            # ========== 步骤 1: 更新状态为 PARSING ==========
            logger.info("[1/5] 解析文档...")
            self.db.update_file_status(file_id, FileStatus.PARSING)
            
            try:
                # 导入加载器
                from rag5.ingestion.loaders import (
                    TextLoader, PDFLoader, MarkdownLoader
                )
                
                # 根据文件扩展名选择加载器
                loaders = {
                    ".txt": TextLoader(),
                    ".md": MarkdownLoader(),
                    ".pdf": PDFLoader(),
                    ".docx": None  # TODO: 添加 DOCX 加载器支持
                }
                
                loader = loaders.get(file_entity.file_extension.lower())
                if loader is None:
                    raise KnowledgeBaseError(
                        f"不支持的文件格式: {file_entity.file_extension}"
                    )
                
                # 加载文档
                logger.debug(f"使用加载器: {loader.__class__.__name__}")
                documents = loader.load(str(file_path))
                
                if not documents:
                    raise KnowledgeBaseError("文档加载失败：未提取到内容")
                
                total_chars = sum(len(doc.page_content) for doc in documents)
                logger.info(
                    f"✓ 加载了 {len(documents)} 个文档，"
                    f"共 {total_chars} 字符"
                )
                
            except Exception as e:
                error_msg = f"文档解析失败: {e}"
                logger.error(error_msg, exc_info=True)
                self.db.update_file_status(
                    file_id,
                    FileStatus.FAILED,
                    failed_reason=error_msg
                )
                raise KnowledgeBaseError(error_msg)
            
            # ========== 步骤 2: 分块文档 ==========
            logger.info("[2/5] 分块文档...")
            
            try:
                # 导入分块器
                from rag5.ingestion.splitters import (
                    RecursiveSplitter,
                    ChineseTextSplitter
                )
                from rag5.utils import ChineseTextDiagnostic
                
                # 使用知识库的 ChunkConfig
                chunk_config = kb.chunk_config
                logger.debug(
                    f"分块配置 - size: {chunk_config.chunk_size}, "
                    f"overlap: {chunk_config.chunk_overlap}, "
                    f"parser: {chunk_config.parser_type}"
                )
                
                # 检测文本语言并选择合适的分块器
                chinese_diagnostic = ChineseTextDiagnostic()
                sample_text = documents[0].page_content[:1000] if documents else ""
                
                try:
                    analysis = chinese_diagnostic.analyze_text(sample_text)
                    chinese_ratio = analysis.get('chinese_ratio', 0)
                    logger.debug(f"文本中文占比: {chinese_ratio:.1%}")
                    
                    # 如果中文占比超过 30%，使用中文分块器
                    if chinese_ratio >= 0.3:
                        logger.info("检测到中文文本，使用 ChineseTextSplitter")
                        splitter = ChineseTextSplitter(
                            chunk_size=chunk_config.chunk_size,
                            chunk_overlap=chunk_config.chunk_overlap,
                            respect_sentence_boundary=True
                        )
                    else:
                        logger.debug("使用 RecursiveSplitter")
                        splitter = RecursiveSplitter(
                            chunk_size=chunk_config.chunk_size,
                            chunk_overlap=chunk_config.chunk_overlap,
                            separators=[
                                chunk_config.separator,
                                "\n\n",
                                "\n",
                                " ",
                                ""
                            ]
                        )
                except Exception as diag_error:
                    logger.debug(f"文本诊断失败，使用默认分块器: {diag_error}")
                    splitter = RecursiveSplitter(
                        chunk_size=chunk_config.chunk_size,
                        chunk_overlap=chunk_config.chunk_overlap
                    )
                
                # 执行分块
                chunks = splitter.split_documents(documents)
                
                if not chunks:
                    raise KnowledgeBaseError("文档分块失败：未生成任何块")
                
                chunk_sizes = [len(chunk.page_content) for chunk in chunks]
                avg_size = sum(chunk_sizes) / len(chunk_sizes)
                logger.info(
                    f"✓ 创建了 {len(chunks)} 个块，"
                    f"平均大小: {avg_size:.0f} 字符"
                )
                
            except Exception as e:
                error_msg = f"文档分块失败: {e}"
                logger.error(error_msg, exc_info=True)
                self.db.update_file_status(
                    file_id,
                    FileStatus.FAILED,
                    failed_reason=error_msg
                )
                raise KnowledgeBaseError(error_msg)
            
            # ========== 步骤 3: 更新状态为 PERSISTING ==========
            logger.info("[3/5] 生成嵌入...")
            self.db.update_file_status(file_id, FileStatus.PERSISTING)
            
            try:
                # 导入嵌入管理器
                from rag5.tools.embeddings import OllamaEmbeddingsManager
                from rag5.config import settings
                
                # 使用知识库的 embedding_model
                embeddings_manager = OllamaEmbeddingsManager(
                    model_name=kb.embedding_model,
                    base_url=settings.ollama_host
                )
                
                logger.debug(f"使用嵌入模型: {kb.embedding_model}")
                
                # 提取文本内容
                texts = [chunk.page_content for chunk in chunks]
                
                # 批量生成嵌入
                logger.debug(f"生成 {len(texts)} 个嵌入向量...")
                embeddings = embeddings_manager.embed_documents(texts)
                
                if len(embeddings) != len(chunks):
                    raise KnowledgeBaseError(
                        f"嵌入数量 ({len(embeddings)}) 与块数量 ({len(chunks)}) 不匹配"
                    )
                
                logger.info(f"✓ 生成了 {len(embeddings)} 个嵌入向量")
                
            except Exception as e:
                error_msg = f"生成嵌入失败: {e}"
                logger.error(error_msg, exc_info=True)
                self.db.update_file_status(
                    file_id,
                    FileStatus.FAILED,
                    failed_reason=error_msg
                )
                raise KnowledgeBaseError(error_msg)
            
            # ========== 步骤 4: 存储到向量存储 ==========
            logger.info("[4/5] 存储向量...")
            
            try:
                # 准备块数据
                chunk_data = []
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_dict = {
                        "id": f"{file_id}_chunk_{i}",
                        "text": chunk.page_content,
                        "file_id": file_id,
                        "kb_id": file_entity.kb_id,
                        "source": file_entity.file_name,
                        "chunk_index": i,
                        "file_extension": file_entity.file_extension,
                    }
                    
                    # 添加文档的元数据
                    if hasattr(chunk, 'metadata') and chunk.metadata:
                        for key, value in chunk.metadata.items():
                            if key not in chunk_dict:
                                chunk_dict[key] = value
                    
                    chunk_data.append(chunk_dict)
                
                # 插入到向量存储
                inserted_count = await self.vector_manager.insert_chunks(
                    kb_id=file_entity.kb_id,
                    chunks=chunk_data,
                    embeddings=embeddings
                )
                
                if inserted_count != len(chunks):
                    logger.warning(
                        f"部分块插入失败: {inserted_count}/{len(chunks)}"
                    )
                
                logger.info(f"✓ 存储了 {inserted_count} 个向量")
                
            except Exception as e:
                error_msg = f"存储向量失败: {e}"
                logger.error(error_msg, exc_info=True)
                self.db.update_file_status(
                    file_id,
                    FileStatus.FAILED,
                    failed_reason=error_msg
                )
                raise KnowledgeBaseError(error_msg)
            
            # ========== 步骤 5: 更新状态为 SUCCEEDED ==========
            logger.info("[5/5] 完成处理...")
            
            updated_file = self.db.update_file_status(
                file_id,
                FileStatus.SUCCEEDED,
                chunk_count=len(chunks)
            )
            
            if not updated_file:
                raise KnowledgeBaseError(f"更新文件状态失败: {file_id}")
            
            logger.info(
                f"✓ 文件处理成功: {file_entity.file_name} "
                f"(块数: {len(chunks)})"
            )
            
            return updated_file
            
        except (FileNotFoundError, KnowledgeBaseError):
            raise
        except Exception as e:
            logger.error(f"处理文件时发生未预期的错误: {e}", exc_info=True)
            
            # 尝试更新状态为失败
            try:
                self.db.update_file_status(
                    file_id,
                    FileStatus.FAILED,
                    failed_reason=f"未预期的错误: {e}"
                )
            except Exception as update_error:
                logger.error(f"更新失败状态时出错: {update_error}")
            
            raise KnowledgeBaseError(f"处理文件失败: {e}")
    
    def _calculate_md5(self, file_path: Path) -> str:
        """
        计算文件的 MD5 哈希值
        
        参数:
            file_path: 文件路径
        
        返回:
            MD5 哈希值（32 个十六进制字符）
        """
        md5_hash = hashlib.md5()
        
        with open(file_path, "rb") as f:
            # 分块读取以处理大文件
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取管理器统计信息
        
        返回:
            统计信息字典
        
        示例:
            >>> stats = manager.get_statistics()
            >>> print(f"缓存中有 {stats['cached_kbs']} 个知识库")
        """
        cache_stats = self.provider.get_statistics()
        
        return {
            "cached_kbs": cache_stats["total_kbs"],
            "embedding_dimension": self.embedding_dimension,
            "db_path": self.db.db_path,
            "file_storage_path": str(self.file_storage_path),
            "max_file_size": self.max_file_size
        }
    
    async def query_knowledge_base(
        self,
        kb_id: str,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        查询知识库中的文档
        
        步骤:
        1. 获取知识库配置
        2. 使用知识库的 embedding_model 生成查询向量
        3. 使用知识库的 RetrievalConfig 搜索向量存储
        4. 应用相似度阈值过滤
        5. 应用重排序（如果启用）
        6. 返回结果及元数据
        
        参数:
            kb_id: 知识库 ID
            query: 查询文本
            top_k: 返回结果数量（可选，使用知识库配置）
            similarity_threshold: 相似度阈值（可选，使用知识库配置）
        
        返回:
            搜索结果列表，每个结果包含:
            - id: 块 ID
            - score: 相似度分数
            - text: 文本内容
            - file_id: 文件 ID
            - source: 来源文件名
            - chunk_index: 块索引
            - metadata: 其他元数据
        
        异常:
            KnowledgeBaseNotFoundError: 知识库不存在
            ValueError: 查询文本为空
            KnowledgeBaseError: 查询失败
        
        示例:
            >>> results = await manager.query_knowledge_base(
            ...     kb_id="kb_123",
            ...     query="什么是人工智能？",
            ...     top_k=5
            ... )
            >>> for result in results:
            ...     print(f"Score: {result['score']:.4f}")
            ...     print(f"Text: {result['text'][:100]}...")
        """
        try:
            logger.info(f"查询知识库 {kb_id}: {query[:50]}...")
            
            # 1. 验证查询文本
            if not query or not query.strip():
                raise ValueError("查询文本不能为空")
            
            query = query.strip()
            
            # 2. 获取知识库配置
            kb = self.db.get_kb(kb_id)
            if not kb:
                raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")
            
            logger.debug(f"知识库: {kb.name}, 模型: {kb.embedding_model}")
            
            # 3. 使用知识库的 RetrievalConfig（或使用参数覆盖）
            retrieval_config = kb.retrieval_config
            
            # 使用参数覆盖配置（如果提供）
            final_top_k = top_k if top_k is not None else retrieval_config.top_k
            final_threshold = (
                similarity_threshold 
                if similarity_threshold is not None 
                else retrieval_config.similarity_threshold
            )
            
            logger.debug(
                f"检索配置 - mode: {retrieval_config.retrieval_mode}, "
                f"top_k: {final_top_k}, threshold: {final_threshold}"
            )
            
            # 4. 生成查询向量
            logger.debug("[1/3] 生成查询向量...")
            
            try:
                from rag5.tools.embeddings import OllamaEmbeddingsManager
                from rag5.config import settings
                
                # 使用知识库的 embedding_model
                embeddings_manager = OllamaEmbeddingsManager(
                    model=kb.embedding_model,
                    base_url=settings.ollama_host
                )
                
                query_vector = embeddings_manager.embed_query(query)
                
                logger.debug(f"✓ 查询向量生成完成，维度: {len(query_vector)}")
                
            except Exception as e:
                error_msg = f"生成查询向量失败: {e}"
                logger.error(error_msg, exc_info=True)
                raise KnowledgeBaseError(error_msg)
            
            # 5. 搜索向量存储
            logger.debug("[2/3] 搜索向量存储...")
            
            try:
                search_results = await self.vector_manager.search(
                    kb_id=kb_id,
                    query_vector=query_vector,
                    top_k=final_top_k,
                    score_threshold=final_threshold
                )
                
                logger.debug(f"✓ 搜索完成，找到 {len(search_results)} 个结果")
                
            except Exception as e:
                error_msg = f"向量搜索失败: {e}"
                logger.error(error_msg, exc_info=True)
                raise KnowledgeBaseError(error_msg)
            
            # 6. 格式化结果
            logger.debug("[3/3] 格式化结果...")
            
            formatted_results = []
            for result in search_results:
                payload = result.get("payload", {})
                
                formatted_result = {
                    "id": result.get("id"),
                    "score": result.get("score"),
                    "text": payload.get("text", ""),
                    "file_id": payload.get("file_id", ""),
                    "source": payload.get("source", ""),
                    "chunk_index": payload.get("chunk_index", 0),
                    "kb_id": payload.get("kb_id", kb_id),
                    "metadata": {
                        k: v for k, v in payload.items()
                        if k not in ["text", "file_id", "source", "chunk_index", "kb_id"]
                    }
                }
                
                formatted_results.append(formatted_result)
            
            # 7. 应用重排序（如果启用）
            if retrieval_config.enable_rerank and retrieval_config.rerank_model:
                logger.debug("重排序已启用，但当前未实现重排序功能")
                logger.warning(
                    f"知识库 {kb_id} 启用了重排序 (模型: {retrieval_config.rerank_model})，"
                    "但重排序功能尚未实现，将跳过此步骤"
                )
                # TODO: 实现重排序功能
                # formatted_results = self._apply_reranking(
                #     query=query,
                #     results=formatted_results,
                #     rerank_model=retrieval_config.rerank_model
                # )
            
            # 8. 记录结果统计
            if formatted_results:
                scores = [r["score"] for r in formatted_results]
                logger.info(
                    f"✓ 查询完成，返回 {len(formatted_results)} 个结果 "
                    f"(分数范围: {min(scores):.4f} - {max(scores):.4f})"
                )
            else:
                logger.info("✓ 查询完成，未找到匹配结果")
            
            return formatted_results
            
        except (KnowledgeBaseNotFoundError, ValueError):
            raise
        except KnowledgeBaseError:
            raise
        except Exception as e:
            logger.error(f"查询知识库时发生未预期的错误: {e}", exc_info=True)
            raise KnowledgeBaseError(f"查询知识库失败: {e}")
    
    def __repr__(self) -> str:
        """返回管理器的字符串表示"""
        stats = self.get_statistics()
        return (
            f"<KnowledgeBaseManager("
            f"cached_kbs={stats['cached_kbs']}, "
            f"db='{stats['db_path']}'"
            f")>"
        )
