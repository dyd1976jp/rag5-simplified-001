"""
配置默认值定义模块

定义所有配置项的默认值。
"""

# ============================================================================
# Ollama 配置默认值
# ============================================================================

# Ollama 服务地址
DEFAULT_OLLAMA_HOST = "http://localhost:11434"

# 大语言模型名称
DEFAULT_LLM_MODEL = "qwen2.5:7b"

# 嵌入模型名称
DEFAULT_EMBED_MODEL = "bge-m3"

# LLM 请求超时时间（秒）
DEFAULT_LLM_TIMEOUT = 60


# ============================================================================
# Qdrant 配置默认值
# ============================================================================

# Qdrant 服务地址
DEFAULT_QDRANT_URL = "http://localhost:6333"

# 向量集合名称
DEFAULT_COLLECTION_NAME = "knowledge_base"

# 向量维度（bge-m3 模型生成 1024 维向量）
DEFAULT_VECTOR_DIM = 1024


# ============================================================================
# 检索参数默认值
# ============================================================================

# 检索返回的最大结果数
DEFAULT_TOP_K = 5

# 相似度阈值（0-1 之间）
DEFAULT_SIMILARITY_THRESHOLD = 0.5  # 降低阈值以提高召回率

# 启用混合搜索（向量搜索 + 关键词搜索）
DEFAULT_ENABLE_HYBRID_SEARCH = False

# 混合搜索中向量搜索的权重
DEFAULT_VECTOR_SEARCH_WEIGHT = 0.7

# 混合搜索中关键词搜索的权重
DEFAULT_KEYWORD_SEARCH_WEIGHT = 0.3

# 自适应搜索的最小阈值
DEFAULT_MIN_SIMILARITY_THRESHOLD = 0.1

# 自适应搜索的目标结果数
DEFAULT_TARGET_RESULTS = 3


# ============================================================================
# 文档分块参数默认值
# ============================================================================

# 文档分块大小（字符数）
DEFAULT_CHUNK_SIZE = 500

# 分块重叠大小（字符数）
DEFAULT_CHUNK_OVERLAP = 50

# 是否尊重句子边界（避免在句子中间切分）
DEFAULT_RESPECT_SENTENCE_BOUNDARY = True

# 是否启用中文优化分块
DEFAULT_ENABLE_CHINESE_SPLITTER = True

# 中英文分隔符
DEFAULT_SEPARATORS = [
    "\n\n",      # 段落分隔
    "\n",        # 行分隔
    "。",        # 中文句号
    "！",        # 中文感叹号
    "？",        # 中文问号
    "；",        # 中文分号
    "，",        # 中文逗号
    ". ",        # 英文句号
    "! ",        # 英文感叹号
    "? ",        # 英文问号
    "; ",        # 英文分号
    ", ",        # 英文逗号
    " ",         # 空格
    "",          # 字符级别
]


# ============================================================================
# 请求限制默认值
# ============================================================================

# 最大查询长度（字符数）
DEFAULT_MAX_QUERY_LENGTH = 2000

# 批处理大小
DEFAULT_BATCH_SIZE = 100


# ============================================================================
# 日志配置默认值
# ============================================================================

# 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
DEFAULT_LOG_LEVEL = "INFO"

# 日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 日志文件路径
DEFAULT_LOG_FILE = "logs/rag_app.log"

# 是否启用查询日志（记录所有查询详情）
DEFAULT_ENABLE_QUERY_LOGGING = True

# 是否启用摄取日志（记录文档摄取详情）
DEFAULT_ENABLE_INGESTION_LOGGING = True

# 是否同时输出到控制台
DEFAULT_ENABLE_CONSOLE_LOGGING = True


# ============================================================================
# 增强日志配置默认值（Enhanced LLM Logging）
# ============================================================================

# 是否启用 LLM 交互日志（记录所有 LLM 请求和响应）
DEFAULT_ENABLE_LLM_LOGGING = True

# 是否启用 Agent 反思日志（记录 Agent 推理过程）
DEFAULT_ENABLE_REFLECTION_LOGGING = True

