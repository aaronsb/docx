"""Table of Contents processor for document structure extraction."""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging


class TOCFormat(Enum):
    """Supported TOC formats."""
    DOT_LEADER = "dot_leader"  # Title ........... 23
    TAB_SEPARATED = "tab_separated"  # Title\t23
    NUMBERED = "numbered"  # 1.2.3 Title  23
    INDENTED = "indented"  # Hierarchical indentation
    UNKNOWN = "unknown"


@dataclass
class TOCEntry:
    """Represents a single table of contents entry."""
    number: str  # Section number (e.g., "1.2.3")
    title: str  # Section title
    page: int  # Page number
    level: int  # Hierarchy level (1-based)
    raw_text: str  # Original text from TOC
    children: List['TOCEntry'] = field(default_factory=list)
    parent: Optional['TOCEntry'] = None
    
    def add_child(self, child: 'TOCEntry'):
        """Add a child entry."""
        child.parent = self
        self.children.append(child)
    
    def get_full_path(self) -> str:
        """Get the full hierarchical path."""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.title}"
        return self.title


@dataclass
class TOCStructure:
    """Complete table of contents structure."""
    entries: List[TOCEntry]
    format: TOCFormat
    toc_pages: List[int]  # Pages containing the TOC
    root_entries: List[TOCEntry]  # Top-level entries
    
    def get_flat_entries(self) -> List[TOCEntry]:
        """Get all entries in a flat list."""
        flat = []
        
        def traverse(entry: TOCEntry):
            flat.append(entry)
            for child in entry.children:
                traverse(child)
        
        for root in self.root_entries:
            traverse(root)
        
        return flat
    
    def find_entry_by_page(self, page: int) -> Optional[TOCEntry]:
        """Find entry by page number."""
        for entry in self.get_flat_entries():
            if entry.page == page:
                return entry
        return None


