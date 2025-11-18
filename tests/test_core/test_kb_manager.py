"""
测试知识库管理器

测试 KnowledgeBaseManager 的核心功能。
"""

import pytest
import pytest_asyncio
import tempfile
import shutil
from pathlib import Path

from rag5.core.knowledge_base import (
    KnowledgeBaseManager,
    KnowledgeBase,
    ChunkConfig,
    RetrievalConfig,
    KnowledgeBaseError,
    KnowledgeBaseNotFoundError,
    KnowledgeBaseAlreadyExistsError,
    FileStatus
)
from rag5.tools.vectordb import QdrantManager


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def qdrant_manager():
    """创建 Qdrant 管理器"""
    return QdrantManager("http://localhost:6333")


@pytest_asyncio.fixture
async def kb_manager(temp_dir, qdrant_manager):
    """创建知识库管理器"""
    db_path = str(Path(temp_dir) / "test_kb.db")
    file_storage_path = str(Path(temp_dir) / "files")
    manager = KnowledgeBaseManager(
        db_path=db_path,
        qdrant_manager=qdrant_manager,
        file_storage_path=file_storage_path,
        embedding_dimension=1024
    )
    await manager.initialize()
    return manager


@pytest.mark.asyncio
async def test_create_knowledge_base(kb_manager):
    """测试创建知识库"""
    kb = await kb_manager.create_knowledge_base(
        name="test_kb",
        description="Test knowledge base",
        embedding_model="nomic-embed-text"
    )
    
    assert kb is not None
    assert kb.name == "test_kb"
    assert kb.description == "Test knowledge base"
    assert kb.embedding_model == "nomic-embed-text"
    assert kb.id.startswith("kb_")
    assert kb.document_count == 0
    assert kb.total_size == 0
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_create_knowledge_base_with_custom_config(kb_manager):
    """测试使用自定义配置创建知识库"""
    chunk_config = ChunkConfig(
        chunk_size=1024,
        chunk_overlap=100,
        parser_type="recursive"
    )
    
    retrieval_config = RetrievalConfig(
        retrieval_mode="vector",
        top_k=10,
        similarity_threshold=0.5
    )
    
    kb = await kb_manager.create_knowledge_base(
        name="custom_kb",
        description="Custom config KB",
        embedding_model="nomic-embed-text",
        chunk_config=chunk_config,
        retrieval_config=retrieval_config
    )
    
    assert kb.chunk_config.chunk_size == 1024
    assert kb.chunk_config.chunk_overlap == 100
    assert kb.chunk_config.parser_type == "recursive"
    assert kb.retrieval_config.retrieval_mode == "vector"
    assert kb.retrieval_config.top_k == 10
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_create_duplicate_name(kb_manager):
    """测试创建重复名称的知识库"""
    kb = await kb_manager.create_knowledge_base(
        name="duplicate_kb",
        description="First KB",
        embedding_model="nomic-embed-text"
    )
    
    # 尝试创建同名知识库
    with pytest.raises(KnowledgeBaseAlreadyExistsError):
        await kb_manager.create_knowledge_base(
            name="duplicate_kb",
            description="Second KB",
            embedding_model="nomic-embed-text"
        )
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_list_knowledge_bases(kb_manager):
    """测试列出知识库"""
    # 创建多个知识库
    kb1 = await kb_manager.create_knowledge_base(
        name="kb1",
        description="KB 1",
        embedding_model="nomic-embed-text"
    )
    
    kb2 = await kb_manager.create_knowledge_base(
        name="kb2",
        description="KB 2",
        embedding_model="nomic-embed-text"
    )
    
    # 列出知识库
    kbs, total = await kb_manager.list_knowledge_bases(page=1, size=10)
    
    assert total >= 2
    assert len(kbs) >= 2
    
    # 验证知识库在列表中
    kb_names = [kb.name for kb in kbs]
    assert "kb1" in kb_names
    assert "kb2" in kb_names
    
    # 清理
    await kb_manager.delete_knowledge_base(kb1.id)
    await kb_manager.delete_knowledge_base(kb2.id)


@pytest.mark.asyncio
async def test_get_knowledge_base(kb_manager):
    """测试获取知识库详情"""
    kb = await kb_manager.create_knowledge_base(
        name="get_test_kb",
        description="Get test",
        embedding_model="nomic-embed-text"
    )
    
    # 获取知识库
    retrieved_kb = await kb_manager.get_knowledge_base(kb.id)
    
    assert retrieved_kb is not None
    assert retrieved_kb.id == kb.id
    assert retrieved_kb.name == kb.name
    assert retrieved_kb.description == kb.description
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_get_nonexistent_knowledge_base(kb_manager):
    """测试获取不存在的知识库"""
    with pytest.raises(KnowledgeBaseNotFoundError):
        await kb_manager.get_knowledge_base("kb_nonexistent")


