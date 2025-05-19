#!/usr/bin/env python3
"""Test direct conversion with markitdown backend."""

from pathlib import Path
from pdf_manipulator.intelligence.markitdown import MarkitdownBackend

def test_direct_conversion():
    """Test direct document conversion."""
    pdf_path = Path("/home/aaron/Projects/ai/pdf_sources/AGA-State-of-the-States-2023.pdf")
    output_dir = Path("/home/aaron/Projects/ai/docx/output_v2/test_direct/")
    
    # Create markitdown backend
    backend = MarkitdownBackend()
    
    # Create output directory
    doc_dir = output_dir / pdf_path.stem
    markdown_dir = doc_dir / "markdown"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing: {pdf_path}")
    print(f"Output to: {markdown_dir}")
    
    # Process document directly
    toc = backend.process_direct_document(
        document_path=pdf_path,
        output_dir=markdown_dir,
        base_filename=pdf_path.stem,
    )
    
    print("\nConversion complete!")
    print(f"TOC: {toc.get('toc_file')}")
    print(f"Markdown: {toc.get('output_files', {}).get('markdown')}")
    print(f"Content stats: {toc.get('content_stats')}")

if __name__ == "__main__":
    test_direct_conversion()