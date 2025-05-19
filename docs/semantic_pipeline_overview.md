# Semantic Pipeline Architecture Overview

This document provides a comprehensive overview of the semantic pipeline implementation in Memory Graph Extract, detailing the components, features, and usage patterns.

## Executive Summary

The semantic pipeline transforms documents into rich, queryable knowledge graphs by extracting not just text, but semantic understanding. It builds ontologically-tagged networks of relationships that preserve document intent and meaning, enabling sophisticated traversal and inference capabilities.

## Architecture Components

### 1. Core Pipeline Components

#### StructureAnalyzer
- **Purpose**: Extracts and constructs document structure
- **Features**:
  - Native PDF TOC extraction
  - Markitdown-based fallback for documents without TOC
  - Hierarchical structure synthesis from content analysis
  - Confidence scoring for structure detection
- **Location**: `pdf_manipulator/processors/structure_analyzer.py`

#### ContentAnalyzer
- **Purpose**: Performs initial lexical and statistical analysis
- **Features**:
  - Word stem extraction using NLTK
  - Bayesian term significance calculation
  - Relationship detection through pattern matching
  - TF-IDF scoring for term importance
- **Location**: `pdf_manipulator/processors/content_analyzer.py`

#### GraphBuilder
- **Purpose**: Constructs semantic knowledge graphs
- **Features**:
  - Ontological tagging system with domain classification
  - Dynamic edge scoring with recency factors
  - Node and edge confidence tracking
  - Subgraph extraction and traversal
- **Location**: `pdf_manipulator/memory/graph_builder.py`

#### SemanticEnhancer
- **Purpose**: Enriches understanding through LLM processing
- **Features**:
  - Context-aware page processing
  - Multimodal understanding (text + images)
  - Semantic relationship extraction
  - Summary generation with confidence scores
- **Location**: `pdf_manipulator/processors/semantic_enhancer.py`

### 2. Intelligence Backends

#### OpenAI Multimodal Backend
- **Purpose**: Integration with GPT-4V for vision and text processing
- **Features**:
  - Vision model support (GPT-4V, GPT-4-turbo)
  - Structured JSON output for semantic analysis
  - Cost estimation and model information
  - Configurable temperature and token limits
- **Location**: `pdf_manipulator/intelligence/openai_multimodal.py`

#### Ollama Multimodal Backend
- **Purpose**: Local LLM processing with LLaVA support
- **Features**:
  - Support for LLaVA, BakLLaVA, and other multimodal models
  - Local processing without API dependencies
  - Model management and downloading
  - Processing time estimation
- **Location**: `pdf_manipulator/intelligence/ollama_multimodal.py`

#### Mock Backend
- **Purpose**: Testing without real LLM calls
- **Features**:
  - Predictable responses for testing
  - Configurable response patterns
  - Call tracking and verification
  - Performance testing support
- **Location**: `tests/test_semantic_pipeline.py`

### 3. Pipeline Orchestration

#### SemanticOrchestrator
- **Purpose**: Coordinates the entire processing pipeline
- **Features**:
  - Phase-based processing (structure → analysis → enhancement → output)
  - Parallel page processing with configurable workers
  - Progress tracking and reporting
  - Error handling with graceful degradation
- **Location**: `pdf_manipulator/core/semantic_orchestrator.py`

#### ProcessingConfig
- **Purpose**: Configuration management for pipeline behavior
- **Features**:
  - Enable/disable LLM enhancement
  - Parallel processing settings
  - Context window management
  - Output format selection
- **Location**: `pdf_manipulator/core/semantic_orchestrator.py`

### 4. Configuration System

#### SemanticConfigManager
- **Purpose**: Manages pipeline configuration
- **Features**:
  - YAML-based configuration
  - Environment variable substitution
  - CLI argument merging
  - Configuration validation
- **Location**: `pdf_manipulator/config/semantic_config_manager.py`

#### Configuration Schema
- **Purpose**: Defines all configurable parameters
- **Features**:
  - Backend configurations (OpenAI, Ollama, HTTP)
  - Pipeline behavior settings
  - Performance tuning options
  - Output format specifications
- **Location**: `pdf_manipulator/config/semantic_pipeline_config.yaml`

## Key Features

### Document Structure Discovery
- Native PDF TOC extraction with metadata parsing
- Fallback to content-based structure detection
- Heading pattern recognition (numbered, chapter, markdown styles)
- Hierarchical relationship preservation
- Confidence-based structure validation

### Initial Content Analysis
- Word stem extraction for concept identification
- Bayesian analysis for term significance
- Pattern-based relationship detection
- Co-occurrence analysis for implicit connections
- TF-IDF scoring for document-wide importance

### Semantic Enhancement
- Multimodal LLM processing (text + images)
- Context-aware understanding with TOC structure
- Previous page summaries for continuity
- Semantic relationship extraction with typed edges
- Confidence scoring for all extracted information

