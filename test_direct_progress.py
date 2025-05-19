#!/usr/bin/env python3
"""Test direct conversion with progress tracking."""

from pathlib import Path
from pdf_manipulator.intelligence.markitdown import MarkitdownBackend

# Test file
pdf_path = Path("/home/aaron/Projects/ai/pdf_sources/AGA-State-of-the-States-2023.pdf")
output_dir = Path("/home/aaron/Projects/ai/docx/output_v2/test_direct_with_progress/")

# Create output directory
doc_dir = output_dir / pdf_path.stem
markdown_dir = doc_dir / "markdown"
markdown_dir.mkdir(parents=True, exist_ok=True)

# Create markitdown backend
backend = MarkitdownBackend()

# Process with progress
print("Starting direct conversion with progress...")
toc = backend.process_direct_document(
    document_path=pdf_path,
    output_dir=markdown_dir,
    base_filename=pdf_path.stem,
    show_progress=True,
)

print("\nConversion complete!")
print(f"Output: {toc.get('output_files', {}).get('markdown')}")
print(f"Stats: {toc.get('content_stats')}")