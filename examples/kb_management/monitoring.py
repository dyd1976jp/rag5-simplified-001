"""
Monitoring and Performance Example

This example demonstrates monitoring and performance tracking:
- KB statistics and metrics
- Query performance measurement
- Resource usage monitoring
- Health checks

Run this example:
    python examples/kb_management/monitoring.py
"""

import asyncio
import sys
from pathlib import Path
import time
import psutil
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rag5.core.knowledge_base import KnowledgeBaseManager, initialize_kb_system
from rag5.core.knowledge_base.models import ChunkConfig, RetrievalConfig
from rag5.core.knowledge_base.vector_manager import VectorStoreManager
from rag5.config import settings
from qdrant_client import QdrantClient


def get_memory_usage():
    """Get current memory usage"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB


def get_disk_usage(path: str):
    """Get disk usage for a path"""
    if os.path.exists(path):
        if os.path.isfile(path):
            return os.path.getsize(path) / 1024 / 1024  # MB
        else:
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total += os.path.getsize(filepath)
            return total / 1024 / 1024  # MB
    return 0


async def monitor_kb_statistics(manager: KnowledgeBaseManager):
    """Monitor knowledge base statistics"""
    print("\n" + "=" * 60)
    print("Knowledge Base Statistics")
    print("=" * 60)
    
    kbs, total = await manager.list_knowledge_bases(page=1, size=100)
    
    print(f"\nTotal Knowledge Bases: {total}")
    
    if not kbs:
        print("  No knowledge bases found")
        return
    
    print("\nDetailed Statistics:")
    print("-" * 60)
    
    total_docs = 0
    total_size = 0
    
    for kb in kbs:
        print(f"\n📚 {kb.name}")
        print(f"   ID: {kb.id}")
        print(f"   Description: {kb.description}")
        print(f"   Embedding Model: {kb.embedding_model}")
        print(f"   Documents: {kb.document_count}")
        print(f"   Total Size: {kb.total_size / 1024:.2f} KB")
        print(f"   Created: {kb.created_at}")
        print(f"   Updated: {kb.updated_at}")
        
        # Get file statistics
        files, file_count = await manager.list_files(kb_id=kb.id, page=1, size=100)
        
        if files:
            total_chunks = sum(f.chunk_count for f in files)
            avg_chunks = total_chunks / len(files)
            
            print(f"   Files: {len(files)}")
            print(f"   Total Chunks: {total_chunks}")
            print(f"   Avg Chunks/File: {avg_chunks:.1f}")
            
            # Status breakdown
            status_counts = {}
            for file in files:
                status = file.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"   File Status:")
            for status, count in status_counts.items():
                print(f"     - {status}: {count}")
        
        total_docs += kb.document_count
        total_size += kb.total_size
    
    print("\n" + "-" * 60)
    print(f"Overall Totals:")
    print(f"  Total Documents: {total_docs}")
    print(f"  Total Size: {total_size / 1024:.2f} KB")


async def measure_query_performance(
    manager: KnowledgeBaseManager,
    kb_id: str,
    queries: list,
    iterations: int = 3
):
    """Measure query performance"""
    print("\n" + "=" * 60)
    print("Query Performance Measurement")
    print("=" * 60)
    
    results = []
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        times = []
        result_counts = []
        
        for i in range(iterations):
            start_time = time.time()
            
            query_results = await manager.query_knowledge_base(
                kb_id=kb_id,
                query=query,
                top_k=5
            )
            
            elapsed = time.time() - start_time
            times.append(elapsed)
            result_counts.append(len(query_results))
            
            print(f"  Iteration {i+1}: {elapsed:.3f}s ({len(query_results)} results)")
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_results = sum(result_counts) / len(result_counts)
        
        print(f"\nStatistics:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Min time: {min_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  Average results: {avg_results:.1f}")
        
        results.append({
            "query": query,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "avg_results": avg_results
        })
    
    return results


async def monitor_resource_usage(manager: KnowledgeBaseManager, kb_id: str):
    """Monitor resource usage"""
    print("\n" + "=" * 60)
    print("Resource Usage Monitoring")
    print("=" * 60)
    
    # Memory usage
    memory_before = get_memory_usage()
    print(f"\nMemory Usage (before operations): {memory_before:.2f} MB")
    
    # Perform some operations
    print("\nPerforming operations...")
    
    # Query operation
    start_time = time.time()
    results = await manager.query_knowledge_base(
        kb_id=kb_id,
        query="test query",
        top_k=10
    )
    query_time = time.time() - start_time
    
    memory_after = get_memory_usage()
    memory_delta = memory_after - memory_before
    
    print(f"\nQuery Performance:")
    print(f"  Time: {query_time:.3f}s")
    print(f"  Results: {len(results)}")
    print(f"  Memory delta: {memory_delta:+.2f} MB")
    
    # Disk usage
    print(f"\nDisk Usage:")
    
    db_size = get_disk_usage(settings.kb_database_path)
    print(f"  Database: {db_size:.2f} MB")
    
    docs_size = get_disk_usage(settings.file_storage_path)
    print(f"  Documents: {docs_size:.2f} MB")
    
    # Vector store size (if accessible)
    vector_path = "qdrant_storage"
    if os.path.exists(vector_path):
        vector_size = get_disk_usage(vector_path)
        print(f"  Vector Store: {vector_size:.2f} MB")
    
    total_disk = db_size + docs_size
    print(f"  Total: {total_disk:.2f} MB")
    
    # System resources
    print(f"\nSystem Resources:")
    print(f"  CPU Usage: {psutil.cpu_percent()}%")
    print(f"  Memory Usage: {psutil.virtual_memory().percent}%")
    print(f"  Disk Usage: {psutil.disk_usage('/').percent}%")


async def health_check(manager: KnowledgeBaseManager):
    """Perform system health check"""
    print("\n" + "=" * 60)
    print("System Health Check")
    print("=" * 60)
    
    checks = []
    
    # Check database
    print("\n🔍 Checking database...")
    try:
        kbs, total = await manager.list_knowledge_bases(page=1, size=1)
        print(f"  ✓ Database accessible ({total} KBs)")
        checks.append(("Database", True, f"{total} KBs"))
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        checks.append(("Database", False, str(e)))
    
    # Check vector store
    print("\n🔍 Checking vector store...")
    try:
        collections = manager.vector_manager.client.get_collections()
        print(f"  ✓ Vector store accessible ({len(collections.collections)} collections)")
        checks.append(("Vector Store", True, f"{len(collections.collections)} collections"))
    except Exception as e:
        print(f"  ✗ Vector store error: {e}")
        checks.append(("Vector Store", False, str(e)))
    
    # Check file storage
    print("\n🔍 Checking file storage...")
    try:
        storage_path = Path(settings.file_storage_path)
        if storage_path.exists():
            file_count = len(list(storage_path.rglob("*.*")))
            print(f"  ✓ File storage accessible ({file_count} files)")
            checks.append(("File Storage", True, f"{file_count} files"))
        else:
            print(f"  ⚠ File storage directory doesn't exist")
            checks.append(("File Storage", False, "Directory not found"))
    except Exception as e:
        print(f"  ✗ File storage error: {e}")
        checks.append(("File Storage", False, str(e)))
    
    # Summary
    print("\n" + "-" * 60)
    print("Health Check Summary:")
    print("-" * 60)
    
    all_healthy = all(check[1] for check in checks)
    
    for component, healthy, details in checks:
        status = "✓" if healthy else "✗"
        print(f"  {status} {component}: {details}")
    
    if all_healthy:
        print("\n✓ All systems operational")
    else:
        print("\n⚠ Some systems have issues")
    
    return all_healthy


async def continuous_monitoring(
    manager: KnowledgeBaseManager,
    kb_id: str,
    duration: int = 30,
    interval: int = 5
):
    """Continuous monitoring for a duration"""
    print("\n" + "=" * 60)
    print(f"Continuous Monitoring ({duration}s)")
    print("=" * 60)
    
    print(f"\nMonitoring every {interval}s for {duration}s...")
    print("Press Ctrl+C to stop early\n")
    
    start_time = time.time()
    iteration = 0
    
    try:
        while time.time() - start_time < duration:
            iteration += 1
            elapsed = time.time() - start_time
            
            print(f"\n[{elapsed:.0f}s] Iteration {iteration}")
            print("-" * 40)
            
            # Get KB stats
            kb = await manager.get_knowledge_base(kb_id)
            print(f"  Documents: {kb.document_count}")
            
            # Memory usage
            memory = get_memory_usage()
            print(f"  Memory: {memory:.2f} MB")
            
            # CPU usage
            cpu = psutil.cpu_percent(interval=1)
            print(f"  CPU: {cpu}%")
            
            # Quick query test
            query_start = time.time()
            results = await manager.query_knowledge_base(
                kb_id=kb_id,
                query="test",
                top_k=3
            )
            query_time = time.time() - query_start
            print(f"  Query time: {query_time:.3f}s")
            
            await asyncio.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    
    print(f"\n✓ Monitoring completed ({iteration} iterations)")


async def generate_performance_report(
    manager: KnowledgeBaseManager,
    kb_id: str
):
    """Generate comprehensive performance report"""
    print("\n" + "=" * 60)
    print("Performance Report")
    print("=" * 60)
    
    kb = await manager.get_knowledge_base(kb_id)
    
    print(f"\nKnowledge Base: {kb.name}")
    print(f"ID: {kb.id}")
    print(f"Created: {kb.created_at}")
    
    # Configuration
    print(f"\nConfiguration:")
    print(f"  Embedding Model: {kb.embedding_model}")
    print(f"  Chunk Size: {kb.chunk_config.chunk_size}")
    print(f"  Chunk Overlap: {kb.chunk_config.chunk_overlap}")
    print(f"  Parser Type: {kb.chunk_config.parser_type}")
    print(f"  Retrieval Mode: {kb.retrieval_config.retrieval_mode}")
    print(f"  Top K: {kb.retrieval_config.top_k}")
    print(f"  Similarity Threshold: {kb.retrieval_config.similarity_threshold}")
    
    # Data statistics
    files, _ = await manager.list_files(kb_id=kb_id, page=1, size=100)
    
    if files:
        total_chunks = sum(f.chunk_count for f in files)
        avg_chunks = total_chunks / len(files)
        total_size = sum(f.file_size for f in files)
        avg_size = total_size / len(files)
        
        print(f"\nData Statistics:")
        print(f"  Total Files: {len(files)}")
        print(f"  Total Chunks: {total_chunks}")
        print(f"  Avg Chunks/File: {avg_chunks:.1f}")
        print(f"  Total Size: {total_size / 1024:.2f} KB")
        print(f"  Avg File Size: {avg_size / 1024:.2f} KB")
    
    # Query performance
    print(f"\nQuery Performance:")
    test_queries = ["test query 1", "test query 2", "test query 3"]
    
    total_time = 0
    total_results = 0
    
    for query in test_queries:
        start = time.time()
        results = await manager.query_knowledge_base(
            kb_id=kb_id,
            query=query,
            top_k=5
        )
        elapsed = time.time() - start
        
        total_time += elapsed
        total_results += len(results)
    
    avg_query_time = total_time / len(test_queries)
    avg_results = total_results / len(test_queries)
    
    print(f"  Avg Query Time: {avg_query_time:.3f}s")
    print(f"  Avg Results: {avg_results:.1f}")
    print(f"  Queries/Second: {1/avg_query_time:.2f}")
    
    # Resource usage
    print(f"\nResource Usage:")
    print(f"  Memory: {get_memory_usage():.2f} MB")
    print(f"  Database Size: {get_disk_usage(settings.kb_database_path):.2f} MB")
    print(f"  Documents Size: {get_disk_usage(settings.file_storage_path):.2f} MB")
    
    # Recommendations
    print(f"\nRecommendations:")
    
    if avg_query_time > 1.0:
        print(f"  ⚠ Query time is high. Consider:")
        print(f"    - Reducing top_k value")
        print(f"    - Increasing similarity threshold")
        print(f"    - Using vector-only retrieval mode")
    
    if avg_chunks > 100:
        print(f"  ⚠ High chunk count per file. Consider:")
        print(f"    - Increasing chunk size")
        print(f"    - Reducing chunk overlap")
    
    if len(files) > 1000:
        print(f"  ℹ Large number of files. Consider:")
        print(f"    - Splitting into multiple KBs")
        print(f"    - Implementing pagination")
    
    print(f"\n✓ Report generated successfully")


async def main():
    print("=" * 60)
    print("Monitoring and Performance Example")
    print("=" * 60)
    
    # Initialize system
    print("\n🚀 Initializing system...")
    db, default_kb = initialize_kb_system(
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
    
    # Use default KB or create new one
    if default_kb:
        kb_id = default_kb.id
        print(f"\nUsing default KB: {kb_id}")
    else:
        print("\nNo default KB found. Please create one first.")
        return
    
    # Health check
    await health_check(manager)
    
    # KB statistics
    await monitor_kb_statistics(manager)
    
    # Resource usage
    await monitor_resource_usage(manager, kb_id)
    
    # Query performance (if KB has documents)
    kb = await manager.get_knowledge_base(kb_id)
    if kb.document_count > 0:
        test_queries = [
            "What is this about?",
            "Explain the main concept",
            "Give me details"
        ]
        await measure_query_performance(manager, kb_id, test_queries, iterations=3)
        
        # Generate report
        await generate_performance_report(manager, kb_id)
    else:
        print("\n⚠ No documents in KB. Skipping query performance tests.")
        print("  Upload some documents first to see query performance metrics.")
    
    # Optional: Continuous monitoring
    print("\n" + "=" * 60)
    monitor_continuous = input("\nRun continuous monitoring? (y/n): ")
    
    if monitor_continuous.lower() == 'y':
        duration = int(input("Duration in seconds (default 30): ") or "30")
        interval = int(input("Interval in seconds (default 5): ") or "5")
        await continuous_monitoring(manager, kb_id, duration, interval)
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    
    print("\n💡 Monitoring Best Practices:")
    print("  - Regular health checks ensure system reliability")
    print("  - Track query performance to identify bottlenecks")
    print("  - Monitor resource usage to prevent issues")
    print("  - Generate reports for optimization insights")
    print("  - Use continuous monitoring for production systems")


if __name__ == "__main__":
    asyncio.run(main())
