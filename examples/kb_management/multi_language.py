"""
Multi-Language Knowledge Base Example

This example demonstrates creating separate knowledge bases for different languages,
each with an appropriate embedding model.

Supported languages:
- English
- Chinese
- Japanese (if model available)

Run this example:
    python examples/kb_management/multi_language.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rag5.core.knowledge_base import KnowledgeBaseManager, initialize_kb_system
from rag5.core.knowledge_base.models import ChunkConfig, RetrievalConfig
from rag5.core.knowledge_base.vector_manager import VectorStoreManager
from rag5.config import settings
from qdrant_client import QdrantClient


async def create_english_kb(manager: KnowledgeBaseManager):
    """Create knowledge base for English documents"""
    print("\n🇺🇸 Creating English KB...")
    
    kb = await manager.create_knowledge_base(
        name="docs_en",
        description="English documentation and content",
        embedding_model="nomic-embed-text",  # Excellent for English
        chunk_config=ChunkConfig(
            chunk_size=512,
            chunk_overlap=50,
            parser_type="sentence"
        ),
        retrieval_config=RetrievalConfig(
            retrieval_mode="hybrid",
            top_k=5,
            similarity_threshold=0.3
        )
    )
    
    print(f"✓ English KB created: {kb.id}")
    print(f"  Model: {kb.embedding_model}")
    
    return kb


async def create_chinese_kb(manager: KnowledgeBaseManager):
    """Create knowledge base for Chinese documents"""
    print("\n🇨🇳 Creating Chinese KB...")
    
    kb = await manager.create_knowledge_base(
        name="docs_zh",
        description="中文文档和内容",
        embedding_model="bge-m3",  # Good for Chinese
        chunk_config=ChunkConfig(
            chunk_size=512,
            chunk_overlap=50,
            parser_type="sentence"
        ),
        retrieval_config=RetrievalConfig(
            retrieval_mode="hybrid",
            top_k=5,
            similarity_threshold=0.3
        )
    )
    
    print(f"✓ Chinese KB created: {kb.id}")
    print(f"  Model: {kb.embedding_model}")
    
    return kb


async def create_sample_documents(manager: KnowledgeBaseManager, kbs: dict):
    """Create sample documents in different languages"""
    print("\n📄 Creating sample documents...")
    
    docs_dir = Path(settings.file_storage_path)
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # English document
    en_doc = docs_dir / "sample_en.txt"
    en_doc.write_text("""
    Introduction to Machine Learning
    
    Machine learning is a branch of artificial intelligence that focuses on building
    applications that learn from data and improve their accuracy over time without
    being programmed to do so.
    
    Types of Machine Learning:
    
    1. Supervised Learning
    In supervised learning, the algorithm learns from labeled training data. The model
    is trained on a dataset where the correct output is already known.
    
    2. Unsupervised Learning
    Unsupervised learning works with unlabeled data. The algorithm tries to find
    patterns and relationships in the data without any guidance.
    
    3. Reinforcement Learning
    Reinforcement learning is about taking suitable action to maximize reward in a
    particular situation. The agent learns through trial and error.
    
    Applications:
    - Image recognition
    - Natural language processing
    - Recommendation systems
    - Autonomous vehicles
    """)
    
    # Chinese document
    zh_doc = docs_dir / "sample_zh.txt"
    zh_doc.write_text("""
    机器学习简介
    
    机器学习是人工智能的一个分支，专注于构建能够从数据中学习并随着时间推移提高准确性的应用程序，
    而无需明确编程。
    
    机器学习的类型：
    
    1. 监督学习
    在监督学习中，算法从标记的训练数据中学习。模型在已知正确输出的数据集上进行训练。
    
    2. 无监督学习
    无监督学习处理未标记的数据。算法尝试在没有任何指导的情况下找到数据中的模式和关系。
    
    3. 强化学习
    强化学习是关于采取适当的行动以在特定情况下最大化奖励。代理通过试错来学习。
    
    应用领域：
    - 图像识别
    - 自然语言处理
    - 推荐系统
    - 自动驾驶汽车
    """)
    
    print("✓ Sample documents created")
    
    # Upload documents
    print("\n📤 Uploading documents...")
    
    # Upload English document
    print("  Uploading English document...")
    en_file = await manager.upload_file(
        kb_id=kbs["en"].id,
        file_path=str(en_doc)
    )
    await manager.process_file(en_file.id)
    print(f"  ✓ {en_doc.name} processed")
    
    # Upload Chinese document
    print("  Uploading Chinese document...")
    zh_file = await manager.upload_file(
        kb_id=kbs["zh"].id,
        file_path=str(zh_doc)
    )
    await manager.process_file(zh_file.id)
    print(f"  ✓ {zh_doc.name} processed")
    
    return {"en": en_doc, "zh": zh_doc}


async def demonstrate_language_queries(manager: KnowledgeBaseManager, kbs: dict):
    """Demonstrate querying in different languages"""
    print("\n🔍 Demonstrating language-specific queries...")
    
    # English queries
    print("\n" + "=" * 60)
    print("English Queries")
    print("=" * 60)
    
    en_queries = [
        "What is supervised learning?",
        "What are the applications of machine learning?"
    ]
    
    for query in en_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        results = await manager.query_knowledge_base(
            kb_id=kbs["en"].id,
            query=query,
            top_k=2
        )
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"  Score: {result['score']:.4f}")
                print(f"  Content: {result['content'][:150]}...")
        else:
            print("  No results found")
    
    # Chinese queries
    print("\n" + "=" * 60)
    print("Chinese Queries (中文查询)")
    print("=" * 60)
    
    zh_queries = [
        "什么是监督学习？",
        "机器学习有哪些应用？"
    ]
    
    for query in zh_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        results = await manager.query_knowledge_base(
            kb_id=kbs["zh"].id,
            query=query,
            top_k=2
        )
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"  Score: {result['score']:.4f}")
                print(f"  Content: {result['content'][:150]}...")
        else:
            print("  No results found")


async def demonstrate_cross_language_isolation(manager: KnowledgeBaseManager, kbs: dict):
    """Demonstrate that language KBs are isolated"""
    print("\n🔒 Demonstrating language isolation...")
    print("\nQuerying English KB with Chinese query:")
    print("(Should have lower relevance scores)")
    
    query = "什么是机器学习？"  # "What is machine learning?" in Chinese
    
    print(f"\nQuery: {query}")
    print(f"Target: English KB")
    print("-" * 60)
    
    results = await manager.query_knowledge_base(
        kb_id=kbs["en"].id,
        query=query,
        top_k=2
    )
    
    if results:
        print(f"Found {len(results)} result(s) (may have lower scores)")
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Score: {result['score']:.4f}")
    else:
        print("No results found (expected due to language mismatch)")
    
    print("\n" + "-" * 60)
    print("Querying Chinese KB with English query:")
    print("(Should have lower relevance scores)")
    
    query = "What is machine learning?"
    
    print(f"\nQuery: {query}")
    print(f"Target: Chinese KB")
    print("-" * 60)
    
    results = await manager.query_knowledge_base(
        kb_id=kbs["zh"].id,
        query=query,
        top_k=2
    )
    
    if results:
        print(f"Found {len(results)} result(s) (may have lower scores)")
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Score: {result['score']:.4f}")
    else:
        print("No results found (expected due to language mismatch)")


async def main():
    print("=" * 60)
    print("Multi-Language Knowledge Base Example")
    print("=" * 60)
    
    # Initialize system
    print("\n🚀 Initializing system...")
    db, _ = initialize_kb_system(
        db_path=settings.kb_database_path,
        create_default=True
    )
    
    qdrant_client = QdrantClient(url=settings.qdrant_url)
    vector_manager = VectorStoreManager(qdrant_client)
    
    manager = KnowledgeBaseManager(
        db_path=settings.kb_database_path,
        vector_manager=vector_manager,
        file_storage_path=settings.file_storage_path
    )
    print("✓ System initialized")
    
    # Create language-specific KBs
    print("\n" + "=" * 60)
    print("Creating Language-Specific Knowledge Bases")
    print("=" * 60)
    
    en_kb = await create_english_kb(manager)
    zh_kb = await create_chinese_kb(manager)
    
    kbs = {
        "en": en_kb,
        "zh": zh_kb
    }
    
    # Create and upload sample documents
    print("\n" + "=" * 60)
    print("Creating and Uploading Sample Documents")
    print("=" * 60)
    
    docs = await create_sample_documents(manager, kbs)
    
    # Demonstrate queries
    await demonstrate_language_queries(manager, kbs)
    
    # Demonstrate isolation
    print("\n" + "=" * 60)
    print("Demonstrating Language Isolation")
    print("=" * 60)
    
    await demonstrate_cross_language_isolation(manager, kbs)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    print("\nLanguage-specific knowledge bases allow you to:")
    print("  ✓ Use optimal embedding models for each language")
    print("  ✓ Maintain language isolation")
    print("  ✓ Improve search relevance")
    print("  ✓ Support multilingual applications")
    
    print("\nCreated Knowledge Bases:")
    for lang, kb in kbs.items():
        kb_info = await manager.get_knowledge_base(kb.id)
        print(f"\n{lang.upper()} KB:")
        print(f"  ID: {kb_info.id}")
        print(f"  Name: {kb_info.name}")
        print(f"  Model: {kb_info.embedding_model}")
        print(f"  Documents: {kb_info.document_count}")
    
    # Cleanup
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)
    
    cleanup = input("\nDo you want to delete all example KBs? (y/n): ")
    
    if cleanup.lower() == 'y':
        for kb in kbs.values():
            await manager.delete_knowledge_base(kb_id=kb.id)
        print("✓ Deleted all language KBs")
        
        # Delete sample files
        for doc in docs.values():
            if doc.exists():
                doc.unlink()
        print("✓ Deleted sample documents")
    else:
        print("✓ Knowledge bases preserved")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
