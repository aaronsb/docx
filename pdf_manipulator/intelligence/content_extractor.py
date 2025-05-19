"""Content extraction processor using intelligence backends.

This module handles the extraction of text content from documents using
various AI backends for enhanced understanding.
"""
from pdf_manipulator.intelligence.processor import DocumentProcessor

# Create alias with new semantic name
class ContentExtractor(DocumentProcessor):
    """Extracts and enhances content using AI intelligence.
    
    This processor:
    - Extracts text from images/documents
    - Enhances content with AI understanding
    - Falls back to OCR when needed
    - Preserves semantic meaning during extraction
    """
    pass  # Inherits all functionality from DocumentProcessor