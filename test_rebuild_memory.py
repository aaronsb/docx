#!/usr/bin/env python3
"""Test script for memory rebuild functionality."""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pdf_manipulator.core.pipeline import DocumentProcessor
from pdf_manipulator.utils.logging_config import get_logger

logger = get_logger("test_rebuild")

def test_rebuild():
    """Test the rebuild_memory_from_extracted_data functionality."""
    
    # Example paths - modify these to match your test data
    output_dir = Path("output")
    
    # Look for an existing contents file to test with
    contents_files = list(output_dir.glob("*/*_contents.json"))
    
    if not contents_files:
        print("No extracted documents found in output directory")
        print("Please run 'mge extract <pdf_file>' first to generate test data")
        return
    
    # Use the first found file
    contents_file = contents_files[0]
    test_doc_name = contents_file.parent.parent.name
    
    if not contents_file.exists():
        print(f"Error: Test file not found at {contents_file}")
        print("Please run 'mge extract <pdf_file>' first to generate test data")
        return
    
    print(f"Testing rebuild with: {contents_file}")
    
    # Check if memory database already exists
    memory_db = output_dir / test_doc_name / "memory_graph.db"
    if memory_db.exists():
        print(f"Found existing database at: {memory_db}")
        print("Removing it to test rebuild...")
        os.remove(memory_db)
    
    # Create document processor
    processor = DocumentProcessor(
        output_dir=output_dir,
        ai_transcriber=None,
        ocr_processor=None
    )
    
    try:
        # Rebuild memory from extracted data
        print("Rebuilding memory database...")
        new_db_path = processor.rebuild_memory_from_extracted_data(
            contents_file=contents_file,
            domain="test_rebuild"
        )
        
        print(f"Success! Memory database rebuilt at: {new_db_path}")
        
        # Verify the database was created
        if new_db_path.exists():
            file_size = new_db_path.stat().st_size
            print(f"Database size: {file_size:,} bytes")
        else:
            print("Error: Database file was not created")
            
    except Exception as e:
        print(f"Error during rebuild: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rebuild()