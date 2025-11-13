"""
RAG5 简化系统 - 安装配置

基于检索增强生成(RAG)技术的本地化问答系统。
"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "基于检索增强生成(RAG)技术的本地化问答系统"

# 读取依赖列表
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
else:
    # 如果 requirements.txt 不存在，使用硬编码的依赖列表
    requirements = [
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "langchain-ollama>=0.1.0",
        "langgraph>=0.0.20",
        "qdrant-client>=1.7.0",
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "streamlit>=1.30.0",
        "python-dotenv>=1.0.0",
        "pypdf>=3.17.0",
        "unstructured>=0.11.0",
        "httpx>=0.25.0",
        "requests>=2.31.0",
    ]

# 开发依赖
dev_requirements = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]

setup(
    name="rag5-simplified",
    version="2.0.0",
    author="RAG5 Team",
    author_email="contact@rag5.example.com",
    description="基于检索增强生成(RAG)技术的本地化问答系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rag5-simplified",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/rag5-simplified/issues",
        "Documentation": "https://github.com/yourusername/rag5-simplified/blob/main/README.md",
        "Source Code": "https://github.com/yourusername/rag5-simplified",
    },
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "docs", "*.egg-info"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="rag, retrieval-augmented-generation, llm, langchain, ollama, qdrant, ai, nlp",
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rag5-ingest=scripts.ingest:main",
            "rag5-api=scripts.run_api:main",
            "rag5-ui=scripts.run_ui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "rag5": [
            "config/*.py",
            "core/**/*.py",
            "tools/**/*.py",
            "ingestion/**/*.py",
            "interfaces/**/*.py",
            "utils/*.py",
        ],
    },
    zip_safe=False,
    license="MIT",
)
