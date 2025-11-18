#!/usr/bin/env python
"""
嵌入模型配置和切换工具

提供多种嵌入模型的标准化配置,方便用户根据需求选择合适的模型。
"""

from dataclasses import dataclass
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingModelConfig:
    """嵌入模型配置"""
    model_name: str          # Ollama 模型名称
    vector_dim: int          # 向量维度
    model_size_mb: float     # 模型大小(MB)
    description: str         # 模型描述
    stability: str           # 稳定性评级: stable, unstable
    performance: str         # 性能评级: fast, medium, slow
    quality: str             # 质量评级: high, medium, low
    recommended: bool        # 是否推荐用于生产环境


# 支持的嵌入模型配置
EMBEDDING_MODELS: Dict[str, EmbeddingModelConfig] = {
    "nomic-embed-text": EmbeddingModelConfig(
        model_name="nomic-embed-text",
        vector_dim=768,
        model_size_mb=274,
        description="Nomic AI 的高质量文本嵌入模型,平衡了性能、质量和稳定性",
        stability="stable",
        performance="fast",
        quality="medium-high",
        recommended=True
    ),

    "mxbai-embed-large": EmbeddingModelConfig(
        model_name="mxbai-embed-large",
        vector_dim=1024,
        model_size_mb=670,
        description="MixedBread AI 的大型嵌入模型,高质量但较慢",
        stability="stable",
        performance="medium",
        quality="high",
        recommended=True
    ),

    "all-minilm": EmbeddingModelConfig(
        model_name="all-minilm",
        vector_dim=384,
        model_size_mb=23,
        description="微软的轻量级模型,速度极快但质量中等",
        stability="stable",
        performance="fast",
        quality="medium",
        recommended=True
    ),

    "bge-m3": EmbeddingModelConfig(
        model_name="bge-m3",
        vector_dim=1024,
        model_size_mb=567,
        description="BAAI 的多语言嵌入模型,质量高但在某些 Ollama 版本中不稳定",
        stability="unstable",
        performance="slow",
        quality="high",
        recommended=False
    ),

    "bge-large": EmbeddingModelConfig(
        model_name="bge-large",
        vector_dim=1024,
        model_size_mb=1340,
        description="BAAI 的大型嵌入模型,高质量",
        stability="stable",
        performance="medium",
        quality="high",
        recommended=True
    ),
}


def get_model_config(model_name: str) -> EmbeddingModelConfig:
    """
    获取指定模型的配置

    Args:
        model_name: 模型名称(可以包含 :latest 等标签)

    Returns:
        模型配置对象

    Raises:
        ValueError: 如果模型未找到
    """
    # 移除版本标签(如 :latest)
    base_model_name = model_name.split(":")[0]

    if base_model_name not in EMBEDDING_MODELS:
        raise ValueError(
            f"未知的嵌入模型: {model_name}\n"
            f"支持的模型: {', '.join(EMBEDDING_MODELS.keys())}"
        )

    return EMBEDDING_MODELS[base_model_name]


def list_recommended_models() -> Dict[str, EmbeddingModelConfig]:
    """获取所有推荐用于生产环境的模型"""
    return {
        name: config
        for name, config in EMBEDDING_MODELS.items()
        if config.recommended
    }


def get_stable_alternative(current_model: str) -> str:
    """
    如果当前模型不稳定,推荐一个稳定的替代模型

    Args:
        current_model: 当前使用的模型名称

    Returns:
        推荐的替代模型名称,如果当前模型已经稳定则返回当前模型
    """
    try:
        config = get_model_config(current_model)

        if config.stability == "stable":
            logger.info(f"当前模型 {current_model} 已经是稳定模型")
            return current_model

        # 优先推荐 nomic-embed-text
        logger.warning(
            f"当前模型 {current_model} 标记为不稳定\n"
            f"推荐切换到 nomic-embed-text (稳定、快速、高质量)"
        )
        return "nomic-embed-text"

    except ValueError:
        # 未知模型,推荐默认安全选项
        logger.warning(f"未知模型 {current_model},推荐使用 nomic-embed-text")
        return "nomic-embed-text"


def normalize_model_name(model_name: str) -> str:
    """
    标准化模型名称(移除版本标签)

    Args:
        model_name: 原始模型名称(如 "bge-m3:latest")

    Returns:
        标准化的模型名称(如 "bge-m3")

    Example:
        >>> normalize_model_name("bge-m3:latest")
        'bge-m3'
        >>> normalize_model_name("nomic-embed-text")
        'nomic-embed-text'
    """
    return model_name.split(":")[0]


