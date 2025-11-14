# Implementation Plan

- [x] 1. 重构现有 UI 结构，支持多页面导航
  - 将现有 app.py 中的聊天功能提取到 pages/chat.py
  - 在 app.py 中添加页面路由逻辑（使用 st.sidebar.radio）
  - 创建 pages/ 目录结构
  - 更新 SessionState 类，添加页面状态管理方法
  - 测试页面切换功能
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. 实现 API 客户端封装
  - 创建 pages/knowledge_base/api_client.py
  - 实现 KnowledgeBaseAPIClient 类
  - 实现知识库 CRUD 方法（list, get, create, update, delete）
  - 实现文件管理方法（list_files, upload_files, delete_file）
  - 实现查询方法（query_knowledge_base）
  - 添加错误处理和重试逻辑
  - 添加请求超时配置
  - _Requirements: 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1_

- [x] 3. 实现知识库列表页面
  - 创建 pages/knowledge_base/list.py
  - 实现 render_kb_list_page 函数
  - 实现知识库卡片组件 render_kb_card
  - 添加 3x3 网格布局显示知识库
  - 实现分页功能
  - 添加空状态提示
  - 实现刷新功能
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4. 实现创建知识库功能
  - 实现 render_create_kb_dialog 函数（使用 @st.dialog）
  - 添加知识库名称和描述输入
  - 添加切片配置输入（chunk_size, chunk_overlap）
  - 添加向量模型选择
  - 添加检索配置输入（top_k, similarity_threshold, retrieval_mode）
  - 实现表单验证
  - 调用 API 创建知识库
  - 创建成功后跳转到详情页面
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 5. 实现删除知识库功能
  - 实现 show_delete_confirmation 函数（使用 @st.dialog）
  - 添加删除确认对话框
  - 显示警告信息
  - 调用 API 删除知识库
  - 删除成功后刷新列表
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 6. 实现知识库详情页面框架
  - 创建 pages/knowledge_base/detail.py
  - 实现 render_kb_detail_page 函数
  - 添加顶部导航（返回按钮和知识库信息）
  - 使用 st.tabs 创建三个标签页
  - 实现标签页切换逻辑
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. 实现文件管理标签页
  - 实现 render_file_management_tab 函数
  - 添加文件上传组件（st.file_uploader）
  - 实现文件列表显示
  - 添加搜索和筛选功能
  - 实现 render_file_row 组件
  - 显示文件状态（使用彩色标记）
  - 添加文件分页功能
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 11.1, 12.1, 12.2, 12.3, 12.4_

- [x] 8. 实现文件操作功能
  - 实现文件上传功能（调用 upload_files API）
  - 实现文件删除功能（调用 delete_file API）
  - 实现文件重新处理功能
  - 添加操作进度提示
  - 添加操作成功/失败反馈
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 8.1, 8.2, 8.3, 9.1, 9.2, 9.3_

- [x] 9. 实现知识库设置标签页
  - 实现 render_kb_settings_tab 函数
  - 使用 st.form 创建配置表单
  - 添加基本信息编辑（名称、描述）
  - 添加切片配置编辑
  - 添加检索配置编辑（top_k, similarity_threshold, retrieval_mode）
  - 实现保存功能（调用 update_knowledge_base API）
  - 添加保存成功/失败反馈
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 10. 实现检索测试标签页
  - 实现 render_retrieval_test_tab 函数
  - 添加查询输入框
  - 添加 top_k 滑块
  - 实现搜索功能（调用 query_knowledge_base API）
  - 使用 st.expander 显示检索结果
  - 显示相似度分数和内容
  - 显示元数据信息
  - 添加空结果提示
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 11. 集成知识库选择器到聊天页面
  - 修改 pages/chat.py
  - 在侧边栏添加知识库选择器
  - 使用 st.selectbox 显示知识库列表
  - 在 SessionState 中保存选定的知识库
  - 修改 handle_user_input 函数，支持传入 kb_id 参数
  - 修改 ask 函数调用，传入选定的知识库 ID
  - 显示当前使用的知识库名称
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 12. 实现工具函数和组件
  - 创建 pages/knowledge_base/components.py
  - 实现 format_datetime 函数
  - 实现 format_file_size 函数
  - 实现 safe_api_call 错误处理包装器
  - 实现用户反馈函数（show_success, show_error, show_warning, show_info）
  - 实现输入验证函数（validate_kb_name, validate_file_upload）
  - 额外实现：format_percentage, truncate_text, validate_chunk_config, validate_retrieval_config, render_status_badge, create_progress_bar, show_spinner
  - 创建了完整的测试套件（20 个单元测试通过）
  - 创建了交互式演示应用（test_components_demo.py）
  - 创建了详细的使用文档（COMPONENTS_USAGE.md）
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 15.1, 15.2, 15.3, 15.4_

- [x] 13. 添加配置管理
  - 创建 rag5/interfaces/ui/config.py
  - 定义 UIConfig 类
  - 添加 API 配置（base_url, timeout）
  - 添加 UI 配置（page_size, file_page_size）
  - 添加缓存配置（cache_ttl）
  - 支持环境变量配置
  - 额外实现：类方法访问、全局配置实例、配置显示方法
  - 创建了完整的测试套件（10 个单元测试通过）
  - 创建了详细的使用文档（CONFIG_USAGE.md）
  - _Requirements: All_

- [ ] 14. 实现性能优化
  - 添加 @st.cache_data 装饰器缓存 API 响应
  - 实现 get_knowledge_bases_cached 函数
  - 实现 get_kb_files_cached 函数
  - 优化 st.rerun() 调用
  - 实现懒加载策略
  - _Requirements: All_

- [ ] 15. 更新文档和示例
  - 更新 scripts/run_ui.py 的帮助文档
  - 创建 UI 使用指南文档
  - 添加知识库管理功能说明
  - 添加截图和示例
  - 更新 README.md
  - _Requirements: All_

- [ ]* 16. 编写测试
- [ ]* 16.1 编写 API 客户端单元测试
  - 测试所有 API 方法
  - 测试错误处理
  - 测试请求参数格式化
  - _Requirements: 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1_

- [ ]* 16.2 编写状态管理测试
  - 测试 SessionState 新增方法
  - 测试状态持久化
  - 测试状态初始化
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 16.3 编写工具函数测试
  - 测试日期时间格式化
  - 测试文件大小格式化
  - 测试输入验证
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ]* 16.4 编写集成测试
  - 测试页面导航流程
  - 测试知识库 CRUD 流程
  - 测试文件上传流程
  - 测试检索测试流程
  - _Requirements: All_