# 是否启用对话上下文日志（记录对话历史变化）
DEFAULT_ENABLE_CONTEXT_LOGGING = True

# LLM 交互日志文件路径
DEFAULT_LLM_LOG_FILE = "logs/llm_interactions.log"

# Agent 反思日志文件路径
DEFAULT_REFLECTION_LOG_FILE = "logs/agent_reflections.log"

# 对话上下文日志文件路径
DEFAULT_CONTEXT_LOG_FILE = "logs/conversation_context.log"

# 是否记录 LLM 提示词（可能包含敏感信息）
DEFAULT_LOG_PROMPTS = True

# 是否记录 LLM 响应（可能包含敏感信息）
DEFAULT_LOG_RESPONSES = True

# 是否对敏感数据进行脱敏处理（已弃用，使用 REDACT_PROMPTS 和 REDACT_RESPONSES）
DEFAULT_REDACT_SENSITIVE = False

# 是否对 LLM 提示词进行脱敏处理
DEFAULT_REDACT_PROMPTS = False

# 是否对 LLM 响应进行脱敏处理
DEFAULT_REDACT_RESPONSES = False

# 单条日志条目的最大大小（字节）
DEFAULT_MAX_LOG_ENTRY_SIZE = 102400  # 100KB

# 是否启用异步日志写入（提高性能）
DEFAULT_ASYNC_LOGGING = True

# 日志缓冲区大小（条目数）
DEFAULT_LOG_BUFFER_SIZE = 100

# 是否启用日志轮转
DEFAULT_ENABLE_LOG_ROTATION = True

# 日志轮转方式（"size" 或 "time"）
DEFAULT_LOG_ROTATION_TYPE = "size"

# 基于大小的轮转：单个日志文件的最大大小（字节）
DEFAULT_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB

# 基于时间的轮转：轮转间隔（"midnight", "H", "D", "W0"-"W6"）
DEFAULT_LOG_ROTATION_WHEN = "midnight"

# 保留的轮转日志文件数量
DEFAULT_LOG_BACKUP_COUNT = 5

# 是否自动压缩轮转的日志文件
DEFAULT_LOG_COMPRESS_ROTATED = True


# ============================================================================
# 统一流程日志配置默认值（Unified Flow Logging）
# ============================================================================

# 是否启用统一流程日志（记录完整的查询处理流程）
DEFAULT_ENABLE_FLOW_LOGGING = True

# 统一流程日志文件路径
DEFAULT_FLOW_LOG_FILE = "logs/unified_flow.log"

# 流程日志详细级别（"minimal", "normal", "verbose"）
DEFAULT_FLOW_DETAIL_LEVEL = "normal"

# 流程日志内容最大长度（字符数，超过则截断）
DEFAULT_FLOW_MAX_CONTENT_LENGTH = 500

# 是否对流程日志启用异步写入
DEFAULT_FLOW_ASYNC_LOGGING = True

# 是否保留独立的日志文件（向后兼容）
DEFAULT_KEEP_SEPARATE_LOGS = True

# 流程日志轮转配置
# 是否启用流程日志轮转
DEFAULT_FLOW_ROTATION_ENABLED = True

# 流程日志轮转方式（"size" 或 "time"）
DEFAULT_FLOW_ROTATION_TYPE = "size"

# 基于大小的轮转：单个流程日志文件的最大大小（字节）
DEFAULT_FLOW_MAX_BYTES = 10 * 1024 * 1024  # 10MB

# 基于时间的轮转：轮转间隔（"midnight", "H", "D", "W0"-"W6"）
DEFAULT_FLOW_ROTATION_WHEN = "midnight"

# 保留的流程日志轮转文件数量
DEFAULT_FLOW_BACKUP_COUNT = 5

# 是否自动压缩轮转的流程日志文件
DEFAULT_FLOW_COMPRESS_ROTATED = True


# ============================================================================
# 知识库管理配置默认值 (Knowledge Base Management)
# ============================================================================

