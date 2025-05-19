"""Structure analyzer for document TOC extraction and construction."""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging
from pathlib import Path

import fitz  # PyMuPDF
from markitdown import MarkItDown

from ..memory.toc_processor import TOCStructure, TOCEntry, TOCFormat, TOCProcessor
from ..core.exceptions import DocumentProcessingError


@dataclass
class Section:
    """Represents a document section."""
    id: str
    title: str
    number: Optional[str]
    level: int
    page_start: int
    page_end: Optional[int]
    content: Optional[str]
    parent_id: Optional[str]
    children_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "number": self.number,
            "level": self.level,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "content": self.content,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "confidence": self.confidence
        }


class HeadingDetector:
    """Detects headings in text content."""
    
    def __init__(self):
        """Initialize heading patterns."""
        self.patterns = [
            # Numbered sections: "1.2.3 Title"
            (r'^(\d+(?:\.\d+)*)\s+([A-Z].*?)$', 'numbered'),
            # Chapter style: "Chapter 1: Title"
            (r'^(Chapter\s+\d+:?)\s+(.+)$', 'chapter'),
            # Markdown style: "# Title" or "## Title"
            (r'^(#{1,6})\s+(.+)$', 'markdown'),
            # Roman numerals: "I. Title"
            (r'^([IVXLCDM]+\.?)\s+(.+)$', 'roman'),
            # Lettered sections: "A. Title"
            (r'^([A-Z]\.)\s+(.+)$', 'lettered'),
            # Uppercase title (heuristic)
            (r'^([A-Z][A-Z\s]+)$', 'uppercase'),
        ]
        
        # Heading keywords
        self.keywords = {
            'introduction', 'conclusion', 'summary', 'abstract',
            'preface', 'foreword', 'appendix', 'references',
            'bibliography', 'glossary', 'index', 'acknowledgments'
        }
    
    def detect_headings(self, text: str) -> List[Tuple[str, str, int, str]]:
        """Detect headings in text content.
        
        Returns:
            List of (title, number, confidence, type) tuples
        """
        headings = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check patterns
            for pattern, heading_type in self.patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    groups = match.groups()
                    
                    if heading_type == 'numbered':
                        number, title = groups
                        confidence = 0.9
                    elif heading_type == 'chapter':
                        number, title = groups[0], groups[1]
                        confidence = 0.95
                    elif heading_type == 'markdown':
                        number = str(len(groups[0]))  # Count #'s
                        title = groups[1]
                        confidence = 0.85
                    elif heading_type == 'uppercase':
                        title = groups[0]
                        number = None
                        confidence = 0.6
                    else:
                        number = groups[0] if len(groups) > 1 else None
                        title = groups[-1]
                        confidence = 0.7
                    
                    # Boost confidence for keywords
                    if any(keyword in title.lower() for keyword in self.keywords):
                        confidence = min(confidence + 0.1, 1.0)
                    
                    headings.append((title, number, confidence, heading_type))
                    break
        
        return headings


