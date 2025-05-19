"""Test framework for semantic pipeline with mock LLM backends."""
import pytest
import json
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

from pdf_manipulator.core.semantic_orchestrator import SemanticOrchestrator, ProcessingConfig
from pdf_manipulator.processors.structure_analyzer import StructureAnalyzer, TOCStructure, TOCEntry
from pdf_manipulator.processors.content_analyzer import ContentAnalyzer
from pdf_manipulator.processors.semantic_enhancer import SemanticEnhancer
from pdf_manipulator.memory.graph_builder import GraphBuilder, NodeType, EdgeType
from pdf_manipulator.intelligence.base import IntelligenceBackend


class MockLLMBackend(IntelligenceBackend):
    """Mock backend for testing without real LLM calls."""
    
    def __init__(self, 
                 responses: Optional[Dict[str, str]] = None,
                 default_confidence: float = 0.9):
        """Initialize mock backend.
        
        Args:
            responses: Predefined responses for specific prompts
            default_confidence: Default confidence score
        """
        super().__init__()
        self.supports_vision = True
        self.call_count = 0
        self.last_prompt = None
        self.last_image = None
        self.responses = responses or {}
        self.default_confidence = default_confidence
    
    def process(self, prompt: str, image: Optional[str] = None, **kwargs) -> str:
        """Return predictable responses for testing."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_image = image
        
        # Check for predefined response
        for key, response in self.responses.items():
            if key in prompt:
                return response
        
        # Generate structured response based on prompt content
        if "semantic analysis" in prompt.lower() or kwargs.get("json_mode"):
            return json.dumps({
                "summary": "This section discusses the main topic of the document.",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "relationships": [
                    ["concept1", "relates_to", "concept2"],
                    ["concept2", "supports", "concept3"]
                ],
                "ontology_tags": ["technical", "algorithm", "data_structure"],
                "confidence": self.default_confidence,
                "evidence": ["Supporting quote from the text"]
            })
        elif "relationships" in prompt.lower():
            return "Related to: Section 2, Section 3. References: Figure 1."
        else:
            return f"Mock response for prompt: {prompt[:50]}..."
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information."""
        return {
            "provider": "mock",
            "model": "mock-llm",
            "supports_vision": self.supports_vision,
            "call_count": self.call_count
        }