# 知识库数据库路径
DEFAULT_KB_DATABASE_PATH = "data/knowledge_bases.db"

# 文件存储路径
DEFAULT_FILE_STORAGE_PATH = "docs"

# 支持的文件格式列表
DEFAULT_SUPPORTED_FILE_FORMATS = [".txt", ".md", ".pdf", ".docx"]

# 文件大小限制（字节）- 默认 50MB
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024

# 默认分块配置
DEFAULT_KB_CHUNK_SIZE = 512
DEFAULT_KB_CHUNK_OVERLAP = 50
DEFAULT_KB_PARSER_TYPE = "sentence"
DEFAULT_KB_SEPARATOR = "\n\n"

# 默认检索配置
DEFAULT_KB_RETRIEVAL_MODE = "hybrid"
DEFAULT_KB_TOP_K = 5
DEFAULT_KB_SIMILARITY_THRESHOLD = 0.3
DEFAULT_KB_VECTOR_WEIGHT = 0.5
DEFAULT_KB_ENABLE_RERANK = False
DEFAULT_KB_RERANK_MODEL = ""

# 知识库名称长度限制
DEFAULT_KB_NAME_MIN_LENGTH = 2
DEFAULT_KB_NAME_MAX_LENGTH = 64

# 文件处理批次大小
DEFAULT_KB_FILE_BATCH_SIZE = 10

# 文件处理超时时间（秒）
DEFAULT_KB_FILE_PROCESSING_TIMEOUT = 300


# ============================================================================
# 配置项说明
# ============================================================================

