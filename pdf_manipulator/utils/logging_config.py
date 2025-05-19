"""Centralized logging configuration for the PDF Manipulator."""
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console


# Global console instance for rich output
console = Console()


class PDFManipulatorLogger:
    """Centralized logger configuration for the entire application."""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger configuration."""
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Set up the root logger with Rich handler."""
        # Create root logger
        self._logger = logging.getLogger("pdf_manipulator")
        self._logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self._logger.handlers.clear()
        
        # Create Rich handler for console output
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setLevel(logging.INFO)  # Default console level
        
        # Create formatter for console
        console_format = "%(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))
        
        # Add handler to logger
        self._logger.addHandler(console_handler)
        
        # Optionally add file handler for debugging
        log_dir = Path.home() / ".pdf_manipulator" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / "pdf_manipulator.log",
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        
        self._logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger for a specific module.
        
        Args:
            name: Module name (e.g., 'pipeline', 'markitdown', 'memory')
            
        Returns:
            Logger instance for the module
        """
        return self._logger.getChild(name)
    
    def set_console_level(self, level: str):
        """Set the console logging level.
        
        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
        }
        
        if level.upper() in level_map:
            for handler in self._logger.handlers:
                if isinstance(handler, RichHandler):
                    handler.setLevel(level_map[level.upper()])
    
    def enable_verbose(self):
        """Enable verbose (DEBUG) logging to console."""
        self.set_console_level('DEBUG')
    
    def disable_file_logging(self):
        """Disable file logging (useful for testing)."""
        for handler in self._logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                self._logger.removeHandler(handler)


# Global logger factory
logger_factory = PDFManipulatorLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.
    
    Args:
        name: Module name
        
    Returns:
        Logger instance
    """
    return logger_factory.get_logger(name)


def configure_logging(console_level: str = "INFO", enable_file: bool = True):
    """Configure logging for the application.
    
    Args:
        console_level: Console logging level
        enable_file: Whether to enable file logging
    """
    logger_factory.set_console_level(console_level)
    if not enable_file:
        logger_factory.disable_file_logging()


# Predefined log messages for consistent formatting
class LogMessages:
    """Predefined log message templates."""
    
    # Processing stages
    STAGE_START = "[cyan]Starting:[/cyan] {stage}"
    STAGE_COMPLETE = "[green]Completed:[/green] {stage} ({duration:.2f}s)"
    STAGE_FAILED = "[red]Failed:[/red] {stage} - {error}"
    
    # Page processing
    PAGE_RENDER = "Rendering page {current}/{total}"
    PAGE_TRANSCRIBE = "Transcribing page {current}/{total}"
    PAGE_MARKDOWN = "Creating markdown for page {current}/{total}"
    PAGE_COMPLETE = "Page {page} processed successfully"
    
    # Document processing
    DOC_LOAD = "Loading document: {filename}"
    DOC_CONVERT = "Converting document with {backend}"
    DOC_SAVE = "Saving output to: {path}"
    
    # Memory operations
    MEMORY_STORE = "Storing in memory: {item_type}"
    MEMORY_TOC = "Detected TOC with {count} entries"
    MEMORY_GRAPH = "Building memory graph relationships"
    
    # Status updates
    STATUS_UPDATE = "[dim]{message}[/dim]"
    PROGRESS_UPDATE = "{task}: {current}/{total} ({percent}%)"