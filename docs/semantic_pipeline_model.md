# Semantic Conversion Pipeline Model

This document describes the theoretical model for DocX's semantic conversion pipeline, which transforms PDF documents into ontologically-rich knowledge graphs.

## Overview

The pipeline is designed to extract not just text, but semantic understanding from PDFs, building a graph structure that captures relationships, context, and meaning. Unlike traditional vector embedding approaches, we focus on creating an ontologically-tagged semantic graph.

## Pipeline Stages

### 1. Document Structure Discovery

The pipeline begins by establishing the document's hierarchical structure:

1. **TOC Detection**
   - First attempt: Extract actual Table of Contents if present in PDF
   - Fallback: Use markitdown to extract content per page
   - Construct best-guess TOC from page-level content analysis

This TOC forms the backbone of our semantic graph, providing the primary hierarchical structure.

### 2. Initial Content Attachment

Once we have a TOC structure, we perform initial content analysis:

- **Text Analysis Methods**:
  - Word stem extraction
  - Bayesian analysis for term significance
  - Basic relationship detection
  
- **Graph Construction**:
  - Attach content to TOC nodes
  - Create initial edge relationships
  - Apply preliminary scoring to connections

Note: This stage deliberately avoids deep language model analysis, focusing on extractable patterns.

### 3. Semantic Enhancement via LLM

With the basic structure in place, we enhance understanding using reasoning models:

1. **Context Preparation**
   - Current TOC structure
   - Page content in markdown format
   - Raw image capture of the page

2. **LLM Processing** (e.g., LLaVA backend)
   - Generate coherent summary considering:
     - TOC context
     - Markdown content
     - Visual elements
   
3. **Graph Updates**
   - Attach coherent summary to TOC node
   - Create high-confidence edge (score: 1.0)
   - De-score legacy/preliminary edges
   - Propagate semantic understanding through TOC

### 4. Iterative Refinement

As each page is processed:

- TOC inherits semantic, ontologically-tagged understanding
- Cross-references between sections are identified
- Relationships strengthen or weaken based on context
- Upper limit consideration for context size (TOC + markdown)

## Output Structure

The final output is a JSON-based graph containing:

- **Nodes**:
  - Unique IDs for pages/sections
  - Ontological tags
  - Semantic summaries
  - Confidence scores

- **Edges**:
  - Relationships between sections
  - Confidence scores
  - Relationship types
  - Directional indicators

## Key Principles

1. **Structure-First Approach**: TOC provides the organizing principle
2. **Ontological Tagging**: Not vector embeddings, but semantic categories
3. **Progressive Enhancement**: Basic extraction → LLM understanding
4. **Context Awareness**: Each page inherits TOC context
5. **Relationship Scoring**: Dynamic edge weights based on confidence

## Practical Considerations

- **Context Limits**: Monitor TOC + markdown size for LLM constraints
- **Fallback Strategies**: Graceful degradation when TOC unavailable
- **Edge Management**: Balance between comprehensive connections and graph clarity
- **Performance**: Consider chunking for large documents

## Implementation Notes

This model guides the development of:
- `SemanticOrchestrator`: Overall pipeline management
- `StructureAnalyzer`: TOC extraction and construction
- `GraphBuilder`: Node and edge creation
- `IntelligenceBackend`: LLM enhancement layer

The goal is to create a queryable, semantically-rich representation of document knowledge that captures not just content, but understanding.