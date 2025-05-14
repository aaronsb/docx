"""llama.cpp HTTP server intelligence backend."""
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Union

import httpx

from pdf_manipulator.intelligence.base import IntelligenceBackend, IntelligenceError


class LlamaCppHttpBackend(IntelligenceBackend):
    """Intelligence backend using llama.cpp HTTP server."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the llama.cpp HTTP backend.
        
        Args:
            config: Backend configuration dictionary
        """
        self.base_url = config.get("base_url", "http://localhost:8080")
        self.model = config.get("model")
        self.timeout = config.get("timeout", 120)
        self.n_predict = config.get("n_predict", 2048)
        self.temperature = config.get("temperature", 0.1)
        self.api_key = config.get("api_key") or os.environ.get("LLAMA_API_KEY")
        
        # Ensure base_url doesn't end with a slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
    
    def transcribe_image(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe text from an image using llama.cpp HTTP server.
        
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
                "prompt": prompt,
                "image_data": [{"data": base64_image, "id": 0}],
                "n_predict": self.n_predict,
                "temperature": self.temperature,
                "stream": False,
            }
            
            # Add model name if specified
            if self.model:
                payload["model"] = self.model
            
            # Prepare headers
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Send request to llama.cpp HTTP server
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/completion", json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            # Extract the response based on llama.cpp HTTP API format
            if "content" in result:
                return result.get("content", "")
            elif "completion" in result:
                return result.get("completion", "")
            else:
                raise IntelligenceError("Unexpected response format from llama.cpp HTTP server")
        
        except Exception as e:
            raise IntelligenceError(f"Failed to transcribe image with llama.cpp HTTP server: {e}")
    
    def transcribe_text(
        self,
        text: str,
        prompt_template: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Process text using llama.cpp HTTP server.
        
        Args:
            text: Text to process
            prompt_template: Optional custom prompt template
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling
            
        Returns:
            Processed text
            
        Raises:
            IntelligenceError: If processing fails
        """
        if not text:
            return ""
        
        try:
            # Use default prompt template if none provided
            if prompt_template is None:
                prompt_template = ("Below is the OCR output from a document. "
                                  "Please correct any OCR errors and format the content in clean markdown:\n\n"
                                  "{text}\n\nCorrected markdown:")
            
            # Format the prompt
            prompt = prompt_template.format(text=text)
            
            # Prepare the request payload
            payload = {
                "prompt": prompt,
                "n_predict": max_tokens or self.n_predict,
                "temperature": temperature if temperature is not None else self.temperature,
                "stream": False,
            }
            
            # Add model name if specified
            if self.model:
                payload["model"] = self.model
            
            # Prepare headers
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Send request to llama.cpp HTTP server
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/completion", json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            # Extract the response based on llama.cpp HTTP API format
            if "content" in result:
                return result.get("content", "")
            elif "completion" in result:
                return result.get("completion", "")
            else:
                raise IntelligenceError("Unexpected response format from llama.cpp HTTP server")
        
        except Exception as e:
            raise IntelligenceError(f"Failed to process text with llama.cpp HTTP server: {e}")
    
    def supports_image_input(self) -> bool:
        """Check if this backend supports direct image input.
        
        Returns:
            True, as llama.cpp HTTP server can support image input if configured correctly
        """
        # We assume the server is configured for multimodal input
        # A more robust implementation would check this via API
        return True
    
    def get_name(self) -> str:
        """Get the name of the intelligence backend.
        
        Returns:
            Backend name
        """
        return "llama_cpp_http"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        try:
            # Try to get model info from server
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            with httpx.Client(timeout=self.timeout) as client:
                # Try to get server model info via appropriate endpoint
                try:
                    response = client.get(f"{self.base_url}/model", headers=headers)
                    if response.status_code == 200:
                        return response.json()
                except:
                    pass
                
                # If that fails, try using simple ping to check server connectivity
                try:
                    response = client.get(f"{self.base_url}/health", headers=headers)
                    if response.status_code == 200:
                        return {
                            "status": "online",
                            "url": self.base_url,
                            "model": self.model or "unknown"
                        }
                except:
                    pass
            
            # If we get here, we couldn't connect to the server
            return {
                "status": "unknown",
                "url": self.base_url,
                "model": self.model or "unknown",
                "message": "Could not determine model info from server"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "url": self.base_url,
                "model": self.model or "unknown",
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