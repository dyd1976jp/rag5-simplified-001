"""
Batch Operations Example

This example demonstrates efficient batch processing of multiple files:
- Batch file uploads
- Parallel processing
- Progress tracking
- Error handling

Run this example:
    python examples/kb_management/batch_operations.py
"""

import asyncio
import sys
from pathlib import Path
from typing import List
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rag5.core.knowledge_base import KnowledgeBaseManager, initialize_kb_system
from rag5.core.knowledge_base.models import ChunkConfig, RetrievalConfig, FileStatus
from rag5.core.knowledge_base.vector_manager import VectorStoreManager
from rag5.config import settings
from qdrant_client import QdrantClient


async def create_sample_files(count: int = 10) -> List[Path]:
    """Create multiple sample files for batch processing"""
    print(f"\n📄 Creating {count} sample files...")
    
    docs_dir = Path(settings.file_storage_path) / "batch_test"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    files = []
    
    topics = [
        ("AI", "Artificial Intelligence is the simulation of human intelligence..."),
        ("ML", "Machine Learning is a subset of AI that enables systems to learn..."),
        ("DL", "Deep Learning uses neural networks with multiple layers..."),
        ("NLP", "Natural Language Processing enables computers to understand human language..."),
        ("CV", "Computer Vision enables machines to interpret visual information..."),
        ("RL", "Reinforcement Learning is about learning through trial and error..."),
        ("Data", "Data Science combines statistics, programming, and domain knowledge..."),
        ("Cloud", "Cloud Computing provides on-demand access to computing resources..."),
        ("IoT", "Internet of Things connects physical devices to the internet..."),
        ("Blockchain", "Blockchain is a distributed ledger technology...")
    ]
    
    for i in range(count):
        topic, content = topics[i % len(topics)]
        file_path = docs_dir / f"document_{i+1:02d}_{topic.lower()}.txt"
        
        full_content = f"""
        Topic: {topic}
        Document {i+1}
        
        {content}
        
        This is a sample document for batch processing demonstration.
        It contains information about {topic} and related concepts.
        
        Additional content to make the document longer and more realistic.
        This helps demonstrate the chunking and embedding process.
        """
        
        file_path.write_text(full_content)
        files.append(file_path)
    
    print(f"✓ Created {len(files)} sample files in {docs_dir}")
    return files


async def batch_upload_sequential(
    manager: KnowledgeBaseManager,
    kb_id: str,
    files: List[Path]
) -> List[str]:
    """Upload files sequentially"""
    print(f"\n📤 Sequential upload of {len(files)} files...")
    
    start_time = time.time()
    file_ids = []
    
    for i, file_path in enumerate(files, 1):
        print(f"  [{i}/{len(files)}] Uploading {file_path.name}...", end=" ")
        
        try:
            file_entity = await manager.upload_file(
                kb_id=kb_id,
                file_path=str(file_path)
            )
            file_ids.append(file_entity.id)
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elapsed = time.time() - start_time
    print(f"\n✓ Sequential upload completed in {elapsed:.2f}s")
    print(f"  Average: {elapsed/len(files):.2f}s per file")
    
    return file_ids


async def batch_process_sequential(
    manager: KnowledgeBaseManager,
    file_ids: List[str]
) -> dict:
    """Process files sequentially"""
    print(f"\n⚙️  Sequential processing of {len(file_ids)} files...")
    
    start_time = time.time()
    results = {"succeeded": 0, "failed": 0}
    
    for i, file_id in enumerate(file_ids, 1):
        print(f"  [{i}/{len(file_ids)}] Processing file...", end=" ")
        
        try:
            await manager.process_file(file_id)
            results["succeeded"] += 1
            print("✓")
        except Exception as e:
            results["failed"] += 1
            print(f"✗ Error: {e}")
    
    elapsed = time.time() - start_time
    print(f"\n✓ Sequential processing completed in {elapsed:.2f}s")
    print(f"  Average: {elapsed/len(file_ids):.2f}s per file")
    print(f"  Succeeded: {results['succeeded']}")
    print(f"  Failed: {results['failed']}")
    
    return results


async def batch_process_parallel(
    manager: KnowledgeBaseManager,
    file_ids: List[str],
    max_concurrent: int = 3
) -> dict:
    """Process files in parallel with concurrency limit"""
    print(f"\n⚙️  Parallel processing of {len(file_ids)} files...")
    print(f"  Max concurrent: {max_concurrent}")
    
    start_time = time.time()
    results = {"succeeded": 0, "failed": 0}
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(file_id: str, index: int):
        async with semaphore:
            print(f"  [{index}/{len(file_ids)}] Processing file...", end=" ")
            try:
                await manager.process_file(file_id)
                results["succeeded"] += 1
                print("✓")
            except Exception as e:
                results["failed"] += 1
                print(f"✗ Error: {e}")
    
    # Process all files in parallel (with concurrency limit)
    tasks = [
        process_with_semaphore(file_id, i+1)
        for i, file_id in enumerate(file_ids)
    ]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    print(f"\n✓ Parallel processing completed in {elapsed:.2f}s")
    print(f"  Average: {elapsed/len(file_ids):.2f}s per file")
    print(f"  Speedup: {(elapsed/len(file_ids)) / (elapsed/len(file_ids)):.2f}x")
    print(f"  Succeeded: {results['succeeded']}")
    print(f"  Failed: {results['failed']}")
    
    return results


