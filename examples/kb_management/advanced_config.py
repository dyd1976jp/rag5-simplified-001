"""
Advanced Configuration Example

This example demonstrates advanced configuration options for knowledge bases:
- Different chunking strategies
- Various retrieval modes
- Reranking configuration
- Performance tuning

Run this example:
    python examples/kb_management/advanced_config.py
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


async def demonstrate_chunking_strategies(manager: KnowledgeBaseManager):
    """Demonstrate different chunking strategies"""
    print("\n" + "=" * 60)
    print("Chunking Strategies")
    print("=" * 60)
    
    strategies = [
        {
            "name": "small_chunks",
            "description": "Small chunks for precise matching",
            "config": ChunkConfig(
                chunk_size=256,
                chunk_overlap=25,
                parser_type="sentence"
            )
        },
        {
            "name": "large_chunks",
            "description": "Large chunks for more context",
            "config": ChunkConfig(
                chunk_size=1024,
                chunk_overlap=100,
                parser_type="recursive"
            )
        },
        {
            "name": "semantic_chunks",
            "description": "Semantic-based chunking (experimental)",
            "config": ChunkConfig(
                chunk_size=512,
                chunk_overlap=50,
                parser_type="semantic"
            )
        }
    ]
    
    kbs = {}
    
    for strategy in strategies:
        print(f"\n📦 Creating KB with {strategy['name']}...")
        print(f"   {strategy['description']}")
        
        kb = await manager.create_knowledge_base(
            name=f"kb_{strategy['name']}",
            description=strategy['description'],
            embedding_model="nomic-embed-text",
            chunk_config=strategy['config']
        )
        
        print(f"   ✓ Created: {kb.id}")
        print(f"     Chunk size: {kb.chunk_config.chunk_size}")
        print(f"     Overlap: {kb.chunk_config.chunk_overlap}")
        print(f"     Parser: {kb.chunk_config.parser_type}")
        
        kbs[strategy['name']] = kb
    
    return kbs


async def demonstrate_retrieval_modes(manager: KnowledgeBaseManager):
    """Demonstrate different retrieval modes"""
    print("\n" + "=" * 60)
    print("Retrieval Modes")
    print("=" * 60)
    
    modes = [
        {
            "name": "vector_only",
            "description": "Pure semantic search",
            "config": RetrievalConfig(
                retrieval_mode="vector",
                top_k=5,
                similarity_threshold=0.3
            )
        },
        {
            "name": "fulltext_only",
            "description": "Keyword-based search",
            "config": RetrievalConfig(
                retrieval_mode="fulltext",
                top_k=5,
                similarity_threshold=0.3
            )
        },
        {
            "name": "hybrid_balanced",
            "description": "Balanced hybrid search",
            "config": RetrievalConfig(
                retrieval_mode="hybrid",
                top_k=5,
                similarity_threshold=0.3,
                vector_weight=0.5
            )
        },
        {
            "name": "hybrid_semantic",
            "description": "Semantic-focused hybrid",
            "config": RetrievalConfig(
                retrieval_mode="hybrid",
                top_k=5,
                similarity_threshold=0.3,
                vector_weight=0.7  # Favor semantic
            )
        }
    ]
    
    kbs = {}
    
    for mode in modes:
        print(f"\n🔍 Creating KB with {mode['name']}...")
        print(f"   {mode['description']}")
        
        kb = await manager.create_knowledge_base(
            name=f"kb_{mode['name']}",
            description=mode['description'],
            embedding_model="nomic-embed-text",
            retrieval_config=mode['config']
        )
        
        print(f"   ✓ Created: {kb.id}")
        print(f"     Mode: {kb.retrieval_config.retrieval_mode}")
        print(f"     Top K: {kb.retrieval_config.top_k}")
        print(f"     Threshold: {kb.retrieval_config.similarity_threshold}")
        if kb.retrieval_config.retrieval_mode == "hybrid":
            print(f"     Vector weight: {kb.retrieval_config.vector_weight}")
        
        kbs[mode['name']] = kb
    
    return kbs


async def demonstrate_precision_tuning(manager: KnowledgeBaseManager):
    """Demonstrate precision vs recall tuning"""
    print("\n" + "=" * 60)
    print("Precision vs Recall Tuning")
    print("=" * 60)
    
    configs = [
        {
            "name": "high_precision",
            "description": "Few but highly relevant results",
            "config": RetrievalConfig(
                retrieval_mode="vector",
                top_k=3,
                similarity_threshold=0.6,  # High threshold
                enable_rerank=True
            )
        },
        {
            "name": "balanced",
            "description": "Balanced precision and recall",
            "config": RetrievalConfig(
                retrieval_mode="hybrid",
                top_k=5,
                similarity_threshold=0.3,  # Medium threshold
                vector_weight=0.5
            )
        },
        {
            "name": "high_recall",
            "description": "Many results for exploration",
            "config": RetrievalConfig(
                retrieval_mode="hybrid",
                top_k=20,
                similarity_threshold=0.2,  # Low threshold
                vector_weight=0.5
            )
        }
    ]
    
    kbs = {}
    
    for config in configs:
        print(f"\n⚖️  Creating KB with {config['name']}...")
        print(f"   {config['description']}")
        
        kb = await manager.create_knowledge_base(
            name=f"kb_{config['name']}",
            description=config['description'],
            embedding_model="nomic-embed-text",
            retrieval_config=config['config']
        )
        
        print(f"   ✓ Created: {kb.id}")
        print(f"     Top K: {kb.retrieval_config.top_k}")
        print(f"     Threshold: {kb.retrieval_config.similarity_threshold}")
        print(f"     Rerank: {kb.retrieval_config.enable_rerank}")
        
        kbs[config['name']] = kb
    
    return kbs


async def demonstrate_configuration_updates(manager: KnowledgeBaseManager):
    """Demonstrate updating KB configuration"""
    print("\n" + "=" * 60)
    print("Configuration Updates")
    print("=" * 60)
    
    # Create a KB
    print("\n📝 Creating initial KB...")
    kb = await manager.create_knowledge_base(
        name="kb_updateable",
        description="Initial configuration",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(
            chunk_size=512,
            chunk_overlap=50
        ),
        retrieval_config=RetrievalConfig(
            top_k=5,
            similarity_threshold=0.3
        )
    )
    
    print(f"✓ Created: {kb.id}")
    print(f"  Initial top_k: {kb.retrieval_config.top_k}")
    print(f"  Initial threshold: {kb.retrieval_config.similarity_threshold}")
    
    # Update retrieval config
    print("\n🔄 Updating retrieval configuration...")
    updated_kb = await manager.update_knowledge_base(
        kb_id=kb.id,
        retrieval_config=RetrievalConfig(
            top_k=10,  # Increased
            similarity_threshold=0.4,  # Increased
            enable_rerank=True  # Enabled
        )
    )
    
    print(f"✓ Updated: {updated_kb.id}")
    print(f"  New top_k: {updated_kb.retrieval_config.top_k}")
    print(f"  New threshold: {updated_kb.retrieval_config.similarity_threshold}")
    print(f"  Reranking: {updated_kb.retrieval_config.enable_rerank}")
    
    # Update description
    print("\n📝 Updating description...")
    updated_kb = await manager.update_knowledge_base(
        kb_id=kb.id,
        description="Updated configuration with reranking"
    )
    
    print(f"✓ Description updated: {updated_kb.description}")
    
    return kb


async def demonstrate_performance_configs(manager: KnowledgeBaseManager):
    """Demonstrate performance-optimized configurations"""
    print("\n" + "=" * 60)
    print("Performance-Optimized Configurations")
    print("=" * 60)
    
    configs = [
        {
            "name": "speed_optimized",
            "description": "Optimized for query speed",
            "chunk_config": ChunkConfig(
                chunk_size=512,
                chunk_overlap=50,
                parser_type="sentence"  # Fastest
            ),
            "retrieval_config": RetrievalConfig(
                retrieval_mode="vector",  # Fastest mode
                top_k=5,
                similarity_threshold=0.4,  # Higher threshold = fewer results
                enable_rerank=False  # No reranking overhead
            )
        },
        {
            "name": "quality_optimized",
            "description": "Optimized for result quality",
            "chunk_config": ChunkConfig(
                chunk_size=768,
                chunk_overlap=100,
                parser_type="semantic"  # Better boundaries
            ),
            "retrieval_config": RetrievalConfig(
                retrieval_mode="hybrid",  # Best accuracy
                top_k=20,
                similarity_threshold=0.2,  # Lower threshold = more results
                enable_rerank=True,  # Rerank for quality
                vector_weight=0.6
            )
        },
        {
            "name": "memory_optimized",
            "description": "Optimized for low memory usage",
            "chunk_config": ChunkConfig(
                chunk_size=256,  # Smaller chunks
                chunk_overlap=25,
                parser_type="sentence"
            ),
            "retrieval_config": RetrievalConfig(
                retrieval_mode="vector",
                top_k=3,  # Fewer results
                similarity_threshold=0.5,
                enable_rerank=False
            )
        }
    ]
    
    kbs = {}
    
    for config in configs:
        print(f"\n⚡ Creating {config['name']} KB...")
        print(f"   {config['description']}")
        
        kb = await manager.create_knowledge_base(
            name=f"kb_{config['name']}",
            description=config['description'],
            embedding_model="nomic-embed-text",
            chunk_config=config['chunk_config'],
            retrieval_config=config['retrieval_config']
        )
        
        print(f"   ✓ Created: {kb.id}")
        print(f"     Chunk size: {kb.chunk_config.chunk_size}")
        print(f"     Retrieval mode: {kb.retrieval_config.retrieval_mode}")
        print(f"     Top K: {kb.retrieval_config.top_k}")
        print(f"     Reranking: {kb.retrieval_config.enable_rerank}")
        
        kbs[config['name']] = kb
    
    return kbs


async def main():
    print("=" * 60)
    print("Advanced Configuration Example")
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
    
    all_kbs = []
    
    # Demonstrate chunking strategies
    chunking_kbs = await demonstrate_chunking_strategies(manager)
    all_kbs.extend(chunking_kbs.values())
    
    # Demonstrate retrieval modes
    retrieval_kbs = await demonstrate_retrieval_modes(manager)
    all_kbs.extend(retrieval_kbs.values())
    
    # Demonstrate precision tuning
    precision_kbs = await demonstrate_precision_tuning(manager)
    all_kbs.extend(precision_kbs.values())
    
    # Demonstrate configuration updates
    update_kb = await demonstrate_configuration_updates(manager)
    all_kbs.append(update_kb)
    
    # Demonstrate performance configs
    performance_kbs = await demonstrate_performance_configs(manager)
    all_kbs.extend(performance_kbs.values())
    
    # Summary
    print("\n" + "=" * 60)
    print("Configuration Summary")
    print("=" * 60)
    
    print("\n📊 Key Takeaways:")
    print("\n1. Chunking Strategy:")
    print("   - Small chunks (256): Better for precise matching")
    print("   - Medium chunks (512): Balanced (recommended)")
    print("   - Large chunks (1024): Better for context")
    
    print("\n2. Retrieval Mode:")
    print("   - Vector: Fastest, semantic search")
    print("   - Fulltext: Keyword-based search")
    print("   - Hybrid: Best accuracy (recommended)")
    
    print("\n3. Precision vs Recall:")
    print("   - High precision: High threshold (0.6+), few results")
    print("   - Balanced: Medium threshold (0.3-0.5)")
    print("   - High recall: Low threshold (0.2-), many results")
    
    print("\n4. Performance Optimization:")
    print("   - Speed: Vector mode, no reranking, higher threshold")
    print("   - Quality: Hybrid mode, reranking, lower threshold")
    print("   - Memory: Smaller chunks, fewer results")
    
    print(f"\n📈 Created {len(all_kbs)} knowledge bases with different configurations")
    
    # Cleanup
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)
    
    cleanup = input("\nDo you want to delete all example KBs? (y/n): ")
    
    if cleanup.lower() == 'y':
        for kb in all_kbs:
            await manager.delete_knowledge_base(kb_id=kb.id)
        print(f"✓ Deleted all {len(all_kbs)} knowledge bases")
    else:
        print("✓ Knowledge bases preserved")
        print("\nYou can experiment with these configurations:")
        for kb in all_kbs:
            print(f"  - {kb.name}: {kb.id}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
