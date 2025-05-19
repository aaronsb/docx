"""Main orchestrator for semantic document processing.

This module provides the high-level orchestration of the semantic extraction pipeline.
"""
from pdf_manipulator.core.pipeline import DocumentProcessor

# Create alias with new semantic name
class SemanticOrchestrator(DocumentProcessor):
    """Orchestrates the semantic extraction pipeline.
    
    This is the main coordinator that manages:
    - Document rendering (if needed)
    - Content extraction
    - Semantic analysis
    - Knowledge graph construction
    - Memory storage
    """
    pass  # Inherits all functionality from DocumentProcessor