def is_embedding_model(model_name: str, family: str = "") -> bool:
    """
    判断一个模型是否是嵌入模型

    Args:
        model_name: 模型名称
        family: 模型家族(可选)

    Returns:
        是否是嵌入模型

    Example:
        >>> is_embedding_model("bge-m3")
        True
        >>> is_embedding_model("llama2")
        False
    """
    base_name = normalize_model_name(model_name)

    # 检查是否在已知的嵌入模型列表中
    if base_name in EMBEDDING_MODELS:
        return True

    # 通过名称模式判断
    embedding_patterns = [
        "embed", "embedding", "bge", "nomic", "mxbai", "minilm",
        "e5", "instructor", "gte", "retrieval"
    ]

    model_lower = base_name.lower()
    for pattern in embedding_patterns:
        if pattern in model_lower:
            return True

    # 通过家族名称判断
    if family:
        family_lower = family.lower()
        if "embed" in family_lower or "bert" in family_lower:
            return True

    return False


def resolve_embedding_dimension(model_name: str, default_dimension: int = 1024) -> int:
    """
    解析模型的嵌入维度

    Args:
        model_name: 模型名称
        default_dimension: 默认维度(如果无法确定)

    Returns:
        模型的向量维度

    Example:
        >>> resolve_embedding_dimension("nomic-embed-text")
        768
        >>> resolve_embedding_dimension("bge-m3")
        1024
        >>> resolve_embedding_dimension("unknown-model", 512)
        512
    """
    base_name = normalize_model_name(model_name)

    try:
        config = get_model_config(base_name)
        return config.vector_dim
    except ValueError:
        # 未知模型,返回默认维度
        logger.debug(f"未知模型 {model_name},使用默认维度 {default_dimension}")
        return default_dimension


def build_fallback_model_infos(default_dimension: int, default_models: List[str]) -> List[Dict]:
    """
    构建回退模型信息列表(当无法从 Ollama 获取模型列表时使用)

    Args:
        default_dimension: 默认向量维度
        default_models: 默认模型列表

    Returns:
        模型信息字典列表

    Example:
        >>> infos = build_fallback_model_infos(768, ["nomic-embed-text"])
        >>> len(infos) > 0
        True
    """
    fallback_infos = []

    # 首先添加默认模型
    for model_name in default_models:
        base_name = normalize_model_name(model_name)

        try:
            config = get_model_config(base_name)
            fallback_infos.append({
                "name": model_name,
                "display_name": model_name,
                "family": "embedding",
                "dimension": config.vector_dim,
                "tags": []
            })
        except ValueError:
            # 未知模型,使用默认维度
            fallback_infos.append({
                "name": model_name,
                "display_name": model_name,
                "family": "unknown",
                "dimension": default_dimension,
                "tags": []
            })

    # 然后添加所有推荐的嵌入模型
    for name, config in list_recommended_models().items():
        # 避免重复
        if name not in default_models:
            fallback_infos.append({
                "name": name,
                "display_name": f"{name} (推荐)",
                "family": "embedding",
                "dimension": config.vector_dim,
                "tags": [config.stability, config.performance]
            })

    return fallback_infos


def print_model_comparison():
    """打印所有支持模型的对比表格"""
    print("\n" + "="*80)
    print("支持的嵌入模型对比")
    print("="*80)
    print(f"{'模型名称':<25} {'维度':<6} {'大小':<8} {'稳定性':<8} {'性能':<8} {'质量':<10} {'推荐':<4}")
    print("-"*80)

    for name, config in EMBEDDING_MODELS.items():
        recommended_mark = "✓" if config.recommended else "✗"
        print(
            f"{config.model_name:<25} "
            f"{config.vector_dim:<6} "
            f"{config.model_size_mb:<8.0f} "
            f"{config.stability:<8} "
            f"{config.performance:<8} "
            f"{config.quality:<10} "
            f"{recommended_mark:<4}"
        )

    print("="*80)
    print("\n推荐模型:")
    for name, config in list_recommended_models().items():
        print(f"  • {name}: {config.description}")
    print()


if __name__ == "__main__":
    # 演示模型对比
    print_model_comparison()

    # 测试获取配置
    print("\n测试获取 bge-m3 配置:")
    config = get_model_config("bge-m3:latest")
    print(f"  模型: {config.model_name}")
    print(f"  维度: {config.vector_dim}")
    print(f"  稳定性: {config.stability}")
    print(f"  推荐: {'是' if config.recommended else '否'}")

    # 测试获取替代模型
    print("\n测试获取 bge-m3 的稳定替代模型:")
    alternative = get_stable_alternative("bge-m3:latest")
    print(f"  推荐替代: {alternative}")
