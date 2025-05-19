# DocX Semantic Architecture

This document outlines the architecture of DocX, focusing on its core purpose: transforming PDF documents into semantic knowledge graphs for intelligent understanding.

## Core Vision

DocX is designed as a semantic understanding engine that creates queryable knowledge graphs from PDF documents. Instead of just extracting text, it builds a semantic network capturing:

- Document structure and hierarchies
- Relationships between content elements
- Cross-document connections
- Contextual understanding of information

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Document      │────▶│    Semantic      │────▶│   Knowledge     │
│   Input         │     │    Processor     │     │   Graph         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        │
        │                       ▼                        │
        │               ┌──────────────────┐            │
        │               │   Intelligence   │            │
        │               │   Backends       │            │
        │               └──────────────────┘            │
        │                       │                        ▼
        │                       ▼                ┌─────────────────┐
        │               ┌──────────────────┐     │  Memory Graph   │
        └──────────────▶│  TOC Analyzer    │────▶│  Database       │
                        └──────────────────┘     └─────────────────┘
```

## Component Hierarchy

### 1. Semantic Processing Layer (Primary)
The core of the system, focused on understanding and graph construction:

- **MemoryProcessor**: Orchestrates semantic extraction and graph building
- **MemoryAdapter**: Manages knowledge graph storage and relationships
- **TOCProcessor**: Analyzes document structure for semantic understanding
- **RelationshipEngine**: Maps connections between content elements

### 2. Intelligence Layer
AI backends that enhance semantic understanding:

- **IntelligenceBackend** (base)
  - MarkitdownBackend: Direct semantic extraction
  - OllamaBackend: AI-enhanced understanding
  - LlamaCppBackend: Local model integration
  - MemoryEnhancedBackend: Context-aware processing

### 3. Content Extraction Layer
Tools for pulling content from documents:

- **PDFDocument**: Core PDF handling
- **ImageRenderer**: Converts pages when needed
- **OCRProcessor**: Fallback text extraction

### 4. Pipeline Layer
Orchestration and coordination:

- **DocumentProcessor**: Manages the semantic extraction pipeline
- **ProcessingProgress**: Tracks pipeline execution

## Semantic Graph Structure

The knowledge graph captures multiple relationship types:

```
Document (root)
├── Page Nodes
│   ├── "part_of" → Document
│   └── "precedes/follows" → Other Pages
├── Section Nodes
│   ├── "part_of" → Document
│   ├── "contains" → Pages
│   └── "relates_to" → Other Sections
└── Concept Nodes
    ├── "mentioned_in" → Pages/Sections
    └── "related_to" → Other Concepts
```

## Processing Pipeline

### 1. Direct Semantic Extraction (Primary Path)
```
PDF → Markitdown → Semantic Analysis → Knowledge Graph
```

### 2. Enhanced AI Processing (When Needed)
```
PDF → Render → AI Analysis → Semantic Extraction → Knowledge Graph
         ↓
       OCR (fallback)
```

### 3. Memory-Enhanced Processing
```
Existing Graph → Context → AI Processing → Enhanced Graph
```

## Command Structure

The CLI reflects the semantic focus:

```
pdfx process     - Extract semantic graph from document
pdfx memory      - Interact with knowledge graphs
  ├── search     - Semantic search across graphs
  ├── info       - Graph statistics and structure
  ├── connect    - Link related documents
  └── export     - Export graph data

pdfx render      - Utility for image generation
pdfx ocr         - Utility for text extraction
```

## Configuration Philosophy

Configuration emphasizes semantic understanding:

```yaml
memory:
  enabled: true          # Semantic graph is primary output
  domain:
    name: "knowledge"    # Organize by knowledge domains
  extraction:
    relationships: true  # Detect connections
    summaries: true     # Generate semantic summaries
    
intelligence:
  default_backend: "memory_enhanced"  # Use context-aware processing
  use_context: true                  # Leverage existing knowledge
```

## Future Directions

1. **Advanced Relationship Detection**
   - Concept extraction and linking
   - Citation and reference mapping
   - Temporal relationship understanding

2. **Cross-Document Intelligence**
   - Automatic document clustering
   - Knowledge domain discovery
   - Contradiction detection

3. **Semantic Query Engine**
   - Natural language graph queries
   - Path-based reasoning
   - Knowledge synthesis

4. **Graph Visualization**
   - Interactive knowledge maps
   - Relationship exploration tools
   - Semantic clustering views

## Integration Points

The system is designed to integrate with:

1. **Memory Graph MCP**: Direct database compatibility
2. **Claude Desktop**: Knowledge-enhanced AI assistance
3. **External Knowledge Bases**: Import/export capabilities
4. **Semantic Web Standards**: RDF/OWL export options

## Performance Considerations

- Incremental graph building for large documents
- Cached relationship calculations
- Parallel processing for multi-document analysis
- Optimized graph queries via SQLite indexes

The architecture prioritizes semantic understanding while maintaining flexibility for different document types and processing needs.