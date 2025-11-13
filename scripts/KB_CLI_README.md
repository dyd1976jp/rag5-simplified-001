# 知识库管理 CLI 工具

命令行工具，用于管理 RAG5 系统的知识库。

## 功能特性

- ✅ 创建、列出、更新、删除知识库
- ✅ 上传和管理文件
- ✅ 查询知识库内容
- ✅ 配置分块和检索参数
- ✅ JSON 输出支持
- ✅ 详细日志模式

## 安装要求

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

确保以下服务正在运行：
- Qdrant (默认: http://localhost:6333)
- Ollama (默认: http://localhost:11434)

## 快速开始

### 1. 创建知识库

```bash
python scripts/kb_manager.py create \
    --name tech_docs \
    --description "技术文档知识库" \
    --embedding-model nomic-embed-text
```

可选参数：
- `--chunk-size`: 分块大小（默认: 512）
- `--chunk-overlap`: 分块重叠（默认: 50）
- `--parser-type`: 解析器类型（sentence/recursive/semantic）
- `--top-k`: 检索结果数量（默认: 5）
- `--similarity-threshold`: 相似度阈值（默认: 0.3）
- `--retrieval-mode`: 检索模式（vector/fulltext/hybrid）

### 2. 列出所有知识库

```bash
# 基本列表
python scripts/kb_manager.py list

# 分页
python scripts/kb_manager.py list --page 2 --size 20

# JSON 输出
python scripts/kb_manager.py list --json
```

### 3. 查看知识库详情

```bash
python scripts/kb_manager.py get --kb-id kb_123abc
```

### 4. 更新知识库配置

```bash
# 更新描述
python scripts/kb_manager.py update \
    --kb-id kb_123abc \
    --description "更新后的描述"

# 更新检索配置
python scripts/kb_manager.py update \
    --kb-id kb_123abc \
    --top-k 10 \
    --similarity-threshold 0.5

# 更新分块配置
python scripts/kb_manager.py update \
    --kb-id kb_123abc \
    --chunk-size 1024 \
    --chunk-overlap 100
```

### 5. 上传文件

```bash
# 上传文件（不立即处理）
python scripts/kb_manager.py upload \
    --kb-id kb_123abc \
    --file /path/to/document.pdf

# 上传并立即处理
python scripts/kb_manager.py upload \
    --kb-id kb_123abc \
    --file /path/to/document.pdf \
    --process

# 自定义文件名
python scripts/kb_manager.py upload \
    --kb-id kb_123abc \
    --file /path/to/document.pdf \
    --name "my_document.pdf"
```

支持的文件格式：
- `.txt` - 文本文件
- `.md` - Markdown 文件
- `.pdf` - PDF 文档
- `.docx` - Word 文档

### 6. 列出文件

```bash
# 列出所有文件
python scripts/kb_manager.py list-files --kb-id kb_123abc

# 按状态过滤
python scripts/kb_manager.py list-files \
    --kb-id kb_123abc \
    --status succeeded

# 分页
python scripts/kb_manager.py list-files \
    --kb-id kb_123abc \
    --page 2 \
    --size 20
```

文件状态：
- `pending` - 等待处理
- `parsing` - 正在解析
- `persisting` - 正在存储
- `succeeded` - 处理成功
- `failed` - 处理失败
- `cancelled` - 已取消

### 7. 删除文件

```bash
# 交互式删除（需要确认）
python scripts/kb_manager.py delete-file \
    --kb-id kb_123abc \
    --file-id file_456def

# 跳过确认
python scripts/kb_manager.py delete-file \
    --kb-id kb_123abc \
    --file-id file_456def \
    --yes
```

### 8. 查询知识库

```bash
# 基本查询
python scripts/kb_manager.py query \
    --kb-id kb_123abc \
    --query "什么是人工智能？"

# 自定义参数
python scripts/kb_manager.py query \
    --kb-id kb_123abc \
    --query "什么是人工智能？" \
    --top-k 10 \
    --similarity-threshold 0.4

# 显示完整文本
python scripts/kb_manager.py query \
    --kb-id kb_123abc \
    --query "什么是人工智能？" \
    --full

# JSON 输出
python scripts/kb_manager.py query \
    --kb-id kb_123abc \
    --query "什么是人工智能？" \
    --json
```

### 9. 删除知识库

```bash
# 交互式删除（需要确认）
python scripts/kb_manager.py delete --kb-id kb_123abc

# 跳过确认
python scripts/kb_manager.py delete --kb-id kb_123abc --yes
```

⚠️ **警告**: 删除知识库将删除所有关联的文件和向量数据，此操作不可撤销！

## 全局选项

所有命令都支持以下全局选项：

- `-v, --verbose`: 启用详细日志输出
- `--json`: 以 JSON 格式输出结果

示例：

```bash
# 详细日志
python scripts/kb_manager.py list -v

# JSON 输出
python scripts/kb_manager.py list --json

# 组合使用
python scripts/kb_manager.py list -v --json
```

## 完整工作流示例

```bash
# 1. 创建知识库
python scripts/kb_manager.py create \
    --name my_kb \
    --description "我的知识库" \
    --embedding-model nomic-embed-text \
    --chunk-size 512 \
    --top-k 5

# 输出: kb_123abc

# 2. 上传文件
python scripts/kb_manager.py upload \
    --kb-id kb_123abc \
    --file ./docs/document1.pdf \
    --process

python scripts/kb_manager.py upload \
    --kb-id kb_123abc \
    --file ./docs/document2.md \
    --process

# 3. 查看文件列表
python scripts/kb_manager.py list-files \
    --kb-id kb_123abc \
    --status succeeded

# 4. 查询知识库
python scripts/kb_manager.py query \
    --kb-id kb_123abc \
    --query "总结文档的主要内容" \
    --top-k 3

# 5. 更新配置（如果需要）
python scripts/kb_manager.py update \
    --kb-id kb_123abc \
    --top-k 10

# 6. 删除不需要的文件
python scripts/kb_manager.py delete-file \
    --kb-id kb_123abc \
    --file-id file_456def \
    --yes

# 7. 查看知识库详情
python scripts/kb_manager.py get --kb-id kb_123abc
```

## 配置

CLI 工具使用以下配置：

- **数据库路径**: `./data/knowledge_bases.db`
- **文件存储路径**: `./docs`
- **Qdrant URL**: 从 `settings.qdrant_url` 读取
- **向量维度**: 从 `settings.vector_dim` 读取

可以通过修改 `.env` 文件来更改这些配置。

## 错误处理

CLI 工具提供清晰的错误消息：

```bash
# 知识库不存在
✗ 知识库不存在: kb_invalid

# 名称已存在
✗ 知识库名称 'my_kb' 已存在

# 文件格式不支持
✗ 不支持的文件格式: .xlsx。支持的格式: .txt, .md, .pdf, .docx

# 文件过大
✗ 文件过大: 150.5MB，最大允许: 100.0MB
```

使用 `-v` 选项可以查看详细的错误堆栈：

```bash
python scripts/kb_manager.py create --name test -v
```

## 故障排除

### 1. 无法连接到 Qdrant

```
✗ 创建向量集合失败: Connection refused
```

**解决方案**: 确保 Qdrant 正在运行：

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 2. 嵌入模型不可用

```
✗ 生成嵌入失败: Model not found
```

**解决方案**: 拉取嵌入模型：

```bash
ollama pull nomic-embed-text
```

### 3. 数据库锁定

```
✗ 创建数据库记录失败: database is locked
```

**解决方案**: 确保没有其他进程正在使用数据库，或等待当前操作完成。

### 4. 文件处理失败

```
✗ 文档解析失败: ...
```

**解决方案**: 
- 检查文件是否损坏
- 确保文件格式正确
- 查看详细日志 (`-v`) 了解具体错误

## 高级用法

### 批量操作

使用 shell 脚本批量上传文件：

```bash
#!/bin/bash
KB_ID="kb_123abc"

for file in ./docs/*.pdf; do
    echo "上传: $file"
    python scripts/kb_manager.py upload \
        --kb-id "$KB_ID" \
        --file "$file" \
        --process
done
```

### JSON 输出处理

使用 `jq` 处理 JSON 输出：

```bash
# 提取所有知识库 ID
python scripts/kb_manager.py list --json | jq -r '.knowledge_bases[].id'

# 统计文档总数
python scripts/kb_manager.py list --json | jq '[.knowledge_bases[].document_count] | add'

# 查找特定名称的知识库
python scripts/kb_manager.py list --json | jq '.knowledge_bases[] | select(.name == "tech_docs")'
```

### 自动化脚本

创建自动化脚本进行定期维护：

```bash
#!/bin/bash
# 每日知识库维护脚本

# 列出所有知识库
echo "=== 知识库列表 ==="
python scripts/kb_manager.py list

# 检查失败的文件
for kb_id in $(python scripts/kb_manager.py list --json | jq -r '.knowledge_bases[].id'); do
    echo "检查知识库: $kb_id"
    python scripts/kb_manager.py list-files \
        --kb-id "$kb_id" \
        --status failed
done
```

## 性能建议

1. **批量上传**: 使用 `--process` 选项立即处理文件，避免后续手动处理
2. **分页**: 处理大量数据时使用分页参数 `--page` 和 `--size`
3. **JSON 输出**: 需要程序化处理时使用 `--json` 选项
4. **并发**: 可以同时运行多个 CLI 实例处理不同的知识库

## 相关文档

- [知识库管理设计文档](../.kiro/specs/knowledge-base-management/design.md)
- [需求文档](../.kiro/specs/knowledge-base-management/requirements.md)
- [任务列表](../.kiro/specs/knowledge-base-management/tasks.md)

## 支持

如有问题或建议，请查看项目文档或提交 issue。
