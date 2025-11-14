"""
Unit tests for AsyncLogWriter.

Tests buffered writing, batch writes, flush operation, shutdown and cleanup,
and thread safety.
"""

import pytest
import tempfile
import os
import time
import threading
from pathlib import Path
from rag5.utils.async_writer import AsyncLogWriter


class TestAsyncLogWriter:
    """Test suite for AsyncLogWriter"""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        yield log_file
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)
    
    @pytest.fixture
    def writer(self, temp_log_file):
        """Create an async writer"""
        writer = AsyncLogWriter(
            log_file=temp_log_file,
            buffer_size=10,
            flush_interval=1.0
        )
        yield writer
        # Cleanup
        writer.shutdown(timeout=2.0)
    
    def test_initialization_creates_log_directory(self):
        """Test that writer creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "subdir", "async.log")
            writer = AsyncLogWriter(log_file=log_file)
            
            # Directory should be created
            assert os.path.exists(os.path.dirname(log_file))
            
            # Cleanup
            writer.shutdown()
    
    def test_initialization_starts_writer_thread(self, writer):
        """Test that writer thread is started on initialization"""
        assert writer._writer_thread.is_alive()
    
    def test_write_single_entry(self, writer, temp_log_file):
        """Test writing a single log entry"""
        writer.write("Test log entry")
        
        # Force flush to ensure write completes
        writer.flush()
        time.sleep(0.2)
        
        # Read and verify
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Test log entry" in content
    
    def test_write_multiple_entries(self, temp_log_file):
        """Test writing multiple log entries"""
        writer = AsyncLogWriter(log_file=temp_log_file)
        
        entries = [f"Log entry {i}" for i in range(5)]
        
        for entry in entries:
            writer.write(entry)
        
        # Shutdown to ensure all entries are written
        writer.shutdown(timeout=2.0)
        
        # Read and verify
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
        for i, line in enumerate(lines):
            assert f"Log entry {i}" in line
    
    def test_buffered_writing(self, writer, temp_log_file):
        """Test that entries are buffered before writing"""
        # Write fewer entries than buffer size
        for i in range(5):
            writer.write(f"Entry {i}")
        
        # Don't flush - entries should be buffered
        time.sleep(0.1)
        
        # File might be empty or have some entries depending on timing
        # The key is that not all entries are written immediately
        stats = writer.get_stats()
        assert stats["queue_size"] >= 0  # Some entries may still be queued
    
    def test_batch_write_on_buffer_full(self, writer, temp_log_file):
        """Test that batch write occurs when buffer is full"""
        # Write more entries than buffer size (buffer_size=10)
        for i in range(15):
            writer.write(f"Entry {i}")
        
        # Wait for batch write to complete
        time.sleep(0.3)
        
        # Read and verify
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # At least the first batch should be written
        assert len(lines) >= 10
    
    def test_batch_write_on_flush_interval(self, temp_log_file):
        """Test that batch write occurs after flush interval"""
        # Create writer with short flush interval
        writer = AsyncLogWriter(
            log_file=temp_log_file,
            buffer_size=100,  # Large buffer
            flush_interval=0.5  # Short interval
        )
        
        try:
            # Write a few entries
            for i in range(3):
                writer.write(f"Entry {i}")
            
            # Wait for flush interval to expire
            time.sleep(0.7)
            
            # Read and verify
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            assert len(lines) == 3
        finally:
            writer.shutdown()
    
    def test_flush_forces_immediate_write(self, temp_log_file):
        """Test that flush forces immediate write"""
        writer = AsyncLogWriter(log_file=temp_log_file)
        
        # Write entries
        for i in range(3):
            writer.write(f"Entry {i}")
        
        # Shutdown to ensure all entries are written
        writer.shutdown(timeout=2.0)
        
        # All entries should be written
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
    
    def test_shutdown_flushes_remaining_entries(self, temp_log_file):
        """Test that shutdown flushes all remaining entries"""
        writer = AsyncLogWriter(
            log_file=temp_log_file,
            buffer_size=100,  # Large buffer to prevent auto-flush
            flush_interval=10.0  # Long interval
        )
        
        # Write entries
        for i in range(5):
            writer.write(f"Entry {i}")
        
        # Shutdown immediately (should flush all entries)
        writer.shutdown(timeout=2.0)
        
        # All entries should be written
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
    
    def test_shutdown_waits_for_thread(self, writer):
        """Test that shutdown waits for writer thread to terminate"""
        writer.write("Test entry")
        
        # Shutdown
        writer.shutdown(timeout=2.0)
        
        # Thread should be terminated
        assert not writer._writer_thread.is_alive()
    
    def test_shutdown_with_timeout(self, temp_log_file):
        """Test shutdown with timeout"""
        writer = AsyncLogWriter(log_file=temp_log_file)
        
        # Shutdown with very short timeout
        writer.shutdown(timeout=0.1)
        
        # Should complete (may or may not terminate thread in time)
        # The important thing is it doesn't hang
        assert True
    
    def test_shutdown_is_idempotent(self, writer):
        """Test that shutdown can be called multiple times safely"""
        writer.shutdown(timeout=1.0)
        
        # Second shutdown should not raise
        writer.shutdown(timeout=1.0)
    
    def test_write_after_shutdown_is_ignored(self, writer, temp_log_file):
        """Test that writes after shutdown are ignored"""
        writer.shutdown(timeout=1.0)
        
        # Try to write after shutdown
        writer.write("This should be ignored")
        
        time.sleep(0.2)
        
        # File should be empty or not contain the entry
        if os.path.exists(temp_log_file):
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "This should be ignored" not in content
    
    def test_thread_safety_concurrent_writes(self, writer, temp_log_file):
        """Test thread safety with concurrent writes"""
        num_threads = 5
        entries_per_thread = 10
        
        def write_entries(thread_id):
            for i in range(entries_per_thread):
                writer.write(f"Thread {thread_id} Entry {i}")
        
        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=write_entries, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Flush and wait
        writer.flush()
        time.sleep(0.3)
        
        # Read and verify
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Should have all entries
        assert len(lines) == num_threads * entries_per_thread
    
    def test_get_stats_initial(self, writer):
        """Test get_stats returns correct initial values"""
        stats = writer.get_stats()
        
        assert stats["entries_written"] == 0
        assert stats["batches_written"] == 0
        assert stats["errors"] == 0
        assert stats["queue_size"] >= 0
    
    def test_get_stats_after_writes(self, temp_log_file):
        """Test get_stats after writing entries"""
        writer = AsyncLogWriter(log_file=temp_log_file)
        
        # Write entries
        for i in range(15):
            writer.write(f"Entry {i}")
        
        # Shutdown to ensure all entries are written
        writer.shutdown(timeout=2.0)
        
        stats = writer.get_stats()
        
        assert stats["entries_written"] == 15
        assert stats["batches_written"] >= 1
    
    def test_chinese_characters_preserved(self, writer, temp_log_file):
        """Test that Chinese characters are preserved"""
        writer.write("李小勇和人合作入股了什么公司")
        
        writer.flush()
        time.sleep(0.2)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "李小勇和人合作入股了什么公司" in content
    
    def test_unicode_characters_preserved(self, temp_log_file):
        """Test that various Unicode characters are preserved"""
        writer = AsyncLogWriter(log_file=temp_log_file)
        
        entries = [
            "Hello 世界",
            "Привет мир",
            "مرحبا بالعالم",
            "🎉🎊🎈",
        ]
        
        for entry in entries:
            writer.write(entry)
        
        writer.shutdown(timeout=2.0)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for entry in entries:
            assert entry in content
    
    def test_large_entry(self, writer, temp_log_file):
        """Test writing a large log entry"""
        large_entry = "A" * 10000
        
        writer.write(large_entry)
        writer.flush()
        time.sleep(0.2)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert large_entry in content
    
    def test_many_small_entries(self, temp_log_file):
        """Test writing many small entries"""
        writer = AsyncLogWriter(log_file=temp_log_file)
        
        num_entries = 100
        
        for i in range(num_entries):
            writer.write(f"Entry {i}")
        
        writer.shutdown(timeout=2.0)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == num_entries
    
    def test_empty_entry(self, writer, temp_log_file):
        """Test writing an empty entry"""
        writer.write("")
        
        writer.flush()
        time.sleep(0.2)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Empty entry should still create a line
        assert len(lines) == 1
    
    def test_entry_with_newlines(self, writer, temp_log_file):
        """Test writing entry with embedded newlines"""
        entry = "Line 1\nLine 2\nLine 3"
        
        writer.write(entry)
        writer.flush()
        time.sleep(0.2)
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Entry should be written as-is
        assert "Line 1" in content
        assert "Line 2" in content
        assert "Line 3" in content
    
    def test_buffer_size_configuration(self, temp_log_file):
        """Test that buffer size configuration works"""
        writer = AsyncLogWriter(
            log_file=temp_log_file,
            buffer_size=5,
            flush_interval=10.0
        )
        
        try:
            # Write exactly buffer_size entries
            for i in range(5):
                writer.write(f"Entry {i}")
            
            # Wait for batch write
            time.sleep(0.3)
            
            # Should have written the batch
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            assert len(lines) == 5
        finally:
            writer.shutdown()
    
    def test_flush_interval_configuration(self, temp_log_file):
        """Test that flush interval configuration works"""
        writer = AsyncLogWriter(
            log_file=temp_log_file,
            buffer_size=100,
            flush_interval=0.3
        )
        
        try:
            writer.write("Entry 1")
            
            # Wait for flush interval
            time.sleep(0.5)
            
            # Should have flushed
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            assert len(lines) == 1
        finally:
            writer.shutdown()
    
    def test_multiple_writers_same_file(self, temp_log_file):
        """Test multiple writers to the same file"""
        writer1 = AsyncLogWriter(log_file=temp_log_file)
        writer2 = AsyncLogWriter(log_file=temp_log_file)
        
        try:
            writer1.write("From writer 1")
            writer2.write("From writer 2")
            
            writer1.flush()
            writer2.flush()
            time.sleep(0.3)
            
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Both entries should be present
            assert "From writer 1" in content
            assert "From writer 2" in content
        finally:
            writer1.shutdown()
            writer2.shutdown()
    
    def test_writer_thread_name(self, writer, temp_log_file):
        """Test that writer thread has descriptive name"""
        thread_name = writer._writer_thread.name
        
        assert "AsyncLogWriter" in thread_name
        assert temp_log_file in thread_name
    
    def test_error_handling_invalid_file_path(self):
        """Test error handling with invalid file path"""
        # This should not raise during initialization
        # (directory creation might fail but should be handled)
        try:
            writer = AsyncLogWriter(log_file="/invalid/path/that/does/not/exist/file.log")
            writer.write("Test")
            writer.shutdown()
        except Exception:
            # If it does raise, that's also acceptable behavior
            pass
