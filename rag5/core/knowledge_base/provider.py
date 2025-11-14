"""
知识库提供者 - 内存缓存层

提供知识库配置的快速访问，通过内存缓存提高性能。
"""

import asyncio
import logging
from typing import Dict, Optional, List

from rag5.core.knowledge_base.models import KnowledgeBase
from rag5.core.knowledge_base.database import KnowledgeBaseDatabase

logger = logging.getLogger(__name__)


class KnowledgeBaseProvider:
    """
    知识库提供者 - 内存缓存层
    
    提供对知识库配置的快速访问，通过内存缓存减少数据库查询。
    支持线程安全的并发操作。
    """
    
    def __init__(self):
        """初始化提供者"""
        self.config_map: Dict[str, KnowledgeBase] = {}
        self.name_to_id: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        logger.info("知识库提供者初始化完成")
    
    def add(self, kb: KnowledgeBase) -> None:
        """
        添加知识库到缓存
        
        参数:
            kb: 知识库实体
        """
        self.config_map[kb.id] = kb
        self.name_to_id[kb.name] = kb.id
        logger.debug(f"添加知识库到缓存: {kb.name} (ID: {kb.id})")
    
    def update(self, kb: KnowledgeBase) -> None:
        """
        更新缓存中的知识库
        
        处理名称变更的情况，确保 name_to_id 映射保持一致。
        
        参数:
            kb: 更新后的知识库实体
        """
        # 检查是否存在旧的知识库
        old_kb = self.config_map.get(kb.id)
        
        # 如果名称发生变化，需要更新 name_to_id 映射
        if old_kb and old_kb.name != kb.name:
            # 删除旧名称的映射
            self.name_to_id.pop(old_kb.name, None)
            logger.debug(f"删除旧名称映射: {old_kb.name}")
        
        # 更新缓存
        self.config_map[kb.id] = kb
        self.name_to_id[kb.name] = kb.id
        logger.debug(f"更新知识库缓存: {kb.name} (ID: {kb.id})")
    
    def delete(self, kb_id: str) -> None:
        """
        从缓存中删除知识库
        
        参数:
            kb_id: 知识库 ID
        """
        kb = self.config_map.pop(kb_id, None)
        if kb:
            self.name_to_id.pop(kb.name, None)
            logger.debug(f"从缓存中删除知识库: {kb.name} (ID: {kb_id})")
        else:
            logger.warning(f"尝试删除不存在的知识库: {kb_id}")
    
    def get(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        根据 ID 获取知识库
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            知识库实体，如果不存在则返回 None
        """
        return self.config_map.get(kb_id)
    
    def get_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """
        根据名称获取知识库
        
        参数:
            name: 知识库名称
        
        返回:
            知识库实体，如果不存在则返回 None
        """
        kb_id = self.name_to_id.get(name)
        return self.config_map.get(kb_id) if kb_id else None
    
    def list_all(self) -> List[KnowledgeBase]:
        """
        获取所有缓存的知识库
        
        返回:
            知识库列表
        """
        return list(self.config_map.values())
    
    def exists(self, kb_id: str) -> bool:
        """
        检查知识库是否存在
        
        参数:
            kb_id: 知识库 ID
        
        返回:
            是否存在
        """
        return kb_id in self.config_map
    
    def exists_by_name(self, name: str) -> bool:
        """
        检查知识库名称是否存在
        
        参数:
            name: 知识库名称
        
        返回:
            是否存在
        """
        return name in self.name_to_id
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.config_map.clear()
        self.name_to_id.clear()
        logger.info("清空知识库缓存")
    
    async def load_from_db(self, db: KnowledgeBaseDatabase) -> int:
        """
        从数据库加载所有知识库到缓存
        
        使用异步锁确保线程安全。
        
        参数:
            db: 知识库数据库实例
        
        返回:
            加载的知识库数量
        """
        async with self._lock:
            # 清空现有缓存
            self.clear()
            
            # 从数据库加载所有知识库
            kbs, total = db.list_kbs(offset=0, limit=1000)  # 假设不会超过 1000 个
            
            # 添加到缓存
            for kb in kbs:
                self.add(kb)
            
            logger.info(f"从数据库加载 {len(kbs)} 个知识库到缓存")
            return len(kbs)
    
    async def refresh_kb(self, db: KnowledgeBaseDatabase, kb_id: str) -> bool:
        """
        从数据库刷新单个知识库
        
        参数:
            db: 知识库数据库实例
            kb_id: 知识库 ID
        
        返回:
            是否成功刷新
        """
        async with self._lock:
            kb = db.get_kb(kb_id)
            if kb:
                self.update(kb)
                logger.debug(f"刷新知识库缓存: {kb.name} (ID: {kb_id})")
                return True
            else:
                # 如果数据库中不存在，从缓存中删除
                self.delete(kb_id)
                logger.warning(f"知识库在数据库中不存在，已从缓存删除: {kb_id}")
                return False
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        返回:
            包含缓存统计的字典
        """
        return {
            "total_kbs": len(self.config_map),
            "total_names": len(self.name_to_id)
        }
    
    def __len__(self) -> int:
        """返回缓存中的知识库数量"""
        return len(self.config_map)
    
    def __contains__(self, kb_id: str) -> bool:
        """支持 'in' 操作符"""
        return kb_id in self.config_map
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"KnowledgeBaseProvider(kbs={len(self.config_map)})"
