#!/usr/bin/env python3
"""Simple test for TOC processor without PDF dependencies."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_manipulator.memory.toc_processor import TOCProcessor, TOCFormat


def test_toc_processor():
    """Test TOC processor with sample content."""
    print("Testing TOC Processor")
    print("=" * 50)
    
    # Sample pages with different TOC formats
    test_cases = [
        {
            "name": "Dot Leader Format",
            "pages": {
                0: """
                TABLE OF CONTENTS
                
                1. Introduction ........................... 5
                2. Background ............................ 8
                   2.1 Historical Context ................. 10
                   2.2 Current State ..................... 15
                3. Methodology ........................... 20
                   3.1 Data Collection ................... 22
                   3.2 Analysis Methods .................. 28
                4. Results .............................. 35
                """,
                1: "Regular content page",
            }
        },
        {
            "name": "Numbered Format",
            "pages": {
                0: """
                Contents
                
                1. Introduction  5
                2. Background  8
                2.1 Historical Context  10
                2.2 Current State  15
                3. Methodology  20
                3.1 Data Collection  22
                """,
                1: "Regular content page",
            }
        },
        {
            "name": "Chapter Format",
            "pages": {
                0: """
                Table of Contents
                
                Chapter 1: Introduction ................ 5
                Chapter 2: Background ................. 12
                Chapter 3: Methods .................... 23
                Chapter 4: Results .................... 45
                """,
                1: "Regular content page",
            }
        }
    ]
    
    toc_processor = TOCProcessor()
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print("-" * 30)
        
        # Detect TOC
        result = toc_processor.detect_toc(test_case['pages'])
        
        if result:
            toc_pages, toc_content = result
            print(f"✓ TOC detected on pages: {toc_pages}")
            
            # Parse TOC
            toc_structure = toc_processor.parse_toc(toc_content, toc_pages)
            
            if toc_structure:
                print(f"✓ Format: {toc_structure.format.value}")
                print(f"✓ Entries: {len(toc_structure.entries)}")
                
                # Display entries
                for entry in toc_structure.root_entries:
                    print(f"  {entry.number or '•'} {entry.title} -> page {entry.page}")
                    for child in entry.children:
                        print(f"    {child.number} {child.title} -> page {child.page}")
            else:
                print("✗ Failed to parse TOC structure")
        else:
            print("✗ No TOC detected")


def test_format_detection():
    """Test TOC format detection."""
    print("\n\nTesting Format Detection")
    print("=" * 50)
    
    toc_processor = TOCProcessor()
    
    test_formats = {
        "Dot Leader": """
        1. Introduction ........................... 5
        2. Background ............................ 8
        """,
        "Tab Separated": "1. Introduction\t5\n2. Background\t8",
        "Numbered": """
        1. Introduction  5
        2. Background  8
        2.1 Sub-section  10
        """,
    }
    
    for name, content in test_formats.items():
        print(f"\nTesting {name} format:")
        detected = toc_processor._detect_format(content)
        print(f"  Detected: {detected.value}")


def test_entry_parsing():
    """Test individual entry parsing."""
    print("\n\nTesting Entry Parsing")
    print("=" * 50)
    
    toc_processor = TOCProcessor()
    
    # Test individual lines
    test_lines = [
        ("1. Introduction ........................... 5", TOCFormat.DOT_LEADER),
        ("Chapter 1: Getting Started ................ 10", TOCFormat.DOT_LEADER),
        ("2.3.1 Deep Subsection .................... 123", TOCFormat.DOT_LEADER),
        ("1. Introduction  5", TOCFormat.NUMBERED),
        ("Introduction\t5", TOCFormat.TAB_SEPARATED),
    ]
    
    for line, format_type in test_lines:
        print(f"\nParsing: '{line}' as {format_type.value}")
        entries = toc_processor._parse_entries(line, format_type)
        
        if entries:
            entry = entries[0]
            print(f"  ✓ Title: {entry.title}")
            print(f"  ✓ Page: {entry.page}")
            print(f"  ✓ Number: {entry.number}")
            print(f"  ✓ Level: {entry.level}")
        else:
            print("  ✗ Failed to parse")


if __name__ == "__main__":
    test_toc_processor()
    test_format_detection()
    test_entry_parsing()