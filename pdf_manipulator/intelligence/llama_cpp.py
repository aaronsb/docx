"""llama.cpp direct intelligence backend."""
import os
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, Union

from pdf_manipulator.intelligence.base import IntelligenceBackend, IntelligenceError


class LlamaCppBackend(IntelligenceBackend):
    """Intelligence backend using llama.cpp Python bindings."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the llama.cpp backend.
        
        Args:
            config: Backend configuration dictionary
            
        Raises:
            IntelligenceError: If llama-cpp-python is not installed
        """
        # Check if llama_cpp is available
        self._has_llama_cpp = importlib.util.find_spec("llama_cpp") is not None
        if not self._has_llama_cpp:
            raise IntelligenceError(
                "llama-cpp-python not installed. Install with: pip install llama-cpp-python "
                "or pip install 'pdf_manipulator[llama]'"
            )
        
        # Store configuration
        self.model_path = config.get("model_path")
        self.n_ctx = config.get("n_ctx", 2048)
        self.n_gpu_layers = config.get("n_gpu_layers", -1)
        
        # Try to get model path from environment if not in config
        if not self.model_path:
            self.model_path = os.environ.get("LLAMA_MODEL_PATH")
            if not self.model_path:
                raise IntelligenceError(
                    "No model path provided for llama_cpp backend. "
                    "Set model_path in config or LLAMA_MODEL_PATH environment variable."
                )
        
        # Initialize llama.cpp model (lazy loading)
        self._llm = None
    
    def _load_model(self):
        """Load the LLM model.
        
        Raises:
            IntelligenceError: If model cannot be loaded
        """
        if self._llm is not None:
            return
        
        try:
            from llama_cpp import Llama
            
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
            )
        
        except ImportError:
            raise IntelligenceError(
                "llama-cpp-python not installed correctly. "
                "Try reinstalling with: pip install llama-cpp-python"
            )
        except Exception as e:
            raise IntelligenceError(f"Failed to load LLM model: {e}")
    
    def transcribe_image(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe text from an image.
        
        This backend doesn't support direct image transcription without OCR.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for transcription
            
        Raises:
            IntelligenceError: Always, as this backend doesn't support direct image input
        """
        raise IntelligenceError(
            "llama.cpp backend doesn't support direct image transcription. "
            "Use OCR first and then process the text with this backend."
        )
    
    def transcribe_text(
        self,
        text: str,
        prompt_template: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        """Process text using llama.cpp.
        
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
        try:
            if not text:
                return ""
            
            # Ensure model is loaded
            self._load_model()
            
            # Use default prompt template if none provided
            if prompt_template is None:
                prompt_template = ("Below is the OCR output from a document. "
                                  "Please correct any OCR errors and format the content in clean markdown:\n\n"
                                  "{text}\n\nCorrected markdown:")
            
            # Format the prompt
            prompt = prompt_template.format(text=text)
            
            # Generate response
            response = self._llm(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                echo=False,
            )
            
            return response["choices"][0]["text"].strip()
        
        except Exception as e:
            raise IntelligenceError(f"Failed to process text with llama.cpp: {e}")
    
    def supports_image_input(self) -> bool:
        """Check if this backend supports direct image input.
        
        Returns:
            False, as this backend doesn't support direct image input
        """
        return False
    
    def get_name(self) -> str:
        """Get the name of the intelligence backend.
        
        Returns:
            Backend name
        """
        return "llama_cpp"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        model_path = Path(self.model_path)
        
        return {
            "name": model_path.name,
            "path": str(model_path),
            "size": model_path.stat().st_size if model_path.exists() else None,
            "parameters": {
                "n_ctx": self.n_ctx,
                "n_gpu_layers": self.n_gpu_layers
            }
        }