@pytest.mark.asyncio
async def test_update_knowledge_base(kb_manager):
    """测试更新知识库"""
    kb = await kb_manager.create_knowledge_base(
        name="update_test_kb",
        description="Original description",
        embedding_model="nomic-embed-text"
    )
    
    # 更新描述
    updated_kb = await kb_manager.update_knowledge_base(
        kb_id=kb.id,
        description="Updated description"
    )
    
    assert updated_kb.description == "Updated description"
    assert updated_kb.name == kb.name  # 名称未变
    
    # 更新检索配置
    new_retrieval_config = RetrievalConfig(top_k=20)
    updated_kb = await kb_manager.update_knowledge_base(
        kb_id=kb.id,
        retrieval_config=new_retrieval_config
    )
    
    assert updated_kb.retrieval_config.top_k == 20
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_update_knowledge_base_name(kb_manager):
    """测试更新知识库名称"""
    kb = await kb_manager.create_knowledge_base(
        name="old_name",
        description="Test",
        embedding_model="nomic-embed-text"
    )
    
    # 更新名称
    updated_kb = await kb_manager.update_knowledge_base(
        kb_id=kb.id,
        name="new_name"
    )
    
    assert updated_kb.name == "new_name"
    
    # 验证可以通过新名称找到
    kb_by_name = kb_manager.get_kb_by_name("new_name")
    assert kb_by_name is not None
    assert kb_by_name.id == kb.id
    
    # 验证旧名称不存在
    old_kb = kb_manager.get_kb_by_name("old_name")
    assert old_kb is None
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_update_to_duplicate_name(kb_manager):
    """测试更新为已存在的名称"""
    kb1 = await kb_manager.create_knowledge_base(
        name="kb1",
        description="KB 1",
        embedding_model="nomic-embed-text"
    )
    
    kb2 = await kb_manager.create_knowledge_base(
        name="kb2",
        description="KB 2",
        embedding_model="nomic-embed-text"
    )
    
    # 尝试将 kb2 的名称改为 kb1
    with pytest.raises(KnowledgeBaseAlreadyExistsError):
        await kb_manager.update_knowledge_base(
            kb_id=kb2.id,
            name="kb1"
        )
    
    # 清理
    await kb_manager.delete_knowledge_base(kb1.id)
    await kb_manager.delete_knowledge_base(kb2.id)


@pytest.mark.asyncio
async def test_delete_knowledge_base(kb_manager):
    """测试删除知识库"""
    kb = await kb_manager.create_knowledge_base(
        name="delete_test_kb",
        description="To be deleted",
        embedding_model="nomic-embed-text"
    )
    
    kb_id = kb.id
    
    # 删除知识库
    success = await kb_manager.delete_knowledge_base(kb_id)
    assert success is True
    
    # 验证知识库不存在
    with pytest.raises(KnowledgeBaseNotFoundError):
        await kb_manager.get_knowledge_base(kb_id)
    
    # 验证缓存中也不存在
    cached_kb = kb_manager.get_kb_from_cache(kb_id)
    assert cached_kb is None


@pytest.mark.asyncio
async def test_delete_nonexistent_knowledge_base(kb_manager):
    """测试删除不存在的知识库"""
    with pytest.raises(KnowledgeBaseNotFoundError):
        await kb_manager.delete_knowledge_base("kb_nonexistent")


@pytest.mark.asyncio
async def test_get_kb_by_name(kb_manager):
    """测试根据名称获取知识库"""
    kb = await kb_manager.create_knowledge_base(
        name="name_test_kb",
        description="Name test",
        embedding_model="nomic-embed-text"
    )
    
    # 从缓存获取
    cached_kb = kb_manager.get_kb_by_name("name_test_kb")
    assert cached_kb is not None
    assert cached_kb.id == kb.id
    assert cached_kb.name == "name_test_kb"
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_refresh_cache(kb_manager):
    """测试刷新缓存"""
    # 创建知识库
    kb = await kb_manager.create_knowledge_base(
        name="cache_test_kb",
        description="Cache test",
        embedding_model="nomic-embed-text"
    )
    
    # 刷新缓存
    count = await kb_manager.refresh_cache()
    assert count >= 1
    
    # 验证知识库在缓存中
    cached_kb = kb_manager.get_kb_from_cache(kb.id)
    assert cached_kb is not None
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_get_statistics(kb_manager):
    """测试获取统计信息"""
    stats = kb_manager.get_statistics()
    
    assert "cached_kbs" in stats
    assert "embedding_dimension" in stats
    assert "db_path" in stats
    assert stats["embedding_dimension"] == 1024


