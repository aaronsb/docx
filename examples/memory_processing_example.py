#!/usr/bin/env python3
"""
Example: Process a PDF and store contents in a memory graph database.

This example demonstrates how to:
1. Process a PDF document with AI transcription
2. Store the extracted content in a memory graph SQLite database
3. Query the stored memories for later use
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_manipulator.core.pipeline import DocumentProcessor
from pdf_manipulator.extractors.ocr import OCRProcessor
from pdf_manipulator.intelligence.processor import create_processor
from pdf_manipulator.memory.memory_adapter import MemoryConfig, MemoryAdapter
from pdf_manipulator.utils.config import load_config


def process_pdf_with_memory(
    pdf_path: str,
    output_dir: str = "output",
    backend: str = "ollama",
    use_memory: bool = True
):
    """Process a PDF and store in memory graph."""
    print(f"Processing {pdf_path} with {backend} backend...")
    
    # Load configuration
    try:
        config = load_config()
    except:
        config = {}
    
    # Set up OCR processor
    ocr_processor = OCRProcessor()
    
    # Set up AI processor
    intelligence_processor = None
    try:
        intelligence_processor = create_processor(
            config=config,
            ocr_processor=ocr_processor,
            backend_name=backend,
        )
    except Exception as e:
        print(f"Could not initialize {backend} backend: {e}")
        print("Falling back to OCR only")
    
    # Set up memory configuration
    memory_config = None
    if use_memory:
        memory_config = MemoryConfig(
            database_path=Path(output_dir) / "memory_graph.db",
            domain_name="pdf_processing",
            domain_description="PDF document processing and extraction",
            enable_relationships=True,
            enable_summaries=True,
            tags_prefix="pdf:",
            min_content_length=50,
        )
    
    # Create document processor
    document_processor = DocumentProcessor(
        output_dir=output_dir,
        renderer_kwargs={"dpi": 300},
        ocr_processor=ocr_processor,
        ai_transcriber=intelligence_processor,
        memory_config=memory_config,
        intelligence_processor=intelligence_processor,
    )
    
    # Process the PDF
    result = document_processor.process_pdf(
        pdf_path=pdf_path,
        use_ai=intelligence_processor is not None,
        store_in_memory=use_memory,
    )
    
    print("\n✓ Document processed successfully!")
    
    # Display results
    stats = result.get("stats", {})
    memory_info = result.get("memory_storage", {})
    perf = result.get("performance", {})
    
    print(f"\nResults:")
    print(f"- Pages processed: {stats.get('processed_pages', 0)}")
    print(f"- Processing time: {perf.get('total_duration_formatted', 'N/A')}")
    
    if memory_info.get("enabled"):
        print(f"\nMemory Storage:")
        print(f"- Database: {memory_info.get('database_path')}")
        print(f"- Document ID: {memory_info.get('document_id')}")
        print(f"- Pages stored: {len(memory_info.get('page_memories', {}))}")
        print(f"- Sections found: {len(memory_info.get('section_memories', {}))}")
    
    return result


def query_memories(database_path: str, query: str):
    """Query the memory graph for related content."""
    print(f"\nQuerying memories for: '{query}'")
    
    # Connect to memory database
    memory_config = MemoryConfig(
        database_path=Path(database_path),
        domain_name="pdf_processing",
    )
    
    adapter = MemoryAdapter(memory_config)
    adapter.connect()
    
    # Search memories
    results = adapter.search_memories(query, limit=5)
    
    print(f"\nFound {len(results)} relevant memories:")
    for i, memory in enumerate(results):
        print(f"\n{i+1}. {memory['path']}")
        print(f"   Tags: {', '.join(memory['tags'])}")
        content_preview = memory['content'][:200] + "..." if len(memory['content']) > 200 else memory['content']
        print(f"   Content: {content_preview}")
        if memory.get('content_summary'):
            print(f"   Summary: {memory['content_summary']}")
    
    # Get recent memories
    print("\n\nRecent memories:")
    recent = adapter.get_recent_memories(limit=3)
    for i, memory in enumerate(recent):
        print(f"\n{i+1}. {memory['path']} ({memory['timestamp']})")
        print(f"   Tags: {', '.join(memory['tags'])}")
    
    adapter.disconnect()


def main():
    """Main example execution."""
    # Example 1: Process a PDF with memory storage
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        print("Usage: python memory_processing_example.py <pdf_file>")
        print("Or run with default example")
        # Use a sample PDF if available
        pdf_file = "sample.pdf"
    
    if Path(pdf_file).exists():
        # Process the PDF
        result = process_pdf_with_memory(
            pdf_path=pdf_file,
            output_dir="memory_output",
            backend="ollama",  # or "llama_cpp" or "llama_cpp_http"
            use_memory=True
        )
        
        # Example 2: Query the stored memories
        memory_db = result["memory_storage"]["database_path"]
        if memory_db and Path(memory_db).exists():
            # Query for specific content
            query_memories(memory_db, "table of contents")
            query_memories(memory_db, "introduction")
            query_memories(memory_db, "conclusion")
    else:
        print(f"Error: File '{pdf_file}' not found")
        print("\nTo run this example:")
        print("1. Make sure you have Ollama running with 'llava' model")
        print("2. Provide a PDF file: python memory_processing_example.py yourfile.pdf")


if __name__ == "__main__":
    main()