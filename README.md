# Memory Graph Extract

## What is this?

Memory Graph Extract is my first attempt at building a semantic conversion pipeline for PDF files. It transforms documents into knowledge graphs that language models can use to recall and reason about information.

Instead of just extracting text from PDFs, I'm trying to:

1. Understand the structure and meaning of documents
2. Build connections between related concepts
3. Create knowledge that AI assistants can actually use
4. Make document content queryable by meaning, not just keywords

This project connects with:
- [memory-graph](https://github.com/aaronsb/memory-graph) - Lets AI models access the knowledge
- [memory-graph-interface](https://github.com/aaronsb/memory-graph-interface) - Lets humans explore and tune the graphs

## How it works

The basic idea is simple:

1. **Extract text from PDF** (using different techniques)
2. **Analyze the content** to find structure, topics and connections
3. **Build a semantic graph** with nodes (ideas, sections) and edges (relationships)
4. **Store everything** in a format language models can use

What makes this different from typical document indexing:

- **Semantic edges** connect related information even when the words differ
- **Deterministic text analysis** finds patterns without requiring AI
- **Ontological labeling** categorizes information into meaningful types
- **Multimodal processing** can "see" and understand diagrams and images

The system uses either **OpenAI's API** (better results, costs money) or **local Ollama models** (free, requires good hardware). The quality depends heavily on combining classical text ranking with multimodal AI analysis.

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

## Getting Started

This project is a work in progress, but here's how to try it out:

### Installation

```bash
# Clone repository
git clone https://github.com/aaronsb/memory-graph-extract.git
cd memory-graph-extract

# Basic installation 
pip install -e .

# If you want to try local LLMs (requires good GPU)
pip install -e '.[llama]'
```

### Choosing a Backend

You have two main options:

1. **OpenAI** (recommended for best results)
   - Requires an API key
   - Better understanding of documents
   - Works on any hardware
   - Set up with: `export OPENAI_API_KEY=your-key-here`

2. **Ollama** (free, local processing)
   - Requires decent GPU (8GB+ VRAM)
   - Install Ollama separately: [ollama.com](https://ollama.com)
   - Pull a model: `ollama pull llava:latest`
   - Works offline, no API costs

### Converting Your First Document

```bash
# Using OpenAI (best quality)
mge semantic process your-document.pdf output/ --backend openai

# Using local Ollama (free)
mge semantic process your-document.pdf output/ --backend ollama

# Basic processing without AI (fast but limited understanding)
mge semantic process your-document.pdf output/ --no-llm
```

### Exploring the Results

```bash
# View information about the graph
mge memory info output/your-document/memory_graph.db

# Search for concepts
mge memory search "your search terms" --database output/your-document/memory_graph.db
```

### What's Generated?

The system creates:

- **SQLite database** containing the knowledge graph
- **Markdown files** with extracted text
- **JSON metadata** describing document structure

These can be used with the memory-graph server to give AI assistants access to your documents in a way they can actually understand and reason about.

### Configuration

The system uses several configuration files that you can customize:

1. **Environment Variables** (`.env`)
   - Copy `.env.example` to `.env` in the project root
   - Set your API keys and endpoints:
   ```
   # OpenAI API credentials (required for OpenAI backend)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Ollama configuration (customize if not using default)
   OLLAMA_BASE_URL=http://localhost:11434
   ```

2. **Default Configuration** (`pdf_manipulator/config/default_config.yaml`)
   - General settings for the basic pipeline
   - Rendering, OCR, and memory settings
   - Intelligence backend configuration

3. **Semantic Pipeline Configuration** (`pdf_manipulator/config/semantic_pipeline_config.yaml`)
   - Advanced settings for the semantic pipeline
   - LLM backend configuration
   - Graph construction parameters
   - Ontology settings
   - Performance tuning

Most settings work out-of-the-box, but you'll need to set up an API key in your `.env` file if using OpenAI.

See [Semantic Pipeline Overview](docs/semantic_pipeline_overview.md) for more details about how it works.

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

## How It's Built

I've tried to design this system to be understandable even if you're not an expert in knowledge graphs. Here's a simplified view:

```
PDF Document → Text Extraction → Semantic Understanding → Knowledge Graph
                                        ↓
                               [SQLite Database]
                                        ↓  
                    ┌─────────────────┴───────────────┐
                    │                                 │
              AI Assistant             Web Interface for Humans
         (via memory-graph MCP)      (memory-graph-interface)
```

### Main Components

1. **Text Extractor**: Gets text and images from the PDF
2. **Structure Analyzer**: Figures out how the document is organized
3. **Semantic Processor**: Uses AI to understand what the document actually means
4. **Graph Builder**: Creates connections between related pieces of information
5. **Memory Adapter**: Saves everything in a format that's useful for language models

The real magic happens in the combination of classical NLP techniques (like TextRank for summarization) and multimodal language models that can "see" and understand the document content. This hybrid approach helps overcome the limitations of either method alone.

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

## Key Technologies

Instead of listing all dependencies, here are the main technologies powering this project:

- **PyMuPDF**: For reading PDFs and extracting text/images
- **Markitdown**: For converting various document formats
- **TextRank**: For extracting important sentences without requiring AI
- **SQLite**: For storing the knowledge graph in a portable format
- **OpenAI API / Ollama**: For semantic understanding of content
- **NLTK & spaCy**: For basic natural language processing

The goal is to combine these tools in a way that creates richer understanding than any single approach could provide.

## Current Status

This is my first attempt at building a semantic knowledge system, so it's still evolving. The system works but has limitations:

- Document understanding varies based on the model quality
- Large documents may require significant processing time
- Local models (like LLaVA via Ollama) require good hardware
- Complex technical documents may not be analyzed perfectly

I'm actively exploring improvements to make the system more accurate and efficient.

## Contributing

I welcome contributions that enhance semantic understanding:

1. Improved relationship detection algorithms
2. Better semantic extraction methods
3. Enhanced graph visualization
4. Cross-document intelligence features

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [memory-graph](https://github.com/aaronsb/memory-graph) ecosystem for the database format
- [memory-graph-interface](https://github.com/aaronsb/memory-graph-interface) for visualization capabilities
- The AI/ML community for semantic understanding research