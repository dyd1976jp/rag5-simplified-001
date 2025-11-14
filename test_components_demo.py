#!/usr/bin/env python
"""
知识库组件演示应用

这个 Streamlit 应用演示了 components.py 中的各种 UI 组件。
运行方式: streamlit run test_components_demo.py
"""

import streamlit as st
from datetime import datetime
from rag5.interfaces.ui.pages.knowledge_base.components import (
    # 格式化函数
    format_datetime,
    format_file_size,
    format_percentage,
    truncate_text,
    # 用户反馈函数
    show_success,
    show_error,
    show_warning,
    show_info,
    show_spinner,
    # 输入验证函数
    validate_kb_name,
    validate_chunk_config,
    validate_retrieval_config,
    # UI 组件
    render_status_badge,
    create_progress_bar,
)
import time

st.set_page_config(
    page_title="知识库组件演示",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 知识库组件演示")
st.markdown("---")

# 侧边栏导航
demo_section = st.sidebar.radio(
    "选择演示部分",
    [
        "📊 格式化函数",
        "✅ 用户反馈",
        "🔍 输入验证",
        "🎨 UI 组件"
    ]
)

# ==================== 格式化函数演示 ====================
if demo_section == "📊 格式化函数":
    st.header("📊 格式化函数演示")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. 日期时间格式化")
        st.code("""format_datetime("2024-01-15T10:30:00Z")""")
        result = format_datetime("2024-01-15T10:30:00Z")
        st.success(f"结果: {result}")

        st.subheader("2. 文件大小格式化")
        size_bytes = st.slider("文件大小（字节）", 0, 10*1024*1024*1024, 1048576)
        st.code(f"format_file_size({size_bytes})")
        result = format_file_size(size_bytes)
        st.success(f"结果: {result}")

    with col2:
        st.subheader("3. 百分比格式化")
        percentage = st.slider("百分比值", 0.0, 100.0, 85.5)
        decimals = st.select_slider("小数位数", [0, 1, 2], value=1)
        st.code(f"format_percentage({percentage}, decimals={decimals})")
        result = format_percentage(percentage, decimals=decimals)
        st.success(f"结果: {result}")

        st.subheader("4. 文本截断")
        text = st.text_input("输入文本", "这是一段很长的文本内容需要被截断")
        max_length = st.slider("最大长度", 5, 50, 10)
        st.code(f'truncate_text("{text}", max_length={max_length})')
        result = truncate_text(text, max_length=max_length)
        st.success(f"结果: {result}")

# ==================== 用户反馈演示 ====================
elif demo_section == "✅ 用户反馈":
    st.header("✅ 用户反馈函数演示")

    st.subheader("点击按钮查看不同类型的消息")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ 成功消息", use_container_width=True):
            show_success("操作成功完成！")

    with col2:
        if st.button("❌ 错误消息", use_container_width=True):
            show_error("操作失败", details="详细错误信息：连接超时")

    with col3:
        if st.button("⚠️ 警告消息", use_container_width=True):
            show_warning("此操作不可撤销，请谨慎操作")

    with col4:
        if st.button("ℹ️ 信息消息", use_container_width=True):
            show_info("暂无数据，请先上传文件")

    st.markdown("---")
    st.subheader("加载旋转器演示")

    if st.button("🔄 显示加载旋转器", use_container_width=True):
        with show_spinner("正在处理，请稍候..."):
            time.sleep(2)
        show_success("处理完成！")

# ==================== 输入验证演示 ====================
elif demo_section == "🔍 输入验证":
    st.header("🔍 输入验证函数演示")

    # 知识库名称验证
    st.subheader("1. 知识库名称验证")
    kb_name = st.text_input("输入知识库名称", "")
    if st.button("验证知识库名称"):
        valid, error = validate_kb_name(kb_name)
        if valid:
            show_success("知识库名称有效！")
        else:
            show_error(f"知识库名称无效: {error}")

    st.markdown("---")

    # 分块配置验证
    st.subheader("2. 分块配置验证")
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.number_input("分块大小", min_value=0, value=500)
    with col2:
        chunk_overlap = st.number_input("分块重叠", min_value=0, value=50)

    if st.button("验证分块配置"):
        valid, error = validate_chunk_config(chunk_size, chunk_overlap)
        if valid:
            show_success("分块配置有效！")
        else:
            show_error(f"分块配置无效: {error}")

    st.markdown("---")

    # 检索配置验证
    st.subheader("3. 检索配置验证")
    col1, col2 = st.columns(2)
    with col1:
        top_k = st.number_input("返回结果数 (top_k)", min_value=0, value=5)
    with col2:
        similarity_threshold = st.slider(
            "相似度阈值",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05
        )

    if st.button("验证检索配置"):
        valid, error = validate_retrieval_config(top_k, similarity_threshold)
        if valid:
            show_success("检索配置有效！")
        else:
            show_error(f"检索配置无效: {error}")

# ==================== UI 组件演示 ====================
elif demo_section == "🎨 UI 组件":
    st.header("🎨 UI 组件演示")

    # 状态徽章
    st.subheader("1. 状态徽章")
    st.write("不同状态的徽章显示：")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write("成功状态:")
        render_status_badge("success")
    with col2:
        st.write("错误状态:")
        render_status_badge("error")
    with col3:
        st.write("处理中:")
        render_status_badge("processing")
    with col4:
        st.write("待处理:")
        render_status_badge("pending")

    st.markdown("---")

    # 进度条
    st.subheader("2. 进度条")

    col1, col2 = st.columns(2)
    with col1:
        current = st.slider("当前进度", 0, 100, 30)
    with col2:
        total = st.slider("总进度", 1, 100, 100)

    create_progress_bar(current, total, label="上传进度")

    st.markdown("---")

    # 动态进度条演示
    st.subheader("3. 动态进度条演示")
    if st.button("🚀 开始处理", use_container_width=True):
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        for i in range(0, 101, 10):
            with progress_placeholder:
                create_progress_bar(i, 100, label="正在处理文件...")

            with status_placeholder:
                if i < 30:
                    render_status_badge("pending")
                elif i < 100:
                    render_status_badge("processing")
                else:
                    render_status_badge("success")

            time.sleep(0.3)

        show_success("处理完成！")

# 页脚
st.markdown("---")
st.caption("💡 这些组件来自 `rag5/interfaces/ui/pages/knowledge_base/components.py`")
