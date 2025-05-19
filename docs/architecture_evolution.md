# Architecture Evolution

This document describes the architectural evolution of Memory Graph Extract (MGE), with a focus on the transformative refactoring that shaped the current system. It provides context for why certain design decisions were made and how they contribute to the project's core mission of semantic knowledge graph extraction.

## Overview

Memory Graph Extract has evolved from a document processing tool to a semantic knowledge graph builder. This evolution required significant architectural changes to prioritize semantic understanding and make the memory graph central to the system's operation.

## Core Architectural Principles

Throughout the refactoring process, these principles have guided our decisions:

1. **Semantic Focus**: Systems should prioritize understanding document meaning, not just extracting text
2. **Memory Graph Centrality**: Knowledge graphs are the primary output, not an optional feature
3. **Separation of Concerns**: Clear boundaries between processing stages
4. **Single Responsibility**: Each component focuses on one aspect of semantic processing
5. **Code Quality**: No file exceeds 500 lines, improving maintainability

## Architectural Transformation

### CLI Structure Evolution

The command-line interface was restructured from a monolithic design to a modular, semantic-focused organization:

**Before**: Single `commands.py` (929 lines) containing all CLI functionality

**After**: Modular command structure:
```
cli/
├── __init__.py
├── base.py              # Shared CLI utilities and decorators
├── process_commands.py  # Document processing commands
├── memory_commands.py   # Memory graph operations
├── config_commands.py   # Configuration management
├── semantic_commands.py # Semantic pipeline commands
├── utility_commands.py  # Render, OCR, info commands
└── main.py              # Entry point with command registration
```

This reorganization improved:
- **Discoverability**: Commands are logically grouped by domain
- **Maintainability**: Each file has clear responsibilities
- **Extensibility**: New command groups can be added without modifying existing code
- **Clarity**: Command relationships are explicit in the file structure

### Processor Hierarchy Clarification

A major architectural improvement was clarifying the previously confusing processor hierarchy:

**Before**: Multiple "Processor" classes with unclear boundaries:
- `DocumentProcessor` (in `intelligence/processor.py`)
- `DocumentProcessor` (in `core/pipeline.py`) 
- `MemoryProcessor`
- `TOCProcessor`
- `OCRProcessor`

**After**: Clear semantic naming and responsibilities:
- `SemanticOrchestrator` (was DocumentProcessor in pipeline)
- `ContentExtractor` (was DocumentProcessor in intelligence)
- `GraphBuilder` (was MemoryProcessor)
- `StructureAnalyzer` (was TOCProcessor)

The processor hierarchy now follows a clear pattern:
- `BaseProcessor` - Abstract base class
- `SemanticProcessor` - Semantic understanding 
- `ContentProcessor` - Text extraction
- `StructureProcessor` - Document structure
- `GraphProcessor` - Knowledge graph operations

This clarification resolved naming conflicts and made the flow of processing more intuitive.

### Intelligence Backend Organization

Intelligence backends were refactored for clarity and extensibility:

**Before**: Ad-hoc implementation with unclear hierarchy

**After**: Clear base classes with standardized interfaces:
- `BaseIntelligenceBackend` (abstract)
- `DirectExtractionBackend` (for markitdown)
- `AIEnhancedBackend` (for Ollama, LlamaCpp)
- `ContextAwareBackend` (for memory-enhanced)

The standardized methods include:
- `extract_semantic_content()`
- `enhance_with_context()`
- `generate_relationships()`

This structure makes it easier to implement new intelligence backends while maintaining consistent behavior.

### Memory Module Reorganization

The memory module was restructured to emphasize its central role:

**Before**: Memory functionality mixed with processing logic

**After**: Clean separation:
```
memory/
├── __init__.py
├── adapter.py          # Database operations
├── builder.py          # Graph construction logic
├── query.py            # Search and traversal
├── relationships.py    # Relationship detection
└── schema.sql          # Database schema
```

The memory module is now the focal point of the architecture, not an auxiliary feature.

### Configuration System Simplification

Configuration was simplified to prioritize semantic understanding:

- Created `SemanticConfig` class for graph-related settings
- Simplified backend configuration
- Made memory/graph the primary output, not optional

## Current Architecture

The current architecture reflects the semantic focus of Memory Graph Extract:

```
Document → SemanticOrchestrator → IntelligenceBackend → MemoryProcessor → Graph Database
             ↓                                              ↓
        ContentExtractor                             GraphBuilder
             ↓                                              ↓
        TOCProcessor                              StructureAnalyzer
```

### Key Components

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

## Metrics of Success

The architectural refactoring has achieved several key metrics:

- **Files refactored**: 15+
- **Lines reduced**: 929 → multiple files under 300 lines
- **New modules created**: 10
- **Clarity improved**: Significantly

## Future Architectural Directions

The refactoring process continues with these planned enhancements:

1. **Backend Consolidation**
   - Further standardize intelligence backends
   - Create clearer inheritance structure
   - Unify interface patterns across AI services

2. **Memory Module Enhancement**
   - Separate graph operations more cleanly
   - Enhance query capabilities
   - Improve relationship detection algorithms

3. **Testing Architecture**
   - Create semantic-focused test suite
   - Organize test structure by component
   - Add integration tests for full pipeline

```
tests/
├── unit/
│   ├── test_processors/
│   ├── test_memory/
│   └── test_backends/
├── integration/
│   ├── test_pipeline/
│   └── test_cli/
└── fixtures/
    ├── sample_pdfs/
    └── test_graphs/
```

## Conclusion

The architectural evolution of Memory Graph Extract represents a fundamental shift from document processing to semantic knowledge graph extraction. The refactoring has successfully aligned the codebase structure with its true purpose: building rich, queryable networks of interconnected information from documents.

For new developers, understanding this evolution provides context for the current design decisions and future development direction. The semantic focus permeates all aspects of the system, from the CLI organization to the processor hierarchy and memory graph centrality.