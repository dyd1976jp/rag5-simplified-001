#!/usr/bin/env python3
"""
API 服务启动脚本

命令行工具，用于启动 RAG5 系统的 REST API 服务。
提供灵活的配置选项，支持自定义主机、端口和日志级别。
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加父目录到路径以支持导入
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
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


def main():
    """
    主函数 - 解析命令行参数并启动 API 服务
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='RAG5 REST API 服务启动工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置启动 API 服务
  python scripts/run_api.py

  # 指定主机和端口
  python scripts/run_api.py --host 0.0.0.0 --port 8080

  # 启用自动重载（开发模式）
  python scripts/run_api.py --reload

  # 使用详细日志
  python scripts/run_api.py --log-level debug

  # 打印配置信息
  python scripts/run_api.py --print-config

  # 仅检查服务状态
  python scripts/run_api.py --check-only

访问 API:
  - API 文档: http://localhost:8000/docs
  - ReDoc 文档: http://localhost:8000/redoc
  - 健康检查: http://localhost:8000/api/v1/health
        """
    )

    # 服务器配置参数
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='服务器主机地址（默认: localhost）'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='服务器端口（默认: 8000）'
    )

    parser.add_argument(
        '--reload',
        action='store_true',
        help='启用自动重载（开发模式）'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='工作进程数（默认: 1）'
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
        help='仅检查服务状态，不启动服务器'
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
                logger.warning("⚠ 部分依赖服务不可用，API 可能无法正常工作")
                logger.warning("继续启动服务器...")

        # 启动服务器
        logger.info("=" * 60)
        logger.info("启动 RAG5 API 服务器")
        logger.info("=" * 60)
        logger.info(f"主机: {args.host}")
        logger.info(f"端口: {args.port}")
        logger.info(f"工作进程: {args.workers}")
        logger.info(f"自动重载: {'是' if args.reload else '否'}")
        logger.info(f"日志级别: {args.log_level}")
        logger.info("")
        logger.info(f"API 文档: http://{args.host}:{args.port}/docs")
        logger.info(f"ReDoc 文档: http://{args.host}:{args.port}/redoc")
        logger.info(f"健康检查: http://{args.host}:{args.port}/api/v1/health")
        logger.info("=" * 60)
        logger.info("")

        # 使用 uvicorn 启动服务器
        uvicorn.run(
            "rag5.interfaces.api.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,  # reload 模式下只能使用 1 个 worker
            log_level=args.log_level,
            access_log=True
        )

        return 0

    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
        return 0
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
