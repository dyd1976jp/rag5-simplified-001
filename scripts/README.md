# RAG5 脚本使用指南

本目录包含 RAG5 系统的所有命令行工具和启动脚本。

## 脚本列表

### 1. setup_models.sh - 模型安装脚本
下载和安装 Ollama 模型。

**用法**:
```bash
./scripts/setup_models.sh
```

**功能**:
- 检查 Ollama 是否已安装
- 检查 Ollama 服务是否运行
- 下载 LLM 模型（qwen2.5:7b）
- 下载嵌入模型（bge-m3）

### 2. ingest.py - 数据摄取脚本
将文档加载到向量数据库。

**基本用法**:
```bash
python scripts/ingest.py <目录路径>
```

**示例**:
```bash
# 摄取 docs 目录
python scripts/ingest.py docs

# 使用详细日志
python scripts/ingest.py docs --verbose

# 自定义批处理大小
python scripts/ingest.py docs --batch-size 50

# 打印配置
python scripts/ingest.py docs --print-config
```

**支持的文件格式**:
- 文本文件 (.txt)
- PDF 文件 (.pdf)
- Markdown 文件 (.md)

### 3. run_api.py - API 服务启动脚本
启动 REST API 服务。

**基本用法**:
```bash
python scripts/run_api.py
```

**示例**:
```bash
# 默认启动（localhost:8000）
python scripts/run_api.py

# 指定主机和端口
python scripts/run_api.py --host 0.0.0.0 --port 8080

# 开发模式（自动重载）
python scripts/run_api.py --reload

# 生产模式（多进程）
python scripts/run_api.py --workers 4

# 使用详细日志
python scripts/run_api.py --log-level debug
```

**访问地址**:
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/v1/health

### 4. run_ui.py - UI 服务启动脚本
启动 Streamlit Web UI。

**基本用法**:
```bash
python scripts/run_ui.py
```

**示例**:
```bash
# 默认启动（localhost:8501）
python scripts/run_ui.py

# 指定端口
python scripts/run_ui.py --port 8502

# 使用深色主题
python scripts/run_ui.py --theme dark

# 自动打开浏览器
python scripts/run_ui.py --browser

# 允许外部访问
python scripts/run_ui.py --server-address 0.0.0.0
```

**访问地址**:
- 默认地址: http://localhost:8501

### 5. debug_retrieval.py - 检索调试脚本
全面的检索系统诊断工具，用于调试和验证检索功能。

**基本用法**:
```bash
python scripts/debug_retrieval.py
```

**示例**:
```bash
# 运行完整诊断（使用默认查询）
python scripts/debug_retrieval.py

# 使用自定义查询
python scripts/debug_retrieval.py --query "李小勇是谁"

# 使用自定义关键词
python scripts/debug_retrieval.py --keyword "李小勇"

# 指定集合名称
python scripts/debug_retrieval.py --collection my_collection

# 组合使用
python scripts/debug_retrieval.py \
  --query "于朦朧是怎么死的" \
  --keyword "于朦朧" \
  --collection knowledge_base
```

**功能**:
- 检查数据库状态（集合统计、样本数据）
- 关键词搜索测试（验证文档是否已索引）
- 嵌入模型验证（测试模型是否正常工作）
- 查询测试（使用不同阈值测试查询效果）
- 问题诊断（自动检测常见问题）
- 生成诊断报告（保存到 logs/ 目录）

**详细文档**: 参见 [DEBUG_RETRIEVAL_README.md](DEBUG_RETRIEVAL_README.md)

### 6. compress_logs.py - 日志压缩脚本
手动压缩旧日志文件以节省磁盘空间。

**基本用法**:
```bash
python scripts/compress_logs.py
```

**示例**:
```bash
# 压缩 7 天前的日志文件
python scripts/compress_logs.py

# 压缩 30 天前的日志文件
python scripts/compress_logs.py --days 30

# 预览将要压缩的文件（不实际压缩）
python scripts/compress_logs.py --dry-run

# 压缩指定目录的日志
python scripts/compress_logs.py --log-dir /path/to/logs

# 保留原始文件（不删除）
python scripts/compress_logs.py --keep-original

# 详细输出
python scripts/compress_logs.py --verbose
```

**功能**:
- 查找指定天数之前的日志文件
- 使用 gzip 压缩日志文件
- 显示压缩统计信息（文件数、节省空间）
- 支持预览模式（dry-run）
- 可配置是否保留原始文件

**定时任务**:
可以使用 cron 定期运行压缩脚本：
```bash
# 每天凌晨 2 点压缩 7 天前的日志
0 2 * * * cd /path/to/rag5-simplified && python scripts/compress_logs.py --days 7

# 每周日凌晨 3 点压缩 30 天前的日志
0 3 * * 0 cd /path/to/rag5-simplified && python scripts/compress_logs.py --days 30
```

