"""Progress tracking and visual output utilities."""
from typing import Optional, Dict, Any
from pathlib import Path
import time

from rich.console import Console
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.spinner import Spinner
from rich.status import Status

from .logging_config import get_logger, console, LogMessages

logger = get_logger("progress")


class ProcessingProgress:
    """Rich progress tracking for document processing."""
    
    def __init__(self, total_pages: Optional[int] = None):
        """Initialize progress tracking.
        
        Args:
            total_pages: Total number of pages (for page-based progress)
        """
        self.total_pages = total_pages
        self.current_stage = "Initializing"
        self.start_time = time.time()
        
        # Track different stages
        self.stages = {
            "initialization": "Initializing",
            "pdf_loading": "Loading PDF",
            "rendering": "Rendering Pages",
            "transcription": "Processing Content",
            "memory_storage": "Storing in Memory",
            "finalization": "Finalizing",
        }
        
        self.status_display = None
        self.stage_times = {}
        
    def start(self):
        """Start the progress tracking."""
        pass  # No longer using progress bars
        
    def stop(self):
        """Stop the progress tracking."""
        if self.status_display:
            self.status_display.stop()
            self.status_display = None
        
    def start_stage(self, stage: str, total: Optional[int] = None):
        """Start a new processing stage.
        
        Args:
            stage: Stage identifier
            total: Total items for this stage (for stages with progress tracking)
        """
        description = self.stages.get(stage, stage.replace("_", " ").title())
        
        # Stop any existing status display
        if self.status_display:
            self.status_display.stop()
            
        # Update current stage
        self.current_stage = description
        self.stage_times[stage] = {"start": time.time(), "total": total}
        
        # Log the stage start
        console.print(f"[cyan]Starting:[/cyan] {description}")
        
        # For stages with page-by-page progress, use status display
        if stage in ["rendering", "transcription"] and total:
            self.start_page_status(stage, total)
        
    def update_stage(self, stage: str, advance: int = 1):
        """Update progress for a stage.
        
        Args:
            stage: Stage identifier
            advance: How much to advance
        """
        # For page-tracking stages, updates are handled by update_page_status
        if stage in self.stage_times and "current" in self.stage_times[stage]:
            self.stage_times[stage]["current"] = self.stage_times[stage].get("current", 0) + advance
            
    def complete_stage(self, stage: str):
        """Mark a stage as complete.
        
        Args:
            stage: Stage identifier
        """
        # Stop any page status display
        if self.status_display and stage in ["rendering", "transcription"]:
            self.status_display.stop()
            self.status_display = None
            
        # Calculate and store stage duration
        if stage in self.stage_times:
            self.stage_times[stage]["end"] = time.time()
            duration = self.stage_times[stage]["end"] - self.stage_times[stage]["start"]
            self.stage_times[stage]["duration"] = duration
            
        console.print(f"[green]Completed:[/green] {self.stages.get(stage, stage)}")
            
    def log_message(self, message: str, style: str = ""):
        """Log a message with optional styling.
        
        Args:
            message: Message to log
            style: Rich style string
        """
        console.print(message, style=style)
        
    def start_page_status(self, stage: str, total_pages: int):
        """Start a status display for page-by-page processing.
        
        Args:
            stage: Stage name (rendering or transcription)
            total_pages: Total number of pages
        """
        if self.status_display:
            self.status_display.stop()
        
        self.status_display = console.status(
            f"[cyan]{self.stages.get(stage, stage)}[/cyan]: Starting...",
            spinner="dots"
        )
        self.status_display.start()
        self._page_total = total_pages
        self._current_stage = stage
        
    def update_page_status(self, current_page: int):
        """Update the page status display.
        
        Args:
            current_page: Current page number (1-based)
        """
        if self.status_display:
            stage_name = self.stages.get(self._current_stage, self._current_stage)
            status_message = f"[cyan]{stage_name}[/cyan]: Page {current_page}/{self._page_total}"
            self.status_display.update(status_message)
            
            # Log the progress for detailed tracking
            if self._current_stage == "rendering":
                logger.info(LogMessages.PAGE_RENDER.format(current=current_page, total=self._page_total))
            elif self._current_stage == "transcription":
                logger.info(LogMessages.PAGE_TRANSCRIBE.format(current=current_page, total=self._page_total))
            else:
                logger.info(f"{stage_name}: Page {current_page}/{self._page_total}")
            
    def stop_page_status(self):
        """Stop the page status display."""
        if self.status_display:
            self.status_display.stop()
            self.status_display = None
        
    def show_status_panel(self, stats: Dict[str, Any]):
        """Show a status panel with current statistics.
        
        Args:
            stats: Dictionary of statistics to display
        """
        # Create a table for stats
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in stats.items():
            table.add_row(key, str(value))
            
        # Create panel
        panel = Panel(
            table,
            title=f"[bold cyan]{self.current_stage}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
        
        console.print(panel)


class DirectConversionProgress:
    """Progress tracking specifically for direct markitdown conversion."""
    
    def __init__(self, document_path: Path):
        """Initialize direct conversion progress.
        
        Args:
            document_path: Path to the document
        """
        self.document_path = document_path
        self.start_time = time.time()
        self.status_display = None
        
    def show_conversion_start(self):
        """Show conversion start message."""
        logger.info(LogMessages.DOC_LOAD.format(filename=self.document_path.name))
        console.print()
        console.print(f"[bold cyan]Starting Direct Document Conversion[/bold cyan]")
        console.print(f"[dim]Document:[/dim] {self.document_path.name}")
        console.print()
        
        # Show spinner while converting
        self.status_display = console.status("[cyan]Initializing markitdown...[/cyan]")
        self.status_display.start()
        return self.status_display
        
    def update_status(self, message: str):
        """Update the status message.
        
        Args:
            message: New status message
        """
        logger.debug(f"Status: {message}")
        if self.status_display:
            self.status_display.update(f"[cyan]{message}[/cyan]")
            
    def show_conversion_complete(self, stats: Dict[str, Any]):
        """Show conversion completion with statistics.
        
        Args:
            stats: Content statistics
        """
        # Stop the status display
        if self.status_display:
            self.status_display.stop()
            self.status_display = None
            
        elapsed = time.time() - self.start_time
        
        # Create results table
        table = Table(title="[bold green]Conversion Complete[/bold green]", box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        
        table.add_row("Total Characters", f"{stats.get('total_characters', 0):,}")
        table.add_row("Total Words", f"{stats.get('total_words', 0):,}")
        table.add_row("Total Lines", f"{stats.get('total_lines', 0):,}")
        table.add_row("Conversion Time", f"{elapsed:.2f}s")
        
        console.print()
        console.print(table)
        console.print()


def create_processing_layout() -> Layout:
    """Create a rich layout for processing display.
    
    Returns:
        Layout object for rich display
    """
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    
    layout["body"].split_row(
        Layout(name="progress"),
        Layout(name="stats", size=40)
    )
    
    return layout


def format_time(seconds: float) -> str:
    """Format time in seconds to human readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining = seconds % 3600
        minutes = int(remaining // 60)
        secs = remaining % 60
        return f"{hours}h {minutes}m {secs:.1f}s"