"""OpenAI multimodal backend with GPT-4V support."""
import os
import base64
import json
import time
from typing import Dict, List, Optional, Any, Union
import logging
from pathlib import Path
import traceback
import inspect

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

# Import error types - handle different versions of the OpenAI SDK
try:
    # Newer SDK version
    from openai.types import APIError, APIConnectionError, APITimeoutError, RateLimitError
except ImportError:
    try:
        # Alternative import paths for different SDK versions
        from openai import APIError, APIConnectionError, APITimeoutError, RateLimitError
    except ImportError:
        # Fallback if specific error types are not available
        APIError = Exception
        APIConnectionError = Exception
        APITimeoutError = Exception
        RateLimitError = Exception

from .base import IntelligenceBackend
from ..core.exceptions import ProcessingError


class OpenAIMultimodalBackend(IntelligenceBackend):
    """OpenAI API backend with vision support for semantic extraction."""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-4o-mini",
                 max_tokens: int = 4096,
                 temperature: float = 0.1,
                 timeout: int = 60,
                 logger: Optional[logging.Logger] = None):
        """Initialize OpenAI multimodal backend.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (must support vision)
            max_tokens: Maximum tokens in response
            temperature: Model temperature (0-1)
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("OpenAI API key not found - check your .env file or environment variables")
            raise ValueError("OpenAI API key required")
        else:
            self.logger.info(f"Initializing OpenAI client with model: {model}")
            
        # Create a masked version of the API key for logging 
        masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
        self.logger.debug(f"Using API key: {masked_key}")
        
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Vision models
        self.vision_models = {
            "gpt-4-vision-preview",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini"
        }
        
        # Check if model supports vision
        self.supports_vision = model in self.vision_models
        
        self.logger.info(f"Initialized OpenAI backend with model: {model}")
    
    def process(self, prompt: str, image: Optional[str] = None, 
               **kwargs) -> str:
        """Process text and optional image with GPT-4V.
        
        Args:
            prompt: Text prompt for the model
            image: Base64 encoded image (optional)
            **kwargs: Additional parameters
            
        Returns:
            Model response text
        """
        start_time = time.time()
        debug_info = {
            "prompt_length": len(prompt),
            "has_image": image is not None,
            "image_size_bytes": len(image) if image else 0,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "json_mode": kwargs.get("json_mode", False),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Build messages
            messages = self._build_messages(prompt, image)
            
            # Log the request details
            has_image = image is not None
            json_mode = kwargs.get("json_mode", False)
            self.logger.info(f"Calling OpenAI API - Model: {self.model}, Has Image: {has_image}, JSON Mode: {json_mode}")
            self.logger.debug(f"Prompt length: {len(prompt)} chars, Image size: {len(image) if image else 0} bytes")
            
            # Make API call with retries
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Make API call
                    self.logger.debug(f"Sending request to OpenAI API (attempt {retry_count+1}/{max_retries})...")
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        response_format={"type": "json_object"} if kwargs.get("json_mode") else None
                    )
                    
                    # Extract response
                    content = response.choices[0].message.content
                    
                    # Update debug info with success info
                    debug_info.update({
                        "status": "success",
                        "elapsed_time": time.time() - start_time,
                        "response_length": len(content),
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        }
                    })
                    
                    self.logger.info(f"Received response from OpenAI API - Length: {len(content)} chars in {debug_info['elapsed_time']:.2f}s")
                    self.logger.info(f"Token usage: {response.usage.prompt_tokens} prompt, {response.usage.completion_tokens} completion, {response.usage.total_tokens} total")
                    self.logger.debug(f"OpenAI response preview: {content[:200]}...")
                    
                    # Save detailed debug info if needed
                    self._save_debug_info("api_success", debug_info)
                    
                    return content
                
                except RateLimitError as e:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.warning(f"Rate limit exceeded, retrying in {wait_time}s: {e}")
                    debug_info.update({"retry_info": {"count": retry_count, "error": str(e), "wait_time": wait_time}})
                    
                    if retry_count < max_retries:
                        time.sleep(wait_time)
                    else:
                        debug_info.update({"status": "rate_limit_failure", "error": str(e)})
                        self._save_debug_info("api_rate_limit_error", debug_info)
                        raise ProcessingError(f"Rate limit error: {e}")
                
                except APITimeoutError as e:
                    retry_count += 1
                    wait_time = 2 ** retry_count
                    self.logger.warning(f"OpenAI API timeout, retrying in {wait_time}s: {e}")
                    debug_info.update({"retry_info": {"count": retry_count, "error": str(e), "wait_time": wait_time}})
                    
                    if retry_count < max_retries:
                        time.sleep(wait_time)
                    else:
                        debug_info.update({"status": "timeout_failure", "error": str(e)})
                        self._save_debug_info("api_timeout_error", debug_info)
                        raise ProcessingError(f"API timeout: {e}")
                        
                except APIConnectionError as e:
                    retry_count += 1
                    wait_time = 2 ** retry_count
                    self.logger.warning(f"OpenAI API connection error, retrying in {wait_time}s: {e}")
                    debug_info.update({"retry_info": {"count": retry_count, "error": str(e), "wait_time": wait_time}})
                    
                    if retry_count < max_retries:
                        time.sleep(wait_time)
                    else:
                        debug_info.update({"status": "connection_failure", "error": str(e)})
                        self._save_debug_info("api_connection_error", debug_info)
                        raise ProcessingError(f"API connection error: {e}. Please check your network connection and API endpoint.")
                
                except Exception as e:
                    # Other errors don't retry
                    debug_info.update({"status": "error", "error": str(e)})
                    self._save_debug_info("api_unknown_error", debug_info)
                    raise
            
        except Exception as e:
            # This catches all other exceptions not handled by the retry mechanism
            elapsed_time = time.time() - start_time
            error_type = type(e).__name__
            error_detail = str(e)
            
            # For OpenAI specific errors, try to get more details
            if isinstance(e, APIError):
                error_detail = f"API Error: {e.status_code} - {e.message}"
            
            self.logger.error(f"OpenAI processing error ({error_type}): {error_detail}")
            
            # Log with traceback
            self.logger.error(f"Error details: {traceback.format_exc()}")
            
            debug_info.update({
                "status": "failure",
                "error_type": error_type,
                "error_detail": error_detail,
                "elapsed_time": elapsed_time,
                "traceback": traceback.format_exc()
            })
            
            self._save_debug_info("api_error", debug_info)
            raise ProcessingError(f"Failed to process with OpenAI: {error_detail}")
    
    def process_document_page(self, 
                            page_text: str,
                            page_image: Optional[str] = None,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a document page for semantic extraction.
        
        Args:
            page_text: Extracted text from page
            page_image: Page image as base64 string
            context: Additional context (TOC, previous summaries, etc.)
            
        Returns:
            Semantic analysis results
        """
        # Build semantic extraction prompt
        prompt = self._build_semantic_prompt(page_text, context)
        
        # Process with JSON mode for structured output
        response = self.process(prompt, page_image, json_mode=True)
        
        try:
            # Parse JSON response
            result = json.loads(response)
            
            # Ensure required fields
            return {
                "summary": result.get("summary", ""),
                "key_concepts": result.get("key_concepts", []),
                "relationships": result.get("relationships", []),
                "ontology_tags": result.get("ontology_tags", []),
                "confidence": result.get("confidence", 0.8),
                "evidence": result.get("evidence", [])
            }
            
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON response, extracting text")
            return {
                "summary": response,
                "key_concepts": [],
                "relationships": [],
                "ontology_tags": [],
                "confidence": 0.5,
                "evidence": []
            }
    
    def supports_batch_processing(self) -> bool:
        """Check if backend supports batch processing."""
        return False  # OpenAI processes one at a time
        
    def process_page_with_context(self,
                               image_path: Union[str, Path],
                               extracted_text: str,
                               context: Optional[Dict[str, Any]] = None) -> str:
        """Process page with both extracted text and image for enhanced understanding.
        
        This is the key method for our enhanced semantic pipeline flow.
        
        Args:
            image_path: Path to page image
            extracted_text: Previously extracted text (OCR/markitdown) or a unified prompt
            context: Additional context (TOC, previous summaries, etc.)
            
        Returns:
            Enhanced semantic analysis
        """
        # Check if extracted_text is already a comprehensive prompt
        if "Semantic Analysis Task" in extracted_text and "Response Format" in extracted_text:
            # This is already a unified prompt from SemanticProcessor
            prompt = extracted_text
            self.logger.debug("Using unified prompt from SemanticProcessor")
        else:
            # Build traditional enhanced prompt combining extracted text and image analysis
            prompt = self._build_semantic_prompt(extracted_text, context)
        
        # Read and encode image
        image_path = Path(image_path)
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode()
        
        # Make single API call with both the prompt and image
        self.logger.info(f"Making single call to OpenAI model: {self.model} for comprehensive page analysis")
        
        return self.process(prompt, image_b64, json_mode=True)
    
    def _build_messages(self, prompt: str, image: Optional[str] = None) -> List[Dict]:
        """Build messages for OpenAI API."""
        messages = [
            {
                "role": "system",
                "content": """You are an expert document analyst specializing in semantic extraction. 
Your task is to understand document content deeply and extract meaningful relationships."""
            }
        ]
        
        # Build user message
        user_content = []
        
        # Add text prompt
        user_content.append({
            "type": "text",
            "text": prompt
        })
        
        # Add image if available and model supports it
        if image and self.supports_vision:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image}",
                    "detail": "high"  # High detail for document analysis
                }
            })
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def _build_semantic_prompt(self, page_text: str, 
                             context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for semantic extraction."""
        toc_context = ""
        if context and "toc_structure" in context:
            toc_context = f"""
Document Structure:
{context["toc_structure"]}

Current Section: {context.get("current_section", "Unknown")}
"""
        
        previous_context = ""
        if context and "previous_summaries" in context:
            summaries = context["previous_summaries"][-2:]  # Last 2 summaries
            if summaries:
                previous_context = f"""
Previous Context:
{chr(10).join(summaries)}
"""
        
        prompt = f"""Analyze this document page and extract semantic information.

{toc_context}
{previous_context}

Page Content:
{page_text}

Please provide a comprehensive semantic analysis in JSON format:

{{
    "summary": "A coherent summary that captures the semantic meaning and intent of the content",
    "key_concepts": ["list", "of", "key", "concepts"],
    "relationships": [
        ["source_concept", "relationship_type", "target_concept"],
        // Examples: ["algorithm", "implements", "data structure"]
        //          ["theory", "contradicts", "previous model"]
    ],
    "ontology_tags": ["appropriate", "classification", "tags"],
    "confidence": 0.95,  // Your confidence in the analysis (0-1)
    "evidence": ["specific quotes or references supporting the analysis"]
}}

Focus on:
1. Semantic intent, not just keywords
2. Meaningful relationships between concepts
3. Appropriate ontological classification
4. Context-aware understanding"""
        
        return prompt
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate that response has required fields."""
        required_fields = ["summary", "key_concepts", "relationships", 
                          "ontology_tags", "confidence"]
        
        for field in required_fields:
            if field not in response:
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate types
        if not isinstance(response["key_concepts"], list):
            return False
        
        if not isinstance(response["relationships"], list):
            return False
        
        if not isinstance(response["confidence"], (int, float)):
            return False
        
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": "openai",
            "model": self.model,
            "supports_vision": self.supports_vision,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
    def get_name(self) -> str:
        """Get backend name."""
        return "openai-multimodal"
        
    def supports_image_input(self) -> bool:
        """Check if backend supports image input."""
        return self.supports_vision
        
    def transcribe_image(self, image_path: Union[str, Path]) -> str:
        """Transcribe image to text - required by IntelligenceBackend."""
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode()
        
        prompt = "Extract all text from this image, preserving structure and formatting as much as possible."
        return self.process(prompt, image_b64)
        
    def transcribe_text(self, text: str) -> str:
        """Process text with the model - required by IntelligenceBackend."""
        return self.process(text)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for processing.
        
        Note: These are approximate costs and may change.
        """
        # Approximate pricing (as of 2024)
        pricing = {
            "gpt-4-vision-preview": {
                "input": 0.01 / 1000,  # $0.01 per 1K tokens
                "output": 0.03 / 1000  # $0.03 per 1K tokens
            },
            "gpt-4-turbo": {
                "input": 0.01 / 1000,
                "output": 0.03 / 1000
            },
            "gpt-4o": {
                "input": 0.005 / 1000,
                "output": 0.015 / 1000
            },
            "gpt-4o-mini": {
                "input": 0.00015 / 1000,
                "output": 0.0006 / 1000
            }
        }
        
        if self.model in pricing:
            rates = pricing[self.model]
            return (input_tokens * rates["input"]) + (output_tokens * rates["output"])
        
        # Default estimate
        return (input_tokens * 0.01 / 1000) + (output_tokens * 0.03 / 1000)
        
    def _save_debug_info(self, event_type: str, data: Dict[str, Any]) -> None:
        """Save debug information to file if debug mode is enabled.
        
        Args:
            event_type: Type of event (init, call, response, error)
            data: Debug data to save
        """
        # Only save if debug mode is enabled and debug_dir is set
        if not hasattr(self, "debug_mode") or not self.debug_mode:
            return
            
        try:
            # If no debug dir, just log
            if not hasattr(self, "debug_dir") or not self.debug_dir:
                self.logger.debug(f"Debug event {event_type}: {json.dumps(data, indent=2)}")
                return
                
            # Create timestamped filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{timestamp}_{event_type}.json"
            debug_file = self.debug_dir / filename
            
            # Write debug info
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
                
            self.logger.debug(f"Saved debug info to {debug_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save debug info: {e}")
    
    def _get_caller_info(self) -> Dict[str, str]:
        """Get information about the caller for debugging."""
        caller_info = {}
        try:
            # Get the stack frames
            stack = inspect.stack()
            # Skip this function and look for external callers
            for frame in stack[1:]:
                if frame.filename != __file__:
                    # Found external caller
                    caller_info = {
                        "file": frame.filename,
                        "line": frame.lineno,
                        "function": frame.function
                    }
                    break
        except Exception as e:
            self.logger.debug(f"Failed to get caller info: {e}")
        return caller_info