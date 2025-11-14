# 接口模块

接口模块提供了与 RAG5 系统交互的用户界面，包括 REST API 和 Web UI 两种方式。

## 模块结构

```
interfaces/
├── __init__.py          # 模块导出
├── README.md            # 本文档
├── api/                 # REST API 子模块
│   ├── __init__.py
│   ├── app.py          # FastAPI 应用
│   ├── models.py       # 请求/响应模型
│   ├── routes.py       # 路由定义
│   └── handlers.py     # 请求处理器
└── ui/                  # Web UI 子模块
    ├── __init__.py
    ├── app.py          # Streamlit 应用
    ├── state.py        # 会话状态管理
    └── components.py   # UI 组件
```

## API 子模块

### 功能说明

REST API 子模块基于 FastAPI 框架，提供 HTTP 接口用于与 RAG 系统交互。主要特性：

- **请求验证**: 使用 Pydantic 模型自动验证输入
- **错误处理**: 统一的错误处理和响应格式
- **健康检查**: 监控系统组件状态
- **API 文档**: 自动生成的交互式文档（Swagger UI）

### API 端点

#### 1. POST /api/v1/chat

与 RAG 代理进行对话。

**请求体**:
```json
{
  "query": "什么是 RAG？",
  "history": [
    {
      "role": "user",
      "content": "你好"
    },
    {
      "role": "assistant",
      "content": "你好！有什么可以帮助你的？"
    }
  ]
}
```

**响应**:
```json
{
  "answer": "RAG（检索增强生成）是一种结合了信息检索和文本生成的技术..."
}
```

**错误响应**:
- `400 Bad Request`: 请求参数无效
- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: 服务不可用（Ollama 或 Qdrant 未运行）
- `504 Gateway Timeout`: 请求超时

#### 2. GET /api/v1/health

检查系统健康状态。

**响应**:
```json
{
  "status": "ok",
  "components": {
    "ollama": "ok",
    "qdrant": "ok"
  }
}
```

状态值：
- `ok`: 所有组件正常
- `degraded`: 部分组件异常
- `error`: 系统错误

#### 3. GET /

获取 API 信息。

**响应**:
```json
{
  "name": "Simple RAG API",
  "version": "2.0.0",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

### 使用示例

#### Python 客户端

```python
import requests

# 发送聊天请求
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "query": "什么是 RAG？",
        "history": []
    }
)

if response.status_code == 200:
    answer = response.json()["answer"]
    print(answer)
else:
    print(f"错误: {response.json()['detail']}")

# 检查健康状态
health = requests.get("http://localhost:8000/api/v1/health")
print(health.json())
```

#### cURL

```bash
# 聊天请求
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是 RAG？",
    "history": []
  }'

# 健康检查
curl "http://localhost:8000/api/v1/health"
```

#### JavaScript/Fetch

```javascript
// 发送聊天请求
const response = await fetch('http://localhost:8000/api/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '什么是 RAG？',
    history: []
  })
});

const data = await response.json();
console.log(data.answer);
```

### 启动 API 服务

```bash
# 方法 1: 直接运行模块
python -m rag5.interfaces.api.app

# 方法 2: 使用 uvicorn
uvicorn rag5.interfaces.api.app:app --host localhost --port 8000

# 方法 3: 使用脚本（如果已创建）
python scripts/run_api.py
```

访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## UI 子模块

### 功能说明

Web UI 子模块基于 Streamlit 框架，提供友好的聊天界面。主要特性：

- **实时对话**: 流畅的聊天体验
- **历史管理**: 自动保存和显示对话历史
- **状态监控**: 实时显示系统组件状态
- **错误处理**: 友好的错误提示
- **响应式设计**: 适配不同屏幕尺寸

### UI 功能

#### 主界面

- **消息显示**: 显示用户和助手的对话历史
- **输入框**: 输入问题并发送
- **加载指示**: 显示"思考中..."状态
- **错误提示**: 显示错误和警告信息

#### 侧边栏

- **设置**: 清空对话按钮
- **系统信息**: 显示对话轮数和消息总数
- **限制信息**: 显示最大问题长度等限制
- **系统状态**: 实时显示 Ollama 和 Qdrant 的运行状态

### 使用示例

#### 启动 UI 服务

```bash
# 方法 1: 直接运行模块
streamlit run rag5/interfaces/ui/app.py

# 方法 2: 使用 Python 模块
python -m streamlit run rag5/interfaces/ui/app.py

# 方法 3: 使用脚本（如果已创建）
python scripts/run_ui.py
```

访问 UI：http://localhost:8501

#### 自定义会话状态

```python
from rag5.interfaces.ui.state import SessionState

# 初始化状态
SessionState.initialize()

# 添加消息
SessionState.add_message("user", "你好")
SessionState.add_message("assistant", "你好！有什么可以帮助你的？")

# 获取消息
messages = SessionState.get_messages()
print(f"共有 {len(messages)} 条消息")

# 获取对话轮数
turn_count = SessionState.get_turn_count()
print(f"进行了 {turn_count} 轮对话")

# 清空消息
SessionState.clear_messages()
```

#### 自定义 UI 组件

```python
import streamlit as st
from rag5.interfaces.ui.components import (
    render_page_header,
    render_chat_history,
    render_sidebar
)

# 渲染页面标题
render_page_header()

# 渲染对话历史
messages = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！"}
]
render_chat_history(messages)

