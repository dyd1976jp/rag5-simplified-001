#!/usr/bin/env python3
"""
Log compression utility script.

This script manually compresses old log files to save disk space.
It can be run as a standalone script or scheduled as a cron job.

Usage:
    python scripts/compress_logs.py [--log-dir DIRECTORY] [--days DAYS] [--dry-run]

Examples:
    # Compress all .log files older than 7 days in logs/ directory
    python scripts/compress_logs.py

    # Compress logs older than 30 days
    python scripts/compress_logs.py --days 30

    # Preview what would be compressed without actually compressing
    python scripts/compress_logs.py --dry-run

    # Compress logs in a specific directory
    python scripts/compress_logs.py --log-dir /path/to/logs
"""

import argparse
import gzip
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_log_files(
    log_dir: Path,
    days_old: int = 7,
    extensions: List[str] = ['.log']
) -> List[Path]:
    """
    Find log files older than specified days.
    
    Args:
        log_dir: Directory to search for log files
        days_old: Minimum age in days for files to be compressed
        extensions: List of file extensions to consider
    
    Returns:
        List of Path objects for files to compress
    """
    cutoff_time = datetime.now() - timedelta(days=days_old)
    files_to_compress = []
    
    if not log_dir.exists():
        logger.warning(f"Log directory does not exist: {log_dir}")
        return files_to_compress
    
    for file_path in log_dir.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Check if file has a log extension
        if file_path.suffix not in extensions:
            continue
        
        # Skip already compressed files
        if file_path.suffix == '.gz':
            continue
        
        # Check if file is old enough
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_mtime < cutoff_time:
            files_to_compress.append(file_path)
    
    return sorted(files_to_compress)


def compress_file(file_path: Path, remove_original: bool = True) -> bool:
    """
    Compress a file using gzip.
    
    Args:
        file_path: Path to the file to compress
        remove_original: Whether to remove the original file after compression
    
    Returns:
        True if compression succeeded, False otherwise
    """
    compressed_path = Path(str(file_path) + '.gz')
    
    try:
        # Check if compressed version already exists
        if compressed_path.exists():
            logger.warning(f"Compressed file already exists: {compressed_path}")
            return False
        
        # Compress the file
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Get file sizes for reporting
        original_size = file_path.stat().st_size
        compressed_size = compressed_path.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        logger.info(
            f"Compressed {file_path.name}: "
            f"{original_size:,} bytes -> {compressed_size:,} bytes "
            f"({compression_ratio:.1f}% reduction)"
        )
        
        # Remove original file if requested
        if remove_original:
            file_path.unlink()
            logger.debug(f"Removed original file: {file_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to compress {file_path}: {e}", exc_info=True)
        
        # Clean up partial compressed file if it exists
        if compressed_path.exists():
            try:
                compressed_path.unlink()
            except Exception:
                pass
        
        return False


def compress_logs(
    log_dir: Path,
    days_old: int = 7,
    dry_run: bool = False,
    remove_original: bool = True
) -> dict:
    """
    Compress old log files in a directory.
    
    Args:
        log_dir: Directory containing log files
        days_old: Minimum age in days for files to be compressed
        dry_run: If True, only show what would be compressed without actually compressing
        remove_original: Whether to remove original files after compression
    
    Returns:
        Dictionary with statistics (files_found, files_compressed, bytes_saved)
    """
    logger.info(f"Searching for log files older than {days_old} days in {log_dir}")
    
    # Find files to compress
    files_to_compress = find_log_files(log_dir, days_old)
    
    if not files_to_compress:
        logger.info("No log files found to compress")
        return {
            "files_found": 0,
            "files_compressed": 0,
            "bytes_saved": 0
        }
    
    logger.info(f"Found {len(files_to_compress)} log files to compress")
    
    if dry_run:
        logger.info("DRY RUN - No files will be compressed")
        for file_path in files_to_compress:
            file_size = file_path.stat().st_size
            logger.info(f"Would compress: {file_path} ({file_size:,} bytes)")
        
        total_size = sum(f.stat().st_size for f in files_to_compress)
        return {
            "files_found": len(files_to_compress),
            "files_compressed": 0,
            "bytes_saved": 0,
            "potential_bytes_saved": total_size
        }
    
    # Compress files
    files_compressed = 0
    bytes_saved = 0
    
    for file_path in files_to_compress:
        original_size = file_path.stat().st_size
        
        if compress_file(file_path, remove_original):
            files_compressed += 1
            
            # Calculate bytes saved (original size - compressed size)
            compressed_path = Path(str(file_path) + '.gz')
            if compressed_path.exists():
                compressed_size = compressed_path.stat().st_size
                bytes_saved += (original_size - compressed_size)
    
    logger.info(
        f"Compression complete: {files_compressed}/{len(files_to_compress)} files compressed, "
        f"{bytes_saved:,} bytes saved"
    )
    
    return {
        "files_found": len(files_to_compress),
        "files_compressed": files_compressed,
        "bytes_saved": bytes_saved
    }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Compress old log files to save disk space",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compress all .log files older than 7 days in logs/ directory
  python scripts/compress_logs.py

  # Compress logs older than 30 days
  python scripts/compress_logs.py --days 30

  # Preview what would be compressed without actually compressing
  python scripts/compress_logs.py --dry-run

  # Compress logs in a specific directory
  python scripts/compress_logs.py --log-dir /path/to/logs
        """
    )
    
    parser.add_argument(
        '--log-dir',
        type=str,
        default='logs',
        help='Directory containing log files (default: logs)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Compress files older than this many days (default: 7)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be compressed without actually compressing'
    )
    
    parser.add_argument(
        '--keep-original',
        action='store_true',
        help='Keep original files after compression (default: remove)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert log directory to Path
    log_dir = Path(args.log_dir)
    
    # Run compression
    try:
        stats = compress_logs(
            log_dir=log_dir,
            days_old=args.days,
            dry_run=args.dry_run,
            remove_original=not args.keep_original
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("COMPRESSION SUMMARY")
        print("=" * 60)
        print(f"Files found:      {stats['files_found']}")
        print(f"Files compressed: {stats['files_compressed']}")
        
        if args.dry_run:
            potential_saved = stats.get('potential_bytes_saved', 0)
            print(f"Potential space saved: {potential_saved:,} bytes ({potential_saved / 1024 / 1024:.2f} MB)")
        else:
            bytes_saved = stats['bytes_saved']
            print(f"Space saved:      {bytes_saved:,} bytes ({bytes_saved / 1024 / 1024:.2f} MB)")
        
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during log compression: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
