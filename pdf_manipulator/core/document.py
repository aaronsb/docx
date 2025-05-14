"""PDF Document core functionality."""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

import fitz  # PyMuPDF

from pdf_manipulator.core.exceptions import DocumentError


class PDFDocument:
    """Core PDF document class for manipulation operations."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize a PDF document.
        
        Args:
            file_path: Path to the PDF file
        
        Raises:
            DocumentError: If the file does not exist or is not a valid PDF
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            raise DocumentError(f"File not found: {self.file_path}")
        
        try:
            self.doc = fitz.open(self.file_path)
            self.page_count = len(self.doc)
            self.metadata = self.doc.metadata
        except Exception as e:
            raise DocumentError(f"Error opening PDF: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
    
    def close(self):
        """Close the document and free resources."""
        if hasattr(self, 'doc') and self.doc:
            self.doc.close()
            
    def get_page(self, page_number: int):
        """Get a specific page from the document.
        
        Args:
            page_number: Zero-based page index
            
        Returns:
            The page object
            
        Raises:
            DocumentError: If the page number is invalid
        """
        if not 0 <= page_number < self.page_count:
            raise DocumentError(f"Invalid page number: {page_number}. Document has {self.page_count} pages.")
        
        return self.doc[page_number]
    
    def get_page_dimensions(self, page_number: int) -> Tuple[float, float]:
        """Get width and height of a page in points.
        
        Args:
            page_number: Zero-based page index
            
        Returns:
            Tuple of (width, height) in points
        """
        page = self.get_page(page_number)
        return page.rect.width, page.rect.height
    
    def get_text(self, page_number: Optional[int] = None) -> str:
        """Extract text from a page or the entire document.
        
        Args:
            page_number: Zero-based page index or None for all pages
            
        Returns:
            Extracted text content
        """
        if page_number is not None:
            page = self.get_page(page_number)
            return page.get_text()
        
        return "".join(page.get_text() for page in self.doc)