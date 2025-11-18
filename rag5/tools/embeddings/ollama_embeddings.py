"""
Ollama 嵌入模型管理模块

使用 Ollama API 提供文本向量化功能。
参考 LM Studio 实现，提供简洁可靠的嵌入服务。
"""

import logging
import requests
from typing import List
import time

logger = logging.getLogger(__name__)


class OllamaEmbeddingsManager:
    """Ollama 嵌入模型管理器"""

    def __init__(
        self,
        model: str = "bge-m3",
        base_url: str = "http://localhost:11434",
        batch_size: int = 10
    ):
        """
        初始化 Ollama 嵌入管理器

        参数:
            model: Ollama 中加载的模型名称
            base_url: Ollama API 地址
            batch_size: 批次大小
        """
        self.model = model
        # 标准化 base_url - 移除尾部斜杠
        self.base_url = base_url.rstrip('/')
        self.batch_size = batch_size
        self.embeddings_url = f"{self.base_url}/api/embed"

        logger.info(f"初始化 Ollama 嵌入管理器: model={model}, embeddings_url={self.embeddings_url}")

    def check_ollama_available(self) -> bool:
        """
        检查 Ollama 服务是否可用

        返回:
            Ollama 服务是否可用
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Ollama 服务可用")
                return True
            else:
                logger.warning(f"Ollama 服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"无法连接到 Ollama: {e}")
            return False

    def check_model_available(self) -> bool:
        """
        检查嵌入模型是否可用

        返回:
            模型是否可用
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
        初始化嵌入模型(验证 Ollama 服务和模型可用性)

        异常:
            ConnectionError: Ollama 服务不可用
            ValueError: 嵌入模型不可用
        """
        if not self.check_ollama_available():
            raise ConnectionError(
                f"Ollama 服务不可用: {self.base_url}\n"
                f"请确保 Ollama 正在运行: ollama serve"
            )

        if not self.check_model_available():
            raise ValueError(
                f"嵌入模型 '{self.model}' 不可用\n"
                f"请运行: ollama pull {self.model}"
            )

        logger.info(f"✓ Ollama 嵌入模型验证通过: {self.model}")

    def embed_query(self, text: str) -> List[float]:
        """
        将查询文本转换为向量

        参数:
            text: 查询文本

        返回:
            向量（浮点数列表）
        """
        start_time = time.time()

        try:
            payload = {
                "model": self.model,
                "input": text
            }

            response = requests.post(
                self.embeddings_url,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                # Ollama 返回格式: {"embeddings": [[...]]}
                embeddings = result.get('embeddings', [])
                if not embeddings or len(embeddings) == 0:
                    raise ValueError("Ollama 返回空嵌入列表")

                vector = embeddings[0]

                elapsed = time.time() - start_time
                logger.debug(
                    f"生成查询向量成功，维度: {len(vector)}，"
                    f"耗时: {elapsed:.3f}秒"
                )

                return vector
            else:
                error_msg = f"Ollama API 错误: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", {error_detail}"
                except:
                    error_msg += f", {response.text}"

                logger.error(error_msg)
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"查询嵌入失败: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文档文本转换为向量

        参数:
            texts: 文档文本列表

        返回:
            向量列表
        """
        if not texts:
            raise ValueError("文档文本列表不能为空")

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("所有文档文本都为空")

        total_docs = len(valid_texts)
        batch_size = self.batch_size
        total_batches = (total_docs + batch_size - 1) // batch_size

        logger.info(
            f"使用 Ollama 嵌入 {total_docs} 个文档，"
            f"批次大小: {batch_size}, 批次数量: {total_batches}"
        )

        vectors: List[List[float]] = []
        start_time = time.time()

        for batch_index, start_idx in enumerate(range(0, total_docs, batch_size), start=1):
            batch = valid_texts[start_idx:start_idx + batch_size]
            batch_start = time.time()

            logger.debug(f"处理批次 {batch_index}/{total_batches}, 文档数: {len(batch)}")

            try:
                payload = {
                    "model": self.model,
                    "input": batch
                }

                logger.debug(f"发送请求到 Ollama: {len(batch)} 个文本")

                response = requests.post(
                    self.embeddings_url,
                    json=payload,
                    timeout=120
                )

                logger.debug(f"收到响应，状态码: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        logger.debug(f"Ollama 响应键: {list(result.keys())}")
                    except Exception as json_err:
                        logger.error(f"JSON 解析失败: {json_err}")
                        logger.error(f"响应内容: {response.text[:500]}")
                        raise RuntimeError(f"无法解析 Ollama 响应: {json_err}")

                    # 检查响应格式 - Ollama 使用 "embeddings" 而不是 "data"
                    if 'embeddings' not in result:
                        logger.error(f"响应缺少 'embeddings' 字段。完整响应: {result}")
                        raise RuntimeError(f"Ollama 响应格式错误: 缺少 'embeddings' 字段")

                    batch_vectors = result['embeddings']

                    if len(batch_vectors) != len(batch):
                        raise ValueError(
                            f"返回向量数量 ({len(batch_vectors)}) 与文档数量 ({len(batch)}) 不匹配"
                        )

                    vectors.extend(batch_vectors)

                    batch_time = time.time() - batch_start
                    logger.debug(
                        f"批次 {batch_index} 完成，耗时: {batch_time:.3f}秒，"
                        f"速度: {len(batch)/batch_time:.1f} 文档/秒"
                    )
                else:
                    error_msg = f"批次 {batch_index} 失败: HTTP {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f", 详情: {error_detail}"
                    except:
                        error_msg += f", 响应: {response.text[:200]}"

                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            except requests.exceptions.RequestException as req_err:
                logger.error(f"批次 {batch_index} 网络请求失败: {req_err}")
                raise
            except Exception as e:
                logger.error(f"批次 {batch_index} 嵌入失败: {e}", exc_info=True)
                raise

        total_time = time.time() - start_time
        logger.info(
            f"✓ Ollama 嵌入完成，生成 {len(vectors)} 个向量，"
            f"总耗时: {total_time:.2f}秒，平均速度: {len(vectors)/total_time:.2f} 向量/秒"
        )

        return vectors

    def __repr__(self) -> str:
        """返回管理器的字符串表示"""
        return f"<OllamaEmbeddingsManager(model='{self.model}', base_url='{self.base_url}')>"
