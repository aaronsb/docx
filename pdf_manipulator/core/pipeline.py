"""Document processing pipeline."""
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
import json
from datetime import datetime

from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.renderers.image_renderer import ImageRenderer
from pdf_manipulator.core.exceptions import PDFManipulatorError
from pdf_manipulator.memory.memory_processor import MemoryProcessor
from pdf_manipulator.memory.memory_adapter import MemoryConfig
from pdf_manipulator.utils.progress import ProcessingProgress
from pdf_manipulator.utils.logging_config import get_logger, LogMessages

logger = get_logger("pipeline")


class PerformanceTimer:
    """Simple timer for tracking performance metrics."""
    
    def __init__(self):
        """Initialize the performance timer."""
        self.start_time = time.time()
        self.steps = []
        self.step_durations = {}
        self.current_step = None
        self.current_step_start = None
        
    def start_step(self, step_name: str):
        """Start timing a processing step.
        
        Args:
            step_name: Name of the processing step
        """
        # If we're already in a step, end it first
        if self.current_step:
            self.end_step()
            
        self.current_step = step_name
        self.current_step_start = time.time()
        self.steps.append(step_name)
    
    def end_step(self):
        """End timing the current step."""
        if self.current_step and self.current_step_start:
            duration = time.time() - self.current_step_start
            
            # Store the step duration
            if self.current_step in self.step_durations:
                self.step_durations[self.current_step] += duration
            else:
                self.step_durations[self.current_step] = duration
                
            self.current_step = None
            self.current_step_start = None
    
    def get_total_duration(self) -> float:
        """Get the total duration of all processing.
        
        Returns:
            Total duration in seconds
        """
        return time.time() - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        # End any open step
        if self.current_step:
            self.end_step()
            
        total_duration = self.get_total_duration()
        
        return {
            "total_duration_seconds": total_duration,
            "total_duration_formatted": self._format_time(total_duration),
            "steps": self.step_durations,
            "steps_formatted": {step: self._format_time(duration) 
                               for step, duration in self.step_durations.items()},
            "timestamp": datetime.now().isoformat(),
        }
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time in seconds to a human-readable string.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.2f}s"
        else:
            hours = int(seconds // 3600)
            remaining = seconds % 3600
            minutes = int(remaining // 60)
            remaining_seconds = remaining % 60
            return f"{hours}h {minutes}m {remaining_seconds:.2f}s"


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
        ocr_processor=None,  # Kept for backward compatibility but not used
        ai_transcriber=None,
        memory_config: Optional[MemoryConfig] = None,
        intelligence_processor=None,
    ):
        """Initialize the document processor.
        
        Args:
            output_dir: Directory for output files
            renderer_kwargs: Keyword arguments for the image renderer
            ocr_processor: Kept for backward compatibility but not used
            ai_transcriber: AI transcriber instance
            memory_config: Optional memory storage configuration
            intelligence_processor: Optional intelligence processor for memory summaries
        """
        self.output_dir = Path(output_dir)
        self.renderer_kwargs = renderer_kwargs or {}
        self.ocr_processor = None  # Set to None regardless of what was passed
        self.ai_transcriber = ai_transcriber
        self.memory_config = memory_config
        self.intelligence_processor = intelligence_processor
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_pdf(
        self,
        pdf_path: Union[str, Path],
        use_ai: bool = True,
        page_range: Optional[List[int]] = None,
        store_in_memory: bool = False,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """Process a PDF document through the complete pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            use_ai: Whether to use AI transcription
            page_range: Optional list of page numbers to process (0-based)
            store_in_memory: Whether to store results in memory graph database
            
        Returns:
            Dictionary with document structure
            
        Raises:
            PDFManipulatorError: If processing fails
        """
        # Initialize performance timer
        timer = PerformanceTimer()
        timer.start_step("initialization")
        
        # Initialize progress tracking
        progress = None
        if show_progress:
            progress = ProcessingProgress()
            progress.start()
            progress.start_stage("initialization")
        
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
        
        if progress:
            progress.complete_stage("initialization")
            
        timer.end_step()
        
        try:
            # Open PDF file
            timer.start_step("pdf_loading")
            
            if progress:
                progress.start_stage("pdf_loading")
                
            with PDFDocument(pdf_path) as doc:
                # Extract the document's native table of contents
                native_toc = doc.get_toc()
                has_native_toc = len(native_toc) > 0
                
                # Track document stats
                stats = {
                    "total_pages": doc.page_count,
                    "processed_pages": 0,
                }
                
                if progress:
                    progress.log_message(f"Loaded PDF: {doc.page_count} pages")
                    progress.complete_stage("pdf_loading")
                    
                timer.end_step()
                
                # Initialize renderer
                timer.start_step("rendering")
                renderer = ImageRenderer(doc)
                
                # Determine pages to process
                if page_range is not None:
                    pages_to_process = page_range
                else:
                    pages_to_process = list(range(doc.page_count))
                
                stats["processed_pages"] = len(pages_to_process)
                
                if progress:
                    progress.start_stage("rendering", total=len(pages_to_process))
                
                # Render pages to images
                image_paths = []
                for i, page_num in enumerate(pages_to_process):
                    output_file = images_dir / f"page_{page_num:04d}.png"
                    renderer.render_page_to_png(
                        page_number=page_num,
                        output_path=output_file,
                        **self.renderer_kwargs
                    )
                    image_paths.append(output_file)
                    
                    if progress:
                        progress.update_stage("rendering", advance=1)
                        progress.update_page_status(page_num + 1)
                        
                if progress:
                    progress.complete_stage("rendering")
                    
                timer.end_step()
                
                # Process images with OCR or AI
                timer.start_step("transcription")
                
                if progress:
                    progress.start_stage("transcription", total=len(image_paths))
                    
                if use_ai and self.ai_transcriber:
                    # Process with AI transcription
                    if hasattr(self.ai_transcriber, 'transcribe_document_pages_with_progress'):
                        toc = self.ai_transcriber.transcribe_document_pages_with_progress(
                            image_paths=image_paths,
                            output_dir=markdown_dir,
                            base_filename=base_filename,
                            progress=progress,
                        )
                    else:
                        toc = self.ai_transcriber.transcribe_document_pages(
                            image_paths=image_paths,
                            output_dir=markdown_dir,
                            base_filename=base_filename,
                        )
                    stats["transcription_method"] = "ai"
                
                else:
                    raise PDFManipulatorError("No AI processor available for transcription")
                    
                if progress:
                    progress.complete_stage("transcription")
                    
                timer.end_step()
                
                # Store in memory graph if enabled
                if store_in_memory and self.memory_config:
                    timer.start_step("memory_storage")
                    
                    # Build page content dictionary from markdown files
                    page_content = {}
                    for i, page_num in enumerate(pages_to_process):
                        md_file = markdown_dir / f"page_{i:04d}.md"
                        if md_file.exists():
                            with open(md_file, 'r', encoding='utf-8') as f:
                                page_content[page_num] = f.read()
                    
                    # Create memory processor and store content
                    memory_db_path = doc_dir / "memory_graph.db"
                    memory_config = MemoryConfig(
                        database_path=memory_db_path,
                        domain_name=self.memory_config.domain_name,
                        domain_description=self.memory_config.domain_description,
                        enable_relationships=self.memory_config.enable_relationships,
                        enable_summaries=self.memory_config.enable_summaries,
                        tags_prefix=self.memory_config.tags_prefix,
                        min_content_length=self.memory_config.min_content_length,
                    )
                    
                    with MemoryProcessor(
                        memory_config, 
                        self.intelligence_processor, 
                        use_toc_first=True
                    ) as mem_processor:
                        # Extract semantic analysis from TOC
                        semantic_analysis = {}
                        if "pages" in toc:
                            for page in toc["pages"]:
                                page_num = page.get("page_number", 0) - 1  # Convert to 0-based
                                if "semantic_analysis" in page:
                                    semantic_analysis[page_num] = page["semantic_analysis"]
                        
                        memory_results = mem_processor.process_document(
                            pdf_document=doc,
                            page_content=page_content,
                            document_metadata={
                                'filename': str(pdf_path),
                                'base_filename': base_filename,
                                'transcription_method': stats.get('transcription_method', 'unknown'),
                            },
                            semantic_analysis=semantic_analysis if semantic_analysis else None
                        )
                        
                        # Add memory results to TOC
                        toc["memory_storage"] = {
                            "enabled": True,
                            "database_path": str(memory_db_path),
                            "document_id": memory_results.get("document_id"),
                            "page_memories": memory_results.get("page_memories", {}),
                            "section_memories": memory_results.get("section_memories", {}),
                        }
                        stats["memory_storage"] = "completed"
                    
                    timer.end_step()
                else:
                    toc["memory_storage"] = {"enabled": False}
                    stats["memory_storage"] = "disabled"
                
                # Add native document TOC to the output if available
                timer.start_step("finalization")
                
                if progress:
                    progress.start_stage("finalization")
                    
                if has_native_toc:
                    toc["native_toc"] = native_toc
                    toc["has_native_toc"] = True
                else:
                    toc["has_native_toc"] = False
                
                # Add document metadata
                toc["metadata"] = doc.metadata
                
                # Add performance metrics to output
                performance = timer.get_summary()
                toc["performance"] = performance
                toc["stats"] = stats
                
                # Calculate average time per page
                if stats["processed_pages"] > 0:
                    render_time = performance["steps"].get("rendering", 0)
                    transcription_time = performance["steps"].get("transcription", 0)
                    
                    toc["performance"]["avg_render_time_per_page"] = render_time / stats["processed_pages"]
                    toc["performance"]["avg_transcription_time_per_page"] = transcription_time / stats["processed_pages"]
                    
                    toc["performance"]["avg_render_time_per_page_formatted"] = timer._format_time(
                        render_time / stats["processed_pages"]
                    )
                    toc["performance"]["avg_transcription_time_per_page_formatted"] = timer._format_time(
                        transcription_time / stats["processed_pages"]
                    )
                
                # Save TOC to JSON file
                toc_path = doc_dir / f"{base_filename}_contents.json"
                with open(toc_path, 'w', encoding='utf-8') as f:
                    json.dump(toc, f, indent=2)
                    
                if progress:
                    progress.complete_stage("finalization")
                    progress.stop()
                    
                timer.end_step()
                
                return toc
        
        except Exception as e:
            # Record the error in performance metrics
            timer.start_step("error_handling")
            performance = timer.get_summary()
            timer.end_step()
            
            # Stop progress tracking on error
            if progress:
                progress.log_message(f"[red]Error: {e}[/red]")
                progress.stop()
            
            # Can still try to save performance data even if processing failed
            try:
                error_stats = {
                    "performance": performance,
                    "error": str(e),
                    "status": "failed"
                }
                
                # Try to save error stats
                error_path = doc_dir / f"{base_filename}_error_stats.json"
                with open(error_path, 'w', encoding='utf-8') as f:
                    json.dump(error_stats, f, indent=2)
            except:
                pass  # Ignore errors in error handling
    
    def rebuild_memory_from_extracted_data(
        self,
        contents_file: Union[str, Path],
        domain: str = 'pdf_processing'
    ) -> Path:
        """Rebuild memory database from previously extracted data.
        
        This method reads the contents.json file and associated markdown files
        to reconstruct the memory database without reprocessing the PDF.
        
        Args:
            contents_file: Path to the {document}_contents.json file
            domain: Memory domain name for the database
            
        Returns:
            Path to the recreated memory database
            
        Raises:
            PDFManipulatorError: If reconstruction fails
        """
        contents_file = Path(contents_file)
        
        # Load the contents file
        logger.info(f"Loading extracted data from {contents_file}")
        with open(contents_file, 'r', encoding='utf-8') as f:
            contents = json.load(f)
        
        # Extract document info
        doc_name = contents.get('document_name', contents_file.stem.replace('_contents', ''))
        doc_dir = contents_file.parent.parent
        markdown_dir = contents_file.parent
        
        # Set up memory configuration
        memory_path = doc_dir / "memory_graph.db"
        
        # Delete existing database if it exists
        if memory_path.exists():
            logger.info(f"Removing existing database at {memory_path}")
            os.remove(memory_path)
        
        self.memory_config = MemoryConfig(
            database_path=memory_path,
            domain_name=domain,
            domain_description=f"Semantic graph for {doc_name}",
            enable_relationships=True,
            enable_summaries=True
        )
        
        # Initialize memory processor
        mem_processor = MemoryProcessor(
            memory_adapter=self.memory_config,
            intelligence_processor=self.intelligence_processor
        )
        
        # Reconstruct page content from markdown files
        page_content = {}
        pages_data = contents.get('pages', [])
        
        logger.info(f"Reconstructing content for {len(pages_data)} pages")
        
        for page_info in pages_data:
            page_num = page_info.get('page_number', 0) - 1  # Convert to 0-based
            
            # Read markdown content
            markdown_file = markdown_dir / page_info.get('markdown_file', f"page_{page_num:04d}.md")
            if markdown_file.exists():
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remove the "# Page N" header if present
                    lines = content.split('\n')
                    if lines and lines[0].startswith('# Page '):
                        content = '\n'.join(lines[2:])  # Skip header and empty line
                    page_content[page_num] = content
            else:
                logger.warning(f"Markdown file not found: {markdown_file}")
                page_content[page_num] = ""
        
        # Extract semantic analysis data
        semantic_analysis = {}
        for page_info in pages_data:
            page_num = page_info.get('page_number', 0) - 1
            if 'semantic_analysis' in page_info:
                semantic_analysis[page_num] = page_info['semantic_analysis']
        
        # Prepare document metadata
        document_metadata = {
            'filename': doc_name + '.pdf',
            'path': str(doc_dir.parent / (doc_name + '.pdf')),
            'page_count': len(pages_data),
            'has_toc': contents.get('has_toc', False),
            'extracted_at': contents.get('extraction_date', datetime.now().isoformat()),
            'backend_used': contents.get('backend', {}).get('type', 'unknown'),
            'model_used': contents.get('backend', {}).get('model', 'unknown')
        }
        
        # Create a minimal PDFDocument-like object for the memory processor
        # Since we're rebuilding from extracted data, we don't need the actual PDF
        class MockPDFDoc:
            def __init__(self, page_count):
                self.page_count = page_count
                
        mock_doc = MockPDFDoc(len(pages_data))
        
        # Process with memory
        logger.info("Rebuilding memory graph from extracted data")
        memory_results = mem_processor.process_document(
            pdf_document=mock_doc,
            page_content=page_content,
            document_metadata=document_metadata,
            semantic_analysis=semantic_analysis if semantic_analysis else None
        )
        
        # Log results
        if memory_results:
            logger.info(f"Memory graph rebuilt successfully at {memory_path}")
            logger.info(f"Created {memory_results.get('nodes_created', 0)} nodes")
            logger.info(f"Created {memory_results.get('relationships_created', 0)} relationships")
        
        return memory_path