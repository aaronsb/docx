"""PDF Document core functionality."""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

import fitz  # PyMuPDF

from pdf_manipulator.core.exceptions import DocumentError


class Document:
    """Core PDF document class for manipulation operations."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize a PDF document.
        
        Args:
            file_path: Path to the PDF file
        
        Raises:
            DocumentError: If the file does not exist or is not a valid PDF
        """
        self.file_path = Path(file_path)
        self.filename = str(self.file_path.name)
        
        if not self.file_path.exists():
            raise DocumentError(f"File not found: {self.file_path}")
        
        try:
            self.doc = fitz.open(self.file_path)
            self.page_count = len(self.doc)
            self.num_pages = self.page_count  # Alias for compatibility
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
    
    def get_info(self) -> Dict[str, Any]:
        """Get document metadata/info.
        
        Returns:
            Dictionary with document metadata
        """
        return self.metadata
            
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
    
    def get_toc(self) -> List[Dict[str, Any]]:
        """Extract the table of contents (document outline) from the PDF.
        
        Returns:
            List of TOC entries, each with title, page number, and level.
            Empty list if no TOC exists.
            
        Example output:
            [
                {"title": "Chapter 1", "page": 1, "level": 1},
                {"title": "Section 1.1", "page": 2, "level": 2},
                {"title": "Chapter 2", "page": 10, "level": 1}
            ]
        """
        try:
            # Get raw TOC data (list of tuples)
            raw_toc = self.doc.get_toc()
            
            # Process each TOC entry
            processed_toc = []
            for entry in raw_toc:
                level, title, page = entry[:3]
                
                # Format the entry (PyMuPDF page numbers are 1-based)
                processed_entry = {
                    "level": level,
                    "title": title,
                    "page": page,  # 1-based page number
                    "page_index": page - 1,  # 0-based page index
                }
                
                processed_toc.append(processed_entry)
            
            return processed_toc
        
        except Exception as e:
            # If extraction fails, return empty list rather than raising an error
            # This is because not all PDFs have a TOC
            return []
    
    def has_toc(self) -> bool:
        """Check if the document has a table of contents.
        
        Returns:
            True if the document has a TOC, False otherwise
        """
        return len(self.get_toc()) > 0


# Keep PDFDocument as an alias for backward compatibility
PDFDocument = Document