async def monitor_processing_status(
    manager: KnowledgeBaseManager,
    kb_id: str,
    expected_count: int
):
    """Monitor file processing status"""
    print(f"\n📊 Monitoring processing status...")
    
    while True:
        files, total = await manager.list_files(kb_id=kb_id, page=1, size=100)
        
        status_counts = {
            "pending": 0,
            "parsing": 0,
            "persisting": 0,
            "succeeded": 0,
            "failed": 0
        }
        
        for file in files:
            status_counts[file.status.value] += 1
        
        print(f"\r  Status: ", end="")
        print(f"Pending: {status_counts['pending']}, ", end="")
        print(f"Processing: {status_counts['parsing'] + status_counts['persisting']}, ", end="")
        print(f"Succeeded: {status_counts['succeeded']}, ", end="")
        print(f"Failed: {status_counts['failed']}", end="")
        
        # Check if all files are processed
        if status_counts['succeeded'] + status_counts['failed'] >= expected_count:
            print()  # New line
            break
        
        await asyncio.sleep(1)
    
    print(f"\n✓ All files processed")
    return status_counts


async def handle_failed_files(
    manager: KnowledgeBaseManager,
    kb_id: str
):
    """Handle failed file processing"""
    print(f"\n🔧 Checking for failed files...")
    
    files, total = await manager.list_files(
        kb_id=kb_id,
        status=FileStatus.FAILED,
        page=1,
        size=100
    )
    
    if not files:
        print("  ✓ No failed files")
        return
    
    print(f"  Found {len(files)} failed file(s)")
    
    for file in files:
        print(f"\n  File: {file.file_name}")
        print(f"    ID: {file.id}")
        print(f"    Reason: {file.failed_reason}")
        
        # Option to retry or delete
        action = input(f"    Action (r=retry, d=delete, s=skip): ").lower()
        
        if action == 'r':
            print(f"    Retrying...")
            try:
                await manager.process_file(file.id)
                print(f"    ✓ Retry successful")
            except Exception as e:
                print(f"    ✗ Retry failed: {e}")
        elif action == 'd':
            print(f"    Deleting...")
            await manager.delete_file(kb_id=kb_id, file_id=file.id)
            print(f"    ✓ Deleted")
        else:
            print(f"    Skipped")


async def demonstrate_batch_statistics(
    manager: KnowledgeBaseManager,
    kb_id: str
):
    """Show batch processing statistics"""
    print(f"\n📈 Batch Processing Statistics")
    print("=" * 60)
    
    kb = await manager.get_knowledge_base(kb_id)
    files, total = await manager.list_files(kb_id=kb_id, page=1, size=100)
    
    print(f"\nKnowledge Base: {kb.name}")
    print(f"  Total documents: {kb.document_count}")
    print(f"  Total size: {kb.total_size / 1024:.2f} KB")
    
    # Calculate statistics
    total_chunks = sum(f.chunk_count for f in files)
    avg_chunks = total_chunks / len(files) if files else 0
    avg_size = sum(f.file_size for f in files) / len(files) if files else 0
    
    print(f"\nFile Statistics:")
    print(f"  Total files: {len(files)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Average chunks per file: {avg_chunks:.1f}")
    print(f"  Average file size: {avg_size / 1024:.2f} KB")
    
    # Status breakdown
    status_counts = {}
    for file in files:
        status = file.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\nStatus Breakdown:")
    for status, count in status_counts.items():
        percentage = (count / len(files)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")


async def main():
    print("=" * 60)
    print("Batch Operations Example")
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
    
    # Create knowledge base
    print("\n📚 Creating knowledge base...")
    kb = await manager.create_knowledge_base(
        name="batch_test_kb",
        description="Knowledge base for batch operations testing",
        embedding_model="nomic-embed-text",
        chunk_config=ChunkConfig(chunk_size=512, chunk_overlap=50),
        retrieval_config=RetrievalConfig(top_k=5, similarity_threshold=0.3)
    )
    print(f"✓ Created: {kb.id}")
    
    # Create sample files
    file_count = 10
    sample_files = await create_sample_files(file_count)
    
    # Batch upload
    print("\n" + "=" * 60)
    print("Batch Upload")
    print("=" * 60)
    
    file_ids = await batch_upload_sequential(manager, kb.id, sample_files)
    
    # Choose processing method
    print("\n" + "=" * 60)
    print("Batch Processing")
    print("=" * 60)
    
    print("\nProcessing methods:")
    print("  1. Sequential (slower but simpler)")
    print("  2. Parallel (faster with concurrency)")
    
    choice = input("\nChoose method (1 or 2): ")
    
    if choice == "2":
        max_concurrent = int(input("Max concurrent processes (default 3): ") or "3")
        results = await batch_process_parallel(manager, file_ids, max_concurrent)
    else:
        results = await batch_process_sequential(manager, file_ids)
    
    # Monitor status
    await monitor_processing_status(manager, kb.id, len(file_ids))
    
    # Handle failed files
    await handle_failed_files(manager, kb.id)
    
    # Show statistics
    await demonstrate_batch_statistics(manager, kb.id)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)
    
    cleanup = input("\nDo you want to delete the test KB and files? (y/n): ")
    
    if cleanup.lower() == 'y':
        await manager.delete_knowledge_base(kb_id=kb.id)
        print("✓ Deleted knowledge base")
        
        # Delete sample files
        for file_path in sample_files:
            if file_path.exists():
                file_path.unlink()
        
        # Remove directory if empty
        batch_dir = Path(settings.file_storage_path) / "batch_test"
        if batch_dir.exists() and not list(batch_dir.iterdir()):
            batch_dir.rmdir()
        
        print("✓ Deleted sample files")
    else:
        print("✓ Test data preserved")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    
    print("\n💡 Key Takeaways:")
    print("  - Batch uploads are efficient for multiple files")
    print("  - Parallel processing can significantly speed up ingestion")
    print("  - Monitor processing status to track progress")
    print("  - Handle failed files appropriately (retry or delete)")
    print("  - Use statistics to understand your data")


if __name__ == "__main__":
    asyncio.run(main())
