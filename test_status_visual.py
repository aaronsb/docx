#!/usr/bin/env python3
"""Test to visually confirm status updates are working."""

import time
from pdf_manipulator.utils.progress import ProcessingProgress

def test_status_updates():
    """Test status updates with artificial delays."""
    progress = ProcessingProgress()
    progress.start()
    
    # Test rendering
    print("\nTesting rendering progress...")
    progress.start_stage("rendering", total=5)
    
    for i in range(5):
        time.sleep(1)  # Artificial delay to see updates
        progress.update_stage("rendering", advance=1)
        progress.update_page_status(i + 1)
    
    progress.complete_stage("rendering")
    
    # Test transcription
    print("\nTesting transcription progress...")
    progress.start_stage("transcription", total=5)
    
    for i in range(5):
        time.sleep(1)  # Artificial delay to see updates
        progress.update_stage("transcription", advance=1)
        progress.update_page_status(i + 1)
    
    progress.complete_stage("transcription")
    
    progress.stop()
    print("\nTest complete!")

if __name__ == "__main__":
    test_status_updates()