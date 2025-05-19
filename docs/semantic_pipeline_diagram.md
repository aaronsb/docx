# Semantic Pipeline Visual Model

```mermaid
graph TD
    A[PDF Document] --> B{Has TOC?}
    B -->|Yes| C[Extract TOC]
    B -->|No| D[Markitdown Extract]
    D --> E[Construct TOC]
    C --> F[TOC Structure]
    E --> F
    
    F --> G[Initial Analysis]
    G --> H[Word Stems]
    G --> I[Bayesian Analysis]
    G --> J[Basic Relationships]
    
    H --> K[Initial Graph]
    I --> K
    J --> K
    
    K --> L[Page Processing Loop]
    L --> M[Prepare Context]
    M --> N[TOC Structure]
    M --> O[Markdown Content]
    M --> P[Page Image]
    
    N --> Q[LLM Processing]
    O --> Q
    P --> Q
    
    Q --> R[Coherent Summary]
    R --> S[Update Graph]
    S --> T[High Score Edge 1.0]
    S --> U[De-score Old Edges]
    S --> V[Inherit Semantics]
    
    V --> W{More Pages?}
    W -->|Yes| L
    W -->|No| X[Final Graph]
    
    X --> Y[JSON Output]
    Y --> Z[Ontological Tags]
    Y --> AA[Unique IDs]
    Y --> AB[Edge Relationships]
    Y --> AC[Confidence Scores]
```

## Pipeline Flow

1. **Structure Discovery Phase**
   - Check for existing TOC
   - Fall back to markitdown extraction
   - Build hierarchical structure

2. **Initial Analysis Phase**
   - Extract word stems
   - Perform Bayesian analysis
   - Identify basic relationships
   - Create preliminary graph

3. **Semantic Enhancement Phase**
   - Process each page iteratively
   - Combine TOC context with content
   - Use LLM for deep understanding
   - Update graph with high-confidence edges

4. **Output Generation Phase**
   - Produce JSON graph structure
   - Include ontological tagging
   - Maintain relationship scoring
   - Enable semantic querying

## Key Components

### Nodes
- Document sections/pages
- Semantic summaries
- Ontological categories
- Confidence scores

### Edges
- Inter-section relationships
- Weighted by confidence
- Typed connections
- Bidirectional where appropriate

### Context Management
- TOC provides global context
- Page content provides local detail
- LLM bridges understanding
- Context size limits respected