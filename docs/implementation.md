# Implementation Guide

This guide provides instructions for implementing, extending, and customizing Memory Graph Extract. It focuses on practical information for working with the codebase.

## Table of Contents

- [Core Architecture](#core-architecture)
- [Adding New Intelligence Backends](#adding-new-intelligence-backends)
- [Customizing the Semantic Pipeline](#customizing-the-semantic-pipeline)
- [Extending Memory Graph Capabilities](#extending-memory-graph-capabilities)
- [Implementation Best Practices](#implementation-best-practices)
- [Edge Scoring System](#edge-scoring-system)
- [Current Limitations](#current-limitations)
- [Next Development Steps](#next-development-steps)

## Core Architecture

The semantic pipeline is designed as a series of stages that transform PDF documents into semantic knowledge graphs. The core components interact as follows:

```
Document → SemanticOrchestrator → IntelligenceBackend → MemoryProcessor → Graph Database
             ↓                                              ↓
        ContentExtractor                             GraphBuilder
             ↓                                              ↓
        TOCProcessor                              StructureAnalyzer
```

### 1. Structure Discovery - `StructureAnalyzer`

**Path**: `pdf_manipulator/processors/structure_analyzer.py`

```python
class StructureAnalyzer:
    """Discovers and constructs document structure."""
    
    def extract_toc(self, pdf_path: str) -> Optional[TOC]:
        """Extract existing TOC from PDF."""
        pass
    
    def construct_toc(self, page_contents: List[str]) -> TOC:
        """Build TOC from page-level analysis."""
        pass
    
    def analyze_hierarchy(self, content: str) -> List[Section]:
        """Detect section headers and structure."""
        pass
```

### 2. Initial Analysis - `ContentAnalyzer`

**Path**: `pdf_manipulator/processors/content_analyzer.py`

```python
class ContentAnalyzer:
    """Performs initial content analysis without deep LLM."""
    
    def extract_word_stems(self, text: str) -> List[Stem]:
        """Extract word stems for indexing."""
        pass
    
    def bayesian_analysis(self, text: str, toc: TOC) -> Dict[str, float]:
        """Calculate term significance using Bayesian methods."""
        pass
    
    def detect_relationships(self, content: str) -> List[Relationship]:
        """Find basic relationships between concepts."""
        pass
```

### 3. Graph Builder - `GraphBuilder`

**Path**: `pdf_manipulator/memory/graph_builder.py`

```python
class GraphBuilder:
    """Constructs semantic knowledge graph."""
    
    def create_node(self, content: dict, ontology_tags: List[str]) -> Node:
        """Create node with ontological tagging."""
        pass
    
    def create_edge(self, source: Node, target: Node, 
                   confidence: float, relationship_type: str) -> Edge:
        """Create weighted edge between nodes."""
        pass
    
    def update_scores(self, edge: Edge, new_confidence: float):
        """Dynamically update edge confidence scores."""
        pass
```

### 4. Semantic Enhancement - `SemanticEnhancer`

**Path**: `pdf_manipulator/processors/semantic_enhancer.py`

```python
class SemanticEnhancer:
    """LLM-based semantic understanding enhancement."""
    
    def __init__(self, backend: IntelligenceBackend):
        """Initialize with configurable backend."""
        self.backend = backend  # Could be OpenAI, Ollama, etc.
    
    def prepare_context(self, toc: TOC, page: Page) -> Context:
        """Prepare context for LLM processing."""
        return {
            "toc_structure": toc.to_string(),
            "current_page": page.markdown,
            "page_image": page.image_base64 if self.backend.supports_vision else None
        }
    
    def enhance_with_llm(self, context: Context) -> Summary:
        """Generate coherent understanding using LLM."""
        prompt = self._build_prompt(context)
        return self.backend.process(prompt, context.get("page_image"))
    
    def update_graph(self, graph: Graph, summary: Summary, 
                    confidence: float = 1.0):
        """Update graph with enhanced understanding."""
        pass
```

### 5. Pipeline Orchestration - `SemanticOrchestrator`

**Path**: `pdf_manipulator/core/semantic_orchestrator.py`

This component coordinates the entire pipeline, managing:
- Document loading and preprocessing
- Sequencing of processing stages
- Context window management
- Parallel processing
- Result aggregation
- Error handling and recovery

## Adding New Intelligence Backends

The `IntelligenceBackend` abstract class serves as the foundation for all LLM backends in the pipeline. New backends can be added by implementing this interface.

### Backend Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IntelligenceBackend(ABC):
    """Abstract base class for intelligence backends."""
    
    @property
    def supports_vision(self) -> bool:
        """Whether this backend supports image processing."""
        return False
    
    @abstractmethod
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Process content with the intelligence backend.
        
        Args:
            text: Text prompt or content to process
            image: Optional base64-encoded image data
            
        Returns:
            Processed result as string
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model being used."""
        return {
            "name": "base",
            "supports_vision": self.supports_vision,
            "vendor": "generic"
        }
```

### Example: Implementing OpenAI Backend

```python
class OpenAIMultimodalBackend(IntelligenceBackend):
    """OpenAI API with vision support."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._supports_vision = model in ["gpt-4-vision-preview", "gpt-4-turbo"]
    
    @property
    def supports_vision(self) -> bool:
        return self._supports_vision
    
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Process with GPT-4 Vision."""
        messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
        if image and self.supports_vision:
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"}
            })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model,
            "supports_vision": self.supports_vision,
            "vendor": "openai",
            "max_tokens": 4096
        }
```

### Example: Implementing Ollama Backend

```python
class OllamaBackend(IntelligenceBackend):
    """Local Ollama endpoint."""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._supports_vision = model in ["llava", "bakllava"]
    
    @property
    def supports_vision(self) -> bool:
        return self._supports_vision
    
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Process with Ollama."""
        data = {"model": self.model, "prompt": text}
        if image and self.supports_vision:
            data["images"] = [image]
        
        response = requests.post(f"{self.base_url}/api/generate", json=data)
        return response.json()["response"]
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model,
            "supports_vision": self.supports_vision,
            "vendor": "ollama",
            "local": True
        }
```

### Backend Registration

Register new backends in the factory:

```python
# Add to pdf_manipulator/intelligence/base.py

def get_backend(backend_type: str, config: Dict[str, Any]) -> IntelligenceBackend:
    """Factory function to get intelligence backend."""
    if backend_type == "openai":
        from pdf_manipulator.intelligence.openai_multimodal import OpenAIMultimodalBackend
        return OpenAIMultimodalBackend(
            api_key=config.get("api_key"),
            model=config.get("model", "gpt-4-vision-preview")
        )
    elif backend_type == "ollama":
        from pdf_manipulator.intelligence.ollama_multimodal import OllamaBackend
        return OllamaBackend(
            model=config.get("model", "llava"),
            base_url=config.get("base_url", "http://localhost:11434")
        )
    elif backend_type == "http":
        from pdf_manipulator.intelligence.http_endpoint import HTTPEndpointBackend
        return HTTPEndpointBackend(
            endpoint_url=config.get("endpoint_url"),
            headers=config.get("headers", {})
        )
    elif backend_type == "custom_backend":
        # Add your custom backend here
        from your_module import CustomBackend
        return CustomBackend(**config)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
```

## Customizing the Semantic Pipeline

### Custom Configuration

Create a YAML configuration file to customize pipeline behavior:

```yaml
semantic_pipeline:
  # LLM Backend Configuration
  llm_backend:
    type: "openai"  # Options: openai, ollama, http, [your_custom_backend]
    config:
      # For OpenAI
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4-vision-preview"
      
      # For Ollama
      # base_url: "http://localhost:11434"
      # model: "llava"
      
      # For HTTP Endpoint
      # endpoint_url: "https://api.example.com/llm"
      # headers:
      #   Authorization: "Bearer ${API_TOKEN}"
  
  # Pipeline Configuration
  structure_discovery:
    prefer_native_toc: true
    fallback_to_markitdown: true
  
  initial_analysis:
    use_word_stems: true
    bayesian_threshold: 0.3
  
  semantic_enhancement:
    max_context_tokens: 4096
    confidence_threshold: 0.8
    
  # Output Configuration
  output:
    format: "both"  # Options: json, sqlite, both
    include_intermediate: false
  
  # Performance Configuration
  performance:
    parallel_pages: 4
    batch_size: 10
    cache_enabled: true
    cache_ttl: 3600
```

### Custom Prompt Templates

Create custom prompts for LLM processing by extending the `PromptTemplates` class:

```python
# pdf_manipulator/processors/prompt_templates.py

class PromptTemplates:
    """Provides customizable prompt templates for semantic processing."""
    
    def __init__(self, custom_templates: Dict[str, str] = None):
        self.templates = {
            "semantic_analysis": self.DEFAULT_SEMANTIC_ANALYSIS,
            "relationship_extraction": self.DEFAULT_RELATIONSHIP_EXTRACTION,
            "toc_construction": self.DEFAULT_TOC_CONSTRUCTION,
            # Add more default templates as needed
        }
        
        # Override with custom templates if provided
        if custom_templates:
            self.templates.update(custom_templates)
    
    @property
    def DEFAULT_SEMANTIC_ANALYSIS(self) -> str:
        return """
        Analyze the following page content and provide a semantic understanding.
        
        Document Structure:
        {toc_structure}
        
        Current Page Content:
        {current_page}
        
        Provide:
        1. A coherent summary of this page's content
        2. Key concepts mentioned
        3. Relationships to other sections
        4. Document role of this content
        """
    
    # Add more default templates
    
    def get_template(self, template_name: str) -> str:
        """Get a prompt template by name."""
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        return self.templates[template_name]
```

### Custom Pipeline Stages

Create custom pipeline stages by implementing the appropriate interfaces:

```python
# Example: Custom content analyzer
from pdf_manipulator.processors.content_analyzer import ContentAnalyzer

class CustomContentAnalyzer(ContentAnalyzer):
    """Custom content analysis implementation."""
    
    def __init__(self, additional_features: bool = False):
        super().__init__()
        self.additional_features = additional_features
    
    def detect_relationships(self, content: str) -> List[Relationship]:
        """Override with custom relationship detection logic."""
        # Your custom implementation here
        relationships = super().detect_relationships(content)
        
        if self.additional_features:
            # Add additional relationship detection
            pass
            
        return relationships
```

## Extending Memory Graph Capabilities

### Custom Ontology System

Create domain-specific ontologies to enrich graph classification:

```python
# pdf_manipulator/memory/ontology.py

class OntologySystem:
    """Manages ontological tagging for semantic graphs."""
    
    def __init__(self, domain: str = "general"):
        self.domain = domain
        self.ontology = self._load_ontology(domain)
    
    def _load_ontology(self, domain: str) -> Dict[str, Any]:
        """Load domain-specific ontology definitions."""
        # Load from config or embedded definitions
        if domain == "general":
            return self.DEFAULT_ONTOLOGY
        elif domain == "medical":
            return self.MEDICAL_ONTOLOGY
        # Add more domains as needed
        else:
            # Custom domain handling
            pass
    
    @property
    def DEFAULT_ONTOLOGY(self) -> Dict[str, Any]:
        return {
            "categories": [
                "concept", "entity", "process", "event", 
                "location", "temporal", "attribute"
            ],
            "relationships": {
                "contains": {"bidirectional": False, "inverse": "is_part_of"},
                "references": {"bidirectional": False, "inverse": "referenced_by"},
                "relates_to": {"bidirectional": True, "inverse": "relates_to"},
                "supports": {"bidirectional": False, "inverse": "supported_by"},
                "contradicts": {"bidirectional": True, "inverse": "contradicts"}
            }
        }
    
    def get_categories(self) -> List[str]:
        """Get all ontology categories for this domain."""
        return self.ontology.get("categories", [])
    
    def get_relationship_types(self) -> List[str]:
        """Get all relationship types for this domain."""
        return list(self.ontology.get("relationships", {}).keys())
    
    def classify_content(self, content: str) -> List[str]:
        """Classify content into ontological categories."""
        # Implement classification logic
        # This could use basic pattern matching or LLM-based classification
        pass
```

### Custom Relationship Types

Define custom relationship types with specific properties:

```python
# pdf_manipulator/memory/relationships.py

class RelationshipTypes:
    """Defines and manages relationship types in the semantic graph."""
    
    @staticmethod
    def get_all_types() -> Dict[str, Dict[str, Any]]:
        """Get all standard relationship types with their properties."""
        return {
            "contains": {
                "description": "Hierarchical containment relationship",
                "directional": True,
                "strength_decay": 0.0,  # Structural relationships don't decay
                "default_confidence": 1.0
            },
            "references": {
                "description": "Direct reference to another element",
                "directional": True,
                "strength_decay": 0.1,  # Slight decay over time
                "default_confidence": 0.9
            },
            "relates_to": {
                "description": "General semantic relationship",
                "directional": False,
                "strength_decay": 0.2,  # Moderate decay
                "default_confidence": 0.7
            },
            "supports": {
                "description": "Supporting evidence or argument",
                "directional": True,
                "strength_decay": 0.1,
                "default_confidence": 0.8
            },
            "contradicts": {
                "description": "Contradictory information",
                "directional": False, 
                "strength_decay": 0.05,
                "default_confidence": 0.8
            },
            "defines": {
                "description": "Definition relationship",
                "directional": True,
                "strength_decay": 0.0,  # Definitions don't decay
                "default_confidence": 0.95
            },
            # Custom relationship types can be added here
        }
    
    @classmethod
    def register_custom_type(cls, 
                           name: str, 
                           properties: Dict[str, Any]) -> None:
        """Register a new custom relationship type."""
        all_types = cls.get_all_types()
        if name in all_types:
            raise ValueError(f"Relationship type {name} already exists")
            
        # Validate required properties
        required = ["description", "directional", "strength_decay", "default_confidence"]
        for prop in required:
            if prop not in properties:
                raise ValueError(f"Missing required property: {prop}")
                
        # Add the new type (this would need proper persistence in a real implementation)
        # This is just a demonstration
        all_types[name] = properties
```

### Custom Graph Query Capabilities

Extend the graph query functionality:

```python
# pdf_manipulator/memory/graph_querier.py

class GraphQuerier:
    """Provides advanced query capabilities for semantic graphs."""
    
    def __init__(self, graph_path: str):
        """Initialize with path to graph database."""
        self.graph_path = graph_path
        self.conn = self._connect_to_db()
    
    def _connect_to_db(self):
        """Connect to SQLite database."""
        import sqlite3
        return sqlite3.connect(self.graph_path)
    
    def search_by_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search nodes by content similarity."""
        # Implement content-based search
        pass
    
    def find_path(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """Find shortest path between nodes."""
        # Implement pathfinding algorithm
        pass
    
    def get_subgraph(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """Extract subgraph centered on a node."""
        # Implement subgraph extraction
        pass
    
    def execute_custom_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a custom SQL query against the graph database."""
        cursor = self.conn.cursor()
        result = cursor.execute(query, params or {})
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
```

## Implementation Best Practices

### Component Design

1. **Single Responsibility Principle**
   - Each component should focus on a single aspect of processing
   - Avoid monolithic classes with multiple responsibilities
   - Create focused interfaces for specific functionality

2. **Dependency Injection**
   - Use constructor injection for dependencies
   - Allow configuration through parameters
   - Make backends and processors swappable

```python
# Good example
class SemanticEnhancer:
    def __init__(self, 
                backend: IntelligenceBackend,
                prompt_templates: PromptTemplates = None,
                config: Dict[str, Any] = None):
        self.backend = backend
        self.prompt_templates = prompt_templates or PromptTemplates()
        self.config = config or {}
```

3. **Configuration Over Code**
   - Use configuration files for customizable behavior
   - Avoid hard-coded values for thresholds, paths, etc.
   - Support environment variable substitution

### Error Handling

1. **Graceful Degradation**
   - Design each component to handle failures in dependencies
   - Provide fallback mechanisms where possible
   - Continue processing even with partial failures

```python
# Example of graceful degradation
def extract_toc(self, pdf_path: str) -> Optional[TOC]:
    """Extract TOC with fallbacks."""
    try:
        # First attempt: Extract native TOC
        toc = self._extract_native_toc(pdf_path)
        if toc and len(toc.sections) > 0:
            return toc
            
        # Second attempt: Use markitdown
        if self.config.get("fallback_to_markitdown", True):
            logger.info("Native TOC not found, falling back to markitdown")
            return self._extract_with_markitdown(pdf_path)
            
        # Third attempt: Construct from content
        logger.info("Constructing TOC from content")
        pages = self._extract_page_content(pdf_path)
        return self.construct_toc(pages)
            
    except Exception as e:
        logger.error(f"TOC extraction failed: {e}")
        # Final fallback: Create minimal TOC
        return self._create_minimal_toc(pdf_path)
```

2. **Specific Exceptions**
   - Define and use domain-specific exceptions
   - Include contextual information in error messages
   - Implement appropriate cleanup in exception handlers

```python
# pdf_manipulator/core/exceptions.py

class SemanticPipelineError(Exception):
    """Base exception for semantic pipeline errors."""
    pass

class StructureDiscoveryError(SemanticPipelineError):
    """Error during structure discovery phase."""
    pass

class LLMProcessingError(SemanticPipelineError):
    """Error during LLM processing."""
    pass

class GraphBuildingError(SemanticPipelineError):
    """Error during graph building."""
    pass
```

### Performance Optimization

1. **Parallel Processing**
   - Parallelize page-level processing
   - Use thread pools for I/O-bound operations
   - Implement batching for LLM requests

```python
# Example of parallel processing
def process_pages(self, pdf_path: str, max_workers: int = 4) -> List[ProcessedPage]:
    """Process pages in parallel."""
    from concurrent.futures import ThreadPoolExecutor
    
    # Extract pages
    pages = self._extract_pages(pdf_path)
    
    # Process in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(self._process_page, page) for page in pages]
        results = [future.result() for future in futures]
        
    return results
```

2. **Caching**
   - Implement caching for expensive operations
   - Use time-to-live (TTL) for dynamic data
   - Store intermediate results for reuse

```python
# Example of caching implementation
class CachedProcessor:
    """Processor with caching capabilities."""
    
    def __init__(self, cache_enabled: bool = True, cache_ttl: int = 3600):
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.cache_timestamps = {}
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if valid."""
        if not self.cache_enabled or key not in self.cache:
            return None
            
        timestamp = self.cache_timestamps.get(key, 0)
        if time.time() - timestamp > self.cache_ttl:
            return None
            
        return self.cache[key]
    
    def _store_in_cache(self, key: str, value: Any) -> None:
        """Store value in cache."""
        if not self.cache_enabled:
            return
            
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()
```

## Edge Scoring System

The semantic pipeline uses a sophisticated scoring system for edges in the knowledge graph:

```
final_edge_score = base_lexical_similarity * semantic_multiplier * recency_factor
```

### Implementation

```python
# pdf_manipulator/memory/edge_scorer.py

class EdgeScorer:
    """Manages edge scoring in the semantic graph."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Default configuration values
        self.semantic_multiplier = self.config.get("semantic_multiplier", 1.5)
        self.recency_decay_rate = self.config.get("recency_decay_rate", 0.9)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.3)
    
    def calculate_score(self, 
                       base_score: float, 
                       is_semantic: bool,
                       edge_age: int = 0, 
                       relationship_type: str = "relates_to") -> float:
        """Calculate final edge score.
        
        Args:
            base_score: Initial lexical/statistical score (0-1)
            is_semantic: Whether this edge was identified by semantic analysis
            edge_age: Age of the edge in processing steps
            relationship_type: Type of relationship
            
        Returns:
            Final edge score (0-1)
        """
        # Get relationship properties
        rel_props = RelationshipTypes.get_all_types().get(
            relationship_type, 
            {"strength_decay": 0.1, "default_confidence": 0.7}
        )
        
        # Calculate multipliers
        semantic_mult = self.semantic_multiplier if is_semantic else 1.0
        recency_factor = self._calculate_recency(
            edge_age, 
            rel_props.get("strength_decay", 0.1)
        )
        
        # Calculate final score
        score = base_score * semantic_mult * recency_factor
        
        # Apply confidence threshold
        if score < self.confidence_threshold:
            score = 0
            
        # Cap at 1.0
        return min(score, 1.0)
    
    def _calculate_recency(self, age: int, decay_rate: float) -> float:
        """Calculate recency factor based on edge age."""
        if age == 0:
            return 1.0
        return (self.recency_decay_rate ** age) * (1 - decay_rate * age)
    
    def update_edge_scores(self, 
                         graph: Graph, 
                         processing_step: int) -> None:
        """Update all edge scores based on current processing step."""
        for edge_id, edge in graph.edges.items():
            age = processing_step - edge.created_at
            edge.weight = self.calculate_score(
                edge.base_score,
                edge.is_semantic,
                age,
                edge.relationship_type
            )
```

## Testing and Validation

### Mock LLM Backend for Testing

```python
# tests/mock_llm_backend.py

class MockLLMBackend(IntelligenceBackend):
    """Mock backend for testing without real LLM calls."""
    
    def __init__(self, responses: Dict[str, str] = None):
        self._supports_vision = True
        self.call_count = 0
        self.calls = []
        self.responses = responses or {
            "summarize": "This section discusses the main topic of the document.",
            "relationships": "Related to: Section 2, Section 3. References: Figure 1.",
            "default": "Mock response for testing purposes."
        }
    
    @property
    def supports_vision(self) -> bool:
        return self._supports_vision
    
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Return predictable responses for testing."""
        self.call_count += 1
        self.calls.append({"text": text, "has_image": image is not None})
        
        # Determine response based on prompt content
        for key, response in self.responses.items():
            if key in text.lower():
                return response
                
        return self.responses.get("default", "Mock response")
```

### Basic Pipeline Test

```python
# tests/test_semantic_pipeline.py

def test_basic_pipeline_flow():
    """Ensure content flows through pipeline stages."""
    
    # Test with simple PDF
    test_pdf = "test_data/simple.pdf"
    
    # Stage 1: Structure Discovery
    analyzer = StructureAnalyzer()
    toc = analyzer.extract_toc(test_pdf)
    assert toc is not None
    assert len(toc.sections) > 0
    
    # Stage 2: Initial Analysis
    content_analyzer = ContentAnalyzer()
    first_page = extract_page_content(test_pdf, 0)
    word_stems = content_analyzer.extract_word_stems(first_page)
    assert len(word_stems) > 0
    
    # Stage 3: Graph Building
    graph_builder = GraphBuilder()
    node = graph_builder.create_node(
        {"content": first_page, "page": 0},
        ["document", "introduction"]
    )
    assert node.id is not None
    
    # Stage 4: Enhancement (mock LLM)
    mock_backend = MockLLMBackend()
    enhancer = SemanticEnhancer(mock_backend)
    context = enhancer.prepare_context(toc, Page(0, first_page))
    summary = enhancer.enhance_with_llm(context)
    assert len(summary) > 0
    
    print("✓ Content flows through all pipeline stages")
```

### End-to-End Test

```python
# tests/test_semantic_pipeline.py

def test_end_to_end_processing():
    """Test complete document processing."""
    
    pipeline = SemanticPipeline(
        backend=MockLLMBackend(),
        config={"semantic_pipeline": {"use_llm": True}}
    )
    
    result = pipeline.process("test_data/sample.pdf")
    
    # Verify output structure
    assert "nodes" in result
    assert "edges" in result
    assert len(result["nodes"]) > 0
    
    # Check node structure
    first_node = result["nodes"][0]
    assert "id" in first_node
    assert "content" in first_node
    assert "ontology_tags" in first_node
    
    print("✓ End-to-end processing produces expected structure")
```

## Current Limitations

While Memory Graph Extract offers valuable functionality for semantic document processing, it's important to be aware of its current limitations:

### 1. Document Types and Formats

- **PDF Focus**: Currently optimized primarily for PDF documents
- **Text-Heavy Documents**: Works best with text-focused rather than primarily visual documents
- **Simple Structures**: Complex nested documents may not be analyzed perfectly

### 2. Processing Capabilities

- **Document Size**: Very large documents may require significant processing time
- **Memory Usage**: Processing large PDFs can be memory-intensive
- **Language Support**: Currently optimized for English content

### 3. AI Backend Considerations

- **Model Quality Impact**: Understanding quality varies based on the model used
- **OpenAI Dependency**: Best results currently require OpenAI's API (external dependency)
- **Local Performance**: Local models like LLaVA via Ollama require good GPU hardware

### 4. Graph Construction

- **Simple Relationships**: Currently focuses on basic relationship types
- **Limited Inference**: Doesn't automatically infer complex relationships between concepts
- **Cross-Document Links**: Cross-document connections are limited in the current version

## Next Development Steps

Future development will focus on practical improvements that address current limitations:

### Near-Term Improvements

1. **Enhanced Document Support**
   - Better handling of image-heavy documents
   - Improved table and diagram extraction
   - Support for more input formats

2. **Performance Optimizations**
   - Incremental processing for large documents
   - Memory usage improvements
   - Optional processing modes for limited hardware

3. **User Experience**
   - Better progress reporting
   - More detailed logging
   - Improved error messages and recovery

### Medium-Term Goals

1. **Relationship Enhancement**
   - More sophisticated relationship detection
   - Better confidence scoring for edges
   - Improved ontological classification

2. **Integration Improvements**
   - Better compatibility with memory-graph ecosystem
   - Simplified setup process
   - Export to more visualization formats

3. **Local Model Support**
   - Optimizations for local LLM backends
   - Better handling of context limitations
   - Fallback mechanisms for limited hardware

### Contributing Areas

If you're interested in contributing to Memory Graph Extract, these areas would be particularly valuable:

1. **Testing and Validation**: Creating test cases with different document types
2. **Documentation**: Improving examples and explanations
3. **Performance**: Identifying and addressing bottlenecks
4. **Integration**: Enhancing compatibility with related tools

Memory Graph Extract is a work in progress, and contributions that help address these limitations are welcome!