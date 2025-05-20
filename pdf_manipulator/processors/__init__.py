"""Semantic processing components for Memory Graph Extract."""

# Import renamed processors for easier access
from pdf_manipulator.core.pipeline import DocumentProcessor as SemanticOrchestrator
from pdf_manipulator.intelligence.processor import DocumentProcessor as ContentExtractor
from pdf_manipulator.memory.memory_processor import MemoryProcessor as GraphBuilder
from pdf_manipulator.memory.toc_processor import TOCProcessor as StructureAnalyzer

__all__ = [
    'SemanticOrchestrator',
    'ContentExtractor',
    'GraphBuilder',
    'StructureAnalyzer'
]