"""OpenAI multimodal backend with GPT-4V support."""
import os
import base64
import json
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from .base import IntelligenceBackend
from ..core.exceptions import ProcessingError


class OpenAIMultimodalBackend(IntelligenceBackend):
    """OpenAI API backend with vision support for semantic extraction."""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-4-vision-preview",
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
            raise ValueError("OpenAI API key required")
        
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
        try:
            # Build messages
            messages = self._build_messages(prompt, image)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"} if kwargs.get("json_mode") else None
            )
            
            # Extract response
            content = response.choices[0].message.content
            
            self.logger.debug(f"OpenAI response: {content[:200]}...")
            
            return content
            
        except Exception as e:
            self.logger.error(f"OpenAI processing error: {e}")
            raise ProcessingError(f"Failed to process with OpenAI: {e}")
    
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