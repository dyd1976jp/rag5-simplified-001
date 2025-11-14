"""
配置访问接口模块

提供统一的配置访问接口，整合配置加载、验证和默认值。
"""

import logging
from typing import List, Optional
from pathlib import Path

from rag5.config.loader import ConfigLoader
from rag5.config.validator import ConfigValidator
from rag5.config.defaults import (
    DEFAULT_OLLAMA_HOST,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBED_MODEL,
    DEFAULT_LLM_TIMEOUT,
    DEFAULT_QDRANT_URL,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_VECTOR_DIM,
    DEFAULT_TOP_K,
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_ENABLE_HYBRID_SEARCH,
    DEFAULT_VECTOR_SEARCH_WEIGHT,
    DEFAULT_KEYWORD_SEARCH_WEIGHT,
    DEFAULT_MIN_SIMILARITY_THRESHOLD,
    DEFAULT_TARGET_RESULTS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_RESPECT_SENTENCE_BOUNDARY,
    DEFAULT_ENABLE_CHINESE_SPLITTER,
    DEFAULT_SEPARATORS,
    DEFAULT_MAX_QUERY_LENGTH,
    DEFAULT_BATCH_SIZE,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FILE,
    DEFAULT_ENABLE_QUERY_LOGGING,
    DEFAULT_ENABLE_INGESTION_LOGGING,
    DEFAULT_ENABLE_CONSOLE_LOGGING,
    DEFAULT_ENABLE_LLM_LOGGING,
    DEFAULT_ENABLE_REFLECTION_LOGGING,
    DEFAULT_ENABLE_CONTEXT_LOGGING,
    DEFAULT_LLM_LOG_FILE,
    DEFAULT_REFLECTION_LOG_FILE,
    DEFAULT_CONTEXT_LOG_FILE,
    DEFAULT_LOG_PROMPTS,
    DEFAULT_LOG_RESPONSES,
    DEFAULT_REDACT_SENSITIVE,
    DEFAULT_REDACT_PROMPTS,
    DEFAULT_REDACT_RESPONSES,
    DEFAULT_MAX_LOG_ENTRY_SIZE,
    DEFAULT_ASYNC_LOGGING,
    DEFAULT_LOG_BUFFER_SIZE,
    DEFAULT_ENABLE_LOG_ROTATION,
    DEFAULT_LOG_ROTATION_TYPE,
    DEFAULT_LOG_MAX_BYTES,
    DEFAULT_LOG_ROTATION_WHEN,
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_COMPRESS_ROTATED,
    DEFAULT_ENABLE_FLOW_LOGGING,
    DEFAULT_FLOW_LOG_FILE,
    DEFAULT_FLOW_DETAIL_LEVEL,
    DEFAULT_FLOW_MAX_CONTENT_LENGTH,
    DEFAULT_FLOW_ASYNC_LOGGING,
    DEFAULT_KEEP_SEPARATE_LOGS,
    DEFAULT_FLOW_ROTATION_ENABLED,
    DEFAULT_FLOW_ROTATION_TYPE,
    DEFAULT_FLOW_MAX_BYTES,
    DEFAULT_FLOW_ROTATION_WHEN,
    DEFAULT_FLOW_BACKUP_COUNT,
    DEFAULT_FLOW_COMPRESS_ROTATED,
)

logger = logging.getLogger(__name__)


