#!/usr/bin/env python3
"""Test script for TOC-based document processing."""
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_manipulator.memory.toc_processor import TOCProcessor
from pdf_manipulator.memory.memory_processor import MemoryProcessor
from pdf_manipulator.memory.memory_adapter import MemoryConfig
from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.core.pipeline import DocumentProcessor


def test_toc_detection():
    """Test TOC detection on sample content."""
    # Sample page content with TOC
    sample_pages = {
        0: """
        TABLE OF CONTENTS
        
        1. Introduction ........................... 5
        2. Background ............................ 8
           2.1 Historical Context ................. 10
           2.2 Current State ..................... 15
        3. Methodology ........................... 20
           3.1 Data Collection ................... 22
           3.2 Analysis Methods .................. 28
        4. Results .............................. 35
        5. Discussion ........................... 42
        6. Conclusion ........................... 48
        
        Appendix A .............................. 52
        References .............................. 55
        """,
        1: "Some content on page 1",
        5: "Introduction chapter content...",
        8: "Background chapter content...",
    }
    
    toc_processor = TOCProcessor()
    result = toc_processor.detect_toc(sample_pages)
    
    if result:
        toc_pages, toc_content = result
        print(f"✓ TOC detected on pages: {toc_pages}")
        
        # Parse the TOC
        toc_structure = toc_processor.parse_toc(toc_content, toc_pages)
        if toc_structure:
            print(f"✓ Parsed {len(toc_structure.entries)} TOC entries")
            
            # Display hierarchy
            for entry in toc_structure.root_entries:
                print(f"  {entry.number} {entry.title} -> page {entry.page}")
                for child in entry.children:
                    print(f"    {child.number} {child.title} -> page {child.page}")
            
            # Create blueprint
            blueprint = toc_processor.create_blueprint(toc_structure, sample_pages)
            print(f"\n✓ Created blueprint with {len(blueprint['page_mapping'])} mapped pages")
            print(f"  Orphan pages: {blueprint['orphan_pages']}")
    else:
        print("✗ No TOC detected")


def test_pdf_with_toc(pdf_path: str):
    """Test TOC processing with real PDF."""
    if not Path(pdf_path).exists():
        print(f"Error: File '{pdf_path}' not found")
        return
    
    print(f"\nProcessing PDF with TOC-first approach: {pdf_path}")
    
    # Set up memory config
    memory_config = MemoryConfig(
        database_path=Path("test_toc.db"),
        domain_name="toc_test",
        domain_description="Testing TOC-based processing",
    )
    
    # Create processor
    processor = DocumentProcessor(
        output_dir="output_toc_test",
        memory_config=memory_config,
    )
    
    # Process the PDF
    result = processor.process_pdf(
        pdf_path=pdf_path,
        store_in_memory=True,
    )
    
    # Display results
    memory_info = result.get("memory_storage", {})
    if memory_info:
        structure_method = memory_info.get("structure_method", "unknown")
        print(f"\n✓ Document processed using {structure_method} method")
        
        if memory_info.get("toc_structure"):
            toc = memory_info["toc_structure"]
            print(f"  TOC entries: {len(toc.entries)}")
            print(f"  Root sections: {len(toc.root_entries)}")
        
        print(f"  Sections created: {len(memory_info.get('section_memories', {}))}")
        print(f"  Pages processed: {len(memory_info.get('page_memories', {}))}")


def main():
    """Main test function."""
    print("Testing TOC Processing")
    print("=" * 50)
    
    # Test with sample content
    test_toc_detection()
    
    # Test with real PDF if provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_pdf_with_toc(pdf_path)
    else:
        print("\nTo test with a real PDF, run:")
        print(f"  python {sys.argv[0]} <pdf_file>")


if __name__ == "__main__":
    main()