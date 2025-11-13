"""
配置验证器模块

负责验证配置值的有效性。
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ConfigValidator:
    """
    配置验证器类

    验证配置值的有效性，包括 URL、整数、浮点数、范围等。

    示例:
        >>> validator = ConfigValidator()
        >>> is_valid = validator.validate_url('http://localhost:11434')
        >>> errors = validator.validate_all(config_dict)
    """

    def __init__(self):
        """初始化配置验证器"""
        self._errors: List[str] = []
        self._warnings: List[str] = []

    def validate_url(self, url: str, field_name: str = "URL") -> bool:
        """
        验证 URL 格式

        参数:
            url: 要验证的 URL
            field_name: 字段名称，用于错误消息

        返回:
            True 如果 URL 有效，否则 False

        示例:
            >>> validator = ConfigValidator()
            >>> validator.validate_url('http://localhost:11434', 'OLLAMA_HOST')
            True
        """
        if not url:
            self._errors.append(f"{field_name} 不能为空")
            return False

        # 检查是否以 http:// 或 https:// 开头
        if not url.startswith(('http://', 'https://')):
            # 检查是否是常见的错误格式
            if url.startswith('localhost') or url.split(':')[0].replace('.', '').replace('-', '').isalnum():
                self._warnings.append(f"{field_name} 应该包含协议前缀 (http:// 或 https://): {url}")
                return True  # 宽松验证，只是警告
            else:
                self._errors.append(f"{field_name} 必须是有效的 URL，以 http:// 或 https:// 开头: {url}")
                return False

        # 使用 urlparse 进行更详细的验证
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                self._errors.append(f"{field_name} 缺少主机名: {url}")
                return False
            return True
        except Exception as e:
            self._errors.append(f"{field_name} 格式无效: {url} ({e})")
            return False

    def validate_positive_int(self, value: int, field_name: str = "值") -> bool:
        """
        验证正整数

        参数:
            value: 要验证的整数
            field_name: 字段名称，用于错误消息

        返回:
            True 如果值是正整数，否则 False

        示例:
            >>> validator = ConfigValidator()
            >>> validator.validate_positive_int(5, 'TOP_K')
            True
        """
        if not isinstance(value, int):
            self._errors.append(f"{field_name} 必须是整数: {value}")
            return False

        if value <= 0:
            self._errors.append(f"{field_name} 必须大于 0: {value}")
            return False

        return True

    def validate_non_negative_int(self, value: int, field_name: str = "值") -> bool:
        """
        验证非负整数

        参数:
            value: 要验证的整数
            field_name: 字段名称，用于错误消息

        返回:
            True 如果值是非负整数，否则 False
        """
        if not isinstance(value, int):
            self._errors.append(f"{field_name} 必须是整数: {value}")
            return False

        if value < 0:
            self._errors.append(f"{field_name} 不能为负数: {value}")
            return False

        return True

    def validate_range(self, value: float, min_val: float, max_val: float,
                      field_name: str = "值") -> bool:
        """
        验证值是否在指定范围内

        参数:
            value: 要验证的值
            min_val: 最小值（包含）
            max_val: 最大值（包含）
            field_name: 字段名称，用于错误消息

        返回:
            True 如果值在范围内，否则 False

        示例:
            >>> validator = ConfigValidator()
            >>> validator.validate_range(0.7, 0.0, 1.0, 'SIMILARITY_THRESHOLD')
            True
        """
        if not isinstance(value, (int, float)):
            self._errors.append(f"{field_name} 必须是数字: {value}")
            return False

        if value < min_val or value > max_val:
            self._errors.append(f"{field_name} 必须在 {min_val} 到 {max_val} 之间: {value}")
            return False

        return True

    def validate_non_empty_string(self, value: str, field_name: str = "值") -> bool:
        """
        验证非空字符串

        参数:
            value: 要验证的字符串
            field_name: 字段名称，用于错误消息

        返回:
            True 如果字符串非空，否则 False
        """
        if not isinstance(value, str):
            self._errors.append(f"{field_name} 必须是字符串: {value}")
            return False

        if not value.strip():
            self._errors.append(f"{field_name} 不能为空")
            return False

        return True

    def validate_comparison(self, value1: Any, value2: Any,
                          field_name1: str, field_name2: str,
                          operator: str = '<') -> bool:
        """
        验证两个值的比较关系

        参数:
            value1: 第一个值
            value2: 第二个值
            field_name1: 第一个字段名称
            field_name2: 第二个字段名称
            operator: 比较操作符 ('<', '<=', '>', '>=')

        返回:
            True 如果比较关系成立，否则 False
        """
        try:
            if operator == '<':
                result = value1 < value2
                op_text = "小于"
            elif operator == '<=':
                result = value1 <= value2
                op_text = "小于等于"
            elif operator == '>':
                result = value1 > value2
                op_text = "大于"
            elif operator == '>=':
                result = value1 >= value2
                op_text = "大于等于"
            else:
                self._errors.append(f"不支持的比较操作符: {operator}")
                return False

            if not result:
                self._errors.append(f"{field_name1} ({value1}) 必须{op_text} {field_name2} ({value2})")
                return False

            return True
        except Exception as e:
            self._errors.append(f"比较 {field_name1} 和 {field_name2} 时出错: {e}")
            return False

    def validate_all(self, config: Dict[str, Any]) -> List[str]:
        """
        验证所有配置项

        参数:
            config: 配置字典

        返回:
            错误消息列表，如果没有错误则返回空列表

        示例:
            >>> validator = ConfigValidator()
            >>> config = {
            ...     'ollama_host': 'http://localhost:11434',
            ...     'top_k': 5,
            ...     'similarity_threshold': 0.7
            ... }
            >>> errors = validator.validate_all(config)
            >>> if errors:
            ...     print("配置错误:", errors)
        """
        self._errors = []
        self._warnings = []

        # 验证 Ollama 配置
        if 'ollama_host' in config:
            self.validate_url(config['ollama_host'], 'OLLAMA_HOST')

        if 'llm_model' in config:
            self.validate_non_empty_string(config['llm_model'], 'LLM_MODEL')

        if 'embed_model' in config:
            self.validate_non_empty_string(config['embed_model'], 'EMBED_MODEL')

        # 验证 Qdrant 配置
        if 'qdrant_url' in config:
            self.validate_url(config['qdrant_url'], 'QDRANT_URL')

        if 'collection_name' in config:
            self.validate_non_empty_string(config['collection_name'], 'COLLECTION_NAME')

        # 验证检索参数
        if 'top_k' in config:
            self.validate_positive_int(config['top_k'], 'TOP_K')

        if 'similarity_threshold' in config:
            self.validate_range(config['similarity_threshold'], 0.0, 1.0, 'SIMILARITY_THRESHOLD')

        # 验证分块参数
        if 'chunk_size' in config:
            self.validate_positive_int(config['chunk_size'], 'CHUNK_SIZE')

        if 'chunk_overlap' in config:
            self.validate_non_negative_int(config['chunk_overlap'], 'CHUNK_OVERLAP')

            # 验证 chunk_overlap < chunk_size
            if 'chunk_size' in config and 'chunk_overlap' in config:
                self.validate_comparison(
                    config['chunk_overlap'],
                    config['chunk_size'],
                    'CHUNK_OVERLAP',
                    'CHUNK_SIZE',
                    '<'
                )

        # 验证其他参数
        if 'max_query_length' in config:
            self.validate_positive_int(config['max_query_length'], 'MAX_QUERY_LENGTH')

        if 'llm_timeout' in config:
            self.validate_positive_int(config['llm_timeout'], 'LLM_TIMEOUT')

        if 'vector_dim' in config:
            self.validate_positive_int(config['vector_dim'], 'VECTOR_DIM')

        # 验证知识库管理配置
        if 'kb_database_path' in config:
            self.validate_non_empty_string(config['kb_database_path'], 'KB_DATABASE_PATH')

        if 'file_storage_path' in config:
            self.validate_non_empty_string(config['file_storage_path'], 'FILE_STORAGE_PATH')

        if 'max_file_size' in config:
            self.validate_positive_int(config['max_file_size'], 'MAX_FILE_SIZE')

        if 'kb_chunk_size' in config:
            self.validate_positive_int(config['kb_chunk_size'], 'KB_CHUNK_SIZE')
            # 验证范围 100-2048
            if config['kb_chunk_size'] < 100 or config['kb_chunk_size'] > 2048:
                self._errors.append(f"KB_CHUNK_SIZE 必须在 100 到 2048 之间: {config['kb_chunk_size']}")

        if 'kb_chunk_overlap' in config:
            self.validate_non_negative_int(config['kb_chunk_overlap'], 'KB_CHUNK_OVERLAP')
            # 验证范围 0-500
            if config['kb_chunk_overlap'] > 500:
                self._errors.append(f"KB_CHUNK_OVERLAP 不能超过 500: {config['kb_chunk_overlap']}")
            
            # 验证 kb_chunk_overlap < kb_chunk_size
            if 'kb_chunk_size' in config and 'kb_chunk_overlap' in config:
                self.validate_comparison(
                    config['kb_chunk_overlap'],
                    config['kb_chunk_size'],
                    'KB_CHUNK_OVERLAP',
                    'KB_CHUNK_SIZE',
                    '<'
                )

        if 'kb_parser_type' in config:
            allowed_parser_types = ["sentence", "recursive", "semantic"]
            if config['kb_parser_type'] not in allowed_parser_types:
                self._errors.append(
                    f"KB_PARSER_TYPE 必须是以下之一: {', '.join(allowed_parser_types)}"
                )

        if 'kb_retrieval_mode' in config:
            allowed_retrieval_modes = ["vector", "fulltext", "hybrid"]
            if config['kb_retrieval_mode'] not in allowed_retrieval_modes:
                self._errors.append(
                    f"KB_RETRIEVAL_MODE 必须是以下之一: {', '.join(allowed_retrieval_modes)}"
                )

        if 'kb_top_k' in config:
            self.validate_positive_int(config['kb_top_k'], 'KB_TOP_K')
            # 验证范围 1-100
            if config['kb_top_k'] < 1 or config['kb_top_k'] > 100:
                self._errors.append(f"KB_TOP_K 必须在 1 到 100 之间: {config['kb_top_k']}")

        if 'kb_similarity_threshold' in config:
            self.validate_range(
                config['kb_similarity_threshold'], 
                0.0, 
                1.0, 
                'KB_SIMILARITY_THRESHOLD'
            )

        if 'kb_vector_weight' in config:
            self.validate_range(
                config['kb_vector_weight'], 
                0.0, 
                1.0, 
                'KB_VECTOR_WEIGHT'
            )

        if 'kb_name_min_length' in config:
            self.validate_positive_int(config['kb_name_min_length'], 'KB_NAME_MIN_LENGTH')

        if 'kb_name_max_length' in config:
            self.validate_positive_int(config['kb_name_max_length'], 'KB_NAME_MAX_LENGTH')
            
            # 验证 kb_name_min_length < kb_name_max_length
            if 'kb_name_min_length' in config and 'kb_name_max_length' in config:
                self.validate_comparison(
                    config['kb_name_min_length'],
                    config['kb_name_max_length'],
                    'KB_NAME_MIN_LENGTH',
                    'KB_NAME_MAX_LENGTH',
                    '<'
                )

        if 'kb_file_batch_size' in config:
            self.validate_positive_int(config['kb_file_batch_size'], 'KB_FILE_BATCH_SIZE')

        if 'kb_file_processing_timeout' in config:
            self.validate_positive_int(config['kb_file_processing_timeout'], 'KB_FILE_PROCESSING_TIMEOUT')

        if 'supported_file_formats' in config:
            if not isinstance(config['supported_file_formats'], list):
                self._errors.append("SUPPORTED_FILE_FORMATS 必须是列表")
            elif not config['supported_file_formats']:
                self._errors.append("SUPPORTED_FILE_FORMATS 不能为空列表")
            else:
                # 验证每个格式都是字符串且以点开头
                for fmt in config['supported_file_formats']:
                    if not isinstance(fmt, str):
                        self._errors.append(f"文件格式必须是字符串: {fmt}")
                    elif not fmt.startswith('.'):
                        self._warnings.append(f"文件格式应该以点开头: {fmt}")

        # 记录警告
        for warning in self._warnings:
            logger.warning(warning)

        return self._errors

    def get_errors(self) -> List[str]:
        """获取所有错误消息"""
        return self._errors

    def get_warnings(self) -> List[str]:
        """获取所有警告消息"""
        return self._warnings

    def clear(self):
        """清除所有错误和警告"""
        self._errors = []
        self._warnings = []
