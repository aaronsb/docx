"""Enhanced knowledge graph builder with ontological tagging and edge scoring."""
import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from enum import Enum
import logging
import math


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""
    DOCUMENT = "document"
    SECTION = "section"
    PAGE = "page"
    CONCEPT = "concept"
    ENTITY = "entity"
    SUMMARY = "summary"
    METADATA = "metadata"


class EdgeType(Enum):
    """Types of edges in the knowledge graph."""
    PART_OF = "part_of"
    PRECEDES = "precedes"
    REFERENCES = "references"
    RELATES_TO = "relates_to"
    CONTAINS = "contains"
    SUMMARIZES = "summarizes"
    DERIVED_FROM = "derived_from"
    SIMILAR_TO = "similar_to"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    DEFINES = "defines"
    EXAMPLE_OF = "example_of"


@dataclass
class OntologyTag:
    """Represents an ontological classification."""
    category: str
    confidence: float
    domain: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    """Represents a node in the knowledge graph."""
    id: str
    type: NodeType
    content: Dict[str, Any]
    ontology_tags: List[OntologyTag] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "ontology_tags": [
                {
                    "category": tag.category,
                    "confidence": tag.confidence,
                    "domain": tag.domain,
                    "attributes": tag.attributes
                }
                for tag in self.ontology_tags
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confidence": self.confidence
        }


@dataclass
class Edge:
    """Represents an edge in the knowledge graph."""
    id: str
    source_id: str
    target_id: str
    type: EdgeType
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value,
            "weight": self.weight,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "evidence": self.evidence
        }


class EdgeScorer:
    """Manages dynamic edge scoring with recency factors."""
    
    def __init__(self, decay_rate: float = 0.1):
        """Initialize edge scorer.
        
        Args:
            decay_rate: Rate at which old edges decay (0-1)
        """
        self.decay_rate = decay_rate
        self.edge_timestamps: Dict[str, datetime] = {}
    
    def calculate_score(self, 
                       lexical_similarity: float,
                       semantic_strength: float,
                       edge_id: str) -> float:
        """Calculate final edge score with recency factor.
        
        Formula: final_score = lexical_base * semantic_multiplier * recency_factor
        """
        # Get recency factor
        recency = self._calculate_recency_factor(edge_id)
        
        # Semantic multiplier (gives higher weight to semantic connections)
        semantic_multiplier = 1.0 + semantic_strength
        
        # Calculate final score
        final_score = lexical_similarity * semantic_multiplier * recency
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def update_edge_timestamp(self, edge_id: str):
        """Update timestamp for edge recency calculation."""
        self.edge_timestamps[edge_id] = datetime.now()
    
    def decay_old_edges(self, edges: List[Edge]) -> List[Edge]:
        """Apply decay to old edges based on recency."""
        current_time = datetime.now()
        
        for edge in edges:
            if edge.id in self.edge_timestamps:
                time_diff = (current_time - self.edge_timestamps[edge.id]).total_seconds()
                decay_factor = math.exp(-self.decay_rate * time_diff / 3600)  # Hourly decay
                edge.weight *= decay_factor
        
        return edges
    
    def _calculate_recency_factor(self, edge_id: str) -> float:
        """Calculate recency factor for edge."""
        if edge_id not in self.edge_timestamps:
            return 1.0  # New edge gets full weight
        
        current_time = datetime.now()
        time_diff = (current_time - self.edge_timestamps[edge_id]).total_seconds()
        
        # Exponential decay based on time
        recency_factor = math.exp(-self.decay_rate * time_diff / 3600)  # Hourly decay
        
        return recency_factor


