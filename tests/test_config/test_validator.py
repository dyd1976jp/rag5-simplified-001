"""
测试配置验证器模块
"""

import pytest
from rag5.config.validator import ConfigValidator


def test_validator_initialization():
    """测试ConfigValidator初始化"""
    validator = ConfigValidator()
    assert validator is not None
    assert validator.errors == []


def test_validate_url_valid():
    """测试验证有效URL"""
    validator = ConfigValidator()

    valid_urls = [
        'http://localhost:11434',
        'https://example.com',
        'http://192.168.1.1:8080',
        'https://api.example.com/path',
    ]

    for url in valid_urls:
        assert validator.validate_url(url, 'TEST_URL') is True, f"Failed for: {url}"
        assert len(validator.errors) == 0


def test_validate_url_invalid():
    """测试验证无效URL"""
    validator = ConfigValidator()

    invalid_urls = [
        'not-a-url',
        'ftp://invalid-scheme.com',
        'http:/missing-slash',
        '',
        'localhost:11434',  # 缺少协议
    ]

    for url in invalid_urls:
        validator.errors = []  # 重置错误列表
        assert validator.validate_url(url, 'TEST_URL') is False, f"Should fail for: {url}"
        assert len(validator.errors) > 0


def test_validate_positive_int_valid():
    """测试验证正整数"""
    validator = ConfigValidator()

    assert validator.validate_positive_int(1, 'TEST_INT') is True
    assert validator.validate_positive_int(100, 'TEST_INT') is True
    assert validator.validate_positive_int(999999, 'TEST_INT') is True
    assert len(validator.errors) == 0


def test_validate_positive_int_invalid():
    """测试验证无效正整数"""
    validator = ConfigValidator()

    invalid_values = [0, -1, -100]

    for val in invalid_values:
        validator.errors = []
        assert validator.validate_positive_int(val, 'TEST_INT') is False
        assert len(validator.errors) > 0


def test_validate_range_valid():
    """测试验证范围内的值"""
    validator = ConfigValidator()

    assert validator.validate_range(0.5, 0.0, 1.0, 'TEST_RANGE') is True
    assert validator.validate_range(0.0, 0.0, 1.0, 'TEST_RANGE') is True
    assert validator.validate_range(1.0, 0.0, 1.0, 'TEST_RANGE') is True
    assert validator.validate_range(50, 0, 100, 'TEST_RANGE') is True
    assert len(validator.errors) == 0


def test_validate_range_invalid():
    """测试验证范围外的值"""
    validator = ConfigValidator()

    invalid_cases = [
        (-0.1, 0.0, 1.0),
        (1.1, 0.0, 1.0),
        (-1, 0, 100),
        (101, 0, 100),
    ]

    for val, min_val, max_val in invalid_cases:
        validator.errors = []
        assert validator.validate_range(val, min_val, max_val, 'TEST_RANGE') is False
        assert len(validator.errors) > 0


def test_validate_non_empty_valid():
    """测试验证非空字符串"""
    validator = ConfigValidator()

    assert validator.validate_non_empty('test', 'TEST_STR') is True
    assert validator.validate_non_empty('a', 'TEST_STR') is True
    assert validator.validate_non_empty('  text  ', 'TEST_STR') is True
    assert len(validator.errors) == 0


def test_validate_non_empty_invalid():
    """测试验证空字符串"""
    validator = ConfigValidator()

    invalid_values = ['', '   ', '\t', '\n']

    for val in invalid_values:
        validator.errors = []
        assert validator.validate_non_empty(val, 'TEST_STR') is False
        assert len(validator.errors) > 0


def test_validate_all_success():
    """测试验证所有配置（成功）"""
    validator = ConfigValidator()

    config = {
        'ollama_host': 'http://localhost:11434',
        'qdrant_url': 'http://localhost:6333',
        'llm_model': 'qwen2.5:7b',
        'embed_model': 'bge-m3',
        'top_k': 5,
        'similarity_threshold': 0.7,
        'chunk_size': 500,
        'chunk_overlap': 50,
    }

    errors = validator.validate_all(config)
    assert len(errors) == 0


def test_validate_all_with_errors():
    """测试验证所有配置（有错误）"""
    validator = ConfigValidator()

    config = {
        'ollama_host': 'invalid-url',
        'qdrant_url': 'http://localhost:6333',
        'llm_model': '',
        'embed_model': 'bge-m3',
        'top_k': -5,
        'similarity_threshold': 1.5,
        'chunk_size': 500,
        'chunk_overlap': 50,
    }

    errors = validator.validate_all(config)
    assert len(errors) > 0

    # 应该包含多个错误
    error_str = ' '.join(errors)
    assert 'ollama_host' in error_str.lower()
    assert 'llm_model' in error_str.lower()
    assert 'top_k' in error_str.lower()
    assert 'similarity_threshold' in error_str.lower()


def test_validate_all_missing_keys():
    """测试验证缺少必需键的配置"""
    validator = ConfigValidator()

    config = {
        'ollama_host': 'http://localhost:11434',
        # 缺少其他必需的键
    }

    errors = validator.validate_all(config)
    # 应该有错误，因为缺少必需的配置项
    assert len(errors) > 0


def test_error_accumulation():
    """测试错误累积"""
    validator = ConfigValidator()

    # 执行多个验证
    validator.validate_url('invalid', 'URL1')
    validator.validate_positive_int(-1, 'INT1')
    validator.validate_range(2.0, 0.0, 1.0, 'RANGE1')

    # 应该累积所有错误
    assert len(validator.errors) == 3


