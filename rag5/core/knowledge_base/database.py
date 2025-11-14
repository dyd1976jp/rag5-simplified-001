"""
知识库数据库操作

提供 SQLite 数据库的 CRUD 操作，用于知识库和文件管理。
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager

from rag5.core.knowledge_base.models import (
    KnowledgeBase,
    FileEntity,
    FileStatus,
    ChunkConfig,
    RetrievalConfig
)

logger = logging.getLogger(__name__)


class KnowledgeBaseDatabase:
    """知识库数据库操作类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        参数:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_db()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # 启用外键约束（SQLite 默认不启用）
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表和索引"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建知识库表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    embedding_model TEXT NOT NULL,
                    chunk_config TEXT NOT NULL,
                    retrieval_config TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            
            # 创建文件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kb_files (
                    id TEXT PRIMARY KEY,
                    kb_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_extension TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_md5 TEXT NOT NULL,
                    status TEXT NOT NULL,
                    failed_reason TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    UNIQUE(kb_id, file_name)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kb_files_kb_id 
                ON kb_files(kb_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kb_files_status 
                ON kb_files(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kb_created_at 
                ON knowledge_bases(created_at DESC)
            """)
            
            logger.info("数据库表和索引初始化完成")
    
    # ==================== 知识库 CRUD 操作 ====================
    
    def create_kb(self, kb: KnowledgeBase) -> KnowledgeBase:
        """
        创建新知识库
        
        参数:
            kb: 知识库实体
        
        返回:
            创建的知识库实体
        
        异常:
            sqlite3.IntegrityError: 如果名称已存在
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO knowledge_bases (
                    id, name, description, embedding_model,
                    chunk_config, retrieval_config, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kb.id,
                kb.name,
                kb.description,
                kb.embedding_model,
                kb.chunk_config.model_dump_json(),
                kb.retrieval_config.model_dump_json(),
                kb.created_at.isoformat(),
                kb.updated_at.isoformat()
            ))
            
            logger.info(f"创建知识库: {kb.name} (ID: {kb.id})")
            return kb
    
    def get_kb(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        根据 ID 获取知识库
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            知识库实体，如果不存在则返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM knowledge_bases WHERE id = ?
            """, (kb_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_kb(row)
    
    def get_kb_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """
        根据名称获取知识库
        
        参数:
            name: 知识库名称
        
        返回:
            知识库实体，如果不存在则返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM knowledge_bases WHERE name = ?
            """, (name,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_kb(row)
    
    def list_kbs(
        self,
        offset: int = 0,
        limit: int = 10
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        列出所有知识库（分页）
        
        参数:
            offset: 偏移量
            limit: 每页数量
        
        返回:
            (知识库列表, 总数)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) FROM knowledge_bases")
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            cursor.execute("""
                SELECT * FROM knowledge_bases
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            kbs = [self._row_to_kb(row) for row in rows]
            
            return kbs, total
    
    def update_kb(self, kb_id: str, **updates) -> Optional[KnowledgeBase]:
        """
        更新知识库
        
        参数:
            kb_id: 知识库 ID
            **updates: 要更新的字段
        
        返回:
            更新后的知识库实体，如果不存在则返回 None
        """
        # 首先获取现有知识库
        kb = self.get_kb(kb_id)
        if not kb:
            return None
        
        # 准备更新字段
        update_fields = []
        update_values = []
        
        if "name" in updates:
            update_fields.append("name = ?")
            update_values.append(updates["name"])
        
        if "description" in updates:
            update_fields.append("description = ?")
            update_values.append(updates["description"])
        
        if "embedding_model" in updates:
            update_fields.append("embedding_model = ?")
            update_values.append(updates["embedding_model"])
        
        if "chunk_config" in updates:
            chunk_config = updates["chunk_config"]
            if isinstance(chunk_config, dict):
                chunk_config = ChunkConfig(**chunk_config)
            update_fields.append("chunk_config = ?")
            update_values.append(chunk_config.model_dump_json())
        
        if "retrieval_config" in updates:
            retrieval_config = updates["retrieval_config"]
            if isinstance(retrieval_config, dict):
                retrieval_config = RetrievalConfig(**retrieval_config)
            update_fields.append("retrieval_config = ?")
            update_values.append(retrieval_config.model_dump_json())
        
        if not update_fields:
            return kb
        
        # 添加 updated_at
        update_fields.append("updated_at = ?")
        update_values.append(datetime.now().isoformat())
        
        # 添加 WHERE 条件的值
        update_values.append(kb_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            sql = f"""
                UPDATE knowledge_bases
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            
            cursor.execute(sql, update_values)
            
            logger.info(f"更新知识库: {kb_id}")
        
        # 返回更新后的知识库
        return self.get_kb(kb_id)
    
    def delete_kb(self, kb_id: str) -> bool:
        """
        删除知识库
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            是否成功删除
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM knowledge_bases WHERE id = ?
            """, (kb_id,))
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"删除知识库: {kb_id}")
            
            return deleted
    
    def get_kb_statistics(self, kb_id: str) -> Dict[str, int]:
        """
        获取知识库统计信息
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            包含 document_count 和 total_size 的字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as document_count,
                    COALESCE(SUM(file_size), 0) as total_size
                FROM kb_files
                WHERE kb_id = ? AND status = ?
            """, (kb_id, FileStatus.SUCCEEDED.value))
            
            row = cursor.fetchone()
            return {
                "document_count": row["document_count"],
                "total_size": row["total_size"]
            }
    
    # ==================== 文件 CRUD 操作 ====================
    
    def create_file(self, file: FileEntity) -> FileEntity:
        """
        创建新文件记录
        
        参数:
            file: 文件实体
        
        返回:
            创建的文件实体
        
        异常:
            sqlite3.IntegrityError: 如果文件名在知识库中已存在
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO kb_files (
                    id, kb_id, file_name, file_path, file_extension,
                    file_size, file_md5, status, failed_reason, chunk_count,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file.id,
                file.kb_id,
                file.file_name,
                file.file_path,
                file.file_extension,
                file.file_size,
                file.file_md5,
                file.status.value,
                file.failed_reason,
                file.chunk_count,
                file.created_at.isoformat(),
                file.updated_at.isoformat(),
                json.dumps(file.metadata)
            ))
            
            logger.info(f"创建文件记录: {file.file_name} (ID: {file.id})")
            return file
    
    def get_file(self, file_id: str) -> Optional[FileEntity]:
        """
        根据 ID 获取文件
        
        参数:
            file_id: 文件 ID
        
        返回:
            文件实体，如果不存在则返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM kb_files WHERE id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_file(row)
    
    def list_files(
        self,
        kb_id: str,
        status: Optional[FileStatus] = None,
        offset: int = 0,
        limit: int = 10
    ) -> Tuple[List[FileEntity], int]:
        """
        列出知识库中的文件（分页）
        
        参数:
            kb_id: 知识库 ID
            status: 可选的状态过滤
            offset: 偏移量
            limit: 每页数量
        
        返回:
            (文件列表, 总数)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建查询
            where_clause = "WHERE kb_id = ?"
            params = [kb_id]
            
            if status:
                where_clause += " AND status = ?"
                params.append(status.value)
            
            # 获取总数
            cursor.execute(
                f"SELECT COUNT(*) FROM kb_files {where_clause}",
                params
            )
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            params.extend([limit, offset])
            cursor.execute(f"""
                SELECT * FROM kb_files
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, params)
            
            rows = cursor.fetchall()
            files = [self._row_to_file(row) for row in rows]
            
            return files, total
    
    def update_file_status(
        self,
        file_id: str,
        status: FileStatus,
        failed_reason: Optional[str] = None,
        chunk_count: Optional[int] = None
    ) -> Optional[FileEntity]:
        """
        更新文件状态
        
        参数:
            file_id: 文件 ID
            status: 新状态
            failed_reason: 失败原因（可选）
            chunk_count: 块数量（可选）
        
        返回:
            更新后的文件实体，如果不存在则返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            update_fields = ["status = ?", "updated_at = ?"]
            update_values = [status.value, datetime.now().isoformat()]
            
            if failed_reason is not None:
                update_fields.append("failed_reason = ?")
                update_values.append(failed_reason)
            
            if chunk_count is not None:
                update_fields.append("chunk_count = ?")
                update_values.append(chunk_count)
            
            update_values.append(file_id)
            
            cursor.execute(f"""
                UPDATE kb_files
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, update_values)
            
            if cursor.rowcount > 0:
                logger.info(f"更新文件状态: {file_id} -> {status.value}")
        
        # Get the updated file after commit
        return self.get_file(file_id)
    
    def delete_file(self, file_id: str) -> bool:
        """
        删除文件记录
        
        参数:
            file_id: 文件 ID
        
        返回:
            是否成功删除
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM kb_files WHERE id = ?
            """, (file_id,))
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"删除文件记录: {file_id}")
            
            return deleted
    
    # ==================== 辅助方法 ====================
    
    def _row_to_kb(self, row: sqlite3.Row) -> KnowledgeBase:
        """将数据库行转换为 KnowledgeBase 对象"""
        # 获取统计信息
        stats = self.get_kb_statistics(row["id"])
        
        return KnowledgeBase(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            embedding_model=row["embedding_model"],
            chunk_config=ChunkConfig.model_validate_json(row["chunk_config"]),
            retrieval_config=RetrievalConfig.model_validate_json(row["retrieval_config"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            document_count=stats["document_count"],
            total_size=stats["total_size"]
        )
    
    def _row_to_file(self, row: sqlite3.Row) -> FileEntity:
        """将数据库行转换为 FileEntity 对象"""
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        
        return FileEntity(
            id=row["id"],
            kb_id=row["kb_id"],
            file_name=row["file_name"],
            file_path=row["file_path"],
            file_extension=row["file_extension"],
            file_size=row["file_size"],
            file_md5=row["file_md5"],
            status=FileStatus(row["status"]),
            failed_reason=row["failed_reason"],
            chunk_count=row["chunk_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=metadata
        )
