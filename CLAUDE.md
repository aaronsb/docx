# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Memory Graph Extract (formerly DocX/pdfx) is a semantic extraction framework that transforms documents into knowledge graphs compatible with the memory-graph ecosystem. It goes beyond text extraction to build a deep understanding of document content, creating queryable networks of interconnected information.

**Core Purpose**: Build semantic knowledge graphs from documents, not just extract text.

## Architecture Philosophy

The system is designed around semantic understanding:

1. **Primary Output**: Knowledge graphs (SQLite databases compatible with memory-graph-mcp)
2. **Processing Focus**: Relationships, structure, and meaning
3. **Intelligence**: AI-enhanced understanding with context awareness

## Key Commands

### Primary Commands
```bash
# Extract document into semantic graph
mge extract document.pdf output/ --memory

# Process directory of documents
mge extract-dir papers/ output/ --memory --recursive

# Memory graph operations
mge memory search "query" --database graph.db
mge memory info graph.db
mge memory connect doc1.db doc2.db
mge memory export graph.db

# Development setup
pip install -e .                    # Basic installation
pip install -e ".[llama]"          # With llama.cpp support
pip install -e ".[dev]"            # With test dependencies
```

### Testing Commands
```bash
# Install test dependencies if not already installed
pip install pytest pytest-cov pytest-mock

# Run tests (no test suite currently exists)
pytest tests/                      # Will need to create tests directory
pytest --cov=pdf_manipulator      # With coverage
```

### Linting & Type Checking
```bash
# No specific linting/type checking setup found
# Consider adding:
pip install black isort mypy flake8
black pdf_manipulator/            # Code formatting
isort pdf_manipulator/            # Import sorting
mypy pdf_manipulator/             # Type checking
flake8 pdf_manipulator/           # Linting
```

## High-Level Architecture

### Core Components Interaction
```
Document → SemanticOrchestrator → IntelligenceBackend → MemoryProcessor → Graph Database
             ↓                                              ↓
        ContentExtractor                             GraphBuilder
             ↓                                              ↓
        TOCProcessor                              StructureAnalyzer
```

### Key Abstractions

1. **SemanticOrchestrator** (`core/semantic_orchestrator.py`)
   - Central coordinator for the extraction pipeline
   - Manages flow between components
   - Handles pipeline configuration

2. **IntelligenceBackend** (`intelligence/base.py`)
   - Abstract base for AI processors
   - Implementations: Markitdown, Ollama, LlamaCpp, MemoryEnhanced
   - Context-aware processing interface

3. **MemoryProcessor** (`memory/memory_processor.py`)
   - Manages semantic graph construction
   - Coordinates with GraphBuilder and StructureAnalyzer
   - Handles cross-document relationships

4. **DocumentProcessor** (`core/pipeline.py`)
   - Legacy pipeline (being refactored)
   - Still handles basic extraction flow

### Processing Pipeline Stages

1. **Structure Discovery**
   - Extract existing TOC or construct from content
   - Establish document hierarchy

2. **Initial Analysis**
   - Word stem extraction
   - Bayesian term analysis
   - Basic relationship mapping

3. **Semantic Enhancement**
   - LLM-based understanding
   - Context-aware page processing
   - Graph enrichment with high-confidence edges

4. **Output Generation**
   - JSON graph with ontological tagging
   - SQLite database (memory-graph format)
   - Confidence scoring throughout

## Configuration System

Configuration emphasizes semantic understanding:

```yaml
memory:
  enabled: true                    # Default: semantic graphs
  database_name: "memory_graph.db"
  domain:
    name: "knowledge"
    description: "Document knowledge base"
  extraction:
    detect_relationships: true
    generate_summaries: true
    min_content_length: 50

intelligence:
  default_backend: "memory_enhanced"
  backends:
    markitdown:
      # Direct semantic extraction
    ollama:
      model: "llava:latest"
      base_url: "http://localhost:11434"
    memory_enhanced:
      use_context: true
```

## Development Guidelines

### Adding New Features

1. **Semantic Understanding First**
   - Features should enhance graph construction
   - Focus on relationships and meaning
   - Consider cross-document connections

2. **Memory Graph is Central**
   - Not an optional feature
   - Primary output format
   - Compatible with memory-graph-mcp

3. **Intelligence Backend Pattern**
   ```python
   class NewBackend(IntelligenceBackend):
       def process_page(self, image_path, **kwargs):
           # Implement semantic extraction
           pass
           
       def process_with_context(self, content, context):
           # Use existing knowledge
           pass
   ```

### Code Organization

1. **Module Structure**
   - `core/`: Pipeline orchestration
   - `intelligence/`: AI backends
   - `memory/`: Graph building
   - `cli/`: Command interface
   - `utils/`: Shared utilities

2. **Avoid Monoliths**
   - Keep files under ~500 lines
   - Single responsibility per class
   - Use composition over inheritance

### Error Handling

- Use specific exceptions from `core/exceptions.py`
- Gracefully handle missing AI backends
- Provide semantic fallbacks

## CLI Patterns

Commands follow semantic operations:

```
mge [semantic-verb] [input] [options]
```

Semantic verbs:
- `extract`: Build semantic graph
- `memory`: Graph operations
- `process`: Legacy compatibility
- `config`: Settings management

Utility verbs:
- `render`: Generate images
- `ocr`: Extract text

## Integration Points

1. **memory-graph-mcp**: Direct database compatibility
2. **memory-graph-interface**: Web UI for graphs
3. **Claude Desktop**: Knowledge-enhanced assistance

## Future Refactoring

Currently transitioning from `pdfx`/`DocX` naming to `mge` (Memory Graph Extract):
- CLI commands support both naming schemes
- Internal modules still use `pdf_manipulator` namespace
- Consider full rename to `memory_graph_extract` package

## Testing Strategy

When adding tests:
1. Create `tests/` directory structure
2. Test semantic extraction accuracy
3. Verify relationship detection
4. Validate graph construction
5. Check cross-document connections

## Performance Considerations

1. **Graph Building**
   - Incremental construction for large docs
   - Batch relationship calculations
   - Optimize SQLite indexes

2. **Memory Usage**
   - Stream process large documents
   - Cache frequently accessed nodes
   - Limit graph traversal depth

3. **Processing Speed**
   - Use markitdown for direct extraction
   - Parallelize multi-document processing
   - Cache AI model responses