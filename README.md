# Memory Graph Extract

A semantic extraction framework that transforms documents into knowledge graphs compatible with the memory-graph ecosystem. Part of a suite of tools for building and interacting with semantic memory.

**Related Tools:**
- [memory-graph](https://github.com/aaronsb/memory-graph) - MCP server enabling AI language models to interact with semantic graph memory
- [memory-graph-interface](https://github.com/aaronsb/memory-graph-interface) - Web interface for humans to explore and interact with memory graphs

## Purpose

Memory Graph Extract goes beyond simple text extraction to build a **semantic understanding** of documents. It creates knowledge graphs that capture:

- Document structure and hierarchies
- Relationships between pages, sections, and concepts  
- Context-aware content extraction
- Cross-document connections and references

The generated semantic graphs are stored in SQLite databases compatible with the memory-graph ecosystem, making your documents queryable and interconnected across both AI assistants and human interfaces.

## Core Features

### Semantic Understanding
- **Knowledge Graph Construction**: Transform documents into interconnected semantic nodes
- **Relationship Mapping**: Capture "part_of", "precedes", "relates_to" connections
- **Context Preservation**: Maintain document structure and meaning
- **Cross-Document Linking**: Build knowledge networks across multiple documents

### Processing Capabilities  
- **Multi-Format Support**: PDF, Word, PowerPoint, Excel, images, and more via markitdown
- **AI-Enhanced Understanding**: Multiple AI backends for intelligent processing
- **Structure Detection**: Automatic TOC and section identification
- **Ontological Tagging**: Semantic categorization beyond simple embeddings

### Memory Graph Features
- **Ecosystem Compatible**: Direct integration with memory-graph and memory-graph-interface
- **Semantic Search**: Query documents by meaning, not just keywords
- **Relationship Traversal**: Follow connections between concepts
- **Domain Organization**: Separate knowledge domains for different topics

## Primary Use Cases

### 1. Knowledge Base Creation
Build a searchable, interconnected knowledge graph from your document collection:

```bash
# Process document into semantic graph
mge extract research-paper.pdf output/ --memory

# Process entire directory
mge extract-dir papers/ output/ --memory --recursive
```

### 2. Semantic Document Analysis
Extract meaning and relationships from complex documents:

```bash
# Analyze with enhanced AI understanding
mge extract technical-manual.pdf output/ --backend ollama --model llava:latest --memory

# Use existing knowledge to enhance processing
mge extract related-doc.pdf output/ --memory --use-context
```

### 3. Cross-Document Intelligence
Connect related information across multiple documents:

```bash
# Process multiple related documents
mge extract doc1.pdf output/ --memory --domain research
mge extract doc2.pdf output/ --memory --domain research

# Query across documents
mge memory search "quantum computing" --domain research
```

### 4. Integration with Memory Graph Ecosystem

```bash
# Extract documents for AI assistant access
mge extract library/*.pdf knowledge/ --memory
# Use with memory-graph MCP server
memory-graph serve knowledge/memory_graph.db

# Or explore with human interface
memory-graph-interface --database knowledge/memory_graph.db
```

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/aaronsb/memory-graph-extract.git
cd memory-graph-extract

# Install with memory graph support
pip install -e .

# Optional: Install with llama.cpp for local AI
pip install -e '.[llama]'
```

### Semantic Pipeline (Recommended)

The new semantic pipeline provides enhanced extraction with LLM-powered understanding:

```bash
# Extract document with semantic analysis
mge semantic process document.pdf output/

# Use specific LLM backend
mge semantic process document.pdf output/ --backend ollama  # Local with Ollama
mge semantic process document.pdf output/ --backend openai  # Cloud with GPT-4V

# Process without LLM (basic extraction)
mge semantic process document.pdf output/ --no-llm
```

### Basic Extraction (Legacy)

```bash
# Traditional extraction
mge extract document.pdf output/ --memory

# View the generated knowledge graph
mge memory info output/document/memory_graph.db

# Search the semantic content
mge memory search "key concepts" --database output/document/memory_graph.db
```

### Key Features of Semantic Pipeline

- **Multimodal Understanding**: Process both text and images with LLaVA or GPT-4V
- **Ontological Tagging**: Automatic categorization with domain-specific tags
- **Dynamic Graph Building**: Confidence-based edges with temporal decay
- **Parallel Processing**: Fast extraction with configurable workers
- **Flexible Backends**: Choose between local (Ollama) or cloud (OpenAI) processing

See [Semantic Pipeline Overview](docs/semantic_pipeline_overview.md) for detailed documentation.

### Advanced Processing

```python
from memory_graph_extract.core.document import Document
from memory_graph_extract.memory.processor import MemoryProcessor
from memory_graph_extract.memory.adapter import MemoryConfig

# Configure semantic extraction
memory_config = MemoryConfig(
    database_path="knowledge_graph.db",
    domain_name="research_papers",
    enable_relationships=True,
    enable_summaries=True
)

# Process document into semantic graph
with Document("paper.pdf") as doc:
    with MemoryProcessor(memory_config) as processor:
        results = processor.process_document(
            document=doc,
            page_content=extracted_content,
            metadata={'tags': ['AI', 'research']}
        )
        
# Query the knowledge graph
similar_docs = processor.find_similar_documents("machine learning")
document_graph = processor.get_document_graph(results['document_id'])
```

## Architecture

The system is designed around semantic understanding using the memory-graph database format:

```
Document → Content Extraction → Semantic Analysis → Knowledge Graph
                                     ↓
                            [Memory Graph Database]
                                     ↓  
                    ┌────────────────┴────────────────┐
                    │                                 │
            [memory-graph]                [memory-graph-interface]
            (AI Access via MCP)           (Human Web Interface)
```

### Key Components

1. **Semantic Orchestrator**: Manages the extraction pipeline
2. **Content Extractor**: Extracts text and structure via markitdown
3. **Graph Builder**: Constructs interconnected knowledge networks
4. **Structure Analyzer**: Detects document organization and hierarchies
5. **Relationship Engine**: Maps connections between concepts

## Output Structure

Processing creates a rich semantic graph compatible with the memory-graph ecosystem:

```
output_directory/
└── document_name/
    ├── memory_graph.db       # Semantic knowledge graph (memory-graph format)
    ├── markdown/             # Extracted content
    │   ├── document.md      # Full document
    │   └── sections/        # Individual sections
    └── metadata.json        # Document structure and relationships
```

The `memory_graph.db` contains:
- **Nodes**: Document, pages, sections, concepts
- **Edges**: Relationships between nodes
- **Metadata**: Context and semantic information
- **Search Index**: Full-text semantic search

## Configuration

Configure semantic extraction behavior:

```yaml
memory:
  enabled: true                    # Enable semantic graph by default
  database_name: "memory_graph.db"
  domain:
    name: "documents"
    description: "Document knowledge base"
  
  # Semantic extraction settings
  extraction:
    min_content_length: 50        # Minimum text for node creation
    detect_relationships: true    # Auto-detect connections
    generate_summaries: true      # AI-generated summaries
    
  # Graph construction
  graph:
    max_depth: 3                 # Relationship traversal depth
    similarity_threshold: 0.7    # For auto-connections
```

## Integration

### Memory Graph MCP Server

The generated databases work directly with [memory-graph](https://github.com/aaronsb/memory-graph):

```bash
# Extract documents
mge extract documents/*.pdf knowledge/

# Serve via MCP for AI assistants
memory-graph serve knowledge/memory_graph.db

# Use with Claude Desktop, Cody, etc.
```

### Memory Graph Interface

Explore your knowledge graphs with [memory-graph-interface](https://github.com/aaronsb/memory-graph-interface):

```bash
# Launch web interface
memory-graph-interface --database knowledge/memory_graph.db

# Access at http://localhost:8080
```

### Python API

```python
from memory_graph_extract.memory.adapter import MemoryAdapter

# Query existing knowledge graph
adapter = MemoryAdapter(config)
adapter.connect()

# Semantic search
results = adapter.search_memories("machine learning concepts")

# Traverse relationships
graph = adapter.get_document_graph(document_id, max_depth=2)
```

## Command Line Interface

The CLI uses the `mge` command (Memory Graph Extract):

```bash
# Extract documents
mge extract document.pdf output/
mge extract-dir folder/ output/

# Memory operations
mge memory search "query" --database graph.db
mge memory info graph.db
mge memory connect db1.db db2.db

# Configuration
mge config show
mge config set memory.enabled true

# Utilities
mge render document.pdf output/ --dpi 300
mge ocr image.png output/
```

## Contributing

We welcome contributions that enhance semantic understanding:

1. Improved relationship detection algorithms
2. Better semantic extraction methods
3. Enhanced graph visualization
4. Cross-document intelligence features

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [memory-graph](https://github.com/aaronsb/memory-graph) ecosystem for the database format
- [memory-graph-interface](https://github.com/aaronsb/memory-graph-interface) for visualization capabilities
- PyMuPDF for document handling
- markitdown for multi-format conversion
- The AI/ML community for semantic understanding research