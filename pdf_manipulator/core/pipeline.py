"""Document processing pipeline."""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
import json

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer
from pdf_manipulator.core.exceptions import PDFManipulatorError


class DocumentPipeline:
    """Pipeline for processing PDF documents with various processors."""
    
    def __init__(self):
        """Initialize the document pipeline."""
        self.processors = []
    
    def add_processor(self, processor: Callable, name: Optional[str] = None) -> 'DocumentPipeline':
        """Add a processor to the pipeline.
        
        Args:
            processor: Function to process document data
            name: Optional name for the processor
            
        Returns:
            Self for chaining
        """
        processor_name = name or getattr(processor, '__name__', f"processor_{len(self.processors)}")
        self.processors.append((processor_name, processor))
        return self
    
    def process(self, input_data: Any) -> Any:
        """Run the processing pipeline on input data.
        
        Args:
            input_data: Input data for the pipeline
            
        Returns:
            Processed data
            
        Raises:
            PDFManipulatorError: If processing fails
        """
        current_data = input_data
        
        for name, processor in self.processors:
            try:
                current_data = processor(current_data)
            except Exception as e:
                raise PDFManipulatorError(f"Error in processor '{name}': {e}")
        
        return current_data


class DocumentProcessor:
    """High-level document processor combining multiple components."""
    
    def __init__(
        self,
        output_dir: Union[str, Path],
        renderer_kwargs: Optional[Dict[str, Any]] = None,
        ocr_processor=None,
        ai_transcriber=None,
    ):
        """Initialize the document processor.
        
        Args:
            output_dir: Directory for output files
            renderer_kwargs: Keyword arguments for the image renderer
            ocr_processor: OCR processor instance
            ai_transcriber: AI transcriber instance
        """
        self.output_dir = Path(output_dir)
        self.renderer_kwargs = renderer_kwargs or {}
        self.ocr_processor = ocr_processor
        self.ai_transcriber = ai_transcriber
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_pdf(
        self,
        pdf_path: Union[str, Path],
        use_ai: bool = True,
        page_range: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Process a PDF document through the complete pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            use_ai: Whether to use AI transcription
            page_range: Optional list of page numbers to process (0-based)
            
        Returns:
            Dictionary with document structure
            
        Raises:
            PDFManipulatorError: If processing fails
        """
        pdf_path = Path(pdf_path)
        base_filename = pdf_path.stem
        
        # Create subdirectory for this document
        doc_dir = self.output_dir / base_filename
        os.makedirs(doc_dir, exist_ok=True)
        
        # Create subdirectories
        images_dir = doc_dir / "images"
        markdown_dir = doc_dir / "markdown"
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(markdown_dir, exist_ok=True)
        
        try:
            # Open PDF and render pages to images
            with PDFDocument(pdf_path) as doc:
                renderer = ImageRenderer(doc)
                
                # Determine pages to process
                if page_range is not None:
                    pages_to_process = page_range
                else:
                    pages_to_process = list(range(doc.page_count))
                
                # Render pages to images
                image_paths = []
                for page_num in pages_to_process:
                    output_file = images_dir / f"page_{page_num:04d}.png"
                    renderer.render_page_to_png(
                        page_number=page_num,
                        output_path=output_file,
                        **self.renderer_kwargs
                    )
                    image_paths.append(output_file)
                
                # Process images with OCR or AI
                if use_ai and self.ai_transcriber:
                    # Get OCR function for fallback
                    ocr_func = None
                    if self.ocr_processor:
                        ocr_func = self.ocr_processor.extract_text
                    
                    # Process with AI transcription
                    toc = self.ai_transcriber.transcribe_document_pages(
                        image_paths=image_paths,
                        output_dir=markdown_dir,
                        base_filename=base_filename,
                    )
                
                elif self.ocr_processor:
                    # Process with OCR only
                    toc = self.ocr_processor.analyze_document_pages(
                        image_paths=image_paths,
                        output_dir=markdown_dir,
                        base_filename=base_filename,
                    )
                
                else:
                    raise PDFManipulatorError("No OCR or AI processor available")
                
                # Save TOC to JSON file
                toc_path = doc_dir / f"{base_filename}_contents.json"
                with open(toc_path, 'w', encoding='utf-8') as f:
                    json.dump(toc, f, indent=2)
                
                return toc
        
        except Exception as e:
            raise PDFManipulatorError(f"Failed to process document: {e}")