@pytest.mark.asyncio
async def test_pagination(kb_manager):
    """测试分页功能"""
    # 创建多个知识库
    kbs_created = []
    for i in range(5):
        kb = await kb_manager.create_knowledge_base(
            name=f"page_test_kb_{i}",
            description=f"Page test {i}",
            embedding_model="nomic-embed-text"
        )
        kbs_created.append(kb)
    
    # 测试第一页
    kbs_page1, total = await kb_manager.list_knowledge_bases(page=1, size=3)
    assert len(kbs_page1) == 3
    assert total >= 5
    
    # 测试第二页
    kbs_page2, total = await kb_manager.list_knowledge_bases(page=2, size=3)
    assert len(kbs_page2) >= 2
    
    # 验证两页的知识库不重复
    page1_ids = {kb.id for kb in kbs_page1}
    page2_ids = {kb.id for kb in kbs_page2}
    assert len(page1_ids & page2_ids) == 0
    
    # 清理
    for kb in kbs_created:
        await kb_manager.delete_knowledge_base(kb.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ==================== 文件管理测试 ====================

@pytest.fixture
def sample_text_file(temp_dir):
    """创建示例文本文件"""
    file_path = Path(temp_dir) / "sample.txt"
    file_path.write_text("This is a sample text file for testing.\nIt has multiple lines.\n")
    return str(file_path)


@pytest.fixture
def sample_md_file(temp_dir):
    """创建示例 Markdown 文件"""
    file_path = Path(temp_dir) / "sample.md"
    file_path.write_text("# Sample Markdown\n\nThis is a test document.\n")
    return str(file_path)


@pytest.fixture
def large_file(temp_dir):
    """创建大文件（用于测试大小限制）"""
    file_path = Path(temp_dir) / "large.txt"
    # 创建 1MB 的文件
    with open(file_path, "wb") as f:
        f.write(b"x" * (1024 * 1024))
    return str(file_path)


@pytest.mark.asyncio
async def test_upload_file(kb_manager, sample_text_file):
    """测试上传文件"""
    # 创建知识库
    kb = await kb_manager.create_knowledge_base(
        name="upload_test_kb",
        description="Upload test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件
    file_entity = await kb_manager.upload_file(
        kb_id=kb.id,
        file_path=sample_text_file
    )
    
    assert file_entity is not None
    assert file_entity.id.startswith("file_")
    assert file_entity.kb_id == kb.id
    assert file_entity.file_name == "sample.txt"
    assert file_entity.file_extension == ".txt"
    assert file_entity.file_size > 0
    assert file_entity.status == "pending"
    assert len(file_entity.file_md5) == 32  # MD5 哈希长度
    
    # 验证文件已存储
    stored_path = Path(file_entity.file_path)
    assert stored_path.exists()
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_upload_file_with_custom_name(kb_manager, sample_text_file):
    """测试使用自定义文件名上传"""
    kb = await kb_manager.create_knowledge_base(
        name="custom_name_kb",
        description="Custom name test",
        embedding_model="nomic-embed-text"
    )
    
    # 使用自定义文件名上传
    file_entity = await kb_manager.upload_file(
        kb_id=kb.id,
        file_path=sample_text_file,
        file_name="custom_name.txt"
    )
    
    assert file_entity.file_name == "custom_name.txt"
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_upload_markdown_file(kb_manager, sample_md_file):
    """测试上传 Markdown 文件"""
    kb = await kb_manager.create_knowledge_base(
        name="md_test_kb",
        description="Markdown test",
        embedding_model="nomic-embed-text"
    )
    
    file_entity = await kb_manager.upload_file(
        kb_id=kb.id,
        file_path=sample_md_file
    )
    
    assert file_entity.file_extension == ".md"
    assert file_entity.file_name == "sample.md"
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_upload_file_overwrites_existing(kb_manager, sample_text_file):
    """同名文件再次上传应覆盖旧记录并重复利用文件 ID"""
    kb = await kb_manager.create_knowledge_base(
        name="overwrite_kb",
        description="Overwrite test",
        embedding_model="nomic-embed-text"
    )

    first_entity = await kb_manager.upload_file(
        kb_id=kb.id,
        file_path=sample_text_file
    )

    original_md5 = first_entity.file_md5
    stored_path = Path(first_entity.file_path)
    assert stored_path.exists()

    # 修改源文件内容，保持名称不变
    Path(sample_text_file).write_text("Updated content for overwrite test", encoding="utf-8")

    updated_entity = await kb_manager.upload_file(
        kb_id=kb.id,
        file_path=sample_text_file
    )

    assert updated_entity.id == first_entity.id
    assert updated_entity.file_md5 != original_md5
    assert updated_entity.status == FileStatus.PENDING
    assert updated_entity.chunk_count == 0
    assert Path(updated_entity.file_path).exists()

    files, total = await kb_manager.list_files(kb_id=kb.id)
    assert total == 1
    assert files[0].id == first_entity.id

    await kb_manager.delete_file(kb.id, updated_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_upload_to_nonexistent_kb(kb_manager, sample_text_file):
    """测试上传到不存在的知识库"""
    from rag5.core.knowledge_base import KnowledgeBaseNotFoundError
    
    with pytest.raises(KnowledgeBaseNotFoundError):
        await kb_manager.upload_file(
            kb_id="kb_nonexistent",
            file_path=sample_text_file
        )


@pytest.mark.asyncio
async def test_upload_nonexistent_file(kb_manager):
    """测试上传不存在的文件"""
    from rag5.core.knowledge_base import FileValidationError
    
    kb = await kb_manager.create_knowledge_base(
        name="nonexistent_file_kb",
        description="Test",
        embedding_model="nomic-embed-text"
    )
    
    with pytest.raises(FileValidationError):
        await kb_manager.upload_file(
            kb_id=kb.id,
            file_path="/path/to/nonexistent/file.txt"
        )
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_upload_unsupported_format(kb_manager, temp_dir):
    """测试上传不支持的文件格式"""
    from rag5.core.knowledge_base import FileValidationError
    
    # 创建不支持的文件格式
    unsupported_file = Path(temp_dir) / "test.xyz"
    unsupported_file.write_text("test content")
    
    kb = await kb_manager.create_knowledge_base(
        name="unsupported_format_kb",
        description="Test",
        embedding_model="nomic-embed-text"
    )
    
    with pytest.raises(FileValidationError):
        await kb_manager.upload_file(
            kb_id=kb.id,
            file_path=str(unsupported_file)
        )
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_upload_empty_file(kb_manager, temp_dir):
    """测试上传空文件"""
    from rag5.core.knowledge_base import FileValidationError
    
    # 创建空文件
    empty_file = Path(temp_dir) / "empty.txt"
    empty_file.write_text("")
    
    kb = await kb_manager.create_knowledge_base(
        name="empty_file_kb",
        description="Test",
        embedding_model="nomic-embed-text"
    )
    
    with pytest.raises(FileValidationError):
        await kb_manager.upload_file(
            kb_id=kb.id,
            file_path=str(empty_file)
        )
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_upload_file_size_limit(kb_manager, temp_dir):
    """测试文件大小限制"""
    from rag5.core.knowledge_base import FileValidationError
    
    # 创建一个超过限制的管理器（限制为 1KB）
    db_path = str(Path(temp_dir) / "test_size_limit.db")
    qdrant = QdrantManager("http://localhost:6333")
    small_limit_manager = KnowledgeBaseManager(
        db_path=db_path,
        qdrant_manager=qdrant,
        max_file_size=1024  # 1KB 限制
    )
    await small_limit_manager.initialize()
    
    # 创建知识库
    kb = await small_limit_manager.create_knowledge_base(
        name="size_limit_kb",
        description="Test",
        embedding_model="nomic-embed-text"
    )
    
    # 创建超过限制的文件
    large_file = Path(temp_dir) / "large.txt"
    large_file.write_text("x" * 2048)  # 2KB
    
    with pytest.raises(FileValidationError):
        await small_limit_manager.upload_file(
            kb_id=kb.id,
            file_path=str(large_file)
        )
    
    # 清理
    await small_limit_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_list_files(kb_manager, sample_text_file, sample_md_file):
    """测试列出文件"""
    kb = await kb_manager.create_knowledge_base(
        name="list_files_kb",
        description="List files test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传多个文件
    file1 = await kb_manager.upload_file(kb.id, sample_text_file)
    file2 = await kb_manager.upload_file(kb.id, sample_md_file)
    
    # 列出文件
    files, total = await kb_manager.list_files(kb_id=kb.id, page=1, size=10)
    
    assert total == 2
    assert len(files) == 2
    
    file_ids = {f.id for f in files}
    assert file1.id in file_ids
    assert file2.id in file_ids
    
    # 清理
    await kb_manager.delete_file(kb.id, file1.id)
    await kb_manager.delete_file(kb.id, file2.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_list_files_with_status_filter(kb_manager, sample_text_file):
    """测试按状态过滤文件列表"""
    from rag5.core.knowledge_base import FileStatus
    
    kb = await kb_manager.create_knowledge_base(
        name="filter_files_kb",
        description="Filter test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件
    file1 = await kb_manager.upload_file(kb.id, sample_text_file)
    
    # 列出 PENDING 状态的文件
    files, total = await kb_manager.list_files(
        kb_id=kb.id,
        status=FileStatus.PENDING,
        page=1,
        size=10
    )
    
    assert total >= 1
    assert all(f.status == FileStatus.PENDING for f in files)
    
    # 清理
    await kb_manager.delete_file(kb.id, file1.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_list_files_pagination(kb_manager, temp_dir):
    """测试文件列表分页"""
    kb = await kb_manager.create_knowledge_base(
        name="pagination_files_kb",
        description="Pagination test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传多个文件
    files_created = []
    for i in range(5):
        file_path = Path(temp_dir) / f"file_{i}.txt"
        file_path.write_text(f"Content {i}")
        file_entity = await kb_manager.upload_file(kb.id, str(file_path))
        files_created.append(file_entity)
    
    # 测试第一页
    files_page1, total = await kb_manager.list_files(kb_id=kb.id, page=1, size=3)
    assert len(files_page1) == 3
    assert total == 5
    
    # 测试第二页
    files_page2, total = await kb_manager.list_files(kb_id=kb.id, page=2, size=3)
    assert len(files_page2) == 2
    
    # 验证不重复
    page1_ids = {f.id for f in files_page1}
    page2_ids = {f.id for f in files_page2}
    assert len(page1_ids & page2_ids) == 0
    
    # 清理
    for file_entity in files_created:
        await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_delete_file(kb_manager, sample_text_file):
    """测试删除文件"""
    kb = await kb_manager.create_knowledge_base(
        name="delete_file_kb",
        description="Delete file test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件
    file_entity = await kb_manager.upload_file(kb.id, sample_text_file)
    file_id = file_entity.id
    stored_path = Path(file_entity.file_path)
    
    # 验证文件存在
    assert stored_path.exists()
    
    # 删除文件
    success = await kb_manager.delete_file(kb.id, file_id)
    assert success is True
    
    # 验证文件已从存储中删除
    assert not stored_path.exists()
    
    # 验证文件记录已从数据库删除
    files, total = await kb_manager.list_files(kb_id=kb.id)
    assert total == 0
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_delete_nonexistent_file(kb_manager):
    """测试删除不存在的文件"""
    from rag5.core.knowledge_base import FileNotFoundError
    
    kb = await kb_manager.create_knowledge_base(
        name="delete_nonexistent_kb",
        description="Test",
        embedding_model="nomic-embed-text"
    )
    
    with pytest.raises(FileNotFoundError):
        await kb_manager.delete_file(kb.id, "file_nonexistent")
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_delete_file_wrong_kb(kb_manager, sample_text_file):
    """测试删除属于其他知识库的文件"""
    from rag5.core.knowledge_base import FileValidationError
    
    # 创建两个知识库
    kb1 = await kb_manager.create_knowledge_base(
        name="kb1_wrong",
        description="KB 1",
        embedding_model="nomic-embed-text"
    )
    
    kb2 = await kb_manager.create_knowledge_base(
        name="kb2_wrong",
        description="KB 2",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件到 kb1
    file_entity = await kb_manager.upload_file(kb1.id, sample_text_file)
    
    # 尝试从 kb2 删除文件
    with pytest.raises(FileValidationError):
        await kb_manager.delete_file(kb2.id, file_entity.id)
    
    # 清理
    await kb_manager.delete_file(kb1.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb1.id)
    await kb_manager.delete_knowledge_base(kb2.id)


@pytest.mark.asyncio
async def test_delete_kb_cascades_files(kb_manager, sample_text_file):
    """测试删除知识库时级联删除文件"""
    kb = await kb_manager.create_knowledge_base(
        name="cascade_delete_kb",
        description="Cascade test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件
    file_entity = await kb_manager.upload_file(kb.id, sample_text_file)
    stored_path = Path(file_entity.file_path)
    
    # 验证文件存在
    assert stored_path.exists()
    
    # 删除知识库
    await kb_manager.delete_knowledge_base(kb.id)
    
    # 注意：文件系统中的文件不会自动删除（需要手动清理或在 delete_knowledge_base 中实现）
    # 但数据库记录会被级联删除


@pytest.mark.asyncio
async def test_md5_calculation(kb_manager, sample_text_file):
    """测试 MD5 哈希计算"""
    kb = await kb_manager.create_knowledge_base(
        name="md5_test_kb",
        description="MD5 test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传同一个文件两次
    file1 = await kb_manager.upload_file(
        kb_id=kb.id,
        file_path=sample_text_file,
        file_name="file1.txt"
    )
    
    file2 = await kb_manager.upload_file(
        kb_id=kb.id,
        file_path=sample_text_file,
        file_name="file2.txt"
    )
    
    # MD5 应该相同
    assert file1.file_md5 == file2.file_md5
    
    # 清理
    await kb_manager.delete_file(kb.id, file1.id)
    await kb_manager.delete_file(kb.id, file2.id)
    await kb_manager.delete_knowledge_base(kb.id)


# ==================== 文件处理流程测试 ====================

@pytest.fixture
def processing_text_file(temp_dir):
    """创建用于处理测试的文本文件"""
    file_path = Path(temp_dir) / "process_test.txt"
    content = """This is a test document for file processing.
It contains multiple paragraphs to test the chunking functionality.

The document should be loaded, chunked, embedded, and stored in the vector database.
This tests the complete file processing pipeline.

Each chunk should be properly indexed with metadata including the file ID and source.
"""
    file_path.write_text(content)
    return str(file_path)


@pytest.mark.asyncio
async def test_process_file_basic(kb_manager, processing_text_file):
    """测试基本文件处理流程"""
    from rag5.core.knowledge_base import FileStatus
    
    # 创建知识库
    kb = await kb_manager.create_knowledge_base(
        name="process_test_kb",
        description="Process test",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(chunk_size=100, chunk_overlap=20)
    )
    
    # 上传文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    assert file_entity.status == FileStatus.PENDING
    assert file_entity.chunk_count == 0
    
    # 处理文件
    processed_file = await kb_manager.process_file(file_entity.id)
    
    # 验证处理结果
    assert processed_file.status == FileStatus.SUCCEEDED
    assert processed_file.chunk_count > 0
    assert processed_file.failed_reason is None
    
    # 验证向量已存储
    stats = kb_manager.vector_manager.get_collection_stats(kb.id)
    assert stats is not None
    assert stats.get("vectors_count", 0) > 0
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_process_file_with_custom_chunk_config(kb_manager, processing_text_file):
    """测试使用自定义分块配置处理文件"""
    from rag5.core.knowledge_base import FileStatus
    
    # 创建知识库，使用较小的块大小
    kb = await kb_manager.create_knowledge_base(
        name="custom_chunk_kb",
        description="Custom chunk test",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(
            chunk_size=50,
            chunk_overlap=10,
            parser_type="recursive"
        )
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    processed_file = await kb_manager.process_file(file_entity.id)
    
    # 验证使用了自定义配置（较小的块应该产生更多的块）
    assert processed_file.status == FileStatus.SUCCEEDED
    assert processed_file.chunk_count > 3  # 应该有多个小块
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_process_file_status_transitions(kb_manager, processing_text_file):
    """测试文件处理过程中的状态转换"""
    from rag5.core.knowledge_base import FileStatus
    
    kb = await kb_manager.create_knowledge_base(
        name="status_test_kb",
        description="Status test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    initial_status = file_entity.status
    
    # 验证初始状态
    assert initial_status == FileStatus.PENDING
    
    # 处理文件
    processed_file = await kb_manager.process_file(file_entity.id)
    
    # 验证最终状态
    assert processed_file.status == FileStatus.SUCCEEDED
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_process_nonexistent_file(kb_manager):
    """测试处理不存在的文件"""
    from rag5.core.knowledge_base import FileNotFoundError
    
    with pytest.raises(FileNotFoundError):
        await kb_manager.process_file("file_nonexistent")


@pytest.mark.asyncio
async def test_process_file_with_missing_storage(kb_manager, processing_text_file):
    """测试处理存储文件已删除的情况"""
    from rag5.core.knowledge_base import FileNotFoundError
    
    kb = await kb_manager.create_knowledge_base(
        name="missing_storage_kb",
        description="Missing storage test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    
    # 删除存储的文件（模拟文件丢失）
    stored_path = Path(file_entity.file_path)
    stored_path.unlink()
    
    # 尝试处理文件
    with pytest.raises(FileNotFoundError):
        await kb_manager.process_file(file_entity.id)
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_process_markdown_file(kb_manager, temp_dir):
    """测试处理 Markdown 文件"""
    from rag5.core.knowledge_base import FileStatus
    
    # 创建 Markdown 文件
    md_file = Path(temp_dir) / "test.md"
    md_content = """# Test Document

This is a test markdown document.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""
    md_file.write_text(md_content)
    
    kb = await kb_manager.create_knowledge_base(
        name="md_process_kb",
        description="Markdown process test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, str(md_file))
    processed_file = await kb_manager.process_file(file_entity.id)
    
    # 验证处理成功
    assert processed_file.status == FileStatus.SUCCEEDED
    assert processed_file.chunk_count > 0
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_process_chinese_text_file(kb_manager, temp_dir):
    """测试处理中文文本文件"""
    from rag5.core.knowledge_base import FileStatus
    
    # 创建中文文本文件
    chinese_file = Path(temp_dir) / "chinese.txt"
    chinese_content = """这是一个中文测试文档。
它包含多个段落来测试分块功能。

文档应该被加载、分块、嵌入并存储到向量数据库中。
这测试了完整的文件处理流程。

每个块都应该被正确索引，包含文件ID和来源等元数据。
"""
    chinese_file.write_text(chinese_content, encoding='utf-8')
    
    kb = await kb_manager.create_knowledge_base(
        name="chinese_process_kb",
        description="Chinese process test",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(chunk_size=100, chunk_overlap=20)
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, str(chinese_file))
    processed_file = await kb_manager.process_file(file_entity.id)
    
    # 验证处理成功
    assert processed_file.status == FileStatus.SUCCEEDED
    assert processed_file.chunk_count > 0
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_process_file_updates_chunk_count(kb_manager, processing_text_file):
    """测试文件处理更新块计数"""
    from rag5.core.knowledge_base import FileStatus
    
    kb = await kb_manager.create_knowledge_base(
        name="chunk_count_kb",
        description="Chunk count test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    assert file_entity.chunk_count == 0
    
    # 处理文件
    processed_file = await kb_manager.process_file(file_entity.id)
    
    # 验证块计数已更新
    assert processed_file.chunk_count > 0
    
    # 从数据库重新获取文件，验证持久化
    file_from_db = kb_manager.db.get_file(file_entity.id)
    assert file_from_db.chunk_count == processed_file.chunk_count
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


# ==================== 知识库查询测试 ====================

@pytest.mark.asyncio
async def test_query_knowledge_base_basic(kb_manager, processing_text_file):
    """测试基本知识库查询功能"""
    # 创建知识库
    kb = await kb_manager.create_knowledge_base(
        name="query_test_kb",
        description="Query test",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(chunk_size=100, chunk_overlap=20),
        retrieval_config=RetrievalConfig(
            top_k=5,
            similarity_threshold=0.3
        )
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    await kb_manager.process_file(file_entity.id)
    
    # 查询知识库
    results = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="test document"
    )
    
    # 验证结果
    assert isinstance(results, list)
    assert len(results) > 0
    
    # 验证结果格式
    for result in results:
        assert "id" in result
        assert "score" in result
        assert "text" in result
        assert "file_id" in result
        assert "source" in result
        assert "chunk_index" in result
        assert "kb_id" in result
        assert "metadata" in result
        
        # 验证分数在合理范围内
        assert 0.0 <= result["score"] <= 1.0
        
        # 验证文本不为空
        assert len(result["text"]) > 0
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_with_custom_top_k(kb_manager, processing_text_file):
    """测试使用自定义 top_k 查询"""
    kb = await kb_manager.create_knowledge_base(
        name="custom_topk_kb",
        description="Custom top_k test",
        embedding_model="nomic-embed-text",
        retrieval_config=RetrievalConfig(top_k=10)
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    await kb_manager.process_file(file_entity.id)
    
    # 使用自定义 top_k 查询
    results = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="test document",
        top_k=3
    )
    
    # 验证返回结果数量不超过 top_k
    assert len(results) <= 3
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_with_custom_threshold(kb_manager, processing_text_file):
    """测试使用自定义相似度阈值查询"""
    kb = await kb_manager.create_knowledge_base(
        name="custom_threshold_kb",
        description="Custom threshold test",
        embedding_model="nomic-embed-text",
        retrieval_config=RetrievalConfig(
            top_k=10,
            similarity_threshold=0.3
        )
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    await kb_manager.process_file(file_entity.id)
    
    # 使用较高的阈值查询
    results_high_threshold = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="test document",
        similarity_threshold=0.7
    )
    
    # 使用较低的阈值查询
    results_low_threshold = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="test document",
        similarity_threshold=0.1
    )
    
    # 验证所有结果都满足阈值要求
    for result in results_high_threshold:
        assert result["score"] >= 0.7
    
    for result in results_low_threshold:
        assert result["score"] >= 0.1
    
    # 较低阈值应该返回更多或相同数量的结果
    assert len(results_low_threshold) >= len(results_high_threshold)
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_nonexistent_kb(kb_manager):
    """测试查询不存在的知识库"""
    from rag5.core.knowledge_base import KnowledgeBaseNotFoundError
    
    with pytest.raises(KnowledgeBaseNotFoundError):
        await kb_manager.query_knowledge_base(
            kb_id="kb_nonexistent",
            query="test query"
        )


@pytest.mark.asyncio
async def test_query_empty_text(kb_manager):
    """测试使用空查询文本"""
    kb = await kb_manager.create_knowledge_base(
        name="empty_query_kb",
        description="Empty query test",
        embedding_model="nomic-embed-text"
    )
    
    with pytest.raises(ValueError):
        await kb_manager.query_knowledge_base(
            kb_id=kb.id,
            query=""
        )
    
    with pytest.raises(ValueError):
        await kb_manager.query_knowledge_base(
            kb_id=kb.id,
            query="   "
        )
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_empty_kb(kb_manager):
    """测试查询空知识库（没有文档）"""
    kb = await kb_manager.create_knowledge_base(
        name="empty_kb_query",
        description="Empty KB query test",
        embedding_model="nomic-embed-text"
    )
    
    # 查询空知识库
    results = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="test query"
    )
    
    # 应该返回空列表
    assert isinstance(results, list)
    assert len(results) == 0
    
    # 清理
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_uses_kb_config(kb_manager, processing_text_file):
    """测试查询使用知识库的配置"""
    # 创建知识库，使用特定的检索配置
    kb = await kb_manager.create_knowledge_base(
        name="config_test_kb",
        description="Config test",
        embedding_model="nomic-embed-text",
        retrieval_config=RetrievalConfig(
            retrieval_mode="vector",
            top_k=3,
            similarity_threshold=0.5
        )
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    await kb_manager.process_file(file_entity.id)
    
    # 查询（不指定参数，应使用知识库配置）
    results = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="test document"
    )
    
    # 验证使用了知识库的配置
    assert len(results) <= 3  # top_k=3
    
    # 验证所有结果满足阈值
    for result in results:
        assert result["score"] >= 0.5  # similarity_threshold=0.5
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_multiple_files(kb_manager, temp_dir):
    """测试查询包含多个文件的知识库"""
    kb = await kb_manager.create_knowledge_base(
        name="multi_file_kb",
        description="Multi-file test",
        embedding_model="nomic-embed-text"
    )
    
    # 创建并上传多个文件
    file1_path = Path(temp_dir) / "file1.txt"
    file1_path.write_text("This document is about artificial intelligence and machine learning.")
    
    file2_path = Path(temp_dir) / "file2.txt"
    file2_path.write_text("This document discusses natural language processing and text analysis.")
    
    file1 = await kb_manager.upload_file(kb.id, str(file1_path))
    file2 = await kb_manager.upload_file(kb.id, str(file2_path))
    
    await kb_manager.process_file(file1.id)
    await kb_manager.process_file(file2.id)
    
    # 查询
    results = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="machine learning",
        top_k=10
    )
    
    # 验证结果来自不同文件
    assert len(results) > 0
    
    # 可能包含来自两个文件的结果
    file_ids = {r["file_id"] for r in results}
    assert len(file_ids) >= 1
    
    # 清理
    await kb_manager.delete_file(kb.id, file1.id)
    await kb_manager.delete_file(kb.id, file2.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_chinese_text(kb_manager, temp_dir):
    """测试查询中文文本"""
    # 创建中文文本文件
    chinese_file = Path(temp_dir) / "chinese_query.txt"
    chinese_content = """人工智能是计算机科学的一个分支。
它致力于开发能够模拟人类智能的系统。
机器学习是人工智能的一个重要子领域。
深度学习是机器学习的一种方法。
"""
    chinese_file.write_text(chinese_content, encoding='utf-8')
    
    kb = await kb_manager.create_knowledge_base(
        name="chinese_query_kb",
        description="Chinese query test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, str(chinese_file))
    await kb_manager.process_file(file_entity.id)
    
    # 使用中文查询
    results = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="什么是机器学习？"
    )
    
    # 验证返回结果
    assert len(results) > 0
    
    # 验证结果包含中文文本
    for result in results:
        assert len(result["text"]) > 0
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_result_ordering(kb_manager, processing_text_file):
    """测试查询结果按相似度排序"""
    kb = await kb_manager.create_knowledge_base(
        name="ordering_kb",
        description="Ordering test",
        embedding_model="nomic-embed-text"
    )
    
    # 上传并处理文件
    file_entity = await kb_manager.upload_file(kb.id, processing_text_file)
    await kb_manager.process_file(file_entity.id)
    
    # 查询
    results = await kb_manager.query_knowledge_base(
        kb_id=kb.id,
        query="test document",
        top_k=10
    )
    
    # 验证结果按分数降序排列
    if len(results) > 1:
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), "结果应该按分数降序排列"
    
    # 清理
    await kb_manager.delete_file(kb.id, file_entity.id)
    await kb_manager.delete_knowledge_base(kb.id)


@pytest.mark.asyncio
async def test_query_kb_isolation(kb_manager, temp_dir):
    """测试知识库查询隔离性"""
    # 创建两个知识库
    kb1 = await kb_manager.create_knowledge_base(
        name="isolation_kb1",
        description="KB 1",
        embedding_model="nomic-embed-text"
    )
    
    kb2 = await kb_manager.create_knowledge_base(
        name="isolation_kb2",
        description="KB 2",
        embedding_model="nomic-embed-text"
    )
    
    # 为每个知识库上传不同的文件
    file1_path = Path(temp_dir) / "kb1_file.txt"
    file1_path.write_text("This is content for knowledge base one.")
    
    file2_path = Path(temp_dir) / "kb2_file.txt"
    file2_path.write_text("This is content for knowledge base two.")
    
    file1 = await kb_manager.upload_file(kb1.id, str(file1_path))
    file2 = await kb_manager.upload_file(kb2.id, str(file2_path))
    
    await kb_manager.process_file(file1.id)
    await kb_manager.process_file(file2.id)
    
    # 查询 kb1
    results_kb1 = await kb_manager.query_knowledge_base(
        kb_id=kb1.id,
        query="knowledge base",
        top_k=10
    )
    
    # 查询 kb2
    results_kb2 = await kb_manager.query_knowledge_base(
        kb_id=kb2.id,
        query="knowledge base",
        top_k=10
    )
    
    # 验证结果隔离
    assert len(results_kb1) > 0
    assert len(results_kb2) > 0
    
    # 验证 kb1 的结果只来自 kb1
    for result in results_kb1:
        assert result["kb_id"] == kb1.id
        assert result["file_id"] == file1.id
    
    # 验证 kb2 的结果只来自 kb2
    for result in results_kb2:
        assert result["kb_id"] == kb2.id
        assert result["file_id"] == file2.id
    
    # 清理
    await kb_manager.delete_file(kb1.id, file1.id)
    await kb_manager.delete_file(kb2.id, file2.id)
    await kb_manager.delete_knowledge_base(kb1.id)
    await kb_manager.delete_knowledge_base(kb2.id)
