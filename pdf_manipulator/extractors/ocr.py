"""OCR functionality for document processing."""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json

import pytesseract
from PIL import Image
import numpy as np

from pdf_manipulator.core.exceptions import ExtractorError


class OCRProcessor:
    """OCR processor for extracting text from images."""

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        language: str = "eng",
        config: Optional[str] = None,
    ):
        """Initialize the OCR processor.
        
        Args:
            tesseract_cmd: Path to tesseract executable
            language: Language for OCR
            config: Configuration for Tesseract
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.language = language
        self.config = config
    
    def extract_text(self, image_path: Union[str, Path]) -> str:
        """Extract text from an image.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Extracted text
            
        Raises:
            ExtractorError: If extraction fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ExtractorError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.language, config=self.config)
            return text
        
        except Exception as e:
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
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ExtractorError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, lang=self.language, config=self.config, output_type=pytesseract.Output.DICT)
            
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
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ExtractorError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            boxes = pytesseract.image_to_boxes(image, lang=self.language, config=self.config)
            
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