#!/usr/bin/env python3
"""Quick test script for markitdown integration."""

import sys
from pathlib import Path
from markitdown import MarkItDown

def test_markitdown():
    """Test if markitdown is installed and working."""
    try:
        # Create a markitdown instance
        converter = MarkItDown()
        print("✓ markitdown is installed successfully")
        return True
    except ImportError as e:
        print(f"✗ markitdown import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error initializing markitdown: {e}")
        return False

def test_conversion(file_path):
    """Test file conversion."""
    try:
        converter = MarkItDown()
        result = converter.convert(file_path)
        
        print(f"\n✓ Conversion successful for: {file_path}")
        print(f"Content length: {len(result.text_content)} characters")
        print("\nFirst 500 characters:")
        print("-" * 40)
        print(result.text_content[:500])
        print("-" * 40)
        return True
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing markitdown integration...\n")
    
    # Test 1: Check installation
    if not test_markitdown():
        sys.exit(1)
    
    # Test 2: Try to convert a file if provided
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        if Path(test_file).exists():
            test_conversion(test_file)
        else:
            print(f"File not found: {test_file}")
    else:
        print("\nTo test conversion, run: python test_markitdown.py <file_path>")
    
    print("\nmarkitdown integration test complete!")