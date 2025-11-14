"""
Basic Knowledge Base Management Example

This example demonstrates the fundamental operations:
1. Creating a knowledge base
2. Uploading documents
3. Querying the knowledge base
4. Cleaning up

Run this example:
    python examples/kb_management/basic_usage.py
"""

import asyncio
import os
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


async def main():
    print("=" * 60)
    print("Knowledge Base Management - Basic Usage Example")
    print("=" * 60)
    print()
    
    # Step 1: Initialize the system
    print("Step 1: Initializing knowledge base system...")
    db, default_kb = initialize_kb_system(
        db_path=settings.kb_database_path,
        create_default=True
    )
    print(f"✓ System initialized")
    print(f"  Database: {settings.kb_database_path}")
    if default_kb:
        print(f"  Default KB: {default_kb.name} ({default_kb.id})")
    print()
    
    # Step 2: Create vector store manager
    print("Step 2: Connecting to vector store...")
    qdrant_client = QdrantClient(url=settings.qdrant_url)
    vector_manager = VectorStoreManager(qdrant_client)
    print(f"✓ Connected to Qdrant at {settings.qdrant_url}")
    print()
    
    # Step 3: Create knowledge base manager
    print("Step 3: Creating knowledge base manager...")
    manager = KnowledgeBaseManager(
        db_path=settings.kb_database_path,
        vector_manager=vector_manager,
        file_storage_path=settings.file_storage_path
    )
    print("✓ Manager created")
    print()
    
    # Step 4: Create a new knowledge base
    print("Step 4: Creating a new knowledge base...")
    kb = await manager.create_knowledge_base(
        name="example_kb",
        description="Example knowledge base for demonstration",
        embedding_model="nomic-embed-text",
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
    print(f"✓ Knowledge base created")
    print(f"  ID: {kb.id}")
    print(f"  Name: {kb.name}")
    print(f"  Embedding Model: {kb.embedding_model}")
    print(f"  Chunk Size: {kb.chunk_config.chunk_size}")
    print(f"  Top K: {kb.retrieval_config.top_k}")
    print()
    
    # Step 5: Create a sample document
    print("Step 5: Creating sample document...")
    sample_doc_path = Path(settings.file_storage_path) / "sample_example.txt"
    sample_doc_path.parent.mkdir(parents=True, exist_ok=True)
    
    sample_content = """
    Artificial Intelligence (AI) is the simulation of human intelligence processes by machines,
    especially computer systems. These processes include learning (the acquisition of information
    and rules for using the information), reasoning (using rules to reach approximate or definite
    conclusions) and self-correction.
    
    Machine Learning is a subset of AI that provides systems the ability to automatically learn
    and improve from experience without being explicitly programmed. Machine learning focuses on
    the development of computer programs that can access data and use it to learn for themselves.
    
    Deep Learning is a subset of machine learning that uses neural networks with multiple layers.
    These neural networks attempt to simulate the behavior of the human brain—allowing it to
    "learn" from large amounts of data.
    """
    
    with open(sample_doc_path, "w") as f:
        f.write(sample_content)
    
    print(f"✓ Sample document created at {sample_doc_path}")
    print()
    
    # Step 6: Upload the document
    print("Step 6: Uploading document to knowledge base...")
    file_entity = await manager.upload_file(
        kb_id=kb.id,
        file_path=str(sample_doc_path)
    )
    print(f"✓ Document uploaded")
    print(f"  File ID: {file_entity.id}")
    print(f"  File Name: {file_entity.file_name}")
    print(f"  File Size: {file_entity.file_size} bytes")
    print(f"  Status: {file_entity.status.value}")
    print()
    
    # Step 7: Process the document
    print("Step 7: Processing document...")
    print("  This may take a few moments...")
    await manager.process_file(file_entity.id)
    
    # Get updated file info
    files, _ = await manager.list_files(kb_id=kb.id)
    processed_file = files[0]
    
    print(f"✓ Document processed")
    print(f"  Status: {processed_file.status.value}")
    print(f"  Chunks: {processed_file.chunk_count}")
    print()
    
    # Step 8: Query the knowledge base
    print("Step 8: Querying the knowledge base...")
    queries = [
        "What is artificial intelligence?",
        "Explain machine learning",
        "What is deep learning?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        results = await manager.query_knowledge_base(
            kb_id=kb.id,
            query=query,
            top_k=2
        )
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"  Score: {result['score']:.4f}")
                print(f"  Content: {result['content'][:150]}...")
                print(f"  Source: {result['source']}")
        else:
            print("  No results found")
    
    print()
    print("=" * 60)
    
    # Step 9: List all knowledge bases
    print("\nStep 9: Listing all knowledge bases...")
    kbs, total = await manager.list_knowledge_bases(page=1, size=10)
    print(f"✓ Found {total} knowledge base(s)")
    for kb_item in kbs:
        print(f"  - {kb_item.name} ({kb_item.id})")
        print(f"    Documents: {kb_item.document_count}")
        print(f"    Description: {kb_item.description}")
    print()
    
    # Step 10: Cleanup (optional)
    print("Step 10: Cleanup...")
    cleanup = input("Do you want to delete the example knowledge base? (y/n): ")
    
    if cleanup.lower() == 'y':
        await manager.delete_knowledge_base(kb_id=kb.id)
        print(f"✓ Knowledge base '{kb.name}' deleted")
        
        # Delete sample file
        if sample_doc_path.exists():
            sample_doc_path.unlink()
            print(f"✓ Sample document deleted")
    else:
        print("✓ Knowledge base preserved")
        print(f"  You can query it using: kb_id='{kb.id}'")
    
    print()
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
