"""Base processor classes for semantic document understanding."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging

from pdf_manipulator.utils.logging_config import get_logger


class BaseProcessor(ABC):
    """Abstract base class for all processors."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize base processor.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or get_logger(self.__class__.__name__)
    
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """Process input and return results.
        
        Must be implemented by subclasses.
        """
        pass
    
    def validate_input(self, *args, **kwargs) -> bool:
        """Validate input parameters.
        
        Can be overridden by subclasses for specific validation.
        """
        return True
    
    def prepare_output(self, result: Any) -> Any:
        """Prepare output for return.
        
        Can be overridden by subclasses for specific formatting.
        """
        return result


class SemanticProcessor(BaseProcessor):
    """Base class for semantic understanding processors."""
    
    @abstractmethod
    def extract_semantics(self, content: str) -> Dict[str, Any]:
        """Extract semantic information from content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing semantic information
        """
        pass
    
    @abstractmethod
    def build_relationships(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build relationships between semantic nodes.
        
        Args:
            nodes: List of semantic nodes
            
        Returns:
            List of relationships
        """
        pass


class ContentProcessor(BaseProcessor):
    """Base class for content extraction processors."""
    
    @abstractmethod
    def extract_text(self, source: Union[str, Path]) -> str:
        """Extract text from source.
        
        Args:
            source: Source file or path
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    def enhance_content(self, text: str) -> str:
        """Enhance extracted content.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Enhanced text content
        """
        pass


class StructureProcessor(BaseProcessor):
    """Base class for document structure processors."""
    
    @abstractmethod
    def analyze_structure(self, content: Union[str, Dict[int, str]]) -> Dict[str, Any]:
        """Analyze document structure.
        
        Args:
            content: Document content (text or page dict)
            
        Returns:
            Structure analysis results
        """
        pass
    
    @abstractmethod
    def extract_hierarchy(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract hierarchical structure.
        
        Args:
            structure: Raw structure data
            
        Returns:
            Hierarchical structure representation
        """
        pass


class GraphProcessor(BaseProcessor):
    """Base class for knowledge graph processors."""
    
    @abstractmethod
    def create_node(self, content: str, metadata: Dict[str, Any]) -> str:
        """Create a graph node.
        
        Args:
            content: Node content
            metadata: Node metadata
            
        Returns:
            Node ID
        """
        pass
    
    @abstractmethod
    def create_edge(self, source_id: str, target_id: str, 
                   relationship: str, strength: float = 1.0) -> str:
        """Create a graph edge.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship: Relationship type
            strength: Relationship strength
            
        Returns:
            Edge ID
        """
        pass
    
    @abstractmethod
    def query_graph(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Query the knowledge graph.
        
        Args:
            query: Search query
            **kwargs: Additional query parameters
            
        Returns:
            Query results
        """
        pass