"""AI-powered document transcription and analysis."""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
import base64
import importlib.util

import httpx
from dotenv import load_dotenv

from pdf_manipulator.core.exceptions import ExtractorError


# Load environment variables
load_dotenv()


class OllamaTranscriber:
    """Document transcriber using Ollama."""
    
    def __init__(
        self,
        model_name: str = "llava:latest",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        """Initialize the Ollama transcriber.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: URL of the Ollama API
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = timeout
    
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
    
    def transcribe_image(
        self,
        image_path: Union[str, Path],
        prompt: str = "Transcribe all text in this document image to markdown format. Preserve layout and formatting as best as possible.",
    ) -> str:
        """Transcribe text from an image using Ollama model.
        
        Args:
            image_path: Path to the image
            prompt: Prompt for the model
            
        Returns:
            Transcribed text
            
        Raises:
            ExtractorError: If transcription fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ExtractorError(f"Image file not found: {image_path}")
        
        try:
            # Encode the image
            base64_image = self._encode_image(image_path)
            
            # Prepare the request payload
            payload = {
                "model": self.model_name,
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
            raise ExtractorError(f"Failed to transcribe image with Ollama: {e}")


class LlamaTranscriber:
    """Document transcriber using llama.cpp."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
    ):
        """Initialize the llama.cpp transcriber.
        
        Args:
            model_path: Path to the model file
            n_ctx: Context window size
            n_gpu_layers: Number of layers to run on GPU (-1 for all)
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._llm = None
        
        # Check if llama_cpp is available
        self._has_llama_cpp = importlib.util.find_spec("llama_cpp") is not None
        if not self._has_llama_cpp:
            print("Warning: llama-cpp-python not installed. Install with: pip install llama-cpp-python")
    
    def _load_model(self):
        """Load the LLM model."""
        if not self._has_llama_cpp:
            raise ExtractorError(
                "llama-cpp-python not installed. Install with: pip install llama-cpp-python or pip install 'doc_ai_toolkit[llama]'"
            )
        
        try:
            from llama_cpp import Llama
            
            model_path = self.model_path
            if not model_path:
                # Try to get from environment
                model_path = os.environ.get("LLAMA_MODEL_PATH")
                
            if not model_path:
                raise ExtractorError("Model path not provided and LLAMA_MODEL_PATH not set")
            
            self._llm = Llama(
                model_path=model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
            )
        
        except ImportError:
            raise ExtractorError("llama-cpp-python not installed correctly. Try reinstalling with: pip install llama-cpp-python")
        except Exception as e:
            raise ExtractorError(f"Failed to load LLM model: {e}")
    
    def transcribe_text(
        self,
        text: str,
        prompt_template: str = "Below is the OCR output from a document. Please correct any OCR errors and format the content in clean markdown:\n\n{text}\n\nCorrected markdown:",
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        """Transcribe and clean OCR text using LLM.
        
        Args:
            text: OCR text to clean and format
            prompt_template: Template for the prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Cleaned and formatted text
            
        Raises:
            ExtractorError: If transcription fails
        """
        try:
            if not self._llm:
                self._load_model()
            
            prompt = prompt_template.format(text=text)
            
            response = self._llm(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                echo=False,
            )
            
            return response["choices"][0]["text"].strip()
        
        except Exception as e:
            raise ExtractorError(f"Failed to transcribe text with llama.cpp: {e}")


class DocumentTranscriber:
    """Document transcriber for processing document images with AI."""
    
    def __init__(
        self,
        transcriber: Union[OllamaTranscriber, LlamaTranscriber, Any],
        use_ocr_fallback: bool = True,
        ocr_fallback: Optional[Callable] = None,
    ):
        """Initialize the document transcriber.
        
        Args:
            transcriber: AI transcriber instance
            use_ocr_fallback: Whether to use OCR as fallback
            ocr_fallback: OCR function to use as fallback
        """
        self.transcriber = transcriber
        self.use_ocr_fallback = use_ocr_fallback
        self.ocr_fallback = ocr_fallback
    
    def transcribe_document_pages(
        self,
        image_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        base_filename: str,
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe multiple document pages and create a structured TOC.
        
        Args:
            image_paths: List of paths to page images
            output_dir: Directory for output files
            base_filename: Base name for output files
            prompt: Custom prompt for transcription
            
        Returns:
            Dictionary with document structure
            
        Raises:
            ExtractorError: If transcription fails
        """
        output_dir = Path(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            toc = {
                "document_name": base_filename,
                "total_pages": len(image_paths),
                "pages": []
            }
            
            for i, image_path in enumerate(image_paths):
                image_path = Path(image_path)
                page_num = i
                
                # First try AI transcription
                try:
                    if isinstance(self.transcriber, OllamaTranscriber):
                        default_prompt = "Transcribe all text in this document image to markdown format. Preserve layout including tables, lists, headings, and paragraphs."
                        text = self.transcriber.transcribe_image(image_path, prompt or default_prompt)
                    else:
                        # For non-Ollama transcribers that can't handle images directly
                        # Use OCR fallback and then clean with LLM
                        if self.use_ocr_fallback and self.ocr_fallback:
                            ocr_text = self.ocr_fallback(image_path)
                            text = self.transcriber.transcribe_text(ocr_text)
                        else:
                            raise ExtractorError("Non-image transcriber needs OCR fallback")
                
                except Exception as e:
                    if self.use_ocr_fallback and self.ocr_fallback:
                        # Fall back to OCR
                        text = self.ocr_fallback(image_path)
                    else:
                        raise ExtractorError(f"Transcription failed and no OCR fallback: {e}")
                
                # Save text to markdown file
                md_path = output_dir / f"{image_path.stem}.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Page {page_num + 1}\n\n{text}")
                
                # Add page info to TOC
                page_info = {
                    "page_number": page_num + 1,
                    "image_file": str(image_path.name),
                    "markdown_file": str(md_path.name),
                    "first_line": text.split('\n')[0] if text else "",
                    "word_count": len(text.split()) if text else 0,
                }
                
                toc["pages"].append(page_info)
            
            # Save TOC to JSON file
            toc_path = output_dir / f"{base_filename}_contents.json"
            with open(toc_path, 'w', encoding='utf-8') as f:
                json.dump(toc, f, indent=2)
            
            return toc
        
        except Exception as e:
            raise ExtractorError(f"Failed to transcribe document: {e}")