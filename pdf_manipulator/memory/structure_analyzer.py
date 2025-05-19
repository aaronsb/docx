"""Document structure analyzer for semantic understanding.

This module analyzes document structure, including table of contents,
sections, hierarchies, and logical organization.
"""
from pdf_manipulator.memory.toc_processor import TOCProcessor

# Create alias with new semantic name
class StructureAnalyzer(TOCProcessor):
    """Analyzes document structure for semantic understanding.
    
    This processor:
    - Detects table of contents
    - Identifies document sections
    - Maps hierarchical relationships
    - Extracts structural metadata
    - Provides blueprint for semantic extraction
    """
    pass  # Inherits all functionality from TOCProcessor