def test_clear_errors():
    """测试清除错误"""
    validator = ConfigValidator()

    validator.validate_url('invalid', 'URL1')
    assert len(validator.errors) > 0

    validator.errors = []
    assert len(validator.errors) == 0


def test_validate_chunk_overlap():
    """测试验证chunk_overlap小于chunk_size"""
    validator = ConfigValidator()

    # 有效情况
    config = {
        'ollama_host': 'http://localhost:11434',
        'qdrant_url': 'http://localhost:6333',
        'llm_model': 'test',
        'embed_model': 'test',
        'top_k': 5,
        'similarity_threshold': 0.7,
        'chunk_size': 500,
        'chunk_overlap': 50,
    }

    errors = validator.validate_all(config)
    assert len(errors) == 0

    # 无效情况：overlap >= size
    config['chunk_overlap'] = 500
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_chunk_size():
    """测试验证知识库分块大小"""
    validator = ConfigValidator()
    
    # 有效值
    assert validator.validate_positive_int(512, 'KB_CHUNK_SIZE') is True
    validator.errors = []
    
    # 范围验证
    config = {'kb_chunk_size': 512}
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 超出范围
    config = {'kb_chunk_size': 50}  # 小于 100
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0
    
    config = {'kb_chunk_size': 3000}  # 大于 2048
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_chunk_overlap():
    """测试验证知识库分块重叠"""
    validator = ConfigValidator()
    
    # 有效值
    config = {
        'kb_chunk_size': 512,
        'kb_chunk_overlap': 50
    }
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # overlap >= chunk_size
    config = {
        'kb_chunk_size': 512,
        'kb_chunk_overlap': 512
    }
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0
    
    # overlap 超过 500
    config = {'kb_chunk_overlap': 600}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_parser_type():
    """测试验证知识库解析器类型"""
    validator = ConfigValidator()
    
    # 有效值
    for parser_type in ["sentence", "recursive", "semantic"]:
        config = {'kb_parser_type': parser_type}
        validator.errors = []
        errors = validator.validate_all(config)
        assert len(errors) == 0, f"Failed for parser_type: {parser_type}"
    
    # 无效值
    config = {'kb_parser_type': 'invalid'}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_retrieval_mode():
    """测试验证知识库检索模式"""
    validator = ConfigValidator()
    
    # 有效值
    for mode in ["vector", "fulltext", "hybrid"]:
        config = {'kb_retrieval_mode': mode}
        validator.errors = []
        errors = validator.validate_all(config)
        assert len(errors) == 0, f"Failed for retrieval_mode: {mode}"
    
    # 无效值
    config = {'kb_retrieval_mode': 'invalid'}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_top_k():
    """测试验证知识库 top_k"""
    validator = ConfigValidator()
    
    # 有效值
    config = {'kb_top_k': 5}
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 边界值
    config = {'kb_top_k': 1}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    config = {'kb_top_k': 100}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 超出范围
    config = {'kb_top_k': 0}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0
    
    config = {'kb_top_k': 101}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_similarity_threshold():
    """测试验证知识库相似度阈值"""
    validator = ConfigValidator()
    
    # 有效值
    config = {'kb_similarity_threshold': 0.3}
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 边界值
    config = {'kb_similarity_threshold': 0.0}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    config = {'kb_similarity_threshold': 1.0}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 超出范围
    config = {'kb_similarity_threshold': -0.1}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0
    
    config = {'kb_similarity_threshold': 1.1}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_vector_weight():
    """测试验证知识库向量权重"""
    validator = ConfigValidator()
    
    # 有效值
    config = {'kb_vector_weight': 0.5}
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 边界值
    config = {'kb_vector_weight': 0.0}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    config = {'kb_vector_weight': 1.0}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 超出范围
    config = {'kb_vector_weight': -0.1}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0
    
    config = {'kb_vector_weight': 1.1}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_name_length():
    """测试验证知识库名称长度限制"""
    validator = ConfigValidator()
    
    # 有效值
    config = {
        'kb_name_min_length': 2,
        'kb_name_max_length': 64
    }
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # min >= max
    config = {
        'kb_name_min_length': 64,
        'kb_name_max_length': 2
    }
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_file_size():
    """测试验证文件大小限制"""
    validator = ConfigValidator()
    
    # 有效值
    config = {'max_file_size': 50 * 1024 * 1024}
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 无效值
    config = {'max_file_size': 0}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_supported_file_formats():
    """测试验证支持的文件格式"""
    validator = ConfigValidator()
    
    # 有效值
    config = {'supported_file_formats': ['.txt', '.md', '.pdf']}
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 空列表
    config = {'supported_file_formats': []}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0
    
    # 非列表
    config = {'supported_file_formats': '.txt'}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_paths():
    """测试验证知识库路径配置"""
    validator = ConfigValidator()
    
    # 有效值
    config = {
        'kb_database_path': 'data/knowledge_bases.db',
        'file_storage_path': 'docs'
    }
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 空字符串
    config = {'kb_database_path': ''}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


def test_validate_kb_batch_and_timeout():
    """测试验证批处理和超时配置"""
    validator = ConfigValidator()
    
    # 有效值
    config = {
        'kb_file_batch_size': 10,
        'kb_file_processing_timeout': 300
    }
    errors = validator.validate_all(config)
    assert len(errors) == 0
    
    # 无效值
    config = {'kb_file_batch_size': 0}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0
    
    config = {'kb_file_processing_timeout': -1}
    validator.errors = []
    errors = validator.validate_all(config)
    assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
