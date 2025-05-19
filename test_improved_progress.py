#!/usr/bin/env python3
"""Test the improved single-line progress display."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_manipulator.core.pipeline import DocumentProcessor
from pdf_manipulator.utils.config import load_config
from pdf_manipulator.extractors.ocr import OCRProcessor

def test_progress():
    """Test the improved progress display with a small PDF."""
    # Load config
    config = load_config()
    
    # Use a small test PDF
    pdf_path = "/home/aaron/Projects/ai/pdf_sources/AGA-State-of-the-States-2023.pdf"
    output_dir = "/home/aaron/Projects/ai/docx/output_v2/test_new_progress/"
    
    # Initialize OCR
    ocr_processor = OCRProcessor(language="eng")
    
    # Create document processor
    processor = DocumentProcessor(
        output_dir=output_dir,
        renderer_kwargs={"dpi": 200},  # Lower DPI for faster testing
        ocr_processor=ocr_processor,
    )
    
    print("Testing improved progress display...\n")
    
    # Process only first 5 pages for quick test
    toc = processor.process_pdf(
        pdf_path=pdf_path,
        use_ai=False,  # Use OCR only for faster testing
        page_range=[0, 1, 2, 3, 4],  # First 5 pages
        show_progress=True,
    )
    
    print("\nProcessing complete!")
    print(f"Pages processed: {toc['stats']['processed_pages']}")
    print(f"Method: {toc['stats']['transcription_method']}")
    print(f"Total time: {toc['performance']['total_duration_formatted']}")

if __name__ == "__main__":
    test_progress()