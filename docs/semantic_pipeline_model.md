# Semantic Conversion Pipeline Model

This document describes the theoretical model for Memory Graph Extract's semantic conversion pipeline, which transforms PDF documents into ontologically-rich knowledge graphs.

## Overview

The pipeline is designed to extract not just text, but semantic understanding from documents, building a graph structure that captures relationships, context, and meaning. Unlike traditional vector embedding approaches, we focus on creating an ontologically-tagged semantic graph that preserves document intention and enables sophisticated traversal.

## Pipeline Stages

### 1. Document Structure Discovery

The pipeline begins by establishing the document's hierarchical structure:

1. **TOC Detection**
   - First attempt: Extract actual Table of Contents if present in PDF
   - Fallback: Use markitdown to extract content per page
   - Construct best-guess TOC from page-level content analysis

This TOC forms the backbone of our semantic graph, providing the primary hierarchical structure.

### 2. Initial Content Analysis

Once we have a TOC structure, we perform initial content analysis without deep LLM processing:

- **Text Analysis Methods**:
  - Word stem extraction for core concept identification
  - Bayesian analysis for term significance and relationships
  - Basic relationship detection between sections
  
- **Graph Construction**:
  - Attach content to TOC nodes
  - Create initial edge relationships
  - Apply preliminary scoring to connections

Note: This stage deliberately avoids deep language model analysis, focusing on extractable patterns.

### 3. Semantic Enhancement via LLM

With the basic structure in place, we enhance understanding using multimodal reasoning models:

1. **Context Preparation**
   - Current TOC structure provides global context
   - Page content in markdown format
   - Raw image capture of the page (when visual processing is available)

2. **LLM Processing** (e.g., LLaVA, GPT-4V)
   - Generate coherent summary considering all modalities
   - Extract semantic intentions rather than just surface content
   - Identify relationships not captured in initial analysis
   
3. **Graph Updates**
   - Attach coherent summary to TOC node
   - Create high-confidence semantic edges (score: 1.0)
   - Gradually de-score legacy/preliminary edges based on recency
   - Propagate semantic understanding through TOC inheritance

### 4. Iterative Refinement

As each page is processed:

- TOC inherits semantic, ontologically-tagged understanding
- Cross-references between sections are strengthened or weakened
- Relationships evolve based on accumulated context
- Context window management ensures processing within LLM limits

## Edge Scoring Mechanism

The system uses a sophisticated approach to edge weighting:

```
final_edge_score = base_lexical_similarity * semantic_multiplier * recency_factor
```

- **Lexical Base**: Initial score from Bayesian analysis and word stem relationships
- **Semantic Multiplier**: Higher weight for LLM-identified semantic connections
- **Recency Factor**: Newer edges receive higher scores; older edges decay
- **Priority System**: Semantic-to-semantic connections receive the highest priority

## Output Structure

The final output is a JSON-based graph containing:

- **Nodes**:
  - Unique IDs for pages/sections
  - Ontological tags (domain-specific categorization)
  - Semantic summaries (LLM-generated)
  - Confidence scores
  - Original content references

- **Edges**:
  - Typed relationships (e.g., "part_of", "references", "contradicts")
  - Confidence scores (0-1 range)
  - Directional indicators
  - Temporal metadata

## Key Principles

1. **Structure-First Approach**: TOC provides the organizing principle
2. **Ontological Tagging**: Semantic categories, not just vector embeddings
3. **Progressive Enhancement**: Basic extraction → LLM understanding
4. **Context Awareness**: Each page inherits document-wide context
5. **Dynamic Scoring**: Edge weights evolve throughout processing
6. **Multimodal Integration**: Visual elements enhance text understanding

## Practical Considerations

### Scalability
- **Context Limits**: Monitor TOC + markdown size for LLM constraints
- **Chunking Strategy**: Large documents may require logical partitioning
- **Parallel Processing**: Page-level processing can be parallelized
- **Memory Management**: Graph pruning for extremely large documents

### Robustness
- **Fallback Strategies**: Graceful degradation when TOC unavailable
- **Quality Checks**: Confidence thresholds for summary acceptance
- **Error Recovery**: Continue processing even with partial failures
- **Format Flexibility**: Handle diverse document structures

### Performance
- **Caching**: Reuse processed components where possible
- **Batch Processing**: Optimize API calls for external LLMs
- **Selective Enhancement**: Only apply LLM to high-value content
- **Resource Adaptation**: Scale processing based on available compute

## Implementation Architecture

This model guides the development of:

1. **SemanticOrchestrator**: Overall pipeline management
   - Coordinates all processing stages
   - Manages context and state
   - Handles error recovery

2. **StructureAnalyzer**: TOC extraction and construction
   - Native PDF TOC extraction
   - Markitdown-based fallback
   - Hierarchical structure synthesis

3. **ContentAnalyzer**: Initial lexical analysis
   - Word stem extraction
   - Bayesian relationship detection
   - Preliminary graph construction

4. **GraphBuilder**: Node and edge creation
   - Ontological tagging system
   - Dynamic edge scoring
   - Relationship type management

5. **SemanticEnhancer**: LLM enhancement layer
   - Multimodal context preparation
   - LLM backend abstraction
   - Summary quality validation

## Advanced Features

### Beyond Vector Similarity
- **Intentional Preservation**: Captures document purpose, not just content
- **Hierarchical Context**: Preserves structural relationships
- **Semantic Traversal**: Enables meaning-based navigation
- **Emergent Insights**: Discovers implicit connections

### MCP Server Integration
- **Guided Exploration**: LLMs navigate via semantic paths
- **Grounded Responses**: Reduces hallucination through structure
- **Contextual Understanding**: Preserves document-specific knowledge
- **Query Optimization**: Efficient traversal of knowledge graphs

## Future Extensions

1. **Cross-Document Intelligence**
   - Link related concepts across document boundaries
   - Build domain-specific knowledge networks
   - Enable comparative analysis

2. **Temporal Dynamics**
   - Track semantic evolution over document versions
   - Identify changing relationships
   - Version-aware querying

3. **Interactive Refinement**
   - Expert validation of semantic connections
   - User-guided ontology development
   - Feedback-based improvement

4. **Domain Specialization**
   - Field-specific ontologies
   - Custom relationship types
   - Specialized processing pipelines

The goal is to create a queryable, semantically-rich representation of document knowledge that captures not just content, but understanding—enabling both human and AI agents to explore document meaning through structured traversal rather than simple text matching.