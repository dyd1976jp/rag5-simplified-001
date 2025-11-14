# UI 配置使用指南

## 概述

`config.py` 模块提供了 Streamlit UI 应用的配置管理功能，支持通过环境变量自定义配置。

## 配置项说明

### API 配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `API_BASE_URL` | `API_BASE_URL` | `http://localhost:8000` | API 后端服务地址 |
| `API_TIMEOUT` | `API_TIMEOUT` | `30` | API 请求超时时间（秒） |

### UI 配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `PAGE_SIZE` | `PAGE_SIZE` | `9` | 知识库列表每页显示数量（3x3 网格） |
| `FILE_PAGE_SIZE` | `FILE_PAGE_SIZE` | `10` | 文件列表每页显示数量 |

### 缓存配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `CACHE_TTL` | `CACHE_TTL` | `60` | 缓存存活时间（秒） |

## 使用方式

### 方式 1：使用默认配置

```python
from rag5.interfaces.ui.config import config

# 直接访问配置
print(config.API_BASE_URL)  # http://localhost:8000
print(config.API_TIMEOUT)   # 30
print(config.PAGE_SIZE)     # 9
```

### 方式 2：使用类方法

```python
from rag5.interfaces.ui.config import UIConfig

# 使用类方法获取配置
api_url = UIConfig.get_api_base_url()
timeout = UIConfig.get_api_timeout()
page_size = UIConfig.get_page_size()
```

### 方式 3：查看所有配置

```python
from rag5.interfaces.ui.config import UIConfig

# 获取所有配置的字典
config_dict = UIConfig.display_config()
print(config_dict)
# {
#   "api": {
#     "base_url": "http://localhost:8000",
#     "timeout": 30
#   },
#   "ui": {
#     "page_size": 9,
#     "file_page_size": 10
#   },
#   "cache": {
#     "ttl": 60
#   }
# }
```

## 环境变量配置

### 方法 1：在 .env 文件中配置

创建或编辑 `.env` 文件：

```bash
# API 配置
API_BASE_URL=http://api.example.com:8000
API_TIMEOUT=60

# UI 配置
PAGE_SIZE=12
FILE_PAGE_SIZE=20

# 缓存配置
CACHE_TTL=120
```

### 方法 2：在命令行中设置

```bash
# Linux/Mac
export API_BASE_URL=http://api.example.com:8000
export API_TIMEOUT=60
streamlit run rag5/interfaces/ui/app.py

# Windows (CMD)
set API_BASE_URL=http://api.example.com:8000
set API_TIMEOUT=60
streamlit run rag5/interfaces/ui/app.py

# Windows (PowerShell)
$env:API_BASE_URL="http://api.example.com:8000"
$env:API_TIMEOUT="60"
streamlit run rag5/interfaces/ui/app.py
```

### 方法 3：在 Docker 中配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  ui:
    image: rag5-ui
    environment:
      - API_BASE_URL=http://api:8000
      - API_TIMEOUT=60
      - PAGE_SIZE=12
      - FILE_PAGE_SIZE=20
      - CACHE_TTL=120
    ports:
      - "8501:8501"
```

## 实际应用示例

### 在 API 客户端中使用

```python
from rag5.interfaces.ui.config import config
from rag5.interfaces.ui.pages.knowledge_base.api_client import KnowledgeBaseAPIClient

# 使用配置初始化 API 客户端
api_client = KnowledgeBaseAPIClient(
    base_url=config.API_BASE_URL,
    timeout=config.API_TIMEOUT
)
```

### 在分页组件中使用

```python
from rag5.interfaces.ui.config import config
import streamlit as st

# 使用配置设置分页大小
response = api_client.list_knowledge_bases(
    page=1,
    size=config.PAGE_SIZE  # 使用配置的页面大小
)
```

### 在缓存装饰器中使用

```python
from rag5.interfaces.ui.config import config
import streamlit as st

@st.cache_data(ttl=config.CACHE_TTL)  # 使用配置的 TTL
def get_knowledge_bases():
    # 获取知识库列表
    pass
```

## 配置验证

配置模块包含自动验证：

- ✅ 所有数值配置必须为正整数
- ✅ API_BASE_URL 必须是有效的字符串
- ✅ 超时时间建议在 1-300 秒之间
- ✅ 页面大小建议在 1-100 之间
- ✅ 缓存 TTL 建议在 1-3600 秒之间

## 测试

运行配置模块测试：

```bash
# 运行所有配置测试
pytest tests/test_interfaces/test_ui_config.py -v

# 运行特定测试
pytest tests/test_interfaces/test_ui_config.py::TestUIConfig::test_default_config_values -v
```

## 故障排除

### 问题 1：配置未生效

**原因**：配置在模块导入时读取，之后修改环境变量不会生效。

**解决方案**：
1. 在启动应用前设置环境变量
2. 或者重启应用以重新加载配置

### 问题 2：类型错误

**原因**：环境变量始终是字符串，需要转换为正确的类型。

**解决方案**：
配置模块已自动处理类型转换，确保数值配置使用 `int()` 转换。

### 问题 3：配置值不合理

**原因**：环境变量设置了无效值（如负数、零等）。

**解决方案**：
检查测试日志，确保配置值在合理范围内：
- API_TIMEOUT: 1-300 秒
- PAGE_SIZE: 1-100
- FILE_PAGE_SIZE: 1-100
- CACHE_TTL: 1-3600 秒

## 最佳实践

1. **开发环境**：使用默认配置或 `.env` 文件
2. **生产环境**：使用环境变量或容器编排工具配置
3. **配置管理**：将敏感配置（如 API 密钥）存储在安全的地方
4. **版本控制**：不要将 `.env` 文件提交到 Git
5. **文档更新**：修改配置时同步更新本文档

## 参考链接

- [Streamlit Configuration](https://docs.streamlit.io/library/advanced-features/configuration)
- [Python os.getenv](https://docs.python.org/3/library/os.html#os.getenv)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
