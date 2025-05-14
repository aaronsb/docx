"""OCR functionality for document processing."""
import os
import sys
import shutil
import platform
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
import importlib.util

import numpy as np
from PIL import Image

from pdf_manipulator.core.exceptions import ExtractorError


class OCRProcessor:
    """OCR processor for extracting text from images."""

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        language: str = "eng",
        config: Optional[str] = None,
        tessdata_dir: Optional[str] = None,
    ):
        """Initialize the OCR processor.
        
        Args:
            tesseract_cmd: Path to tesseract executable
            language: Language for OCR
            config: Configuration for Tesseract
            tessdata_dir: Path to tessdata directory
        """
        self.language = language
        self.config = config
        self._pytesseract = None
        
        # Configure tesseract environment
        if tessdata_dir:
            os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
        
        # Check for tesseract installation
        self._is_tesseract_available = False
        self._tesseract_error = None
        
        try:
            # Try to import pytesseract
            import pytesseract
            self._pytesseract = pytesseract
            
            # Set custom tesseract command if provided
            if tesseract_cmd:
                self._pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            else:
                # Try to find tesseract in PATH
                tesseract_path = shutil.which('tesseract')
                if tesseract_path:
                    self._pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Verify tesseract is working by getting version
            version = self._pytesseract.get_tesseract_version()
            self._is_tesseract_available = True
        except Exception as e:
            self._tesseract_error = str(e)
            
            # If this is ImportError, provide more helpful message
            if isinstance(e, ImportError):
                self._tesseract_error = "pytesseract is not installed. Install with: pip install pytesseract"
            
            # If tesseract command not found, provide installation instructions
            if "tesseract" in str(e).lower() and ("not" in str(e).lower() or "failed" in str(e).lower()):
                self._provide_tesseract_install_guidance()
    
    def _provide_tesseract_install_guidance(self):
        """Provide guidance for installing Tesseract based on OS."""
        os_name = platform.system().lower()
        
        if os_name == "linux":
            self._tesseract_error += "\n\nInstall Tesseract on Linux with:\n"
            self._tesseract_error += "  sudo apt-get update\n"
            self._tesseract_error += "  sudo apt-get install -y tesseract-ocr\n"
            self._tesseract_error += "  sudo apt-get install -y tesseract-ocr-eng  # or other language packs"
        elif os_name == "darwin":  # macOS
            self._tesseract_error += "\n\nInstall Tesseract on macOS with:\n"
            self._tesseract_error += "  brew install tesseract\n"
            self._tesseract_error += "  brew install tesseract-lang  # for additional languages"
        elif os_name == "windows":
            self._tesseract_error += "\n\nInstall Tesseract on Windows:\n"
            self._tesseract_error += "  1. Download installer from https://github.com/UB-Mannheim/tesseract/wiki\n"
            self._tesseract_error += "  2. Install and add to PATH\n"
            self._tesseract_error += "  3. Set TESSDATA_PREFIX environment variable to tessdata directory"
        
        self._tesseract_error += "\n\nAlternatively, specify tessdata_dir parameter:\n"
        self._tesseract_error += "  OCRProcessor(tessdata_dir='/path/to/tessdata')\n"
        self._tesseract_error += "\nOr use the TESSDATA_PREFIX environment variable:\n"
        self._tesseract_error += "  export TESSDATA_PREFIX=/path/to/tessdata"
    
    def _ensure_tesseract_available(self):
        """Verify that tesseract is available and raise error if not."""
        if not self._is_tesseract_available:
            raise ExtractorError(
                f"Tesseract OCR is not available: {self._tesseract_error}\n\n"
                "You can use AI transcription with --use-ai flag instead."
            )
    
    def configure_tesseract(self, 
                           tesseract_cmd: Optional[str] = None, 
                           tessdata_dir: Optional[str] = None):
        """Reconfigure tesseract settings.
        
        Args:
            tesseract_cmd: Path to tesseract executable
            tessdata_dir: Path to tessdata directory
            
        Returns:
            True if configuration was successful
        """
        try:
            # Set tessdata directory
            if tessdata_dir:
                os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
            
            # Set command path
            if tesseract_cmd and self._pytesseract:
                self._pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            # Try to import pytesseract if not already done
            if not self._pytesseract:
                import pytesseract
                self._pytesseract = pytesseract
                
                if tesseract_cmd:
                    self._pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            # Test configuration
            version = self._pytesseract.get_tesseract_version()
            self._is_tesseract_available = True
            return True
        
        except Exception as e:
            self._tesseract_error = str(e)
            self._is_tesseract_available = False
            return False
    
    def extract_text(self, image_path: Union[str, Path]) -> str:
        """Extract text from an image.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Extracted text
            
        Raises:
            ExtractorError: If extraction fails
        """
        self._ensure_tesseract_available()
        
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ExtractorError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            text = self._pytesseract.image_to_string(image, lang=self.language, config=self.config)
            return text
        
        except Exception as e:
            # Special handling for language data errors
            if "Failed loading language" in str(e):
                raise ExtractorError(
                    f"Failed to load language '{self.language}' in Tesseract. "
                    f"Make sure the language data is installed in the tessdata directory. "
                    f"Try: sudo apt-get install tesseract-ocr-{self.language}"
                )
            raise ExtractorError(f"Failed to extract text from image: {e}")
    
    def extract_data(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract structured data from an image including text, layout and confidence.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Dictionary with extracted data
            
        Raises:
            ExtractorError: If extraction fails
        """
        self._ensure_tesseract_available()
        
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ExtractorError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            data = self._pytesseract.image_to_data(
                image, 
                lang=self.language, 
                config=self.config, 
                output_type=self._pytesseract.Output.DICT
            )
            
            # Convert numpy arrays to lists for JSON serialization
            for k, v in data.items():
                if isinstance(v, np.ndarray):
                    data[k] = v.tolist()
            
            return data
        
        except Exception as e:
            raise ExtractorError(f"Failed to extract data from image: {e}")
    
    def extract_boxes(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract bounding boxes for text regions.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Dictionary with bounding box data
            
        Raises:
            ExtractorError: If extraction fails
        """
        self._ensure_tesseract_available()
        
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ExtractorError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            boxes = self._pytesseract.image_to_boxes(image, lang=self.language, config=self.config)
            
            # Parse boxes output
            result = []
            for box in boxes.splitlines():
                parts = box.split()
                if len(parts) >= 5:
                    char, x1, y1, x2, y2 = parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                    result.append({
                        "char": char,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    })
            
            return {"boxes": result}
        
        except Exception as e:
            raise ExtractorError(f"Failed to extract boxes from image: {e}")


class DocumentAnalyzer:
    """Document analyzer for extracting structure and content."""
    
    def __init__(self, ocr_processor: OCRProcessor):
        """Initialize the document analyzer.
        
        Args:
            ocr_processor: OCR processor to use for text extraction
        """
        self.ocr = ocr_processor
    
    def analyze_document_pages(
        self,
        image_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        base_filename: str,
    ) -> Dict[str, Any]:
        """Analyze multiple document pages and create a structured TOC.
        
        Args:
            image_paths: List of paths to page images
            output_dir: Directory for output files
            base_filename: Base name for output files
            
        Returns:
            Dictionary with document structure
            
        Raises:
            ExtractorError: If analysis fails
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
                
                # Extract page text
                text = self.ocr.extract_text(image_path)
                
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
            raise ExtractorError(f"Failed to analyze document: {e}")