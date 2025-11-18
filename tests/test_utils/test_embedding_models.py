#!/usr/bin/env python
"""
测试嵌入模型配置工具
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from rag5.utils.embedding_models import (
    get_model_config,
    list_recommended_models,
    get_stable_alternative,
    print_model_comparison,
    normalize_model_name,
    is_embedding_model,
    resolve_embedding_dimension,
    build_fallback_model_infos,
    EMBEDDING_MODELS
)


def test_get_model_config():
    """测试获取模型配置"""
    print("\n测试 get_model_config:")

    # 测试获取 bge-m3 配置
    config = get_model_config("bge-m3:latest")
    assert config.model_name == "bge-m3"
    assert config.vector_dim == 1024
    assert config.stability == "unstable"
    assert config.recommended == False
    print("  ✓ bge-m3 配置正确")

    # 测试获取 nomic-embed-text 配置
    config = get_model_config("nomic-embed-text")
    assert config.model_name == "nomic-embed-text"
    assert config.vector_dim == 768
    assert config.stability == "stable"
    assert config.recommended == True
    print("  ✓ nomic-embed-text 配置正确")


def test_list_recommended_models():
    """测试获取推荐模型列表"""
    print("\n测试 list_recommended_models:")

    recommended = list_recommended_models()

    # bge-m3 不应该在推荐列表中
    assert "bge-m3" not in recommended
    print("  ✓ bge-m3 未在推荐列表中")

    # nomic-embed-text 应该在推荐列表中
    assert "nomic-embed-text" in recommended
    print("  ✓ nomic-embed-text 在推荐列表中")

    print(f"  推荐模型数量: {len(recommended)}")


def test_get_stable_alternative():
    """测试获取稳定替代模型"""
    print("\n测试 get_stable_alternative:")

    # bge-m3 应该推荐替代模型
    alternative = get_stable_alternative("bge-m3:latest")
    assert alternative == "nomic-embed-text"
    print("  ✓ bge-m3 推荐替代为 nomic-embed-text")

    # 稳定模型应该返回自己
    alternative = get_stable_alternative("nomic-embed-text")
    assert alternative == "nomic-embed-text"
    print("  ✓ nomic-embed-text 返回自己")


def test_model_count():
    """测试模型数量"""
    print("\n测试模型数量:")
    print(f"  总模型数: {len(EMBEDDING_MODELS)}")
    print(f"  推荐模型数: {len(list_recommended_models())}")


def test_normalize_model_name():
    """测试标准化模型名称"""
    print("\n测试 normalize_model_name:")

    assert normalize_model_name("bge-m3:latest") == "bge-m3"
    print("  ✓ bge-m3:latest -> bge-m3")

    assert normalize_model_name("nomic-embed-text") == "nomic-embed-text"
    print("  ✓ nomic-embed-text -> nomic-embed-text")


def test_is_embedding_model():
    """测试嵌入模型判断"""
    print("\n测试 is_embedding_model:")

    assert is_embedding_model("bge-m3") == True
    print("  ✓ bge-m3 是嵌入模型")

    assert is_embedding_model("nomic-embed-text") == True
    print("  ✓ nomic-embed-text 是嵌入模型")

    assert is_embedding_model("llama2") == False
    print("  ✓ llama2 不是嵌入模型")


def test_resolve_embedding_dimension():
    """测试解析嵌入维度"""
    print("\n测试 resolve_embedding_dimension:")

    assert resolve_embedding_dimension("nomic-embed-text") == 768
    print("  ✓ nomic-embed-text 维度为 768")

    assert resolve_embedding_dimension("bge-m3") == 1024
    print("  ✓ bge-m3 维度为 1024")

    assert resolve_embedding_dimension("unknown-model", 512) == 512
    print("  ✓ unknown-model 使用默认维度 512")


def test_build_fallback_model_infos():
    """测试构建回退模型信息"""
    print("\n测试 build_fallback_model_infos:")

    infos = build_fallback_model_infos(768, ["nomic-embed-text"])
    assert len(infos) > 0
    print(f"  ✓ 生成了 {len(infos)} 个回退模型信息")

    # 检查第一个模型是默认模型
    assert infos[0]["name"] == "nomic-embed-text"
    assert infos[0]["dimension"] == 768
    print("  ✓ 默认模型在列表首位")


if __name__ == "__main__":
    print("="*60)
    print("测试嵌入模型配置工具")
    print("="*60)

    try:
        test_get_model_config()
        test_list_recommended_models()
        test_get_stable_alternative()
        test_model_count()
        test_normalize_model_name()
        test_is_embedding_model()
        test_resolve_embedding_dimension()
        test_build_fallback_model_infos()

        print("\n" + "="*60)
        print("✓ 所有测试通过!")
        print("="*60)

        # 打印模型对比表
        print_model_comparison()

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