class TOCProcessor:
    """Processor for detecting and parsing table of contents."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the TOC processor."""
        self.logger = logger or logging.getLogger(__name__)
        
        # TOC detection patterns
        self.toc_indicators = [
            r'table\s+of\s+contents',
            r'contents',
            r'toc',
            r'índice',  # Spanish
            r'table\s+des\s+matières',  # French
            r'inhaltsverzeichnis',  # German
        ]
        
        # Entry parsing patterns
        self.entry_patterns = {
            TOCFormat.DOT_LEADER: [
                # Matches: "1.2.3 Section Title ........... 23"
                r'^([\d.]+)?\s*(.+?)\s*\.{2,}\s*(\d+)$',
                # Matches: "Chapter 1: Title ........... 23"
                r'^(Chapter\s+\d+:?)\s*(.+?)\s*\.{2,}\s*(\d+)$',
                # Matches: "Section Title ........... 23"
                r'^(.+?)\s*\.{2,}\s*(\d+)$',
            ],
            TOCFormat.TAB_SEPARATED: [
                # Matches: "1.2.3\tSection Title\t23"
                r'^([\d.]+)?\t(.+?)\t(\d+)$',
                # Matches: "Section Title\t23"
                r'^(.+?)\t(\d+)$',
            ],
            TOCFormat.NUMBERED: [
                # Matches: "1.2.3 Section Title  23"
                r'^([\d.]+)\s+(.+?)\s+(\d+)$',
                # Matches: "1. Section Title  23"
                r'^(\d+\.)\s+(.+?)\s+(\d+)$',
            ],
        }
    
    def detect_toc(self, pages: Dict[int, str]) -> Optional[Tuple[List[int], str]]:
        """Detect table of contents in the document.
        
        Returns:
            Tuple of (TOC page numbers, TOC content) or None
        """
        toc_pages = []
        toc_content = []
        
        for page_num in sorted(pages.keys()):
            content = pages[page_num]
            
            # Check for TOC indicators
            if self._is_toc_page(content):
                toc_pages.append(page_num)
                toc_content.append(content)
                
                # Look for continuation pages
                if self._continues_on_next_page(content):
                    # Check next few pages for continuation
                    for i in range(1, 4):  # Check up to 3 pages ahead
                        next_page = page_num + i
                        if next_page in pages:
                            next_content = pages[next_page]
                            if self._is_toc_continuation(next_content):
                                toc_pages.append(next_page)
                                toc_content.append(next_content)
                            else:
                                break
                
                # Found TOC, return it
                return toc_pages, '\n'.join(toc_content)
        
        return None
    
    def parse_toc(self, toc_content: str, toc_pages: List[int]) -> Optional[TOCStructure]:
        """Parse table of contents structure.
        
        Args:
            toc_content: Combined TOC text
            toc_pages: Pages containing the TOC
            
        Returns:
            TOCStructure or None if parsing fails
        """
        # Detect format
        format_type = self._detect_format(toc_content)
        
        # Parse entries based on format
        entries = self._parse_entries(toc_content, format_type)
        
        if not entries:
            self.logger.warning("No entries found in TOC")
            return None
        
        # Build hierarchy
        root_entries = self._build_hierarchy(entries)
        
        return TOCStructure(
            entries=entries,
            format=format_type,
            toc_pages=toc_pages,
            root_entries=root_entries
        )
    
    def _is_toc_page(self, content: str) -> bool:
        """Check if a page is a table of contents."""
        lower_content = content.lower()
        
        # Check for TOC indicators
        for pattern in self.toc_indicators:
            if re.search(pattern, lower_content, re.IGNORECASE):
                # Additional validation: should have multiple entries with page numbers
                # Look for page numbers at end of line or after dots
                page_number_patterns = [
                    r'\b\d+\s*$',  # Number at end of line
                    r'\.{2,}\s*\d+',  # Dots followed by number
                    r'\t\d+',  # Tab followed by number
                ]
                
                page_number_count = 0
                for page_pattern in page_number_patterns:
                    page_number_count += len(re.findall(page_pattern, content, re.MULTILINE))
                
                if page_number_count >= 3:  # At least 3 entries
                    return True
        
        return False
    
    def _continues_on_next_page(self, content: str) -> bool:
        """Check if TOC continues on next page."""
        lines = content.strip().split('\n')
        if lines:
            last_line = lines[-1].lower()
            return 'continued' in last_line or 'cont.' in last_line
        return False
    
    def _is_toc_continuation(self, content: str) -> bool:
        """Check if page is a continuation of TOC."""
        # Look for similar patterns without TOC header
        page_number_count = len(re.findall(r'\b\d+\s*$', content, re.MULTILINE))
        return page_number_count >= 3
    
    def _detect_format(self, content: str) -> TOCFormat:
        """Detect the TOC format type."""
        lines = content.split('\n')
        
        # Count occurrences of different patterns
        format_scores = {format_type: 0 for format_type in TOCFormat}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for dot leaders
            if re.search(r'\.{2,}', line):
                format_scores[TOCFormat.DOT_LEADER] += 1
            
            # Check for tabs
            if '\t' in line:
                format_scores[TOCFormat.TAB_SEPARATED] += 1
            
            # Check for numbered sections
            if re.match(r'^\d+(?:\.\d+)*\s+', line):
                format_scores[TOCFormat.NUMBERED] += 1
        
        # Choose format with highest score
        if max(format_scores.values()) > 0:
            return max(format_scores.items(), key=lambda x: x[1])[0]
        
        return TOCFormat.UNKNOWN
    
    def _parse_entries(self, content: str, format_type: TOCFormat) -> List[TOCEntry]:
        """Parse individual TOC entries."""
        entries = []
        lines = content.split('\n')
        
        patterns = self.entry_patterns.get(format_type, [])
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            entry = None
            
            # Try format-specific patterns
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    entry = self._create_entry_from_match(match, line, format_type)
                    break
            
            # Fallback to generic parsing
            if not entry and format_type == TOCFormat.UNKNOWN:
                entry = self._parse_generic_entry(line)
            
            if entry:
                entries.append(entry)
                self.logger.debug(f"Parsed TOC entry: {entry.title} -> page {entry.page}")
        
        return entries
    
    def _create_entry_from_match(self, match: re.Match, raw_text: str, 
                                format_type: TOCFormat) -> Optional[TOCEntry]:
        """Create TOC entry from regex match."""
        groups = match.groups()
        
        if format_type == TOCFormat.DOT_LEADER:
            if len(groups) == 3:
                number = groups[0] or ""
                title = groups[1].strip()
                page = int(groups[2])
            else:
                title = groups[0].strip()
                page = int(groups[1])
                number = ""
        
        elif format_type == TOCFormat.TAB_SEPARATED:
            if len(groups) == 3:
                number = groups[0] or ""
                title = groups[1].strip()
                page = int(groups[2])
            else:
                title = groups[0].strip()
                page = int(groups[1])
                number = ""
        
        elif format_type == TOCFormat.NUMBERED:
            number = groups[0]
            title = groups[1].strip()
            page = int(groups[2])
        
        else:
            return None
        
        # Calculate level based on number
        level = 1
        if number:
            level = number.count('.') + 1
        
        return TOCEntry(
            number=number,
            title=title,
            page=page,
            level=level,
            raw_text=raw_text
        )
    
    def _parse_generic_entry(self, line: str) -> Optional[TOCEntry]:
        """Parse entry with generic patterns."""
        # Try to find page number at end
        page_match = re.search(r'\b(\d+)\s*$', line)
        if page_match:
            page = int(page_match.group(1))
            title = line[:page_match.start()].strip()
            
            # Check for section number
            number_match = re.match(r'^([\d.]+)\s+', title)
            if number_match:
                number = number_match.group(1)
                title = title[number_match.end():].strip()
                level = number.count('.') + 1
            else:
                number = ""
                level = 1
            
            return TOCEntry(
                number=number,
                title=title,
                page=page,
                level=level,
                raw_text=line
            )
        
        return None
    
    def _build_hierarchy(self, entries: List[TOCEntry]) -> List[TOCEntry]:
        """Build hierarchical structure from flat entries."""
        root_entries = []
        stack = []  # Stack of (level, entry) tuples
        
        for entry in entries:
            # Find appropriate parent
            while stack and stack[-1][0] >= entry.level:
                stack.pop()
            
            if stack:
                # Add as child to last item in stack
                parent = stack[-1][1]
                parent.add_child(entry)
            else:
                # Top-level entry
                root_entries.append(entry)
            
            # Add to stack
            stack.append((entry.level, entry))
        
        return root_entries
    
    def create_blueprint(self, toc: TOCStructure, pages: Dict[int, str]) -> Dict[str, Any]:
        """Create a document blueprint from TOC structure.
        
        Returns:
            Blueprint with page mapping and section hierarchy
        """
        blueprint = {
            "toc_structure": toc,
            "page_mapping": {},
            "section_tree": {},
            "orphan_pages": []
        }
        
        # Create page mapping
        flat_entries = toc.get_flat_entries()
        
        for entry in flat_entries:
            blueprint["page_mapping"][entry.page] = {
                "section": entry.number or entry.title,
                "title": entry.title,
                "level": entry.level,
                "path": entry.get_full_path()
            }
        
        # Find orphan pages (not in TOC)
        toc_pages = set(entry.page for entry in flat_entries)
        all_pages = set(pages.keys())
        blueprint["orphan_pages"] = sorted(all_pages - toc_pages)
        
        # Create section tree
        def build_tree(entries: List[TOCEntry]) -> Dict[str, Any]:
            tree = {}
            for entry in entries:
                tree[entry.title] = {
                    "number": entry.number,
                    "page": entry.page,
                    "level": entry.level,
                    "children": build_tree(entry.children) if entry.children else {}
                }
            return tree
        
        blueprint["section_tree"] = build_tree(toc.root_entries)
        
        return blueprint