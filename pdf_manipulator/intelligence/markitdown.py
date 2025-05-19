"""Markitdown backend for direct document to markdown conversion."""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from markitdown import MarkItDown

from pdf_manipulator.intelligence.base import IntelligenceBackend, IntelligenceError
from pdf_manipulator.utils.progress import DirectConversionProgress
from pdf_manipulator.utils.logging_config import get_logger, LogMessages, console

logger = get_logger("markitdown")


class MarkitdownBackend(IntelligenceBackend):
    """Direct document to markdown converter using markitdown."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the markitdown backend.
        
        Args:
            config: Optional configuration (not used for markitdown)
        """
        self.config = config or {}
        self.converter = MarkItDown()
    
    def transcribe_image(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
    ) -> str:
        """Convert image to markdown using markitdown.
        
        Args:
            image_path: Path to the image file
            prompt: Not used for markitdown
            
        Returns:
            Converted markdown text
            
        Raises:
            IntelligenceError: If conversion fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise IntelligenceError(f"Image file not found: {image_path}")
        
        try:
            result = self.converter.convert(str(image_path))
            return result.text_content
        except Exception as e:
            raise IntelligenceError(f"Failed to convert image with markitdown: {e}")
    
    def transcribe_text(
        self,
        text: str,
        prompt_template: Optional[str] = None,
    ) -> str:
        """Pass through text as markdown (no processing needed).
        
        Args:
            text: Text to process
            prompt_template: Not used for markitdown
            
        Returns:
            Input text unchanged
        """
        return text
    
    def supports_image_input(self) -> bool:
        """markitdown supports various file types including images.
        
        Returns:
            True
        """
        return True
    
    def get_name(self) -> str:
        """Get the name of the backend.
        
        Returns:
            Backend name
        """
        return "markitdown"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about markitdown.
        
        Returns:
            Dictionary with backend information
        """
        return {
            "backend": "markitdown",
            "description": "Direct document to markdown converter",
            "supported_formats": "PDF, PowerPoint, Word, Excel, Images, HTML, Text, and more",
            "compute_required": "None (CPU only)",
        }
    
    def convert_document(
        self,
        document_path: Union[str, Path],
    ) -> str:
        """Convert any supported document directly to markdown.
        
        Args:
            document_path: Path to the document file
            
        Returns:
            Converted markdown text
            
        Raises:
            IntelligenceError: If conversion fails
        """
        document_path = Path(document_path)
        
        if not document_path.exists():
            raise IntelligenceError(f"Document file not found: {document_path}")
        
        try:
            result = self.converter.convert(str(document_path))
            return result.text_content
        except Exception as e:
            raise IntelligenceError(f"Failed to convert document with markitdown: {e}")
    
    def transcribe_document_pages(
        self,
        image_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        base_filename: str,
        custom_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process multiple document pages and create a structured TOC.
        
        For markitdown, this processes the original document directly
        rather than individual image pages.
        
        Args:
            image_paths: List of paths to page images
            output_dir: Directory for output files
            base_filename: Base name for output files
            custom_prompt: Not used for markitdown
            
        Returns:
            Dictionary with document structure
            
        Raises:
            IntelligenceError: If processing fails
        """
        output_dir = Path(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            toc = {
                "document_name": base_filename,
                "total_pages": len(image_paths),
                "backend": self.get_name(),
                "processing_note": "Direct document conversion using markitdown"
            }
            
            # Add model info
            toc["model_info"] = self.get_model_info()
            
            # If we have image paths, assume we're processing a rendered PDF
            # In that case, convert each image individually
            for i, image_path in enumerate(image_paths):
                image_path = Path(image_path)
                page_num = i
                
                # Process the image
                text = self.transcribe_image(image_path)
                
                # Save text to markdown file
                md_path = output_dir / f"page_{page_num:04d}.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Page {page_num + 1}\n\n{text}")
                
                # Add page info to TOC
                page_info = {
                    "page_number": page_num + 1,
                    "image_file": str(image_path.name),
                    "markdown_file": str(md_path.name),
                    "first_line": text.split('\n')[0] if text else "",
                    "word_count": len(text.split()) if text else 0,
                }
                
                toc.setdefault("pages", []).append(page_info)
            
            return toc
        
        except Exception as e:
            raise IntelligenceError(f"Failed to process document: {e}")
    
    def process_direct_document(
        self,
        document_path: Union[str, Path],
        output_dir: Union[str, Path],
        base_filename: str,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """Process a document directly using markitdown without rendering to images.
        
        Args:
            document_path: Path to the document file
            output_dir: Directory for output files
            base_filename: Base name for output files
            
        Returns:
            Dictionary with document structure
            
        Raises:
            IntelligenceError: If processing fails
        """
        document_path = Path(document_path)
        output_dir = Path(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize progress tracking
        progress = None
        if show_progress:
            progress = DirectConversionProgress(document_path)
            status = progress.show_conversion_start()
        
        try:
            # Update status to show conversion is happening
            if show_progress:
                progress.update_status("Converting document to markdown...")
            
            # Convert the entire document at once
            markdown_content = self.convert_document(document_path)
            
            # Update status to show saving
            if show_progress:
                progress.update_status("Saving markdown output...")
            
            # Save to a single markdown file
            md_path = output_dir / f"{base_filename}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Create content statistics
            content_stats = {
                "total_characters": len(markdown_content),
                "total_words": len(markdown_content.split()),
                "total_lines": len(markdown_content.splitlines())
            }
            
            # Show completion if progress tracking
            if progress:
                progress.show_conversion_complete(content_stats)
            
            # Create TOC structure
            toc = {
                "document_name": base_filename,
                "backend": self.get_name(),
                "processing_note": "Direct document conversion using markitdown",
                "model_info": self.get_model_info(),
                "output_files": {
                    "markdown": str(md_path.name),
                    "full_path": str(md_path)
                },
                "content_stats": content_stats
            }
            
            # Save TOC to JSON
            toc_path = output_dir / f"{base_filename}_contents.json"
            with open(toc_path, 'w', encoding='utf-8') as f:
                json.dump(toc, f, indent=2)
            
            toc["toc_file"] = str(toc_path)
            
            return toc
        
        except Exception as e:
            if progress:
                # Show error in progress
                status.stop()
                console.print(f"[red]Error: {e}[/red]")
            raise IntelligenceError(f"Failed to process document directly: {e}")