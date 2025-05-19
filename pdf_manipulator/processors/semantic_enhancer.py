"""Semantic enhancer for LLM-based understanding and graph enrichment."""
import base64
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import logging
from pathlib import Path

from ..intelligence.base import IntelligenceBackend
from ..memory.graph_builder import Node, Edge, NodeType, EdgeType
from .structure_analyzer import TOCStructure


@dataclass
class Context:
    """Context for LLM processing."""
    toc_structure: str
    current_page: str
    page_image: Optional[str] = None
    page_number: int = 0
    total_pages: int = 0
    previous_summaries: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "toc_structure": self.toc_structure,
            "current_page": self.current_page,
            "page_image": self.page_image,
            "page_number": self.page_number,
            "total_pages": self.total_pages,
            "previous_summaries": self.previous_summaries or []
        }


@dataclass
class Summary:
    """Enhanced summary with semantic understanding."""
    text: str
    key_concepts: List[str]
    relationships: List[Tuple[str, str, str]]  # (source, relation, target)
    ontology_tags: List[str]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "key_concepts": self.key_concepts,
            "relationships": [
                {"source": r[0], "relation": r[1], "target": r[2]} 
                for r in self.relationships
            ],
            "ontology_tags": self.ontology_tags,
            "confidence": self.confidence
        }