class Settings:
    """
    配置访问接口类

    提供统一的配置访问接口，自动加载环境变量、应用默认值并验证配置。

    示例:
        >>> from rag5.config import settings
        >>> print(settings.ollama_host)
        'http://localhost:11434'
        >>> settings.validate()
    """

    def __init__(self, env_file: str = '.env'):
        """
        初始化配置

        参数:
            env_file: .env 文件路径
        """
        self._loader = ConfigLoader()
        self._validator = ConfigValidator()
        self._validated = False

        # 尝试加载 .env 文件
        # 如果是相对路径，尝试从多个位置查找
        env_path = Path(env_file)
        
        if not env_path.is_absolute():
            # 尝试的路径列表
            search_paths = [
                env_path,  # 当前目录
                Path.cwd() / env_file,  # 工作目录
                Path(__file__).parent.parent.parent / env_file,  # 项目根目录
            ]
            
            for path in search_paths:
                if path.exists():
                    env_path = path
                    break
        
        if env_path.exists():
            self._loader.load_env_file(str(env_path))
        else:
            logger.warning(f".env 文件不存在: {env_file}，将使用默认配置")

    # ========================================================================
    # Ollama 配置属性
    # ========================================================================

    @property
    def ollama_host(self) -> str:
        """Ollama 服务地址"""
        return self._loader.get_env('OLLAMA_HOST', DEFAULT_OLLAMA_HOST)

    @property
    def llm_model(self) -> str:
        """大语言模型名称"""
        return self._loader.get_env('LLM_MODEL', DEFAULT_LLM_MODEL)

    @property
    def embed_model(self) -> str:
        """嵌入模型名称"""
        return self._loader.get_env('EMBED_MODEL', DEFAULT_EMBED_MODEL)

    @property
    def llm_timeout(self) -> int:
        """LLM 请求超时时间（秒）"""
        return self._loader.get_env_int('LLM_TIMEOUT', DEFAULT_LLM_TIMEOUT)

    # ========================================================================
    # Qdrant 配置属性
    # ========================================================================

    @property
    def qdrant_url(self) -> str:
        """Qdrant 向量数据库地址"""
        return self._loader.get_env('QDRANT_URL', DEFAULT_QDRANT_URL)

    @property
    def collection_name(self) -> str:
        """向量集合名称"""
        return self._loader.get_env('COLLECTION_NAME', DEFAULT_COLLECTION_NAME)

    @property
    def vector_dim(self) -> int:
        """向量维度"""
        return self._loader.get_env_int('VECTOR_DIM', DEFAULT_VECTOR_DIM)

    # ========================================================================
    # 检索参数属性
    # ========================================================================

    @property
    def top_k(self) -> int:
        """检索返回的最大结果数"""
        return self._loader.get_env_int('TOP_K', DEFAULT_TOP_K)

    @property
    def similarity_threshold(self) -> float:
        """相似度阈值"""
        return self._loader.get_env_float('SIMILARITY_THRESHOLD', DEFAULT_SIMILARITY_THRESHOLD)

    @property
    def enable_hybrid_search(self) -> bool:
        """是否启用混合搜索（向量+关键词）"""
        return self._loader.get_env_bool('ENABLE_HYBRID_SEARCH', DEFAULT_ENABLE_HYBRID_SEARCH)

    @property
    def vector_search_weight(self) -> float:
        """混合搜索中向量搜索的权重"""
        return self._loader.get_env_float('VECTOR_SEARCH_WEIGHT', DEFAULT_VECTOR_SEARCH_WEIGHT)

    @property
    def keyword_search_weight(self) -> float:
        """混合搜索中关键词搜索的权重"""
        return self._loader.get_env_float('KEYWORD_SEARCH_WEIGHT', DEFAULT_KEYWORD_SEARCH_WEIGHT)

    @property
    def min_similarity_threshold(self) -> float:
        """自适应搜索的最小阈值"""
        return self._loader.get_env_float('MIN_SIMILARITY_THRESHOLD', DEFAULT_MIN_SIMILARITY_THRESHOLD)

    @property
    def target_results(self) -> int:
        """自适应搜索的目标结果数"""
        return self._loader.get_env_int('TARGET_RESULTS', DEFAULT_TARGET_RESULTS)

    # ========================================================================
    # 分块参数属性
    # ========================================================================

    @property
    def chunk_size(self) -> int:
        """文档分块大小（字符数）"""
        return self._loader.get_env_int('CHUNK_SIZE', DEFAULT_CHUNK_SIZE)

    @property
    def chunk_overlap(self) -> int:
        """分块重叠大小（字符数）"""
        return self._loader.get_env_int('CHUNK_OVERLAP', DEFAULT_CHUNK_OVERLAP)

    @property
    def respect_sentence_boundary(self) -> bool:
        """是否尊重句子边界（避免在句子中间切分）"""
        return self._loader.get_env_bool('RESPECT_SENTENCE_BOUNDARY', DEFAULT_RESPECT_SENTENCE_BOUNDARY)

    @property
    def enable_chinese_splitter(self) -> bool:
        """是否启用中文优化分块"""
        return self._loader.get_env_bool('ENABLE_CHINESE_SPLITTER', DEFAULT_ENABLE_CHINESE_SPLITTER)

    @property
    def separators(self) -> List[str]:
        """文档分隔符列表"""
        return DEFAULT_SEPARATORS

    # ========================================================================
    # 请求限制属性
    # ========================================================================

    @property
    def max_query_length(self) -> int:
        """最大查询长度（字符数）"""
        return self._loader.get_env_int('MAX_QUERY_LENGTH', DEFAULT_MAX_QUERY_LENGTH)

    @property
    def batch_size(self) -> int:
        """批处理大小"""
        return self._loader.get_env_int('BATCH_SIZE', DEFAULT_BATCH_SIZE)

    # ========================================================================
    # 日志配置属性
    # ========================================================================

    @property
    def log_level(self) -> str:
        """日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）"""
        return self._loader.get_env('LOG_LEVEL', DEFAULT_LOG_LEVEL)

    @property
    def log_file(self) -> str:
        """日志文件路径"""
        return self._loader.get_env('LOG_FILE', DEFAULT_LOG_FILE)

    @property
    def enable_query_logging(self) -> bool:
        """是否启用查询日志"""
        return self._loader.get_env_bool('ENABLE_QUERY_LOGGING', DEFAULT_ENABLE_QUERY_LOGGING)

    @property
    def enable_ingestion_logging(self) -> bool:
        """是否启用摄取日志"""
        return self._loader.get_env_bool('ENABLE_INGESTION_LOGGING', DEFAULT_ENABLE_INGESTION_LOGGING)

    @property
    def enable_console_logging(self) -> bool:
        """是否同时输出到控制台"""
        return self._loader.get_env_bool('ENABLE_CONSOLE_LOGGING', DEFAULT_ENABLE_CONSOLE_LOGGING)

    # ========================================================================
    # 增强日志配置属性（Enhanced LLM Logging）
    # ========================================================================

    @property
    def enable_llm_logging(self) -> bool:
        """是否启用 LLM 交互日志"""
        return self._loader.get_env_bool('ENABLE_LLM_LOGGING', DEFAULT_ENABLE_LLM_LOGGING)

    @property
    def enable_reflection_logging(self) -> bool:
        """是否启用 Agent 反思日志"""
        return self._loader.get_env_bool('ENABLE_REFLECTION_LOGGING', DEFAULT_ENABLE_REFLECTION_LOGGING)

    @property
    def enable_context_logging(self) -> bool:
        """是否启用对话上下文日志"""
        return self._loader.get_env_bool('ENABLE_CONTEXT_LOGGING', DEFAULT_ENABLE_CONTEXT_LOGGING)

    @property
    def llm_log_file(self) -> str:
        """LLM 交互日志文件路径"""
        return self._loader.get_env('LLM_LOG_FILE', DEFAULT_LLM_LOG_FILE)

    @property
    def reflection_log_file(self) -> str:
        """Agent 反思日志文件路径"""
        return self._loader.get_env('REFLECTION_LOG_FILE', DEFAULT_REFLECTION_LOG_FILE)

    @property
    def context_log_file(self) -> str:
        """对话上下文日志文件路径"""
        return self._loader.get_env('CONTEXT_LOG_FILE', DEFAULT_CONTEXT_LOG_FILE)

    @property
    def log_prompts(self) -> bool:
        """是否记录 LLM 提示词"""
        return self._loader.get_env_bool('LOG_PROMPTS', DEFAULT_LOG_PROMPTS)

    @property
    def log_responses(self) -> bool:
        """是否记录 LLM 响应"""
        return self._loader.get_env_bool('LOG_RESPONSES', DEFAULT_LOG_RESPONSES)

    @property
    def redact_sensitive(self) -> bool:
        """是否对敏感数据进行脱敏处理（已弃用，使用 redact_prompts 和 redact_responses）"""
        return self._loader.get_env_bool('REDACT_SENSITIVE', DEFAULT_REDACT_SENSITIVE)

    @property
    def redact_prompts(self) -> bool:
        """是否对 LLM 提示词进行脱敏处理"""
        return self._loader.get_env_bool('REDACT_PROMPTS', DEFAULT_REDACT_PROMPTS)

    @property
    def redact_responses(self) -> bool:
        """是否对 LLM 响应进行脱敏处理"""
        return self._loader.get_env_bool('REDACT_RESPONSES', DEFAULT_REDACT_RESPONSES)

    @property
    def max_log_entry_size(self) -> int:
        """单条日志条目的最大大小（字节）"""
        return self._loader.get_env_int('MAX_LOG_ENTRY_SIZE', DEFAULT_MAX_LOG_ENTRY_SIZE)

    @property
    def async_logging(self) -> bool:
        """是否启用异步日志写入"""
        return self._loader.get_env_bool('ASYNC_LOGGING', DEFAULT_ASYNC_LOGGING)

    @property
    def log_buffer_size(self) -> int:
        """日志缓冲区大小（条目数）"""
        return self._loader.get_env_int('LOG_BUFFER_SIZE', DEFAULT_LOG_BUFFER_SIZE)

    @property
    def enable_log_rotation(self) -> bool:
        """是否启用日志轮转"""
        return self._loader.get_env_bool('ENABLE_LOG_ROTATION', DEFAULT_ENABLE_LOG_ROTATION)

    @property
    def log_rotation_type(self) -> str:
        """日志轮转方式（size 或 time）"""
        return self._loader.get_env('LOG_ROTATION_TYPE', DEFAULT_LOG_ROTATION_TYPE)

    @property
    def log_max_bytes(self) -> int:
        """基于大小的轮转：单个日志文件的最大大小（字节）"""
        return self._loader.get_env_int('LOG_MAX_BYTES', DEFAULT_LOG_MAX_BYTES)

    @property
    def log_rotation_when(self) -> str:
        """基于时间的轮转：轮转间隔"""
        return self._loader.get_env('LOG_ROTATION_WHEN', DEFAULT_LOG_ROTATION_WHEN)

    @property
    def log_backup_count(self) -> int:
        """保留的轮转日志文件数量"""
        return self._loader.get_env_int('LOG_BACKUP_COUNT', DEFAULT_LOG_BACKUP_COUNT)

    @property
    def log_compress_rotated(self) -> bool:
        """是否自动压缩轮转的日志文件"""
        return self._loader.get_env_bool('LOG_COMPRESS_ROTATED', DEFAULT_LOG_COMPRESS_ROTATED)

    # ========================================================================
    # 统一流程日志配置属性（Unified Flow Logging）
    # ========================================================================

    @property
    def enable_flow_logging(self) -> bool:
        """是否启用统一流程日志"""
        return self._loader.get_env_bool('ENABLE_FLOW_LOGGING', DEFAULT_ENABLE_FLOW_LOGGING)

    @property
    def flow_log_file(self) -> str:
        """统一流程日志文件路径"""
        return self._loader.get_env('FLOW_LOG_FILE', DEFAULT_FLOW_LOG_FILE)

    @property
    def flow_detail_level(self) -> str:
        """流程日志详细级别（minimal, normal, verbose）"""
        level = self._loader.get_env('FLOW_DETAIL_LEVEL', DEFAULT_FLOW_DETAIL_LEVEL)
        # 验证详细级别是否有效
        valid_levels = ['minimal', 'normal', 'verbose']
        if level not in valid_levels:
            logger.warning(
                f"Invalid FLOW_DETAIL_LEVEL '{level}', using default '{DEFAULT_FLOW_DETAIL_LEVEL}'. "
                f"Valid options: {', '.join(valid_levels)}"
            )
            return DEFAULT_FLOW_DETAIL_LEVEL
        return level

    @property
    def flow_max_content_length(self) -> int:
        """流程日志内容最大长度（字符数）"""
        return self._loader.get_env_int('FLOW_MAX_CONTENT_LENGTH', DEFAULT_FLOW_MAX_CONTENT_LENGTH)

    @property
    def flow_async_logging(self) -> bool:
        """是否对流程日志启用异步写入"""
        return self._loader.get_env_bool('FLOW_ASYNC_LOGGING', DEFAULT_FLOW_ASYNC_LOGGING)

    @property
    def keep_separate_logs(self) -> bool:
        """是否保留独立的日志文件（向后兼容）"""
        return self._loader.get_env_bool('KEEP_SEPARATE_LOGS', DEFAULT_KEEP_SEPARATE_LOGS)

    @property
    def flow_rotation_enabled(self) -> bool:
        """是否启用流程日志轮转"""
        return self._loader.get_env_bool('FLOW_ROTATION_ENABLED', DEFAULT_FLOW_ROTATION_ENABLED)

    @property
    def flow_rotation_type(self) -> str:
        """流程日志轮转方式（size 或 time）"""
        rotation_type = self._loader.get_env('FLOW_ROTATION_TYPE', DEFAULT_FLOW_ROTATION_TYPE)
        # 验证轮转类型是否有效
        valid_types = ['size', 'time']
        if rotation_type not in valid_types:
            logger.warning(
                f"Invalid FLOW_ROTATION_TYPE '{rotation_type}', using default '{DEFAULT_FLOW_ROTATION_TYPE}'. "
                f"Valid options: {', '.join(valid_types)}"
            )
            return DEFAULT_FLOW_ROTATION_TYPE
        return rotation_type

    @property
    def flow_max_bytes(self) -> int:
        """基于大小的轮转：单个流程日志文件的最大大小（字节）"""
        return self._loader.get_env_int('FLOW_MAX_BYTES', DEFAULT_FLOW_MAX_BYTES)

    @property
    def flow_rotation_when(self) -> str:
        """基于时间的轮转：轮转间隔"""
        return self._loader.get_env('FLOW_ROTATION_WHEN', DEFAULT_FLOW_ROTATION_WHEN)

    @property
    def flow_backup_count(self) -> int:
        """保留的流程日志轮转文件数量"""
        return self._loader.get_env_int('FLOW_BACKUP_COUNT', DEFAULT_FLOW_BACKUP_COUNT)

    @property
    def flow_compress_rotated(self) -> bool:
        """是否自动压缩轮转的流程日志文件"""
        return self._loader.get_env_bool('FLOW_COMPRESS_ROTATED', DEFAULT_FLOW_COMPRESS_ROTATED)

    # ========================================================================
    # 验证方法
    # ========================================================================

    def validate(self) -> None:
        """
        验证所有配置项

        如果配置无效，抛出 ValueError 异常。

        异常:
            ValueError: 配置验证失败

        示例:
            >>> from rag5.config import settings
            >>> try:
            ...     settings.validate()
            ...     print("配置验证成功")
            ... except ValueError as e:
            ...     print(f"配置错误: {e}")
        """
        # 构建配置字典
        config = {
            'ollama_host': self.ollama_host,
            'llm_model': self.llm_model,
            'embed_model': self.embed_model,
            'llm_timeout': self.llm_timeout,
            'qdrant_url': self.qdrant_url,
            'collection_name': self.collection_name,
            'vector_dim': self.vector_dim,
            'top_k': self.top_k,
            'similarity_threshold': self.similarity_threshold,
            'enable_hybrid_search': self.enable_hybrid_search,
            'vector_search_weight': self.vector_search_weight,
            'keyword_search_weight': self.keyword_search_weight,
            'min_similarity_threshold': self.min_similarity_threshold,
            'target_results': self.target_results,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'respect_sentence_boundary': self.respect_sentence_boundary,
            'enable_chinese_splitter': self.enable_chinese_splitter,
            'max_query_length': self.max_query_length,
            'batch_size': self.batch_size,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'enable_query_logging': self.enable_query_logging,
            'enable_ingestion_logging': self.enable_ingestion_logging,
            'enable_console_logging': self.enable_console_logging,
            'enable_llm_logging': self.enable_llm_logging,
            'enable_reflection_logging': self.enable_reflection_logging,
            'enable_context_logging': self.enable_context_logging,
            'llm_log_file': self.llm_log_file,
            'reflection_log_file': self.reflection_log_file,
            'context_log_file': self.context_log_file,
            'log_prompts': self.log_prompts,
            'log_responses': self.log_responses,
            'redact_sensitive': self.redact_sensitive,
            'redact_prompts': self.redact_prompts,
            'redact_responses': self.redact_responses,
            'max_log_entry_size': self.max_log_entry_size,
            'async_logging': self.async_logging,
            'log_buffer_size': self.log_buffer_size,
            'enable_log_rotation': self.enable_log_rotation,
            'log_rotation_type': self.log_rotation_type,
            'log_max_bytes': self.log_max_bytes,
            'log_rotation_when': self.log_rotation_when,
            'log_backup_count': self.log_backup_count,
            'log_compress_rotated': self.log_compress_rotated,
            'enable_flow_logging': self.enable_flow_logging,
            'flow_log_file': self.flow_log_file,
            'flow_detail_level': self.flow_detail_level,
            'flow_max_content_length': self.flow_max_content_length,
            'flow_async_logging': self.flow_async_logging,
            'keep_separate_logs': self.keep_separate_logs,
        }

        # 执行验证
        errors = self._validator.validate_all(config)

        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            logger.error("\n请检查您的 .env 文件。示例配置:")
            logger.error("  OLLAMA_HOST=http://localhost:11434")
            logger.error("  LLM_MODEL=qwen2.5:7b")
            logger.error("  EMBED_MODEL=bge-m3")
            logger.error("  QDRANT_URL=http://localhost:6333")
            logger.error("  COLLECTION_NAME=knowledge_base")
            logger.error("  TOP_K=5")
            logger.error("  SIMILARITY_THRESHOLD=0.3")
            logger.error("  ENABLE_HYBRID_SEARCH=false")
            logger.error("  CHUNK_SIZE=500")
            logger.error("  CHUNK_OVERLAP=50")
            logger.error("  RESPECT_SENTENCE_BOUNDARY=true")
            logger.error("  ENABLE_CHINESE_SPLITTER=true")
            logger.error("  LOG_LEVEL=INFO")
            logger.error("  LOG_FILE=logs/rag_app.log")
            logger.error("  ENABLE_QUERY_LOGGING=true")
            raise ValueError(error_msg)

        self._validated = True
        logger.info("✓ 配置验证成功")

    def print_config(self) -> None:
        """
        打印当前配置

        示例:
            >>> from rag5.config import settings
            >>> settings.print_config()
        """
        logger.info("=" * 60)
        logger.info("当前配置:")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Ollama 配置:")
        logger.info(f"  - Host: {self.ollama_host}")
        logger.info(f"  - LLM Model: {self.llm_model}")
        logger.info(f"  - Embed Model: {self.embed_model}")
        logger.info(f"  - Timeout: {self.llm_timeout}s")
        logger.info("")
        logger.info("Qdrant 配置:")
        logger.info(f"  - URL: {self.qdrant_url}")
        logger.info(f"  - Collection: {self.collection_name}")
        logger.info(f"  - Vector Dim: {self.vector_dim}")
        logger.info("")
        logger.info("检索参数:")
        logger.info(f"  - Top K: {self.top_k}")
        logger.info(f"  - Similarity Threshold: {self.similarity_threshold}")
        logger.info(f"  - Enable Hybrid Search: {self.enable_hybrid_search}")
        logger.info(f"  - Vector Search Weight: {self.vector_search_weight}")
        logger.info(f"  - Keyword Search Weight: {self.keyword_search_weight}")
        logger.info(f"  - Min Similarity Threshold: {self.min_similarity_threshold}")
        logger.info(f"  - Target Results: {self.target_results}")
        logger.info("")
        logger.info("分块参数:")
        logger.info(f"  - Chunk Size: {self.chunk_size}")
        logger.info(f"  - Chunk Overlap: {self.chunk_overlap}")
        logger.info(f"  - Respect Sentence Boundary: {self.respect_sentence_boundary}")
        logger.info(f"  - Enable Chinese Splitter: {self.enable_chinese_splitter}")
        logger.info("")
        logger.info("请求限制:")
        logger.info(f"  - Max Query Length: {self.max_query_length}")
        logger.info(f"  - Batch Size: {self.batch_size}")
        logger.info("")
        logger.info("日志配置:")
        logger.info(f"  - Log Level: {self.log_level}")
        logger.info(f"  - Log File: {self.log_file}")
        logger.info(f"  - Enable Query Logging: {self.enable_query_logging}")
        logger.info(f"  - Enable Ingestion Logging: {self.enable_ingestion_logging}")
        logger.info(f"  - Enable Console Logging: {self.enable_console_logging}")
        logger.info("")
        logger.info("增强日志配置:")
        logger.info(f"  - Enable LLM Logging: {self.enable_llm_logging}")
        logger.info(f"  - Enable Reflection Logging: {self.enable_reflection_logging}")
        logger.info(f"  - Enable Context Logging: {self.enable_context_logging}")
        logger.info(f"  - LLM Log File: {self.llm_log_file}")
        logger.info(f"  - Reflection Log File: {self.reflection_log_file}")
        logger.info(f"  - Context Log File: {self.context_log_file}")
        logger.info(f"  - Log Prompts: {self.log_prompts}")
        logger.info(f"  - Log Responses: {self.log_responses}")
        logger.info(f"  - Redact Sensitive: {self.redact_sensitive} (deprecated)")
        logger.info(f"  - Redact Prompts: {self.redact_prompts}")
        logger.info(f"  - Redact Responses: {self.redact_responses}")
        logger.info(f"  - Max Log Entry Size: {self.max_log_entry_size}")
        logger.info(f"  - Async Logging: {self.async_logging}")
        logger.info(f"  - Log Buffer Size: {self.log_buffer_size}")
        logger.info(f"  - Enable Log Rotation: {self.enable_log_rotation}")
        logger.info(f"  - Log Rotation Type: {self.log_rotation_type}")
        logger.info(f"  - Log Max Bytes: {self.log_max_bytes}")
        logger.info(f"  - Log Rotation When: {self.log_rotation_when}")
        logger.info(f"  - Log Backup Count: {self.log_backup_count}")
        logger.info(f"  - Log Compress Rotated: {self.log_compress_rotated}")
        logger.info("")
        logger.info("统一流程日志配置:")
        logger.info(f"  - Enable Flow Logging: {self.enable_flow_logging}")
        logger.info(f"  - Flow Log File: {self.flow_log_file}")
        logger.info(f"  - Flow Detail Level: {self.flow_detail_level}")
        logger.info(f"  - Flow Max Content Length: {self.flow_max_content_length}")
        logger.info(f"  - Flow Async Logging: {self.flow_async_logging}")
        logger.info(f"  - Keep Separate Logs: {self.keep_separate_logs}")
        logger.info(f"  - Flow Rotation Enabled: {self.flow_rotation_enabled}")
        logger.info(f"  - Flow Rotation Type: {self.flow_rotation_type}")
        logger.info(f"  - Flow Max Bytes: {self.flow_max_bytes}")
        logger.info(f"  - Flow Rotation When: {self.flow_rotation_when}")
        logger.info(f"  - Flow Backup Count: {self.flow_backup_count}")
        logger.info(f"  - Flow Compress Rotated: {self.flow_compress_rotated}")
        logger.info("")
        logger.info("=" * 60)

    def to_dict(self) -> dict:
        """
        将配置转换为字典

        返回:
            配置字典
        """
        return {
            'ollama_host': self.ollama_host,
            'llm_model': self.llm_model,
            'embed_model': self.embed_model,
            'llm_timeout': self.llm_timeout,
            'qdrant_url': self.qdrant_url,
            'collection_name': self.collection_name,
            'vector_dim': self.vector_dim,
            'top_k': self.top_k,
            'similarity_threshold': self.similarity_threshold,
            'enable_hybrid_search': self.enable_hybrid_search,
            'vector_search_weight': self.vector_search_weight,
            'keyword_search_weight': self.keyword_search_weight,
            'min_similarity_threshold': self.min_similarity_threshold,
            'target_results': self.target_results,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'respect_sentence_boundary': self.respect_sentence_boundary,
            'enable_chinese_splitter': self.enable_chinese_splitter,
            'max_query_length': self.max_query_length,
            'batch_size': self.batch_size,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'enable_query_logging': self.enable_query_logging,
            'enable_ingestion_logging': self.enable_ingestion_logging,
            'enable_console_logging': self.enable_console_logging,
            'enable_llm_logging': self.enable_llm_logging,
            'enable_reflection_logging': self.enable_reflection_logging,
            'enable_context_logging': self.enable_context_logging,
            'llm_log_file': self.llm_log_file,
            'reflection_log_file': self.reflection_log_file,
            'context_log_file': self.context_log_file,
            'log_prompts': self.log_prompts,
            'log_responses': self.log_responses,
            'redact_sensitive': self.redact_sensitive,
            'redact_prompts': self.redact_prompts,
            'redact_responses': self.redact_responses,
            'max_log_entry_size': self.max_log_entry_size,
            'async_logging': self.async_logging,
            'log_buffer_size': self.log_buffer_size,
            'enable_log_rotation': self.enable_log_rotation,
            'log_rotation_type': self.log_rotation_type,
            'log_max_bytes': self.log_max_bytes,
            'log_rotation_when': self.log_rotation_when,
            'log_backup_count': self.log_backup_count,
            'log_compress_rotated': self.log_compress_rotated,
            'enable_flow_logging': self.enable_flow_logging,
            'flow_log_file': self.flow_log_file,
            'flow_detail_level': self.flow_detail_level,
            'flow_max_content_length': self.flow_max_content_length,
            'flow_async_logging': self.flow_async_logging,
            'keep_separate_logs': self.keep_separate_logs,
            'flow_rotation_enabled': self.flow_rotation_enabled,
            'flow_rotation_type': self.flow_rotation_type,
            'flow_max_bytes': self.flow_max_bytes,
            'flow_rotation_when': self.flow_rotation_when,
            'flow_backup_count': self.flow_backup_count,
            'flow_compress_rotated': self.flow_compress_rotated,
        }


# ============================================================================
# 全局配置单例
# ============================================================================

settings = Settings()