class StructureAnalyzer:
    """Enhanced structure analyzer for document TOC extraction and construction."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the structure analyzer."""
        self.logger = logger or logging.getLogger(__name__)
        self.toc_processor = TOCProcessor(logger=self.logger)
        self.heading_detector = HeadingDetector()
        self.markitdown = MarkItDown()
        
    def extract_toc(self, pdf_path: str) -> Optional[TOCStructure]:
        """Extract existing TOC from PDF using native methods."""
        try:
            doc = fitz.open(pdf_path)
            
            # Try to get TOC from PDF metadata
            toc_metadata = doc.get_toc()
            if toc_metadata:
                return self._parse_metadata_toc(toc_metadata, doc)
            
            # Fall back to text-based detection
            pages_text = {}
            for page_num in range(len(doc)):
                page = doc[page_num]
                pages_text[page_num] = page.get_text()
            
            # Use existing TOC processor for text-based detection
            toc_result = self.toc_processor.detect_toc(pages_text)
            if toc_result:
                toc_pages, toc_content = toc_result
                return self.toc_processor.parse_toc(toc_content, toc_pages)
            
            doc.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting TOC: {e}")
            return None
    
    def construct_toc(self, pdf_path: str, page_contents: Optional[List[str]] = None) -> TOCStructure:
        """Construct TOC from page-level analysis using markitdown."""
        try:
            # Extract content if not provided
            if page_contents is None:
                page_contents = self._extract_page_contents(pdf_path)
            
            sections = []
            section_id_counter = 0
            
            # Process each page to find headings
            for page_num, content in enumerate(page_contents):
                # Convert to markdown using markitdown
                markdown_content = self._convert_to_markdown(content, page_num)
                
                # Detect headings
                headings = self.heading_detector.detect_headings(markdown_content)
                
                for title, number, confidence, heading_type in headings:
                    if confidence < 0.5:  # Skip low confidence headings
                        continue
                    
                    # Determine level from heading type and number
                    level = self._determine_heading_level(number, heading_type)
                    
                    section = Section(
                        id=f"section_{section_id_counter}",
                        title=title,
                        number=number,
                        level=level,
                        page_start=page_num,
                        page_end=None,
                        content=None,
                        parent_id=None,
                        confidence=confidence
                    )
                    sections.append(section)
                    section_id_counter += 1
            
            # Build hierarchy and create TOC structure
            return self._build_toc_from_sections(sections)
            
        except Exception as e:
            self.logger.error(f"Error constructing TOC: {e}")
            raise DocumentProcessingError(f"Failed to construct TOC: {e}")
    
    def analyze_hierarchy(self, content: str) -> List[Section]:
        """Detect section headers and structure in content."""
        sections = []
        
        # Extract headings
        headings = self.heading_detector.detect_headings(content)
        
        # Convert to sections
        for i, (title, number, confidence, heading_type) in enumerate(headings):
            level = self._determine_heading_level(number, heading_type)
            
            section = Section(
                id=f"content_section_{i}",
                title=title,
                number=number,
                level=level,
                page_start=0,  # Will be set by caller
                page_end=None,
                content=None,
                parent_id=None,
                confidence=confidence
            )
            sections.append(section)
        
        return sections
    
    def extract_or_construct_toc(self, pdf_path: str) -> TOCStructure:
        """Extract existing TOC or construct one if not found."""
        # Try native extraction first
        toc = self.extract_toc(pdf_path)
        if toc:
            self.logger.info("Successfully extracted native TOC")
            return toc
        
        # Fall back to construction
        self.logger.info("No native TOC found, constructing from content")
        return self.construct_toc(pdf_path)
    
    def _parse_metadata_toc(self, toc_metadata: List, doc: fitz.Document) -> TOCStructure:
        """Parse TOC from PDF metadata."""
        entries = []
        root_entries = []
        
        for item in toc_metadata:
            level, title, page_num = item[0], item[1], item[2]
            
            # Create TOC entry
            entry = TOCEntry(
                number="",  # Metadata doesn't provide section numbers
                title=title,
                page=page_num - 1,  # Convert to 0-based
                level=level,
                raw_text=title
            )
            entries.append(entry)
        
        # Build hierarchy
        stack = []
        for entry in entries:
            # Find parent
            while stack and stack[-1].level >= entry.level:
                stack.pop()
            
            if stack:
                parent = stack[-1]
                parent.add_child(entry)
            else:
                root_entries.append(entry)
            
            stack.append(entry)
        
        return TOCStructure(
            entries=entries,
            format=TOCFormat.UNKNOWN,
            toc_pages=[],  # Metadata TOC doesn't have specific pages
            root_entries=root_entries
        )
    
    def _extract_page_contents(self, pdf_path: str) -> List[str]:
        """Extract text content from each page."""
        contents = []
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                contents.append(text)
            doc.close()
        except Exception as e:
            self.logger.error(f"Error extracting page contents: {e}")
            raise DocumentProcessingError(f"Failed to extract page contents: {e}")
        
        return contents
    
    def _convert_to_markdown(self, content: str, page_num: int) -> str:
        """Convert content to markdown using markitdown."""
        try:
            # Write content to temporary file for markitdown
            temp_file = Path(f"/tmp/page_{page_num}.txt")
            temp_file.write_text(content)
            
            # Convert using markitdown
            result = self.markitdown.convert(str(temp_file))
            markdown = result.text_content
            
            # Clean up
            temp_file.unlink()
            
            return markdown
        except Exception as e:
            self.logger.warning(f"Markitdown conversion failed, using raw text: {e}")
            return content
    
    def _determine_heading_level(self, number: Optional[str], heading_type: str) -> int:
        """Determine heading level from number and type."""
        if number and '.' in str(number):
            # Count dots for numbered sections
            return str(number).count('.') + 1
        elif heading_type == 'chapter':
            return 1
        elif heading_type == 'markdown' and number:
            # Markdown level from # count
            return int(number)
        elif heading_type == 'uppercase':
            return 1  # Assume main sections
        else:
            # Default based on type
            type_levels = {
                'roman': 1,
                'lettered': 2,
                'numbered': 1,
            }
            return type_levels.get(heading_type, 2)
    
    def _build_toc_from_sections(self, sections: List[Section]) -> TOCStructure:
        """Build TOC structure from detected sections."""
        # Convert sections to TOC entries
        entries = []
        for section in sections:
            entry = TOCEntry(
                number=section.number or "",
                title=section.title,
                page=section.page_start,
                level=section.level,
                raw_text=section.title
            )
            entries.append(entry)
        
        # Build hierarchy
        root_entries = self.toc_processor._build_hierarchy(entries)
        
        return TOCStructure(
            entries=entries,
            format=TOCFormat.UNKNOWN,
            toc_pages=[],  # Constructed TOC doesn't have specific pages
            root_entries=root_entries
        )
    
    def get_confidence_score(self, toc: TOCStructure) -> float:
        """Calculate confidence score for TOC structure."""
        if not toc.entries:
            return 0.0
        
        # Factors for confidence
        has_page_numbers = all(entry.page >= 0 for entry in toc.entries)
        has_hierarchy = any(entry.level > 1 for entry in toc.entries)
        has_section_numbers = any(entry.number for entry in toc.entries)
        entry_count = len(toc.entries)
        
        # Calculate score
        score = 0.0
        if has_page_numbers:
            score += 0.3
        if has_hierarchy:
            score += 0.3
        if has_section_numbers:
            score += 0.2
        if entry_count >= 5:
            score += 0.2
        
        # Adjust for format
        if toc.format != TOCFormat.UNKNOWN:
            score += 0.1
        
        return min(score, 1.0)