class SemanticEnhancer:
    """LLM-based semantic understanding enhancement."""
    
    def __init__(self, backend: IntelligenceBackend, 
                 logger: Optional[logging.Logger] = None):
        """Initialize with configurable backend."""
        self.backend = backend
        self.logger = logger or logging.getLogger(__name__)
        self.context_window_size = 4096  # Default context size
        self.summary_cache: Dict[str, Summary] = {}
        
    def prepare_context(self, toc: TOCStructure, 
                       page_content: str,
                       page_image_path: Optional[str] = None,
                       page_number: int = 0,
                       total_pages: int = 0,
                       previous_summaries: Optional[List[str]] = None) -> Context:
        """Prepare context for LLM processing."""
        # Convert TOC to string representation
        toc_string = self._toc_to_string(toc)
        
        # Encode image if available and backend supports vision
        page_image = None
        if page_image_path and self.backend.supports_vision:
            page_image = self._encode_image(page_image_path)
        
        # Trim context to fit window
        context = Context(
            toc_structure=self._trim_to_window(toc_string, self.context_window_size // 4),
            current_page=self._trim_to_window(page_content, self.context_window_size // 2),
            page_image=page_image,
            page_number=page_number,
            total_pages=total_pages,
            previous_summaries=previous_summaries or []
        )
        
        return context
    
    def enhance_with_llm(self, context: Context) -> Summary:
        """Generate coherent understanding using LLM."""
        # Check cache first
        cache_key = f"{context.page_number}_{hash(context.current_page)}"
        if cache_key in self.summary_cache:
            return self.summary_cache[cache_key]
        
        # Build prompt
        prompt = self._build_prompt(context)
        
        # Process with backend
        response = self.backend.process(prompt, context.page_image)
        
        # Parse response into structured summary
        summary = self._parse_response(response)
        
        # Cache the result
        self.summary_cache[cache_key] = summary
        
        return summary
    
    def update_graph(self, graph: 'GraphBuilder', summary: Summary, 
                    node: Node, confidence: float = 1.0):
        """Update graph with enhanced understanding."""
        # Update node with semantic summary
        node.content["semantic_summary"] = summary.text
        node.content["key_concepts"] = summary.key_concepts
        
        # Add ontology tags
        for tag in summary.ontology_tags:
            graph.apply_ontological_inference(node)
        
        # Create high-confidence semantic edges
        for source, relation, target in summary.relationships:
            # Find or create target node
            target_node = self._find_or_create_node(graph, target, summary)
            
            # Map relation to edge type
            edge_type = self._map_relation_to_edge_type(relation)
            
            # Create semantic edge with high confidence
            edge = graph.create_edge(
                source=node,
                target=target_node,
                edge_type=edge_type,
                confidence=confidence,
                semantic_strength=1.0,  # High semantic weight
                evidence=[summary.text]
            )
            
            # Update edge scores with semantic boost
            graph.update_scores(edge, confidence, semantic_boost=1.0)
    
    def process_page_sequence(self, pages: List[Dict[str, Any]], 
                            toc: TOCStructure,
                            graph: 'GraphBuilder') -> List[Summary]:
        """Process a sequence of pages with context awareness."""
        summaries = []
        previous_summaries = []
        
        for i, page in enumerate(pages):
            # Prepare context with previous summaries
            context = self.prepare_context(
                toc=toc,
                page_content=page["content"],
                page_image_path=page.get("image_path"),
                page_number=i,
                total_pages=len(pages),
                previous_summaries=previous_summaries[-3:]  # Last 3 summaries
            )
            
            # Generate summary
            summary = self.enhance_with_llm(context)
            summaries.append(summary)
            
            # Create node for page
            page_node = graph.create_node(
                content={
                    "text": page["content"],
                    "page_number": i,
                    "semantic_summary": summary.text
                },
                node_type=NodeType.PAGE,
                ontology_tags=summary.ontology_tags,
                confidence=summary.confidence
            )
            
            # Update graph with semantic understanding
            self.update_graph(graph, summary, page_node)
            
            # Add to context for next pages
            previous_summaries.append(summary.text)
        
        return summaries
    
    def _build_prompt(self, context: Context) -> str:
        """Build prompt for LLM processing."""
        prompt = f"""You are analyzing a document page within the context of its structure. 
Your task is to generate a semantic understanding that captures the intended meaning and relationships.

Document Structure:
{context.toc_structure}

Current Page {context.page_number + 1} of {context.total_pages}:
{context.current_page}

Previous Context:
{chr(10).join(context.previous_summaries[-2:])}

Please provide:
1. A coherent summary that captures the semantic meaning (not just keywords)
2. Key concepts introduced or discussed
3. Relationships between concepts (format: source|relation|target)
4. Appropriate ontological tags for classification
5. Confidence score (0-1) for your understanding

Format your response as JSON:
{{
    "summary": "coherent semantic summary",
    "key_concepts": ["concept1", "concept2"],
    "relationships": [
        ["source", "relation", "target"]
    ],
    "ontology_tags": ["tag1", "tag2"],
    "confidence": 0.95
}}"""
        
        return prompt
    
    def _parse_response(self, response: str) -> Summary:
        """Parse LLM response into structured summary."""
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            return Summary(
                text=data.get("summary", ""),
                key_concepts=data.get("key_concepts", []),
                relationships=[tuple(r) for r in data.get("relationships", [])],
                ontology_tags=data.get("ontology_tags", []),
                confidence=data.get("confidence", 0.7)
            )
        except json.JSONDecodeError:
            # Fallback parsing for non-JSON responses
            self.logger.warning("Failed to parse JSON response, using fallback")
            
            return Summary(
                text=response,
                key_concepts=[],
                relationships=[],
                ontology_tags=[],
                confidence=0.5
            )
    
    def _toc_to_string(self, toc: TOCStructure) -> str:
        """Convert TOC structure to string representation."""
        lines = []
        
        def format_entry(entry, indent=0):
            prefix = "  " * indent
            lines.append(f"{prefix}{entry.number} {entry.title} (p.{entry.page})")
            for child in entry.children:
                format_entry(child, indent + 1)
        
        for root in toc.root_entries:
            format_entry(root)
        
        return "\n".join(lines)
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for vision models."""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            self.logger.warning(f"Failed to encode image: {e}")
            return ""
    
    def _trim_to_window(self, text: str, max_chars: int) -> str:
        """Trim text to fit within context window."""
        if len(text) <= max_chars:
            return text
        
        # Trim from the middle to preserve beginning and end
        half = max_chars // 2
        return text[:half] + "\n...[truncated]...\n" + text[-half:]
    
    def _find_or_create_node(self, graph: 'GraphBuilder', 
                           concept: str, summary: Summary) -> Node:
        """Find existing node or create new one for concept."""
        # Search existing nodes
        for node in graph.nodes.values():
            if concept.lower() in node.content.get("text", "").lower():
                return node
        
        # Create new concept node
        return graph.create_node(
            content={"text": concept, "derived_from": summary.text},
            node_type=NodeType.CONCEPT,
            ontology_tags=summary.ontology_tags,
            confidence=summary.confidence * 0.8  # Slightly lower confidence for derived
        )
    
    def _map_relation_to_edge_type(self, relation: str) -> EdgeType:
        """Map text relation to edge type."""
        relation_lower = relation.lower()
        
        mapping = {
            "contains": EdgeType.CONTAINS,
            "references": EdgeType.REFERENCES,
            "relates to": EdgeType.RELATES_TO,
            "part of": EdgeType.PART_OF,
            "similar to": EdgeType.SIMILAR_TO,
            "contradicts": EdgeType.CONTRADICTS,
            "supports": EdgeType.SUPPORTS,
            "defines": EdgeType.DEFINES,
            "example of": EdgeType.EXAMPLE_OF,
            "summarizes": EdgeType.SUMMARIZES,
            "precedes": EdgeType.PRECEDES,
            "follows": EdgeType.PRECEDES,  # Reverse direction
            "derived from": EdgeType.DERIVED_FROM
        }
        
        for key, edge_type in mapping.items():
            if key in relation_lower:
                return edge_type
        
        return EdgeType.RELATES_TO  # Default