class GraphBuilder:
    """Enhanced graph builder with ontological tagging and dynamic scoring."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the graph builder."""
        self.logger = logger or logging.getLogger(__name__)
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.edge_scorer = EdgeScorer()
        
        # Ontology configuration
        self.ontology_domains = {
            "technical": ["algorithm", "data_structure", "system", "protocol"],
            "business": ["process", "strategy", "metric", "organization"],
            "academic": ["theory", "methodology", "research", "hypothesis"],
            "general": ["concept", "definition", "example", "summary"]
        }
    
    def create_node(self, 
                   content: Dict[str, Any],
                   node_type: NodeType,
                   ontology_tags: Optional[List[str]] = None,
                   confidence: float = 1.0) -> Node:
        """Create a node with ontological tagging."""
        node_id = str(uuid.uuid4())
        
        # Process ontology tags
        tags = []
        if ontology_tags:
            for tag_name in ontology_tags:
                # Determine domain
                domain = self._determine_domain(tag_name)
                
                tag = OntologyTag(
                    category=tag_name,
                    confidence=confidence,
                    domain=domain
                )
                tags.append(tag)
        
        # Create node
        node = Node(
            id=node_id,
            type=node_type,
            content=content,
            ontology_tags=tags,
            confidence=confidence
        )
        
        # Add to graph
        self.nodes[node_id] = node
        self.logger.debug(f"Created node {node_id} of type {node_type.value}")
        
        return node
    
    def create_edge(self,
                   source: Node,
                   target: Node,
                   edge_type: EdgeType,
                   confidence: float = 1.0,
                   semantic_strength: float = 0.0,
                   evidence: Optional[List[str]] = None) -> Edge:
        """Create weighted edge between nodes."""
        edge_id = str(uuid.uuid4())
        
        # Calculate initial weight
        lexical_similarity = self._calculate_lexical_similarity(source, target)
        weight = self.edge_scorer.calculate_score(
            lexical_similarity,
            semantic_strength,
            edge_id
        )
        
        # Create edge
        edge = Edge(
            id=edge_id,
            source_id=source.id,
            target_id=target.id,
            type=edge_type,
            weight=weight,
            confidence=confidence,
            evidence=evidence or []
        )
        
        # Update timestamp for recency tracking
        self.edge_scorer.update_edge_timestamp(edge_id)
        
        # Add to graph
        self.edges[edge_id] = edge
        self.logger.debug(f"Created edge {edge_id} from {source.id} to {target.id}")
        
        return edge
    
    def update_scores(self, edge: Edge, new_confidence: float, 
                     semantic_boost: float = 0.0):
        """Dynamically update edge confidence scores."""
        # Update confidence
        edge.confidence = new_confidence
        edge.updated_at = datetime.now()
        
        # Recalculate weight with semantic boost
        lexical_similarity = self._calculate_lexical_similarity(
            self.nodes[edge.source_id],
            self.nodes[edge.target_id]
        )
        
        edge.weight = self.edge_scorer.calculate_score(
            lexical_similarity,
            semantic_boost,
            edge.id
        )
        
        # Update timestamp
        self.edge_scorer.update_edge_timestamp(edge.id)
    
    def apply_ontological_inference(self, node: Node) -> List[OntologyTag]:
        """Apply ontological inference to derive additional tags."""
        inferred_tags = []
        
        # Check existing tags for inference rules
        for tag in node.ontology_tags:
            # Example inference rules
            if tag.category == "algorithm" and tag.confidence > 0.8:
                inferred_tags.append(OntologyTag(
                    category="computational",
                    confidence=tag.confidence * 0.9,
                    domain="technical"
                ))
            
            if tag.category == "hypothesis" and tag.confidence > 0.7:
                inferred_tags.append(OntologyTag(
                    category="research_question",
                    confidence=tag.confidence * 0.8,
                    domain="academic"
                ))
        
        # Add inferred tags to node
        node.ontology_tags.extend(inferred_tags)
        
        return inferred_tags
    
    def build_subgraph(self, root_node_id: str, 
                      max_depth: int = 3) -> Dict[str, Any]:
        """Build a subgraph starting from a root node."""
        subgraph = {
            "nodes": {},
            "edges": {}
        }
        
        visited = set()
        queue = [(root_node_id, 0)]
        
        while queue:
            node_id, depth = queue.pop(0)
            
            if node_id in visited or depth > max_depth:
                continue
            
            visited.add(node_id)
            
            # Add node to subgraph
            if node_id in self.nodes:
                subgraph["nodes"][node_id] = self.nodes[node_id].to_dict()
            
            # Find connected edges
            for edge_id, edge in self.edges.items():
                if edge.source_id == node_id:
                    subgraph["edges"][edge_id] = edge.to_dict()
                    if edge.target_id not in visited:
                        queue.append((edge.target_id, depth + 1))
                elif edge.target_id == node_id:
                    subgraph["edges"][edge_id] = edge.to_dict()
                    if edge.source_id not in visited:
                        queue.append((edge.source_id, depth + 1))
        
        return subgraph
    
    def export_graph(self) -> Dict[str, Any]:
        """Export the entire graph as JSON-compatible structure."""
        # Apply decay to old edges
        edge_list = list(self.edges.values())
        self.edge_scorer.decay_old_edges(edge_list)
        
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": {edge_id: edge.to_dict() for edge_id, edge in self.edges.items()},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": self._get_node_type_stats(),
                "edge_types": self._get_edge_type_stats(),
                "ontology_coverage": self._calculate_ontology_coverage()
            }
        }
    
    def _determine_domain(self, tag_name: str) -> Optional[str]:
        """Determine the domain for an ontology tag."""
        for domain, keywords in self.ontology_domains.items():
            if any(keyword in tag_name.lower() for keyword in keywords):
                return domain
        return "general"
    
    def _calculate_lexical_similarity(self, source: Node, target: Node) -> float:
        """Calculate lexical similarity between nodes."""
        # Simple implementation - can be enhanced
        source_text = str(source.content.get("text", "")).lower()
        target_text = str(target.content.get("text", "")).lower()
        
        if not source_text or not target_text:
            return 0.0
        
        # Word overlap similarity
        source_words = set(source_text.split())
        target_words = set(target_text.split())
        
        intersection = source_words.intersection(target_words)
        union = source_words.union(target_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _get_node_type_stats(self) -> Dict[str, int]:
        """Get statistics on node types."""
        stats = {}
        for node in self.nodes.values():
            node_type = node.type.value
            stats[node_type] = stats.get(node_type, 0) + 1
        return stats
    
    def _get_edge_type_stats(self) -> Dict[str, int]:
        """Get statistics on edge types."""
        stats = {}
        for edge in self.edges.values():
            edge_type = edge.type.value
            stats[edge_type] = stats.get(edge_type, 0) + 1
        return stats
    
    def _calculate_ontology_coverage(self) -> float:
        """Calculate the percentage of nodes with ontology tags."""
        tagged_nodes = sum(1 for node in self.nodes.values() if node.ontology_tags)
        total_nodes = len(self.nodes)
        
        if total_nodes == 0:
            return 0.0
        
        return tagged_nodes / total_nodes