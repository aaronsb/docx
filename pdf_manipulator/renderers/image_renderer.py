"""PDF page to image rendering functionality."""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

import fitz

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.core.exceptions import RenderError


class ImageRenderer:
    """Renderer for converting PDF pages to images."""

    def __init__(self, document: PDFDocument):
        """Initialize renderer with a PDF document.
        
        Args:
            document: PDFDocument instance
        """
        self.document = document
    
    def render_page_to_png(
        self, 
        page_number: int, 
        output_path: Union[str, Path],
        dpi: int = 300,
        alpha: bool = False,
        zoom: float = 1.0,
    ) -> Path:
        """Render a specific page to a PNG image.
        
        Args:
            page_number: Zero-based page index
            output_path: Path where to save the PNG
            dpi: Resolution in dots per inch
            alpha: Whether to include an alpha channel
            zoom: Additional zoom factor
            
        Returns:
            Path to the rendered image
            
        Raises:
            RenderError: If rendering fails
        """
        output_path = Path(output_path)
        
        try:
            page = self.document.get_page(page_number)
            
            # Calculate zoom factor based on DPI
            # 72 is the base DPI for PDFs
            zoom_factor = zoom * dpi / 72
            
            # Create pixmap
            matrix = fitz.Matrix(zoom_factor, zoom_factor)
            colorspace = "RGBA" if alpha else "RGB"  
            
            pix = page.get_pixmap(matrix=matrix, alpha=alpha, colorspace=colorspace)
            
            # Save pixmap
            pix.save(output_path)
            
            return output_path
        
        except Exception as e:
            raise RenderError(f"Failed to render page {page_number} to PNG: {e}")
    
    def render_document_to_pngs(
        self,
        output_dir: Union[str, Path],
        file_prefix: str = "page_",
        dpi: int = 300,
        alpha: bool = False,
        zoom: float = 1.0,
        page_range: Optional[Tuple[int, Optional[int]]] = None,
    ) -> List[Path]:
        """Render multiple pages or the entire document to PNG images.
        
        Args:
            output_dir: Directory where to save the PNGs
            file_prefix: Prefix for image filenames
            dpi: Resolution in dots per inch
            alpha: Whether to include an alpha channel
            zoom: Additional zoom factor
            page_range: Optional tuple (start, end) for page range (0-based, end is exclusive)
                        If end is None, renders to the last page
            
        Returns:
            List of paths to the rendered images
            
        Raises:
            RenderError: If rendering fails
        """
        output_dir = Path(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        start_page = 0
        end_page = self.document.page_count
        
        if page_range:
            start_page = page_range[0]
            end_page = page_range[1] if page_range[1] is not None else self.document.page_count
        
        try:
            output_paths = []
            for page_num in range(start_page, end_page):
                output_file = output_dir / f"{file_prefix}{page_num:04d}.png"
                self.render_page_to_png(
                    page_number=page_num,
                    output_path=output_file,
                    dpi=dpi,
                    alpha=alpha,
                    zoom=zoom,
                )
                output_paths.append(output_file)
            
            return output_paths
        
        except Exception as e:
            raise RenderError(f"Failed to render document to PNGs: {e}")