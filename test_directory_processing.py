#!/usr/bin/env python3
"""
Test script for directory processing functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import subprocess

def setup_test_directory():
    """Create a test directory structure with PDF files"""
    test_dir = Path(tempfile.mkdtemp(prefix="pdf_test_"))
    
    # Create subdirectories
    subdir1 = test_dir / "documents"
    subdir2 = test_dir / "reports" / "2024"
    
    os.makedirs(subdir1, exist_ok=True)
    os.makedirs(subdir2, exist_ok=True)
    
    # Copy a test PDF to multiple locations (if available)
    test_pdf = None
    for pdf_path in Path.cwd().rglob("*.pdf"):
        if pdf_path.stat().st_size < 10 * 1024 * 1024:  # Under 10MB
            test_pdf = pdf_path
            break
    
    if test_pdf:
        # Copy to multiple locations with different names
        shutil.copy(test_pdf, subdir1 / "document1.pdf")
        shutil.copy(test_pdf, subdir1 / "document2.pdf")
        shutil.copy(test_pdf, subdir2 / "report.pdf")
        
        print(f"Created test directory structure in: {test_dir}")
        print(f"  - {subdir1}/document1.pdf")
        print(f"  - {subdir1}/document2.pdf")
        print(f"  - {subdir2}/report.pdf")
    else:
        print("No suitable test PDF found. Please place a PDF file in the project directory.")
        shutil.rmtree(test_dir)
        return None
    
    return test_dir

def test_directory_processing():
    """Test the directory processing functionality"""
    print("Testing directory processing feature...")
    
    # Setup test directory
    test_dir = setup_test_directory()
    if not test_dir:
        return
    
    try:
        output_dir = test_dir / "output"
        
        # Run the process command on the directory
        cmd = [
            "pdfx",
            "process",
            str(test_dir),
            str(output_dir),
            "--backend", "markitdown",
            "--direct",
            "--progress"
        ]
        
        print(f"\nRunning command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\nDirectory processing completed successfully!")
            print("\nOutput:")
            print(result.stdout)
            
            # Verify output structure
            print("\nVerifying output structure:")
            for path in output_dir.rglob("*"):
                if path.is_file():
                    print(f"  - {path.relative_to(output_dir)}")
        else:
            print(f"\nError: Command failed with return code {result.returncode}")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            
    finally:
        # Cleanup
        print(f"\nCleaning up test directory: {test_dir}")
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_directory_processing()