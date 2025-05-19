#!/usr/bin/env python3
"""Direct test of TOC processor without imports."""
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Copy the essential parts for testing
class TOCFormat(Enum):
    """Supported TOC formats."""
    DOT_LEADER = "dot_leader"
    TAB_SEPARATED = "tab_separated"  
    NUMBERED = "numbered"
    INDENTED = "indented"
    UNKNOWN = "unknown"


@dataclass
class TOCEntry:
    """Represents a single table of contents entry."""
    number: str
    title: str
    page: int
    level: int
    raw_text: str
    children: List['TOCEntry'] = field(default_factory=list)
    parent: Optional['TOCEntry'] = None


# Test TOC detection function
def test_toc_detection():
    """Test TOC pattern detection."""
    print("Testing TOC Detection Patterns")
    print("=" * 50)
    
    toc_indicators = [
        r'table\s+of\s+contents',
        r'contents',
        r'toc',
    ]
    
    test_pages = [
        ("TABLE OF CONTENTS\n1. Intro ... 5\n2. Methods ... 10", True),
        ("Contents\n\nChapter 1 ... 5", True),
        ("Regular page content with no TOC", False),
        ("This page mentions contents but isn't a TOC", False),
    ]
    
    for content, expected in test_pages:
        lower_content = content.lower()
        found = False
        
        for pattern in toc_indicators:
            if re.search(pattern, lower_content, re.IGNORECASE):
                # Additional validation: page numbers
                page_count = len(re.findall(r'\b\d+\s*$', content, re.MULTILINE))
                if page_count >= 2:  # At least 2 entries
                    found = True
                    break
        
        result = "✓" if found == expected else "✗"
        print(f"{result} Expected {expected}, got {found}: '{content[:30]}...'")


def test_entry_patterns():
    """Test TOC entry parsing patterns."""
    print("\n\nTesting Entry Patterns")
    print("=" * 50)
    
    patterns = {
        "Dot Leader": [
            r'^([\d.]+)?\s*(.+?)\s*\.{2,}\s*(\d+)$',
            r'^(Chapter\s+\d+:?)\s*(.+?)\s*\.{2,}\s*(\d+)$',
        ],
        "Numbered": [
            r'^([\d.]+)\s+(.+?)\s+(\d+)$',
        ],
        "Tab": [
            r'^(.+?)\t(\d+)$',
        ]
    }
    
    test_entries = [
        ("1. Introduction ........................... 5", "Dot Leader"),
        ("Chapter 1: Getting Started ................ 10", "Dot Leader"),
        ("2.3.1 Deep Section ....................... 123", "Dot Leader"),
        ("1. Introduction  5", "Numbered"),
        ("Introduction\t5", "Tab"),
    ]
    
    for entry, expected_type in test_entries:
        print(f"\nTesting: '{entry}'")
        matched = False
        
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.match(pattern, entry)
                if match:
                    print(f"  ✓ Matched with {pattern_type}")
                    print(f"    Groups: {match.groups()}")
                    matched = True
                    break
            if matched:
                break
        
        if not matched:
            print(f"  ✗ No pattern matched")


def test_hierarchy_building():
    """Test building hierarchical structure."""
    print("\n\nTesting Hierarchy Building")
    print("=" * 50)
    
    # Create sample entries
    entries = [
        TOCEntry("1", "Introduction", 5, 1, "1. Introduction ... 5"),
        TOCEntry("2", "Background", 8, 1, "2. Background ... 8"),
        TOCEntry("2.1", "History", 10, 2, "2.1 History ... 10"),
        TOCEntry("2.2", "Current State", 15, 2, "2.2 Current State ... 15"),
        TOCEntry("3", "Methods", 20, 1, "3. Methods ... 20"),
    ]
    
    # Build hierarchy
    root_entries = []
    stack = []
    
    for entry in entries:
        # Find appropriate parent
        while stack and stack[-1][0] >= entry.level:
            stack.pop()
        
        if stack:
            parent = stack[-1][1]
            parent.children.append(entry)
            entry.parent = parent
        else:
            root_entries.append(entry)
        
        stack.append((entry.level, entry))
    
    # Display hierarchy
    print("Built hierarchy:")
    for root in root_entries:
        print(f"{root.number}. {root.title} (page {root.page})")
        for child in root.children:
            print(f"  {child.number} {child.title} (page {child.page})")


if __name__ == "__main__":
    test_toc_detection()
    test_entry_patterns()  
    test_hierarchy_building()