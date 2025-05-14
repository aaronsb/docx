"""Ollama intelligence backend."""
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Union

import httpx

from pdf_manipulator.intelligence.base import IntelligenceBackend, IntelligenceError


class OllamaBackend(IntelligenceBackend):
    """Intelligence backend using Ollama API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Ollama backend.
        
        Args:
            config: Backend configuration dictionary
        """
        self.model = config.get("model", "llava:latest")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.timeout = config.get("timeout", 120)
    
    def transcribe_image(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe text from an image using Ollama.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for transcription
            
        Returns:
            Transcribed text
            
        Raises:
            IntelligenceError: If transcription fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise IntelligenceError(f"Image file not found: {image_path}")
        
        # Use default prompt if none provided
        if prompt is None:
            prompt = ("Transcribe all text in this document image to markdown format. "
                     "Preserve layout and formatting as best as possible.")
        
        try:
            # Encode the image
            base64_image = self._encode_image(image_path)
            
            # Prepare the request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False,
            }
            
            # Send request to Ollama
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                result = response.json()
            
            return result.get("response", "")
        
        except Exception as e:
            raise IntelligenceError(f"Failed to transcribe image with Ollama: {e}")
    
    def transcribe_text(
        self,
        text: str,
        prompt_template: Optional[str] = None,
    ) -> str:
        """Process text using Ollama.
        
        Args:
            text: Text to process
            prompt_template: Optional custom prompt template
            
        Returns:
            Processed text
            
        Raises:
            IntelligenceError: If processing fails
        """
        if not text:
            return ""
        
        # Use default prompt template if none provided
        if prompt_template is None:
            prompt_template = ("Below is the OCR output from a document. "
                              "Please correct any OCR errors and format the content in clean markdown:\n\n"
                              "{text}\n\nCorrected markdown:")
        
        # Format the prompt
        prompt = prompt_template.format(text=text)
        
        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            
            # Send request to Ollama
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                result = response.json()
            
            return result.get("response", "")
        
        except Exception as e:
            raise IntelligenceError(f"Failed to process text with Ollama: {e}")
    
    def supports_image_input(self) -> bool:
        """Check if Ollama supports direct image input.
        
        Returns:
            True if supported, False otherwise
        """
        # Check if model is likely multimodal
        model_lower = self.model.lower()
        return any(name in model_lower for name in ["llava", "bakllava", "clip", "vision"])
    
    def get_name(self) -> str:
        """Get the name of the intelligence backend.
        
        Returns:
            Backend name
        """
        return "ollama"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Ollama model.
        
        Returns:
            Dictionary with model information
        """
        try:
            # Check if model is loaded
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                result = response.json()
            
            models = result.get("models", [])
            
            # Find the current model
            for model in models:
                if model.get("name") == self.model:
                    return {
                        "name": model.get("name"),
                        "size": model.get("size"),
                        "modified_at": model.get("modified_at"),
                        "details": model
                    }
            
            # Model not found
            return {
                "name": self.model,
                "status": "not_loaded",
                "message": f"Model {self.model} is not loaded. Run 'ollama pull {self.model}' to download it."
            }
        
        except Exception as e:
            return {
                "name": self.model,
                "status": "error",
                "message": f"Failed to get model info: {e}"
            }
    
    def _encode_image(self, image_path: Union[str, Path]) -> str:
        """Encode image to base64.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Base64 encoded image
        """
        image_path = Path(image_path)
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")