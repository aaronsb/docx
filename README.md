# DocX - Semantic Graph PDF Extractor

A Python framework for transforming PDF documents into semantic knowledge graphs, enabling intelligent understanding of document content and relationships.

## Purpose

DocX goes beyond simple text extraction to build a **semantic understanding** of PDF documents. It creates a knowledge graph that captures:

- Document structure and hierarchies
- Relationships between pages, sections, and concepts  
- Context-aware content extraction
- Cross-document connections and references

The generated semantic graphs are stored in SQLite databases compatible with [memory-graph-mcp](https://github.com/aaronsb/memory-graph), making your documents queryable and interconnected.

## Core Features

### Semantic Understanding
- **Knowledge Graph Construction**: Transform documents into interconnected semantic nodes
- **Relationship Mapping**: Capture "part_of", "precedes", "relates_to" connections
- **Context Preservation**: Maintain document structure and meaning
- **Cross-Document Linking**: Build knowledge networks across multiple PDFs

### Processing Capabilities  
- **Direct Document Conversion**: Fast semantic extraction via markitdown
- **AI-Enhanced Understanding**: Multiple AI backends for intelligent processing
- **Structure Detection**: Automatic TOC and section identification
- **Multi-format Support**: PDF, Word, PowerPoint, Excel, images, and more

### Memory Graph Features
- **MCP-Compatible Storage**: Direct integration with memory-graph ecosystem
- **Semantic Search**: Query documents by meaning, not just keywords
- **Relationship Traversal**: Follow connections between concepts
- **Domain Organization**: Separate knowledge domains for different topics

## Primary Use Cases

### 1. Knowledge Base Creation
Build a searchable, interconnected knowledge graph from your document collection:

```bash
# Process document into semantic graph
pdfx process research-paper.pdf output/ --memory

# Process entire directory
pdfx process-dir papers/ output/ --memory --recursive
```

### 2. Semantic Document Analysis
Extract meaning and relationships from complex documents:

```bash
# Analyze with enhanced AI understanding
pdfx process technical-manual.pdf output/ --backend ollama --model llava:latest --memory

# Use existing knowledge to enhance processing
pdfx process related-doc.pdf output/ --memory --use-context
```

### 3. Cross-Document Intelligence
Connect related information across multiple PDFs:

```bash
# Process multiple related documents
pdfx process doc1.pdf output/ --memory --domain research
pdfx process doc2.pdf output/ --memory --domain research

# Query across documents
pdfx memory search "quantum computing" --domain research
```

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/aaronsb/docx.git
cd docx

# Install with memory graph support
pip install -e .

# Optional: Install with llama.cpp for local AI
pip install -e '.[llama]'
```

### Basic Semantic Extraction

```bash
# Extract document into semantic graph
pdfx process document.pdf output/ --memory

# View the generated knowledge graph
pdfx memory info output/document/memory_graph.db

# Search the semantic content
pdfx memory search "key concepts" --database output/document/memory_graph.db
```

### Advanced Processing

```python
from pdf_manipulator.core.document import PDFDocument
from pdf_manipulator.memory.memory_processor import MemoryProcessor
from pdf_manipulator.memory.memory_adapter import MemoryConfig

# Configure semantic extraction
memory_config = MemoryConfig(
    database_path="knowledge_graph.db",
    domain_name="research_papers",
    enable_relationships=True,
    enable_summaries=True
)

# Process document into semantic graph
with PDFDocument("paper.pdf") as doc:
    with MemoryProcessor(memory_config) as processor:
        results = processor.process_document(
            pdf_document=doc,
            page_content=extracted_content,
            document_metadata={'tags': ['AI', 'research']}
        )
        
# Query the knowledge graph
similar_docs = processor.find_similar_documents("machine learning")
document_graph = processor.get_document_graph(results['document_id'])
```

## Architecture

The system is designed around semantic understanding:

```
Document → Content Extraction → Semantic Analysis → Knowledge Graph
                                      ↓
                              [Memory Graph Database]
                                      ↓  
                            Queryable Semantic Network
```

### Key Components

1. **Semantic Processors**: Extract meaning from content
2. **Memory Adapter**: Store semantic nodes and relationships
3. **Graph Builder**: Construct interconnected knowledge networks
4. **TOC Analyzer**: Detect document structure and hierarchies
5. **Relationship Engine**: Map connections between concepts

## Output Structure

Processing creates a rich semantic graph:

```
output_directory/
└── document_name/
    ├── memory_graph.db       # Semantic knowledge graph
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
    name: "pdf_processing"
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

### Memory Graph MCP

The generated databases work directly with [memory-graph-mcp](https://github.com/aaronsb/memory-graph):

```bash
# Use with Claude Desktop
cp output/document/memory_graph.db ~/.claude/memories/

# Or configure MCP server
memory-graph-mcp serve output/document/memory_graph.db
```

### Python API

```python
from pdf_manipulator.memory.memory_adapter import MemoryAdapter

# Query existing knowledge graph
adapter = MemoryAdapter(config)
adapter.connect()

# Semantic search
results = adapter.search_memories("machine learning concepts")

# Traverse relationships
graph = adapter.get_document_graph(document_id, max_depth=2)
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

- [memory-graph-mcp](https://github.com/aaronsb/memory-graph) for graph storage format
- PyMuPDF for document handling
- markitdown for direct conversion
- The AI/ML community for semantic understanding research