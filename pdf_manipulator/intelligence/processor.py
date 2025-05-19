"""Document processor integrating intelligence backends."""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable

from pdf_manipulator.intelligence.base import IntelligenceBackend, IntelligenceManager, IntelligenceError
from pdf_manipulator.utils.logging_config import get_logger, LogMessages

logger = get_logger("intelligence")


class DocumentProcessor:
    """Document processor using intelligence backends."""
    
    def __init__(
        self,
        intelligence_backend: IntelligenceBackend,
        ocr_processor: Optional[Callable] = None,
        use_ocr_fallback: bool = True,
    ):
        """Initialize the document processor.
        
        Args:
            intelligence_backend: Intelligence backend instance
            ocr_processor: OCR processor function (extract_text method)
            use_ocr_fallback: Whether to use OCR as fallback
        """
        self.intelligence = intelligence_backend
        self.ocr_processor = ocr_processor
        self.use_ocr_fallback = use_ocr_fallback
    
    def process_image(
        self,
        image_path: Union[str, Path],
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Process an image using the intelligence backend.
        
        Args:
            image_path: Path to image file
            custom_prompt: Optional custom prompt for processing
            
        Returns:
            Processed text
            
        Raises:
            IntelligenceError: If processing fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise IntelligenceError(f"Image file not found: {image_path}")
        
        try:
            # Check if backend supports direct image input
            if self.intelligence.supports_image_input():
                # Process with intelligence backend
                return self.intelligence.transcribe_image(image_path, prompt=custom_prompt)
            elif self.use_ocr_fallback and self.ocr_processor:
                # Use OCR and then clean with intelligence
                ocr_text = self.ocr_processor(image_path)
                return self.intelligence.transcribe_text(ocr_text)
            else:
                raise IntelligenceError(
                    f"Backend {self.intelligence.get_name()} doesn't support image input "
                    "and no OCR fallback is provided."
                )
        
        except Exception as e:
            # Try OCR fallback if available
            if self.use_ocr_fallback and self.ocr_processor:
                try:
                    return self.ocr_processor(image_path)
                except Exception as ocr_error:
                    raise IntelligenceError(
                        f"Both intelligence processing and OCR fallback failed: {e}. OCR error: {ocr_error}"
                    )
            
            # Re-raise original error
            raise
    
    def process_text(
        self,
        text: str,
        custom_prompt_template: Optional[str] = None,
    ) -> str:
        """Process text using the intelligence backend.
        
        Args:
            text: Text to process
            custom_prompt_template: Optional custom prompt template
            
        Returns:
            Processed text
            
        Raises:
            IntelligenceError: If processing fails
        """
        if not text:
            return ""
        
        return self.intelligence.transcribe_text(text, prompt_template=custom_prompt_template)
    
    def process_document_pages(
        self,
        image_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        base_filename: str,
        custom_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process multiple document pages and create a structured TOC.
        
        Args:
            image_paths: List of paths to page images
            output_dir: Directory for output files
            base_filename: Base name for output files
            custom_prompt: Custom prompt for processing
            
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
                "backend": self.intelligence.get_name(),
                "pages": []
            }
            
            # Add model info if available
            model_info = self.intelligence.get_model_info()
            if model_info:
                toc["model_info"] = model_info
            
            # Process each page
            for i, image_path in enumerate(image_paths):
                image_path = Path(image_path)
                page_num = i
                
                # Process the image
                logger.info(LogMessages.PAGE_TRANSCRIBE.format(current=i+1, total=len(image_paths)))
                text = self.process_image(image_path, custom_prompt=custom_prompt)
                
                # Save text to markdown file
                md_path = output_dir / f"{image_path.stem}.md"
                logger.info(LogMessages.PAGE_MARKDOWN.format(current=i+1, total=len(image_paths)))
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Page {page_num + 1}\n\n{text}")
                logger.debug(LogMessages.PAGE_COMPLETE.format(page=page_num+1))
                
                # Add page info to TOC
                page_info = {
                    "page_number": page_num + 1,
                    "image_file": str(image_path.name),
                    "markdown_file": str(md_path.name),
                    "first_line": text.split('\n')[0] if text else "",
                    "word_count": len(text.split()) if text else 0,
                }
                
                toc["pages"].append(page_info)
            
            return toc
        
        except Exception as e:
            raise IntelligenceError(f"Failed to process document: {e}")
            
    def process_document_pages_with_progress(
        self,
        image_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        base_filename: str,
        progress=None,
        custom_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process multiple document pages with progress tracking.
        
        Args:
            image_paths: List of paths to page images
            output_dir: Directory for output files
            base_filename: Base name for output files
            progress: Progress tracker instance
            custom_prompt: Custom prompt for processing
            
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
                "backend": self.intelligence.get_name(),
                "pages": []
            }
            
            # Add model info if available
            model_info = self.intelligence.get_model_info()
            if model_info:
                toc["model_info"] = model_info
            
            # Process each page
            for i, image_path in enumerate(image_paths):
                image_path = Path(image_path)
                page_num = i
                
                # Update progress
                if progress:
                    progress.update_stage("transcription", advance=1)
                    progress.update_page_status(page_num + 1)
                
                # Process the image
                logger.info(LogMessages.PAGE_TRANSCRIBE.format(current=i+1, total=len(image_paths)))
                text = self.process_image(image_path, custom_prompt=custom_prompt)
                
                # Save text to markdown file
                md_path = output_dir / f"{image_path.stem}.md"
                logger.info(LogMessages.PAGE_MARKDOWN.format(current=i+1, total=len(image_paths)))
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Page {page_num + 1}\n\n{text}")
                logger.debug(LogMessages.PAGE_COMPLETE.format(page=page_num+1))
                
                # Add page info to TOC
                page_info = {
                    "page_number": page_num + 1,
                    "image_file": str(image_path.name),
                    "markdown_file": str(md_path.name),
                    "first_line": text.split('\n')[0] if text else "",
                    "word_count": len(text.split()) if text else 0,
                }
                
                toc["pages"].append(page_info)
            
            return toc
        
        except Exception as e:
            raise IntelligenceError(f"Failed to process document: {e}")


def create_processor(
    config: Dict[str, Any],
    ocr_processor=None,
    backend_name: Optional[str] = None,
) -> DocumentProcessor:
    """Create a document processor with intelligence backend.
    
    Args:
        config: Configuration dictionary
        ocr_processor: OCR processor instance
        backend_name: Optional name of backend to use
        
    Returns:
        DocumentProcessor instance
        
    Raises:
        IntelligenceError: If processor cannot be created
    """
    try:
        # Create intelligence manager
        manager = IntelligenceManager(config)
        
        # Get intelligence backend
        backend = manager.get_backend(backend_name)
        
        # Create document processor
        use_ocr_fallback = config.get("processing", {}).get("use_ocr_fallback", True)
        
        processor = DocumentProcessor(
            intelligence_backend=backend,
            ocr_processor=ocr_processor.extract_text if ocr_processor else None,
            use_ocr_fallback=use_ocr_fallback,
        )
        
        return processor
    
    except Exception as e:
        raise IntelligenceError(f"Failed to create document processor: {e}")