CONFIG_DESCRIPTIONS = {
    # Ollama 配置
    "OLLAMA_HOST": "Ollama 服务地址，格式为 http://host:port",
    "LLM_MODEL": "大语言模型名称，如 qwen2.5:7b, llama2:7b 等",
    "EMBED_MODEL": "嵌入模型名称，如 bge-m3, nomic-embed-text 等",
    "LLM_TIMEOUT": "LLM 请求超时时间（秒）",

    # Qdrant 配置
    "QDRANT_URL": "Qdrant 向量数据库地址，格式为 http://host:port",
    "COLLECTION_NAME": "向量集合名称，用于存储文档向量",
    "VECTOR_DIM": "向量维度，必须与嵌入模型输出维度一致",

    # 检索参数
    "TOP_K": "检索返回的最大结果数，建议 3-10",
    "SIMILARITY_THRESHOLD": "相似度阈值，0-1 之间，建议 0.3-0.7",
    "ENABLE_HYBRID_SEARCH": "是否启用混合搜索（向量+关键词）",
    "VECTOR_SEARCH_WEIGHT": "混合搜索中向量搜索的权重，0-1 之间",
    "KEYWORD_SEARCH_WEIGHT": "混合搜索中关键词搜索的权重，0-1 之间",
    "MIN_SIMILARITY_THRESHOLD": "自适应搜索的最小阈值",
    "TARGET_RESULTS": "自适应搜索的目标结果数",

    # 分块参数
    "CHUNK_SIZE": "文档分块大小（字符数），建议 300-1000",
    "CHUNK_OVERLAP": "分块重叠大小（字符数），建议为 CHUNK_SIZE 的 10-20%",
    "RESPECT_SENTENCE_BOUNDARY": "是否尊重句子边界（避免在句子中间切分）",
    "ENABLE_CHINESE_SPLITTER": "是否启用中文优化分块",

    # 请求限制
    "MAX_QUERY_LENGTH": "最大查询长度（字符数），防止过长查询",
    "BATCH_SIZE": "批处理大小，用于批量向量化和上传",

    # 日志配置
    "LOG_LEVEL": "日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）",
    "LOG_FILE": "日志文件路径",
    "ENABLE_QUERY_LOGGING": "是否启用查询日志",
    "ENABLE_INGESTION_LOGGING": "是否启用摄取日志",
    "ENABLE_CONSOLE_LOGGING": "是否同时输出到控制台",

    # 增强日志配置
    "ENABLE_LLM_LOGGING": "是否启用 LLM 交互日志",
    "ENABLE_REFLECTION_LOGGING": "是否启用 Agent 反思日志",
    "ENABLE_CONTEXT_LOGGING": "是否启用对话上下文日志",
    "LLM_LOG_FILE": "LLM 交互日志文件路径",
    "REFLECTION_LOG_FILE": "Agent 反思日志文件路径",
    "CONTEXT_LOG_FILE": "对话上下文日志文件路径",
    "LOG_PROMPTS": "是否记录 LLM 提示词",
    "LOG_RESPONSES": "是否记录 LLM 响应",
    "REDACT_SENSITIVE": "是否对敏感数据进行脱敏处理（已弃用）",
    "REDACT_PROMPTS": "是否对 LLM 提示词进行脱敏处理",
    "REDACT_RESPONSES": "是否对 LLM 响应进行脱敏处理",
    "MAX_LOG_ENTRY_SIZE": "单条日志条目的最大大小（字节）",
    "ASYNC_LOGGING": "是否启用异步日志写入",
    "LOG_BUFFER_SIZE": "日志缓冲区大小（条目数）",
    "ENABLE_LOG_ROTATION": "是否启用日志轮转",
    "LOG_ROTATION_TYPE": "日志轮转方式（size 或 time）",
    "LOG_MAX_BYTES": "基于大小的轮转：单个日志文件的最大大小（字节）",
    "LOG_ROTATION_WHEN": "基于时间的轮转：轮转间隔",
    "LOG_BACKUP_COUNT": "保留的轮转日志文件数量",
    "LOG_COMPRESS_ROTATED": "是否自动压缩轮转的日志文件",

    # 统一流程日志配置
    "ENABLE_FLOW_LOGGING": "是否启用统一流程日志",
    "FLOW_LOG_FILE": "统一流程日志文件路径",
    "FLOW_DETAIL_LEVEL": "流程日志详细级别（minimal, normal, verbose）",
    "FLOW_MAX_CONTENT_LENGTH": "流程日志内容最大长度（字符数）",
    "FLOW_ASYNC_LOGGING": "是否对流程日志启用异步写入",
    "KEEP_SEPARATE_LOGS": "是否保留独立的日志文件（向后兼容）",
    "FLOW_ROTATION_ENABLED": "是否启用流程日志轮转",
    "FLOW_ROTATION_TYPE": "流程日志轮转方式（size 或 time）",
    "FLOW_MAX_BYTES": "基于大小的轮转：单个流程日志文件的最大大小（字节）",
    "FLOW_ROTATION_WHEN": "基于时间的轮转：轮转间隔",
    "FLOW_BACKUP_COUNT": "保留的流程日志轮转文件数量",
    "FLOW_COMPRESS_ROTATED": "是否自动压缩轮转的流程日志文件",

    # 知识库管理配置
    "KB_DATABASE_PATH": "知识库数据库文件路径",
    "FILE_STORAGE_PATH": "文件存储根目录路径",
    "SUPPORTED_FILE_FORMATS": "支持的文件格式列表",
    "MAX_FILE_SIZE": "单个文件的最大大小（字节）",
    "KB_CHUNK_SIZE": "知识库默认分块大小（字符数）",
    "KB_CHUNK_OVERLAP": "知识库默认分块重叠大小（字符数）",
    "KB_PARSER_TYPE": "知识库默认解析器类型（sentence, recursive, semantic）",
    "KB_SEPARATOR": "知识库默认分隔符",
    "KB_RETRIEVAL_MODE": "知识库默认检索模式（vector, fulltext, hybrid）",
    "KB_TOP_K": "知识库默认检索返回的最大结果数",
    "KB_SIMILARITY_THRESHOLD": "知识库默认相似度阈值（0-1）",
    "KB_VECTOR_WEIGHT": "知识库混合检索中向量搜索的权重（0-1）",
    "KB_ENABLE_RERANK": "知识库是否默认启用重排序",
    "KB_RERANK_MODEL": "知识库默认重排序模型名称",
    "KB_NAME_MIN_LENGTH": "知识库名称最小长度",
    "KB_NAME_MAX_LENGTH": "知识库名称最大长度",
    "KB_FILE_BATCH_SIZE": "文件处理批次大小",
    "KB_FILE_PROCESSING_TIMEOUT": "文件处理超时时间（秒）",
}


