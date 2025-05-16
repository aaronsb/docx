#!/usr/bin/env python3
"""
Example: Memory-enhanced PDF processing with context queries.

This example demonstrates how to:
1. Use previously stored memories to enhance processing of new documents
2. Query memory graph for context during AI transcription
3. Create relationships between documents
"""

import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_manipulator.core.pipeline import DocumentProcessor
from pdf_manipulator.extractors.ocr import OCRProcessor
from pdf_manipulator.intelligence.processor import create_processor
from pdf_manipulator.intelligence.memory_enhanced import MemoryEnhancedBackend
from pdf_manipulator.memory.memory_adapter import MemoryConfig, MemoryAdapter
from pdf_manipulator.memory.memory_processor import MemoryProcessor
from pdf_manipulator.utils.config import load_config


def process_with_enhanced_memory(
    pdf_path: str,
    memory_db_path: str,
    output_dir: str = "output",
    backend: str = "ollama"
):
    """Process a PDF using existing memories for enhanced context."""
    print(f"Processing {pdf_path} with memory-enhanced {backend} backend...")
    
    # Load configuration
    try:
        config = load_config()
    except:
        config = {}
    
    # Set up OCR processor
    ocr_processor = OCRProcessor()
    
    # Set up base AI processor
    base_processor = create_processor(
        config=config,
        ocr_processor=ocr_processor,
        backend_name=backend,
    )
    
    # Set up memory configuration for enhancement
    memory_config = MemoryConfig(
        database_path=Path(memory_db_path),
        domain_name="pdf_processing",
    )
    
    # Create memory-enhanced processor
    enhanced_processor = MemoryEnhancedBackend(
        base_backend=base_processor,
        memory_config=memory_config,
        max_context_memories=5,
        enable_memory_queries=True
    )
    
    # Set up memory configuration for storage
    storage_memory_config = MemoryConfig(
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
        ai_transcriber=enhanced_processor,
        memory_config=storage_memory_config,
        intelligence_processor=enhanced_processor,
    )
    
    # Process the PDF with memory enhancement
    result = document_processor.process_pdf(
        pdf_path=pdf_path,
        use_ai=True,
        store_in_memory=True,
    )
    
    print("\n✓ Document processed with memory enhancement!")
    
    # Display results
    stats = result.get("stats", {})
    memory_info = result.get("memory_storage", {})
    
    print(f"\nResults:")
    print(f"- Pages processed: {stats.get('processed_pages', 0)}")
    print(f"- Memory context used: {memory_config.database_name}")
    
    if memory_info.get("enabled"):
        print(f"- New memories stored: {len(memory_info.get('page_memories', {}))}")
        print(f"- Document ID: {memory_info.get('document_id')}")
    
    return result


def link_related_documents(
    memory_db_path: str,
    doc1_id: str,
    doc2_id: str,
    relationship: str = "related_to"
):
    """Create relationships between documents in the memory graph."""
    print(f"\nLinking documents: {doc1_id} <-> {doc2_id}")
    
    memory_config = MemoryConfig(
        database_path=Path(memory_db_path),
        domain_name="pdf_processing",
    )
    
    with MemoryProcessor(memory_config) as processor:
        processor.link_related_documents(
            doc1_id=doc1_id,
            doc2_id=doc2_id,
            relationship_type=relationship,
            strength=0.8
        )
        
        print(f"✓ Documents linked with '{relationship}' relationship")


def visualize_document_graph(memory_db_path: str, document_id: str):
    """Show the knowledge graph for a document."""
    print(f"\nDocument graph for: {document_id}")
    
    memory_config = MemoryConfig(
        database_path=Path(memory_db_path),
        domain_name="pdf_processing",
    )
    
    with MemoryProcessor(memory_config) as processor:
        graph = processor.get_document_graph(
            document_id=document_id,
            max_depth=2
        )
        
        print(f"Nodes: {len(graph['nodes'])}")
        print(f"Edges: {len(graph['edges'])}")
        
        # Display some node information
        for node_id, node_data in list(graph['nodes'].items())[:5]:
            print(f"\nNode: {node_id[:8]}...")
            print(f"  Path: {node_data['path']}")
            print(f"  Tags: {', '.join(node_data['tags'])}")
            if node_data.get('summary'):
                print(f"  Summary: {node_data['summary'][:100]}...")


def main():
    """Main example execution."""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Process new PDF: python memory_enhanced_processing.py <pdf_file> [memory_db]")
        print("  Link documents: python memory_enhanced_processing.py --link <db> <doc1> <doc2>")
        print("  Show graph: python memory_enhanced_processing.py --graph <db> <doc_id>")
        return
    
    if sys.argv[1] == "--link" and len(sys.argv) >= 5:
        # Link two documents
        memory_db = sys.argv[2]
        doc1_id = sys.argv[3]
        doc2_id = sys.argv[4]
        relationship = sys.argv[5] if len(sys.argv) > 5 else "related_to"
        
        link_related_documents(memory_db, doc1_id, doc2_id, relationship)
        
    elif sys.argv[1] == "--graph" and len(sys.argv) >= 4:
        # Show document graph
        memory_db = sys.argv[2]
        doc_id = sys.argv[3]
        
        visualize_document_graph(memory_db, doc_id)
        
    else:
        # Process PDF with enhanced memory
        pdf_file = sys.argv[1]
        memory_db = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not Path(pdf_file).exists():
            print(f"Error: File '{pdf_file}' not found")
            return
        
        if memory_db and Path(memory_db).exists():
            # Use existing memory database for enhancement
            process_with_enhanced_memory(
                pdf_path=pdf_file,
                memory_db_path=memory_db,
                output_dir="enhanced_output",
                backend="ollama"
            )
        else:
            print("No memory database specified or found")
            print("Processing without memory enhancement")
            
            # Fall back to regular processing
            from memory_processing_example import process_pdf_with_memory
            process_pdf_with_memory(
                pdf_path=pdf_file,
                output_dir="output",
                backend="ollama",
                use_memory=True
            )


if __name__ == "__main__":
    main()