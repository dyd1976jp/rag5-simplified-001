# 配置模块

配置模块负责加载、验证和管理 RAG5 系统的所有配置项。

## 功能概述

配置模块提供以下功能：

- **环境变量加载**: 从 `.env` 文件和系统环境变量加载配置
- **配置验证**: 验证配置值的有效性，包括 URL、数值范围等
- **默认值管理**: 为所有配置项提供合理的默认值
- **统一访问接口**: 通过 `settings` 单例访问所有配置

## 模块结构

```
config/
├── __init__.py          # 模块初始化，导出 settings
├── loader.py            # 配置加载器
├── validator.py         # 配置验证器
├── defaults.py          # 默认值定义
├── settings.py          # 配置访问接口
└── README.md            # 本文档
```

## 配置项说明

### Ollama 配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| ollama_host | OLLAMA_HOST | http://localhost:11434 | Ollama 服务地址 |
| llm_model | LLM_MODEL | qwen2.5:7b | 大语言模型名称 |
| embed_model | EMBED_MODEL | bge-m3 | 嵌入模型名称 |
| llm_timeout | LLM_TIMEOUT | 60 | LLM 请求超时时间（秒） |

### Qdrant 配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| qdrant_url | QDRANT_URL | http://localhost:6333 | Qdrant 服务地址 |
| collection_name | COLLECTION_NAME | knowledge_base | 向量集合名称 |
| vector_dim | VECTOR_DIM | 1024 | 向量维度 |

### 检索参数

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| top_k | TOP_K | 5 | 检索返回的最大结果数 |
| similarity_threshold | SIMILARITY_THRESHOLD | 0.7 | 相似度阈值（0-1） |

### 分块参数

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| chunk_size | CHUNK_SIZE | 500 | 文档分块大小（字符数） |
| chunk_overlap | CHUNK_OVERLAP | 50 | 分块重叠大小（字符数） |

### 请求限制

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| max_query_length | MAX_QUERY_LENGTH | 2000 | 最大查询长度（字符数） |
| batch_size | BATCH_SIZE | 100 | 批处理大小 |

## 使用示例

### 基本使用

```python
from rag5.config import settings

# 访问配置
print(f"Ollama Host: {settings.ollama_host}")
print(f"LLM Model: {settings.llm_model}")
print(f"Top K: {settings.top_k}")

# 验证配置
try:
    settings.validate()
    print("配置验证成功")
except ValueError as e:
    print(f"配置错误: {e}")

# 打印所有配置
settings.print_config()
```

### 配置文件示例

创建 `.env` 文件：

```bash
# Ollama 配置
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=qwen2.5:7b
EMBED_MODEL=bge-m3
LLM_TIMEOUT=60

# Qdrant 配置
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=knowledge_base
VECTOR_DIM=1024

# 检索参数
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# 分块参数
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# 请求限制
MAX_QUERY_LENGTH=2000
BATCH_SIZE=100
```

### 自定义配置加载

```python
from rag5.config.loader import ConfigLoader

# 创建加载器
loader = ConfigLoader()

# 加载自定义 .env 文件
loader.load_env_file('custom.env')

# 获取配置值
host = loader.get_env('OLLAMA_HOST', 'http://localhost:11434')
top_k = loader.get_env_int('TOP_K', 5)
threshold = loader.get_env_float('SIMILARITY_THRESHOLD', 0.7)
```

### 配置验证

```python
from rag5.config.validator import ConfigValidator

# 创建验证器
validator = ConfigValidator()

# 验证单个配置
is_valid = validator.validate_url('http://localhost:11434', 'OLLAMA_HOST')
is_valid = validator.validate_positive_int(5, 'TOP_K')
is_valid = validator.validate_range(0.7, 0.0, 1.0, 'SIMILARITY_THRESHOLD')

# 验证所有配置
config = {
    'ollama_host': 'http://localhost:11434',
    'llm_model': 'qwen2.5:7b',
    'top_k': 5,
    'similarity_threshold': 0.7,
    'chunk_size': 500,
    'chunk_overlap': 50,
}

errors = validator.validate_all(config)
if errors:
    print("配置错误:")
    for error in errors:
        print(f"  - {error}")
else:
    print("配置验证成功")
```

## 配置验证规则

配置模块会自动验证以下规则：

1. **URL 格式**: `OLLAMA_HOST` 和 `QDRANT_URL` 必须以 `http://` 或 `https://` 开头
2. **非空字符串**: `LLM_MODEL`、`EMBED_MODEL`、`COLLECTION_NAME` 不能为空
3. **正整数**: `TOP_K`、`CHUNK_SIZE`、`MAX_QUERY_LENGTH`、`LLM_TIMEOUT`、`VECTOR_DIM`、`BATCH_SIZE` 必须大于 0
4. **非负整数**: `CHUNK_OVERLAP` 必须大于等于 0
5. **范围验证**: `SIMILARITY_THRESHOLD` 必须在 0 到 1 之间
6. **比较验证**: `CHUNK_OVERLAP` 必须小于 `CHUNK_SIZE`

## 错误处理

配置模块采用以下错误处理策略：

1. **缺失配置**: 使用默认值，记录警告日志
2. **无效格式**: 使用默认值，记录警告日志
3. **验证失败**: 抛出 `ValueError` 异常，包含详细错误信息

## 扩展配置

如需添加新的配置项：

1. 在 `defaults.py` 中定义默认值
2. 在 `settings.py` 中添加属性
3. 在 `validator.py` 的 `validate_all()` 方法中添加验证逻辑
4. 更新本文档的配置项说明

### 示例：添加新配置项

```python
# 1. 在 defaults.py 中添加
DEFAULT_NEW_PARAM = 100

# 2. 在 settings.py 中添加属性
@property
def new_param(self) -> int:
    """新参数说明"""
    return self._loader.get_env_int('NEW_PARAM', DEFAULT_NEW_PARAM)

# 3. 在 validator.py 的 validate_all() 中添加
if 'new_param' in config:
    self.validate_positive_int(config['new_param'], 'NEW_PARAM')

# 4. 在配置字典中添加（settings.py 的 validate() 和 to_dict() 方法）
config = {
    # ... 其他配置
    'new_param': self.new_param,
}
```

## 最佳实践

1. **使用 .env 文件**: 将配置放在 `.env` 文件中，不要硬编码
2. **验证配置**: 在应用启动时调用 `settings.validate()` 验证配置
3. **使用默认值**: 为所有配置项提供合理的默认值
4. **记录日志**: 配置加载和验证过程会自动记录日志
5. **环境隔离**: 不同环境使用不同的 `.env` 文件（如 `.env.dev`、`.env.prod`）

## 常见问题

### Q: 如何在不同环境使用不同配置？

A: 创建不同的 `.env` 文件（如 `.env.dev`、`.env.prod`），然后在初始化时指定：

```python
from rag5.config.settings import Settings

# 开发环境
dev_settings = Settings(env_file='.env.dev')

# 生产环境
prod_settings = Settings(env_file='.env.prod')
```

### Q: 配置验证失败怎么办？

A: 检查错误消息，修正 `.env` 文件中的配置值。常见错误包括：
- URL 缺少协议前缀（http:// 或 https://）
- 数值超出有效范围
- 必填配置项为空

### Q: 如何覆盖默认配置？

A: 在 `.env` 文件中设置相应的环境变量即可覆盖默认值。

### Q: 配置是否支持热更新？

A: 当前版本不支持热更新。修改配置后需要重启应用。

## 相关文档

- [开发指南](../../docs/development.md)
- [API 参考](../../docs/api_reference.md)
- [迁移指南](../../docs/migration_guide.md)
