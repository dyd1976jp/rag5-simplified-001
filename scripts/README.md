# Scripts 目录说明

本目录包含 RAG5 系统的各种工具脚本，用于服务启动、数据处理、调试和测试等任务。

## 服务启动脚本

### `run_ui.py`
启动 Streamlit Web UI 界面。

**用途：** 提供用户友好的 Web 界面，用于知识库管理和智能问答
**使用方法：**
```bash
python scripts/run_ui.py
# 或安装后直接使用
rag5-ui
```
**默认地址：** http://localhost:8501

### `run_api.py`
启动 FastAPI REST API 服务。

**用途：** 提供 RESTful API 接口，供其他应用程序集成使用
**使用方法：**
```bash
python scripts/run_api.py
# 或安装后直接使用
rag5-api
```
**默认地址：** http://localhost:8000
**API 文档：** http://localhost:8000/docs

## 数据处理脚本

### `ingest.py`
文档导入和向量化工具。

**用途：** 批量导入文档到知识库，自动完成文本提取、分块、向量化和存储
**使用方法：**
```bash
# 导入指定目录的文档
python scripts/ingest.py /path/to/docs

# 指定知识库 ID
python scripts/ingest.py /path/to/docs --kb-id <knowledge_base_id>

# 安装后使用
rag5-ingest /path/to/docs
```
**支持格式：** PDF, TXT, MD, DOCX

### `kb_manager.py`
知识库管理工具。

**用途：** 创建、查看、更新、删除知识库及其配置
**使用方法：**
```bash
# 列出所有知识库
python scripts/kb_manager.py list

# 创建新知识库
python scripts/kb_manager.py create --name "我的知识库" --description "描述信息"

# 查看知识库详情
python scripts/kb_manager.py info --id <kb_id>

# 更新知识库配置
python scripts/kb_manager.py update --id <kb_id> --chunk-size 600

# 删除知识库
python scripts/kb_manager.py delete --id <kb_id>

# 上传文件到知识库
python scripts/kb_manager.py upload --id <kb_id> --file /path/to/file.pdf
```

### `migrate_kb.py`
知识库数据迁移工具。

**用途：** 在系统升级时迁移知识库数据结构
**使用方法：**
```bash
python scripts/migrate_kb.py
```
**注意：** 通常在系统升级后自动或手动执行一次

## 调试和诊断脚本

### `debug_retrieval.py`
检索功能调试工具。

**用途：** 诊断向量检索问题，查看检索结果和相似度分数
**使用方法：**
```bash
# 交互式调试
python scripts/debug_retrieval.py

# 使用自定义查询
python scripts/debug_retrieval.py --query "你的问题"

# 搜索特定关键词
python scripts/debug_retrieval.py --keyword "关键词"

# 指定知识库
python scripts/debug_retrieval.py --kb-id <knowledge_base_id>

# 调整返回数量和相似度阈值
python scripts/debug_retrieval.py --top-k 10 --threshold 0.5
```
**输出内容：**
- 检索到的文档片段
- 相似度分数
- 文档元数据
- 性能统计

### `analyze_flow_logs.py`
流程日志分析工具。

**用途：** 分析统一流程日志，提供查询性能和行为分析
**使用方法：**
```bash
# 显示统计信息
python scripts/analyze_flow_logs.py --stats

# 分析特定会话
python scripts/analyze_flow_logs.py --session <session-id>

# 查看最近的查询
python scripts/analyze_flow_logs.py --recent 10

# 导出分析报告
python scripts/analyze_flow_logs.py --export report.json
```

### `compress_logs.py`
日志压缩和归档工具。

**用途：** 压缩旧日志文件以节省磁盘空间
**使用方法：**
```bash
# 压缩超过 7 天的日志
python scripts/compress_logs.py

# 指定保留天数
python scripts/compress_logs.py --days 30

# 删除超过 90 天的压缩日志
python scripts/compress_logs.py --cleanup 90
```

## 测试和验证脚本

### `test_e2e.py`
端到端测试工具。

**用途：** 执行完整的用户场景测试，验证系统各组件协同工作
**使用方法：**
```bash
# 运行所有 E2E 测试
python scripts/test_e2e.py

# 运行特定测试场景
python scripts/test_e2e.py --scenario chat
python scripts/test_e2e.py --scenario ingestion
python scripts/test_e2e.py --scenario kb_management
```

### `test_performance.py`
性能测试工具。

**用途：** 测试系统性能指标（响应时间、吞吐量等）
**使用方法：**
```bash
# 运行性能测试
python scripts/test_performance.py

# 指定测试参数
python scripts/test_performance.py --queries 100 --concurrent 5

# 生成性能报告
python scripts/test_performance.py --report performance_report.html
```

### `validate_performance.py`
性能验证工具。

**用途：** 验证系统是否满足性能要求
**使用方法：**
```bash
# 验证性能指标
python scripts/validate_performance.py

# 使用自定义阈值
python scripts/validate_performance.py --max-latency 2.0 --min-throughput 10
```

### `validate_security.py`
安全验证工具。

**用途：** 检查系统安全配置和潜在漏洞
**使用方法：**
```bash
# 运行安全检查
python scripts/validate_security.py

# 生成安全报告
python scripts/validate_security.py --report security_report.html
```

## 环境设置脚本

### `setup_models.sh`
模型下载和设置脚本。

**用途：** 自动下载所需的 Ollama 模型
**使用方法：**
```bash
# 下载默认模型
./scripts/setup_models.sh

# 下载特定模型
./scripts/setup_models.sh --llm qwen2.5:7b --embed bge-m3
```
**默认模型：**
- LLM: `qwen2.5:7b`
- Embedding: `bge-m3`

## 脚本开发规范

### 文件组织
- 所有可执行脚本应添加执行权限：`chmod +x script_name.py`
- 脚本文件应包含 shebang 行：`#!/usr/bin/env python3`
- 复杂脚本应包含详细的 docstring 说明

### 参数处理
- 使用 `argparse` 处理命令行参数
- 提供 `--help` 帮助信息
- 重要参数应提供默认值

### 错误处理
- 使用适当的异常处理
- 提供清晰的错误消息
- 设置合理的退出码

### 日志记录
- 使用 Python logging 模块
- 提供 `--verbose` 或 `--debug` 选项
- 重要操作应记录到日志文件

## 常见问题

### 脚本无法执行
```bash
# 检查执行权限
ls -l scripts/script_name.py

# 添加执行权限
chmod +x scripts/script_name.py
```

### 模块导入错误
```bash
# 确保已安装项目
pip install -e .

# 或设置 PYTHONPATH
export PYTHONPATH=/path/to/rag5-simplified-001:$PYTHONPATH
```

### 服务依赖未启动
```bash
# 检查 Qdrant
curl http://localhost:6333/collections

# 检查 Ollama
curl http://localhost:11434/api/tags

# 启动 Qdrant
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

## 贡献新脚本

如需添加新脚本，请遵循以下步骤：

1. 在 `scripts/` 目录创建脚本文件
2. 添加清晰的 docstring 和注释（中文）
3. 实现 `--help` 参数
4. 添加错误处理和日志记录
5. 更新本 README 文件
6. 如有需要，在 `pyproject.toml` 中添加控制台入口点
7. 测试脚本功能是否正常

## 相关文档

- [主 README](../README.md) - 项目总体说明
- [CLAUDE.md](../CLAUDE.md) - Claude Code 开发指南
- [配置说明](../docs/configuration.md) - 系统配置详解
