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
        use_ocr_fallback: bool = False,
    ):
        """Initialize the document processor.
        
        Args:
            intelligence_backend: Intelligence backend instance
            ocr_processor: OCR processor function (deprecated - kept for compatibility)
            use_ocr_fallback: Whether to use OCR as fallback (deprecated - kept for compatibility)
        """
        self.intelligence = intelligence_backend
        self.ocr_processor = None  # OCR methods removed
        self.use_ocr_fallback = False  # OCR fallback disabled
        
        # Optional semantic processor for enhanced pipeline
        self.semantic_processor = None
        self.use_semantic_pipeline = False
    
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
            else:
                raise IntelligenceError(
                    f"Backend {self.intelligence.get_name()} doesn't support image input."
                )
        
        except Exception as e:
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
    
    def transcribe_document_pages(
        self,
        image_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        base_filename: str,
        custom_prompt: Optional[str] = None,
        extract_first: bool = True,
    ) -> Dict[str, Any]:
        """Process multiple document pages and create a structured TOC.
        
        Uses enhanced flow when backend supports it:
        1. First extract text using markitdown/OCR
        2. Then enhance with multimodal AI using both text + image
        
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
                
                # Initialize flow flags
                has_enhanced_flow = False
                
                # Check for semantic pipeline
                if self.use_semantic_pipeline and self.semantic_processor:
                    # Use the new semantic pipeline
                    logger.info(f"Using semantic pipeline for page {i+1} - use_semantic_pipeline={self.use_semantic_pipeline}")
                    has_enhanced_flow = True
                    
                    # Build context
                    context = {
                        'page_number': i + 1,
                        'total_pages': len(image_paths),
                        'previous_summaries': []
                    }
                    
                    # Add previous summaries
                    if i > 0:
                        prev_summaries = []
                        for j in range(max(0, i-2), i):
                            prev_page = toc["pages"][j]
                            if "semantic_analysis" in prev_page:
                                summary = prev_page["semantic_analysis"].get("semantic_summary", "")
                                if summary:
                                    prev_summaries.append(summary)
                        context['previous_summaries'] = prev_summaries
                    
                    # Process through semantic pipeline
                    result = self.semantic_processor.process_page(
                        image_path=image_path,
                        page_number=i + 1,
                        context=context,
                        output_dir=output_dir
                    )
                    
                    # Extract enhanced text
                    text = result['extracted_text']
                    if result.get('semantic_enhancement'):
                        enhanced_text = result['semantic_enhancement'].get('enhanced_text')
                        if enhanced_text:
                            text = enhanced_text
                    
                    # Store semantic analysis for page info
                    semantic_info = result
                    
                # Check for enhanced flow capability (using markitdown extraction)
                elif hasattr(self.intelligence, 'process_page_with_context'):
                    # Enhanced flow: Use direct extraction via the intelligence backend
                    logger.debug(f"Using enhanced flow for page {i+1}")
                    has_enhanced_flow = True
                    
                    # Step 1: Use backend's direct extraction if available
                    try:
                        # Try direct transcription first
                        extracted_text = self.intelligence.transcribe_image(str(image_path))
                    except Exception as e:
                        logger.warning(f"Direct extraction failed, continuing with empty text: {e}")
                        extracted_text = ""
                    
                    # Step 2: Build context from previous pages
                    context = {
                        'page_number': i + 1,
                        'total_pages': len(image_paths),
                        'previous_summaries': []
                    }
                    
                    # Add previous page summaries for context
                    if i > 0:
                        prev_summaries = []
                        for j in range(max(0, i-2), i):  # Last 2 pages
                            prev_page = toc["pages"][j]
                            if "semantic_summary" in prev_page:
                                prev_summaries.append(prev_page["semantic_summary"])
                            elif "summary" in prev_page:
                                prev_summaries.append(prev_page["summary"])
                        context['previous_summaries'] = prev_summaries
                    
                    # Step 3: Enhance with multimodal AI
                    enhanced_response = self.intelligence.process_page_with_context(
                        image_path=image_path,
                        extracted_text=extracted_text,
                        context=context
                    )
                    
                    # Parse enhanced response
                    try:
                        import json
                        enhanced_data = json.loads(enhanced_response)
                        text = enhanced_data.get('enhanced_text', extracted_text)
                        semantic_info = {
                            'summary': enhanced_data.get('summary', ''),
                            'key_concepts': enhanced_data.get('key_concepts', []),
                            'relationships': enhanced_data.get('relationships', []),
                            'visual_elements': enhanced_data.get('visual_elements', []),
                            'corrections': enhanced_data.get('corrections', [])
                        }
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse enhanced response, using extracted text")
                        text = extracted_text
                        semantic_info = {}
                else:
                    # Standard flow: Direct transcription
                    text = self.process_image(image_path, custom_prompt=custom_prompt)
                    semantic_info = {}
                
                # Make sure text is a string
                if isinstance(text, list):
                    logger.warning(f"Text for page {page_num + 1} is a list, converting to string")
                    text_str = " ".join(text) if text else ""
                else:
                    text_str = text if text else ""

                # Save text to markdown file
                md_path = output_dir / f"{image_path.stem}.md"
                logger.info(LogMessages.PAGE_MARKDOWN.format(current=i+1, total=len(image_paths)))
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Page {page_num + 1}\n\n{text_str}")
                logger.debug(LogMessages.PAGE_COMPLETE.format(page=page_num+1))

                # Save JSON output if we have semantic data
                if semantic_info:
                    try:
                        import json
                        json_path = output_dir / f"{image_path.stem}.json"
                        logger.info(f"Saving semantic JSON data for page {page_num + 1}")
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(semantic_info, f, indent=2)
                    except Exception as e:
                        logger.warning(f"Failed to save JSON for page {page_num + 1}: {e}")

                
                # Add page info to TOC
                page_info = {
                    "page_number": page_num + 1,
                    "image_file": str(image_path.name),
                    "markdown_file": str(md_path.name),
                    "first_line": text_str.split('\n')[0] if text_str else "",
                    "word_count": len(text_str.split()) if text_str else 0,
                    "enhanced_flow_used": has_enhanced_flow
                }
                
                # Add semantic information if available
                if semantic_info:
                    # Check if using new semantic pipeline format
                    if isinstance(semantic_info, dict) and "semantic_enhancement" in semantic_info:
                        page_info["semantic_pipeline_used"] = True
                        page_info["semantic_analysis"] = semantic_info
                        if semantic_info.get("semantic_enhancement"):
                            enhancement = semantic_info["semantic_enhancement"]
                            page_info["semantic_summary"] = enhancement.get("semantic_summary", "")
                            page_info["key_concepts"] = enhancement.get("key_insights", [])
                    else:
                        # Legacy format
                        page_info["semantic_summary"] = semantic_info.get("summary", "")
                        page_info["key_concepts"] = semantic_info.get("key_concepts", [])
                        page_info["relationships"] = semantic_info.get("relationships", [])
                        page_info["visual_elements"] = semantic_info.get("visual_elements", [])
                        page_info["corrections"] = semantic_info.get("corrections", [])
                
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
                
                # Initialize flow flags
                has_enhanced_flow = False
                
                # Check for semantic pipeline first
                if self.use_semantic_pipeline and self.semantic_processor:
                    # Use the new semantic pipeline
                    logger.debug(f"Using semantic pipeline for page {i+1}")
                    has_enhanced_flow = True
                    
                    # Build context
                    context = {
                        'page_number': i + 1,
                        'total_pages': len(image_paths),
                        'previous_summaries': []
                    }
                    
                    # Add previous summaries
                    if i > 0:
                        prev_summaries = []
                        for j in range(max(0, i-2), i):
                            prev_page = toc["pages"][j]
                            if "semantic_analysis" in prev_page:
                                summary = prev_page["semantic_analysis"].get("semantic_summary", "")
                                if summary:
                                    prev_summaries.append(summary)
                        context['previous_summaries'] = prev_summaries
                    
                    # Process through semantic pipeline
                    result = self.semantic_processor.process_page(
                        image_path=image_path,
                        page_number=i + 1,
                        context=context,
                        output_dir=output_dir
                    )
                    
                    # Extract enhanced text
                    text = result['extracted_text']
                    if result.get('semantic_enhancement'):
                        enhanced_text = result['semantic_enhancement'].get('enhanced_text')
                        if enhanced_text:
                            text = enhanced_text
                    
                    # Store semantic analysis for page info
                    semantic_info = result
                    
                # Check for enhanced flow capability (using direct extraction)
                elif hasattr(self.intelligence, 'process_page_with_context'):
                    # Use same enhanced flow as in transcribe_document_pages
                    logger.debug(f"Using enhanced flow for page {i+1}")
                    has_enhanced_flow = True
                    
                    # Try direct transcription first
                    try:
                        extracted_text = self.intelligence.transcribe_image(str(image_path))
                    except Exception as e:
                        logger.warning(f"Direct extraction failed, continuing with empty text: {e}")
                        extracted_text = ""
                    
                    context = {
                        'page_number': i + 1,
                        'total_pages': len(image_paths),
                        'previous_summaries': []
                    }
                    
                    # Add previous page summaries for context
                    if i > 0:
                        prev_summaries = []
                        for j in range(max(0, i-2), i):
                            prev_page = toc["pages"][j]
                            if "semantic_summary" in prev_page:
                                prev_summaries.append(prev_page["semantic_summary"])
                        context['previous_summaries'] = prev_summaries
                    
                    enhanced_response = self.intelligence.process_page_with_context(
                        image_path=image_path,
                        extracted_text=extracted_text,
                        context=context
                    )
                    
                    try:
                        import json
                        enhanced_data = json.loads(enhanced_response)
                        text = enhanced_data.get('enhanced_text', extracted_text)
                        semantic_info = enhanced_data
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse enhanced response, using extracted text")
                        text = extracted_text
                        semantic_info = {}
                else:
                    # Standard flow
                    text = self.process_image(image_path, custom_prompt=custom_prompt)
                    semantic_info = {}
                
                # Make sure text is a string
                if isinstance(text, list):
                    logger.warning(f"Text for page {page_num + 1} is a list, converting to string")
                    text_str = " ".join(text) if text else ""
                else:
                    text_str = text if text else ""
                
                # Save text to markdown file
                md_path = output_dir / f"{image_path.stem}.md"
                logger.info(LogMessages.PAGE_MARKDOWN.format(current=i+1, total=len(image_paths)))
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Page {page_num + 1}\n\n{text_str}")
                logger.debug(LogMessages.PAGE_COMPLETE.format(page=page_num+1))
                
                # Add page info to TOC
                page_info = {
                    "page_number": page_num + 1,
                    "image_file": str(image_path.name),
                    "markdown_file": str(md_path.name),
                    "first_line": text_str.split('\n')[0] if text_str else "",
                    "word_count": len(text_str.split()) if text_str else 0,
                    "enhanced_flow_used": has_enhanced_flow
                }
                
                # Add semantic information if available
                if semantic_info:
                    # Check if using new semantic pipeline format
                    if isinstance(semantic_info, dict) and "semantic_enhancement" in semantic_info:
                        page_info["semantic_pipeline_used"] = True
                        page_info["semantic_analysis"] = semantic_info
                        if semantic_info.get("semantic_enhancement"):
                            enhancement = semantic_info["semantic_enhancement"]
                            page_info["semantic_summary"] = enhancement.get("semantic_summary", "")
                            page_info["key_concepts"] = enhancement.get("key_insights", [])
                    else:
                        # Legacy format
                        page_info["semantic_summary"] = semantic_info.get("summary", "")
                        page_info["key_concepts"] = semantic_info.get("key_concepts", [])
                        page_info["relationships"] = semantic_info.get("relationships", [])
                        page_info["visual_elements"] = semantic_info.get("visual_elements", [])
                        page_info["corrections"] = semantic_info.get("corrections", [])
                
                toc["pages"].append(page_info)
            
            return toc
        
        except Exception as e:
            raise IntelligenceError(f"Failed to process document: {e}")
    
    # Keep process_document_pages as an alias for backward compatibility
    process_document_pages = transcribe_document_pages


def create_processor(
    config: Dict[str, Any],
    ocr_processor=None,  # Kept for backward compatibility
    backend_name: Optional[str] = None,
) -> DocumentProcessor:
    """Create a document processor with intelligence backend.
    
    Args:
        config: Configuration dictionary
        ocr_processor: Deprecated parameter, kept for compatibility
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
        processor = DocumentProcessor(
            intelligence_backend=backend,
            ocr_processor=None,
            use_ocr_fallback=False,
        )
        
        return processor
    
    except Exception as e:
        raise IntelligenceError(f"Failed to create document processor: {e}")
