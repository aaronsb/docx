"""Knowledge graph builder for semantic document understanding.

This module constructs semantic knowledge graphs from document content,
creating nodes, relationships, and queryable structures.
"""
from pdf_manipulator.memory.memory_processor import MemoryProcessor

# Create alias with new semantic name
class GraphBuilder(MemoryProcessor):
    """Builds semantic knowledge graphs from documents.
    
    This processor:
    - Creates semantic nodes from document elements
    - Establishes relationships between content
    - Manages graph storage and queries
    - Generates summaries for searchability
    - Handles cross-document connections
    """
    pass  # Inherits all functionality from MemoryProcessor