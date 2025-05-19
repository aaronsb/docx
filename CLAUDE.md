# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DocX is a Python framework for transforming PDF documents into semantic knowledge graphs. It goes beyond text extraction to build a deep understanding of document content, creating queryable networks of interconnected information.

**Core Purpose**: Build semantic knowledge graphs from documents, not just extract text.

## Architecture Philosophy

The system is designed around semantic understanding:

1. **Primary Output**: Knowledge graphs (SQLite databases compatible with memory-graph-mcp)
2. **Processing Focus**: Relationships, structure, and meaning
3. **Intelligence**: AI-enhanced understanding with context awareness

## Key Components

### Semantic Processing Layer (Primary)
- `MemoryProcessor`: Orchestrates semantic extraction
- `MemoryAdapter`: Manages graph storage and relationships  
- `TOCProcessor`: Analyzes document structure
- `RelationshipEngine`: Maps content connections

### Intelligence Layer
- `IntelligenceBackend`: Base for AI processors
- `MarkitdownBackend`: Direct semantic extraction
- `OllamaBackend`: AI-enhanced understanding
- `MemoryEnhancedBackend`: Context-aware processing

### Pipeline Layer
- `DocumentProcessor`: Manages extraction pipeline
- `ProcessingProgress`: Visual progress tracking

## Commands and Tools

### Core Semantic Commands

```bash
# Process document into semantic graph (primary use)
pdfx process document.pdf output/ --memory

# Memory graph operations
pdfx memory search "query" --database graph.db
pdfx memory info graph.db
pdfx memory connect doc1.db doc2.db
pdfx memory export graph.db

# Process directory of documents
pdfx process-dir papers/ output/ --memory --recursive
```

### Development Setup

```bash
# Install with semantic graph support
pip install -e .

# Optional: Install with llama.cpp
pip install -e '.[llama]'
```

## Processing Pipeline

### Primary Path: Direct Semantic Extraction
```
PDF → markitdown → Semantic Analysis → Knowledge Graph
```

### Enhanced Path: AI-Powered Understanding
```
PDF → Render → AI Analysis → Semantic Extraction → Knowledge Graph
                    ↓
              OCR (fallback)
```

### Context-Aware Path: Memory-Enhanced Processing
```
Existing Graph → Context → AI Processing → Enhanced Graph
```

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
  use_context: true               # Leverage existing knowledge
```

## Important Development Notes

### When Building Features

1. **Prioritize Semantic Understanding**
   - Features should enhance graph construction
   - Focus on relationships and meaning
   - Consider cross-document connections

2. **Memory Graph is Central**
   - Not an optional feature
   - Primary output format
   - Compatible with memory-graph-mcp

3. **Intelligence Backends**
   - Inherit from `IntelligenceBackend`
   - Implement semantic extraction methods
   - Support context-aware processing

### Code Organization

1. **Avoid Monoliths**
   - Break large files into focused modules
   - Separate concerns clearly
   - Use composition over inheritance

2. **Processor Hierarchy**
   - `SemanticProcessor`: Main orchestrator
   - `ContentProcessor`: Text extraction
   - `GraphBuilder`: Relationship mapping
   - `StructureAnalyzer`: Document structure

### Error Handling

- Use specific exceptions from `core/exceptions.py`
- Gracefully handle missing AI backends
- Provide semantic fallbacks (OCR → basic extraction)

### Testing Approach

- Test graph construction accuracy
- Verify relationship detection
- Check semantic search functionality
- Validate cross-document connections

## Performance Optimization

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

## Future Directions

1. **Enhanced Semantics**
   - Concept extraction
   - Citation mapping
   - Contradiction detection

2. **Graph Intelligence**
   - Natural language queries
   - Path-based reasoning
   - Knowledge synthesis

3. **Visualization**
   - Interactive graph exploration
   - Semantic clustering
   - Relationship maps

## CLI Pattern

Commands follow semantic operations:

```
pdfx [semantic-verb] [input] [options]
```

Semantic verbs:
- `process`: Extract semantic graph
- `memory`: Graph operations
- `analyze`: Deep understanding
- `connect`: Link documents

Utility verbs:
- `render`: Generate images
- `ocr`: Extract text
- `config`: Manage settings

## Integration Notes

The system integrates with:

1. **memory-graph-mcp**: Direct database compatibility
2. **Claude Desktop**: Knowledge-enhanced assistance
3. **Semantic Web**: RDF/OWL export planned

Remember: The goal is semantic understanding, not just text extraction.