# 渲染侧边栏
if render_sidebar(turn_count=1, message_count=2):
    st.write("用户点击了清空对话")
```

## 架构设计

### API 架构

```
请求 → 路由 (routes.py) → 处理器 (handlers.py) → 代理 (agent) → 响应
                ↓
            模型验证 (models.py)
```

**职责分离**:
- `models.py`: 定义数据模型和验证规则
- `routes.py`: 定义 HTTP 路由和端点
- `handlers.py`: 实现业务逻辑和错误处理
- `app.py`: 创建和配置 FastAPI 应用

### UI 架构

```
用户输入 → 状态管理 (state.py) → 代理 (agent) → 组件渲染 (components.py)
```

**职责分离**:
- `state.py`: 管理 Streamlit 会话状态
- `components.py`: 定义可重用的 UI 组件
- `app.py`: 组装组件，实现主应用逻辑

## 配置

### API 配置

API 使用 `rag5.config.settings` 中的配置：

```python
from rag5.config.settings import settings

# Ollama 配置
ollama_host = settings.ollama_host
llm_model = settings.llm_model

# Qdrant 配置
qdrant_url = settings.qdrant_url
collection_name = settings.collection_name

# 其他配置
max_query_length = settings.max_query_length
```

### UI 配置

UI 同样使用统一的配置系统：

```python
from rag5.config.settings import settings

# 在 UI 中使用配置
st.text(f"最大问题长度: {settings.max_query_length}")
```

## 错误处理

### API 错误处理

API 使用标准的 HTTP 状态码和错误响应：

```python
# 400 Bad Request - 输入验证失败
{
  "detail": "Query cannot be empty"
}

# 500 Internal Server Error - 服务器错误
{
  "detail": "Internal server error: ..."
}

# 503 Service Unavailable - 服务不可用
{
  "detail": "Service unavailable: Ollama connection failed"
}
```

### UI 错误处理

UI 使用友好的错误提示：

```python
# 连接错误
st.error("连接错误：无法连接到 Ollama 服务。请确保服务正在运行。")

# 配置错误
st.warning("配置错误：请检查环境变量设置。")

# 一般错误
st.error("抱歉，处理您的问题时出现错误。")
```

## 扩展指南

### 添加新的 API 端点

1. 在 `models.py` 中定义请求/响应模型：

```python
class NewRequest(BaseModel):
    param: str

class NewResponse(BaseModel):
    result: str
```

2. 在 `handlers.py` 中实现处理器：

```python
class NewHandler:
    @staticmethod
    async def handle_new(request: NewRequest) -> NewResponse:
        # 实现业务逻辑
        return NewResponse(result="...")
```

3. 在 `routes.py` 中添加路由：

```python
@router.post("/new")
async def new_endpoint(request: NewRequest) -> NewResponse:
    return await NewHandler.handle_new(request)
```

### 添加新的 UI 组件

1. 在 `components.py` 中定义组件：

```python
def render_new_component(data):
    """渲染新组件"""
    st.subheader("新组件")
    st.write(data)
```

2. 在 `app.py` 中使用组件：

```python
from .components import render_new_component

def main():
    # ...
    render_new_component(data)
```

### 自定义会话状态

扩展 `SessionState` 类以添加新的状态管理：

```python
class SessionState:
    # 现有方法...
    
    @staticmethod
    def get_custom_state():
        """获取自定义状态"""
        if "custom" not in st.session_state:
            st.session_state.custom = {}
        return st.session_state.custom
```

## 测试

### API 测试

```python
from fastapi.testclient import TestClient
from rag5.interfaces.api import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post(
        "/api/v1/chat",
        json={"query": "测试问题", "history": []}
    )
    assert response.status_code == 200
    assert "answer" in response.json()

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()
```

### UI 测试

UI 测试通常需要手动测试或使用 Selenium 等工具：

```python
# 手动测试清单
# 1. 启动 UI
# 2. 输入问题并提交
# 3. 验证响应显示正确
# 4. 点击清空对话按钮
# 5. 验证历史已清空
# 6. 检查侧边栏状态显示
```

## 部署建议

### API 部署

使用 Gunicorn + Uvicorn 部署：

```bash
gunicorn rag5.interfaces.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### UI 部署

使用 Streamlit 的部署选项：

```bash
# 本地部署
streamlit run rag5/interfaces/ui/app.py --server.port 8501

# 使用 Docker
# 在 Dockerfile 中：
CMD ["streamlit", "run", "rag5/interfaces/ui/app.py"]
```

## 常见问题

### Q: API 返回 503 错误？

A: 检查 Ollama 和 Qdrant 服务是否正在运行：
```bash
# 检查 Ollama
curl http://localhost:11434/api/tags

# 检查 Qdrant
curl http://localhost:6333/collections
```

### Q: UI 显示连接错误？

A: 确保配置正确且服务可访问：
```python
from rag5.config.settings import settings
print(settings.ollama_host)
print(settings.qdrant_url)
```

### Q: 如何启用 CORS？

A: 在 `app.py` 中配置 CORS 中间件：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 指定允许的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Q: 如何自定义 UI 样式？

A: 使用 Streamlit 的配置文件 `.streamlit/config.toml`：
```toml
[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## 总结

接口模块提供了两种与 RAG5 系统交互的方式：

1. **REST API**: 适合程序化访问和集成到其他系统
2. **Web UI**: 适合人工交互和演示

两种接口都遵循模块化设计原则，职责清晰，易于扩展和维护。
