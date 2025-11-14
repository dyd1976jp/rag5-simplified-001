# Requirements Document

## Introduction

本功能为 rag5-simplified 系统的现有 Streamlit UI 添加完整的知识库管理界面，参考 PAI-RAG 的功能模式。系统将在现有聊天界面基础上扩展知识库列表、创建、详情、文件管理和检索测试等功能，使用户能够通过 Streamlit Web 界面管理知识库和文档。

## Glossary

- **KnowledgeBaseUI**: 知识库管理的 Streamlit 前端界面
- **RAG5_StreamlitApp**: rag5-simplified 的 Streamlit 应用系统
- **User**: 通过浏览器访问 Streamlit 应用的用户
- **KnowledgeBasePage**: 知识库列表页面组件
- **FileManagementTab**: 文件管理标签页组件
- **ConfigTab**: 知识库配置标签页组件
- **RetrievalTestTab**: 检索测试标签页组件
- **API_Backend**: rag5-simplified 的 FastAPI 后端服务
- **SessionState**: Streamlit 会话状态管理器

## Requirements

### Requirement 1

**User Story:** 作为用户，我想要在 Streamlit 侧边栏中添加知识库管理入口，以便访问知识库功能。

#### Acceptance Criteria

1. THE RAG5_StreamlitApp SHALL 在侧边栏添加"知识库管理"导航选项
2. WHEN 用户选择"知识库管理"，THE RAG5_StreamlitApp SHALL 切换到知识库管理页面
3. THE RAG5_StreamlitApp SHALL 保持原有聊天界面作为默认页面
4. THE RAG5_StreamlitApp SHALL 使用 st.sidebar.radio 或 st.sidebar.selectbox 实现页面切换

### Requirement 2

**User Story:** 作为用户，我想要查看所有知识库的列表，以便了解系统中有哪些知识库。

#### Acceptance Criteria

1. WHEN 用户进入知识库管理页面，THE RAG5_StreamlitApp SHALL 调用 API 获取知识库列表
2. THE RAG5_StreamlitApp SHALL 使用 st.columns 以卡片形式显示知识库
3. THE RAG5_StreamlitApp SHALL 为每个知识库显示名称、描述、ID 和更新时间
4. WHERE 知识库数量超过每页显示数量，THE RAG5_StreamlitApp SHALL 使用 st.pagination 提供分页
5. IF 系统中没有知识库，THEN THE RAG5_StreamlitApp SHALL 显示 st.info 提示和创建按钮

### Requirement 3

**User Story:** 作为用户，我想要创建新的知识库，以便组织不同领域的文档。

#### Acceptance Criteria

1. WHEN 用户点击"新建知识库"按钮，THE RAG5_StreamlitApp SHALL 使用 st.dialog 或 st.expander 显示创建表单
2. THE RAG5_StreamlitApp SHALL 使用 st.text_input 输入知识库名称和描述
3. THE RAG5_StreamlitApp SHALL 使用 st.number_input 设置切片大小和重叠
4. THE RAG5_StreamlitApp SHALL 使用 st.selectbox 选择向量模型和检索策略
5. WHEN 用户提交表单，THE RAG5_StreamlitApp SHALL 验证必填字段并调用创建 API
6. WHEN 创建成功，THE RAG5_StreamlitApp SHALL 使用 st.success 显示成功消息并刷新列表
7. IF 创建失败，THEN THE RAG5_StreamlitApp SHALL 使用 st.error 显示错误信息

### Requirement 4

**User Story:** 作为用户，我想要删除不需要的知识库，以便清理系统资源。

#### Acceptance Criteria

1. WHEN 用户点击知识库卡片上的删除按钮，THE RAG5_StreamlitApp SHALL 使用 st.dialog 显示确认对话框
2. THE RAG5_StreamlitApp SHALL 在对话框中使用 st.warning 警告删除操作不可撤销
3. WHEN 用户确认删除，THE RAG5_StreamlitApp SHALL 调用删除 API 并使用 st.rerun 刷新页面
4. IF 删除失败，THEN THE RAG5_StreamlitApp SHALL 使用 st.error 显示错误提示

### Requirement 5

**User Story:** 作为用户，我想要查看知识库的详细信息和文件列表，以便管理知识库内容。

#### Acceptance Criteria

1. WHEN 用户点击知识库卡片，THE RAG5_StreamlitApp SHALL 切换到知识库详情页面
2. THE RAG5_StreamlitApp SHALL 使用 st.tabs 提供三个标签页：文件管理、知识库设置、检索测试
3. THE RAG5_StreamlitApp SHALL 在页面顶部使用 st.markdown 显示知识库基本信息
4. THE RAG5_StreamlitApp SHALL 在文件管理标签页使用 st.dataframe 显示文件列表
5. WHERE 文件数量超过每页显示数量，THE RAG5_StreamlitApp SHALL 使用分页控件

### Requirement 6

**User Story:** 作为用户，我想要上传文件到知识库，以便添加新的文档内容。

#### Acceptance Criteria

1. THE RAG5_StreamlitApp SHALL 使用 st.file_uploader 提供文件上传功能
2. THE RAG5_StreamlitApp SHALL 支持 accept_multiple_files=True 同时上传多个文件
3. WHEN 用户选择文件后，THE RAG5_StreamlitApp SHALL 使用 st.spinner 显示上传进度
4. WHEN 上传完成，THE RAG5_StreamlitApp SHALL 使用 st.success 显示成功消息并刷新文件列表
5. IF 上传失败，THEN THE RAG5_StreamlitApp SHALL 使用 st.error 显示错误信息

### Requirement 7

**User Story:** 作为用户，我想要查看文件的处理状态，以便了解文件是否已成功索引。

