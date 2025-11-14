"""
Async log writer for performance-optimized logging.

This module provides asynchronous log writing capabilities with buffering
and batch writes to minimize I/O overhead and prevent blocking operations.
"""

import atexit
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from queue import Queue, Empty
from typing import Optional

from rag5.utils.log_rotation import create_rotating_handler

logger = logging.getLogger(__name__)


class AsyncLogWriter:
    """
    Asynchronous log writer with buffering and batch writes.
    
    Provides non-blocking log writing by buffering entries in memory and
    writing them to disk in batches using a background thread. This minimizes
    I/O overhead and prevents logging from blocking application execution.
    
    Attributes:
        log_file: Path to the log file
        buffer_size: Maximum number of entries to buffer before forcing a write
        flush_interval: Maximum time (seconds) between flushes
        
    Example:
        >>> from rag5.utils.async_writer import AsyncLogWriter
        >>> 
        >>> # Create async writer
        >>> writer = AsyncLogWriter(
        ...     log_file="logs/app.log",
        ...     buffer_size=100,
        ...     flush_interval=5.0
        ... )
        >>> 
        >>> # Write log entries (non-blocking)
        >>> writer.write("Log entry 1")
        >>> writer.write("Log entry 2")
        >>> 
        >>> # Force immediate flush
        >>> writer.flush()
        >>> 
        >>> # Shutdown gracefully
        >>> writer.shutdown()
    """
    
    def __init__(
        self,
        log_file: str,
        buffer_size: int = 100,
        flush_interval: float = 5.0,
        enable_rotation: bool = False,
        rotation_type: str = "size",
        max_bytes: int = 10 * 1024 * 1024,
        rotation_when: str = "midnight",
        backup_count: int = 5,
        compress_rotated: bool = True
    ):
        """
        Initialize the async log writer.
        
        Args:
            log_file: Path to the log file
            buffer_size: Maximum number of entries to buffer before forcing a write
            flush_interval: Maximum time (seconds) between flushes
            enable_rotation: Whether to enable log rotation
            rotation_type: Type of rotation ("size" or "time")
            max_bytes: Maximum file size for size-based rotation
            rotation_when: Time interval for time-based rotation
            backup_count: Number of backup files to keep
            compress_rotated: Whether to compress rotated files
        """
        self.log_file = log_file
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.enable_rotation = enable_rotation
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating handler if enabled
        self._rotating_handler: Optional[logging.Handler] = None
        if enable_rotation:
            try:
                self._rotating_handler = create_rotating_handler(
                    log_file=log_file,
                    rotation_type=rotation_type,
                    max_bytes=max_bytes,
                    when=rotation_when,
                    backup_count=backup_count,
                    compress=compress_rotated
                )
                logger.debug(f"Log rotation enabled for {log_file}")
            except Exception as e:
                logger.error(f"Failed to create rotating handler: {e}", exc_info=True)
                self._rotating_handler = None
        
        # Queue for buffering log entries
        self._queue: Queue = Queue()
        
        # Control flags
        self._shutdown_flag = threading.Event()
        self._flush_requested = threading.Event()
        
        # Background writer thread
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            daemon=True,
            name=f"AsyncLogWriter-{log_file}"
        )
        self._writer_thread.start()
        
        # Track statistics
        self._entries_written = 0
        self._batches_written = 0
        self._errors = 0
        
        logger.debug(
            f"AsyncLogWriter initialized for {log_file} "
            f"(buffer_size={buffer_size}, flush_interval={flush_interval}s)"
        )
    
    def write(self, log_entry: str) -> None:
        """
        Write a log entry asynchronously.
        
        Adds the entry to the buffer queue. The entry will be written to disk
        by the background thread, either when the buffer is full or after the
        flush interval expires.
        
        Args:
            log_entry: The log entry string to write
        """
        if self._shutdown_flag.is_set():
            logger.warning(
                f"AsyncLogWriter for {self.log_file} is shut down, "
                "cannot write new entries"
            )
            return
        
        try:
            self._queue.put(log_entry, block=False)
        except Exception as e:
            # Never let logging failures break the application
            logger.error(
                f"Failed to queue log entry for {self.log_file}: {e}",
                exc_info=True
            )
            self._errors += 1
    
    def flush(self) -> None:
        """
        Force immediate flush of buffered entries.
        
        Signals the background thread to write all buffered entries to disk
        immediately, regardless of buffer size or flush interval.
        """
        self._flush_requested.set()
        
        # Wait a short time for flush to complete
        time.sleep(0.1)
    
    def shutdown(self, timeout: float = 5.0) -> None:
        """
        Shutdown the async writer gracefully.
        
        Signals the background thread to stop, flushes all remaining buffered
        entries, and waits for the thread to terminate.
        
        Args:
            timeout: Maximum time (seconds) to wait for shutdown
        """
        if self._shutdown_flag.is_set():
            return
        
        logger.debug(f"Shutting down AsyncLogWriter for {self.log_file}")
        
        # Signal shutdown
        self._shutdown_flag.set()
        
        # Wait for writer thread to finish
        self._writer_thread.join(timeout=timeout)
        
        if self._writer_thread.is_alive():
            logger.warning(
                f"AsyncLogWriter thread for {self.log_file} did not "
                f"terminate within {timeout}s"
            )
        else:
            logger.debug(
                f"AsyncLogWriter for {self.log_file} shut down successfully "
                f"(entries={self._entries_written}, batches={self._batches_written}, "
                f"errors={self._errors})"
            )
    
    def _writer_loop(self) -> None:
        """
        Background thread loop for writing buffered entries.
        
        Continuously monitors the buffer queue and writes entries to disk
        in batches when the buffer is full or the flush interval expires.
        """
        buffer = []
        last_flush_time = time.time()
        
        while not self._shutdown_flag.is_set():
            try:
                # Check if flush is requested
                if self._flush_requested.is_set():
                    self._write_batch(buffer)
                    buffer.clear()
                    last_flush_time = time.time()
                    self._flush_requested.clear()
                    continue
                
                # Try to get an entry from the queue (with timeout)
                try:
                    entry = self._queue.get(timeout=0.1)
                    buffer.append(entry)
                except Empty:
                    pass
                
                # Check if we should flush based on buffer size or time
                current_time = time.time()
                time_since_flush = current_time - last_flush_time
                
                should_flush = (
                    len(buffer) >= self.buffer_size or
                    (buffer and time_since_flush >= self.flush_interval)
                )
                
                if should_flush:
                    self._write_batch(buffer)
                    buffer.clear()
                    last_flush_time = current_time
                    
            except Exception as e:
                logger.error(
                    f"Error in AsyncLogWriter loop for {self.log_file}: {e}",
                    exc_info=True
                )
                self._errors += 1
        
        # Final flush on shutdown
        if buffer:
            self._write_batch(buffer)
            buffer.clear()
        
        # Drain any remaining entries in the queue
        remaining = []
        while not self._queue.empty():
            try:
                remaining.append(self._queue.get_nowait())
            except Empty:
                break
        
        if remaining:
            self._write_batch(remaining)
    
    def _write_batch(self, entries: list) -> None:
        """
        Write a batch of log entries to disk.
        
        Args:
            entries: List of log entry strings to write
        """
        if not entries:
            return
        
        try:
            if self._rotating_handler:
                # Use rotating handler which handles rotation automatically
                for entry in entries:
                    # Create a log record and emit it through the handler
                    record = logging.LogRecord(
                        name="async_writer",
                        level=logging.INFO,
                        pathname="",
                        lineno=0,
                        msg=entry,
                        args=(),
                        exc_info=None
                    )
                    self._rotating_handler.emit(record)
            else:
                # Fall back to simple file writing
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    for entry in entries:
                        f.write(entry + '\n')
            
            self._entries_written += len(entries)
            self._batches_written += 1
            
        except Exception as e:
            # Never let logging failures break the application
            logger.error(
                f"Failed to write batch to {self.log_file}: {e}",
                exc_info=True
            )
            self._errors += 1
    
    def get_stats(self) -> dict:
        """
        Get statistics about the async writer.
        
        Returns:
            Dictionary with statistics (entries_written, batches_written, errors, queue_size)
        """
        return {
            "entries_written": self._entries_written,
            "batches_written": self._batches_written,
            "errors": self._errors,
            "queue_size": self._queue.qsize()
        }


