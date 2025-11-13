"""
测试知识库数据模型

测试 ChunkConfig, RetrievalConfig, KnowledgeBase, FileEntity 的验证和约束。
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from rag5.core.knowledge_base.models import (
    ChunkConfig,
    RetrievalConfig,
    KnowledgeBase,
    FileEntity,
    FileStatus
)


class TestChunkConfig:
    """测试 ChunkConfig 模型"""
    
    def test_default_values(self):
        """测试默认值"""
        config = ChunkConfig()
        
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.parser_type == "sentence"
        assert config.separator == "\n\n"
    
    def test_custom_values(self):
        """测试自定义值"""
        config = ChunkConfig(
            chunk_size=1024,
            chunk_overlap=100,
            parser_type="recursive",
            separator="\n"
        )
        
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 100
        assert config.parser_type == "recursive"
        assert config.separator == "\n"
    
    def test_chunk_size_validation_min(self):
        """测试 chunk_size 最小值验证"""
        with pytest.raises(ValidationError):
            ChunkConfig(chunk_size=50)  # 小于 100
    
    def test_chunk_size_validation_max(self):
        """测试 chunk_size 最大值验证"""
        with pytest.raises(ValidationError):
            ChunkConfig(chunk_size=3000)  # 大于 2048
    
    def test_chunk_overlap_validation_min(self):
        """测试 chunk_overlap 最小值验证"""
        with pytest.raises(ValidationError):
            ChunkConfig(chunk_overlap=-1)  # 小于 0
    
    def test_chunk_overlap_validation_max(self):
        """测试 chunk_overlap 最大值验证"""
        with pytest.raises(ValidationError):
            ChunkConfig(chunk_overlap=600)  # 大于 500
    
    def test_chunk_overlap_exceeds_chunk_size(self):
        """测试 chunk_overlap 不能大于等于 chunk_size"""
        with pytest.raises(ValidationError, match="chunk_overlap 必须小于 chunk_size"):
            ChunkConfig(chunk_size=100, chunk_overlap=100)
        
        with pytest.raises(ValidationError, match="chunk_overlap 必须小于 chunk_size"):
            ChunkConfig(chunk_size=100, chunk_overlap=150)
    
    def test_parser_type_validation(self):
        """测试 parser_type 验证"""
        # 有效的类型
        for parser_type in ["sentence", "recursive", "semantic"]:
            config = ChunkConfig(parser_type=parser_type)
            assert config.parser_type == parser_type
        
        # 无效的类型
        with pytest.raises(ValidationError, match="parser_type 必须是以下之一"):
            ChunkConfig(parser_type="invalid")
    
    def test_valid_edge_cases(self):
        """测试有效的边界情况"""
        # 最小有效配置
        config = ChunkConfig(chunk_size=100, chunk_overlap=0)
        assert config.chunk_size == 100
        assert config.chunk_overlap == 0
        
        # 最大有效配置
        config = ChunkConfig(chunk_size=2048, chunk_overlap=500)
        assert config.chunk_size == 2048
        assert config.chunk_overlap == 500


class TestRetrievalConfig:
    """测试 RetrievalConfig 模型"""
    
    def test_default_values(self):
        """测试默认值"""
        config = RetrievalConfig()
        
        assert config.retrieval_mode == "hybrid"
        assert config.top_k == 5
        assert config.similarity_threshold == 0.3
        assert config.vector_weight == 0.5
        assert config.enable_rerank is False
        assert config.rerank_model == ""
    
    def test_custom_values(self):
        """测试自定义值"""
        config = RetrievalConfig(
            retrieval_mode="vector",
            top_k=10,
            similarity_threshold=0.7,
            vector_weight=0.8,
            enable_rerank=True,
            rerank_model="bge-reranker"
        )
        
        assert config.retrieval_mode == "vector"
        assert config.top_k == 10
        assert config.similarity_threshold == 0.7
        assert config.vector_weight == 0.8
        assert config.enable_rerank is True
        assert config.rerank_model == "bge-reranker"
    
    def test_retrieval_mode_validation(self):
        """测试 retrieval_mode 验证"""
        # 有效的模式
        for mode in ["vector", "fulltext", "hybrid"]:
            config = RetrievalConfig(retrieval_mode=mode)
            assert config.retrieval_mode == mode
        
        # 无效的模式
        with pytest.raises(ValidationError, match="retrieval_mode 必须是以下之一"):
            RetrievalConfig(retrieval_mode="invalid")
    
    def test_top_k_validation(self):
        """测试 top_k 验证"""
        # 有效范围
        config = RetrievalConfig(top_k=1)
        assert config.top_k == 1
        
        config = RetrievalConfig(top_k=100)
        assert config.top_k == 100
        
        # 无效范围
        with pytest.raises(ValidationError):
            RetrievalConfig(top_k=0)
        
        with pytest.raises(ValidationError):
            RetrievalConfig(top_k=101)
    
    def test_similarity_threshold_validation(self):
        """测试 similarity_threshold 验证"""
        # 有效范围
        config = RetrievalConfig(similarity_threshold=0.0)
        assert config.similarity_threshold == 0.0
        
        config = RetrievalConfig(similarity_threshold=1.0)
        assert config.similarity_threshold == 1.0
        
        # 无效范围
        with pytest.raises(ValidationError):
            RetrievalConfig(similarity_threshold=-0.1)
        
        with pytest.raises(ValidationError):
            RetrievalConfig(similarity_threshold=1.1)
    
    def test_vector_weight_validation(self):
        """测试 vector_weight 验证"""
        # 有效范围
        config = RetrievalConfig(vector_weight=0.0)
        assert config.vector_weight == 0.0
        
        config = RetrievalConfig(vector_weight=1.0)
        assert config.vector_weight == 1.0
        
        # 无效范围
        with pytest.raises(ValidationError):
            RetrievalConfig(vector_weight=-0.1)
        
        with pytest.raises(ValidationError):
            RetrievalConfig(vector_weight=1.1)


class TestKnowledgeBase:
    """测试 KnowledgeBase 模型"""
    
    def test_minimal_creation(self):
        """测试最小化创建"""
        kb = KnowledgeBase(
            id="kb_test123",
            name="test_kb",
            embedding_model="nomic-embed-text"
        )
        
        assert kb.id == "kb_test123"
        assert kb.name == "test_kb"
        assert kb.embedding_model == "nomic-embed-text"
        assert kb.description == ""
        assert isinstance(kb.chunk_config, ChunkConfig)
        assert isinstance(kb.retrieval_config, RetrievalConfig)
        assert kb.document_count == 0
        assert kb.total_size == 0
    
    def test_full_creation(self):
        """测试完整创建"""
        chunk_config = ChunkConfig(chunk_size=1024)
        retrieval_config = RetrievalConfig(top_k=10)
        
        kb = KnowledgeBase(
            id="kb_test123",
            name="test_kb",
            description="Test KB",
            embedding_model="nomic-embed-text",
            chunk_config=chunk_config,
            retrieval_config=retrieval_config,
            document_count=5,
            total_size=10000
        )
        
        assert kb.description == "Test KB"
        assert kb.chunk_config.chunk_size == 1024
        assert kb.retrieval_config.top_k == 10
        assert kb.document_count == 5
        assert kb.total_size == 10000
    
    def test_name_validation_empty(self):
        """测试空名称验证"""
        with pytest.raises(ValidationError, match="知识库名称不能为空"):
            KnowledgeBase(
                id="kb_test",
                name="",
                embedding_model="model"
            )
    
    def test_name_validation_format(self):
        """测试名称格式验证"""
        # 有效名称
        valid_names = ["test_kb", "test-kb", "TestKB123", "kb_123"]
        for name in valid_names:
            kb = KnowledgeBase(
                id=f"kb_{name}",
                name=name,
                embedding_model="model"
            )
            assert kb.name == name
        
        # 无效名称（包含特殊字符）
        invalid_names = ["test kb", "test.kb", "test@kb", "测试kb"]
        for name in invalid_names:
            with pytest.raises(ValidationError, match="只能包含字母、数字、下划线和连字符"):
                KnowledgeBase(
                    id="kb_test",
                    name=name,
                    embedding_model="model"
                )
    
    def test_name_validation_length(self):
        """测试名称长度验证"""
        # 太短
        with pytest.raises(ValidationError, match="长度必须在 2-64 个字符之间"):
            KnowledgeBase(
                id="kb_test",
                name="a",
                embedding_model="model"
            )
        
        # 太长
        with pytest.raises(ValidationError, match="长度必须在 2-64 个字符之间"):
            KnowledgeBase(
                id="kb_test",
                name="a" * 65,
                embedding_model="model"
            )
        
        # 边界情况 - 有效
        kb = KnowledgeBase(
            id="kb_test",
            name="ab",  # 2 个字符
            embedding_model="model"
        )
        assert kb.name == "ab"
        
        kb = KnowledgeBase(
            id="kb_test",
            name="a" * 64,  # 64 个字符
            embedding_model="model"
        )
        assert len(kb.name) == 64
    
    def test_embedding_model_validation(self):
        """测试 embedding_model 验证"""
        # 空字符串
        with pytest.raises(ValidationError, match="embedding_model 不能为空"):
            KnowledgeBase(
                id="kb_test",
                name="test",
                embedding_model=""
            )
        
        # 只有空格
        with pytest.raises(ValidationError, match="embedding_model 不能为空"):
            KnowledgeBase(
                id="kb_test",
                name="test",
                embedding_model="   "
            )
        
        # 有效值（会被 strip）
        kb = KnowledgeBase(
            id="kb_test",
            name="test",
            embedding_model="  model  "
        )
        assert kb.embedding_model == "model"
    
    def test_document_count_validation(self):
        """测试 document_count 验证"""
        # 有效值
        kb = KnowledgeBase(
            id="kb_test",
            name="test",
            embedding_model="model",
            document_count=0
        )
        assert kb.document_count == 0
        
        kb = KnowledgeBase(
            id="kb_test",
            name="test",
            embedding_model="model",
            document_count=100
        )
        assert kb.document_count == 100
        
        # 无效值（负数）
        with pytest.raises(ValidationError):
            KnowledgeBase(
                id="kb_test",
                name="test",
                embedding_model="model",
                document_count=-1
            )
    
    def test_total_size_validation(self):
        """测试 total_size 验证"""
        # 有效值
        kb = KnowledgeBase(
            id="kb_test",
            name="test",
            embedding_model="model",
            total_size=0
        )
        assert kb.total_size == 0
        
        # 无效值（负数）
        with pytest.raises(ValidationError):
            KnowledgeBase(
                id="kb_test",
                name="test",
                embedding_model="model",
                total_size=-1
            )
    
    def test_timestamps(self):
        """测试时间戳"""
        kb = KnowledgeBase(
            id="kb_test",
            name="test",
            embedding_model="model"
        )
        
        assert isinstance(kb.created_at, datetime)
        assert isinstance(kb.updated_at, datetime)
        assert kb.updated_at >= kb.created_at
    
    def test_updated_at_before_created_at(self):
        """测试 updated_at 早于 created_at 时的自动修正"""
        now = datetime.now()
        earlier = datetime(2020, 1, 1)
        
        kb = KnowledgeBase(
            id="kb_test",
            name="test",
            embedding_model="model",
            created_at=now,
            updated_at=earlier
        )
        
        # updated_at 应该被修正为 created_at
        assert kb.updated_at == kb.created_at


class TestFileEntity:
    """测试 FileEntity 模型"""
    
    def test_minimal_creation(self):
        """测试最小化创建"""
        file = FileEntity(
            id="file_test123",
            kb_id="kb_test123",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            file_extension=".txt",
            file_size=1000,
            file_md5="d41d8cd98f00b204e9800998ecf8427e"
        )
        
        assert file.id == "file_test123"
        assert file.kb_id == "kb_test123"
        assert file.file_name == "test.txt"
        assert file.file_path == "/path/to/test.txt"
        assert file.file_extension == ".txt"
        assert file.file_size == 1000
        assert file.file_md5 == "d41d8cd98f00b204e9800998ecf8427e"
        assert file.status == FileStatus.PENDING
        assert file.failed_reason is None
        assert file.chunk_count == 0
        assert isinstance(file.metadata, dict)
    
    def test_full_creation(self):
        """测试完整创建"""
        file = FileEntity(
            id="file_test123",
            kb_id="kb_test123",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            file_extension=".txt",
            file_size=1000,
            file_md5="d41d8cd98f00b204e9800998ecf8427e",
            status=FileStatus.SUCCEEDED,
            failed_reason=None,
            chunk_count=10,
            metadata={"key": "value"}
        )
        
        assert file.status == FileStatus.SUCCEEDED
        assert file.chunk_count == 10
        assert file.metadata == {"key": "value"}
    
    def test_file_name_validation(self):
        """测试文件名验证"""
        # 空文件名
        with pytest.raises(ValidationError, match="文件名不能为空"):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="",
                file_path="/path",
                file_extension=".txt",
                file_size=100,
                file_md5="d41d8cd98f00b204e9800998ecf8427e"
            )
        
        # 只有空格
        with pytest.raises(ValidationError, match="文件名不能为空"):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="   ",
                file_path="/path",
                file_extension=".txt",
                file_size=100,
                file_md5="d41d8cd98f00b204e9800998ecf8427e"
            )
        
        # 有效文件名（会被 strip）
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="  test.txt  ",
            file_path="/path",
            file_extension=".txt",
            file_size=100,
            file_md5="d41d8cd98f00b204e9800998ecf8427e"
        )
        assert file.file_name == "test.txt"
    
    def test_file_extension_validation(self):
        """测试文件扩展名验证"""
        # 支持的格式
        supported_formats = [".txt", ".md", ".pdf", ".docx"]
        for ext in supported_formats:
            file = FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name=f"test{ext}",
                file_path="/path",
                file_extension=ext,
                file_size=100,
                file_md5="d41d8cd98f00b204e9800998ecf8427e"
            )
            assert file.file_extension == ext.lower()
        
        # 不支持的格式
        with pytest.raises(ValidationError, match="不支持的文件格式"):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="test.xyz",
                file_path="/path",
                file_extension=".xyz",
                file_size=100,
                file_md5="d41d8cd98f00b204e9800998ecf8427e"
            )
        
        # 自动添加点
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.txt",
            file_path="/path",
            file_extension="txt",  # 没有点
            file_size=100,
            file_md5="d41d8cd98f00b204e9800998ecf8427e"
        )
        assert file.file_extension == ".txt"
        
        # 大小写不敏感
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.TXT",
            file_path="/path",
            file_extension=".TXT",
            file_size=100,
            file_md5="d41d8cd98f00b204e9800998ecf8427e"
        )
        assert file.file_extension == ".txt"
    
    def test_file_size_validation(self):
        """测试文件大小验证"""
        # 有效值
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.txt",
            file_path="/path",
            file_extension=".txt",
            file_size=0,
            file_md5="d41d8cd98f00b204e9800998ecf8427e"
        )
        assert file.file_size == 0
        
        # 无效值（负数）
        with pytest.raises(ValidationError):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="test.txt",
                file_path="/path",
                file_extension=".txt",
                file_size=-1,
                file_md5="d41d8cd98f00b204e9800998ecf8427e"
            )
    
    def test_file_md5_validation(self):
        """测试 MD5 哈希验证"""
        # 有效的 MD5
        valid_md5 = "d41d8cd98f00b204e9800998ecf8427e"
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.txt",
            file_path="/path",
            file_extension=".txt",
            file_size=100,
            file_md5=valid_md5
        )
        assert file.file_md5 == valid_md5.lower()
        
        # 大写 MD5（会被转换为小写）
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.txt",
            file_path="/path",
            file_extension=".txt",
            file_size=100,
            file_md5="D41D8CD98F00B204E9800998ECF8427E"
        )
        assert file.file_md5 == "d41d8cd98f00b204e9800998ecf8427e"
        
        # 空 MD5
        with pytest.raises(ValidationError, match="file_md5 不能为空"):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="test.txt",
                file_path="/path",
                file_extension=".txt",
                file_size=100,
                file_md5=""
            )
        
        # 无效格式（太短）
        with pytest.raises(ValidationError, match="必须是有效的 MD5 哈希值"):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="test.txt",
                file_path="/path",
                file_extension=".txt",
                file_size=100,
                file_md5="abc123"
            )
        
        # 无效格式（包含非十六进制字符）
        with pytest.raises(ValidationError, match="必须是有效的 MD5 哈希值"):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="test.txt",
                file_path="/path",
                file_extension=".txt",
                file_size=100,
                file_md5="g41d8cd98f00b204e9800998ecf8427e"
            )
    
    def test_chunk_count_validation(self):
        """测试 chunk_count 验证"""
        # 有效值
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.txt",
            file_path="/path",
            file_extension=".txt",
            file_size=100,
            file_md5="d41d8cd98f00b204e9800998ecf8427e",
            chunk_count=0
        )
        assert file.chunk_count == 0
        
        # 无效值（负数）
        with pytest.raises(ValidationError):
            FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="test.txt",
                file_path="/path",
                file_extension=".txt",
                file_size=100,
                file_md5="d41d8cd98f00b204e9800998ecf8427e",
                chunk_count=-1
            )
    
    def test_file_status_enum(self):
        """测试文件状态枚举"""
        # 所有有效状态
        for status in FileStatus:
            file = FileEntity(
                id="file_test",
                kb_id="kb_test",
                file_name="test.txt",
                file_path="/path",
                file_extension=".txt",
                file_size=100,
                file_md5="d41d8cd98f00b204e9800998ecf8427e",
                status=status
            )
            assert file.status == status
    
    def test_timestamps(self):
        """测试时间戳"""
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.txt",
            file_path="/path",
            file_extension=".txt",
            file_size=100,
            file_md5="d41d8cd98f00b204e9800998ecf8427e"
        )
        
        assert isinstance(file.created_at, datetime)
        assert isinstance(file.updated_at, datetime)
        assert file.updated_at >= file.created_at
    
    def test_updated_at_before_created_at(self):
        """测试 updated_at 早于 created_at 时的自动修正"""
        now = datetime.now()
        earlier = datetime(2020, 1, 1)
        
        file = FileEntity(
            id="file_test",
            kb_id="kb_test",
            file_name="test.txt",
            file_path="/path",
            file_extension=".txt",
            file_size=100,
            file_md5="d41d8cd98f00b204e9800998ecf8427e",
            created_at=now,
            updated_at=earlier
        )
        
        # updated_at 应该被修正为 created_at
        assert file.updated_at == file.created_at


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