# ============================================================================
# 配置项分组
# ============================================================================

CONFIG_GROUPS = {
    "ollama": [
        "OLLAMA_HOST",
        "LLM_MODEL",
        "EMBED_MODEL",
        "LLM_TIMEOUT",
    ],
    "qdrant": [
        "QDRANT_URL",
        "COLLECTION_NAME",
        "VECTOR_DIM",
    ],
    "retrieval": [
        "TOP_K",
        "SIMILARITY_THRESHOLD",
        "ENABLE_HYBRID_SEARCH",
        "VECTOR_SEARCH_WEIGHT",
        "KEYWORD_SEARCH_WEIGHT",
        "MIN_SIMILARITY_THRESHOLD",
        "TARGET_RESULTS",
    ],
    "chunking": [
        "CHUNK_SIZE",
        "CHUNK_OVERLAP",
        "RESPECT_SENTENCE_BOUNDARY",
        "ENABLE_CHINESE_SPLITTER",
    ],
    "limits": [
        "MAX_QUERY_LENGTH",
        "BATCH_SIZE",
    ],
    "logging": [
        "LOG_LEVEL",
        "LOG_FILE",
        "ENABLE_QUERY_LOGGING",
        "ENABLE_INGESTION_LOGGING",
        "ENABLE_CONSOLE_LOGGING",
    ],
    "enhanced_logging": [
        "ENABLE_LLM_LOGGING",
        "ENABLE_REFLECTION_LOGGING",
        "ENABLE_CONTEXT_LOGGING",
        "LLM_LOG_FILE",
        "REFLECTION_LOG_FILE",
        "CONTEXT_LOG_FILE",
        "LOG_PROMPTS",
        "LOG_RESPONSES",
        "REDACT_SENSITIVE",
        "REDACT_PROMPTS",
        "REDACT_RESPONSES",
        "MAX_LOG_ENTRY_SIZE",
        "ASYNC_LOGGING",
        "LOG_BUFFER_SIZE",
        "ENABLE_LOG_ROTATION",
        "LOG_ROTATION_TYPE",
        "LOG_MAX_BYTES",
        "LOG_ROTATION_WHEN",
        "LOG_BACKUP_COUNT",
        "LOG_COMPRESS_ROTATED",
    ],
    "flow_logging": [
        "ENABLE_FLOW_LOGGING",
        "FLOW_LOG_FILE",
        "FLOW_DETAIL_LEVEL",
        "FLOW_MAX_CONTENT_LENGTH",
        "FLOW_ASYNC_LOGGING",
        "KEEP_SEPARATE_LOGS",
        "FLOW_ROTATION_ENABLED",
        "FLOW_ROTATION_TYPE",
        "FLOW_MAX_BYTES",
        "FLOW_ROTATION_WHEN",
        "FLOW_BACKUP_COUNT",
        "FLOW_COMPRESS_ROTATED",
    ],
    "knowledge_base": [
        "KB_DATABASE_PATH",
        "FILE_STORAGE_PATH",
        "SUPPORTED_FILE_FORMATS",
        "MAX_FILE_SIZE",
        "KB_CHUNK_SIZE",
        "KB_CHUNK_OVERLAP",
        "KB_PARSER_TYPE",
        "KB_SEPARATOR",
        "KB_RETRIEVAL_MODE",
        "KB_TOP_K",
        "KB_SIMILARITY_THRESHOLD",
        "KB_VECTOR_WEIGHT",
        "KB_ENABLE_RERANK",
        "KB_RERANK_MODEL",
        "KB_NAME_MIN_LENGTH",
        "KB_NAME_MAX_LENGTH",
        "KB_FILE_BATCH_SIZE",
        "KB_FILE_PROCESSING_TIMEOUT",
    ],
}
