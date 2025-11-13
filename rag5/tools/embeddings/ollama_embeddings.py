"""
Ollama 嵌入模型管理模块

管理 Ollama 嵌入模型，提供文本向量化功能。
"""

import logging
import requests
from typing import List, Optional
from langchain_ollama import OllamaEmbeddings

from rag5.tools.vectordb.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class OllamaEmbeddingsManager:
    """
    Ollama 嵌入模型管理器

    管理 Ollama 嵌入模型，提供模型可用性检查和文本向量化功能。

    属性:
        model: 嵌入模型名称
        base_url: Ollama 服务地址
        embeddings: LangChain OllamaEmbeddings 实例

    示例:
        >>> from rag5.tools.embeddings import OllamaEmbeddingsManager
        >>>
        >>> manager = OllamaEmbeddingsManager(
        ...     model="bge-m3",
        ...     base_url="http://localhost:11434"
        ... )
        >>>
        >>> if manager.check_model_available():
        ...     vector = manager.embed_query("测试文本")
        ...     print(f"向量维度: {len(vector)}")
    """

    def __init__(self, model: str, base_url: str):
        """
        初始化嵌入模型管理器

        参数:
            model: 嵌入模型名称
            base_url: Ollama 服务地址
        """
        self.model = model
        self.base_url = base_url
        self._embeddings: Optional[OllamaEmbeddings] = None
        logger.debug(f"初始化嵌入模型管理器: model={model}, base_url={base_url}")

    def check_ollama_available(self) -> bool:
        """
        检查 Ollama 服务是否可用

        返回:
            Ollama 服务是否可用

        示例:
            >>> manager = OllamaEmbeddingsManager("bge-m3", "http://localhost:11434")
            >>> if manager.check_ollama_available():
            ...     print("Ollama 服务可用")
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.debug("Ollama 服务可用")
                return True
            else:
                logger.warning(f"Ollama 服务返回状态码: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"无法连接到 Ollama 服务: {e}")
            return False

    def check_model_available(self) -> bool:
        """
        检查嵌入模型是否可用

        返回:
            模型是否可用

        示例:
            >>> manager = OllamaEmbeddingsManager("bge-m3", "http://localhost:11434")
            >>> if manager.check_model_available():
            ...     print("模型可用")
            ... else:
            ...     print("请运行: ollama pull bge-m3")
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [m.get("name", "") for m in models]

                # 检查模型是否在列表中
                is_available = any(self.model in m for m in available_models)

                if is_available:
                    logger.debug(f"嵌入模型 '{self.model}' 可用")
                else:
                    logger.warning(
                        f"嵌入模型 '{self.model}' 不可用. "
                        f"可用模型: {', '.join(available_models)}"
                    )

                return is_available
            else:
                logger.warning(f"无法获取模型列表，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"检查模型可用性时出错: {e}")
            return False

    def initialize(self) -> None:
        """
        初始化嵌入模型

        异常:
            ConnectionError: Ollama 服务不可用
            ValueError: 嵌入模型不可用

        示例:
            >>> manager = OllamaEmbeddingsManager("bge-m3", "http://localhost:11434")
            >>> manager.initialize()
        """
        # 检查 Ollama 服务
        if not self.check_ollama_available():
            error_msg = (
                f"无法连接到 Ollama 服务 ({self.base_url}). "
                f"请确保 Ollama 正在运行: ollama serve"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg)

        # 检查模型
        if not self.check_model_available():
            error_msg = (
                f"嵌入模型 '{self.model}' 不可用. "
                f"请运行: ollama pull {self.model}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 初始化 LangChain 嵌入模型
        try:
            self._embeddings = OllamaEmbeddings(
                model=self.model,
                base_url=self.base_url
            )
            logger.info(f"✓ 初始化嵌入模型: {self.model}")
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {e}")
            raise

    @property
    def embeddings(self) -> OllamaEmbeddings:
        """
        获取嵌入模型实例

        如果模型未初始化，将自动初始化。

        返回:
            OllamaEmbeddings 实例

        异常:
            ConnectionError: Ollama 服务不可用
            ValueError: 嵌入模型不可用
        """
        if self._embeddings is None:
            self.initialize()
        return self._embeddings

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def embed_query(self, text: str) -> List[float]:
        """
        将查询文本转换为向量

        参数:
            text: 查询文本

        返回:
            向量（浮点数列表）

        异常:
            ValueError: 文本为空
            Exception: 向量化失败

        示例:
            >>> manager = OllamaEmbeddingsManager("bge-m3", "http://localhost:11434")
            >>> vector = manager.embed_query("什么是人工智能？")
            >>> print(f"向量维度: {len(vector)}")
        """
        if not text or not text.strip():
            raise ValueError("查询文本不能为空")

        try:
            import time
            start_time = time.time()
            
            text_preview = text[:100] if len(text) > 100 else text
            logger.debug(f"向量化查询文本: {text_preview}...")
            logger.debug(f"文本长度: {len(text)} 字符")
            logger.debug(f"使用模型: {self.model}")
            
            vector = self.embeddings.embed_query(text)
            
            embed_time = time.time() - start_time
            logger.debug(f"生成向量，维度: {len(vector)}")
            logger.debug(f"向量化耗时: {embed_time:.3f}秒")
            
            return vector
        except Exception as e:
            logger.error(f"向量化查询文本失败: {e}", exc_info=True)
            raise

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文档文本转换为向量

        参数:
            texts: 文档文本列表

        返回:
            向量列表

        异常:
            ValueError: 文本列表为空
            Exception: 向量化失败

        示例:
            >>> manager = OllamaEmbeddingsManager("bge-m3", "http://localhost:11434")
            >>> texts = ["文档1", "文档2", "文档3"]
            >>> vectors = manager.embed_documents(texts)
            >>> print(f"生成了 {len(vectors)} 个向量")
        """
        if not texts:
            raise ValueError("文档文本列表不能为空")

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("所有文档文本都为空")

        try:
            import time
            start_time = time.time()
            
            logger.debug(f"向量化 {len(valid_texts)} 个文档...")
            logger.debug(f"使用模型: {self.model}")
            
            # 计算文本统计
            total_chars = sum(len(t) for t in valid_texts)
            avg_chars = total_chars / len(valid_texts)
            logger.debug(f"文本统计 - 总字符: {total_chars}, 平均: {avg_chars:.0f} 字符/文档")
            
            vectors = self.embeddings.embed_documents(valid_texts)
            
            embed_time = time.time() - start_time
            logger.info(f"✓ 成功生成 {len(vectors)} 个向量")
            logger.debug(f"向量化耗时: {embed_time:.3f}秒")
            logger.debug(f"向量化速度: {len(vectors)/embed_time:.1f} 向量/秒")
            
            return vectors
        except Exception as e:
            logger.error(f"向量化文档失败: {e}", exc_info=True)
            raise

    def __repr__(self) -> str:
        """返回管理器的字符串表示"""
        status = "initialized" if self._embeddings else "not initialized"
        return f"<OllamaEmbeddingsManager(model='{self.model}', status='{status}')>"
