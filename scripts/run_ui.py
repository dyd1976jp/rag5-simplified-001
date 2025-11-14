#!/usr/bin/env python3
"""
UI 服务启动脚本

命令行工具，用于启动 RAG5 系统的 Streamlit Web UI。
提供灵活的配置选项，支持自定义端口和主题设置。
"""

import sys
import argparse
import logging
import subprocess
from pathlib import Path

# 添加父目录到路径以支持导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag5.config import settings


def setup_logging(log_level: str = "info"):
    """
    配置日志系统

    参数:
        log_level: 日志级别 (debug, info, warning, error)
    """
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR
    }

    level = level_map.get(log_level.lower(), logging.INFO)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_config():
    """
    验证配置

    异常:
        ValueError: 配置验证失败
    """
    logger = logging.getLogger(__name__)
    logger.info("验证配置...")

    try:
        settings.validate()
        logger.info("✓ 配置验证成功")
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        raise


def check_services():
    """
    检查依赖服务状态

    返回:
        bool: 所有服务是否可用
    """
    logger = logging.getLogger(__name__)
    logger.info("检查依赖服务...")

    import requests

    all_ok = True

    # 检查 Ollama
    try:
        response = requests.get(f"{settings.ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info(f"  ✓ Ollama 运行中: {settings.ollama_host}")
        else:
            logger.warning(f"  ✗ Ollama 响应异常: {settings.ollama_host}")
            all_ok = False
    except Exception as e:
        logger.warning(f"  ✗ 无法连接到 Ollama: {e}")
        all_ok = False

    # 检查 Qdrant
    try:
        response = requests.get(f"{settings.qdrant_url}/collections", timeout=5)
        if response.status_code == 200:
            logger.info(f"  ✓ Qdrant 运行中: {settings.qdrant_url}")
        else:
            logger.warning(f"  ✗ Qdrant 响应异常: {settings.qdrant_url}")
            all_ok = False
    except Exception as e:
        logger.warning(f"  ✗ 无法连接到 Qdrant: {e}")
        all_ok = False

    return all_ok


def check_streamlit():
    """
    检查 Streamlit 是否已安装

    返回:
        bool: Streamlit 是否可用
    """
    try:
        import streamlit
        return True
    except ImportError:
        return False


def main():
    """
    主函数 - 解析命令行参数并启动 UI 服务
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='RAG5 Streamlit Web UI 启动工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置启动 UI 服务
  python scripts/run_ui.py

  # 指定端口
  python scripts/run_ui.py --port 8501

  # 指定服务器地址（允许外部访问）
  python scripts/run_ui.py --server-address 0.0.0.0

  # 使用深色主题
  python scripts/run_ui.py --theme dark

  # 打印配置信息
  python scripts/run_ui.py --print-config

  # 仅检查服务状态
  python scripts/run_ui.py --check-only

访问 UI:
  - 默认地址: http://localhost:8501
        """
    )

    # 服务器配置参数
    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='服务器端口（默认: 8501）'
    )

    parser.add_argument(
        '--server-address',
        type=str,
        default='localhost',
        help='服务器地址（默认: localhost）'
    )

    parser.add_argument(
        '--theme',
        type=str,
        choices=['light', 'dark'],
        default='light',
        help='UI 主题（默认: light）'
    )

    parser.add_argument(
        '--browser',
        action='store_true',
        help='自动打开浏览器'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='日志级别（默认: info）'
    )

    # 工具参数
    parser.add_argument(
        '--print-config',
        action='store_true',
        help='打印当前配置并退出'
    )

    parser.add_argument(
        '--check-only',
        action='store_true',
        help='仅检查服务状态，不启动 UI'
    )

    parser.add_argument(
        '--no-check',
        action='store_true',
        help='跳过服务检查，直接启动'
    )

    # 解析参数
    args = parser.parse_args()

    # 配置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # 检查 Streamlit 是否已安装
        if not check_streamlit():
            logger.error("Streamlit 未安装")
            logger.error("请运行: pip install streamlit")
            return 1

        # 验证配置
        validate_config()

        # 打印配置（如果请求）
        if args.print_config:
            settings.print_config()
            return 0

        # 检查服务
        if not args.no_check:
            services_ok = check_services()

            if args.check_only:
                if services_ok:
                    logger.info("✓ 所有服务运行正常")
                    return 0
                else:
                    logger.warning("⚠ 部分服务不可用")
                    return 1

            if not services_ok:
                logger.warning("⚠ 部分依赖服务不可用，UI 可能无法正常工作")
                logger.warning("继续启动 UI...")

        # 构建 Streamlit 命令
        ui_app_path = Path(__file__).parent.parent / "rag5" / "interfaces" / "ui" / "app.py"

        if not ui_app_path.exists():
            logger.error(f"UI 应用文件不存在: {ui_app_path}")
            return 1

        # 启动 UI
        logger.info("=" * 60)
        logger.info("启动 RAG5 Streamlit UI")
        logger.info("=" * 60)
        logger.info(f"地址: {args.server_address}")
        logger.info(f"端口: {args.port}")
        logger.info(f"主题: {args.theme}")
        logger.info(f"自动打开浏览器: {'是' if args.browser else '否'}")
        logger.info("")
        logger.info(f"访问地址: http://{args.server_address}:{args.port}")
        logger.info("=" * 60)
        logger.info("")
        logger.info("按 Ctrl+C 停止服务器")
        logger.info("")

        # 构建 streamlit 命令
        cmd = [
            "streamlit", "run",
            str(ui_app_path),
            "--server.port", str(args.port),
            "--server.address", args.server_address,
            "--theme.base", args.theme,
        ]

        # 添加浏览器选项
        if not args.browser:
            cmd.extend(["--server.headless", "true"])

        # 运行 Streamlit
        result = subprocess.run(cmd)

        return result.returncode

    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("\nUI 服务器已停止")
        return 0
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        logger.error("请确保在正确的目录中运行此脚本")
        return 1
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