### Graph Construction
- Ontological tagging with domain classification
- Dynamic edge scoring formula: `score = lexical × semantic × recency`
- Temporal decay for edge relevance
- Hierarchical node organization
- Metadata preservation for traceability

### Performance Optimization
- Parallel page processing with thread pools
- Configurable batch sizes for LLM calls
- Caching for processed components
- Memory limits for large documents
- Progress tracking with real-time updates

## Usage Patterns

### Basic Document Processing
```bash
# Process document with default settings
mge semantic process document.pdf output/

# Process with specific backend
mge semantic process document.pdf output/ --backend openai

# Process without LLM enhancement
mge semantic process document.pdf output/ --no-llm
```

### Advanced Configuration
```bash
# Use custom configuration file
mge semantic process document.pdf output/ --config custom.yaml

# Override specific settings
mge semantic process document.pdf output/ --max-pages 50 --parallel 8

# Save intermediate results
mge semantic process document.pdf output/ --save-intermediate
```

### Testing and Validation
```bash
# Test pipeline with mock backend
mge semantic test --backend mock

# Test with specific samples
mge semantic test --samples 5

# Validate configuration
mge config validate semantic_pipeline_config.yaml
```

## Configuration Examples

### Minimal Configuration
```yaml
llm_backend:
  type: "ollama"
  backends:
    ollama:
      model: "llava:latest"

pipeline:
  enable_llm: true
  output_format: "json"
```

### Production Configuration
```yaml
llm_backend:
  type: "openai"
  backends:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4-vision-preview"
      temperature: 0.1

pipeline:
  enable_llm: true
  parallel_pages: 8
  save_intermediate: true
  output_format: "both"

performance:
  cache:
    enabled: true
    ttl: 7200
  memory:
    max_graph_nodes: 50000
```

## Output Formats

### JSON Graph Format
```json
{
  "nodes": {
    "node_id": {
      "type": "page|section|concept",
      "content": {},
      "ontology_tags": [],
      "confidence": 0.95
    }
  },
  "edges": {
    "edge_id": {
      "source_id": "node_id",
      "target_id": "node_id", 
      "type": "contains|references|...",
      "weight": 0.85,
      "confidence": 0.9
    }
  },
  "metadata": {
    "created_at": "2024-01-20T10:00:00",
    "total_nodes": 150,
    "total_edges": 450
  }
}
```

### SQLite Format (Memory-Graph Compatible)
- Direct compatibility with memory-graph MCP server
- Queryable through memory-graph-interface
- Domain-based organization
- Full-text search support

## Integration Points

### Memory Graph Ecosystem
- **memory-graph**: MCP server for AI agent access
- **memory-graph-interface**: Web UI for human exploration
- **Output Compatibility**: SQLite database format matches ecosystem requirements

### External Systems
- **API Endpoints**: RESTful API for graph queries (planned)
- **Export Formats**: RDF/OWL for semantic web (planned)
- **Visualization**: D3.js/Cytoscape.js integration (planned)

## Performance Characteristics

### Processing Speed
- **Basic Extraction**: ~1-2 seconds per page
- **LLM Enhancement**: ~5-10 seconds per page (backend dependent)
- **Parallel Processing**: Linear speedup up to 8 workers
- **Memory Usage**: ~100MB + 10MB per 100 pages

### Scalability
- **Document Size**: Tested up to 1000 pages
- **Graph Size**: Optimized for 10K nodes, 50K edges
- **Concurrent Documents**: Limited by system memory
- **API Rate Limits**: Configurable retry and backoff

## Error Handling

### Graceful Degradation
- TOC extraction → Markitdown fallback → Content construction
- LLM failure → Basic extraction continues
- OCR failure → Skip page with warning
- API timeout → Retry with exponential backoff

### Validation
- Configuration validation before processing
- Structure confidence thresholds
- Relationship strength minimums
- Output format verification

## Future Enhancements

### Cross-Document Intelligence
- Link related concepts across documents
- Build domain-specific knowledge networks
- Detect contradictions and updates
- Track concept evolution over time

### Advanced Semantics
- Custom ontology definitions
- Domain-specific relationship types
- Inference rules for new connections
- Concept clustering and categorization

### Performance Improvements
- GPU acceleration for LLM inference
- Distributed processing for large corpora
- Incremental graph updates
- Real-time processing pipeline

## Conclusion

The semantic pipeline represents a sophisticated approach to document understanding that goes beyond traditional text extraction. By combining structural analysis, statistical processing, and AI-enhanced understanding, it creates rich knowledge graphs that capture not just what documents say, but what they mean.

This architecture enables both human and AI agents to explore document knowledge through natural traversal paths, supporting advanced use cases like research synthesis, knowledge discovery, and intelligent document navigation.