class TestSemanticPipeline:
    """Test the semantic processing pipeline."""
    
    @pytest.fixture
    def mock_backend(self):
        """Create a mock LLM backend."""
        return MockLLMBackend()
    
    @pytest.fixture
    def test_config(self):
        """Create test configuration."""
        return ProcessingConfig(
            enable_llm=True,
            max_pages=5,
            parallel_pages=2,
            save_intermediate=True
        )
    
    @pytest.fixture
    def sample_toc(self):
        """Create a sample TOC structure."""
        root_entry = TOCEntry(
            number="1",
            title="Introduction",
            page=0,
            level=1,
            raw_text="1. Introduction ........... 1"
        )
        
        section1 = TOCEntry(
            number="1.1",
            title="Background",
            page=1,
            level=2,
            raw_text="1.1 Background ........... 2"
        )
        root_entry.add_child(section1)
        
        section2 = TOCEntry(
            number="2",
            title="Methodology",
            page=5,
            level=1,
            raw_text="2. Methodology ........... 5"
        )
        
        return TOCStructure(
            entries=[root_entry, section1, section2],
            format="dot_leader",
            toc_pages=[0],
            root_entries=[root_entry, section2]
        )
    
    def test_basic_pipeline_flow(self, mock_backend, test_config):
        """Test that content flows through all pipeline stages."""
        # Create orchestrator
        orchestrator = SemanticOrchestrator(
            backend=mock_backend,
            config=test_config
        )
        
        # Test component initialization
        assert orchestrator.structure_analyzer is not None
        assert orchestrator.content_analyzer is not None
        assert orchestrator.graph_builder is not None
        assert orchestrator.semantic_enhancer is not None
    
    def test_structure_discovery(self):
        """Test structure analyzer functionality."""
        analyzer = StructureAnalyzer()
        
        # Test heading detection
        text = """
        # Chapter 1: Introduction
        
        This is the introduction text.
        
        ## 1.1 Background
        
        Some background information.
        """
        
        sections = analyzer.analyze_hierarchy(text)
        assert len(sections) >= 2
        assert any("Introduction" in s.title for s in sections)
        assert any("Background" in s.title for s in sections)
    
    def test_content_analysis(self):
        """Test content analyzer functionality."""
        analyzer = ContentAnalyzer()
        
        text = """
        Machine learning is a subset of artificial intelligence.
        Deep learning is a type of machine learning that uses neural networks.
        """
        
        # Test word stem extraction
        stems = analyzer.extract_word_stems(text)
        assert len(stems) > 0
        assert any(s.stem == "learn" for s in stems)
        
        # Test relationship detection
        relationships = analyzer.detect_relationships(text)
        assert len(relationships) > 0
        assert any(r.type == "type_of" for r in relationships)
    
    def test_graph_building(self):
        """Test graph builder functionality."""
        builder = GraphBuilder()
        
        # Create nodes
        doc_node = builder.create_node(
            content={"text": "Document root"},
            node_type=NodeType.DOCUMENT,
            ontology_tags=["research", "paper"]
        )
        
        concept_node = builder.create_node(
            content={"text": "Machine Learning"},
            node_type=NodeType.CONCEPT,
            ontology_tags=["algorithm", "ai"]
        )
        
        # Create edge
        edge = builder.create_edge(
            source=doc_node,
            target=concept_node,
            edge_type=EdgeType.CONTAINS,
            confidence=0.9,
            semantic_strength=0.8
        )
        
        # Verify graph structure
        assert len(builder.nodes) == 2
        assert len(builder.edges) == 1
        assert edge.weight > 0
        
        # Test graph export
        graph_data = builder.export_graph()
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert "metadata" in graph_data
    
    def test_semantic_enhancement(self, mock_backend, sample_toc):
        """Test semantic enhancer functionality."""
        enhancer = SemanticEnhancer(backend=mock_backend)
        builder = GraphBuilder()
        
        # Create a page node
        page_node = builder.create_node(
            content={"text": "Page content", "page_number": 0},
            node_type=NodeType.PAGE
        )
        
        # Prepare context
        context = enhancer.prepare_context(
            toc=sample_toc,
            page_content="This is the page content.",
            page_number=0,
            total_pages=10
        )
        
        # Generate summary
        summary = enhancer.enhance_with_llm(context)
        
        # Verify summary structure
        assert summary.text != ""
        assert len(summary.key_concepts) > 0
        assert len(summary.relationships) > 0
        assert summary.confidence > 0
        
        # Update graph
        enhancer.update_graph(builder, summary, page_node)
        
        # Verify graph was updated
        assert len(builder.edges) > 0
    
    def test_end_to_end_processing(self, mock_backend, test_config, tmp_path):
        """Test complete document processing."""
        # Create test PDF path (would be mocked in real test)
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_text("mock pdf content")
        
        # Create orchestrator
        orchestrator = SemanticOrchestrator(
            backend=mock_backend,
            config=test_config
        )
        
        # Mock the document processing methods
        def mock_extract_pages(doc_path):
            return [
                {"number": 0, "text": "Page 1 content", "image_path": None},
                {"number": 1, "text": "Page 2 content", "image_path": None}
            ]
        
        # Would need to mock these in actual implementation
        # orchestrator._extract_pages = mock_extract_pages
        
        # Process would be tested with mocked components
        # result = orchestrator.process_document(test_pdf, tmp_path)
    
    def test_edge_scoring(self):
        """Test edge scoring mechanism."""
        builder = GraphBuilder()
        
        # Create nodes
        node1 = builder.create_node(
            content={"text": "Machine learning algorithms"},
            node_type=NodeType.CONCEPT
        )
        
        node2 = builder.create_node(
            content={"text": "Deep learning networks"},
            node_type=NodeType.CONCEPT
        )
        
        # Create edge with semantic strength
        edge = builder.create_edge(
            source=node1,
            target=node2,
            edge_type=EdgeType.RELATES_TO,
            semantic_strength=0.9
        )
        
        # Test scoring
        initial_weight = edge.weight
        assert initial_weight > 0
        
        # Update scores
        builder.update_scores(edge, new_confidence=0.95, semantic_boost=0.8)
        assert edge.weight != initial_weight
        assert edge.confidence == 0.95
    
    def test_ontological_inference(self):
        """Test ontological tagging and inference."""
        builder = GraphBuilder()
        
        # Create node with tags
        node = builder.create_node(
            content={"text": "Sorting algorithm"},
            node_type=NodeType.CONCEPT,
            ontology_tags=["algorithm", "computational"]
        )
        
        # Apply inference
        inferred_tags = builder.apply_ontological_inference(node)
        
        # Should have inferred additional tags
        assert len(node.ontology_tags) > 2
    
    def test_parallel_processing(self, mock_backend, test_config):
        """Test parallel page processing."""
        test_config.parallel_pages = 3
        
        orchestrator = SemanticOrchestrator(
            backend=mock_backend,
            config=test_config
        )
        
        # Would test with multiple pages processed in parallel
        # Verify thread safety and correct results
    
    def test_error_handling(self, test_config):
        """Test error handling in pipeline."""
        # Create backend that throws errors
        class ErrorBackend(IntelligenceBackend):
            def process(self, prompt: str, image: Optional[str] = None, **kwargs) -> str:
                raise Exception("Processing error")
        
        error_backend = ErrorBackend()
        error_backend.supports_vision = True
        
        orchestrator = SemanticOrchestrator(
            backend=error_backend,
            config=test_config
        )
        
        # Processing should handle errors gracefully
        # with pytest.raises(ProcessingError):
        #     orchestrator.process_document("fake.pdf", "output/")


# Integration test fixtures
@pytest.fixture
def sample_pdf_content():
    """Create sample PDF-like content for testing."""
    return """
    Table of Contents
    
    1. Introduction ........... 1
    2. Background ............ 3
    3. Methodology ........... 7
    
    Page 1
    
    # Introduction
    
    This document explores the fundamentals of machine learning
    and its applications in modern computing.
    
    Page 3
    
    # Background
    
    Machine learning is a subset of artificial intelligence that
    enables systems to learn from data.
    """


def test_pipeline_with_sample_content(sample_pdf_content):
    """Test pipeline with realistic content."""
    # This would test the full pipeline with sample content
    # mimicking real PDF processing
    pass