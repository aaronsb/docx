# Semantic Pipeline Implementation Guide

This guide provides practical implementation details for the semantic conversion pipeline described in `semantic_pipeline_model.md`.

## Component Mapping

### 1. Structure Discovery - `StructureAnalyzer`

**Current**: `pdf_manipulator/memory/toc_processor.py`  
**Refactor Target**: `pdf_manipulator/processors/structure_analyzer.py`

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

**New Component**: `pdf_manipulator/processors/content_analyzer.py`

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

**Current**: `pdf_manipulator/memory/memory_processor.py`  
**Enhancement Needed**: Add ontological tagging

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

**New Component**: `pdf_manipulator/processors/semantic_enhancer.py`

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

## Supported LLM Backends

### 1. OpenAI (Multimodal)
```python
class OpenAIMultimodalBackend(IntelligenceBackend):
    """OpenAI API with vision support."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.supports_vision = True
    
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Process with GPT-4 Vision."""
        messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
        if image:
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"}
            })
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
```

### 2. Ollama (Local)
```python
class OllamaBackend(IntelligenceBackend):
    """Local Ollama endpoint."""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.supports_vision = model in ["llava", "bakllava"]
    
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Process with Ollama."""
        data = {"model": self.model, "prompt": text}
        if image and self.supports_vision:
            data["images"] = [image]
        
        response = requests.post(f"{self.base_url}/api/generate", json=data)
        return response.json()["response"]
```

### 3. Generic HTTP Endpoint
```python
class HTTPEndpointBackend(IntelligenceBackend):
    """Generic HTTP endpoint for LLMs."""
    
    def __init__(self, endpoint_url: str, headers: Dict[str, str] = None):
        self.endpoint_url = endpoint_url
        self.headers = headers or {}
        self.supports_vision = False  # Configure based on endpoint
    
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Process via HTTP endpoint."""
        payload = {"text": text}
        if image:
            payload["image"] = image
        
        response = requests.post(
            self.endpoint_url, 
            json=payload,
            headers=self.headers
        )
        return response.json()["result"]
```

## Lightweight Testing Strategy

### 1. Pipeline Flow Test
```python
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

### 2. Integration Test
```python
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

### 3. Mock LLM Backend for Testing
```python
class MockLLMBackend(IntelligenceBackend):
    """Mock backend for testing without real LLM calls."""
    
    def __init__(self):
        self.supports_vision = True
        self.call_count = 0
    
    def process(self, text: str, image: Optional[str] = None) -> str:
        """Return predictable responses for testing."""
        self.call_count += 1
        
        if "summarize" in text.lower():
            return "This section discusses the main topic of the document."
        elif "relationships" in text.lower():
            return "Related to: Section 2, Section 3. References: Figure 1."
        else:
            return f"Mock response for prompt: {text[:50]}..."
```

## Configuration

```yaml
semantic_pipeline:
  # LLM Backend Configuration
  llm_backend:
    type: "openai"  # Options: openai, ollama, http
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
  
  # Testing Configuration
  testing:
    use_mock_backend: true
    mock_responses_file: "test_data/mock_responses.json"
```

## Quick Start

```bash
# Install with test dependencies
pip install -e ".[test]"

# Run basic pipeline test
python -m pytest tests/test_pipeline_flow.py

# Test with real PDF (using mock LLM)
pdfx process test.pdf output/ --memory --mock-llm

# Test with real LLM (OpenAI)
export OPENAI_API_KEY="your-key"
pdfx process test.pdf output/ --memory --backend openai

# Test with local Ollama
pdfx process test.pdf output/ --memory --backend ollama --model llava
```

## Next Steps

1. Implement basic pipeline components
2. Create mock LLM backend for testing
3. Add support for OpenAI multimodal API
4. Test with sample PDFs
5. Refine based on output quality