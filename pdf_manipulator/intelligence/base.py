"""Base classes for intelligence backends."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from pdf_manipulator.core.exceptions import PDFManipulatorError


class IntelligenceError(PDFManipulatorError):
    """Error from intelligence processing."""
    pass


class IntelligenceBackend(ABC):
    """Base class for intelligence backends."""
    
    @abstractmethod
    def transcribe_image(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe text from an image.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for transcription
            
        Returns:
            Transcribed text
            
        Raises:
            IntelligenceError: If transcription fails
        """
        pass
    
    @abstractmethod
    def transcribe_text(
        self,
        text: str,
        prompt_template: Optional[str] = None,
    ) -> str:
        """Process text using the intelligence backend.
        
        Args:
            text: Text to process
            prompt_template: Optional custom prompt template
            
        Returns:
            Processed text
            
        Raises:
            IntelligenceError: If processing fails
        """
        pass
    
    @abstractmethod
    def supports_image_input(self) -> bool:
        """Check if the backend supports direct image input.
        
        Returns:
            True if the backend supports image input, False otherwise
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the intelligence backend.
        
        Returns:
            Backend name
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        pass


class IntelligenceManager:
    """Factory and manager for intelligence backends."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the intelligence manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._backends = {}
    
    def get_backend(self, backend_name: Optional[str] = None) -> IntelligenceBackend:
        """Get an intelligence backend instance.
        
        Args:
            backend_name: Name of the backend to use.
                If None, uses the default backend from config.
                
        Returns:
            Intelligence backend instance
            
        Raises:
            IntelligenceError: If the backend cannot be created
        """
        # Determine which backend to use
        if backend_name is None:
            # Use default from config
            backend_name = self.config.get("intelligence", {}).get(
                "default_backend", "markitdown"
            )
        
        # Convert name format (llama-cpp or llama_cpp to llama_cpp)
        backend_name = backend_name.replace("-", "_")
        
        # Return cached backend if available
        if backend_name in self._backends:
            return self._backends[backend_name]
        
        # Create new backend
        try:
            backend = self._create_backend(backend_name)
            self._backends[backend_name] = backend
            return backend
        
        except Exception as e:
            raise IntelligenceError(f"Failed to create intelligence backend '{backend_name}': {e}")
    
    def _create_backend(self, backend_name: str) -> IntelligenceBackend:
        """Create an intelligence backend.
        
        Args:
            backend_name: Name of the backend to create
            
        Returns:
            Intelligence backend instance
            
        Raises:
            IntelligenceError: If the backend cannot be created
        """
        # Get backend configuration
        backend_config = self.config.get("intelligence", {}).get("backends", {}).get(backend_name, {})
        
        # Import the appropriate backend
        if backend_name == "markitdown":
            from pdf_manipulator.intelligence.markitdown import MarkitdownBackend
            return MarkitdownBackend(backend_config)
        
        elif backend_name == "ollama":
            from pdf_manipulator.intelligence.ollama import OllamaBackend
            return OllamaBackend(backend_config)
        
        elif backend_name == "ollama_multimodal":
            from pdf_manipulator.intelligence.ollama_multimodal import OllamaMultimodalBackend
            # Extract specific parameters for OllamaMultimodalBackend
            model = backend_config.get("model", "llava:latest")
            base_url = backend_config.get("base_url", "http://localhost:11434")
            timeout = backend_config.get("timeout", 120)
            return OllamaMultimodalBackend(model=model, base_url=base_url, timeout=timeout)
        
        elif backend_name == "openai":
            from pdf_manipulator.intelligence.openai_multimodal import OpenAIMultimodalBackend
            # Extract specific parameters for OpenAIMultimodalBackend
            api_key = backend_config.get("api_key")
            model = backend_config.get("model", "gpt-4o-mini")
            max_tokens = backend_config.get("max_tokens", 4096)
            temperature = backend_config.get("temperature", 0.1)
            timeout = backend_config.get("timeout", 60)
            return OpenAIMultimodalBackend(
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
        
        elif backend_name == "llama_cpp":
            from pdf_manipulator.intelligence.llama_cpp import LlamaCppBackend
            return LlamaCppBackend(backend_config)
        
        elif backend_name == "llama_cpp_http":
            from pdf_manipulator.intelligence.llama_cpp_http import LlamaCppHttpBackend
            return LlamaCppHttpBackend(backend_config)
        
        else:
            raise IntelligenceError(f"Unknown intelligence backend: {backend_name}")
    
    def list_available_backends(self) -> List[str]:
        """List available intelligence backends.
        
        Returns:
            List of backend names
        """
        # Check for availability of each backend
        available = []
        
        # markitdown (added first as the preferred default)
        try:
            from pdf_manipulator.intelligence.markitdown import MarkitdownBackend
            available.append("markitdown")
        except ImportError:
            pass
        
        # Ollama
        try:
            from pdf_manipulator.intelligence.ollama import OllamaBackend
            available.append("ollama")
        except ImportError:
            pass
        
        # OpenAI
        try:
            from pdf_manipulator.intelligence.openai_multimodal import OpenAIMultimodalBackend
            available.append("openai")
        except ImportError:
            pass
        
        # llama.cpp
        try:
            from pdf_manipulator.intelligence.llama_cpp import LlamaCppBackend
            available.append("llama_cpp")
        except ImportError:
            pass
        
        # llama.cpp HTTP
        try:
            from pdf_manipulator.intelligence.llama_cpp_http import LlamaCppHttpBackend
            available.append("llama_cpp_http")
        except ImportError:
            pass
        
        return available