#### Acceptance Criteria

1. THE RAG5_StreamlitApp SHALL 在文件列表中使用 st.status 或彩色标记显示文件状态
2. THE RAG5_StreamlitApp SHALL 为不同状态使用不同颜色（等待中-黄色、处理中-蓝色、成功-绿色、失败-红色）
3. WHEN 文件状态为失败，THE RAG5_StreamlitApp SHALL 使用 st.expander 显示错误详情
4. THE RAG5_StreamlitApp SHALL 使用 st.selectbox 提供状态筛选功能

### Requirement 8

**User Story:** 作为用户，我想要删除知识库中的文件，以便移除不需要的文档。

#### Acceptance Criteria

1. WHEN 用户点击文件的删除按钮，THE RAG5_StreamlitApp SHALL 调用删除文件 API
2. WHEN 删除成功，THE RAG5_StreamlitApp SHALL 使用 st.success 显示成功消息并刷新列表
3. IF 删除失败，THEN THE RAG5_StreamlitApp SHALL 使用 st.error 显示错误提示

### Requirement 9

**User Story:** 作为用户，我想要重新处理失败的文件，以便修复索引问题。

#### Acceptance Criteria

1. WHEN 用户点击"重新解析"按钮，THE RAG5_StreamlitApp SHALL 调用重新处理文件 API
2. WHEN 重新处理开始，THE RAG5_StreamlitApp SHALL 使用 st.info 显示处理中提示
3. THE RAG5_StreamlitApp SHALL 使用 st.rerun 刷新文件列表以显示最新状态

### Requirement 10

**User Story:** 作为用户，我想要修改知识库的配置，以便调整切片和检索参数。

#### Acceptance Criteria

1. WHEN 用户切换到"知识库设置"标签页，THE RAG5_StreamlitApp SHALL 显示配置表单
2. THE RAG5_StreamlitApp SHALL 使用 st.number_input 修改切片大小、切片重叠、Top-K 等参数
3. THE RAG5_StreamlitApp SHALL 使用 st.slider 调整相似度阈值
4. THE RAG5_StreamlitApp SHALL 使用 st.radio 选择检索策略（向量、全文、混合）
5. WHEN 用户点击保存按钮，THE RAG5_StreamlitApp SHALL 调用更新 API 并使用 st.success 显示成功提示
6. IF 保存失败，THEN THE RAG5_StreamlitApp SHALL 使用 st.error 显示错误信息

### Requirement 11

**User Story:** 作为用户，我想要测试知识库的检索功能，以便验证检索效果。

#### Acceptance Criteria

1. WHEN 用户切换到"检索测试"标签页，THE RAG5_StreamlitApp SHALL 使用 st.text_input 提供查询输入
2. WHEN 用户输入查询并点击搜索，THE RAG5_StreamlitApp SHALL 使用 st.spinner 显示搜索状态
3. THE RAG5_StreamlitApp SHALL 使用 st.expander 以可展开卡片形式显示检索结果
4. THE RAG5_StreamlitApp SHALL 为每个结果显示相似度分数、内容和元数据
5. IF 没有检索结果，THEN THE RAG5_StreamlitApp SHALL 使用 st.info 显示"未找到相关内容"提示

### Requirement 12

**User Story:** 作为用户，我想要搜索和筛选文件，以便快速找到特定文件。

#### Acceptance Criteria

1. THE RAG5_StreamlitApp SHALL 使用 st.text_input 在文件列表上方提供搜索功能
2. THE RAG5_StreamlitApp SHALL 使用 st.selectbox 提供状态筛选下拉菜单
3. WHEN 用户输入搜索关键词或更改筛选条件，THE RAG5_StreamlitApp SHALL 自动更新文件列表
4. THE RAG5_StreamlitApp SHALL 在 SessionState 中保存筛选条件

### Requirement 13

**User Story:** 作为用户，我想要在聊天界面中选择知识库，以便从特定知识库检索信息。

#### Acceptance Criteria

1. THE RAG5_StreamlitApp SHALL 在聊天页面侧边栏添加知识库选择器
2. THE RAG5_StreamlitApp SHALL 使用 st.selectbox 显示可用知识库列表
3. WHEN 用户选择知识库，THE RAG5_StreamlitApp SHALL 在 SessionState 中保存选择
4. WHEN 用户提问时，THE RAG5_StreamlitApp SHALL 使用选定的知识库进行检索
5. THE RAG5_StreamlitApp SHALL 显示当前使用的知识库名称

### Requirement 14

**User Story:** 作为用户，我想要看到操作的即时反馈，以便了解操作是否成功。

#### Acceptance Criteria

1. WHEN 用户执行操作，THE RAG5_StreamlitApp SHALL 使用 st.spinner 显示加载状态
2. WHEN 操作成功，THE RAG5_StreamlitApp SHALL 使用 st.success 显示成功提示
3. IF 操作失败，THEN THE RAG5_StreamlitApp SHALL 使用 st.error 显示错误提示
4. THE RAG5_StreamlitApp SHALL 使用 st.toast 显示临时通知消息

### Requirement 15

**User Story:** 作为用户，我想要使用返回按钮导航，以便在不同页面间切换。

#### Acceptance Criteria

1. THE RAG5_StreamlitApp SHALL 在知识库详情页面顶部提供"返回列表"按钮
2. WHEN 用户点击返回按钮，THE RAG5_StreamlitApp SHALL 切换回知识库列表页面
3. THE RAG5_StreamlitApp SHALL 在 SessionState 中保存当前页面状态
4. THE RAG5_StreamlitApp SHALL 使用 st.button 实现页面导航
