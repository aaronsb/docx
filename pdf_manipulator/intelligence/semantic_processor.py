"""Enhanced semantic processor for multi-step analysis flow."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import base64
import re

# Import the configured logger
from ..utils.logging_config import get_logger

# Module logger
logger = get_logger('semantic_processor')

# Text summarization for long texts
try:
    from summa import summarizer
    SUMMARIZER_AVAILABLE = True
except ImportError:
    SUMMARIZER_AVAILABLE = False
    logger.warning("Summa library not found, text summarization disabled")

from .base import IntelligenceBackend
from .markitdown import MarkitdownBackend
from ..core.exceptions import ProcessingError


class SemanticProcessor:
    """Implements the layered semantic processing flow.
    
    Phase 1: Extract text using markitdown (no LLM)
    Phase 2: Feed text + image to multimodal LLM with guided multi-step prompting
    """
    
    def __init__(self, 
                 extraction_backend: IntelligenceBackend,
                 enhancement_backend: Optional[IntelligenceBackend] = None,
                 logger: Optional[logging.Logger] = None,
                 summarization_ratio: float = 0.2,
                 max_tokens: int = 75,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize semantic processor.
        
        Args:
            extraction_backend: Backend for text extraction (e.g., markitdown)
            enhancement_backend: Backend for semantic enhancement (e.g., ollama_multimodal)
            logger: Logger instance
            summarization_ratio: Target ratio for text summarization (0.0 to 1.0)
                                 Lower values = more aggressive summarization
                                 0.0 = maximum summarization (just title/first sentences)
                                 1.0 = no summarization (use full text)
            max_tokens: Maximum number of tokens to keep even with summarization
            config: Configuration dictionary for templates and other settings
        """
        self.extraction_backend = extraction_backend
        self.enhancement_backend = enhancement_backend
        self.logger = logger or logging.getLogger(__name__)
        self.config = config or {}
        
        # Validate and store summarization parameters
        self.summarization_ratio = max(0.0, min(1.0, summarization_ratio))  # Clamp to 0.0-1.0
        self.max_tokens = max(30, max_tokens)  # Ensure reasonable minimum
        
        # Get the prompt templates from config if available
        self.prompt_templates = self.config.get("semantic_enhancement", {}).get("prompts", {})
        
        # Track summarization info for logging and debugging
        self.last_summarization_info = {
            "was_summarized": False,
            "original_word_count": 0,
            "summarized_word_count": 0,
            "target_ratio": self.summarization_ratio,
            "max_tokens": self.max_tokens
        }
        
    def process_page(self,
                     image_path: Union[str, Path],
                     page_number: int,
                     context: Optional[Dict[str, Any]] = None,
                     output_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Process a single page through the full semantic pipeline.
        
        Args:
            image_path: Path to page image
            page_number: Page number (1-based)
            context: Optional context (TOC, previous pages, etc.)
            output_dir: Optional directory to save intermediate files
            
        Returns:
            Comprehensive page analysis
        """
        image_path = Path(image_path)
        
        # Phase 1: Extract text using markitdown
        self.logger.info(f"Phase 1: Extracting text from page {page_number}")
        extracted_text = self._extract_text(image_path)
        
        # Save extracted text if output directory provided
        if output_dir:
            output_dir = Path(output_dir)
            # Use 0-based page index for filename to match image files
            page_index = page_number - 1
            extraction_file = output_dir / f"page_{page_index:04d}_extracted.md"
            self.logger.info(f"Saving extracted text to {extraction_file}")
            with open(extraction_file, 'w', encoding='utf-8') as f:
                f.write(f"# Page {page_number} - Extracted Text (Phase 1)\n\n")
                f.write(extracted_text if extracted_text else "[No text extracted by markitdown]")
        
        # Initialize result
        result = {
            'page_number': page_number,
            'extracted_text': extracted_text,
            'extraction_method': self.extraction_backend.get_name(),
            'semantic_enhancement': None,
            'original_text_length': len(extracted_text) if extracted_text else 0,
            'word_count': len(re.findall(r'\b\w+\b', extracted_text)) if extracted_text else 0
        }
        
        # Phase 2: Semantic enhancement with multimodal LLM - SINGLE UNIFIED CALL
        if self.enhancement_backend and hasattr(self.enhancement_backend, 'process_page_with_context'):
            self.logger.info(f"Phase 2: Semantic enhancement for page {page_number} (single call approach)")
            
            # Create a single comprehensive prompt that combines all steps
            # This makes a single call to Ollama instead of multiple calls
            unified_prompt = self._create_unified_prompt(extracted_text, context or {})
            
            # Make a single call to the enhancement backend
            self.logger.debug(f"Making unified call to {self.enhancement_backend.get_name()} for page {page_number}")
            unified_response = self.enhancement_backend.process_page_with_context(
                image_path=image_path,
                extracted_text=unified_prompt,  # We use the prompt as the "extracted_text" parameter
                context={}  # No need for additional context since it's in the prompt
            )
            
            # Parse the response
            try:
                import json
                # Look for JSON in the response - often LLaVA will wrap it in ```json ... ```
                json_text = unified_response
                if "```json" in json_text:
                    json_parts = json_text.split("```json")
                    if len(json_parts) > 1:
                        json_text = json_parts[1].split("```")[0]
                elif "```" in json_text:
                    # Try to extract any code block that might contain JSON
                    json_parts = json_text.split("```")
                    if len(json_parts) > 1:
                        for part in json_parts:
                            if part.strip().startswith("{") and part.strip().endswith("}"):
                                json_text = part
                                break
                
                self.logger.debug(f"Attempting to parse JSON response of length {len(json_text)}")
                semantic_data = json.loads(json_text)
                self.logger.info(f"Successfully parsed JSON response with keys: {list(semantic_data.keys())}")
                result['semantic_enhancement'] = semantic_data
                result['enhancement_method'] = self.enhancement_backend.get_name()
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse unified response as JSON: {e}")
                # Store a fragment of the response for debugging
                response_preview = unified_response[:500] + "..." if len(unified_response) > 500 else unified_response
                self.logger.debug(f"Response preview: {response_preview}")
                result['semantic_enhancement'] = {"raw_response": unified_response}
            
            # Ensure semantic_enhancement exists and save the prompt
            result['semantic_enhancement'] = result.get('semantic_enhancement', {})
            result['semantic_enhancement']['prompt'] = unified_prompt
            
            # Add summarization info
            result['summarization_info'] = self.last_summarization_info
            if self.last_summarization_info["was_summarized"]:
                self.logger.info(f"Text was summarized from {self.last_summarization_info['original_word_count']} to {self.last_summarization_info['summarized_word_count']} words")
            
            # Save semantic enhancement if output directory provided
            if output_dir:
                try:
                    semantic_file = output_dir / f"page_{page_index:04d}_semantic.json"
                    self.logger.info(f"Saving semantic enhancement to {semantic_file}")
                    with open(semantic_file, 'w', encoding='utf-8') as f:
                        json.dump(result['semantic_enhancement'], f, indent=2)
                except Exception as e:
                    self.logger.warning(f"Failed to save semantic enhancement: {e}")
        
        return result
    
    def _extract_text(self, image_path: Path) -> str:
        """Get extracted text for a specific page.
        
        Note: This doesn't actually extract from the image, but reads the 
        pre-extracted markdown file created by our script.
        """
        try:
            # Get page number from image filename
            page_number = int(image_path.stem.split('_')[-1])  # Extract page number from filename
            
            # Look for pre-extracted markdown file
            markdown_dir = image_path.parent.parent / "markdown"
            extracted_file = markdown_dir / f"page_{page_number:04d}_extracted.md"
            
            # If the extracted file exists, read its content
            if extracted_file.exists():
                self.logger.debug(f"Using pre-extracted markdown for page {page_number}")
                with open(extracted_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Skip the header (first 2 lines)
                content_lines = content.split('\n')
                if len(content_lines) > 2:
                    content = '\n'.join(content_lines[2:])
            else:
                # If no pre-extracted file, return empty string
                self.logger.warning(f"No pre-extracted markdown found for page {page_number}")
                content = ""
                
            self.logger.debug(f"Extracted text length: {len(content)} characters")
            return content
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            raise ProcessingError(f"Failed to extract text: {e}")
            
    def _smart_summarize(self, text: str, max_tokens: Optional[int] = None) -> Tuple[str, bool]:
        """Intelligently summarize text if it's too long.
        
        Args:
            text: Original text to summarize
            max_tokens: Target maximum number of tokens (words), 
                        overrides self.max_tokens if provided
            
        Returns:
            Tuple of (summarized text, was_summarized flag)
        """
        # Use instance max_tokens if not provided
        max_tokens = max_tokens or self.max_tokens
        # Count words as a rough approximation of tokens
        words = len(re.findall(r'\b\w+\b', text))
        
        # If text is already short enough, return as is
        if words <= max_tokens:
            return text, False
            
        # Extract title and first 1-2 sentences as a fallback - this is especially
        # effective for academic papers that put key info in the title and abstract
        first_sentences = []
        
        # Extract title - assumed to be the first line
        title = text.split('\n')[0] if text else ""
        if title and not title.endswith('.'):
            title = title.strip() + "."
        first_sentences.append(title)
        
        # Add the first 1-2 sentences from the text if needed
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            # Add first sentence after title 
            first_sentences.append(sentences[1])
            
            # If we still need more content, add the next sentence
            if len(" ".join(first_sentences).split()) < max_tokens and len(sentences) > 2:
                first_sentences.append(sentences[2])
        
        # Create fallback summary
        fallback_summary = " ".join(first_sentences)
        
        # If summa is available, use it for summarization
        if SUMMARIZER_AVAILABLE:
            self.logger.info(f"Text is {words} words, summarizing to ~{max_tokens} words")
            
            # Calculate target ratio based on configured summarization_ratio
            # If ratio is 1.0, no summarization is done
            if self.summarization_ratio >= 1.0:
                ratio = 1.0  # No summarization
                self.logger.info(f"Summarization disabled (ratio=1.0), using full text")
                return text, False
            
            # If ratio is 0.0, use minimal summary (title + first sentences)
            if self.summarization_ratio <= 0.0:
                self.logger.info(f"Using maximum summarization (ratio=0.0)")
                # The fallback summary (title + first sentences) will be used
                return fallback_summary, True
            
            # Calculate word-based target ratio (not to exceed max_tokens)
            target_ratio = min(1.0, max_tokens / max(1, words))
            
            # Scale based on configured summarization_ratio (0.0-1.0)
            # Lower ratio = more aggressive summarization
            base_ratio = self.summarization_ratio
            
            # Apply dynamic scaling based on text length and configured ratio
            if words > 10000:
                # For very long texts, scale down more
                ratio = min(target_ratio, base_ratio * 0.1)  
            elif words > 5000:
                ratio = min(target_ratio, base_ratio * 0.2)
            elif words > 1000:
                ratio = min(target_ratio, base_ratio * 0.4)
            elif words > 500:
                ratio = min(target_ratio, base_ratio * 0.7)
            else:
                ratio = min(target_ratio, base_ratio)
                
            # Apply summarization
            try:
                summary = summarizer.summarize(text, ratio=ratio)
                
                # If summary is empty or too short, try with a slightly higher ratio
                if not summary or len(summary.split()) < min(30, max_tokens // 2):
                    self.logger.warning(f"Summary too short, using higher ratio")
                    summary = summarizer.summarize(text, ratio=min(1.0, ratio * 3))
                    
                # If still too short, use the fallback summary
                if not summary or len(summary.split()) < 20:
                    self.logger.warning(f"Summarization failed, using title and first sentences")
                    return fallback_summary, True
                    
                # If summary is still too long, truncate it
                summary_words = len(summary.split())
                if summary_words > max_tokens:
                    summary_words_list = summary.split()
                    summary = " ".join(summary_words_list[:max_tokens])
                    summary_words = len(summary.split())
                
                self.logger.info(f"Summarized from {words} to {summary_words} words ({ratio:.3f} ratio)")
                return summary, True
                
            except Exception as e:
                self.logger.error(f"Summarization error: {e}")
                # Fall back to title and first sentences
                return fallback_summary, True
        else:
            # If summa is not available, use title and first sentences
            self.logger.warning(f"Text is {words} words but summarizer not available, using title and first sentences")
            return fallback_summary, True

    def _create_unified_prompt(self, extracted_text: str, context: Dict[str, Any]) -> str:
        """Create a unified prompt for all semantic processing steps.
        
        This creates a single comprehensive prompt for the Ollama LLaVA model.
        """
        # Intelligently summarize long text to reduce computational load on LLaVA
        # Uses the instance's configured summarization_ratio and max_tokens
        summarized_text, was_summarized = self._smart_summarize(extracted_text)
        
        # Keep track of summarization metrics for logging
        self.last_summarization_info = {
            "was_summarized": was_summarized,
            "original_word_count": len(re.findall(r'\b\w+\b', extracted_text)) if extracted_text else 0,
            "summarized_word_count": len(re.findall(r'\b\w+\b', summarized_text)) if summarized_text else 0
        }
        
        # Prepare previous page context (if available)
        previous_context = ""
        if "previous_summaries" in context and context["previous_summaries"]:
            previous_context = "## Context from Previous Pages\n\n"
            for i, summary in enumerate(context["previous_summaries"]):
                page_num = context.get('page_number', 0) - len(context['previous_summaries']) + i
                previous_context += f"Page {page_num}: {summary}\n\n"
        
        # Add TOC context if available
        toc_context = ""
        if "toc_structure" in context:
            toc_context = f"""## Document Structure
{context['toc_structure']}

"""
        
        # Add current section context if available
        section_context = ""
        if "current_section" in context:
            section_context = f"## Current Section: {context['current_section']}\n\n"
        
        # Get the template from config if available, otherwise use the default
        template = self.prompt_templates.get("unified_prompt", """# Semantic Analysis Task

{toc_context}{section_context}## Page Number
Page {page_number} of {total_pages}

## Extracted Text
The following {summarized_indicator}text was extracted from this document page:

{extracted_text}

{previous_context}

## Visual Analysis Task
I'll now provide the image of the page. Please analyze both the extracted text AND the image together to:

1. Identify the main topic and purpose of this page
2. Extract key concepts and relationships between them
3. Identify ontological categories and tags
4. Determine the content type and domain
5. Provide a comprehensive semantic summary
6. Note any visual elements (diagrams, tables, equations, etc.)
7. Correct any errors in the extracted text based on the image

## Response Format
Provide your analysis in a structured JSON format. IMPORTANT: Your entire response should be valid JSON:

{{
    "main_topic": "Brief description of the main topic",
    "purpose": "The purpose of the content on this page",
    "semantic_summary": "Comprehensive summary of the page content",
    "key_insights": [
        "key insight 1",
        "key insight 2",
        "key insight 3"
    ],
    "relationships": [
        {{
            "concept1": "term1", 
            "concept2": "term2", 
            "relationship": "type of relationship"
        }}
    ],
    "content_type": "research_paper|diagram|code|etc",
    "domain_tags": ["tag1", "tag2", "tag3"],
    "knowledge_domain": "field or domain of knowledge",
    "complexity_level": "beginner|intermediate|advanced|expert",
    "ontology_tags": ["hierarchical", "classification", "tags"],
    "visual_elements": [
        {{
            "type": "figure|table|diagram|equation", 
            "description": "what it shows"
        }}
    ],
    "enhanced_text": "Improved version of the text with corrections",
    "confidence_score": 0.95
}}

Carefully analyze the image now and provide your analysis ONLY in the specified JSON format. Do not include any text outside the JSON structure.""")
        
        # Format the template with the dynamic values
        prompt = template.format(
            toc_context=toc_context,
            section_context=section_context,
            page_number=context.get('page_number', 0),
            total_pages=context.get('total_pages', 'unknown'),
            summarized_indicator='summarized ' if was_summarized else '',
            extracted_text=summarized_text,
            previous_context=previous_context
        )
        
        return prompt
        
    def _pre_extract_all_pages(self, full_markdown: str, pdf_path: str, output_dir: Path):
        """Pre-extract all pages from the full markdown and save to files."""
        from pathlib import Path
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine total pages from PDF
        total_pages = 50  # Default assumption
        try:
            # Try to get actual page count from PDF
            import pypdf
            with pypdf.PdfReader(pdf_path) as pdf:
                total_pages = len(pdf.pages)
        except Exception as e:
            self.logger.warning(f"Could not determine exact page count: {e}")
        
        self.logger.info(f"Pre-extracting markdown for all {total_pages} pages")
        
        # Split content into pages (simple approach)
        lines = full_markdown.split('\n')
        lines_per_page = max(1, len(lines) // total_pages)
        
        # Create extracted files for each page
        for page_num in range(total_pages):
            start_idx = page_num * lines_per_page
            end_idx = min(len(lines), (page_num + 1) * lines_per_page)
            
            # Extract content for this page
            page_content = '\n'.join(lines[start_idx:end_idx])
            
            # Save to extracted markdown file
            extraction_file = output_dir / f"page_{page_num:04d}_extracted.md"
            with open(extraction_file, 'w', encoding='utf-8') as f:
                f.write(f"# Page {page_num + 1} - Extracted Text (Phase 1)\n\n")
                f.write(page_content if page_content.strip() else "[No text extracted by markitdown]")
                
            self.logger.debug(f"Pre-extracted content for page {page_num}")
    
    def _extract_page_from_markdown(self, full_markdown: str, page_number: int) -> str:
        """Extract content for a specific page from the full markdown."""
        # This is a simplified approach - in a real implementation, we'd need to
        # properly parse the markdown structure to identify page boundaries
        lines = full_markdown.split('\n')
        
        # For now, just split by page headers or return a section
        # You might need to customize this based on how markitdown formats the output
        page_marker = f"Page {page_number + 1}"
        
        # Find page start
        start_idx = -1
        for i, line in enumerate(lines):
            if page_marker in line:
                start_idx = i
                break
        
        if start_idx == -1:
            # If no page marker found, divide content by total pages
            total_lines = len(lines)
            lines_per_page = total_lines // 50  # Assuming ~50 pages
            start_idx = page_number * lines_per_page
            end_idx = (page_number + 1) * lines_per_page
            return '\n'.join(lines[start_idx:end_idx])
        
        # Find next page marker
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            if f"Page {page_number + 2}" in lines[i]:
                end_idx = i
                break
        
        return '\n'.join(lines[start_idx:end_idx])
    
    # The method below calls the enhancement backend to process an image and extract information
    def _call_enhancement_backend(self, image_path: Path, prompt: str) -> str:
        """Call the enhancement backend with image and prompt."""
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode()
        
        # Use the backend's process method
        return self.enhancement_backend.process(prompt, image_b64, json_mode=True)
    
    def _parse_json_response(self, response: str, step_name: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning(f"Failed to parse JSON in {step_name}, returning raw response")
            return {"raw_response": response, "parse_error": True}