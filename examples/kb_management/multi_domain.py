"""
Multi-Domain Knowledge Base Example

This example demonstrates creating separate knowledge bases for different domains:
- Technical documentation
- Financial reports
- Legal documents

Each KB has optimized configurations for its domain.

Run this example:
    python examples/kb_management/multi_domain.py
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


async def create_technical_kb(manager: KnowledgeBaseManager):
    """Create a knowledge base optimized for technical documentation"""
    print("\n📚 Creating Technical Documentation KB...")
    
    kb = await manager.create_knowledge_base(
        name="tech_docs",
        description="Technical documentation, API references, and code examples",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(
            chunk_size=512,
            chunk_overlap=50,
            parser_type="recursive",  # Better for structured docs
            separator="\n\n"
        ),
        retrieval_config=RetrievalConfig(
            retrieval_mode="hybrid",  # Combine semantic + keyword
            top_k=10,  # More results for browsing
            similarity_threshold=0.3,
            vector_weight=0.6,  # Favor semantic search
            enable_rerank=False
        )
    )
    
    print(f"✓ Technical KB created: {kb.id}")
    print(f"  - Optimized for: Code and technical content")
    print(f"  - Chunk size: {kb.chunk_config.chunk_size}")
    print(f"  - Parser: {kb.chunk_config.parser_type}")
    print(f"  - Retrieval: {kb.retrieval_config.retrieval_mode}")
    
    return kb


async def create_financial_kb(manager: KnowledgeBaseManager):
    """Create a knowledge base optimized for financial documents"""
    print("\n💰 Creating Financial Reports KB...")
    
    kb = await manager.create_knowledge_base(
        name="finance_docs",
        description="Financial reports, analysis, and statements",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(
            chunk_size=1024,  # Larger chunks for context
            chunk_overlap=100,
            parser_type="sentence",  # Preserve sentence structure
            separator="\n\n"
        ),
        retrieval_config=RetrievalConfig(
            retrieval_mode="vector",  # Pure semantic search
            top_k=5,
            similarity_threshold=0.4,  # Higher precision
            enable_rerank=True,  # Rerank for accuracy
            rerank_model=""
        )
    )
    
    print(f"✓ Financial KB created: {kb.id}")
    print(f"  - Optimized for: Financial documents")
    print(f"  - Chunk size: {kb.chunk_config.chunk_size}")
    print(f"  - Parser: {kb.chunk_config.parser_type}")
    print(f"  - Retrieval: {kb.retrieval_config.retrieval_mode}")
    print(f"  - Reranking: {kb.retrieval_config.enable_rerank}")
    
    return kb


async def create_legal_kb(manager: KnowledgeBaseManager):
    """Create a knowledge base optimized for legal documents"""
    print("\n⚖️  Creating Legal Documents KB...")
    
    kb = await manager.create_knowledge_base(
        name="legal_docs",
        description="Legal contracts, policies, and compliance documents",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(
            chunk_size=768,  # Medium chunks
            chunk_overlap=75,
            parser_type="sentence",  # Preserve legal language
            separator="\n\n"
        ),
        retrieval_config=RetrievalConfig(
            retrieval_mode="hybrid",
            top_k=5,
            similarity_threshold=0.5,  # High precision
            vector_weight=0.5,
            enable_rerank=True  # Important for legal accuracy
        )
    )
    
    print(f"✓ Legal KB created: {kb.id}")
    print(f"  - Optimized for: Legal documents")
    print(f"  - Chunk size: {kb.chunk_config.chunk_size}")
    print(f"  - Parser: {kb.chunk_config.parser_type}")
    print(f"  - Retrieval: {kb.retrieval_config.retrieval_mode}")
    print(f"  - Similarity threshold: {kb.retrieval_config.similarity_threshold}")
    
    return kb


async def create_sample_documents(manager: KnowledgeBaseManager, kbs: dict):
    """Create and upload sample documents to each KB"""
    print("\n📄 Creating sample documents...")
    
    docs_dir = Path(settings.file_storage_path)
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Technical document
    tech_doc = docs_dir / "tech_sample.txt"
    tech_doc.write_text("""
    API Documentation: User Authentication
    
    The authentication API provides secure user login and token management.
    
    Endpoint: POST /api/v1/auth/login
    Request Body:
    {
        "username": "string",
        "password": "string"
    }
    
    Response:
    {
        "token": "jwt_token_string",
        "expires_in": 3600
    }
    
    Error Codes:
    - 401: Invalid credentials
    - 429: Too many requests
    - 500: Server error
    
    Example usage in Python:
    import requests
    
    response = requests.post(
        "https://api.example.com/v1/auth/login",
        json={"username": "user", "password": "pass"}
    )
    token = response.json()["token"]
    """)
    
    # Financial document
    finance_doc = docs_dir / "finance_sample.txt"
    finance_doc.write_text("""
    Quarterly Financial Report - Q4 2023
    
    Revenue Summary:
    Total revenue for Q4 2023 reached $10.5 million, representing a 15% increase
    compared to Q4 2022. This growth was driven primarily by increased product sales
    and expansion into new markets.
    
    Expenses:
    Operating expenses totaled $7.2 million, including:
    - Personnel costs: $4.5 million
    - Marketing: $1.5 million
    - Infrastructure: $1.2 million
    
    Net Income:
    Net income for the quarter was $3.3 million, with a profit margin of 31.4%.
    This represents our strongest quarter to date.
    
    Cash Flow:
    Operating cash flow was positive at $4.1 million. The company maintains
    a strong cash position of $15 million as of December 31, 2023.
    """)
    
    # Legal document
    legal_doc = docs_dir / "legal_sample.txt"
    legal_doc.write_text("""
    Software License Agreement
    
    This Software License Agreement ("Agreement") is entered into as of the date
    of acceptance by the end user ("Licensee").
    
    1. Grant of License
    Subject to the terms and conditions of this Agreement, Licensor hereby grants
    to Licensee a non-exclusive, non-transferable license to use the Software.
    
    2. Restrictions
    Licensee shall not:
    a) Modify, adapt, or create derivative works of the Software
    b) Reverse engineer, decompile, or disassemble the Software
    c) Rent, lease, or lend the Software to third parties
    
    3. Intellectual Property
    All rights, title, and interest in and to the Software remain with Licensor.
    This Agreement does not grant Licensee any rights to trademarks or service marks.
    
    4. Termination
    This Agreement is effective until terminated. Licensor may terminate this
    Agreement immediately if Licensee fails to comply with any term hereof.
    """)
    
    print("✓ Sample documents created")
    
    # Upload documents to respective KBs
    print("\n📤 Uploading documents...")
    
    # Upload to technical KB
    print("  Uploading to Technical KB...")
    tech_file = await manager.upload_file(
        kb_id=kbs["tech"].id,
        file_path=str(tech_doc)
    )
    await manager.process_file(tech_file.id)
    print(f"  ✓ {tech_doc.name} processed")
    
    # Upload to financial KB
    print("  Uploading to Financial KB...")
    finance_file = await manager.upload_file(
        kb_id=kbs["finance"].id,
        file_path=str(finance_doc)
    )
    await manager.process_file(finance_file.id)
    print(f"  ✓ {finance_doc.name} processed")
    
    # Upload to legal KB
    print("  Uploading to Legal KB...")
    legal_file = await manager.upload_file(
        kb_id=kbs["legal"].id,
        file_path=str(legal_doc)
    )
    await manager.process_file(legal_file.id)
    print(f"  ✓ {legal_doc.name} processed")
    
    return {
        "tech": tech_doc,
        "finance": finance_doc,
        "legal": legal_doc
    }


async def demonstrate_queries(manager: KnowledgeBaseManager, kbs: dict):
    """Demonstrate querying different knowledge bases"""
    print("\n🔍 Demonstrating domain-specific queries...")
    
    queries = [
        ("tech", "How do I authenticate users?"),
        ("finance", "What was the revenue in Q4 2023?"),
        ("legal", "What are the license restrictions?")
    ]
    
    for domain, query in queries:
        kb = kbs[domain]
        print(f"\n{'='*60}")
        print(f"Domain: {domain.upper()}")
        print(f"Query: {query}")
        print(f"KB: {kb.name} ({kb.id})")
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
                print(f"  Content: {result['content'][:200]}...")
        else:
            print("  No results found")


async def demonstrate_isolation(manager: KnowledgeBaseManager, kbs: dict):
    """Demonstrate that KBs are isolated from each other"""
    print("\n🔒 Demonstrating KB isolation...")
    print("\nQuerying 'revenue' across all KBs:")
    print("(Should only find results in Financial KB)")
    
    query = "What is the revenue?"
    
    for domain, kb in kbs.items():
        print(f"\n{domain.upper()} KB:")
        results = await manager.query_knowledge_base(
            kb_id=kb.id,
            query=query,
            top_k=1
        )
        
        if results:
            print(f"  ✓ Found {len(results)} result(s)")
            print(f"    Score: {results[0]['score']:.4f}")
        else:
            print(f"  ✗ No results (as expected)")


async def main():
    print("=" * 60)
    print("Multi-Domain Knowledge Base Example")
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
    
    # Create domain-specific KBs
    print("\n" + "=" * 60)
    print("Creating Domain-Specific Knowledge Bases")
    print("=" * 60)
    
    tech_kb = await create_technical_kb(manager)
    finance_kb = await create_financial_kb(manager)
    legal_kb = await create_legal_kb(manager)
    
    kbs = {
        "tech": tech_kb,
        "finance": finance_kb,
        "legal": legal_kb
    }
    
    # Create and upload sample documents
    print("\n" + "=" * 60)
    print("Creating and Uploading Sample Documents")
    print("=" * 60)
    
    docs = await create_sample_documents(manager, kbs)
    
    # Demonstrate queries
    print("\n" + "=" * 60)
    print("Demonstrating Domain-Specific Queries")
    print("=" * 60)
    
    await demonstrate_queries(manager, kbs)
    
    # Demonstrate isolation
    print("\n" + "=" * 60)
    print("Demonstrating Knowledge Base Isolation")
    print("=" * 60)
    
    await demonstrate_isolation(manager, kbs)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for domain, kb in kbs.items():
        kb_info = await manager.get_knowledge_base(kb.id)
        print(f"\n{domain.upper()} KB:")
        print(f"  ID: {kb_info.id}")
        print(f"  Name: {kb_info.name}")
        print(f"  Documents: {kb_info.document_count}")
        print(f"  Chunk Size: {kb_info.chunk_config.chunk_size}")
        print(f"  Retrieval Mode: {kb_info.retrieval_config.retrieval_mode}")
    
    # Cleanup
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)
    
    cleanup = input("\nDo you want to delete all example KBs? (y/n): ")
    
    if cleanup.lower() == 'y':
        for domain, kb in kbs.items():
            await manager.delete_knowledge_base(kb_id=kb.id)
            print(f"✓ Deleted {domain} KB")
        
        # Delete sample files
        for doc in docs.values():
            if doc.exists():
                doc.unlink()
        print("✓ Deleted sample documents")
    else:
        print("✓ Knowledge bases preserved")
        print("\nYou can query them using:")
        for domain, kb in kbs.items():
            print(f"  {domain}: kb_id='{kb.id}'")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
