"""Enhanced Ollama backend with multimodal support for semantic extraction."""
import os
import base64
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging

import httpx

from .base import IntelligenceBackend
from ..core.exceptions import IntelligenceError, ProcessingError


class OllamaMultimodalBackend(IntelligenceBackend):
    """Enhanced Ollama backend with LLaVA and multimodal support."""
    
    def __init__(self, 
                 model: str = "llava:latest",
                 base_url: str = "http://localhost:11434",
                 timeout: int = 120,
                 logger: Optional[logging.Logger] = None):
        """Initialize enhanced Ollama backend.
        
        Args:
            model: Model to use (e.g., llava, bakllava)
            base_url: Ollama server URL
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        
        # Multimodal models
        self.multimodal_models = {
            "llava", "llava-v1.6", "llava:latest",
            "bakllava", "bakllava:latest",
            "llava-phi3", "llava-llama3",
            "moondream", "moondream:latest"
        }
        
        # Check if model supports vision
        model_lower = self.model.lower()
        self.supports_vision = any(mm in model_lower for mm in self.multimodal_models)
        
        # Verify server connection
        self._verify_connection()
        
        self.logger.info(f"Initialized Ollama backend with model: {model}")
    
    def process(self, prompt: str, image: Optional[str] = None, 
               **kwargs) -> str:
        """Process text and optional image with Ollama multimodal models.
        
        Args:
            prompt: Text prompt for the model
            image: Base64 encoded image (optional)
            **kwargs: Additional parameters
            
        Returns:
            Model response text
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": kwargs.get("temperature", 0.1),
                "top_p": kwargs.get("top_p", 0.9),
                "seed": kwargs.get("seed", 42),  # For reproducibility
            }
            
            # Add image if provided and model supports it
            if image and self.supports_vision:
                payload["images"] = [image]
            elif image:
                self.logger.warning(f"Model {self.model} doesn't support images")
            
            # Add format if JSON mode requested
            if kwargs.get("json_mode"):
                payload["format"] = "json"
                # Ensure prompt mentions JSON format
                if "json" not in prompt.lower():
                    payload["prompt"] = prompt + "\n\nRespond in valid JSON format."
            
            # Send request
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            content = result.get("response", "")
            self.logger.debug(f"Ollama response: {content[:200]}...")
            
            return content
            
        except httpx.TimeoutException:
            raise ProcessingError(f"Ollama request timed out after {self.timeout}s")
        except Exception as e:
            self.logger.error(f"Ollama processing error: {e}")
            raise ProcessingError(f"Failed to process with Ollama: {e}")
    
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
        
        # Process with JSON mode
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
        return False  # Ollama processes one at a time
    
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
        
        prompt = f"""You are analyzing a document page. Extract semantic information.

{toc_context}
{previous_context}

Page Content:
{page_text}

Provide a semantic analysis in JSON format:

{{
    "summary": "A coherent summary capturing the semantic meaning",
    "key_concepts": ["list", "of", "concepts"],
    "relationships": [
        ["source", "relation", "target"]
    ],
    "ontology_tags": ["classification", "tags"],
    "confidence": 0.9,
    "evidence": ["supporting quotes"]
}}

Focus on semantic meaning and relationships."""
        
        return prompt
    
    def _verify_connection(self):
        """Verify connection to Ollama server."""
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                # Check if our model is available
                result = response.json()
                models = result.get("models", [])
                model_names = [m.get("name", "").lower() for m in models]
                
                if self.model.lower() not in model_names:
                    self.logger.warning(f"Model {self.model} not found. Available: {model_names}")
                    
        except Exception as e:
            self.logger.warning(f"Could not verify Ollama connection: {e}")
    
    def download_model(self, model_name: Optional[str] = None):
        """Download/pull a model from Ollama registry."""
        model = model_name or self.model
        
        try:
            with httpx.Client(timeout=None) as client:  # No timeout for downloads
                response = client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model},
                    timeout=None
                )
                response.raise_for_status()
                
                # Stream the response to show progress
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "status" in data:
                            self.logger.info(f"Download status: {data['status']}")
                            
        except Exception as e:
            raise ProcessingError(f"Failed to download model {model}: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                result = response.json()
            
            models = result.get("models", [])
            
            # Find current model
            for model in models:
                if model.get("name", "").lower() == self.model.lower():
                    return {
                        "provider": "ollama",
                        "model": model.get("name"),
                        "size": model.get("size"),
                        "supports_vision": self.supports_vision,
                        "digest": model.get("digest"),
                        "modified_at": model.get("modified_at")
                    }
            
            return {
                "provider": "ollama",
                "model": self.model,
                "supports_vision": self.supports_vision,
                "status": "not_loaded",
                "message": f"Model {self.model} not found. Run: ollama pull {self.model}"
            }
            
        except Exception as e:
            return {
                "provider": "ollama",
                "model": self.model,
                "status": "error",
                "message": str(e)
            }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models on the Ollama server."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                result = response.json()
            
            models = result.get("models", [])
            
            # Filter and enhance model info
            available_models = []
            for model in models:
                model_name = model.get("name", "")
                is_multimodal = any(mm in model_name.lower() for mm in self.multimodal_models)
                
                available_models.append({
                    "name": model_name,
                    "size": model.get("size"),
                    "multimodal": is_multimodal,
                    "digest": model.get("digest"),
                    "modified_at": model.get("modified_at")
                })
            
            return available_models
            
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []
    
    def estimate_processing_time(self, page_count: int) -> float:
        """Estimate processing time for document."""
        # Rough estimates based on model
        if "llava" in self.model.lower():
            time_per_page = 5.0  # seconds
        elif "phi" in self.model.lower():
            time_per_page = 3.0
        else:
            time_per_page = 4.0
        
        return page_count * time_per_page