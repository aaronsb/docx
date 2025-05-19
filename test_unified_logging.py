#!/usr/bin/env python3
"""Test unified logging system."""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_manipulator.utils.logging_config import get_logger, configure_logging, LogMessages
from pdf_manipulator.utils.progress import DirectConversionProgress, ProcessingProgress
from rich.console import Console

console = Console()


def test_logging_levels():
    """Test different logging levels."""
    print("Testing Logging Levels")
    print("=" * 50)
    
    # Test different log levels
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    
    for level in levels:
        print(f"\n[Testing {level} level]")
        configure_logging(console_level=level, enable_file=False)
        
        logger = get_logger("test")
        logger.debug("This is a DEBUG message")
        logger.info("This is an INFO message")
        logger.warning("This is a WARNING message")
        logger.error("This is an ERROR message")
        
        time.sleep(0.5)


def test_module_logging():
    """Test logging from different modules."""
    print("\n\nTesting Module-Specific Logging")
    print("=" * 50)
    
    configure_logging(console_level='INFO', enable_file=False)
    
    modules = ["pipeline", "markitdown", "intelligence", "memory", "progress"]
    
    for module in modules:
        logger = get_logger(module)
        logger.info(f"Log message from {module} module")
        time.sleep(0.2)


def test_progress_with_logging():
    """Test progress tracking with logging."""
    print("\n\nTesting Progress with Logging")
    print("=" * 50)
    
    configure_logging(console_level='INFO', enable_file=False)
    logger = get_logger("test")
    
    # Test direct conversion progress
    progress = DirectConversionProgress(Path("test_document.pdf"))
    progress.show_conversion_start()
    
    time.sleep(1)
    progress.update_status("Converting document to markdown...")
    
    time.sleep(1)
    progress.update_status("Extracting document structure...")
    
    time.sleep(1)
    progress.update_status("Saving markdown output...")
    
    stats = {
        "total_characters": 15000,
        "total_words": 2500,
        "total_lines": 300
    }
    progress.show_conversion_complete(stats)


def test_log_messages():
    """Test predefined log messages."""
    print("\n\nTesting Predefined Log Messages")
    print("=" * 50)
    
    configure_logging(console_level='INFO', enable_file=False)
    logger = get_logger("test")
    
    # Test various message formats
    logger.info(LogMessages.STAGE_START.format(stage="Document Processing"))
    time.sleep(0.5)
    
    logger.info(LogMessages.DOC_LOAD.format(filename="test_document.pdf"))
    time.sleep(0.5)
    
    logger.info(LogMessages.DOC_CONVERT.format(backend="markitdown"))
    time.sleep(0.5)
    
    # Simulate page processing
    for i in range(1, 4):
        logger.info(LogMessages.PAGE_TRANSCRIBE.format(current=i, total=3))
        time.sleep(0.3)
        logger.info(LogMessages.PAGE_MARKDOWN.format(current=i, total=3))
        time.sleep(0.3)
    
    logger.info(LogMessages.MEMORY_STORE.format(item_type="document"))
    time.sleep(0.5)
    
    logger.info(LogMessages.STAGE_COMPLETE.format(stage="Document Processing", duration=3.14))


if __name__ == "__main__":
    test_logging_levels()
    test_module_logging()
    test_progress_with_logging()
    test_log_messages()