# Global registry of async writers for shutdown handling
_async_writers = []
_shutdown_registered = False


def register_async_writer(writer: AsyncLogWriter) -> None:
    """
    Register an async writer for automatic shutdown on exit.
    
    Args:
        writer: AsyncLogWriter instance to register
    """
    global _shutdown_registered
    
    _async_writers.append(writer)
    
    # Register shutdown handlers on first registration
    if not _shutdown_registered:
        atexit.register(_shutdown_all_writers)
        
        # Register signal handlers only in main thread
        # signal.signal() can only be called from the main thread
        if threading.current_thread() is threading.main_thread():
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, _signal_handler)
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, _signal_handler)
            logger.debug("Async writer signal handlers registered")
        else:
            logger.debug("Skipping signal handler registration (not in main thread)")
        
        _shutdown_registered = True
        logger.debug("Async writer shutdown handlers registered")


def _shutdown_all_writers() -> None:
    """Shutdown all registered async writers."""
    if not _async_writers:
        return
    
    logger.debug(f"Shutting down {len(_async_writers)} async writers")
    
    for writer in _async_writers:
        try:
            writer.shutdown(timeout=5.0)
        except Exception as e:
            logger.error(f"Error shutting down async writer: {e}", exc_info=True)
    
    _async_writers.clear()


def _signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down async writers")
    _shutdown_all_writers()
    sys.exit(0)