**详细文档**: 参见 [../docs/log_rotation.md](../docs/log_rotation.md)

### 7. migrate_kb.py - 知识库数据库迁移工具
初始化知识库数据库并创建默认知识库。

**基本用法**:
```bash
python -m scripts.migrate_kb [options]
```

**示例**:
```bash
# 基本迁移（创建表和索引）
python -m scripts.migrate_kb

# 迁移并创建默认知识库
python -m scripts.migrate_kb --create-default

# 仅验证数据库结构
python -m scripts.migrate_kb --verify
```

**功能**:
- 创建知识库数据库表和索引
- 验证数据库结构
- 创建默认知识库（用于向后兼容）
- 显示迁移统计信息

**详细文档**: 参见 [../docs/KB_MIGRATION.md](../docs/KB_MIGRATION.md)

### 8. analyze_flow_logs.py - 流程日志分析工具
分析统一流程日志的命令行工具。

**基本用法**:
```bash
python scripts/analyze_flow_logs.py --log-file <path> [options]
```

**示例**:
```bash
# 显示时间统计
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --stats

# 按会话过滤
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --session abc-123-def

# 查找错误
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --errors

# 查找慢操作（超过 5 秒）
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --slow 5.0

# 导出为 JSON
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --export-json output.json

# 导出为 CSV
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --export-csv output.csv

# 组合多个命令
python scripts/analyze_flow_logs.py --log-file logs/unified_flow.log --stats --errors --slow 3.0
```

**功能**:
- 按会话 ID 过滤日志条目
- 计算时间统计（平均、最小、最大、P95）
- 查找所有错误
- 识别慢操作
- 导出为 JSON 或 CSV 格式
- 格式化的终端输出

**详细文档**: 参见 [CLI_USAGE.md](CLI_USAGE.md) 和 [../docs/flow_log_analyzer.md](../docs/flow_log_analyzer.md)

## 完整工作流程

### 首次设置

1. **安装依赖**:
```bash
pip install -r requirements.txt
```

2. **配置环境变量**:
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. **启动 Qdrant**:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

4. **安装模型**:
```bash
./scripts/setup_models.sh
```

5. **摄取文档**:
```bash
python scripts/ingest.py docs
```

### 日常使用

**启动 API 服务**:
```bash
python scripts/run_api.py
```

**启动 UI 服务**（在另一个终端）:
```bash
python scripts/run_ui.py
```

## 常用参数

### 所有脚本通用参数

- `--help`: 显示帮助信息
- `--print-config`: 打印当前配置
- `--check-only`: 仅检查服务状态
- `--no-check`: 跳过服务检查
- `--log-level`: 设置日志级别（debug/info/warning/error）

### ingest.py 特有参数

- `--verbose`: 启用详细日志
- `--batch-size`: 批处理大小
- `--chunk-size`: 文档分块大小
- `--chunk-overlap`: 分块重叠大小
- `--validate-only`: 仅验证配置

### run_api.py 特有参数

- `--host`: 服务器主机地址
- `--port`: 服务器端口
- `--reload`: 启用自动重载（开发模式）
- `--workers`: 工作进程数

### run_ui.py 特有参数

- `--port`: 服务器端口
- `--server-address`: 服务器地址
- `--theme`: UI 主题（light/dark）
- `--browser`: 自动打开浏览器

## 故障排除

### 问题：无法连接到 Ollama

**解决方案**:
```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 如果未运行，启动 Ollama
ollama serve
```

### 问题：无法连接到 Qdrant

**解决方案**:
```bash
# 检查 Qdrant 是否运行
curl http://localhost:6333/collections

# 如果未运行，启动 Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### 问题：模型未找到

**解决方案**:
```bash
# 重新运行模型安装脚本
./scripts/setup_models.sh

# 或手动拉取模型
ollama pull qwen2.5:7b
ollama pull bge-m3
```

### 问题：配置验证失败

**解决方案**:
```bash
# 检查 .env 文件是否存在
ls -la .env

# 如果不存在，从示例创建
cp .env.example .env

# 验证配置
python scripts/ingest.py docs --validate-only
```

## 开发提示

### 开发模式

在开发时，使用以下命令启用自动重载和详细日志：

```bash
# API 开发模式
python scripts/run_api.py --reload --log-level debug

# UI 开发模式
python scripts/run_ui.py --log-level debug
```

### 生产部署

在生产环境中，使用以下配置：

```bash
# API 生产模式
python scripts/run_api.py \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info

# UI 生产模式
python scripts/run_ui.py \
  --server-address 0.0.0.0 \
  --port 8501 \
  --theme light
```

## 更多信息

- 查看各脚本的详细帮助: `python scripts/<script>.py --help`
- 查看配置选项: `python scripts/<script>.py --print-config`
- 查看项目文档: `../README.md`
