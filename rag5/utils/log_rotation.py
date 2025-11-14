"""
Log rotation utilities with automatic compression support.

This module provides rotating file handlers that support both size-based
and time-based rotation with automatic gzip compression of rotated files.
"""

import gzip
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class CompressingRotatingFileHandler(RotatingFileHandler):
    """
    Rotating file handler with automatic gzip compression.
    
    Extends RotatingFileHandler to automatically compress rotated log files
    using gzip compression. This saves disk space while maintaining log history.
    
    Attributes:
        compress: Whether to compress rotated files
    
    Example:
        >>> handler = CompressingRotatingFileHandler(
        ...     filename="logs/app.log",
        ...     maxBytes=10*1024*1024,  # 10MB
        ...     backupCount=5,
        ...     compress=True
        ... )
        >>> logger.addHandler(handler)
    """
    
    def __init__(
        self,
        filename: str,
        mode: str = 'a',
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: Optional[str] = None,
        delay: bool = False,
        compress: bool = True
    ):
        """
        Initialize the handler with compression support.
        
        Args:
            filename: Path to the log file
            mode: File opening mode (default 'a' for append)
            maxBytes: Maximum size in bytes before rotation
            backupCount: Number of backup files to keep
            encoding: File encoding (default None for platform default)
            delay: Whether to delay file opening until first emit
            compress: Whether to compress rotated files
        """
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress = compress
    
    def doRollover(self):
        """
        Perform a rollover and compress the rotated file.
        
        This method is called when the log file reaches maxBytes.
        It rotates the file and optionally compresses it.
        """
        # Close the current file
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Rotate existing backup files
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}")
                
                # Check for both compressed and uncompressed versions
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
                elif os.path.exists(f"{sfn}.gz"):
                    if os.path.exists(f"{dfn}.gz"):
                        os.remove(f"{dfn}.gz")
                    os.rename(f"{sfn}.gz", f"{dfn}.gz")
            
            # Rotate the current file to .1
            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            if os.path.exists(dfn):
                os.remove(dfn)
            if os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dfn)
                
                # Compress the rotated file if enabled
                if self.compress:
                    self._compress_file(dfn)
        
        # Open a new file
        if not self.delay:
            self.stream = self._open()
    
    def _compress_file(self, filename: str) -> None:
        """
        Compress a file using gzip.
        
        Args:
            filename: Path to the file to compress
        """
        try:
            compressed_filename = f"{filename}.gz"
            
            with open(filename, 'rb') as f_in:
                with gzip.open(compressed_filename, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the original uncompressed file
            os.remove(filename)
            
            logger.debug(f"Compressed rotated log file: {compressed_filename}")
            
        except Exception as e:
            logger.error(f"Failed to compress log file {filename}: {e}", exc_info=True)


class CompressingTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Timed rotating file handler with automatic gzip compression.
    
    Extends TimedRotatingFileHandler to automatically compress rotated log files
    using gzip compression. This saves disk space while maintaining log history.
    
    Attributes:
        compress: Whether to compress rotated files
    
    Example:
        >>> handler = CompressingTimedRotatingFileHandler(
        ...     filename="logs/app.log",
        ...     when="midnight",
        ...     interval=1,
        ...     backupCount=7,
        ...     compress=True
        ... )
        >>> logger.addHandler(handler)
    """
    
    def __init__(
        self,
        filename: str,
        when: str = 'h',
        interval: int = 1,
        backupCount: int = 0,
        encoding: Optional[str] = None,
        delay: bool = False,
        utc: bool = False,
        atTime: Optional[object] = None,
        compress: bool = True
    ):
        """
        Initialize the handler with compression support.
        
        Args:
            filename: Path to the log file
            when: Type of interval ('S', 'M', 'H', 'D', 'midnight', 'W0'-'W6')
            interval: Interval multiplier
            backupCount: Number of backup files to keep
            encoding: File encoding (default None for platform default)
            delay: Whether to delay file opening until first emit
            utc: Whether to use UTC time
            atTime: Time of day for daily rotation
            compress: Whether to compress rotated files
        """
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime)
        self.compress = compress
    
    def doRollover(self):
        """
        Perform a rollover and compress the rotated file.
        
        This method is called when the time interval is reached.
        It rotates the file and optionally compresses it.
        """
        # Close the current file
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Get the time that this sequence started at and make it a TimeTuple
        currentTime = int(self.rolloverAt - self.interval)
        dstNow = time.localtime(currentTime)[-1]
        t = self.computeRollover(currentTime) - self.interval
        
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        
        dfn = self.rotation_filename(self.baseFilename + "." + time.strftime(self.suffix, timeTuple))
        
        if os.path.exists(dfn):
            os.remove(dfn)
        
        # Rename the current file
        self.rotate(self.baseFilename, dfn)
        
        # Compress the rotated file if enabled
        if self.compress:
            self._compress_file(dfn)
        
        # Delete old backup files if backupCount is set
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        
        # Open a new file
        if not self.delay:
            self.stream = self._open()
        
        # Update rollover time
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        
        # If DST changes and midnight or weekly rollover, adjust
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        
        self.rolloverAt = newRolloverAt
    
    def _compress_file(self, filename: str) -> None:
        """
        Compress a file using gzip.
        
        Args:
            filename: Path to the file to compress
        """
        try:
            compressed_filename = f"{filename}.gz"
            
            with open(filename, 'rb') as f_in:
                with gzip.open(compressed_filename, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the original uncompressed file
            os.remove(filename)
            
            logger.debug(f"Compressed rotated log file: {compressed_filename}")
            
        except Exception as e:
            logger.error(f"Failed to compress log file {filename}: {e}", exc_info=True)
    
    def getFilesToDelete(self):
        """
        Get list of files to delete based on backupCount.
        
        Overrides parent method to handle both compressed and uncompressed files.
        
        Returns:
            List of file paths to delete
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                # Handle both .gz and non-.gz files
                suffix = fileName[plen:]
                if suffix.endswith('.gz'):
                    suffix = suffix[:-3]
                
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        
        return result


# Import time module for TimedRotatingFileHandler
import time


def create_rotating_handler(
    log_file: str,
    rotation_type: str = "size",
    max_bytes: int = 10 * 1024 * 1024,
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 5,
    compress: bool = True,
    encoding: str = "utf-8"
) -> logging.Handler:
    """
    Create a rotating file handler based on configuration.
    
    Args:
        log_file: Path to the log file
        rotation_type: Type of rotation ("size" or "time")
        max_bytes: Maximum file size for size-based rotation
        when: Time interval for time-based rotation
        interval: Interval multiplier for time-based rotation
        backup_count: Number of backup files to keep
        compress: Whether to compress rotated files
        encoding: File encoding
    
    Returns:
        Configured rotating file handler
    
    Raises:
        ValueError: If rotation_type is invalid
    
    Example:
        >>> # Size-based rotation
        >>> handler = create_rotating_handler(
        ...     log_file="logs/app.log",
        ...     rotation_type="size",
        ...     max_bytes=10*1024*1024,
        ...     backup_count=5
        ... )
        >>> 
        >>> # Time-based rotation (daily at midnight)
        >>> handler = create_rotating_handler(
        ...     log_file="logs/app.log",
        ...     rotation_type="time",
        ...     when="midnight",
        ...     backup_count=7
        ... )
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    if rotation_type.lower() == "size":
        handler = CompressingRotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            compress=compress
        )
        logger.debug(
            f"Created size-based rotating handler for {log_file} "
            f"(max_bytes={max_bytes}, backup_count={backup_count}, compress={compress})"
        )
    
    elif rotation_type.lower() == "time":
        handler = CompressingTimedRotatingFileHandler(
            filename=log_file,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding=encoding,
            compress=compress
        )
        logger.debug(
            f"Created time-based rotating handler for {log_file} "
            f"(when={when}, interval={interval}, backup_count={backup_count}, compress={compress})"
        )
    
    else:
        raise ValueError(f"Invalid rotation_type: {rotation_type}. Must be 'size' or 'time'.")
    
    return handler
