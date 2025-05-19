#!/usr/bin/env python3
"""Test improved progress messages."""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_manipulator.utils.progress import DirectConversionProgress
from rich.console import Console

console = Console()


def test_direct_conversion_progress():
    """Test the improved progress messages for direct conversion."""
    print("Testing Direct Conversion Progress")
    print("=" * 50)
    
    # Create mock document path
    doc_path = Path("test_document.pdf")
    
    # Initialize progress
    progress = DirectConversionProgress(doc_path)
    progress.show_conversion_start()
    
    # Simulate different stages
    time.sleep(1)
    progress.update_status("Converting document to markdown...")
    
    time.sleep(2)
    progress.update_status("Extracting document structure...")
    
    time.sleep(1.5)
    progress.update_status("Processing table of contents...")
    
    time.sleep(1)
    progress.update_status("Saving markdown output...")
    
    time.sleep(0.5)
    
    # Show completion
    stats = {
        "total_characters": 152435,
        "total_words": 23456,
        "total_lines": 2154
    }
    progress.show_conversion_complete(stats)
    
    print("\nTest completed!")


def test_status_messages():
    """Test various status message formats."""
    print("\n\nTesting Status Message Formats")
    print("=" * 50)
    
    messages = [
        "Initializing markitdown...",
        "Converting document to markdown...",
        "Processing page content...",
        "Extracting document structure...",
        "Detecting table of contents...",
        "Processing table of contents...",
        "Mapping content to sections...",
        "Building memory graph...",
        "Saving markdown output...",
        "Creating content statistics...",
        "Finalizing document..."
    ]
    
    from rich.status import Status
    
    for message in messages:
        with console.status(f"[cyan]{message}[/cyan]", spinner="dots") as status:
            time.sleep(0.5)
        console.print(f"✓ {message}")


if __name__ == "__main__":
    test_direct_conversion_progress()
    test_status_messages()